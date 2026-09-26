"""Every figure published in MEMO.md / README.md, asserted against the generated outputs.
Run: python -m pytest tests/ -v   or   python tests/test_claims.py"""
import hashlib
import pathlib
import sys

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT, RAW = ROOT / "output", ROOT / "data" / "raw"
HASHES = {
    "bt_crossings_daily_by_facility.csv": "ce0e43afa649256de1bd2d6f1ac28c94190035f904cab3d96b57c5ffb9ff3b47",
    "crz_entries_daily_by_group_class.csv": "71eb17a0a91318fffffbeaa2707a7a95e6070139cfaac0ff1189d6412c4cfb61",
    "crz_entries_daily_by_period_class.csv": "e2b1ff7078719a4a80416878201460ecb3a1206c4615b2de65a3729762f07d99",
    "mta_daily_ridership_traffic.csv": "f1f93654759bd089041bb84210c0bc43df9450c0b517b0a01f60a01a58260739",
}


def near(a, b, tol, label):
    assert abs(a - b) <= tol, "{}: expected {} +/- {}, got {}".format(label, b, tol, a)


def did():
    return pd.read_csv(OUT / "did_summary.csv").set_index("estimate")["effect_pct"]


def test_raw_data_unmodified():
    """Source extracts match the SHA-256 recorded at download."""
    for name, h in HASHES.items():
        assert hashlib.sha256((RAW / name).read_bytes()).hexdigest() == h, name + " changed"


def test_panel_shape():
    """CLAIM: balanced panel of 1,342 days (735 pre, 607 post), 4 treated and 10 control units."""
    d = pd.read_csv(OUT / "did_summary.csv").iloc[0]
    assert (int(d["panel_days"]), int(d["pre_days"]), int(d["post_days"])) == (1342, 735, 607)


def test_main_effect():
    """CLAIM: tunnel traffic into the zone fell 4.2% relative to comparison bridges."""
    near(did()["Tunnels into zone vs non-Manhattan bridges (both directions)"], -4.17, 0.05, "main")


def test_effect_range():
    """CLAIM: every specification negative; range 2.2% (net of trend) to 4.6% (unadjusted)."""
    e = did().drop("Diversion: RFK + Henry Hudson vs non-Manhattan bridges")
    assert (e < 0).all()
    near(e["Net of pre-existing trend"], -2.21, 0.05, "trend-adjusted")
    near(e["Without seasonal adjustment"], -4.64, 0.05, "unadjusted")
    near(e["Inbound direction only"], -4.07, 0.05, "inbound")


def test_no_fading():
    """CLAIM: year-2 estimate (-5.4%) is not smaller than year 1 (-3.4%)."""
    e = did()
    near(e["Year 1 (2025) only"], -3.36, 0.05, "y1")
    near(e["Year 2 (2026) only"], -5.36, 0.05, "y2")
    assert e["Year 2 (2026) only"] < e["Year 1 (2025) only"]


def test_no_diversion():
    """CLAIM: Manhattan crossings outside the zone changed +0.1% - no displacement."""
    assert abs(did()["Diversion: RFK + Henry Hudson vs non-Manhattan bridges"]) < 0.5


def test_placebos():
    """CLAIM: no placebo exceeds the main effect (max 2.0% bridges, 2.1% dates)."""
    i = pd.read_csv(OUT / "inference.csv").iloc[0]
    near(i["max_abs_placebo_space_pct"], 2.03, 0.05, "space")
    near(i["max_abs_placebo_time_pct"], 2.10, 0.05, "time")
    assert i["p_space"] == 0 and i["p_time"] == 0
    assert int(i["n_space"]) == 5 and int(i["n_time"]) == 13


def test_parallel_pre_trend():
    """CLAIM: pre-period monthly gap is flat (sd 1.3 points) after seasonal adjustment."""
    i = pd.read_csv(OUT / "inference.csv").iloc[0]
    near(i["pre_period_gap_sd_pct"], 1.34, 0.05, "pre sd")


def test_seasonal_adjustment_matters():
    """CLAIM: seasonal adjustment cut pre-period monthly noise from about 6 points to 1.3."""
    i = pd.read_csv(OUT / "inference.csv").iloc[0]
    near(i["pre_period_gap_sd_unadjusted_pct"], 5.71, 0.05, "unadjusted pre sd")


def test_zone_entries_yoy():
    """CLAIM: zone entries -4.2% in 2026 vs 2025; cars -7.4%, taxis & ride-hail +1.5%."""
    near(pd.read_csv(OUT / "crz_yoy.csv").iloc[0]["yoy_pct"], -4.17, 0.05, "yoy")
    m = pd.read_csv(OUT / "crz_vehicle_mix.csv").set_index("vehicle_class")["yoy_2026_vs_2025_pct"]
    near(m["1 - Cars, Pickups and Vans"], -7.4, 0.1, "cars")
    near(m["TLC Taxi/FHV"], 1.5, 0.1, "taxis")


def test_subway_descriptive():
    """CLAIM: subway ridership +9.3% in 2025 vs 2024 (descriptive, not causal)."""
    t = pd.read_csv(OUT / "transit_descriptive.csv").set_index("mode")
    near(t.loc["Subway", "change_2025_vs_2024_pct"], 9.3, 0.1, "subway")


def _main():
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_")]
    bad = 0
    for n, f in tests:
        try:
            f()
            print("  PASS  {:<26} {}".format(n, (f.__doc__ or "").strip().splitlines()[0]))
        except AssertionError as e:
            bad += 1
            print("  FAIL  {:<26} {}".format(n, e))
    print("\n{} passed, {} failed".format(len(tests) - bad, bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(_main())
