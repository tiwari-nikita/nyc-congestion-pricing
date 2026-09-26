"""
Did NYC congestion pricing reduce traffic into the zone - and what else moved?

DESIGN: difference-in-differences on MTA bridge and tunnel crossings, 2023 - 2026.
  Treated  : Hugh L. Carey Tunnel and Queens Midtown Tunnel. Both deliver traffic straight
             into the Congestion Relief Zone (Manhattan below 60th St). Both directions are
             used, because a trip into the zone is also a trip out of it.
  Control  : MTA crossings that never touch Manhattan - Verrazzano-Narrows, Throgs Neck,
             Bronx-Whitestone, Cross Bay, Marine Parkway. Same agency, same toll system,
             same weather and economy, no exposure to the zone toll.
  Spillover: RFK Bridge and Henry Hudson Bridge reach Manhattan north of the zone. They are
             excluded from the control (they could absorb diverted trips) and tested on
             their own for diversion.
  Treatment date: 5 January 2025, when zone tolling began.

Estimator: two-way fixed effects on log daily crossings (unit and date effects), on a
balanced panel, so common shocks - weather, holidays, the economy - cancel out.
With only two treated facilities, conventional standard errors would be unreliable, so
inference is by permutation: the same estimate is recomputed pretending each control
unit was treated, and pretending treatment started on fake dates in the pre-period.
"""
import pathlib
import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW, OUT = ROOT / "data" / "raw", ROOT / "output"
START, POLICY, END = pd.Timestamp("2023-01-01"), pd.Timestamp("2025-01-05"), None

TREATED = {"Hugh L. Carey Tunnel", "Queens Midtown Tunnel"}
CONTROL = {"Verrazzano - Narrows Bridge", "Throgs Neck Bridge", "Bronx - Whitestone Bridge",
           "Cross Bay Bridge", "Marine Parkway Bridge"}
SPILL = {"Robert F. Kennedy Bridge Bronx", "Robert F. Kennedy Bridge Manhattan", "Henry Hudson Bridge"}

bt = pd.read_csv(RAW / "bt_crossings_daily_by_facility.csv", parse_dates=["date"])
bt = bt[bt["date"] >= START].copy()
bt["unit"] = bt["facility"] + " | " + bt["direction"]
bt["group"] = np.select([bt["facility"].isin(TREATED), bt["facility"].isin(CONTROL),
                         bt["facility"].isin(SPILL)], ["treated", "control", "spillover"], "other")


def balanced(df):
    """Keep only dates on which every unit reports, so the panel is balanced."""
    wide = df.pivot_table(index="date", columns="unit", values="crossings", aggfunc="sum")
    wide = wide.dropna()
    wide = wide[(wide > 0).all(axis=1)]
    return wide


def twfe(wide, treated_units, post_mask):
    """Two-way FE DiD on a balanced panel via double demeaning. Returns beta (log points)."""
    y = np.log(wide.to_numpy())
    d = np.zeros_like(y)
    cols = list(wide.columns)
    for u in treated_units:
        d[:, cols.index(u)] = post_mask.astype(float)
    def dm(a):
        return a - a.mean(axis=0, keepdims=True) - a.mean(axis=1, keepdims=True) + a.mean()
    yt, dt = dm(y), dm(d)
    return float((yt * dt).sum() / (dt * dt).sum())


def pct(beta):
    return (np.exp(beta) - 1) * 100


def seasonal_adjust(wide):
    """Remove each unit's own calendar-month pattern, estimated on the pre-period only.

    The control group includes Cross Bay and Marine Parkway, which serve the Rockaway
    beaches and surge every summer; the tunnels do not. Without this, the treated-minus-
    control gap swings with the seasons and a fake mid-2023 'policy' looks as large as the
    real one. Using pre-period months only keeps the policy period from leaking into the
    adjustment. Returns exp(adjusted log) so twfe() can take logs as usual."""
    logw = np.log(wide)
    pre = logw[logw.index < POLICY]
    prof = pre.groupby(pre.index.month).mean()
    prof = prof - prof.mean()                      # pure seasonal shape, zero mean per unit
    adj = logw - prof.reindex(logw.index.month).to_numpy()
    return np.exp(adj)


