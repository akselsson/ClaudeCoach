---
date: 2026-05-03
type: training-preferences
summary: Standing schedule, style, and constraints — long run Friday, Tue work-group quality, Mon/Wed off, polarized, with the Italy holiday + work-leave windows that reshape the Berlin build.
---

# Training preferences and standing schedule

These are the standing facts about how Patrik trains. They override the day-of-week defaults in older block plans (which assumed Saturday long runs and Wednesday quality) and are the source of truth that future weekly reviews defer to.

If any of this changes — long-run day shifts, a chronic niggle appears, work schedule changes — update this file rather than rewriting it inside a block plan.

## Weekly shape

Patrik runs 5 days/week by default; can push to 6 in peak weeks with a recovery jog added to a current rest day, but Mon and Wed mornings are not negotiable.

| Day | Default role | Time of day | Notes |
|---|---|---|---|
| **Mon** | Off | — | Work blocks morning runs. Easy spin OK if legs are restless. |
| **Tue** | **Quality — work-group session** | Evening | Standing menu: 4×4 min @ interval pace, or 5×6 min @ threshold. Easy with the group is allowed when the plan calls for recovery (deload weeks, post-race weeks, race weeks). |
| **Wed** | Off | — | Work blocks morning runs. Bike commute fits here when it happens. |
| **Thu** | Easy or medium-long | Afternoon/evening | Volume buffer day — flex up for higher-volume weeks, flex down for recovery. |
| **Fri** | **Long run** | Morning | The week's anchor. B2B partner-day for big weekends. |
| **Sat** | Medium-long / B2B continuation | Morning | Stacked the day after Friday long when the block calls for B2B; otherwise easy or off. |
| **Sun** | Easy recovery | Flexible | The day-after-the-day-after the long run. Short, conversational. |

**Stress-day spacing:** Tue and Fri are the two stress anchors. Wed off is the natural buffer between them. Sat is "the day after Friday" — only stacked into a real medium-long when the block explicitly says B2B; otherwise stays easy or off.

**Race-week and recovery-week exception:** in race weeks and immediate post-race weeks, Tuesday drops to easy and the long run shrinks or moves to accommodate the race day. The block plan controls; this file just pins the defaults.

## Training style: polarized

Most volume at HR <145 (easy/conversational), with the Tue work-group session and the long run as the two stress points each week. No "moderate" zone-3 grinding for its own sake.

**Why polarized:**
- Lowest injury risk for ultra training, and Berlin Mauerweglauf is the season's A-race.
- Matches the existing weekly rhythm (one quality + one long) — no need to invent a second hard day.
- Patrik confirmed it as the right framework on 2026-05-03 when offered polarized vs. Norwegian sub-threshold-heavy vs. Lydiard hill block. Norwegian-style was rejected as too high-injury-risk to ramp into mid-build; Lydiard was rejected as too rigid for a build that has to accommodate 2 weeks of unstructured Italy training.

## Tuesday work-group session menu

These are the standing options. The block plan picks which one (or "easy with the group") for each week.

- **4×4 min @ interval pace** — VO2-ish, ~5k–10k effort. Used sparingly in the build (max 1×/2 weeks); not appropriate for ultra-specific weeks.
- **5×6 min @ threshold** — sub-threshold to threshold (HR 158–163). The default quality session for the Berlin build. Aerobic-power-with-leg-speed. Use most weeks once quality is reintroduced.
- **Easy with the group** — when the plan calls for it. Same social value, no training cost beyond the run itself.

If a Tuesday session goes off-script (group did something different, body felt off, weather forced a change), note the actual structure in Strava and let the next weekly review reconcile.

## Cross-training

- **Bike commute:** target 1×/week, in practice often 1–2×/month. Treat as opportunistic recovery / commuting overhead, not weekly aerobic load. Don't double up the commute on a tired day.
- **No structured strength work currently.** If you start adding gym sessions during the build, update this file.

## Calendar disruptions for the Berlin build

These reshape the season-plan narrative materially — flag them in every block plan written between now and Aug 15.

- **Italy holiday, ~2 weeks late June / early July (exact dates TBD).** Structured training will be hard. Treat as a maintenance / unstructured block: keep volume up by feel, run on whatever schedule fits the day, no quality required, no specific long-run distance required. Don't try to force a B2B if logistics fight you.

- **On leave from work, Jun 18 – Aug 18.** Mon-Wed morning embargo lifts during this window. Long-run and quality days become flexible — B2Bs can land on any two consecutive days, the long run can move to a Saturday or Sunday if it fits a training-camp setup, etc. **This is the window where the season plan's specificity-block big weekends (50+35, 60+30, 70+40 km) live.** The work leave makes those weekends actually achievable; without it they'd be fiction.

The combination matters: Italy eats roughly weeks 7–8 of the season-plan timeline (the start of the specificity phase). Block plans need to either (a) front-load the specificity-build into weeks 5–6 before Italy, or (b) accept that the specificity phase effectively starts mid-July when Patrik is back, with one less B2B than the season plan implied.

## How to use this file

- **Weekly reviews** (`weekly-training-review` skill): when laying out the next 14 days, use this file's day grid by default. If a block plan says "Wednesday threshold", ignore it and place the threshold on Tuesday — or flag it as a discrepancy worth asking about.
- **New block plans** (`setup-training-plan` skill): start from this file's day grid. Volume targets and phase intent come from the season plan; day-of-week comes from here.
- **Season plan** (`2026-05-03-season-plan-overview.md`): unchanged in macro shape. The specificity phase's calendar dates need to flex around the Italy holiday — the season plan currently doesn't reflect that.
