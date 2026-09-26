# Did NYC congestion pricing reduce traffic into the zone?

**Analysis memo · September 2026**
**Source:** MTA via New York State Open Data. Bridge and tunnel crossings (2023–Sept 2026), Congestion Relief Zone entries (Jan 2025–Sept 2026), daily ridership.

---

## Bottom line

**Yes, modestly and durably.** After tolling began on 5 January 2025, traffic through the two MTA tunnels that feed directly into the zone fell **2–4% relative to comparable MTA bridges**. The effect shows no sign of fading, and there's no evidence the traffic simply moved to other Manhattan crossings.

The range matters more than the headline. The standard estimate is −4.2%. The tunnels were already drifting slightly below the bridges in late 2024, and netting out that pre-existing trend gives −2.2%. The truth likely sits between the two.

## Design

This is a difference-in-differences natural experiment inside one agency's toll system.

- **Treated:** the Hugh L. Carey and Queens-Midtown tunnels, which deliver traffic straight into Manhattan below 60th Street. Both directions count, since a trip into the zone is also a trip out of it.
- **Comparison:** five MTA bridges that never touch Manhattan: Verrazzano-Narrows, Throgs Neck, Bronx-Whitestone, Cross Bay, Marine Parkway. Same toll system, weather and economy, and no exposure to the zone toll.
- **Held out:** the RFK and Henry Hudson bridges reach Manhattan outside the zone, so they could absorb diverted trips. They're tested separately rather than used as comparison.

The estimator is two-way fixed effects on log daily crossings over a balanced panel of 1,342 days (735 before tolling, 607 after), so shocks common to all crossings, such as weather, holidays and the economy, cancel out. Each crossing's own seasonal pattern is removed using pre-period months only. That matters: two of the comparison bridges serve the Rockaway beaches and surge every summer.

## Findings

| Specification | Effect on crossings |
|---|---|
| **Main estimate** (seasonally adjusted, both directions) | **−4.2%** |
| Inbound to Manhattan only | −4.1% |
| Without seasonal adjustment | −4.6% |
| Net of pre-existing trend | −2.2% |
| Year 1 (2025) only | −3.4% |
| Year 2 (2026) only | −5.4% |
| Diversion to RFK + Henry Hudson | **+0.1%** (none) |

**It's not a statistical artifact.** Treating each comparison bridge as if it had been tolled produces effects no larger than 2.0%. Pretending the toll started on 13 different dates in 2023–24 produces effects no larger than 2.1%. The main estimate is about twice either.

**Before tolling, the two groups moved together.** After seasonal adjustment, the monthly gap between tunnels and bridges varied by only ±1.3 points across 2023–24.

**Traffic didn't just relocate.** Crossings into Manhattan north of the zone were unchanged (+0.1%), so the toll deterred trips rather than rerouting them.

**Private cars are adjusting; taxis and ride-hail aren't.** Zone entries fell another 4.2% in 2026 compared with the same days in 2025. Private cars fell 7.4% while taxis and ride-hail rose 1.5%. That's consistent with for-hire vehicles paying a flat per-trip surcharge rather than the full entry toll.

**Subway ridership rose 9.3%** in the first nine months of 2025 compared with 2024. This is descriptive only: the subway has no untolled comparison, so it can't be attributed to the toll.

## Why the method matters

1. **The comparison group was chosen to be clean, not convenient.** Bridges that reach Manhattan outside the zone could gain diverted traffic and bias the comparison, so they're excluded and tested on their own.
2. **Seasonality nearly produced a false result.** Without adjusting each crossing's seasonal pattern, a fake mid-2023 "policy" looked as large as the real one. The adjustment cut pre-period noise from about ±6 points to ±1.3.
3. **Two treated facilities make conventional standard errors unreliable.** Inference comes from permutation, recomputing the estimate under every fake treatment. With only five comparison bridges, that test can't produce a fine-grained p-value; what it shows is that no placebo comes close.
4. **The pre-existing drift is reported, not buried.** Every fake-date placebo came out slightly negative, which pointed to a mild pre-trend. The trend-adjusted −2.2% is reported alongside the headline, and it's only slightly larger than the biggest placebo, so the lower end is the less certain one.

## So what

1. **For pricing policy:** a toll of this size shifts a few percent of trips through major entry points. It's meaningful but not transformative, and cities considering similar schemes should plan around low-single-digit effects on the facilities that bear the toll.
2. **For enforcement design:** the gap between private cars (−7.4%) and for-hire vehicles (+1.5%) says the per-trip surcharge doesn't carry the same deterrent. If reducing vehicle volume is the goal, that's the lever to revisit.
3. **For evaluation practice:** comparison-group choice and seasonal adjustment moved this estimate more than the choice of model did. Those choices deserve the scrutiny that model choice usually gets.

## Limitations

- **Tunnels only.** The Port Authority's Lincoln and Holland tunnels, and the free East River bridges, carry most zone traffic but aren't in MTA's crossing data. This estimate is for the two MTA tunnels.
- **Tunnel users get a toll credit.** Drivers who pay a tunnel toll receive a credit against the zone charge, so these facilities face a smaller net price increase than untolled entry points. The effect elsewhere may be larger.
- **The trend adjustment assumes a linear continuation** of a drift that could have ended on its own. That's why the result is a range, not a point.
- **Zone entries have no pre-period.** The 2025-versus-2026 comparison shows persistence, not the initial drop.
