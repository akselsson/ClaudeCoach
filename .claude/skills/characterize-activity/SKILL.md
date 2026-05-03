---
name: characterize-activity
description: Characterize a single Strava activity numerically — effort level, what it primarily trained, lap structure, time in HR/pace zones, and training-load contribution (TRIMP, Edwards, suffer score). Use this whenever the analysis or review needs more than averages: classifying a run as recovery / easy / steady / tempo / threshold / vo2-or-race, deciding whether a logged "easy" run was actually a quality session, deciding how much load a session contributed, or describing a workout's structure for a weekly review. Especially valuable when `max_heartrate − average_heartrate` is large, when a description hints at structure ("4 x 1 km", "tröskel", "intervals", "fartlek", "tempo"), when a run was unexpectedly hard or long, or when a previous review classification looks suspect. Pulls activity detail and streams via the existing strava CLI (reusing its OAuth + cache).
---

# Characterize an activity

This skill turns one Strava activity into a structured characterization: effort tag, primary training focus, time-in-zone histogram, training-load numbers, lap-structure classification, and HR/pace drift. It exists because activity-level averages routinely hide the truth — a 60 min run with average HR 154 might be steady aerobic, or it might be a 2×3 km tröskel buried in warm-up and cool-down. Coaching off averages produces confident-sounding wrong answers.

The CLI (`characterize.py`) does the math; this skill describes when to invoke it and how to read its output. Output is JSON on stdout; never paste it into analyses — summarise.

## When to use

Reach for this skill when:

- Writing or revising a weekly review and you need to characterize a specific session beyond "easy" or "long".
- A run's `max_heartrate − average_heartrate` is ≥25 bpm — strong sign of hidden quality.
- The description has interval markers (×, x, "tröskel", "threshold", "intervals", "fartlek", "tempo") or pace targets.
- Suffer score is high relative to distance (e.g. 60+ on a 7–10 km run).
- A run came in much faster, longer, or with higher HR than the prior plan called for, and you need to decide how much "extra load" it represented.
- Drilling into a long run to check for fade / cardiac drift before deciding whether the next long run can step up.
- The `weekly-training-review` skill has flagged a session and you need to ground the discussion in numbers, not impressions.

If you only need volume totals or a list of recent activities, prefer the `strava` skill directly — this one is heavier and meant for per-session analysis.

## Bootstrap: `config/training.json`

The CLI needs a project-scoped training profile (max HR, resting HR, HR zone bands). The first time it runs without one, it errors with a pointer back here. Set it up before invoking analysis:

1. **Ask the user for max HR.** Frame it as "the highest HR you've actually seen in training/racing in the last year, not a 220-minus-age estimate". A typical race-end-of-5k value is fine. Without this, TRIMP is meaningless.

2. **Ask for resting HR.** Morning resting HR if known. If they don't track it, default to 50 and tell them TRIMP is approximate. (Edwards load and time-in-zone don't depend on resting HR — they're still accurate.)

3. **Propose a zone scheme.** Read the most recent `analyses/*-block-*.md` and reuse whatever HR bands it documents. Today that file's "HR zones" section says:
   - Easy: HR <140
   - Steady aerobic: HR 140–150
   - Threshold: HR 155–165
   - Race-effort cap (this block): HR 160

   The CLI wants 4–6 contiguous zones covering the whole range. Fill the gaps using the user's existing language plus %-of-max heuristics for anything not in the block plan. A reasonable proposal that matches the current block:

   ```json
   {
     "max_hr": 188,
     "resting_hr": 50,
     "hr_zones": [
       {"name": "easy",      "min": 0,   "max": 140},
       {"name": "steady",    "min": 140, "max": 150},
       {"name": "tempo",     "min": 150, "max": 155},
       {"name": "threshold", "min": 155, "max": 165},
       {"name": "vo2",       "min": 165, "max": 999}
     ]
   }
   ```

4. **Show the proposal back to the user verbatim, ask "does this look right?"** Adjust based on their answer — they'll know whether their personal threshold band is 155–165 or something else better than any heuristic does.

5. **Write `config/training.json`** with the agreed values. Then commit it (`git add config/training.json && git commit -m "..."`). The file is part of the notebook — a future Claude reading old analyses needs to know what zones they were written against.

