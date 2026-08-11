---
date: 2026-08-11
type: activity-sync
summary: The Tue race-week leg, 4 days out — 8.03 km, 43:43, avg HR 137.7, Adidas Evo SL Silver. Two things happened today and the second matters more than the run. (1) The naprapat appointment finally landed and answered the build's oldest open question in the permissive direction: run it, stop at durable pain. That converts the Aug 7 decision tree to "static → race as planned with the protocol and a low DNF threshold", and amends the race-day stop rule. The neuro red-flag list was NOT confirmed and stays as written-but-unverified, so the operative rule is durable pain OR any neuro red flag. (2) The run itself was fine but ran a notch warm — tagged steady_aerobic, not easy, with 32.6% in the 140–150 band and a gratuitous closing surge to 157 in the last 640 m. Load was still the lightest of the last four sessions (TRIMP 74.9). The tracked descent penalty did not worsen: down/flat 0.956 against 0.947–0.949 across Aug 6/7/9, the best of the series. Hip unchanged from Aug 9. No change to the remaining race-week schedule.
---

# Activity sync — Tue Aug 11: the Evo SL leg, and the naprapat verdict

Gear: Adidas Evo SL Silver (Evo SL (outdoor))
Distance 8.03 km · 43:43 · 5:27/km · avg HR 137.7 / max 157 · 63 m gain · cadence 174.8 spm · Strava id 19692028700

Executing the Tue leg of race week from `schedule/2026-08-07-weekly-review.md`: easy 8 km in the Evo SL. Characterized via `characterize-activity` in a sub-agent.

**Read in one line: the naprapat cleared the start, and the run was slightly warmer than prescribed in a way that costs nothing but shouldn't repeat on Thursday.**

## The naprapat answer — the headline

The appointment booked at the Aug 7 review happened. The answer to question (1) — *does running 161 km risk actual harm, or only discomfort?* — was, in Patrik's paraphrase: **go on until you feel actual durable pain.**

This is the most consequential sentence of the build's last three weeks, and it resolves the question in the permissive direction. The Aug 7 review had framed the worst case as referred symptoms from a lumbar disc, against a standing season rule of *DNF over injury, every time*, on the reasoning that a disc is a multi-season problem while Berlin is one race. The naprapat's answer reframes the current känningar as **cost, not damage**. Running on them is not accruing injury; it is accruing discomfort.

**What this changes:**

- **The start is no longer a live question.** Aug 7 set a trajectory rule for Aug 8–14: improving → race as planned; static → race with the protocol and a low DNF threshold; worsening → the start itself becomes a conversation on Aug 12–13. The hip is **static** (see below), so the middle branch applies. That conversation does not need to happen.
- **The race-day stop rule gains a pain criterion**, replacing "unknown." Previously the hip protocol had only neuro red flags as explicit DNF criteria, with ordinary aching deliberately excluded and no guidance on where muscular pain crossed a line. Now there is one: **durable pain** — pain that persists, rather than the awareness that comes and goes.

**What it explicitly does not change, and is not being treated as settled:** the Aug 7 review asked the naprapat to *confirm or correct the neuro red-flag list* — numbness or pins-and-needles down the leg, loss of strength (knee buckling, foot slapping/dragging), symptoms going bilateral, any bowel or bladder change. That did not happen. "Go until durable pain" is a pain-based rule and is silent on nerve signs, which are categorically different: they can be serious while barely hurting. **The list stands as written but unverified.**

**The operative race-day rule is therefore: durable pain OR any neuro red flag → stop.** Not one or the other.

One honest caveat on applying it: "durable pain" is a rule that gets harder to use the deeper into an ultra you are, because at km 120 everything hurts and the reference point for normal is gone. This is precisely what the formal reassessments at km 70 and km 102 are for — **decide at a stop, sitting down, not while running.** The rule is sound; the judgement it requires degrades exactly when it is needed.

## The hip

Unchanged from Aug 9 — still känningar, never pain, same character. This is now the fourth consecutive session with that description (Aug 6, 7, 9, 11) and it is what "static" means in the Aug 7 decision tree. Not improving, not worsening, and per today's clearance, not a reason to change anything.

## What the numbers say

