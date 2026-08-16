---
date: 2026-08-15
type: activity-sync
summary: The A-race, done — Berliner Mauerweglauf 100 miles finished in 22:05:38 elapsed (18:55:49 moving, 3:09:49 stopped) in ~34°C heat. Missed the sub-20 goal for one identifiable reason — a GI crash at km 98 (an old gel, by Patrik's account; heat and fluid volume are alternative suspects) that cost ~2 h of nausea centred on an 84-min stop at the km 103 aid station. Everything around the crash was executed with discipline: avg HR 127.7 with 87% below 140 and literally zero time above 155, a controlled decay 6:06→7:41/km through km 100, and — the standout — a genuine recovery after the crash on a "coca cola-diet": km 121–140 ran at 7:00/km moving, faster than km 81–100, and the final 3 km at 7:17/km. Biggest load on record by 3.3× (TRIMP 1583 vs 485 for the Jul 22 peak leg). Gear: ASICS Superblast 3. This file is the factual record; the race review (fuelling autopsy, hip verdict, recovery prescription) is a separate races/ file.
---

# Activity sync — Sat Aug 15: Berliner Mauerweglauf 100 miles

Gear: ASICS Superblast 3
Distance 163.39 km · elapsed 22:05:38 / moving 18:55:49 (stopped 3:09:49) · avg HR 127.7 / max 155 · 600 m gain · cadence 82.1 (single-leg) · ~13,044 kcal · suffer 432 · Strava id 19760154152

Start 06:02 local. Characterized via `characterize-activity` in a sub-agent. Race plan of record: `races/2026-07-07-mauerweglauf-energiplan.md` as revised by `races/2026-08-10-berlin-hydration-execution-card.md` and `races/2026-08-11-berlin-fuelling-sheet-revision.md` (sub-20h goal, 95 g/h flat with taper-by-feel, concentrate-in-flask + water alongside).

**Read in one line: a disciplined, heat-managed race that was on a reasonable arc until a single GI event at km 98 took ~2 h; the recovery from that crash — finishing the last 60 km on cola, faster than the 20 km before the crash — is the strongest thing in the file.**

## Patrik's own account (Strava description, verbatim)

> Inte riktigt resultatet jag hopppats på men ändå ok efter omständigheterna.
>
> Lugnt och fint på morgonen för att inte bli för varm. Trodde sen att jag lyckades navigera den 34-gradiga värmen helt ok genom att ta det lugnt och kyla ner mig bäst det gick med is från termos där jag hade bag drop och vatten på övriga. Magen kraschade efter att jag drog en gammal gel efter 98 km och behövde en lång paus på nästa hjälpstation för att illamåendet skulle gå över. Vet inte om det var gelen som var boven, om jag druckit för mycket eller om det bara var värmen.
>
> Kom igång igen efter 2 timmars illamående och lyckades slutföra på en coca cola-diet.

## What the numbers say

- **HR discipline was total.** 87.2% of the race below 140, 12.8% in 140–150, nothing above 150 in the streams (detail max 155). The energiplan's "go out controlled" instruction was executed all day — this was the plan's HR shape, start to finish.
- **Pacing decayed gradually, then recovered.** Per-20 km moving pace: 6:06 → 6:15 → 6:40 → 7:11 → 7:41 (km 81–100), then post-crash 7:17 → **7:00** (km 121–140) → 7:23 → 7:17 at the finish. Km 121–140 faster than km 81–100 is not how ultras usually end, let alone on cola alone after a gut shutdown.
- **The crash is fully visible in the data.** Km 101–102 slow/walking, then **+84 min stopped at km 103** (split avg HR 93) — the aid station where the nausea was waited out. With the surrounding walking, the "2 timmars illamående" reconciles almost exactly.
- **One earlier substantial dwell:** km 71, +14 min with a 10:24/km walking split (HR 109) — right at the km 70 drop-bag/reassessment gate the plan prescribed, so at least partly by design.
- **Total stopped time 3:09:49**, of which ~1:24 is the crash and ~8.9 min the km 33 bag-drop (ice thermos per protocol); the rest is regular 2–5 min checkpoint dwells (~16 of them). Even without the crash, dwell was material — the sub-20 scaffold assumed far less.
- **Only 6 of 164 km were walking-dominant** (>10 min/km moving: km 71, 90, 101, 102, 110, 149). The race was run/shuffled nearly throughout, including the Dörferblick section.
- **Negative HR drift:** first-half avg 134.5 → second-half 124.3, with pace slowing — classic late-ultra HR suppression, same pattern as Kungsleden day 2. Not a monitor artifact; lows coincide exactly with stops and walking.

## Load

TRIMP 1583 / Edwards 1496 / suffer 432 — the biggest single session on record by a wide margin: ~3.3× the Jul 22 peak long leg (TRIMP 485) and ~1.55× the entire Kungsleden B2B combined. Recovery planning should treat this as an order-of-magnitude event, not a big long run.

## Counterfactual, for the record

Moving time was 18:55:49. Sub-20 elapsed required holding total stops under ~64 min; the crash alone took ~84 min at km 103 plus the slow approach. Without the GI event — and with the checkpoint dwell pattern of the first 100 km — the finish lands in the ~20:30–21:00 region on this day's pacing: the heat had already priced sub-20 out before the gel. The crash cost roughly 90–120 min; the 34°C day cost the rest.

## Open for the race review (separate file, after debrief)

1. **Gel autopsy:** which gel was "gammal", was it outside the Maurten-only plan of record, and what does that imply for drop-bag stocking hygiene.
2. **Fuelling execution vs the sheet** — g/h actually achieved per block, whether the early-signal ladder (taste → reluctance → sloshing) was noticed before the crash, and how the water-and-electrolytes escalation played against the recorded 1–2 h recovery expectation (which the actual 2 h matched exactly).
3. **Hip/back:** did the km 70 and km 102 reassessment gates run as designed, and did the durable-pain rule ever get close to triggering.
4. **Cooling protocol verdict** (ice thermos at bag drops, water elsewhere) — Patrik's own read is it worked until km 98.
5. **Recovery prescription** for the coming 2–4 weeks — belongs in the review, which will also trigger the viz regeneration.
