---
date: 2026-09-19
type: race-plan
summary: Course model for Lidingöloppet 30 km, built by combining Patrik's own terrain knowledge with a grade-adjusted reanalysis of his 2025 race (activity 15953008292, 2:24:07, avg HR 168.3). Confirms every terrain claim he made — the km 13–20 roller-coaster (10 climbs, median 11.9 m, steep descents feeding straight into ascents) and Abborrbacken at km 25.0–25.8 (+48.4 m at 6.6% from the course low point, 60% larger than any other climb). Decomposes 2025's 43 s/km pace decay into ~16 s/km terrain, ~7 s/km walking and ~20 s/km genuine fade, and relocates the fade from the closing climbs to **km 20–25**, where two of the course's five biggest climbs were run rather than hiked. Cross-validated against the official Lidingöloppet profile chart, which agrees with the GPS analysis on every climb. Records the critical execution detail that **Lidingöloppet's course markers count kilometres REMAINING, not run** (marker = 30 − distance), and restates the staged HR plan and the four-climb hike list in marker terms so they can be applied on the day.
---

# Lidingöloppet 30 km — course model and pacing plan

Built for Sep 26 2026. Evidence base: Patrik's course knowledge, plus a reanalysis of **`15953008292`** (2025-09-27, 30.44 km, 2:24:07, avg HR 168.3, max 179, 561 m gain) using grade-adjusted pace from a 50 m distance-smoothed altitude stream rather than the per-km splits.

## Read this in race markers, not distance

**Lidingöloppet's course markers count DOWN: the sign says kilometres REMAINING.** The 30 km start is marker 30, the finish is marker 0. Every distance in the GPS analysis below is distance *travelled*, so it must be flipped before it is any use on the day:

> **marker = 30 − distance run**

The official profile (`https://runnersworld.se/wp-content/uploads/2021/03/Skarmavbild-2023-01-24-kl.-10.35.03.png`) is drawn in markers, in three panels: 30→20, 20→10, 10→0.

| section | distance run | **race markers** | landmarks |
|---|---|---|---|
| opening | km 0–13 | **30 → 17** | Start/Koltorps gärde 30, **Killingebacken ~25.7**, Ekholmsnäs ~24, Lidingövallen ~22.5, Hustegaholm ~20.2 |
| roller-coaster | km 13–20 | **17 → 10** | Fågelöudde ~15.2, Bosön ~11.3 |
| decisive | km 20–25 | **10 → 5** | Grönsta gärde 10 |
| closing | km 25–30 | **5 → 0** | **Abborrbacken ~4.7**, Sticklinge ~3.5, Mål 0 |

