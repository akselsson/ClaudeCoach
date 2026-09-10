---
date: 2026-09-10
type: activity-sync
summary: Thu Sep 10, the Gate 1 day. Wednesday's sentinel jog was skipped, so this was the first run since the Sep 4 febrile Ursvik. Run as prescribed it was not — 10.1 km rolling loop at 4:59/km, HR 152 avg, finishing 4:32/km @ 160 — but read against the right references it is a reassuring session, not a failed gate. Also records a methodological correction: the first characterization of this run overstated both GAP and HR drift, and the error is documented here so future sessions don't repeat it.
---

# Thu Sep 10 — the Gate 1 run

**Activity 20115667156** · 10.12 km · 50:15 · 4:59/km · HR 152 avg / 170 max · +328 / −335 m (Strava reports 234 m gain) · TRIMP 111 / Edwards 141 / suffer 88 · **Gear: ASICS Superblast 3**

Prescribed (`../schedule/2026-09-07-post-illness-ll-represcription.md`): easy 40–50 min on **flat road**, gate criterion ~5:10–5:20/km at **≤145 bpm without ramping**. What happened: a rolling loop with 23 m of climbing per km, run as a progression finishing at 4:32/km.

Patrik's own read: *"Failed to keep both tempo and heart rate down but I think that's mostly because legs are fresh."*

## Per-kilometre

| km | raw | GAP | HR | Δalt |
|---|---|---|---|---|
| 1 | 4:57 | 4:58 | 137.5 | −8 |
| 2 | 5:09 | 5:11 | 146.9 | −3 |
| 3 | 5:07 | 5:04 | 149.7 | −8 |
| 4 | 5:36 | 4:25 | 149.3 | **+31** |
| 5 | 4:58 | 5:24 | 147.2 | −22 |
| 6 | 5:24 | 4:41 | 157.7 | +20 |
| 7 | 4:55 | 4:48 | 154.2 | −7 |
| 8 | 4:43 | 5:02 | 152.4 | −15 |
| 9 | 4:35 | 4:32 | 160.5 | 0 |
| 10 | 4:57 | 4:27 | 162.6 | +14 |

Thirds (warm-up excluded): GAP **5:02 → 4:49 → 4:41**, HR **148.2 → 153.0 → 158.1**. This is a progression run. A large part of the HR rise is simply running harder.

## The cleanest gate reading

**km 2–4: raw 5:16/km, GAP 5:13/km — actual gate pace — at HR 148.6.**

Against the matched-GAP references in `2026-09-07-illness-week-sync.md`:

| | GAP ~5:05–5:15 | HR |
|---|---|---|
| Aug 28 (healthy, post-ultra) | 5:05–5:12 | 136–144 |
| **Sep 10 (today)** | **5:13** | **148.6** |
| Sep 4 (febrile) | 5:05–5:12 | 151–158 |

Above the healthy band, below the febrile band. Read in isolation that is a marginal fail of the ≤145 clause. Read against training state (below) it is close to what four weeks of near-zero running predicts on its own.

## Drift

At matched grade-adjusted pace, first half vs second half:

| GAP band | 1st half | 2nd half | Δ | sample |
|---|---|---|---|---|
| 4:50–5:20 | 148.1 | 155.2 | +7.1 | 404 s / 329 s |
| 4:40–5:10 | 148.0 | 155.7 | +7.7 | 339 s / 350 s |
| 4:30–5:00 | 148.0 | 156.6 | +8.6 | 277 s / 398 s |

~7–8 bpm across 45 minutes, stable across three bands whose selection biases point in opposite directions (in the 4:30–5:00 band the early samples are the fast moments, the late samples sit near the actual late average). So the shift is real, but it is modest — ordinary cardiac drift over 50 minutes in an afternoon run accounts for much of it.

## ⚠️ Methodological correction — do not repeat this

The first pass at this activity (a `characterize-activity` sub-agent run) reported **"identical pace, identical grade band, +10.4 bpm"** across three segments at 5:03/5:01/5:03 per km. Patrik caught it: km 7–10 were run at 4:42 / 4:39 / 4:32 / 4:53. A 5:03 bucket cannot describe that running.

The cause: the cut filtered stream samples to `|grade| < 2%` **and** a 4:50–5:20/km pace band, then averaged. In the back half that kept **23 and 30 samples — 73 s and 92 s** out of ~5-minute segments, versus 226 s in the first third. It was pairing late-run heart rate with the slowest, most-decelerated moments of fast kilometres.

Three lessons for future analyses:

1. **Always print sample counts and elapsed seconds alongside any filtered HR comparison.** A matched-pace claim built on 73 seconds is not a matched-pace claim.
2. **GAP was inflated.** The sub-agent reported a whole-run GAP of 4:28/km against 4:59 raw — a 31 s/km credit for a net-zero loop. A Minetti cost-ratio model gives ~4:50/km, i.e. ~8 s/km, which is what +328/−335 m over 10 km should buy. Treat any GAP that improves raw pace by >10% on rolling terrain as suspect. `characterize.py` has **no GAP implementation** — any GAP figure in a report is the sub-agent's own ad-hoc model and needs its method stated.
3. **HR-on-speed regressions on progression runs are worthless.** Both the sub-agent's `+2.1 bpm/km` and a recomputed `+1.83 bpm/km` came from models fitting ~2 bpm per m/s of grade-adjusted speed — physiologically impossible. HR lags effort, so on a progression the regression assigns nearly nothing to speed and dumps the whole effort increase into the "drift" residual. Use matched-band comparisons with declared sample sizes instead.

## Gate 1 verdict, and the training-state reframe

The other gate clauses, from Patrik on the day: **resting HR 46** (baseline 44), **no niggles** — right hip flexor silent. Wednesday's sentinel jog *"just fell out of schedule"*, not a symptom.

The decisive context is training state, not illness:

| week | run km |
|---|---|
| Jul 13 | 109 |
| Jul 20 | 96 |
| Jul 27 | 78 |
| Aug 17 | 2 |
| Aug 24 | 34 |
| Aug 31 | 17 |
| Sep 7 | 10 |

**Four weeks at 2 / 34 / 17 / 10 km, against 96–109 km six weeks ago.** Patrik's own read, and it is the right one: *"My resting HR is never as low as 44 unless I'm in a higher volume period. That also goes for the running HR."* A resting HR of 46 measured off four weeks of near-zero running is a training-state readout, not a fever residue — and the same mechanism (plasma volume, stroke volume) fully covers +5 bpm at matched pace and elevated drift.

**Gate 1: passed, on the criteria that matter.** No fever, no chest symptoms, no niggle, resting HR within 2 of a baseline that is itself volume-dependent, and 50 minutes to HR 170 tolerated without incident. The ≤145-at-5:15 clause was written to detect residual illness; it is now measuring detraining, which is a different problem with the opposite treatment.

The illness chapter is closed. Forward consequences in `../schedule/2026-09-10-volume-rebuild.md`.
