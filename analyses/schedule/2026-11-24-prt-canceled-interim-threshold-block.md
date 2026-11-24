---
date: 2026-11-24
type: schedule-update
summary: PRT 100 km (Dec 4) was canceled on Sat Nov 21, so the taper in the Nov 16 review is void. Starts a 4–6 week interim block while Patrik decides what's next. It has two quality days: Tuesday Kundo as the group sets it, and a Thursday session kept below threshold (HR cap ~160–162). Friday keeps an easy ~20 km long run. Easy running is held at 55–65 km/week so the threshold work doesn't turn into detraining plus VO2 sessions. Prescribes Nov 25 – Dec 6.
---

# PRT canceled → interim threshold block

Replaces the forward plan in `2026-11-16-weekly-review.md`. That covered the taper through Nov 29 and race week to Fri Dec 4. **PRT 100 km was canceled on Sat Nov 21.** The season plan (`../season-plan/2026-09-26-prt-100k-season-plan.md`) ended at that race, so there is no season plan for now. The next goal is undecided, and Patrik will decide it during this block.

## Since the Nov 20 sync

| Day | Actual |
|---|---|
| Sat Nov 21 | Family run in sleet, ~1:40 moving, HR 123. Z1, as planned. |
| Sun Nov 22 – Mon Nov 23 | Off. |
| Tue Nov 24 | Kundo 5×6 min threshold with Rickard, 11.4 km, Endorphin Speed 4. Details below. |

**Tue Nov 24, characterized:** threshold intervals, 2 min walk/shuffle recoveries, TRIMP 127. That is the **highest Tuesday load in 10 weeks**: the Nov 10 and Nov 17 5×6 sessions were 97 and 107, and the 4×4s were 63–76. The run was also longer than those.

| Rep | Pace | HR, min 2–6 |
|---|---|---|
| 1 | 4:12 | 159–163 |
| 2 | 4:05 | 166–168 |
| 3 | 4:10 | 166–168 |
| 4 | 4:08 | 167–170 |
| 5 | 4:06 | 168–172 |

The armband trace looks clean, so this isn't a wrist artifact. The reps were 10–15 s/km faster than Nov 10, on taper-fresh legs.

**Corrected the same day: this was threshold, not "edging into VO2".** The first read measured it against the old 5×6 band of 158–163, where only rep 1 fitted. Patrik said he could have run more reps at that pace, with HR rising only slightly, and the data supports him:

- HR was **flat at 166–168 from minute 2 to minute 6 in reps 2–3**. Above threshold it keeps climbing within a rep.
- Reps 4–5 crept 1–3 bpm. That's ordinary drift across a session, not a runaway.
- 166–169 is ~91% of the 184 max, a normal threshold HR for a trained runner. 158–163 (86–89%) is closer to sub-threshold. It was a prescription from May and never a measured threshold.

**Working estimate:** threshold ~4:05–4:12 at HR 165–169 in 6-min reps with walking recoveries. Continuous threshold is probably ~4:12–4:18, because interval reps flatter the number. This is at the season's fitness peak with taper freshness. The preferences file is updated to match.

**What it means for the block:**
- Kundo 5×6 at 165–169 is the intended threshold session. Don't hold it down to 158–163.
- **The Thursday cap of 160–162 stays.** It now sits ~5 bpm under threshold, which is what a sub-threshold session should be.
- **Two uncapped sessions a week would still be the risk**, because the Thursday session would drift up to Kundo intensity.

**Recalibration:** `config/training.json`'s threshold pace zone (4:20–4:30, unchanged since 2026-05-03) is stale. The HR zone (160–170) already fits. Recalibrate the pace zones at the Dec 6 check-in or the review after it. Use pace at 160 from the Thursdays and pace at ~167 from the Kundo 5×6s. An optional alternative is one Thursday (~Dec 10) as a 30-min continuous even effort, where the average HR over the last 20 min estimates threshold HR.

## Why this block, and its shape

- **Direction:** Patrik wants a couple of threshold sessions a week rather than volume. That matches the season plan's 2027 note, "more hills and more threshold/tempo/speed… crowded out by two ultra builds this year". The aerobic base is at its season high (105 / 82 / 67 km the last three weeks), so this is a good time to work on threshold.
- **Polarized with two quality days, not Norwegian double-threshold.** Norwegian-style training was rejected on 2026-05-03 because it was too risky to ramp into mid-build. Here, one of the two days is Kundo at whatever the group runs, and only the second is controlled. That keeps the hard load bounded without adding a third rule system.
- **Easy volume is protected, not cut.** Patrik's HR is volume-dependent (see `../preferences/`): below ~70 km it drifts up within a couple of weeks. A low-volume threshold block would then push the same pace 5+ bpm higher, and the controlled sessions would turn into VO2 work without anyone noticing. Cut the hard work first, never the easy kilometres.
- **Friday keeps a ~20 km long run (Patrik, Nov 24), so the second session moves to Thursday.** Thursday gives 48 h after Kundo, with Wednesday off. The capped session is built to cost little, so an easy long run the next day is fine. Thursday also keeps the weekend free for the daughter run, which floats between Saturday and Sunday. A Sunday session would collide with it in some weeks.

## Standing rules for the block (4–6 weeks, to ~early Jan)

