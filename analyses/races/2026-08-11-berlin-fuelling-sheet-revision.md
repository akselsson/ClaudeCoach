---
date: 2026-08-11
type: race-plan
summary: Patrik rebuilt the Berlin fuelling plan as a live Google Sheet keyed to the 26 VPs, replacing the static CSV as the operating artifact. The architecture change is that mix is now carried as concentrate and diluted in the stomach rather than in the flask — 3 skopor per 450 ml flask (20%) to the km 33 bag, 2 skopor (13.3%) from there on, with plain water drunk alongside on every leg. Effective concentration lands at 6–13%, and 6.6–8.7% through the 35–37 C crux, which is what the execution card wanted. Records the fact that 20% concentrate is TESTED, not assumed — it dissolves if pre-dissolved in a little water, and Patrik has drunk 1.5 flasks/h of it early in runs (~135 g/h) — which retires the card's warning that 10% in heat was untested territory. Two arithmetic errors were found and fixed: the extra-salt formula credited `Sportdryck beräknat` instead of `Sportdryck actual`, and the gel-salt lookup returned Umara values for Maurten gels (unsorted lookup range), crediting 5.2 g of salt that did not exist. Gels are now Maurten-only, deliberately decoupling carbohydrate from sodium. Consequences for packing: extra salt rises to 16.4 g (~13 U Hydrate equivalents against 11 packed), of which ~6 come out of bag 3 alone, and bag 3 needs 600 g of powder against 540 packed. Carb total stands at 1795 g / 95 g/h flat; Patrik has decided to taper by feel rather than by schedule, so this file records the trigger list that decision needs.
---

# Berlin Mauerweglauf — fuelling sheet revision

**Race:** Sat 2026-08-15, start 06:00, 162.1 km, 26 VPs, 3 drop bags (km 33 / km 70 / km 102).

This file records the changes made on Aug 11 to the fuelling plan in `races/2026-08-10-berlin-hydration-execution-card.md`. **The card is still the reference for cooling, decision gates, red flags, thermos technique and caffeine — none of that changed.** What changed is how carbohydrate, fluid and sodium are carried and counted.

**The operating artifact is now a Google Sheet**, not `races/2026-08-10-berlin-checkpoint-fuelling.csv`. The CSV and `scripts/gen_vp_sheet.py` are superseded for race day; keep them as the derivation of the VP table (official km marks, cut-offs, ETA scaffold, air temperature), which the sheet inherited unchanged.

---

## The architecture change: dilute in the drinker, not in the flask

The card already argued for adding water alongside full-strength mix rather than pre-diluting the powder. The sheet takes that one step further: **the mix is now carried as concentrate.**

| | Skopor per 450 ml flask | Concentration in the flask |
|---|---|---|
| Start → VP 5 (km 0–27.8) | **3** | **20%** |
| VP 6 → finish (km 33–162) | **2** | **13.3%** |

Plain water is drunk alongside on every leg. What reaches the stomach is the ratio that matters:

| Block | Effective concentration | Card target |
|---|---|---|
| A · km 0–33 | 6–11% | ~11% |
| B · km 33–70 | 6.7–12.5% | ~9.8% |
| **C · km 70–102** | **6.6–8.7%** | **~7.2%** |
| D · km 102–128 | 5.2–9.6% | ~8.1% |
| E · km 128–162 | 9.4–10% | ~10% |

**The crux block lands almost exactly on target.** The design is sound and the card's concentration reasoning survives intact — it is now delivered by a rule you can execute rather than by a number you have to remember.

**Why this is better than the card's version:** the mix becomes a countable object. "Half a flask out of this VP" (block A) or "one full flask out of this VP" (everywhere after) requires no arithmetic at hour ten. That was the stated goal of the rebuild and it is achieved.

**The one thing it does not make countable is the water**, which is still expressed in millilitres. Since the water is what makes the concentrate safe, that asymmetry is the weak point of the design. The practical rule: **one mix flask + one water flask per leg** through blocks B–D covers 900 ml, which is enough for every leg except two — carry a third flask on VP 11 → VP 12 (7.7 km) and VP 19 → VP 20 (8.7 km / 1160 ml, the longest carry of the race).

---

## What is now tested rather than assumed

**This supersedes the card's stated risk that "10% mix in real heat is untested for you."**

- **20% concentrate dissolves**, provided the powder is first dissolved in a small amount of water before topping up the flask. Tested multiple times.
- **Patrik has drunk ~1.5 flasks/h of 20% concentrate early in runs — roughly 135 g/h.** Not once; repeatedly.

Two consequences worth stating plainly so a later session does not re-open them:

