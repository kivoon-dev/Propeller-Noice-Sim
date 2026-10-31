"""The pages in viz/ must use the same numbers as the model.

Both pages copy the Milestone 1 thrust and power coefficients and the air
constants into JavaScript; the Propeller Lab also copies the 4-blade
coefficients (M3) and which blade slices stall. If the geometry changes (for
example when the real chords are measured), these tests fail until the pages
are updated too.
"""

import csv
import json
import re
from pathlib import Path

import pytest

from propnoise.airfoil import DEFAULT_AIRFOIL
from propnoise.bemt import solve_hover
from propnoise.constants import RHO, SPEED_OF_SOUND
from propnoise.props import GEMFAN_5152_4BLADE, PROPELLERS

VIZ = Path(__file__).resolve().parents[1] / "viz"
PAGES = ("hum_bench.html", "propeller_lab.html")


def _page_source(page):
    return (VIZ / page).read_text(encoding="utf-8")


@pytest.mark.parametrize("page", PAGES)
@pytest.mark.parametrize("prop", PROPELLERS, ids=lambda p: p.name.split()[1])
def test_page_coefficients_match_model(page, prop):
    short_name = prop.name.split(" (")[0]
    match = re.search(r'name: "' + re.escape(short_name) + r'".*?ct: ([0-9.eE+-]+), cp: ([0-9.eE+-]+)',
                      _page_source(page))
    assert match, f"{short_name} not found in {page}"
    sol = solve_hover(prop)
    assert float(match.group(1)) == pytest.approx(sol.ct, rel=1e-9)
    assert float(match.group(2)) == pytest.approx(sol.cp, rel=1e-9)


@pytest.mark.parametrize("page", PAGES)
def test_page_air_constants_match_model(page):
    src = _page_source(page)
    assert float(re.search(r"RHO = ([0-9.]+)", src).group(1)) == RHO
    assert float(re.search(r"C0 = ([0-9.]+)", src).group(1)) == SPEED_OF_SOUND


def test_lab_four_blade_coefficients_match_model():
    match = re.search(r"FOUR = \{ ct: ([0-9.eE+-]+), cp: ([0-9.eE+-]+) \}",
                      _page_source("propeller_lab.html"))
    assert match, "FOUR not found in propeller_lab.html"
    sol = solve_hover(GEMFAN_5152_4BLADE)
    assert float(match.group(1)) == pytest.approx(sol.ct, rel=1e-9)
    assert float(match.group(2)) == pytest.approx(sol.cp, rel=1e-9)


@pytest.mark.parametrize("prop", PROPELLERS, ids=lambda p: p.name.split()[1])
def test_lab_stalled_slices_match_model(prop):
    """'1' marks a slice whose lift has hit the airfoil's maximum (stalled)."""
    short_name = prop.name.split(" (")[0]
    match = re.search(r'name: "' + re.escape(short_name) + r'".*?stall: "([01]+)"',
                      _page_source("propeller_lab.html"), re.S)
    assert match, f"{short_name} stall string not found"
    sol = solve_hover(prop)
    expected = "".join("1" if cl >= DEFAULT_AIRFOIL.cl_max - 1e-12 else "0" for cl in sol.cl)
    assert match.group(1) == expected


def test_lab_scores_match_m4_csv():
    """The Score tab embeds results/m4_scores.csv, rounded for display."""
    src = _page_source("propeller_lab.html")
    scores = json.loads(re.search(r"const SCORES = (\{.*?\});\n", src).group(1))
    csv_path = VIZ.parent / "results" / "m4_scores.csv"
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
    assert sum(len(v) for levels in scores.values() for v in levels.values()) == len(rows)
    for r in rows:
        key = "5152" if r["prop_name"].startswith("Gemfan 5152 ") else "LR5126-2"
        page = next(x for x in scores[key][r["whoosh"]] if x[0] == float(r["thrust_N"]))
        assert page[1] == pytest.approx(float(r["spl_dBA"]), abs=0.051)
        assert page[2] == pytest.approx(float(r["N5"]), abs=0.0051)
        assert page[3] == pytest.approx(float(r["S"]), abs=0.0051)
        assert page[4] == pytest.approx(float(r["PA"]), abs=0.0051)