- **Tuesday: Kundo as the group sets it.** 4×4 runs as VO2 and 5×6 at threshold (HR ~165–169), per the preferences file. No cap beyond the group's format. Add heavy strength in the evening again (see below).
- **Thursday: a session kept below threshold.**
  - **HR cap 160–162**, ~5 bpm under the threshold estimate above. If it reaches ~165, you're at threshold, so slow down. **Every rep at the same pace.** Finish feeling you could run one more rep. That matters more here than it would on a Friday, because the long run comes the next day.
  - Format menu, progressing over the block: 3×10 min / 1 min jog → 4×8 / 1 min → 2×15 / 2 min → 3×12 / 1 min → 2×20 / 2 min. **That's 30 min at that effort to start, ~40 min by week 4.**
  - 2–3 km warm-up and 2 km cool-down, ~12–14 km total. Use flat road or the track, so pace is readable.
  - **Armband on.** Record pace at the cap. That gives the block's progress measure.
  - Shoe: Endorphin Speed, Evo SL or Boston are fine at ≤10 km of quality, per the shin rule. The Adios Pro 5 is fine too.
- **Friday: ~20 km long run, easy, HR <140–145.** This is aerobic volume, not the Z2 stimulus run of the preferences file. With two quality days already in the week, it stays easy and has no segments at race effort. Wear a volume shoe (Torin / Superblast / Megablast). If Thursday's reps went over the cap, cut it to 16 km.
- **Easy: ~55–65 km/week in total**, HR <140, in volume shoes. Friday's long run and the weekend family run are the anchors. Sunday is easy or off.
- **No other quality.** Strides after an easy run are fine. Patrik tends to run over prescription, and that's harmless as extra easy kilometres. A partner-pace 15 km at HR 145–150, or letting Friday drift into Z2/Z3, is not harmless: it would mean three stress days in a row (Thu–Fri plus Tue).
- **Strength is back.** Heavy on Tuesday evening, per the preferences file. The first session (Dec 1) is at ~⅔ of normal load, since the last one was Nov 15. **Maintenance strength moves from Thursday to Saturday after the family run** (the preferences file's alternative slot). That keeps it off the night before the long run, on a day that already follows a session and precedes a long. Skip split squats if they provoke the outside of the left knee.
- **Monday sixth day stays off for two more weeks.** The left lateral knee/foot has been quiet since Nov 13. If it stays quiet through Dec 6, Monday easy runs can come back.
- **Left knee/foot:** if it speaks in Thursday's faster reps, drop that session first, before touching easy volume.

## Next 14 days — Nov 25 to Dec 6

### Week of Nov 23 (rest of week) — ~66 km incl. Tuesday

| Day | Session | Shoe |
|---|---|---|
| Wed Nov 25 | Off. | |
| **Thu Nov 26** | **First sub-threshold session: 3×10 min / 1 min jog, HR cap 160–162**, even pace. 2–3 km warm-up and 2 km cool-down, ~12–13 km in total. Flat road or track. Armband. Record the pace at the cap. It's only 48 h after a big Kundo, so if the legs are flat in the warm-up, make it 2×10. | Endorphin Speed / Adios |
| Fri Nov 27 | ~20 km long, easy, HR <140–145. | Torin / Superblast / Megablast |
| Sat Nov 28 | Family / daughter run, Z1, 12–15 km. Maintenance strength after. | Megablast / Superblast |
| Sun Nov 29 | 8–10 km easy, or off. | Torin |

### Week of Nov 30 — ~65 km

| Day | Session | Shoe |
|---|---|---|
| Mon Nov 30 | Off. | |
| Tue Dec 1 | Kundo as set, 8–10 km. **Evening: heavy strength at ~⅔ load.** | Endorphin Speed |
| Wed Dec 2 | Off. | |
| **Thu Dec 3** | **4×8 min / 1 min jog, HR cap 160–162**, ~13 km total. | Endorphin Speed / Adios |
| Fri Dec 4 | ~20 km long, easy, HR <140–145. This was PRT's day. | Torin / Superblast / Megablast |
| Sat Dec 5 | Family / daughter run, Z1, 14–16 km. Maintenance strength after. | Megablast / Superblast |
| Sun Dec 6 | 8–10 km easy, or off. **Short check-in:** the pace at the cap from both Thursdays, how Friday felt after the session, the knee, and whether there's a next race yet. | Torin |

## What I'm watching for

- **Thursday creep.** The cap is the point of the session. If Thursday's reps settle at 165+, the block becomes two VO2 days a week and Friday pays for it. Pace at a fixed HR is the progress measure. Expect ~4:15–4:25 at 160 to start.
- **Friday's HR.** Easy-paced HR on Friday should sit where it usually does after an easy Thursday. If it runs 5+ bpm high, Thursday cost too much: shorten the reps before anything else.
- **Easy volume sliding below 50 km.** If it does, rising running HR is detraining, not fatigue. The fix is more easy running, not rest.
- **Tuesday load.** Today was the highest Kundo TRIMP in 10 weeks: the right intensity, but longer than usual. If Kundo keeps landing at 120+ and Thursday also feels heavy, make Thursday 2×10 rather than adding recovery days.
- **Threshold calibration.** Pace at HR 160 (Thursdays) and at ~167 (Kundo 5×6), to recalibrate the config pace zones. Taper freshness fades over the block, so expect those paces to slip slightly before they improve.
- **The next goal.** When Patrik picks a race, this block becomes either its base phase (a spring ultra) or its opening phase (anything shorter). That will be a new season-plan file via `setup-training-plan`.

## What changes from the prior plan, and why

- **The whole taper and race week (Nov 25 – Dec 4) are void.** The race was canceled.
- **A second quality session is added on Thursday.** Patrik asked for threshold over volume. Friday keeps the long run at ~20 km, easy, at his request.
- **Strength is back.** Heavy on Tuesday; maintenance moves from Thursday to Saturday, because Thursday is now a quality day before the long run. It was cut for the taper, and there's no taper now.
- **Kept from the Nov 16 review:** Monday sixth day off for now (knee), armband on quality, the shin rule on shoes.
