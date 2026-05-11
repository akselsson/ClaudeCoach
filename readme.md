# ClaudeCoach

A running-coach memory for Claude.

This repo isn't an application — it's a structured notebook that Claude reads and writes. Claude is the runtime. The repo gives Claude continuity across sessions: a record of past analyses, the current training plan, the user's training profile, and a thin set of skills for pulling real data from Strava.

## What's in here

- `analyses/` — dated markdown files (`YYYY-MM-DD-short-slug.md`). Each one is a recommendation, weekly review, race plan, or training-block plan. Reading the most recent files is how Claude stays consistent with prior coaching.
- `config/training.json` — the user's training profile (max HR, resting HR, HR zone bands). Checked in, because changes are themselves part of the coaching record.
- `viz/plan.html` — a single-page visualization of the current forward training plan. Generated from `analyses/` + `config/`. Always committed alongside the analysis change that produced it.
- `.claude/skills/` — the skills Claude uses to work in this repo (see below).
- `CLAUDE.md` — instructions Claude loads at the start of every session in this repo. Read it if you want to understand the conventions in detail.

## Getting started

You need [Claude Code](https://claude.ai/code) and a Strava API app.

1. **Clone the repo** and open it in Claude Code.
2. **Set up Strava credentials.** Copy `.env.example` to `.env` and fill in `STRAVA_CLIENT_ID` / `STRAVA_CLIENT_SECRET` from an app registered at https://www.strava.com/settings/api. The `strava` skill handles OAuth from there — see `.claude/skills/strava/SKILL.md` for the first-run auth flow.
3. **Edit `config/training.json`** with your own max HR, resting HR, and zone bands. The defaults are someone else's heart.
4. **Kick off a plan.** In a Claude Code session, ask something like *"set up a training plan for my marathon in October"* — Claude will invoke the `setup-training-plan` skill, interview you about goals and constraints, pull your Strava history, and write the first analysis file.

From then on, Claude finds prior context automatically by reading `analyses/`.

## Using the skills

You don't call skills directly — you describe what you want and Claude picks the right one. The triggers below are what to say.

| Skill | When to invoke | What to say |
| --- | --- | --- |
| `setup-training-plan` | Starting from scratch, or replacing an existing plan | *"set up a training plan for X"*, *"I have a new race in N weeks"*, *"build a season plan"* |
| `weekly-training-review` | Routine 14-day check-in against an existing plan | *"weekly review"*, *"how's the build going"*, *"plan the next two weeks"* |
| `characterize-activity` | Classify a single workout (effort, zones, structure, load) | *"look at yesterday's run"*, *"was that actually a tempo?"* |
| `update-plan-visualization` | Regenerate `viz/plan.html` after the forward plan changes | Usually triggered automatically by the review/plan skills; ask explicitly if it gets out of sync |
| `strava` | Read raw Strava data (volume, recent activities, HR/pace streams) | *"what did I do last week?"*, *"show me Sunday's long run"* |

## Keeping plans up to date

The flow that keeps the repo honest:

1. **Every ~2 weeks, ask Claude for a training review.** This runs `weekly-training-review`: Claude reads the most recent plan in `analyses/`, pulls actual Strava activity for the period, asks you about any discrepancies, then writes a new dated analysis file containing the review and a refreshed 14-day plan.
2. **For one-off workouts, ask Claude to characterize the run.** `characterize-activity` runs in a sub-agent and reports back effort, zone breakdown, and load — useful when an "easy" run was actually hard, or before writing a race review.
3. **Let the visualization regenerate itself.** Whenever an analysis changes the *forward* plan (weekly review, race review, training-block, season-plan), `update-plan-visualization` runs in a sub-agent and rewrites `viz/plan.html`. The analysis file and the regenerated page are committed together so the repo never sits in an inconsistent state.
4. **Pure observation files don't trigger a regen.** Activity characterizations, niggle logs, post-hoc race notes that don't extend the plan — those just get written and committed on their own.

Rule of thumb: if the change rewrites or extends what you're going to *do* in the future, the page gets regenerated. If it only records what already happened, it doesn't.

## Conventions for analysis files

Each file in `analyses/` starts with a short YAML-ish header (date, type, one-line summary) and contains observations, reasoning, and the recommendation. Filenames are `YYYY-MM-DD-short-slug.md` so chronological order falls out of `ls`. When Claude changes prior guidance, it says so explicitly in the new file.

See `CLAUDE.md` for the full set of conventions Claude follows when working in this repo.