# ---------------------------------------------------------------------------
# Main estimate
# ---------------------------------------------------------------------------
main = bt[bt["group"].isin(["treated", "control"])]
wide_raw = balanced(main)
wide = seasonal_adjust(wide_raw)
post = (wide.index >= POLICY)
treated_units = [u for u in wide.columns if u.split(" | ")[0] in TREATED]
control_units = [u for u in wide.columns if u.split(" | ")[0] in CONTROL]
beta = twfe(wide, treated_units, post)
beta_raw = twfe(wide_raw, treated_units, post)          # robustness: no seasonal adjustment

# inbound-only robustness: only the into-Manhattan direction of each tunnel
inbound = [u for u in treated_units if "to Manhattan" in u]
wide_in = wide[inbound + control_units]
beta_in = twfe(wide_in, inbound, post)

# ---------------------------------------------------------------------------
# Permutation inference
#  (a) placebo in space: treat each control facility (both directions) as if tolled
#  (b) placebo in time : pre-period only, fake policy dates, real treated units
# ---------------------------------------------------------------------------
space = []
for fac in sorted(CONTROL):
    fake = [u for u in control_units if u.startswith(fac)]
    rest = [u for u in control_units if not u.startswith(fac)]
    space.append({"placebo_facility": fac, "beta": twfe(wide[fake + rest], fake, post)})
space = pd.DataFrame(space)
space["effect_pct"] = pct(space["beta"])

pre = wide[wide.index < POLICY]
time_rows = []
for fake_date in pd.date_range("2023-07-01", "2024-07-01", freq="MS"):
    time_rows.append({"fake_policy_date": fake_date.date(),
                      "beta": twfe(pre, treated_units, pre.index >= fake_date)})
timep = pd.DataFrame(time_rows)
timep["effect_pct"] = pct(timep["beta"])

p_space = float((np.abs(space["beta"]) >= abs(beta)).mean())
p_time = float((np.abs(timep["beta"]) >= abs(beta)).mean())

# ---------------------------------------------------------------------------
# Event study: monthly treated-minus-control gap, relative to the pre-period average
# ---------------------------------------------------------------------------
logw = np.log(wide)
gap = logw[treated_units].mean(axis=1) - logw[control_units].mean(axis=1)
monthly = gap.groupby(gap.index.to_period("M")).mean()
monthly = monthly - monthly[monthly.index < pd.Period("2025-01", "M")].mean()
event = pd.DataFrame({"month": monthly.index.astype(str), "gap_log": monthly.values,
                      "gap_pct": pct(monthly.values)})
event.round(4).to_csv(OUT / "event_study_monthly.csv", index=False)
pre_months = event[event["month"] < "2025-01"]
# the same gap without seasonal adjustment, to show what the adjustment removes
logr = np.log(wide_raw)
gap_raw = logr[treated_units].mean(axis=1) - logr[control_units].mean(axis=1)
m_raw = gap_raw.groupby(gap_raw.index.to_period("M")).mean()
pre_sd_raw = float(pct(m_raw[m_raw.index < pd.Period("2025-01", "M")]).std())
post_months = event[event["month"] >= "2025-01"]

# ---------------------------------------------------------------------------
# Trend-adjusted estimate. The pre-period gap drifted down slightly in late 2024, and every
# fake-date placebo came out negative - a sign of a mild pre-existing trend that would
# flatter the headline number. Fit a linear trend to the daily treated-minus-control gap
# over the pre-period, extrapolate it, and measure the post-period gap beyond that trend.
# ---------------------------------------------------------------------------
days = (gap.index - gap.index[0]).days.to_numpy().astype(float)
pre_m = gap.index < POLICY
slope, intercept = np.polyfit(days[pre_m], gap.to_numpy()[pre_m], 1)
beyond = gap.to_numpy()[~pre_m] - (intercept + slope * days[~pre_m])
level = gap.to_numpy()[pre_m].mean()
beta_trend = float(beyond.mean())
trend_per_year_pct = slope * 365.25 * 100