When zones change between training blocks (post-race fitness shift, threshold drift), edit `config/training.json` and commit again. Old analyses stay valid because they were written against the zones in effect at that time; that's why the file is checked in alongside them.

## Invocation

```bash
.claude/skills/characterize-activity/characterize.py <activity-id>
```

Optional flags: `--resolution {low,medium,high}` (stream resolution, default `medium`), `--refresh` (force-refetch detail+streams from Strava), `--config <path>`, `--strava <path>`.

The CLI shells out to `.claude/skills/strava/strava.py activity` and `… streams`, so the on-disk cache (`.cache/strava/`) and OAuth refresh just work — no extra setup. If `strava whoami` works, `characterize.py` works.

```bash
# typical use
.claude/skills/characterize-activity/characterize.py 12345678901

# pipe through jq to surface just the headline
.claude/skills/characterize-activity/characterize.py 12345678901 \
  | jq '{effort: .effort.rating, focus: .primary_focus,
         load: .load, hr_zone_pct: [.hr_zones[] | {name, pct}]}'
```

## Reading the output

The output JSON groups fields by what they answer.

### `effort.rating` and `primary_focus` — the headline

Use these as the single-sentence characterization in the analysis. Effort tags from low to high stimulus:

| `effort.rating` | What it means |
|---|---|
| `recovery` | ≥80 % time in easy zone, peak HR <85 % of max. Don't claim it added training load. |
| `easy_aerobic` | ≥70 % in easy zone. Standard aerobic maintenance. |
| `steady_aerobic` | Bulk of time in steady zone, little above. Long-run / medium-long territory. |
| `tempo` | ≥30 % above steady but not enough at threshold to call it a threshold session. |
| `threshold` | ≥15 % at/above threshold zone. A real quality stimulus. |
| `vo2_or_race` | ≥10 % above threshold. Race effort or VO2max work. |

The thresholds are intentionally calibrated to filter incidental HR pushes. A 60 min run with one 2-min hill push will register ~3 % above threshold — that doesn't make it threshold work. If you think the rating looks off, look at the `rationale` and `hr_zones` for the underlying numbers; the tag is a summary, not a verdict.

`primary_focus` combines effort + structure + duration into one tag. The full vocabulary:

- `recovery`
- `easy_aerobic`, `steady_aerobic`
- `long_endurance` — easy/steady ≥90 min
- `tempo_continuous`, `tempo_intervals`
- `long_with_tempo` — tempo effort but ≥90 min run (long run with lifted finish)
- `threshold_continuous`, `threshold_intervals`
- `long_with_threshold` — threshold effort but ≥90 min run (progression long run, race-pace block in a long run, etc.)
- `vo2max_intervals`, `race_or_hard_continuous`
- `race_or_hard_long` — vo2/race effort sustained ≥90 min (an actual race or a hard long workout)

The `long_with_*` tags exist because the dominant stimulus of a 90+ min run is aerobic; you should describe a 2-hour run with a 20-minute threshold finish as both long *and* threshold, not as a flat threshold session. Read the long-run tag literally — "this run was long, *and* it had quality" — when summarising for an analysis.

### `hr_zones` — ground the percentages

Use this when the analysis needs to say "spent a third of the run above easy" or "11 minutes at threshold". Quote the percentages directly; don't round in ways that change the story (38 % is not "about half").

Easy run sanity check: pct of zone 0 (easy) should be high, everything above tempo near zero. If a run is logged as easy but `hr_zones[0].pct` is 45 %, that run is not easy — call it out.

### `pace_zones` — relative effort histogram, not a prescription

Pace zones are derived from the run's own median pace, not from absolute pace targets. Bands: `very_fast` / `fast` / `steady` / `easy` / `very_easy` (multipliers around the median). Use them to describe pace variation — a run with most time in `steady` was paced flat; a run with substantial `very_fast` plus `very_easy` time has interval-like pace structure. **Do not** quote these as if they were absolute pace zones; the user does not coach by absolute pace.

### `structure` — was this intervals?

`classification` is one of:

- `steady`: low pace variation, no clear pattern — most aerobic runs.
- `intervals`: high pace variation **and** many transitions across median (sawtooth).
- `progression` / `negative_split` / `positive_split`: monotonic pace shift.
- `mixed`: some variation but no clean structure.
- `unknown`: laps missing or insufficient.