1. **Block A needs no further validation and should not be softened.** The sheet asks for 225 ml of concentrate per leg — about 84 g/h from drink — which is well inside proven territory. The Tuesday-before-the-race mix test the card prescribed is unnecessary and was not run.
2. **The Jul 30 failure was 20% *in heat*, not 20% as such.** Those are different questions and the sheet answers them separately: full concentrate where it is proven (cool, fresh, block A), diluted to 6.6–8.7% where it failed (hot, deep, blocks C–D). The design is well matched to the evidence.

---

## The salt calculation — derivation and two fixed bugs

The sheet computes sodium from first principles rather than from a fixed cadence. The formula, verified against the rows:

```
Extra salt (g) = (Dryck behov × 0.0026)
               − salt in [Sportdryck actual]
               − [salt från gel]
```

with `0.0026 g salt/ml`, `0.6333 g` per skopa, and the result divided by `1.3 g` to express it as a fraction of a U Hydrate.

**Two errors were found on Aug 11 and both are now fixed.**

### Bug 1 — the mix-salt term credited `Sportdryck beräknat`

`beräknat` is the volume of mix required to hit the carb target; `actual` is the volume actually planned. They differ on nearly every row, so the sheet was crediting sodium from mix that would not be drunk — and the sign flipped depending on the row. Start was under by a third of a tablet; VP 1 called for 0.2 g when the correct answer was *none needed*. Aggregate over-prescription was ~2 g. Repointing the term at `Sportdryck actual` resolves every row to within display rounding (spot-checked at Start, VP 6 and VP 19).

### Bug 2 — the gel lookup returned Umara values for Maurten gels

The reference table was not sorted by carbohydrate, so a 25 g gel returned Umara gel 20's **0.70 g** of salt instead of Maurten 100's **0.05 g**, and a 30 g gel returned 0.05 instead of Umara gel 30's 0.54. Neither combination existed anywhere in the table.

**This was the bigger error: eight gels × 0.65 g = 5.2 g of salt credited that did not exist — four tablets' worth.** Sorting the lookup range fixed it.

### Gels are now Maurten-only, and that is a deliberate decoupling

Carbohydrate and sodium have different optimal curves in a hot race — carbs should come down late, sodium should not — and a high-sodium gel welds them together. Maurten's near-zero sodium means **every milligram of salt now comes from two sources that are counted directly: the mix and the tablets.** Gel schedule is 9 × Maurten 100 (25 g) + 1 × Maurten 160 (40 g) at VP 19 = 265 g of the 1795 g total.

### What the fixes cost in tablets

Extra salt rises **13.2 g → 16.4 g**, i.e. **~13 U Hydrate equivalents against the 11 in the card's packing list**. It is not evenly distributed:

| Bag | Covers | Extra salt | Card packs | Action |
|---|---|---|---|---|
| Carried from start | Start–VP 5 | 2.4 g (~2) | 2 | ok |
| Bag 1 · km 33 | VP 6–11 | 2.8 g (~2) | 3 | ok |
| Bag 2 · km 70 | VP 12–16 | 3.2 g (~2.5) | 3 | ok |
| **Bag 3 · km 102** | **VP 17–finish** | **8.0 g (~6)** | **3** | **double it** |

**Bag 3 carries the whole sodium load for the last 60 km with essentially none coming from gels.** VP 19 alone asks for 1.7 g — take two there, not one.

### A property of the model worth knowing

Because replacement is pinned to fluid **drunk** (not sweat lost) at 0.0026 g/ml, and total fluid is 18.9 L, the sodium answer is arithmetically determined: **~49 g NaCl ≈ 1020 mg sodium/h.** That is the top of the defensible band for 36 °C, and it was arrived at by construction rather than chosen.

Using fluid drunk as the basis under-estimates true losses in block C (where sweat rate exceeds what the gut absorbs — the card is explicit that this deficit is unavoidable) and over-estimates them at night. Both errors run in the safe direction; full replacement of real sweat sodium across 19 hot hours would be far too much salt.

**The useful property is that sodium is now coupled to fluid.** The night block currently drinks 1000 ml/h at 25–28 °C where the card wanted 600 — cutting that drops the tablet count with it. One change, both budgets.

---

## Carbohydrate: tapering by feel — a recorded decision

**Totals stand at 1795 g / 95 g/h, flat.** `Mål g kolhydrater/h` is a single cell set to 90, so `Carbs önskat` does not taper and the delta column reads a healthy +92 against a target that is itself higher than the card's 88→78→68→65→60.

Per-leg rates, for reference — legs run 25–70 min, so the quantisation to half- and full-flasks makes this lumpy:

