"""Propeller geometry.

Plain words: a propeller is described by how wide it is (diameter), how far it
would screw forward in one turn (pitch), how many blades it has, and how wide each
blade is along its length (chord).

ASSUMPTION: the chord numbers below are ESTIMATES from typical 5-inch FPV
propellers, not measurements of the actual Gemfan blades. When the real
propellers arrive, measure the chord with calipers at 20%, 45%, 75% and 95% of
the radius and update the values here. Diameter, pitch and blade count are the
manufacturer's numbers and are reliable.
"""

from dataclasses import dataclass

import numpy as np

from .constants import INCH


@dataclass(frozen=True)
class Propeller:
    name: str
    diameter_m: float
    pitch_m: float
    blades: int
    chord_root_m: float      # chord at the root of the blade (r_root)
    chord_max_m: float       # widest chord
    r_chord_max: float       # where the widest chord sits, as a fraction of the radius
    chord_tip_m: float       # chord near the tip
    r_root: float = 0.15     # blade starts at 15% of the radius (hub cut-out)

    @property
    def radius_m(self) -> float:
        return self.diameter_m / 2

    def chord(self, r):
        """Chord (m) at non-dimensional radius r (0 = centre, 1 = tip)."""
        r = np.asarray(r, dtype=float)
        return np.interp(r, [self.r_root, self.r_chord_max, 1.0],
                         [self.chord_root_m, self.chord_max_m, self.chord_tip_m])

    def twist(self, r):
        """Blade angle (rad) at radius r for a constant-pitch (helical) blade.

        A blade section at radius r travels 2*pi*r*R per turn; to advance one
        pitch length per turn, it must be angled at atan(pitch / (2*pi*r*R)).
        """
        r = np.asarray(r, dtype=float)
        return np.arctan(self.pitch_m / (2 * np.pi * r * self.radius_m))

    def solidity(self, r):
        """Local solidity: how much of the ring at radius r is covered by blade."""
        return self.blades * self.chord(r) / (np.pi * self.radius_m)


# The two conventional propellers from Empa's 2026 study (both 5.1 inch, 2-blade).
GEMFAN_5152 = Propeller(
    name="Gemfan 5152 (high pitch)",
    diameter_m=5.1 * INCH,
    pitch_m=5.2 * INCH,
    blades=2,
    chord_root_m=0.010,   # ESTIMATE
    chord_max_m=0.015,    # ESTIMATE
    r_chord_max=0.45,     # ESTIMATE
    chord_tip_m=0.006,    # ESTIMATE (pointed "inverse" tip)
)

GEMFAN_LR5126 = Propeller(
    name="Gemfan LR5126-2 (low pitch)",
    diameter_m=5.1 * INCH,
    pitch_m=2.6 * INCH,
    blades=2,
    chord_root_m=0.007,   # ESTIMATE (slim long-range blade)
    chord_max_m=0.010,    # ESTIMATE
    r_chord_max=0.40,     # ESTIMATE
    chord_tip_m=0.005,    # ESTIMATE
)

PROPELLERS = (GEMFAN_5152, GEMFAN_LR5126)