If `classification = intervals`, the `interval_guess` block has heuristic work-rep count and durations. **Trust this only when the user laps deliberately.** A 6×400m repeats workout where the watch auto-laps every 1 km will look uniform and classify as `steady` even though it was clearly intervals — you'll need the description and the HR drift to catch those. Conversely, if the user lapped the warm-up + each rep + cool-down, `interval_guess.work_reps` should match the prescription closely.

`lap_pace_cv`, `transitions`, and the first/second-half pace numbers in `structure` are computed from raw lap data and can be skewed by very short transition laps (a 25 m segment captured between reps will show as a "lap" with absurd pace). When the half-pace numbers in `structure` look impossible, prefer the `drift` section's first/second-half values — they're computed from the streams with walking samples filtered.

### `load` — relative, not absolute

Three numbers, all heuristics:

- `trimp` — Banister TRIMP (HR-time integral, weighted exponentially toward higher HR). Depends on max HR + resting HR being right.
- `edwards` — Sum of (minutes-in-zone × zone-index). Doesn't depend on max HR estimate; maps cleanly onto the configured zones.
- `strava_suffer_score` — Strava's own number, passed through.

**Numbers don't have meaning in isolation.** "TRIMP 142" is meaningless without comparison. Use them to compare sessions within a review (this threshold session contributed ~3× the load of last Tuesday's easy run) or to flag outliers (today's run logged twice the suffer of any other run this week — investigate). Don't quote them as absolute fitness measures.

### `drift` — fade and cardiac drift

`hr_per_km_bpm` is the slope of HR vs. cumulative distance. On a steady-paced run, anything ≥1.5 bpm/km is meaningful cardiac drift — heat, hydration, fatigue, or overreaching. On a progression run with rising pace, drift is expected and not a concern by itself.

`pace_per_km_s` is the slope of pace vs. distance. Negative = sped up (negative split). Positive = slowed down. Read together with the HR slope: pace slowing while HR climbs is the classic "ran out of legs" pattern.

`first_half_avg_*` / `second_half_avg_*` are the cleaner version of the same question for casual reads.

## What NOT to do

- **Don't paste the JSON into `analyses/`.** Per the project's CLAUDE.md, analysis files are summaries — pull, characterize, summarize. Reference the activity id, not the dump.
- **Don't treat TRIMP / Edwards as authoritative.** They're heuristics; they don't replace the user's subjective state. If TRIMP says light but the user says wrecked, the user is right.
- **Don't trust `interval_guess` if you can't confirm the user laps deliberately.** Cross-check against the description. If the description says "4 x 1 km" and `work_reps = 4`, fine. If `work_reps = 12` on a steady run, ignore the block.
- **Don't fall back to averages when this CLI has surfaced a finer-grained answer.** If `effort.rating = threshold` but the avg HR was 148, the avg-HR call was the wrong call. Trust the time-in-zone read.
- **Don't run this on every activity in a review.** It's per-session drilldown. For volume sweeps, use `strava recent` / `strava weekly-volume`.
- **Don't extend this skill to write to Strava.** Read-only by design, like the strava skill.

## Edge cases

- **No streams (very old activity, manual entry).** HR zones, TRIMP, drift, and pace zones will be empty/zero. `effort.rating = unknown`. Lap-based `structure` may still work if laps exist. Note in the analysis that the data was unavailable.
- **No HR data (watch-less ride).** Same as above for HR-derived fields. Pace zones and lap structure still work.
- **Cycling / non-Run activities.** HR and load math still work; pace zones are computed but less informative because cycling pace ≠ running pace. Treat the pace-zone histogram cautiously for rides.
- **Walked/hiked sections (a long run with steep terrain).** Walking samples (velocity <1.4 m/s) are excluded from pace zones and pace drift, but kept in HR zones — a hill walk still imposes cardiovascular load.
- **Auto-1km laps with short intervals (e.g. 6×400m).** Lap classification will likely return `steady` even though the run was clearly intervals. Use the description and a higher HR-stream resolution to catch these.
- **Activities younger than ~2 days.** The strava CLI bypasses its cache for these (the user may still be editing description). Output will reflect whatever's on Strava right now.
