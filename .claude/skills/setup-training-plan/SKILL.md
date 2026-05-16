---
name: setup-training-plan
description: Set up a new training plan from scratch for the ClaudeCoach running coach. Use when the user wants to "make a plan", "set up training", "build a season plan", "plan for race X", "start a new block", "I have a new race coming up", "I want to train for Y" — anything where there isn't yet a plan in `analyses/` for the goal in question, or the existing plan is being thrown out and rewritten. This skill pulls long-term Strava data to ground the plan in the user's actual fitness history, then conducts a structured interview about goals, schedule constraints, training-style preferences, and life context before writing a dated plan file. It is **not** for routine 14-day check-ins against an existing plan — that's `weekly-training-review`.
---

# Set up a training plan

This skill creates a new training plan for the ClaudeCoach notebook. The output is a dated markdown file in `analyses/` (a season plan, a race-specific plan, or a multi-week training block — whichever fits the horizon). The job is to produce a plan that's **specific, grounded in the user's real fitness, and aligned with how the user actually lives** — not a generic template.

## Why this skill exists

A plan that doesn't reflect the user's current fitness, weekly rhythm, or motivation gets ignored within a week. Two things make a plan stick:

1. **It starts from real data.** Volume targets, HR zones, and long-run progressions need to land within a sensible delta of what the user has actually been doing — not what a textbook says a runner with their goal "should" be doing. Strava is the source of truth here.
2. **It reflects choices the user owns.** A plan with Tuesday quality sessions when the user always has childcare on Tuesday is a dead plan. The interview phase is how we surface those constraints before they wreck adherence.

So this skill is mostly about asking well, listening, and then writing a plan that the user can recognize as theirs.

## Relationship to the other skills

- **`strava`** — used to pull long-term history. Always invoke as the bundled CLI at `.claude/skills/strava/strava.py`. Don't hand-roll Strava queries.
- **`weekly-training-review`** — runs *after* a plan exists, comparing the prior 14 days to it and producing the next 14 days. If the user already has an active plan and is asking "how am I doing", redirect them to that skill instead.

In short: this skill is the **on-ramp**. The review skill is the **flywheel**.

## The workflow

Follow these phases in order. Resist the urge to draft the plan before phase 4.

### 1. Orient: read the prior context

Before fetching anything or asking anything, read what's already in the notebook. `analyses/` is organised by type — the active doc of each type is the newest file in its subfolder.

- `ls analyses/season-plan/ | tail -1` → read the current season plan (if any). If one exists and the user is asking for a sub-block within it, the season plan is your strongest constraint.
- `ls analyses/schedule/ | tail -1` → read the current detailed schedule (training block or latest weekly review). Tells you what the user is doing right now.
- `ls analyses/preferences/ | tail -1` → read the current training preferences. Standing schedule, style, constraints — these *override* day-of-week defaults in older block plans.
- `ls analyses/races/ | tail -1` → if there's a recent race plan/review, skim it for context on where the user just was fitness-wise.
- Read this repo's `CLAUDE.md` for repo conventions (folder layout, file naming, the no-JSON-dumps rule).
- Note the user's stated A-race(s) and any commitments already on the calendar.

If a plan that already covers the requested goal exists, **stop and ask** before starting a parallel plan: "There's already a plan for X in `<file>`. Do you want to replace it, extend it, or build something separate alongside it?" Plans collide silently otherwise.

If the relevant subfolders are empty (first-ever plan), say so and skip the prior-plan reading — you'll just need a slightly longer interview to fill in the missing context.

### 2. Pull long-term Strava data to build a profile

Use the strava skill to fetch a long enough window that you can talk credibly about the user's training pattern, not just the last week. **At minimum** pull 12 weeks of weekly volume; pull more if the goal is far out (a 100-miler 6 months away justifies looking at 6 months of history).

```bash
.claude/skills/strava/strava.py weekly-volume --weeks 16 --type Run
.claude/skills/strava/strava.py weekly-volume --weeks 16 --type Ride
.claude/skills/strava/strava.py recent --since 4w --type Run --with-description
```

