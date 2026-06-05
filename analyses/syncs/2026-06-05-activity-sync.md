---
date: 2026-06-05
type: activity-sync
summary: Fri Jun 5 long run — the biggest of the build, prescribed 32 km Z2 (140–150) and executed almost exactly to spec: 31.6 km, avg HR 143, 66% of moving time in the 140–150 steady band, 0% above threshold. Textbook steady long run — flat splits (334.6 → 334.4 s/km half-to-half, zero fade), cardiac drift just 0.36 bpm/km (vs the 0.54 May-29 baseline, both well under the 1.5 governor). The Week-5 governor ("hold at 30 km if Tuesday ran hot or legs read heavy") was live — Tue Jun 2 *did* run hot (VO2 to 95% max) — but never needed to fire: legs absorbed it and ran full distance clean. Body all clear: no pinky-toe pressure, calves/Achilles quiet. Two deviations, both benign: (1) Gear was the **Altra Torin 8**, not the prescribed Megablast — so this is NOT a second sustained-Megablast long (the calf rocker-load watch eases this week) and the Megablast-specific pinky-toe test is deferred again (an all-clear in Torin says nothing about the Megablast toe-box). (2) ~31.6 vs 32 km — a rounding non-event. Load TRIMP 317 / Edwards 354 / suffer 213 — high in absolute terms but entirely volume-driven, not stress. Pure observation — does not change the forward plan.
---

# Activity sync — Fri Jun 5 long run (31.6 km Z2)

Strava id 18796055680. "Löpning vid lunch", no description. 31.6 km, ~2h59 moving (10,747 s), avg HR 143.4, max HR 158, suffer 213. TRIMP 317, Edwards 353.9.

Gear: **Altra Torin 8** (`g29334468`) — the easy-day shoe, used here for the Z2 long instead of the prescribed Megablast. (Note: the `recent` list endpoint returned `gear: null` for this activity; `activity <id>` detail carried the `gear_id` correctly — read gear from the detail endpoint, per the CLAUDE.md gear workflow.)

Prescription was Week 5 Fri (`schedule/2026-05-30-weekly-review.md`): **"Long run: 32 km, Z2 (HR 140–150). Megablast. Biggest of the build. Last 5 km may drift to 150 if it feels right. Full nutrition rehearsal."** Governor stated explicitly: *"if Tuesday's quality ran hot or legs read heavy Thu/Fri, hold at 30 km — don't grind 32 to hit the number."* Baseline to match: May 29's drift 0.54 and fast finish.

## What happened (characterized, sub-agent)

A true steady long run, uniform throughout — 32 laps but no structure, paced flat:

- **Time in zone (HR):** easy <140 19.3% · **steady 140–150 65.9%** (the bulk) · sub-threshold 150–160 14.8% · threshold 160+ **0%**. Pace tightly clustered (lap-pace CV 0.083). Squarely the prescribed Z2 long — never reached into quality.
- **No fade, no drift.** First/second-half pace flat (334.6 → 334.4 s/km). Cardiac drift 0.36 bpm/km — *under* the May-29 baseline of 0.54, far under the 1.5 governor. HR rose only ~5 bpm half-to-half (140.9 → 146.2), max 158 (86% of max 184). No surges, no walk breaks, no late grind.
- **HR reliability:** clean. Zero time above sub-threshold and a low, well-behaved drift slope — the wrist monitor's hard-effort under-read problem doesn't apply to a steady long run. Avg 143 / max 158 is internally consistent. No concerns.
- **Load:** TRIMP 317, Edwards 354, suffer 213 — the biggest single-session load of the block, but driven by ~3 hours of duration, not intensity. Volume, not stress.

So: prescribed 32 km Z2 long → executed 31.6 km Z2 long. About as on-prescription as a session gets — distance, HR band, drift, and finish quality all matched the design.

## The governor that didn't need to fire

The Week-5 governor was genuinely live: Tue Jun 2's quality ran *hot* (a real VO2 4×4 to ~95% max, back half over the 165 back-off line — see `syncs/2026-06-02`). The plan said hold at 30 km if that happened or legs read heavy. They didn't read heavy: full 31.6 km at flat pace, drift *below* the clean-baseline, fastest-finish-capable body. **The hot Tuesday was absorbed without cost** — which extends the Jun 2 readiness signal: not only did the body handle a VO2 4×4 and report it as good, it backed it up with a clean biggest-long-of-the-build three days later. Block 1's long-run progression (24 → 29 → 31.6 km) closes exactly where the rebuild aimed.

## Deviations and decisions

- **Gear: Torin 8, not the prescribed Megablast.** The Torin was scoped to easy duty in the rotation (`schedule/2026-05-26-shoe-rotation.md`); running the full Z2 long in it is a deviation. **Benign, but two real consequences:**
  - This is **not** a second sustained-Megablast long. The "calves/Achilles into the second sustained-Megablast week — the rocker-loading pattern that surfaces calf complaints" watch item from May 30 is **eased this week** — the two-long-Megablast-weeks pattern didn't happen. (Body all-clear regardless.)
  - The **Megablast pinky-toe test is deferred again.** Body was all-clear today, but in the *Torin* — that says nothing about the Megablast toe-box that pinched at 29 km on May 29. The Megablast-specific-vs-foot/sock question stays open; still needs a sustained Megablast (or Evo SL fit-check) run to resolve. The Jun 2 fast Evo SL read (quiet at 6.7 km) remains the only post-May-29 toe-box data, and it was short/weak.
  - Why Torin for the long? Not captured. If deliberate (e.g. saving the Megablast, or the pinky-toe memory steering away from it for a 32 km effort), worth noting forward — that itself would be a soft Megablast signal.
- **~31.6 vs 32 km.** Rounding non-event — full distance, no governor hold. No concern.
- **Nutrition rehearsal** (gel/30 min, ~500 ml/h) — prescribed, not captured in the data. Log separately if you want it tracked; the clean late-run HR/pace suggests fuelling held up.

## Watch list (carried from May 30 / Jun 2, updated)

- **Pinky toes:** all-clear today but in the **Torin**, not the Megablast — the lingering May-29 Megablast toe-box signal is **untested this week**, not cleared. Next sustained Megablast or the deferred Evo SL fit-check is still the real test.
- **Calves / Achilles:** clear after the biggest long of the build. The Megablast rocker-load watch is paused this week (ran in Torin); resumes whenever the Megablast goes long again.
- **RHR** still last logged 46 (May 7) — now overdue through a quality + 31.6 km week. A fresh reading early next week is the cleanest check on whether this load landed harder than the clean drift suggests.
- **Long-run HR/GAP drift:** 0.36 today vs 0.54 (May 29) — the ramp is comfortably inside fitness. Baseline for Jun 12's ~34 km.

## Forward note (does not change the plan)

Pure post-hoc record — no forward-plan change, no viz regeneration. Per `schedule/2026-05-30-weekly-review.md`, the back half of the soft B2B is the **daughter long run ~21 km, Z1 (HR <140), Torin** on Sat or Sun (her pick of day), then Week 6 (Block 2 base-build) opens Mon Jun 8 with the next group quality Tue Jun 9 and the ~34 km long Fri Jun 12. The next 14-day review is due around Jun 13.