- **Effort: `steady_aerobic`, not easy.** 63.6% easy (<140), 32.6% steady (140–150), 3.8% sub-threshold (150–160), nothing above 160. Aug 9 by comparison was 82.4% / 17.6% / 0%. A third of this run sat in the steady band, which is why the characterizer declined to call it easy.
- **Load was still the lightest of the four recent sessions, as intended.** TRIMP 74.9, Edwards 67, suffer 32 — against Aug 9 (144 / 117 / 50), Aug 7 (111 / 93 / 38), Aug 6 (91 / 93 / 53). Roughly half Aug 9's TRIMP. Whatever the intensity tag says, the dose was small.
- **No genuine cardiac drift.** The raw slope of 1.49 bpm/km sits on the 1.5 concern line, but it is manufactured at both ends — km 1 averaged only 124 bpm with HR still ramping, and the final 640 m was a surge. Restricted to km 1.0–7.3 the trend *reverses*: 139.5 → 137.8. The honest read is flat.
- **One discrete finishing surge.** All 112 seconds above 150 bpm fall in the last 640 m, peaking at 157. Nothing above 150 anywhere earlier in the run.
- **Pace positive-split** (5:05 → 5:40/km), with the fastest kilometre first while HR was still catching up. Started quick, settled.

### The descent-penalty series — the tracked number, and it held

| | overall m/beat | down:flat | up:flat |
|---|---|---|---|
| Aug 6 | 1.399 | 0.948 | 1.008 |
| Aug 7 | 1.406 | 0.947 | 0.999 |
| Aug 9 | 1.320 | 0.949 | 1.008 |
| **Aug 11** | **1.356** | **0.956** | **1.055** |

**The one measurable mechanical deficit tracked since the niggle appeared did not worsen — it is the best reading of the four.** Overall efficiency also recovered from Aug 9's dip back toward the Aug 6/7 level, which retrospectively supports the Aug 9 call to log that 6% drop rather than act on it: it was duration, heat and accumulated days, not a real efficiency loss.

**Read this as "no deterioration", not as measured improvement.** Today's route was flatter than the others — 15.9% of distance downhill and 14.3% uphill, against ~21–24% each on Aug 6/7/9. Smaller non-flat bins make the ratios noisier, and the 1.055 uphill figure especially should not be over-read.

*Methodology note: no script for this series is checked into the repo, so the sub-agent rebuilt it from the `strava_factor` GAP curve in `.claude/skills/shoe-speed-vs-effort/build_dataset.py` and calibrated against the recorded figures (reproducing Aug 6/7/9 to within 0.001–0.003). Today's numbers are directly comparable to the earlier ones. Worth checking the script in before this series is extended again.*

## Decisions

- **Race the start.** The naprapat's clearance plus a static hip resolves the Aug 7 decision tree to "race as planned with the protocol and a low DNF threshold." No Aug 12–13 conversation about whether to start.
- **Race-day stop rule, final form: durable pain OR any neuro red flag.** Both, not either alone. The neuro list is unverified and stays in force for exactly that reason.
- **Formal reassessments at km 70 and km 102 gain importance, not less.** They are where the durable-pain judgement actually gets made, because it cannot be made reliably at running pace late in the race.
- **Remaining race week unchanged:** off Wed, 5–6 km shakeout + optional 4×20 s strides Thu, off Fri, race Sat. Nothing today argues for a change.
- **Evo SL Silver: no fit issues** over 8 km. It stays as the early-abort backup in the km 33 drop bag. The shoe A/B was already decided on Aug 9 and today did not reopen it.

## The one correction

Thursday's shakeout should be genuinely easy, and it should not have a finishing surge in it. Today ran a notch warm — a third in the steady band, closing at 157 four days before a 161 km race. **The cost today was near zero**, given the run was 8 km and the lightest load of the last four. But the same shape on Thursday, two days out, is a worse trade: there is no fitness available to gain and the strides are already the intended intensity. Run Thursday under 140 and let the 4×20 s be the only fast part.

## Open going into race day

1. **Neuro red-flag list still unconfirmed by a clinician.** Carried forward as a known gap in the DNF criteria rather than a closed item.
2. **Sleep and systemic energy** — flagged Jul 31, unconfirmed Aug 7, unconfirmed Aug 9, still unconfirmed. Four reviews running. This is now the only fully untouched question left.
3. **Travel logistics to Berlin** — assumed Fri Aug 14.
4. **Hip behaviour beyond ~100 minutes.** Structurally unanswerable before the start line; the race-day hip protocol exists because of it. Today's clearance lowers the stakes of this unknown but does not answer it.
