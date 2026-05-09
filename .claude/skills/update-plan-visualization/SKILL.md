---
name: update-plan-visualization
description: Regenerate the single-page training-plan visualization at `viz/plan.html` from the current state of `analyses/`. Use whenever an analysis file that changes the forward training plan has just been written or modified — weekly reviews, race reviews, training-block files, season-plan files. Always run this in a separate sub-agent because the regeneration produces a long HTML file whose content does not need to live in the main thread's context. Do **not** invoke this skill for files that don't change the forward plan (activity characterizations, niggle logs, observation-only notes).
---

# Update plan visualization

This skill regenerates `viz/plan.html` — a single self-contained HTML page that visualizes the full forward training plan from today through the next A-race and the post-A-race chapter — from the current state of `analyses/` and `config/training.json`.

The page exists because the forward plan is spread across several markdown files (a season-plan file, a current-block file, and any reviews dated after the block file). Reading the plan today means cross-referencing three docs. The page collapses them into one legible artifact.

A stale visualization is worse than none — it looks authoritative while lying about what the plan actually says. The job of this skill is to keep `viz/plan.html` honest.

## When to run

Run this skill in a sub-agent **immediately after** any of the following has been written or modified in `analyses/`:

- **Weekly reviews** (`type: weekly-review`) — they amend session detail in their date range and supersede the block file there.
- **Race reviews** (`type: race-review`) — same as weekly reviews; they typically include a "Next 14 days" amendment.
- **Training-block files** (`type: training-block`) — they redefine the block's day-by-day grid, phase shape, and weekly volume targets.
- **Season-plan files** (`type: season-plan`) — they redefine the macro arc, race calendar, priorities.

**Do NOT run** this skill for:

- Activity characterizations (output of the `characterize-activity` skill) — observation-only.
- Niggle logs, sleep notes, or other observation-only files that don't alter forward sessions.
- Pure formatting/typo fixes to existing analyses.

The trigger rule is simple: if the change rewrites or extends what the user is going to *do* in the future, regenerate. If the change records something that has already happened or notes something to monitor, don't.

## Why a sub-agent

The page is ~1,000 lines of HTML. Authoring it pulls a lot of structured detail through context (week-by-week sessions, SVG coordinate computation, phase color tokens). Done in the main thread, it crowds out actual coaching work. Done in a sub-agent, the parent thread sees only the short diff summary and gets on with whatever follow-up the user actually asked for.

This mirrors the existing convention for `characterize-activity` — same justification, same pattern.

## Workflow

### 1. Orient

List `analyses/` newest-first. Identify the **authoritative trio** for today's forward plan:

- The most recent **season-plan** file — provides the macro arc, race calendar, A-race date, season priorities.
- The most recent **training-block** file — provides the current block's day-by-day sessions, weekly volume targets, Block 2 preview.
- Any **weekly-review** or **race-review** dated *after* the block file — these supersede the block's session detail in their date range.

Read each in full. Note the date ranges they cover.

### 2. Resolve conflicts

If a review (weekly or race) covers a date range that overlaps the block file's day grid, **the review wins for that range**. State the resolution to the user before regenerating, e.g.:

> Reviewing against `block-1-rev2.md` (May 4 – Jun 7) with `kungsholmen-race-review.md` superseding May 11–23 (Weeks 2–3). Will regenerate `viz/plan.html` from these.

If two files of the same type cover overlapping ranges (rare), the later-dated file wins.

### 3. Read the HR zone config

Read `config/training.json` and inline the current zone numbers into the header HR-zone strip. The zones aren't decorative — they're the calibration the rest of the plan is written against, and they sometimes shift between blocks.

Use the `hr_zones` array. The page's HR strip shows: easy / steady / sub-threshold / threshold / vo₂ (race-cap), with bpm ranges and the resting/max HR in the panel label.

### 4. Regenerate `viz/plan.html` end-to-end

Full overwrite. Do **not** attempt incremental edits — the page is short enough that a full rewrite is simpler and avoids drift between header SVG coordinates, week cards, and footer manifest.

Preserve the design system (next section). The visual identity is stable across regenerations; the *data* is what changes.

### 5. Report a short diff to the user

Run `git diff viz/plan.html` and summarize what changed in 3–6 bullets. Specifically call out:

- Any sessions whose distance / HR target / day changed.
- Any phase-band shift on the gantt (e.g. recovery extended, taper started earlier).
- New "today" position (which week the today-rule lands on).
- Any new races added or existing races removed/shifted.
- The new total span (start date → final race).

Surface anything that surprises you — if the plan shifted a long run by 2 weeks or moved a race, mention it explicitly so the user can confirm it was intentional.

### 6. Stage `viz/plan.html` alongside the analysis change

The regeneration is downstream of an analysis edit, and the two must stay in lockstep — committing the analysis without the page (or vice versa) leaves the repo inconsistent. So:

- If the analysis change is **already staged** when this skill runs, run `git add viz/plan.html` so it joins the same commit. Don't run `git commit` itself — the user (or the calling skill) decides when to commit.
- If the analysis change is **not yet staged**, leave `viz/plan.html` unstaged too. The next `git add` of the analysis file should include the page; mention this in the diff summary so the calling thread can stage them together.

Don't create the commit yourself. Skill output is artifact + staging + summary, not the commit itself.

## Design system — preserve across regenerations

The page has a deliberate **two-register** identity. Don't change these without asking the user — the consistency is the point.

### Section structure (top to bottom)