Use this data to answer (silently, for yourself) before you write any questions:

- **Typical weekly running volume** and how stable it is. Is the user a steady 50 km/week runner or do they swing 20–80? Stable runners can absorb a more aggressive build.
- **Long-run habit.** What's the longest run in the last 12 weeks? The 90th-percentile long run? A plan that prescribes a 30 km long run to someone whose current peak is 18 km is fiction.
- **Quality history.** Skim recent activities (with descriptions) for evidence of intervals, threshold, hills. If quality has been absent for months, the plan should reintroduce it gently rather than assume the user can absorb it from week 1.
- **HR zones in practice.** What HR has the user actually been running easy at? If easy is being done at HR 150 and you prescribe HR <140, expect the prescription to be ignored or to make the user feel slow. Either calibrate the zone to reality or address the drift explicitly.
- **Cross-training load.** Don't ignore cycling — a daily commute at zone 2 is real aerobic work and should shape how much you can ask of running.
- **Recent gaps.** Travel, illness, niggles often show up as 1–2 week gaps. Don't pretend they didn't happen.

You don't need to dump this profile back at the user (yet) — it's working memory for shaping the questions and the plan. **Do**, however, summarize it briefly when you ask the questions in phase 3 ("you've been averaging ~55 km/week with a peak long of 22 km — does that match how you feel?") so the user can correct your reading before you commit to it.

### 3. Interview the user

Now ask. The questions below are the canonical set — you don't need to ask all of them every time, but you should consciously decide which to skip and why. **Group questions into one or two messages with 4–6 questions each.** Many round-trips of single questions exhausts the user; a wall of 20 questions paralyses them.

When a question's answer is already obvious from prior analyses, **don't re-ask**. Cite the source ("the season plan has Berlin Mauerweglauf as your A-race on Aug 15 — still right?") and let the user confirm or correct.

#### Goals and horizon

