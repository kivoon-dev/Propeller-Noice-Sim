"""A simple model of how a blade section makes lift and drag.

Plain words: tilt a flat-ish blade into the air and it pushes air down (lift).
Tilt it more and it pushes harder, until the air can't follow the surface any
more and the blade "stalls": lift stops growing and drag jumps.

ASSUMPTION: these numbers are generic values for thin, slightly curved blades
at the low speeds small drone propellers see (Reynolds number around 30,000 to
80,000). They are not measured for the Gemfan blades. Changing them changes the
predicted spin speeds, so the tests check the RESULTS against Empa, not these
numbers.
"""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Airfoil:
    lift_slope_per_rad: float = 5.7      # thin-airfoil theory gives 2*pi; low Re is lower
    alpha_zero_lift_deg: float = -2.0    # a slightly curved blade still lifts at 0 degrees
    cl_max: float = 1.1                  # lift stops growing past this (stall)
    cd0: float = 0.025                   # minimum drag, higher than big wings at low Re
    k_drag: float = 0.02                 # drag rises with lift
    cl_min_drag: float = 0.3             # lift at which drag is smallest
    stall_drag_gain: float = 1.5         # extra drag once stalled

    def coefficients(self, alpha_rad):
        """Return (lift coefficient, drag coefficient) for an angle of attack."""
        alpha = np.asarray(alpha_rad, dtype=float)
        a = alpha - np.radians(self.alpha_zero_lift_deg)
        cl_linear = self.lift_slope_per_rad * a
        cl = np.clip(cl_linear, -self.cl_max, self.cl_max)
        cd = self.cd0 + self.k_drag * (cl - self.cl_min_drag) ** 2
        # Past stall, drag grows with how far past the stall angle we are.
        a_stall = self.cl_max / self.lift_slope_per_rad
        excess = np.maximum(np.abs(a) - a_stall, 0.0)
        cd = cd + self.stall_drag_gain * np.sin(excess) ** 2
        return cl, cd


DEFAULT_AIRFOIL = Airfoil()
