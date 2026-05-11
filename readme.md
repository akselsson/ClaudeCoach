# ClaudeCoach

A running-coach memory for Claude.

There's no app to run. Claude reads and writes markdown files in this repo, and that's how it remembers what training plan you're on, what you've done, and what it told you last time.

## What's in here

- `analyses/` — dated markdown files (`YYYY-MM-DD-short-slug.md`). Weekly reviews, race plans, training blocks, recommendations. Claude reads the recent ones at the start of each session so the advice stays consistent.
- `config/training.json` — your max HR, resting HR, and HR zone bands. Checked in on purpose — when these change, that's a real coaching event.
- `viz/plan.html` — a single-page view of your current forward plan, generated from the analysis files.
- `.claude/skills/` — the skills Claude uses (see below).
- `CLAUDE.md` — the conventions Claude follows in this repo.

## Getting started

You need [Claude Code](https://claude.ai/code) and a Strava API app.

1. Clone the repo and open it in Claude Code.
2. Copy `.env.example` to `.env` and fill in `STRAVA_CLIENT_ID` / `STRAVA_CLIENT_SECRET` from an app registered at https://www.strava.com/settings/api. The first time the `strava` skill runs, it'll walk you through the OAuth handshake — details in `.claude/skills/strava/SKILL.md`.
3. Edit `config/training.json` with your own numbers. The values in there are someone else's.
4. Ask Claude to set up a plan — something like "set up a training plan for my marathon in October". It'll ask about your goals and schedule, look at your Strava history, and write a first plan file.

After that, just talk to Claude. It picks up where the last session left off.

## The skills

You don't invoke skills by name — describe what you want and Claude will pick the right one.

| Skill | When to use it | What you might say |
| --- | --- | --- |
| `setup-training-plan` | Starting fresh, or throwing out the current plan | "set up a plan for X", "I have a new race in N weeks" |
| `weekly-training-review` | Routine ~2-week check-in | "weekly review", "how's the build going", "plan the next two weeks" |
| `characterize-activity` | Take a closer look at one workout | "look at yesterday's run", "was that actually a tempo?" |
| `update-plan-visualization` | Regenerate `viz/plan.html` | Usually runs automatically; ask for it if the page looks stale |
| `strava` | Pull raw Strava data | "what did I do last week?", "show me Sunday's long run" |

## Keeping plans up to date

Roughly:

- Every couple of weeks, ask for a training review. Claude compares the plan against what you actually did on Strava, asks about anything that doesn't match, and writes a new analysis file with a fresh 14-day plan.
- For a specific workout, ask Claude to characterize it. You get back effort level, zone breakdown, and a load estimate — handy when an "easy" run wasn't, or before a race write-up.
- When a review or new plan changes the forward training, `viz/plan.html` gets regenerated and committed alongside the analysis file. The page and the plan move together.
- Notes that only describe what already happened (a workout characterization, a niggle log, a post-race recap that doesn't change anything going forward) don't trigger a regen.

If the change affects what you'll *do* next, the visualization is updated. If it only records what's already done, it isn't.

## Analysis file conventions

Each file in `analyses/` starts with a small header (date, type, one-line summary) and then the observations, reasoning, and recommendation. Filenames are `YYYY-MM-DD-short-slug.md` so they sort chronologically. When the advice changes from what was said before, the new file says so.

More detail in `CLAUDE.md`.