- **What's this plan for?** A specific race (date, distance, terrain), a volume target (e.g. "first 70 km week"), a milestone (first marathon, sub-X half), or a base-building period without a target?
- **If a race: how do you want to approach it?** Race for time/place, race for completion, "run it but don't race it", or use it as a training day?
- **If multiple races: priorities.** A-race (everything serves this), B-race (matters but won't reshape the plan), C-race (run it as it comes). Be concrete about which is which.
- **Horizon of this plan.** Are we sketching the whole season (12+ weeks, low detail) or building the next block (4–6 weeks, day-by-day)? Or both (season overview + first block detailed)?

#### Weekly schedule and life constraints

- **How many days per week do you want to run?** And is that a soft preference or a hard cap (e.g. childcare two evenings, gym day Wednesday)?
- **Which days work best for the long run?** Saturday and Sunday are common; some users have only one weekend day. The long-run anchor shapes everything else.
- **Which days work best for quality (intervals/threshold)?** Quality usually wants 48 h before a long run and 24–48 h after a hard day. If Tuesday and Thursday are blocked, threshold may need to live on Wednesday.
- **Time of day.** Mostly mornings, mostly evenings, mixed? Morning runners can stack a quality + long-run weekend more easily; evening runners often need a recovery buffer the day after.
- **Known disruptions in the next 4–8 weeks.** Travel, work crunch, family commitments, holidays. Better to name them now and plan around them than have a "missed" week every time the user goes to a wedding.
- **Cross-training already in the rhythm.** Bike commute? Strength session? Yoga? These shape recovery — don't pretend they're free.

#### Training style preference

Offer at least three styles and ask which appeals (or whether the user wants to mix):

1. **Polarized** — ~80% very easy, ~20% very hard, almost nothing in the middle. Good for runners who can hold easy easy and want to keep injury risk low. Workhorse style for ultras and many marathon plans.
2. **Pyramidal / threshold-heavy ("Norwegian-ish")** — most volume easy, but a steady diet of moderate threshold work (e.g. double threshold days, lots of sub-threshold). Higher injury risk if not built up to, but big aerobic returns.
3. **Sweet-spot / classic Lydiard** — long aerobic base, then a transition into hill strength, then race-specific quality. Good for runners who like a clear narrative arc.
4. **High-intensity / low-volume** — fewer total km, harder sessions. Suits time-constrained runners chasing 5k–HM, less suitable for ultras.
5. **Free-form / feel-based** — broad weekly targets, day-to-day decided by feel. Suits experienced self-coached runners who hate prescription.

Ask which resonates, and **why** — the reason usually reveals more than the choice. ("I want polarized because I keep blowing up the easy days" is a different problem than "I want polarized because that's what my buddy does".)

#### Body, history, and constraints

- **Any current niggles or chronic issues** (Achilles, knee, ITB, plantar) — even minor ones. These shape volume ramp and surface choice.
- **Recent racing/big efforts** that might still be in the legs.
- **Surface preference / terrain access.** Trail, road, treadmill, track. If the A-race is hilly and the user runs 100% flat, plan needs a hill answer.
- **Climate / season.** Heat, snow, dark mornings. These change what "easy" means and what's realistic.
- **Equipment / gym / track.** Available or not.

#### Calibration questions you can derive but should still confirm

Don't pretend to ask if you already know — but do confirm. "Looking at the last 12 weeks you've been around 55 km/week with a peak long of 22 km — does that feel right, or has something been off (illness, travel, watch issues)?" gives the user a chance to correct your read.

### 4. Synthesize and propose, before writing the file

Before writing, **summarize what you heard back to the user in chat** — goal, priority races, weekly shape, style choice, key constraints, any deviation from prior analyses. One short paragraph or a tight bulleted list. Ask "did I get that right?" and wait.

This is cheap and prevents writing a whole plan around a misread.

### 5. Write the plan file

Filename: `YYYY-MM-DD-<slug>.md` using today's date, placed in the subfolder that matches the file type (see `CLAUDE.md` "Folder layout"). Don't overwrite — if today already has a file with the same slug, suffix it.

#### Pick the right structure for the horizon

- **Season-plan file** (12+ weeks, race-anchored): macro structure only. Phases, weekly volume targets per phase, key weekends, taper outline. Day-by-day not required. Write to `analyses/season-plan/<date>-<slug>.md`. See `analyses/season-plan/2026-05-03-season-plan-overview.md` for the template.
- **Training-block file** (4–6 weeks, detailed): day-by-day tables, HR targets, specific sessions. Write to `analyses/schedule/<date>-<slug>.md`. See `analyses/schedule/2026-05-03-block-1-weeks-may4-jun7.md` for the template.
- **Race-plan file**: race-day pacing, fuelling, bail criteria. Write to `analyses/races/<date>-<slug>.md`.
- **Multiple files.** If the user is starting fresh and has a far-off A-race, write a season-plan file *and* a first training-block file. Cross-reference between them by full path. This is often the right answer — don't shy away from it just because it's two files.

#### File header

Always start with the YAML-ish header per the repo's `CLAUDE.md`:

```markdown
---
date: YYYY-MM-DD
type: <season-plan | training-block | race-plan>
summary: <one-line summary>
---
```

#### Required sections (adapt names, but cover all)

- **Context** — current fitness state in 3–5 bullets, sourced from Strava (weekly volume, peak long run, recent quality, any flagged niggles or gaps). This is what justifies the volumes and intensities you're prescribing.
- **Goal(s)** — race(s) with date, distance, priority. Or volume/milestone goals.
- **Weekly shape** — days running, anchor days for long run and quality, cross-training, planned rest.
- **Training style chosen and why** — name the style, name *why* it was chosen (the user's words from phase 3 when possible).
- **Plan body** — phases (season-plan) or week-by-week tables (training-block). Be concrete: km, HR targets, paces where they exist, cross-training notes.
- **Known disruptions** — travel/work/etc. that the plan accounts for, with the planned adaptation.
- **What I'm watching for** — 3–5 signals that would prompt a course correction at the next review (resting HR drift, niggle escalation, sleep, motivation).
- **Open questions / decisions deferred** — things you and the user agreed to revisit later. This prevents future-you from having to reverse-engineer "wait, did we decide on Stockholm Marathon?".

If you wrote both a season plan and a first block, link them ("First block detail: `analyses/schedule/YYYY-MM-DD-block-1-...md`").

### 6. Reality-check before handing back

Before declaring done, walk through:

- **Volume sanity.** Does week 1 of the new plan land within ~10–15% of the user's recent weekly average? If it's a big jump (up or down), is that a deliberate choice you can defend?
- **Long-run sanity.** Does the first long run fit within reach of the user's recent peak? A jump >25–30% from current peak is a flag.
- **Quality sanity.** Is the prescribed quality at an intensity the user has done recently, or are you reintroducing it? If reintroducing, the first session should be conservative (volume of work-intervals lower than the eventual target).
- **Schedule fit.** Cross-check the day-by-day against constraints the user named in phase 3. Tuesday quality when Tuesday is blocked = ignored plan.
- **Continuity with the season plan** (if writing a block under one). Don't quietly contradict the macro structure.
- **HR zones grounded in reality.** If the user runs easy at HR 150, the plan saying easy <140 is theatre. Either explain why it should change, or write the zone the user actually uses.

Then summarize for the user in chat: 1–2 sentences on what was decided, 1 sentence on the next concrete action (e.g., "first run is Monday: 8 km easy, HR <145"), and the path to the file(s) you wrote.

## Things to avoid

- **Drafting the plan before the interview.** The interview is where the plan becomes the user's plan. Skipping it produces generic output.
- **Asking 15 questions in one go.** Group into clusters of 4–6. Wait. Iterate.
- **Re-asking what's already in `analyses/`.** Cite and confirm instead.
- **Prescribing zones, paces, or volumes that aren't grounded in Strava data.** "Easy run" with no number is not a plan. "20 km easy at HR <140" when the user has averaged HR 150 on every easy run for 3 months is fiction.
- **Treating the season plan as suggestion** when one exists. If you're writing a block under it, respect the macro structure or explicitly say what you're changing and why.
- **Ignoring cross-training.** Cycling commute, strength, anything else with HR cost. Name it in the plan.
- **JSON dumps in the file.** Per repo `CLAUDE.md` — analyses are narrative.
- **Generic "increase volume by 10% per week" templates.** Real plans bend around the user's life, niggles, and motivation arc. The 10% rule is a sanity check, not a plan.

## Edge cases

- **No prior `analyses/` content.** First-ever plan. Skip the prior-context phase and lean longer on the interview. Be extra explicit in the file's "Context" section about what you assumed, since there's nothing else to chain off.
- **No Strava data or very sparse data** (just got a watch, returning from long injury). Skip the volume/quality profiling; the plan is a return-to-running progression. Ask the user to describe recent activity verbally and use that as the baseline.
- **User says "just give me a plan, I don't want to answer questions".** Push back once gently — "the questions are how I avoid handing you a generic plan you'll ignore" — and if they still resist, ask only the must-haves: goal, days available per week, any niggles, and one style preference. Plan with conservative defaults for everything else and write the assumptions explicitly into the file.
- **Goal is impossibly far from current fitness** (e.g. user running 20 km/week wants to PR a marathon in 10 weeks). Don't refuse and don't pretend. Lay out what's realistic in the time available, what the gap is, and let the user choose whether to adjust the goal, the timeline, or accept a more modest target.
- **Strava credentials not set up.** Follow the bootstrap path in `.claude/skills/strava/SKILL.md` first. Don't fabricate fitness data.
- **User wants to throw out an existing plan and restart.** Fine — but write the new file with a short note explaining what changed and why, so future sessions can read the thread. Don't delete the old file.
