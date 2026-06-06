---
name: shoe-speed-vs-effort
description: Generate the shoe-speed-vs-effort chart — a Plotly scatter of grade-adjusted pace (GAP) vs. average heart rate across the user's runs, coloured by shoe model, that reveals which shoes deliver "free pace" (faster at the same effort). Use this whenever the user asks to build, regenerate, or update the shoe chart / speed-vs-effort chart, asks which shoe is fastest or gives the most free pace, wants to compare gear or see whether a model is worth its price, or mentions the GAP-vs-HR shoe scatter. Pulls runs from Strava via the existing strava CLI (reusing its OAuth + cache), corrects for HR-monitor dropouts and interval sessions, and writes a self-contained HTML chart to viz/.
---

# Shoe speed vs. effort

This skill builds a four-chart page from the same per-run dataset. **Chart 1** answers "which of
my shoes actually make me faster?": every qualifying run on a **grade-adjusted-pace (GAP) vs.
average-HR** plane, coloured by shoe model — a shoe whose cluster sits higher (faster GAP) at the
same HR is giving free pace. **Chart 2** answers "is my aerobic fitness trending up?": each run's
**distance per heartbeat** (`1000 / (GAP × HR)`, grade-adjusted) over time, with a moving-median
line and a 25–75th percentile band. **Chart A** answers "does efficiency fade *during* a run, more
for some shoes?": one line per run of rolling m/beat vs distance *into* the run, with a per-shoe
median fade slope. **Chart B** answers "are a shoe's *longer runs* less efficient than its shorter
ones?": one dot per run, whole-run m/beat vs total distance, with a per-shoe fade trend line. Point
size is distance; distance-band / shoe-selector dropdowns, legend toggles, and
click-to-open-in-Strava make them explorable.

It exists because raw pace lies about shoes — hills, heat, fitness, and interval structure all
move pace independently of the gear. Grade-adjusting the pace and pinning effort to HR
controls for most of that, so what's left is closer to a fair shoe comparison. Two corrections
keep the comparison honest and are the reason this is a skill rather than a one-liner:

1. **Low-HR dropout flagging** (optional — see Bootstrap). A monitor that under-reads makes a
   run look like "fast pace at low effort", which would wrongly flatter whatever shoe was worn.
   Those runs are detected and pulled into a separate, hidden-by-default series.
2. **Interval/workout handling** (always on). A whole-run average for an interval session is a
   meaningless blend of fast reps and slow recoveries that lands in the "free pace" corner.
   Interval runs are re-plotted at their *work-rep* pace × mean per-rep max HR instead.
3. **Cardiac-drift HR adjustment** (optional — see Bootstrap). Longer-*duration* runs read a
   higher whole-run average HR for the same pace (HR creeps up with time on feet), pushing them
   rightward so they only compare fairly within one distance band. When on, the chart gains a
   **"HR axis: Raw / Drift-adjusted"** toggle that composes with the distance dropdown; see below.

The two CLIs do the work; this skill describes the first-run configuration and how to invoke
them. Output is an HTML file plus verbose stderr — run the build in a sub-agent (see
Invocation) so the per-run number-crunching stays out of the main thread.

## When to use

Reach for this skill when the user:

- asks to **build / regenerate / refresh the shoe chart** or "the speed vs effort chart".
- asks **which shoe is fastest**, gives the most free pace, or is worth keeping in the rotation.
- wants to **compare two shoes** on the same effort basis, or check whether a new model is
  actually faster than an old one.
- mentions the **GAP-vs-HR scatter** or a gear-comparison visualization.

If the user only wants gear *names*, total km per shoe, or rotation history, use the `strava`
skill (`strava gear <id>`) — this skill is the heavier, chart-building path.

## Bootstrap: `config/training.json` → `shoe_chart`

The build reads its tunables from a `shoe_chart` block in `config/training.json`. The scripts
fall back to sensible defaults if it's missing, but the **HR-dropout detection must be
configured deliberately** — it's the one piece that's wrong for most users out of the box. The
first time the user runs this without a `shoe_chart` block, walk them through this interview,
then write and commit the block.

The skill shares `config/training.json` with `characterize-activity` — `max_hr`, `hr_zones`,
`pace_zones`, and `gear` are already there if that skill has been set up. If they're not, run
its bootstrap first (this skill reads `hr_zones` and `gear`).

### Step 1 — the decisive question: HR-monitor history

Ask, plainly:

> **Have you had heart-rate monitor reliability problems** — a wrist-optical sensor that
> under-reads on cold days, a strap that drops out mid-run, anything that produces
> implausibly low HR for the pace?

- **No** → set `hr_correction.enabled = false`. **Skip the rest of the band questions.** The
  chart will plot every run as a clean per-shoe point with no ⚠ series. This is the right
  default for most people — don't talk them into detection they don't need.
