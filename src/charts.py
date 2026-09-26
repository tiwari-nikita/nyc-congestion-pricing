"""Charts for the congestion pricing analysis."""
import pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
BLUE, ORANGE, AQUA, RED = "#2a78d6", "#eb6834", "#1baf7a", "#e34948"
SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE = "#e1e0d9", "#c3c2b7"
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Segoe UI", "DejaVu Sans"],
                     "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "axes.edgecolor": BASELINE,
                     "axes.labelcolor": INK2, "text.color": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.titlesize": 13, "axes.titleweight": "bold", "font.size": 10})


def style(ax, xgrid=False):
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    ax.grid(axis="x" if xgrid else "y", color=GRID, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)


def titles(ax, t, sub):
    ax.set_title(t, loc="left", pad=32)
    ax.text(0, 1.03, sub, transform=ax.transAxes, color=MUTED, fontsize=9, va="bottom")


def save(fig, name):
    fig.savefig(OUT / name, dpi=150, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    print("wrote", name)


did = pd.read_csv(OUT / "did_summary.csv").set_index("estimate")
main = did.iloc[0]["effect_pct"]

# 1. Event study
ev = pd.read_csv(OUT / "event_study_monthly.csv")
ev["m"] = pd.PeriodIndex(ev["month"], freq="M").to_timestamp()
fig, ax = plt.subplots(figsize=(9.5, 4.8))
pre = ev["m"] < "2025-01-01"
ax.plot(ev.loc[pre, "m"], ev.loc[pre, "gap_pct"], color=MUTED, linewidth=2, marker="o", markersize=4, zorder=3)
ax.plot(ev.loc[~pre, "m"], ev.loc[~pre, "gap_pct"], color=ORANGE, linewidth=2.2, marker="o", markersize=4, zorder=3)
ax.axvline(pd.Timestamp("2025-01-05"), color=INK2, linewidth=1.2, linestyle="--")
ax.axhline(0, color=BASELINE, linewidth=1)
ax.text(pd.Timestamp("2025-01-20"), ax.get_ylim()[1] * 0.85 if ax.get_ylim()[1] > 0 else 1,
        "tolling begins\n5 Jan 2025", fontsize=9, color=INK2)
style(ax)
ax.set_ylabel("Tunnels vs comparison bridges\n(% gap vs 2023-24 average)")
titles(ax, "Traffic through the tunnels into the zone dropped, and stayed down",
       "Monthly gap, seasonally adjusted. Flat before the toll (sd 1.3 pts); estimated effect {:.1f}%.".format(main))
save(fig, "01_event_study.png")

# 2. Placebos
sp = pd.read_csv(OUT / "placebo_space.csv")
tp = pd.read_csv(OUT / "placebo_time.csv")
fig, ax = plt.subplots(figsize=(9, 3.8))
ax.scatter(sp["effect_pct"], np.full(len(sp), 1), s=70, color=MUTED, zorder=3, label="Fake-treated bridge")
ax.scatter(tp["effect_pct"], np.full(len(tp), 0), s=70, color=BASELINE, zorder=3, label="Fake policy date")
ax.scatter([main, main], [0, 1], s=160, color=ORANGE, marker="D", zorder=4, label="Actual estimate")
ax.axvline(0, color=BASELINE, linewidth=1)
style(ax, xgrid=True)
ax.set_yticks([0, 1])
ax.set_yticklabels(["13 fake dates\n(pre-period only)", "5 comparison bridges\ntreated as if tolled"], color=INK2)
ax.set_ylim(-0.6, 1.6)
ax.set_xlabel("Estimated effect on crossings (%)")
titles(ax, "No placebo comes close to the real effect",
       "Largest fake-bridge effect {:.1f}%, largest fake-date effect {:.1f}%, actual {:.1f}%".format(
           sp["effect_pct"].abs().max(), tp["effect_pct"].abs().max(), main))
ax.legend(frameon=False, loc="lower right", fontsize=9, labelcolor=INK2)
save(fig, "02_placebos.png")

# 3. Robustness of the estimate
rob = did.drop(index=did.index[-1])            # diversion shown separately
labels = ["Main estimate (both directions)", "Inbound to Manhattan only", "No seasonal adjustment",
          "Net of pre-existing trend", "Year 1 (2025)", "Year 2 (2026)"]
fig, ax = plt.subplots(figsize=(8.5, 4))
vals = rob["effect_pct"].to_numpy()
cols = [ORANGE, BLUE, BLUE, RED, AQUA, AQUA]
ax.barh(labels[::-1], vals[::-1], color=cols[::-1], height=0.55, zorder=3)
ax.axvline(0, color=INK2, linewidth=1)
style(ax, xgrid=True)
ax.set_xlim(min(vals) * 1.45, 1)
ax.set_xlabel("Effect on crossings vs comparison bridges (%)")
div = did.iloc[-1]["effect_pct"]
titles(ax, "Every specification shows a drop: roughly 2% to 4%",
       "Diversion test: crossings into Manhattan outside the zone changed {:+.1f}%, i.e. no displacement".format(div))
for i, v in enumerate(vals[::-1]):
    ax.text(v - 0.1, i, "{:.1f}%".format(v), va="center", ha="right", color=INK, fontweight="bold")
ax.tick_params(axis="y", labelcolor=INK2)
save(fig, "03_robustness.png")

# 4. Who stopped driving in
mix = pd.read_csv(OUT / "crz_vehicle_mix.csv")
mix = mix[mix["share_of_entries_pct"] >= 1].copy()
short = {"1 - Cars, Pickups and Vans": "Cars, pickups, vans", "TLC Taxi/FHV": "Taxis & ride-hail",
         "2 - Single-Unit Trucks": "Single-unit trucks", "4 - Buses": "Buses"}
mix["label"] = mix["vehicle_class"].map(short)
mix = mix.sort_values("yoy_2026_vs_2025_pct")
fig, ax = plt.subplots(figsize=(8.5, 3.8))
cols = [BLUE if v < 0 else ORANGE for v in mix["yoy_2026_vs_2025_pct"]]
ax.barh(mix["label"], mix["yoy_2026_vs_2025_pct"], color=cols, height=0.55, zorder=3)
ax.axvline(0, color=INK2, linewidth=1)
style(ax, xgrid=True)
ax.set_xlim(-10, 4)
ax.set_xlabel("Change in zone entries, 2026 vs same days of 2025 (%)")
yoy = pd.read_csv(OUT / "crz_yoy.csv").iloc[0]
titles(ax, "Private cars keep falling; taxis and ride-hail don't",
       "All zone entries {:+.1f}% year over year. Shares of entries: cars {:.0f}%, taxis & ride-hail {:.0f}%.".format(
           yoy["yoy_pct"], mix.set_index("label").loc["Cars, pickups, vans", "share_of_entries_pct"],
           mix.set_index("label").loc["Taxis & ride-hail", "share_of_entries_pct"]))
for i, (v, lab) in enumerate(zip(mix["yoy_2026_vs_2025_pct"], mix["label"])):
    ax.text(v + (0.2 if v >= 0 else -0.2), i, "{:+.1f}%".format(v), va="center",
            ha="left" if v >= 0 else "right", color=INK, fontweight="bold")
ax.tick_params(axis="y", labelcolor=INK2)
save(fig, "04_vehicle_mix.png")
