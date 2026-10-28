"""Propeller noise simulator: predicts spin speed, hum and annoyance of drone propellers.

Replicates the conventional-propeller part of Meister, Van Renterghem & Pieren,
"Acoustic and aerodynamic performance evaluation of a commercial toroidal propeller
compared to conventional propellers", Acta Acustica 10, 57 (2026),
https://doi.org/10.1051/aacus/2026057
"""

__version__ = "0.2.0"

EMPA_THRUSTS_N = (0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5)
