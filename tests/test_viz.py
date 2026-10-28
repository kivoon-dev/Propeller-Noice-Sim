"""The Hum Bench page (viz/hum_bench.html) must use the same numbers as the model.

The page copies the Milestone 1 thrust and power coefficients and the air
constants into JavaScript. If the geometry changes (for example when the real
chords are measured), this test fails until the page is updated too.
"""

import re
from pathlib import Path

import pytest

from propnoise.bemt import solve_hover
from propnoise.constants import RHO, SPEED_OF_SOUND
from propnoise.props import PROPELLERS

PAGE = Path(__file__).resolve().parents[1] / "viz" / "hum_bench.html"


def _page_source():
    return PAGE.read_text(encoding="utf-8")


@pytest.mark.parametrize("prop", PROPELLERS, ids=lambda p: p.name.split()[1])
def test_page_coefficients_match_model(prop):
    short_name = prop.name.split(" (")[0]
    match = re.search(r'name: "' + re.escape(short_name) + r'".*?ct: ([0-9.eE+-]+), cp: ([0-9.eE+-]+)',
                      _page_source())
    assert match, f"{short_name} not found in {PAGE.name}"
    sol = solve_hover(prop)
    assert float(match.group(1)) == pytest.approx(sol.ct, rel=1e-9)
    assert float(match.group(2)) == pytest.approx(sol.cp, rel=1e-9)


def test_page_air_constants_match_model():
    src = _page_source()
    assert float(re.search(r"RHO = ([0-9.]+)", src).group(1)) == RHO
    assert float(re.search(r"C0 = ([0-9.]+)", src).group(1)) == SPEED_OF_SOUND