- **Yes** → set `enabled = true` and ask **when they switched to a reliable monitor** (the date
  they started trusting their HR). Write that to `hr_data.monitor_order_date`. Detection only
  flags runs *before* that date; the switch-search window is derived as date + ~6 weeks.

### Step 2 — (only if enabled) confirm the detection bands

Two of the thresholds are **not stored in `shoe_chart`** — R1's and R2's average-HR ceilings
are read live from `hr_zones` (the `max` of the "easy" and "steady" zones). Tell the user this,
so they know that retuning a zone moves the rule. Then propose the explicit numbers and let them
confirm or edit. Defaults (which reproduce the reference athlete's tuned behaviour):

| Knob | Default | What it catches |
|---|---|---|
| `r1_gap_max` / (HR from easy zone) | GAP ≤ 5:00, avg HR < easy ceiling | easy-paced run with a suspiciously low average HR |
| `r2_gap_max` / (HR from steady zone) | GAP ≤ 4:45, avg HR < steady ceiling | fast run with a low average HR |
| `r4_gap_max` / `r4_maxhr` | GAP ≤ 5:00, max HR < 155 | fast effort whose *peak* HR never got plausibly high |
| `resid_drop_bpm` / `resid_z` | 10 bpm / −2σ | run sitting below the athlete's own HR-vs-GAP trend (data-driven, R3) |
| `rep_drop_below_best`, `rep_fast`, `rep_easy` | 20 bpm; 4:15→150; 5:00→135 | interval work reps whose max HR is impossibly low |

The residual rule (R3) is **self-calibrating** — it fits an HR≈a+b·GAP trend on the user's own
recent trusted runs (Theil–Sen), so it adapts to fitness without any per-user number. The
explicit bands above are backstops for dropouts severe enough to bias that trend. If `hr_zones`
aren't set yet, point the user at `characterize-activity`'s bootstrap before continuing.

### Step 3 — confirm the chart knobs

Offer defaults: `window_days` (520 ≈ 18 months of history), `min_distance_km` (2.0), and
`distance_bands_km` (`[12, 20, 35]` → the dropdown's ≤12 / 12–20 / 20–35 / >35 km bands). Adjust
to the user's typical distances if they have a strong opinion.

Also offer the **cardiac-drift adjustment** (`hr_drift`): when on, the chart fits a drift
coefficient (bpm per minute on feet) from the user's own trusted runs and adds a "HR axis:
Raw / Drift-adjusted" toggle so runs of different distances compare on one effort scale. It
defaults to `hr_correction.enabled` (it shares the same trusted population), needs at least
`min_trusted` (default 8) trusted runs to fit, and never hardcodes a coefficient. Leave it on
unless the user only ever compares same-distance runs.

And the **intra-run efficiency** block (`intra_run_efficiency`, powers Chart A): when on,
`build_dataset` stores a per-run rolling m/beat series (vs distance into the run) plus a fade
slope, so the within-run-fade chart can be drawn. Knobs: `downsample_points` (≈30 points/run),
`smooth_window_s` (90 s rolling window), `warmup_trim_km` (0.6 km dropped so the HR-from-rest ramp
doesn't fake a downslope), `min_points` (6). Defaults on; set `enabled: false` to drop Chart A and
the extra series. Steady runs only.

### Step 4 — write and commit

Write the `shoe_chart` block into `config/training.json` and commit it
(`git add config/training.json && git commit -m "..."`). It's part of the notebook — the chart's
detection behaviour at any point in history is defined by what this file said then.

A complete block:

```json
"shoe_chart": {
  "window_days": 520,
  "min_distance_km": 2.0,
  "distance_bands_km": [12, 20, 35],
  "hr_correction": {
    "enabled": true,
    "anchor_window_days": 120,
    "resid_drop_bpm": 10.0,
    "resid_z": -2.0,
    "fast_gap_max": 5.0,
    "r1_gap_max": 5.0,
    "r2_gap_max": 4.75,
    "r4_gap_max": 5.0,
    "r4_maxhr": 155,
    "rep_drop_below_best": 20,
    "rep_fast": {"pace": 4.25, "maxhr": 150},
    "rep_easy": {"pace": 5.0, "maxhr": 135}
  },
  "hr_drift": {
    "enabled": true,
    "min_trusted": 8
  },
  "intra_run_efficiency": {
    "enabled": true,
    "downsample_points": 30,
    "smooth_window_s": 90,
    "warmup_trim_km": 0.6,
    "min_points": 6
  }
}
```

For a user with no monitor history, the whole `hr_correction` block collapses to
`{"enabled": false}` — the other keys are ignored — and `hr_drift` likewise defaults off (so the
HR-axis toggle is hidden).

## Invocation

Two commands, run in order. **Run the build in a separate sub-agent (the Agent tool)** — it
fetches/streams up to a few hundred activities and prints a long per-run diagnostic to stderr;
that volume belongs off the main thread, exactly like `characterize-activity`. Have the
sub-agent report back a short summary (runs included, n flagged, n intervals) and the output
path. The render step is quick and can run in the main thread or the same sub-agent.

```bash
# 1. Build the dataset (cache-first; only fetches activities the strava cache lacks)
.claude/skills/shoe-speed-vs-effort/build_dataset.py
#    → .cache/shoe-speed-vs-effort/dataset.json

# 2. Render the chart
.claude/skills/shoe-speed-vs-effort/render.py
#    → viz/shoe-speed-vs-effort.html
```

A reasonable sub-agent prompt:

> Run `.claude/skills/shoe-speed-vs-effort/build_dataset.py` then
> `.claude/skills/shoe-speed-vs-effort/render.py`. Report back: how many runs were included and
> skipped, how many were flagged as low-HR suspects, how many interval sessions were
> classified (and how many had rep-HR dropouts), and the chart's output path. Don't paste the
> dataset JSON.

Both scripts shell out to `.claude/skills/strava/strava.py`, so OAuth refresh and the on-disk
cache (`.cache/strava/`) just work — if `strava whoami` works, these work. The build also reads
`config/training.json` (the `shoe_chart` block + `hr_zones` + `gear`).

## Reading the page

The HTML page carries **four stacked charts** built from the same dataset and the same shoe
colour map (a shoe is the same colour across all of them). Chart 1 is the shoe comparison; chart 2
is the efficiency-over-time trend; Chart A is within-run efficiency fade; Chart B is efficiency vs
run length.

### Chart 1 — shoe speed vs. effort (GAP vs. HR)

- **Axes:** x = average HR (right = harder); y = grade-adjusted pace, axis reversed so
  **faster is up**. A shoe sitting up-and-left of another at the same HR is giving free pace.
- **Colour** = shoe model; **point size** ∝ distance.
- **Series (toggle in the legend):** per-shoe circles are clean steady runs. `◆ Interval
  (work-rep)` diamonds are workout sessions plotted at their work-rep effort. The `⚠` series
  (suspect HR rings, interval rep-dropout diamonds) are **hidden by default** and only appear
  when HR correction is enabled — click them in the legend to reveal. They're flagged precisely
  because they'd otherwise sit at a misleadingly easy spot.
- **Distance-band dropdown** (top-left) filters every series to a band.
- **HR-axis toggle** (next to the distance dropdown, only when `hr_drift` is on): switches x
  between raw average HR and **drift-adjusted HR** — every run normalised to the reference
  duration (shown in the axis title) using the fitted bpm/min coefficient, so long and short
  runs sit on one comparable effort scale. The adjustment clamps each run's duration to the
  fitted range, so an ultra isn't shifted by a fantasy amount. The two controls compose
  (band ∩ HR-mode), and the **hover always shows the real measured HR**, not the adjusted value —
  the adjustment is a plotting-axis transform, not a claim about what the watch recorded.
- **Faint halo on very long runs.** A run longer than the drift fit's duration ceiling had its
  adjustment capped, so it's under-corrected and genuinely out of regime (GAP also can't capture
  an ultra's walking/terrain/fuelling cost). Such runs get a subtle open ring — read their
  position with caution; it's not a shoe verdict. Toggle "drift adj. capped" in the legend.
- **Click any point** to open that activity in Strava.

When summarising for the user, lean on the steady per-shoe clusters and the interval diamonds;
treat the ⚠ series as "probably bad data", not evidence about a shoe.

### Chart 2 — aerobic efficiency over time (distance per heartbeat)

- **What it is:** one dot per activity of **grade-adjusted metres per heartbeat** =
  `1000 / (GAP × HR)` against the run's date. More distance per beat = fitter, so **up = better**
  (this y-axis is *not* reversed). Intervals use the work-rep `GAP × mean per-rep max-HR`, the
  same normalisation chart 1 uses, so a workout sits at its true effort.
- **Colour** = shoe model (shared with chart 1); **point size** ∝ distance; **diamonds** are
  intervals.
- **Trend line + band:** a ~45-day **moving median** with a shaded **25–75th percentile** band,
  fitted over *all* clean activities (steady and interval). The `⚠` sensor-dropout suspects are
  **excluded** from the trend (a low-HR drop fakes high efficiency) and shown only as the
  hidden-by-default legend series.
- **HR-basis dropdown** (top-right, only when `hr_drift` is on): switches the whole chart — dots,
  moving median, and band — between m/beat from **raw** HR and from **drift-adjusted** HR. The
  adjustment removes cardiac drift (HR creeps up with time on feet), so long runs move *up* to
  their drift-free efficiency and a long-run-heavy stretch no longer drags the trend down. The
  hover still shows the measured HR; the y-axis title updates to say which basis is plotted.
- **Reading it:** expect the line to **rise through a build** (fitness) and dip on heat-, long-run-,
  or interval-heavy stretches. It's a same-shoe-agnostic fitness trend, not a gear verdict — for
  "which shoe", read chart 1. **Click any point** to open it in Strava.

### Chart A — efficiency fade *within* a run (m/beat vs distance into the run)

- **What it is:** one thin **line per run** of rolling grade-adjusted m/beat against distance
  *into* the run — so you watch efficiency decay as the run goes on. Steady runs only (intervals
  are sawtooth, not a fade line). The opening **warmup (`warmup_trim_km`, default 0.6 km) is
  trimmed** — the HR-from-rest ramp would otherwise fake a downslope on every run.
- **Per-shoe summary:** a **bold segment** per shoe = its **median fade slope** through the shoe's
  median run, with the slope (m/beat per **10 km**, − = fades) and run count in the legend, so the
  legend doubles as a fade ranking.
- **Shoe selector** (top-left dropdown): *All shoes* shows only the per-shoe **summary segments**
  (the clean cross-shoe comparison, not 200+ raw lines); pick a shoe to reveal **its individual run
  lines** plus its summary. **Click any run line** to open it in Strava.
- **Reading it:** terrain is removed by GAP and cardiac drift is athlete-level (common to all
  shoes), so the *between-shoe* differences in slope are the closest thing to a shoe effect — a
  shoe whose segment droops more loses efficiency faster as the run wears on. Caveat: the slopes
  are small and bounded by the runs you actually did in each shoe (a shoe only raced short can't
  show a long-run fade), so read it as a hypothesis generator, not a verdict.

### Chart B — efficiency vs run length (whole-run m/beat vs total distance)

- **What it is:** one **dot per run** of whole-run m/beat (`1000/(GAP×HR)`) against the run's
  **total distance** — "are a shoe's longer runs less efficient than its shorter ones?" Steady
  runs only; the "Unbranded Okategoriserat" placeholder is excluded. Point size ∝ distance.
- **Per-shoe trend line:** a robust (Theil–Sen) fit for any shoe with ≥5 runs spanning ≥8 km, with
  the slope (per 10 km) in the legend.
- **Shoe selector** + (when `hr_drift` is on) a **Raw / Drift-adjusted m/beat** toggle. They
  compose (the selector sets visibility, the toggle swaps y) because they touch different
  attributes. **Raw** includes the universal cardiac drift (longer runs read lower m/beat for
  everyone); switch to **drift-adjusted** to strip that out so any remaining downslope is
  shoe-specific. GAP assumes outdoor grade — treadmill-heavy models (one `model_label` can merge
  treadmill + outdoor pairs) read with caution. **Click any point** to open it in Strava.

When summarising Charts A/B for the user: the fade slopes are differential signals across shoes,
heavily caveated by sample size and the distance range each shoe was actually run over.

## What NOT to do

- **Don't commit the dataset or gear cache.** They live under `.cache/shoe-speed-vs-effort/`
  (gitignored, regenerable). Only `viz/shoe-speed-vs-effort.html` is a committable artifact.
- **Don't enable HR correction for a user who hasn't reported monitor problems.** It will flag
  legitimately easy or well-paced runs as "suspect" and confuse the picture. Default to off.
- **Don't hand-edit the R1/R2 HR ceilings in `shoe_chart`** — they aren't there. Change the
  `hr_zones` easy/steady ceilings instead; the rule follows.
- **Don't read a ⚠-flagged point as a verdict on a shoe.** A flagged run is suspected bad HR
  data; it says nothing about the gear worn that day.
- **Don't run the build in the main thread.** Use a sub-agent — the stderr diagnostic and the
  activity crunching are not main-thread context.
- **Don't extend this to write to Strava.** Read-only by design, like the other skills here.

## Edge cases

- **No `shoe_chart` block / partial block.** The scripts fall back to built-in defaults per key,
  so they still run — but HR correction stays off unless `hr_data.monitor_order_date` is set.
  Treat a first run without the block as the trigger to do the Bootstrap interview.
- **A new shoe since the last run.** `build_dataset.py` resolves unknown `gear_id`s via
  `strava gear <id>` and caches the friendly name; no manual step needed for the chart (though
  the gear-tracking convention in CLAUDE.md still applies to sync files).
- **Runs with no HR or no streams.** Skipped (counted in the build's `skipped` tally) — they
  can't be placed on the HR axis.
- **Very few runs (< 5 usable).** The HR-vs-GAP trend can't be fit, so dropout detection flags
  nothing and the build says so. The chart still renders from whatever runs exist.