1. **Data-instrument header** (dark, full-bleed)
   - Top strip: signal-active line, dashboard label, last-updated date.
   - Title row: `<h1>` season-arc title + a 2–3 line subtitle on the right.
   - Four metric chips: today, days-to-A-race, days-to-B-race, current build week.
   - Season gantt SVG: weekly columns from start date through last race, phase bands, race pins (A in amber, B in sage, C/skipped pinned with dashed marker), today vertical rule in amber.
   - Weekly volume chart SVG: bars per week, baseline at the bottom of the viewBox, helper grid lines at sensible km marks, mono numerals at bar tops.
   - HR zone strip: 5 cells, color-coded left rule per zone, bpm ranges from `config/training.json`.
2. **Transition strip** — gradient half-dark / half-light with an amber hairline rule and a single tracked-out caption (`—— BLOCK NN · WEEK-BY-WEEK ——`).
3. **Editorial training journal** (light, warm off-white)
   - Centered preamble paragraph (Fraunces display headline + Sora body) framing the current block's *why*.
   - Block 1 (current block): one `<article class="week">` per week with a left rail (big italic Fraunces week number, phase tag, dates, volume target) and a right column (intent pull-quote + day-by-day list with session tags).
   - Block 2 (next block): 4 narrative cards in a 2-column grid — phases, not days. Italy / unstructured weeks rendered with a hatched diagonal-line background.
4. **A-race banner** (full-bleed dark) — race name in Archivo Black with one word italicized in amber, race date in mono, 4-stat grid, italic Fraunces creed pull-quote on the right.
5. **Postscript** (light) — post-A-race recovery + B-race description, ends with a left-rule callout for the B-race finish.
6. **Footer** (dark) — source-files manifest with `<code>`-tagged paths, "about this page" notes.

### Type stack

Header (data-instrument):
- **Archivo Black** — display headlines (`<h1>`, chip values, A-race title).
- **JetBrains Mono** — all numbers, labels, captions, dashboard chrome.

Body (editorial):
- **Fraunces** (variable, opsz 9-144, italic capable) — section headings, week numbers, intent pull-quotes, postscript headline.
- **Sora** — body text at 16–17px.

All four loaded from Google Fonts in one `<link>` with `display=swap`.

### Color tokens

```
--bg-dark: #0a0d0e        --bg-light: #f5f0e6
--ink-dark: #e8e6e0       --ink-light: #1f1f1d
--ink-dark-dim: #9aa5a5   --ink-light-dim: #7c756a
--amber: #ffb547          --oxblood: #7a2e2e
```

Phase band palette (gantt):
```
history       #2c3539   recovery       #4a7a7a
reintro       #7aa570   base build     #8eb056 → #b4a850 → #c89a45  (graded)
deload        #7c8a5f   italy/unstr.   url(#hatch) over #5e564a
specificity   #c47340 → #b85a32        taper   #b8c4cc → #d8dde0 (graded)
A-race week   amber outline + accent   post-race rec  #4a6a7a
sharpen       #7a9a8e → #a4baa8        B-race week    sharpen + amber outline
```

The accent amber `#ffb547` is reserved for: the today rule, the A-race pin, peak-volume bar labels, banner accents. Don't dilute it onto generic UI.

### Motion

- One staggered `rise` animation on `.week` and `.narr-card` cards on initial load.
- Pulsing dot in the top-strip "PLAN ACTIVE" signal.
- All wrapped in `@media (prefers-reduced-motion: reduce)` to disable when requested.

### Responsive

Single breakpoint at `920px`. Below that:
- Title row collapses to a single column.
- Chips & HR strip go to 2 columns.
- Week cards collapse the rail above the body.
- Race banner & postscript stack vertically.
- The two header SVGs use `viewBox` + `preserveAspectRatio="none"` and just rescale — acceptable degradation.

### Print

Dark sections render with white background and black text via `@media print`. Animations off. Accent colors preserved on the A-race banner.

## What NOT to change without asking

- The **two-register identity**. Don't make the whole page dark, or the whole page light, or merge the two into a single hybrid surface.
- The **source-file precedence rule** (review > block, block > season-plan, latest > earlier).
- The **`viz/plan.html` location**. The `viz/` directory is intentional — keeps the analyses chronology pure markdown.
- The **font stack**. If a font fails to load (Google Fonts outage etc.), let it fall back gracefully — don't substitute a different Google Font without flagging it.
- The **A-race-only amber accent** convention. The B-race uses sage, not amber, on purpose.

If the user asks to change any of these, do it — but treat it as a real design decision, not a regeneration detail, and update this skill file to reflect the new convention.

## Quick reference — the data the page reads

Per regeneration, you need to extract from the source files:

| Variable | Source |
|---|---|
| Today's date | from environment / current date |
| A-race name, date, distance, role | most recent season-plan |
| B-race name, date, distance, role | most recent season-plan |
| Skipped/C races | most recent season-plan |
| Block name + date range | most recent training-block |
| Block phase narrative | most recent training-block |
| Weekly volume targets per week (block) | most recent training-block (overridden by reviews in their range) |
| Day-by-day sessions per week | most recent training-block (overridden by reviews in their range) |
| Block 2 narrative phases | most recent training-block "preview" section |
| HR zones | `config/training.json` |
| Max HR / resting HR | `config/training.json` |

The data goes inline into the HTML — there is no JSON fetch, no script-driven hydration. It's a snapshot, regenerated on demand.

## Sanity checks before reporting done

- The today rule on the gantt visibly lands on the correct week column.
- The two header SVGs use the same x-coordinate scheme so the today rule and week index strip line up between gantt and volume chart.
- Race pins are in the right week columns. (Check by counting weeks from the start date.)
- Every week card's day-of-week labels match the actual calendar dates of that week.
- The footer "Updated YYYY-MM-DD" reflects today.
- A `git diff viz/plan.html` shows no unintended template-level changes — only content updates.
