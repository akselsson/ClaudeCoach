# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

This repo is a running-coach memory for Claude. It stores recommendations, training analyses, and coaching notes as markdown files so that future sessions can read prior context and stay consistent across conversations. See `readme.md` for the one-line summary.

There is no application code here — Claude is the "runtime." The repo is a structured notebook.

## Conventions

### Storing analyses and recommendations
- Write each analysis or recommendation as its own markdown file under `analyses/`.
- Filename: `YYYY-MM-DD-short-slug.md` (e.g. `analyses/2026-05-03-weekly-volume.md`). Dated filenames give a natural chronological history and let Claude locate prior notes without folder-routing decisions.
- Start each file with a short YAML-ish header: date, type (e.g. `weekly-review`, `race-plan`, `recommendation`), and a one-line summary. Keep the body focused on observations, reasoning, and the recommendation itself.
- Before producing a new recommendation, read the most recent files in `analyses/` so the advice is continuous with what was said before. Note explicitly when changing prior guidance and why.

### Strava data
- When training data from Strava is needed, use the `stravalib` Python package (auth via Strava OAuth tokens — ask the user where credentials live before assuming).
- Prefer pulling raw activity data into a short scratch session, then summarising into an analysis file under `analyses/`. Don't commit raw activity dumps.
- After downloading an activity, always run the `characterize-activity` skill on it before classifying or writing it up. Averages alone routinely mislabel sessions (an "easy" run with a long surge, a tempo masked as steady, etc.) — the skill's zone breakdown and load metrics are what catch this.
- Always run `characterize-activity` in a **separate sub-agent** (Agent tool) and have it report back a short characterization — effort tag, primary focus, key zone percentages, load relative to other recent sessions, and any structural notes. Don't run the CLI in the main thread; the JSON dump and per-session number-crunching belong off the main context. The sub-agent's summary is what the analysis is written from.

### Keeping the plan visualization in sync
- A human-readable single-page visualization of the forward training plan lives at `viz/plan.html`. It is generated from the current state of `analyses/` (latest season-plan + current training-block + any newer weekly/race reviews) plus `config/training.json`. A stale visualization is worse than none — it looks authoritative while lying about what the plan actually says.
- Whenever an analysis file is added or modified that changes the **forward** training plan — weekly reviews, race reviews, training-block files, season-plan files — invoke the `update-plan-visualization` skill in a **separate sub-agent** (Agent tool) to regenerate `viz/plan.html`. The sub-agent reports back a short diff summary; the long HTML output stays off the main context. Don't regenerate the page in the main thread.
- Pure observation files (activity characterizations, niggle logs, sleep notes, post-hoc race-review summaries that don't extend the plan) do **not** trigger a regeneration. The trigger rule: if the change rewrites or extends what the user is going to *do* in the future, regenerate; if it only records what already happened, don't.
- When the analysis change is committed, **commit the regenerated `viz/plan.html` together with the analysis file** in the same commit. The visualization is derived from the analyses, so the two must stay in lockstep — a commit that updates the plan but not the page (or vice versa) leaves the repo in an inconsistent state. The commit message should describe the analysis change; the page update is implied.

### Training profile and project-scoped config
- Project-scoped training settings live in `config/` at the repo root and are checked in. The change history of those files is itself part of the coaching record — when zones shift between blocks or max HR is recalibrated, that's a training event worth a commit message.
- Currently this is just `config/training.json` (max HR, resting HR, HR zone bands), used by the `characterize-activity` skill. Future training-data settings (pace zones, lifetime PRs, threshold history) belong here too.
- Strava API credentials live in `<project_root>/.env` as `STRAVA_CLIENT_ID` / `STRAVA_CLIENT_SECRET` (and an optional bootstrap `STRAVA_REFRESH_TOKEN`). `.env` is gitignored — see `.env.example` for the template. The rotating OAuth tokens (access/refresh/expires) are cached at `.cache/strava/token.json`, also gitignored and treated as regenerable state.
- When an analysis cites HR zones (e.g. "threshold session at 158–163"), it is implicitly written against whatever `config/training.json` said at the time. Old analyses are not retroactively wrong when zones change — they were correct in their moment.

## Working in this repo

- This is a notebook, not a codebase. There are no build, lint, or test commands.
- Updates are almost always: read recent `analyses/` files → fetch any new data → write a new dated analysis file.
- Keep markdown lean and skimmable — these files are read by future Claude sessions, not just the user.