# ---------------------------------------------------------------------------
# Diversion: did Manhattan crossings outside the zone absorb traffic?
# ---------------------------------------------------------------------------
sp = bt[bt["group"].isin(["spillover", "control"])]
wide_sp = seasonal_adjust(balanced(sp))
sp_units = [u for u in wide_sp.columns if u.split(" | ")[0] in SPILL]
beta_sp = twfe(wide_sp, sp_units, wide_sp.index >= POLICY)

# ---------------------------------------------------------------------------
# Durability: is the effect fading? Year 2 (2026) vs year 1 (2025) separately
# ---------------------------------------------------------------------------
y1 = wide[(wide.index < pd.Timestamp("2026-01-01"))]
y2 = wide[(wide.index < POLICY) | (wide.index >= pd.Timestamp("2026-01-01"))]
beta_y1 = twfe(y1, treated_units, y1.index >= POLICY)
beta_y2 = twfe(y2, treated_units, y2.index >= POLICY)

# ---------------------------------------------------------------------------
# Zone entries themselves (post-period only): mix and year-over-year persistence
# ---------------------------------------------------------------------------
crz = pd.read_csv(RAW / "crz_entries_daily_by_group_class.csv", parse_dates=["toll_date"])
crz["crz_entries"] = pd.to_numeric(crz["crz_entries"])
per = pd.read_csv(RAW / "crz_entries_daily_by_period_class.csv", parse_dates=["toll_date"])
per["crz_entries"] = pd.to_numeric(per["crz_entries"])
last = crz["toll_date"].max()
same_window_25 = (crz["toll_date"] >= "2025-01-05") & (crz["toll_date"] <= last - pd.DateOffset(years=1))
same_window_26 = (crz["toll_date"] >= "2026-01-05") & (crz["toll_date"] <= last)
d25 = crz[same_window_25].groupby(crz["toll_date"].dt.date)["crz_entries"].sum().mean()
d26 = crz[same_window_26].groupby(crz["toll_date"].dt.date)["crz_entries"].sum().mean()
yoy = (d26 / d25 - 1) * 100
cls = (crz.groupby("vehicle_class")["crz_entries"].sum() / crz["crz_entries"].sum() * 100).sort_values(ascending=False)
cls_yoy = (crz[same_window_26].groupby("vehicle_class")["crz_entries"].sum() /
           crz[same_window_25].groupby("vehicle_class")["crz_entries"].sum() - 1) * 100

# ---------------------------------------------------------------------------
# Transit (descriptive only: no untreated comparison exists for the subway)
# ---------------------------------------------------------------------------
rid = pd.read_csv(RAW / "mta_daily_ridership_traffic.csv", parse_dates=["date"])
rid["count"] = pd.to_numeric(rid["count"])
def avg(mode, a, b):
    m = rid[(rid["mode"] == mode) & (rid["date"] >= a) & (rid["date"] <= b)]
    return m["count"].mean()
transit = []
for mode in ["Subway", "Bus"]:
    base = avg(mode, "2024-01-05", "2024-09-20")
    y25 = avg(mode, "2025-01-05", "2025-09-20")
    y26 = avg(mode, "2026-01-05", "2026-09-20")
    transit.append({"mode": mode, "avg_daily_2024": base, "avg_daily_2025": y25, "avg_daily_2026": y26,
                    "change_2025_vs_2024_pct": (y25 / base - 1) * 100,
                    "change_2026_vs_2025_pct": (y26 / y25 - 1) * 100})
transit = pd.DataFrame(transit)