| Leg out of | g/h | | Leg out of | g/h |
|---|---|---|---|---|
| Start | 95 | | VP 12 | 87 |
| VP 2 | **133** | | VP 14 | 103 |
| VP 6 | 125 | | VP 17 | 94 |
| VP 9 | 115 | | VP 19 | 86 |
| VP 11 | 95 | | VP 25 | 100 |

**Decision: Patrik will cut back by feel rather than on a schedule.** He has done one-to-two-hour stretches on water and electrolytes alone in the late stages of past races to recover a failing gut, and prefers to hold that lever in reserve rather than pre-commit to a taper he may not need. **That is the plan of record — do not re-prescribe a fixed taper.**

Two things make that decision safer without changing it.

### The lever is already countable

The sheet's version of "cut back" is **half a flask instead of a full flask** — 30 g instead of 60 g on that leg — or dropping the gel. No new arithmetic, no new equipment. Decide it at the VP, execute it on the leg.

### Nausea is a lagging indicator — act on these instead

The open question was *when*. In heat, by the time the gut is unmistakably in trouble it has been slowing for 30–60 minutes, and the recovery then costs an hour or two rather than twenty minutes. These arrive earlier, in roughly this order:

1. **The mix stops tasting good** — turns cloying or metallic. Earliest signal by a wide margin, and easy to dismiss.
2. **Not wanting to drink at a VP** when the plan says to. Treat reluctance as data.
3. **Fullness or sloshing** — gastric emptying has already slowed.
4. **Burping.**
5. **Nausea.** By here you are late.

**Act at 1 or 2, not at 4 or 5.** The cost of a half-flask leg that turns out to have been unnecessary is roughly nothing.

### Escalation, amended

The card's ladder stands, with one correction drawn from Patrik's own race history:

1. **Shift toward water** — more water, less mix, same flasks. First response.
2. **Water and electrolytes only.** The card said 20 minutes; **Patrik's experience is that this takes one to two hours to work.** Budget for the longer version rather than declaring it failed at the 20-minute mark and going back to carbohydrate too early.
3. **Rebuild at ~30 g/h** — cola and one gel — then work back up.

**The km 70 and km 102 gates are where this judgement actually gets made**, per the card and per `schedule/2026-08-11-race-week-evo-sl-sync.md` — it cannot be made reliably at running pace late in the race.

---

## Packing changes from the card

| Item | Card | Sheet needs |
|---|---|---|
| Powder — carried from start | 270 g (3 × 90) | 270 g — **exact, no spare** |
| Powder — bag 1 | 360 g | 360 g — **exact, no spare** |
| Powder — bag 2 | 360 g | 300 g — ok |
| **Powder — bag 3** | **540 g** | **600 g — 60 g short** |
| **U Hydrate — bag 3** | **3** | **~6** |
| Gels | ~6 mixed | 9 × Maurten 100 + 1 × Maurten 160 |

Total powder is unchanged at ~1530 g (51 skopor), but the sheet now consumes all of it — the card's "17 portions, 14 consumed, 3 margin" no longer holds. **Pack 20 portions to keep a real margin**, and note that the start bag and bag 1 currently have none.

---

## Columns removed from the sheet — flagged, unresolved

The Aug 11 cleanup removed `Ratio` (correctly — it said "mix only" on rows prescribing 300–500 ml of water), and also `Notes`, `Cooling at this VP`, `Salt at this VP` and `Fyll på sportdryck?`.

Those carried: ice-into-flasks-first at VP 6 and VP 12, night gear and first caffeine at VP 17, the shoe abort at VP 6, the de-escalation check at VP 8, walk-the-climb at VP 20, and headlamp-mandatory by VP 21.

**The columns kept are the ones that could be reconstructed; the ones removed are the ones that cannot.** They now live only in the execution card, which means two documents on race day. Worth restoring the notes column before Friday, or accepting the card as a second artifact deliberately.

---

## Still open

1. **Drop-bag hand-in — Saturday morning or Friday evening?** Unchanged from the card; the km 70 and km 102 ice plan depends on it.
2. **Do the VPs have ice?** Ask at the briefing.
3. **Re-check the forecast Wed and Fri.** Pack for the hot case regardless.
4. **Buy/confirm the extra tablets** — 13 U Hydrate equivalents, 6 of them into bag 3.
5. **Night fluid** — 1000 ml/h at 25–28 °C is ~1.6 L more than the card's 600 ml/h, and it drags the tablet count up with it. The one number in the sheet still worth changing before Friday.
6. **The pacing scaffold opens at 5:45/km for 28 km** against the card's rule that time banked in the cool morning is repaid with interest at 15:30. Fuelling does not break if the race is slower — amounts are pinned to VPs, so a slower race automatically lowers g/h and ml/h — but the two documents disagree about the start.
