---
date: 2026-05-24
type: activity-sync
summary: Sun May 24 daughter run — 21.2 km, 2:27 moving, avg HR 122.8 (cleaned), 236 m gain (id 18633097580). The planned ~21 km Z1 with daughter, executed exactly to prescription. After stripping the km-17 strap-handoff artifact (daughter borrowed the strap; 191 s window, t=7261–7574), 99.9% of the run sat <140 — the headline "max 171" is not real. Negative HR drift across halves (125 → 119) while pace slowed (6:28 → 6:49) — daughter tired, not the runner. No heat signature at this pace; warmth would have mattered at solo-easy pace but didn't here. Closes the May 22 sync's "don't let daughter run drift to steady" watch — it stayed Z1.
---

# Activity sync — Sun May 24 daughter long run

Strava id 18633097580. 21.234 km, 8798 s moving (~6:54/km raw), 236 m gain, avg HR **122.8 cleaned** (raw avg 122.8 — the artifact only affects max, not mean), strap-reported max 171, real max ~125, suffer 37. No description. This is the **daughter Z1 run** the May 22 sync forward look prescribed for the weekend (~21 km, HR <140), run as the soft back-to-back day after Friday's 24 km long run.

## Two facts the user supplied that the streams alone can't tell you

Both are reflected in the read below.

1. **HR-strap handoff at km 17.** The daughter borrowed the strap for a few hundred meters. The trace shows it cleanly — HR ramps 79 → 127 → 153 → 165+ over ~30 s while pace is a steady 6:10–6:20/km on +3% grade (physiologically impossible jump), then drops to 96 when the strap returns. The window is **t=7261–7574 s (191 s, km 16.96–17.55)**. Real HR around km 17 sat at ~120–125, consistent with surrounding samples. The "max 171" you see on the Strava page should be discounted entirely — it's hers, not yours.
2. **Quite warm today.** No heat signature in the data, but only because the pace was so far below MAS that warmth had no room to bite (more on this below). Worth flagging for Friday's solo 28 km.

## Effort: textbook Z1 daughter pace

Characterization (config max HR 184):

| Zone | Raw | Artifact-stripped (the honest read) |
|---|---|---|
| easy <140 | 98.8% | **99.9%** |
| steady 140–150 | 0.1% | 0.1% |
| sub-thr 150–160 | 0.1% | 0% |
| threshold 160–170 | 0.7% | **0%** |
| vo2 >170 | 0.2% | **0%** |

The strap handoff is solely responsible for *all* the non-easy zone time. Strip the 191 s window and the run is essentially 100% easy. Effort tag `easy_aerobic`, primary focus `long_endurance`. Right on prescription.

## Negative HR drift while pace slowed — daughter tired, not runner

First-half HR 125, second-half 119. HR fell. Meanwhile pace slowed 6:28 → 6:49/km. The CLI computes HR drift at **-0.31 bpm/km** (negative is unusual; here it just means the slowdown was paced by the daughter, not forced by the runner's cardio).

This reads as "daughter slowed on the back half, runner followed her down" — not as fade, not as fitness signal. Don't interpret the slowdown as fatigue; it's a companion-pace artifact in the opposite direction from Friday's terrain-driven middle slow patch. The HR/pace ratio across the run is the cleanest "easy" you'd hope for.

## Heat read — quiet today, but a flag for Friday

Avg HR 122 at 6:54/km is *lower* than what you typically see at that pace. On a warm day at a more honest solo-easy pace (5:30–5:45/km) you'd expect ~130s. The daughter pace kept effort so far below MAS that warmth had no room to bite. The data is clean.

**The forward read:** if **Friday May 29's 28 km long run** lands warm, expect HR to drift higher *at the same pace* than it did on May 22's 24k — heat-driven, not fitness. The 140–150 cap then becomes harder to honor without slowing pace. The plan is still the cap; the response if warmth bites is to slow, not to push the cap. May 22's clean GAP-adjusted negative split is the baseline.

## Load

TRIMP 147 (artifact-stripped) / Edwards 144 / Strava suffer 37. Context:

- **vs Fri May 22 long run** (TRIMP 219): ~2/3 the load despite being 3 km shorter, because HR sat 15+ bpm lower. Friday was the stimulus; today was a long, low-stress aerobic accumulator.
- **vs Thu May 21 steady-10k** (TRIMP 89): ~1.6× — same family of load, spread over 2:27 of very-low intensity.

Weekend total: Fri 24 km (TRIMP 219) + Sun 21 km (TRIMP 147) ≈ 366 TRIMP / 45 km running over 3 days. Big weekend volume by absolute number; modest by HR cost because Sunday was Z1. Saturday off means the legs absorbed Friday for ~48h before Sunday — appropriate spacing for a soft B2B.

## What this resolves

**Daughter-run intensity governor: passed.** The May 22 sync's watch item was "Z1 (<140) is the cap — daughter's pace lands it there naturally. Don't let it drift to steady." The run held at 99.9% easy and HR actually *fell* across halves. Don't worry about this on future daughter runs as the default mode; the natural pace floor is well inside the cap.

**Week 4 ramp to 28 km on Fri May 29 still confirmed.** The May 22 long run cleared it; today added Z1 accumulator volume without raising recovery cost meaningfully. No new gating signal.

**The "low-prescribed days run a band hotter" pattern** (May 19, May 21) didn't repeat this weekend. Friday was steady-as-prescribed; Sunday was Z1-as-prescribed. Two clean prescriptions in a row, when the prescription matched what you'd naturally run on the day. Consistent with the May 22 read.

## Forward look

Per `analyses/schedule/2026-05-03-block-1-rev2.md` Week 4 (May 25–31). Nothing in today's run changes any of it.

| Day | Prescription | Status |
|---|---|---|
| Mon May 25 | Off | Standing — earned after a 45 km weekend |
| Tue May 26 | 14 km easy with the group, HR <140 | Group session — watch for the May 19/21 pattern (group pulls effort up a band). If it runs hot again, log it; don't add HR governance on the fly. |
| Wed May 27 | Off | |
| Thu May 28 | 12 km easy, HR <140 | |
| **Fri May 29** | **28 km, HR <145.** Hilly route if available. Full nutrition rehearsal. | Cleared. Heat caveat above — slow pace before pushing the HR cap. |
| **Sat May 30** | 15 km easy, HR <140 (B2B partner — feels-too-easy-for-Saturday is correct). | First B2B since Tuscany. |
| Sun May 31 | 8 km easy recovery, HR <135 | |

## Watching for

- **Niggle check Monday morning.** A 45 km weekend on legs that ran hot Tue + Thu of last week is exactly the loading window where Achilles/calves surface. Nothing reported today; flag if anything appears at rest tomorrow.
- **Tuesday group run intensity.** Third "easy with the group" session in the last three weeks. The pattern so far has been that group runs land a band hotter than written (May 19 → VO2, May 20–21 → steady vs easy). Not a problem in isolation, but if Tue May 26 runs the same way going into a B2B weekend, that's three quality-ish sessions stacked before Fri's 28 km — worth a re-read mid-week.
- **Friday's heat response.** First long run where heat could plausibly bite (May 22 was clean; today the data wouldn't have shown heat at this pace). If HR drifts above 145 at conversational pace on Fri, that's heat, not fitness — slow pace, hold cap, take the lesson into the Berlin build.
- **Saturday B2B execution.** The point of running tired is HR discipline, not pace. <140 is the cap; if HR sits 145+ at any pace, walk it in. Don't trash Sunday's recovery.