# ---------------------------------------------------------------------------
# Save + report
# ---------------------------------------------------------------------------
summary = pd.DataFrame([
    {"estimate": "Tunnels into zone vs non-Manhattan bridges (both directions)", "beta": beta, "effect_pct": pct(beta)},
    {"estimate": "Inbound direction only", "beta": beta_in, "effect_pct": pct(beta_in)},
    {"estimate": "Without seasonal adjustment", "beta": beta_raw, "effect_pct": pct(beta_raw)},
    {"estimate": "Net of pre-existing trend", "beta": beta_trend, "effect_pct": pct(beta_trend)},
    {"estimate": "Year 1 (2025) only", "beta": beta_y1, "effect_pct": pct(beta_y1)},
    {"estimate": "Year 2 (2026) only", "beta": beta_y2, "effect_pct": pct(beta_y2)},
    {"estimate": "Diversion: RFK + Henry Hudson vs non-Manhattan bridges", "beta": beta_sp, "effect_pct": pct(beta_sp)},
])
summary["panel_days"] = len(wide)
summary["pre_days"] = int((~post).sum())
summary["post_days"] = int(post.sum())
summary.round(5).to_csv(OUT / "did_summary.csv", index=False)
space.round(5).to_csv(OUT / "placebo_space.csv", index=False)
timep.round(5).to_csv(OUT / "placebo_time.csv", index=False)
pd.DataFrame([{"p_space": p_space, "p_time": p_time, "n_space": len(space), "n_time": len(timep),
               "max_abs_placebo_space_pct": float(np.abs(space["effect_pct"]).max()),
               "max_abs_placebo_time_pct": float(np.abs(timep["effect_pct"]).max()),
               "pre_period_gap_sd_pct": float(pre_months["gap_pct"].std()),
               "pre_period_gap_sd_unadjusted_pct": pre_sd_raw,
               "post_period_mean_gap_pct": float(post_months["gap_pct"].mean())}]).round(5).to_csv(
    OUT / "inference.csv", index=False)
pd.DataFrame({"vehicle_class": cls.index, "share_of_entries_pct": cls.values,
              "yoy_2026_vs_2025_pct": cls_yoy.reindex(cls.index).values}).round(3).to_csv(
    OUT / "crz_vehicle_mix.csv", index=False)
pd.DataFrame([{"avg_daily_entries_2025": d25, "avg_daily_entries_2026": d26, "yoy_pct": yoy,
               "window_end": last.date()}]).round(2).to_csv(OUT / "crz_yoy.csv", index=False)
transit.round(2).to_csv(OUT / "transit_descriptive.csv", index=False)

pd.set_option("display.width", 200)
print("=" * 92)
print("DIFFERENCE-IN-DIFFERENCES  (balanced panel: {} days, {} pre / {} post; {} treated units, {} control units)".format(
    len(wide), int((~post).sum()), int(post.sum()), len(treated_units), len(control_units)))
print("=" * 92)
print(summary[["estimate", "effect_pct"]].round(2).to_string(index=False))
print()
print("PERMUTATION INFERENCE")
print("  placebo in space ({} fake-treated control facilities): max |effect| {:.2f}%   p = {:.2f}".format(
    len(space), np.abs(space["effect_pct"]).max(), p_space))
print("  placebo in time  ({} fake policy dates, pre-period only): max |effect| {:.2f}%   p = {:.2f}".format(
    len(timep), np.abs(timep["effect_pct"]).max(), p_time))
print()
print("PRE-EXISTING TREND in the gap: {:+.2f} pts/year; effect net of trend {:.2f}%".format(
    trend_per_year_pct, pct(beta_trend)))
print("EVENT STUDY: pre-period monthly gap sd {:.2f} pts; post-period mean gap {:.2f}%".format(
    pre_months["gap_pct"].std(), post_months["gap_pct"].mean()))
print()
print("ZONE ENTRIES: avg daily {:,.0f} (2025) -> {:,.0f} (2026), same calendar window: {:+.2f}%".format(d25, d26, yoy))
print(pd.DataFrame({"share_pct": cls.round(1), "yoy_pct": cls_yoy.reindex(cls.index).round(1)}).to_string())
print()
print("TRANSIT (descriptive, not causal)")
print(transit.round(1).to_string(index=False))
