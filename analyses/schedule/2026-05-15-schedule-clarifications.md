---
date: 2026-05-15
type: schedule-update
summary: Three standing-schedule clarifications from Patrik — Thu May 14 was a no-run (correcting the May 12 sync's assumption), Tuesday is the group session with format set by Kundo and paces set by Patrik's training state, and Friday long is explicitly Z2 (HR 140–150) while the weekend daughter 21k is explicitly Z1 (HR <140). Preferences file updated; Block 1 Weeks 3–5 re-prescribed below.
---

# Schedule clarifications — May 15

Patrik provided three pieces of feedback on the current plan. Two are clarifications to the standing schedule (Tue format rule, Fri/weekend zone tags) and one is an activity correction (Thu May 14 was a no-run, not the planned 8 km easy).

The training-preferences file has been updated with the two standing clarifications. This file records the activity correction and re-prescribes Block 1 from Week 3 forward under the new rules.

## 1. Thursday May 14 — no run

The May 12 activity sync assumed Thu's 8 km easy stayed in. It didn't. Recomputing Week 2:

| Day | Planned | Actual |
|---|---|---|
| Mon May 11 | Off | Off ✓ |
| Tue May 12 | 5–6 km easy <135 | 7.1 km + 4×4min with Kundo (avg HR 120, max 163) |
| Wed May 13 | Off | Off ✓ |
| **Thu May 14** | **8 km easy <140** | **No run** |
| Fri May 15 | 15 km easy <140 | 8.0 km, avg HR 140, max 154 |
| Sat May 16 | Off | (off planned) |
| Sun May 17 | 10–12 km <135 (per May 15 sync) | TBD |

Week running total now lands at ~25–27 km vs the planned 36 (and vs the ~30–32 the May 15 sync assumed). That's a deeper cut than the May 15 sync recognized, but **the recommendation doesn't change**: Sun May 17 still holds at 10–12 km HR <135. Don't reach to recover the missing Thursday volume on Sunday — Week 3 is the rebuild, not the back half of Week 2.

No niggle reported, no flag from Patrik on Thursday's skip — read as a low-friction "didn't get to it" rather than a body signal. If a reason emerges (sleep, niggle, late work), worth noting in a future sync.

## 2. Tuesday — group sets the format, Patrik sets the paces

This resolves the pattern flagged in the May 12 sync ("three Tuesdays in a row of Kundo intervals that the plan tried to remove"). The standing rule, now codified in the preferences file:

- **The group decides each Tuesday's workout.** 4×4 min, 5×6 min, easy night — Kundo picks.
- **Patrik decides the paces.** Build week → reps at prescribed effort. Recovery week → same rep structure jogged at recovery pace. Race/post-race week → easy with the group or skip.
- **The plan stops trying to replace the group session.** Tue is a group day every week.

Knock-on for Block 1: the previous "easy with the group, no intervals" prescriptions for Weeks 2–4 don't survive. If Kundo runs intervals next Tuesday (likely — three weeks in a row already), Patrik joins the format and jogs the reps. Week 5 is when the paces step up to the prescribed quality effort.

## 3. Friday Z2, weekend daughter Z1

Explicit HR zone tags on the two volume days:

- **Friday long run = Z2 (HR 140–150 = "steady" in config/training.json).** Patrik's preferred long-run day. The old "HR <145" framing was ambiguous between Z1 and Z2 — tagging it Z2 means aim for the middle of 140–150, not drift up to it from Z1.
- **Weekend 21 km with daughter = Z1 (HR <140 = "easy" in config/training.json).** Daughter's 6:00–6:30 /km lands it in Z1 naturally; the tag removes any ambiguity that this might count as the week's long-run stimulus (it doesn't — Friday is).

Implication for the long run's HR cap: existing block-1-rev2 prescriptions of "Fri long, HR <145" are superseded — read them as Z2 (HR 140–150) going forward.

## Block 1 forward plan — Weeks 3, 4, 5 re-prescribed

Supersedes the Week 3+ sections of `2026-05-03-block-1-rev2.md` and the "Week 3 held as planned" note in `2026-05-15-activity-sync.md`.

### Week 3 — May 18 to May 24 (reintroduction)

| Day | Session |
|---|---|
| Mon May 18 | Off |
| **Tue May 19** | **Group workout, recovery paces.** Whatever Kundo runs. Reps at recovery effort (jog them), not interval or threshold pace — Week 3 is still rebuild. Cool down with the group. No strides on top. |
| Wed May 20 | Off. Bike commute fits here. |
| Thu May 21 | 10 km easy, HR <140. Maintenance strength after. |
| **Fri May 22** | **Long run: 24 km, Z2 (HR 140–150).** First proper long run since the race. Practice fueling — one gel per 30 min, ~500 ml/h. Morning. |
| **Sat or Sun** | **Daughter long run: ~21 km, Z1 (HR <140).** Her pick of day. |
| Other weekend day | Off, or 6–8 km easy <135 if Friday felt clean. |

**Week target:** ~62–65 km running.

The Friday long is the test session for the new Z2 framing. Watch the HR-to-pace relationship: if 140–150 sits comfortably at a conversational pace, fitness has come back from the 100k recovery + race. If HR drifts up to 150+ at conversational pace, hold Week 4's long rather than ramping it.

### Week 4 — May 25 to May 31 (first B2B, folded with daughter run)

| Day | Session |
|---|---|
| Mon May 25 | Off |
| Tue May 26 | Group workout. **Paces tuned to Week 3 response:** if Friday's Z2 long felt clean and recovery was good, this Tuesday can be the first proper quality of the build (reps at threshold or interval pace as Kundo dictates). If anything looks ragged from Week 3, recovery paces again. |
| Wed May 27 | Off |
| Thu May 28 | 12 km easy, HR <140. Maintenance strength after. |
| **Fri May 29** | **Long run: 28 km, Z2 (HR 140–150).** Full nutrition rehearsal. |
| **Sat May 30** | **B2B partner: daughter long run ~21 km, Z1 (HR <140).** Running on tired legs is the point; daughter's pace lands it in Z1 naturally — exactly the right intensity for the B2B back half. |
| Sun May 31 | Off or 6–8 km easy <135. |

**Week target:** ~75 km running.

This folds the daughter run into the B2B slot — same volume as the original Block 1 prescription (Fri 28 + Sat 15 km easy), same HR cap, social win, one less logistical decision. Daughter takes Saturday this week so the B2B sits together.

### Week 5 — Jun 1 to Jun 7 (first real Tuesday quality + biggest long run)

| Day | Session |
|---|---|
| Mon Jun 1 | Off |
| **Tue Jun 2** | **Group workout, proper paces.** If Kundo runs 5×6 min, that's threshold (HR 158–163). If they run 4×4 min, that's interval (HR up toward threshold, pace ~4:05–4:15/km). Abort to easy with the group if HR climbs above 165 at the prescribed pace — that's "not ready," not "push through." |
| Wed Jun 3 | Off |
| Thu Jun 4 | 14 km steady, HR 140–150. Mid-week aerobic stimulus. |
| **Fri Jun 5** | **Long run: 32 km, Z2 (HR 140–150).** Last 5 km can drift to 150 if it feels right. |
| **Sat or Sun** | **Daughter long run ~21 km, Z1 (HR <140).** Her pick. |
| Other weekend day | Off or 6 km easy <135. |

**Week target:** ~78–80 km running.

This is the first week with two real stress days (Tue quality + Fri long) since the race. If both land cleanly, Block 1 has done its job and Block 2 (Jun 8+) can lock in. If either runs over budget — Tue HR climbing above 165 at prescribed pace, or Fri HR drifting up at conversational pace — Block 2 holds rather than ramps.

## What's watching for

- **Sun May 17 HR-at-easy-pace.** Unchanged from May 15 sync. <130 comfortably = recovered; drifting to 138+ at slow pace = under-recovered, push Tue softer and re-evaluate.
- **Tue May 19 — does "recovery paces in a group context" actually hold?** This is the new rule's first test. The risk is group dynamic pulls paces up. If reps drift to HM-or-faster on what should be a recovery jog, the rule's escape valve (skip the reps, easy with the group) gets used. Worth noting honestly in Strava either way.
- **Fri May 22 HR at Z2.** First explicit-Z2 long run since the framing changed. If 140–150 sits comfortably, the build is on track. If it requires conscious effort to keep HR in the band, fitness is still rebuilding and Week 4 holds the long at 24 km rather than going to 28.
- **Niggle reports.** Nothing flagged so far. Achilles/calves remain the watch list given the post-100k + race + interval-Tuesdays loading sequence.