**The official profile and the 2025 GPS trace agree.** Every climb found in the stream analysis lands where the chart puts it: the km 3.4–4.6 climb is Killingebacken (marker ~25.7, to ~42 m, the chart's joint-highest point); km 25.03–25.77 is Abborrbacken (marker ~5.0–4.2, rising from ~2 m to ~42 m); km 20.5 and km 22.0 are the two climbs at markers ~9.5 and ~8.3; km 28.4–29.5 is the final climb at markers ~1.6–0.5. The two independent sources cross-validate.

**Two things the chart adds that the GPS analysis did not surface:**

1. **The last 10 km (markers 10→0) holds FIVE climbs of 20–40 m, not three** — markers ~9.5, ~8.3, Abborrbacken ~4.7, Sticklinge ~3.5, and a final one at ~1.5. Patrik's "three steep climbs that feel like the biggest of the course" is if anything an undercount. This panel is visibly the hardest of the three.
2. **A big early descent.** Immediately after Killingebacken the course drops from ~42 m to ~2 m between markers 25.3 and 24.7 (km 4.7–5.3). That is ~40 m of descent inside 600 m, at km 5 of 30. **Do not hammer it** — the eccentric bill for that comes due at marker 9.

## The course, in five sections

| section | character | what it means |
|---|---|---|
| **km 0–7** (markers 30–23) | Rolling, but moderate. One real climb at km 3.4–4.6 — **Killingebacken**, marker ~25.7, to the chart's joint-highest point (~42 m), then a sharp ~40 m drop to near sea level by marker 24.7. | Runnable. This is where HR is a *choice*, not a response to the ground. |
| **km 7–13** (markers 23–17) | **The flattest part of the course.** Markers 23–21 sit near sea level. No significant climbs. | Where pace is cheapest per heartbeat. Make time here, not at km 5. |
| **km 13–20** (markers 17–10) | **The roller-coaster.** 19 alternating segments, 10 distinct climbs, median amplitude **11.9 m**. Short steep descents feeding straight into steep ascents: −8.4%→+3.0%, −9.1%→+4.8%, −7.2%→+3.3%, −9.0%→+5.3%, −8.3%→+2.8%. | Net per-km elevation is near zero here, which is why `splits_metric` shows nothing. HR will spike repeatedly and that is normal. |
| **km 20–25** (markers 10–5) | Two of the five biggest climbs on the course, back to back: **km 20.46–20.99 (+30.6 m, 5.7%)** and **km 21.96–22.58 (+26.0 m, 4.2%)**. | **This is where the 2025 race was actually lost.** See below. |
| **km 25–30** (markers 5–0) | **Abborrbacken, marker ~5.0–4.2: +48.4 m over 736 m at 6.6%**, from the course low point (3.5 m, literally sea level) to 51.8 m. Then a long climb at km 28.35–29.52 (+32.2 m, 2.8%). | Abborrbacken is **60% larger than any other climb on the course**. Hiking it is correct and already established practice. |

**On the "course high point":** technically it is 52.2 m at km 4.63, but the top of Abborrbacken is 51.8 m — a 0.4 m difference, inside barometric noise. Functionally tied. The difference is that km 4.63 is reached by a gentle 2.4% drag and km 25.8 by a 6.6% wall from sea level. Patrik's description is accurate in substance.

**A note on precision.** Distances here are GPS distance from the 2025 trace, converted to markers via `30 − distance`. GPS and the painted boards may differ by a few hundred metres over 30 km, so where this file names a marker, trust the *description* of the terrain and the named landmark over the number itself.

## What actually happened in 2025

| block | raw pace | **GAP** | GAP running-only | HR | m(GAP)/beat |
|---|---|---|---|---|---|
| 0–5 | 4:27 | **4:21** | 4:21 | 161.7 | **1.42** |
| 5–10 | 4:27 | 4:26 | 4:26 | 168.0 | 1.34 |
| 10–15 | 4:42 | 4:29 | 4:29 | 167.3 | 1.33 |
| 15–20 | 4:46 | 4:36 | 4:34 | 168.7 | 1.30 |
| 20–25 | 4:56 | **4:52** | **4:47** | 169.9 | **1.22** |
| 25–30 | 5:10 | 4:48 | 4:41 | 172.6 | 1.21 |

### The 43 s/km decay decomposes into three unequal parts

- **~16 s/km (37%) is terrain.** Real. This was Patrik's objection and it was correct.
- **~7 s/km (17%) is walking** — and he *already walked in 2025*: 275 s total, 240 s of it in the last 10 km, every block on a grade of 8–14% (km 20.8, km 24.6, **km 25.2 Abborrbacken for 91 s at 14.1%**, km 28.5 for 71 s at 13.6%). Walking on Sep 26 is not a change of plan; it is formalising existing practice.
- **~20 s/km (47%) is the running genuinely getting slower at equal grade.** GAP running-only goes 4:21 → 4:41.

So terrain plus strategy account for just over half. The remainder is fade, and it is real.

### How big is the fade, honestly

Grade correction makes the heart-rate story *worse*, not better: GAP speed fell across the race, so at held efficiency HR should have **dropped**. Held at opening efficiency, the closing 5 km needed only HR ≈ 146; actual was 172.6.

Decoupling is **~10%** (1.34 → 1.21 m per beat, using km 5–10 as the baseline rather than km 1–5, which contains the from-rest HR ramp). Over 2:24 at 91% of max HR, **4–5% is expected cardiac drift.** So call it **~5% genuine fade** — meaningful, worth fixing, and considerably smaller than a raw reading of the pace column suggests.

### The fade is at km 20–25, not at the finish

Rolling efficiency, slope per segment:

| segment | m/beat | rate |
|---|---|---|
| km 6–13 | 1.34 → 1.32 | flat |
| km 13–20 (roller-coaster) | 1.32 → 1.28 | −0.0067 /km |
| **km 20–24** | **1.28 → 1.23** | **−0.0102 /km** |
| km 24–finish | 1.23 → 1.20 | **+0.0058 /km — stopped deteriorating** |

Running-only GAP says it independently: 4:26 → 4:29 → 4:34 → **4:47** → **4:41**. **The closing 5 km, containing the single biggest climb on the course, is faster at equal grade than the block before it.**

The mechanism is plain. The km 20.5 and km 22 climbs are two of the five biggest on the course, they arrive back to back, and **he ran them** — only 55 s of walking in that whole window. From km 24 on, where he hiked the steep pitches, efficiency stopped falling.

**The prescription is therefore not "walk more at the end."** He already does that, and it works. It is: **arrive at km 20 with more left, and hike the km 20.5 and km 22 climbs as well.**

## The plan for Sep 26

### Staged HR — block averages, not instantaneous ceilings

On the roller-coaster the heart rate will spike above any cap several times per kilometre. That is the terrain, not an error. **Manage the block average; ignore the instantaneous number.**

| **race markers** | distance run | HR | note |
|---|---|---|---|
| **30 → 17** | km 0–13 | **≤ 163 average** | Moderate opening, then the flattest part. Includes Killingebacken at marker 25.7 — climb it, don't race it. |
| **17 → 10** | km 13–20 | **≤ 166 average** | The roller-coaster. Spikes to 170+ on the short ramps are expected and fine. |
| **10 → 5** | km 20–25 | **≤ 168** | Hike the two climbs below and this takes care of itself. |
| **5 → 0** | km 25–30 | **≤ 170**, free from the top of Abborrbacken | |

**Why ≤163 and not 160, and not 168.** In 2025 the first 5 km at HR 161.7 produced **the fastest grade-adjusted running of the entire race (4:21)**. The next 5 km at HR 168.0 produced **slower** running (4:26). Six extra beats bought nothing — it was a pure cost. 161.7 is empirically the heart rate at which he runs this course best, so the cap is set just above it. A flat sub-160 would have been an over-correction to a fade that is ~5%, not 15%.

### The hike list

Walk, deliberately and without ego, on:

| # | **race marker** | distance run | climb | status |
|---|---|---|---|---|
| 1 | **9.5 → 9.0** | km 20.46–20.99 | +30.6 m, 5.7% | **NEW — ran it in 2025; this is where the fade started** |
| 2 | **8.0 → 7.4** | km 21.96–22.58 | +26.0 m, 4.2% | **NEW — same reason** |
| 3 | **5.0 → 4.2** | km 25.03–25.77 | +48.4 m, 6.6%, **Abborrbacken** | hiked in 2025 (91 s) — keep doing it |
| 4 | **1.6 → 0.5** | km 28.35–29.52 | +32.2 m, 2.8% | hiked in 2025 (71 s) — keep doing it |

**The two new ones are both just after the Grönsta gärde marker-10 board.** That board is the cue: from marker 10, the next two hills get walked.

On a climb steep enough that running costs 10+ bpm, hiking is faster over the *remaining* distance even though it is slower over that climb. The 2025 data shows this directly: the blocks he hiked are the blocks where efficiency stopped deteriorating.

### Section tactics

- **km 0–7:** rolling and runnable, and the single easiest place to waste the race. Hold ≤163 even though it will feel absurdly easy.
- **km 7–13:** the flat. This is where pace is cheapest per heartbeat — let the pace come to you here rather than forcing it at km 5.
- **km 13–20:** carry downhill momentum into the following ascent — that is genuinely free speed and Patrik's own technique for this section. But **carry it, don't manufacture it**: hammering a −9% descent costs eccentric damage that gets repaid at km 22. Let each short ramp cost what it costs.
- **km 20–25:** the decisive section. Hike items 1 and 2 above. Everything the first 20 km was disciplined for is spent here.
- **km 25–30:** hike Abborrbacken, then race whatever is left from the top.

### Expected shape

Run correctly, the profile inverts against 2025: slower through km 10, level by km 20, and **faster over the closing 10 km** — which is the same signature this year's fitness already produced on the Ursvik head-to-head (`../syncs/2026-09-11-ursvik-vs-2025-sync.md`: hotter early, better late).

No target time. See `../schedule/2026-09-19-race-week.md` for why, and for the alcohol/sleep context that will make heart rate read high all day.

## Corrections recorded

Two claims made earlier in the Sep 19 session were wrong and are retracted here:

1. **"The 2025 race faded over the last 10 km."** The evidence used was raw pace decay over km 26–30 — the worst possible window to read, conflating the course's biggest climb with 162 s of deliberate walking. The conclusion was directionally right; the evidence proved something else. The fade is at **km 20–25**.
2. **"Strava's km 11 shows +22.6 m, so your memory of km 7–13 as flattest may be off."** That was a net-per-km artefact. The detailed profile puts no significant climb in km 7–13, and it is the section where efficiency held flattest. **Patrik's course memory was right and the split-table flag was the weaker signal.**
