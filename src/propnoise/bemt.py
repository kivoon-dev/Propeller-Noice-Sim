"""Milestone 1: how fast must each propeller spin to make a given thrust?

Plain words
-----------
We cut each blade into thin slices. For every slice we ask two questions that
must have the same answer:
  1. Blade view: how much does this slice push, given its angle and speed?
  2. Air view: how much push does it take to speed up the air flowing through
     this ring of the propeller disc?
The air speed through the disc (the "inflow") that makes both answers match is
found for every slice, then all slices are added up.

Technical
---------
Hover blade element momentum theory (BEMT) with Prandtl tip loss, following
Leishman, Principles of Helicopter Aerodynamics (2000), ch. 3. Coefficients use
the rotor convention: CT = T / (rho * A * (Omega*R)^2), CP = P / (rho * A *
(Omega*R)^3). In hover with fixed blade-section properties, CT and CP do not
depend on spin speed, so thrust grows with the square of RPM and power with the
cube.
"""

from dataclasses import dataclass

import numpy as np
from scipy.optimize import brentq

from .airfoil import DEFAULT_AIRFOIL, Airfoil
from .constants import KINEMATIC_VISCOSITY, RHO, SPEED_OF_SOUND
from .props import Propeller


@dataclass
class HoverSolution:
    prop: Propeller
    ct: float                 # rotor thrust coefficient
    cp: float                 # rotor power coefficient
    r: np.ndarray             # slice positions (fraction of radius)
    dr: np.ndarray            # slice widths
    inflow: np.ndarray        # inflow ratio lambda at each slice
    alpha_deg: np.ndarray     # angle of attack at each slice
    cl: np.ndarray            # lift coefficient at each slice
    residual: np.ndarray      # momentum minus blade-element thrust (should be ~0)


@dataclass
class OperatingPoint:
    prop_name: str
    thrust_N: float
    rpm: float
    tip_speed_ms: float
    tip_mach: float
    bpf_Hz: float             # blade-passing frequency: the main hum
    shaft_Hz: float           # once-per-turn frequency
    power_W: float            # shaft power (mechanical), not battery power
    torque_Nm: float
    figure_of_merit: float    # ideal power / actual power, 0 to 1
    ct_nD: float              # thrust coefficient in the T = C_T rho n^2 D^4 form
    reynolds_75: float        # Reynolds number at 75% radius


def _tip_loss(blades: int, r: float, phi: float) -> float:
    """Prandtl tip-loss factor: lift fades near the tip as air escapes around it."""
    f = 0.5 * blades * (1.0 - r) / (r * max(phi, 1e-9))
    return (2.0 / np.pi) * np.arccos(np.exp(-f))


def solve_hover(prop: Propeller, airfoil: Airfoil = DEFAULT_AIRFOIL,
                n_slices: int = 80) -> HoverSolution:
    """Solve the inflow at every blade slice and integrate CT and CP."""
    edges = np.linspace(prop.r_root, 1.0, n_slices + 1)
    r = 0.5 * (edges[:-1] + edges[1:])
    dr = np.diff(edges)

    inflow = np.zeros_like(r)
    alpha = np.zeros_like(r)
    cl_arr = np.zeros_like(r)
    resid = np.zeros_like(r)
    dct = np.zeros_like(r)
    dcp = np.zeros_like(r)

    for i, (ri, sigma, theta) in enumerate(zip(r, prop.solidity(r), prop.twist(r))):

        def residual(lam, ri=ri, sigma=sigma, theta=theta):
            phi = np.arctan2(lam, ri)
            F = _tip_loss(prop.blades, ri, phi)
            cl, cd = airfoil.coefficients(theta - phi)
            w2 = ri ** 2 + lam ** 2
            blade = 0.5 * sigma * w2 * (cl * np.cos(phi) - cd * np.sin(phi))
            momentum = 4.0 * F * lam ** 2 * ri
            return momentum - blade

        lo, hi = 1e-9, 1.0
        if residual(lo) >= 0:          # this slice makes no lift
            lam = 0.0
        else:
            lam = brentq(residual, lo, hi, xtol=1e-12, maxiter=200)

        phi = np.arctan2(lam, ri)
        cl, cd = airfoil.coefficients(theta - phi)
        w2 = ri ** 2 + lam ** 2
        inflow[i] = lam
        alpha[i] = np.degrees(theta - phi)
        cl_arr[i] = cl
        resid[i] = residual(lam) if lam > 0 else 0.0
        dct[i] = 0.5 * prop.solidity(ri) * w2 * (cl * np.cos(phi) - cd * np.sin(phi))
        dcp[i] = 0.5 * prop.solidity(ri) * w2 * (cl * np.sin(phi) + cd * np.cos(phi)) * ri

    ct = float(np.sum(dct * dr))
    cp = float(np.sum(dcp * dr))
    return HoverSolution(prop, ct, cp, r, dr, inflow, alpha, cl_arr, resid)


def operating_point(sol: HoverSolution, thrust_N: float, rho: float = RHO) -> OperatingPoint:
    """Spin speed, power and figure of merit needed for one thrust."""
    prop = sol.prop
    R = prop.radius_m
    area = np.pi * R ** 2
    omega = np.sqrt(thrust_N / (sol.ct * rho * area * R ** 2))     # rad/s
    tip_speed = omega * R
    power = sol.cp * rho * area * tip_speed ** 3
    n = omega / (2 * np.pi)                                          # rev/s
    ideal_power = thrust_N ** 1.5 / np.sqrt(2 * rho * area)
    chord_75 = float(prop.chord(0.75))
    return OperatingPoint(
        prop_name=prop.name,
        thrust_N=thrust_N,
        rpm=omega * 60 / (2 * np.pi),
        tip_speed_ms=tip_speed,
        tip_mach=tip_speed / SPEED_OF_SOUND,
        bpf_Hz=prop.blades * n,
        shaft_Hz=n,
        power_W=power,
        torque_Nm=power / omega,
        figure_of_merit=ideal_power / power,
        ct_nD=thrust_N / (rho * n ** 2 * prop.diameter_m ** 4),
        reynolds_75=0.75 * tip_speed * chord_75 / KINEMATIC_VISCOSITY,
    )


def sweep(prop: Propeller, thrusts_N, airfoil: Airfoil = DEFAULT_AIRFOIL):
    """Operating points for a list of thrusts (Empa used 0.5 to 3.5 N)."""
    sol = solve_hover(prop, airfoil)
    return [operating_point(sol, float(t)) for t in thrusts_N]
