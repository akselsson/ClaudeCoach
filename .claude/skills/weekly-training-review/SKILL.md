---
name: weekly-training-review
description: Run a 14-day training review for the ClaudeCoach running coach. Compares the most recent 14-day plan in `analyses/` against actual Strava activity, surfaces discrepancies, asks the user about them before writing anything, then produces a new dated analysis file containing the review and a fresh detailed 14-day plan. Use this whenever the user asks for a "weekly review", "training review", "check in on training", "how's the build going", "plan the next two weeks", or any variant of "look at what I did and tell me what's next" — even if the word "review" isn't used, if the request is about taking stock of recent training and deciding what comes next, this is the skill.
---

# Weekly training review

This skill drives the recurring training-review loop for the ClaudeCoach notebook. The goal is **continuity**: each new plan starts from honest reflection on whether the previous plan was actually executed, and any deviations are understood (not just papered over) before the next 14 days are committed to.

It assumes the conventions in the project's `CLAUDE.md` — analyses live as dated markdown files in `analyses/`, the Strava skill at `.claude/skills/strava/strava.py` is the canonical way to read training data, and the season plan / current training block are already documented there.

## Why this skill exists

A coach who only writes new plans and never compares them to reality drifts. The user has a calendar of races (most importantly Berlin Mauerweglauf as the A-race — see `analyses/2026-05-03-season-plan-overview.md` or whatever the most recent season-plan file is). Sticking to the season strategy depends on noticing **why** sessions were missed, swapped, or added — fatigue, travel, niggle, weather, life — because the right correction depends on the cause. Mechanically rewriting the plan without that conversation produces advice that looks confident but isn't grounded.

So the heart of this skill is the bit where you stop and ask. Do not skip it.

## The workflow

Follow these phases in order. Don't write the new plan before finishing phase 3.

### 1. Orient: read the most recent context

Before fetching anything, read:

- The most recent files in `analyses/` (sort by filename, newest first). At minimum read:
  - The most recent **season-plan** or **race-plan** file (gives the macro structure and A-race date).
  - The most recent **training-block** or **weekly-review** file (this is the plan we're reviewing against).
- Anything else in the last 2–3 dated files that might mention niggles, recovery, or decisions the user committed to.

If there is no prior plan in `analyses/` at all, this skill doesn't apply — tell the user and offer to write a first season plan or training block instead.

State briefly to the user which prior files you're using as the baseline (e.g. "Reviewing against `2026-05-03-block-1-weeks-may4-jun7.md`, which covered May 4 – Jun 7"). This makes the review legible and lets the user correct you if they have a newer plan you missed.

### 2. Pull what actually happened

Use the `strava` skill to fetch the last 14 days of activity. **Always** pass `--with-description` for reviews — workout structure ("4 x 1 km", "2 x 3 km tröskel", "fartlek") lives in the description field, and without it you'll mistake interval workouts for moderate easy runs:

```bash
.claude/skills/strava/strava.py recent --since 14d --type Run --with-description
.claude/skills/strava/strava.py weekly-volume --weeks 4 --type Run
```

Pull cycling separately if relevant — commute rides at zone 2–3 are not free recovery:

```bash
.claude/skills/strava/strava.py recent --since 14d --type Ride
```

#### Drill into hidden quality

A run's average HR over 60–90 minutes can hide what was actually a hard workout. Before you describe any run as "easy", check:

- **Description** — explicit structure ("4 x 1 km", "tröskel", "intervals", pace targets)
- **`max_heartrate − average_heartrate`** — a gap of ≳25 bpm strongly suggests intervals; an easy run is much tighter
- **Suffer score** — 60+ on a 7–10 km run is a quality session, not recovery
- **Activity name** — sometimes "Morning Run" is fine; sometimes it's the user being terse about a threshold workout

For any run that trips one of these flags, fetch `activity <id>` and look at `splits_metric` (per-km HR). A clear sawtooth (high → low → high → low) is interval structure; a smooth ramp from warm-up to a sustained higher band is threshold or progression. Either way, treat it as a quality session and record what was actually done.

#### Sub-agent for per-session characterization

For any session that needs more than a glance at averages — anything tripping the hidden-quality flags above, or any run flagged in the description as structured — delegate to a sub-agent (the general-purpose Agent tool) running the `characterize-activity` skill. **Always use a sub-agent for this**, not a direct call in the main thread: the characterizer's JSON output and per-session number-crunching belong off the main context, and the sub-agent's job is to return a short summary (effort tag, primary focus, top zone percentages, load relative to other sessions in the window, structural notes, drift if relevant) plus a one-line verdict on whether it matched the planned session.

A reasonable sub-agent prompt: "Run `characterize-activity` on activity `<id>`. The plan said `<planned session>`. Report back a 4–8 line summary: effort rating, primary focus, top 2–3 HR-zone percentages, training load, structure (interval count if any), drift if notable, and a one-line verdict on whether this matched the plan." Spawn one sub-agent per session that needs drilldown — they're cheap and they keep the main thread focused on the cross-session story.

For obvious easy aerobic runs that don't trip any flags (modest HR, no structured description, no suspicious suffer score), skip characterization entirely — `recent` plus a glance at average HR is enough. Reserve sub-agents for sessions that actually need the drilldown.

Do **not** dump raw JSON into the analysis file. The analysis file is a narrative; the JSON stays in the sub-agent's context.

### 3. Compare and ask — this is the important part

Build a mental (or scratch) table of: planned session → actual session → gap. Look specifically for:

- **Missed sessions.** A long run that didn't happen, a quality day that became an easy day.
- **Swapped sessions.** Long run on Sunday instead of Saturday, threshold replaced by easy.
- **Extra sessions.** Unplanned races, unplanned long runs, double days.
- **Intensity drift.** Easy runs done at HR 150+ when the plan said <140. Threshold sessions done well below or above the prescribed HR band.
- **Volume mismatch.** Weekly km substantially over or under the plan target.
- **Niggle / recovery signals.** Activities cut short, abnormal HR-to-pace at easy effort, gaps that look like forced rest.
- **Hidden quality.** A run logged as "Morning Run" with avg HR 154 may actually be a 2×3km threshold session — see "Drill into hidden quality" in phase 2. If you missed this on the first pass, the rest of the comparison will be wrong.
- **Companion / paced runs.** A run titled with a friend's name or a race name (e.g. "Vårmilen med Emma") may be a social pace job rather than a stimulus for the user. Ask before assuming it's training load.
- **Cycling load.** Don't assume rides are recovery. Average HR 130+ on a 17 km commute is zone 2–3 aerobic work; multiple double-commute days adds up. Note rides explicitly when reviewing fatigue.

Now **stop and ask the user about every meaningful discrepancy** before drafting the new plan. Concrete is better than vague — quote the planned session and the actual data. Examples:

- "Saturday May 16 was scheduled as a 15 km easy rebuild run, but I see a 22 km run at HR 152. What happened — did you feel ready to extend, or did the route push you longer?"
- "The Wednesday threshold (4×8 min @ HR 158–163) doesn't appear. I see a 10 km run at HR 148 instead. Was that a deliberate swap, or did the session not happen?"
- "There's no run logged Thu–Sat last week. Travel, illness, niggle, or just rest?"
- "Easy runs this week averaged HR 148 vs. the <140 target. Heat, fatigue, or watch strap?"

A few rules for asking well:

- **Ask, don't assume.** "It looks like you skipped Thursday — was that planned?" is fine. "You skipped Thursday again, you need to be more consistent" is not. We don't know yet.
- **Group your questions.** One message with 3–5 concrete questions beats five round-trips.
- **If everything matched the plan, say so explicitly** and ask one calibration question instead (sleep, energy, niggles, anything not visible in Strava). Strava data alone never tells the whole story.
- **Always ask about subjective state.** Sleep, soreness, niggles, life stress, motivation — these are invisible to Strava and decisive for the next plan.

Wait for the user's answers. Then proceed.

### 4. Write the new analysis file

Filename: `analyses/YYYY-MM-DD-weekly-review.md` using today's date. If today already has a weekly review, add a short slug suffix (e.g. `-evening`) — don't overwrite.

Structure:

```markdown
---
date: YYYY-MM-DD
type: weekly-review
summary: <one-line summary of where the build stands and what the next 14 days do>
---

# Weekly review — <date range covered, e.g. May 11–24>

## How the last 14 days went

<2–4 short paragraphs. Volume vs target, key sessions hit or missed, what the
data + the user's answers tell us about fitness and recovery. Reference the
prior plan file by name. Be honest — if the block went sideways, say so.>

## Discrepancies and decisions

<Bulleted list. For each meaningful gap between plan and actual, name it and
say what we decided after talking. Example:>

- Threshold session on Wed May 13 was swapped for an easy 10 km. Reason: legs
  still heavy from the half. **Decision:** push first threshold to week 3 of
  the new plan instead of forcing it next week.
- Long run on Sat May 16 ran 22 km instead of the prescribed 15. Felt good,
  HR 152 controlled. **Decision:** OK as-is, no recovery cost flagged. Treat
  next long run as the planned 24 km, not a step up from 22.

## Next 14 days — <date range, e.g. May 25 – Jun 7>

<Day-by-day plan in the same format as prior training-block files: a table per
week with Day | Session columns. Include HR targets and any pacing notes.>

### Week of <date> — <theme, e.g. "base build, first quality">

| Day | Session |
|---|---|
| Mon | ... |
| ... | ... |

**Week target:** ~XX km running.

### Week of <date> — <theme>

| Day | Session |
|---|---|
| ... | ... |

**Week target:** ~XX km running.

## What I'm watching for

<3–5 bullets: signals that would make us course-correct before the next
review. Resting HR drift, niggles to monitor, sleep, life events.>

## What changes from the prior plan, and why

<Short paragraph. If the new 14 days deviate from what the prior plan or season
plan implied, name the change explicitly and the reason. If nothing changed,
say "Continues the prior plan as scheduled."

This section exists so a future Claude session reading the file can
reconstruct the reasoning, not just the prescription.>
```

### 5. Reality-check before handing back

Before declaring the review done, check:

- Does the new 14-day plan respect the season plan and the A-race date? (Don't quietly slide a hard week into taper, don't skip back-to-back weekends if the season plan needed them.)
- Are HR zones and paces continuous with what the prior plan and recent Strava data show? If the user has been running easy at HR 145 because of heat, "easy <140" might be wrong for the next two weeks.
- Did you actually use the user's answers from phase 3? If a discrepancy was discussed but doesn't show up in either the discrepancies section or the new plan, you missed it.
- Is the file skimmable for a future session? Headings, tables, no JSON dumps, no fluff.

Then summarize for the user in chat: 1–2 sentences on what the review concluded and 1–2 sentences on what the next 14 days look like. Link to the file you wrote.

## Things to avoid

- **Writing the new plan before asking about discrepancies.** Tempting, but it makes the asking pointless.
- **Pasting raw Strava JSON into the analysis file.** Summarize.
- **Treating the season plan as immutable.** It's the strongest prior, but if 14 days of data say the build is too aggressive, name it and adjust — don't pretend the data isn't there.
- **Treating the season plan as suggestion.** Equally bad in the other direction. If you propose dropping back-to-back weekends right before the A-race specificity block, you'd better have a reason and you'd better say it out loud.
- **Creating a generic plan.** "Easy run" with no distance or HR target is not a plan. Concrete sessions, concrete numbers, like the existing files.
- **Skipping the "what changes and why" section.** Future sessions can read tables; they can't reconstruct intent.

## Edge cases

- **No Strava data in the period (injury, illness, deload).** Skip phase 3's volume comparison; ask about the cause. The new 14-day plan is a return-to-running plan, not a continuation.
- **The most recent plan in `analyses/` is older than 14 days.** Cover whatever range the prior plan addressed, not a strict 14 days. State the actual range you're reviewing.
- **A race happened in the window.** Read the race-day plan if there is one; review against bail criteria and pacing rules, not just volume.
- **The user asks for a review but credentials aren't set up.** Follow the strava skill's bootstrap instructions in `.claude/skills/strava/SKILL.md` first. Don't fake the data.
