# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

This repo is a running-coach memory for Claude. It stores recommendations, training analyses, and coaching notes as markdown files so that future sessions can read prior context and stay consistent across conversations. See `readme.md` for the one-line summary.

There is no application code here — Claude is the "runtime." The repo is a structured notebook.

## Conventions

### Folder layout under `analyses/`

`analyses/` is organised by type so that "what is currently active?" is always a single sort, never a slug-guessing exercise. The dated filename (`YYYY-MM-DD-<slug>.md`) is preserved; the subfolder tells Claude which question the file answers.

```
analyses/
  preferences/    # training-preferences — standing schedule, style, constraints
  season-plan/    # season-level macro plans (phases, race calendar)
  schedule/       # forward-prescribing files: training-block, weekly-review, schedule-update
  syncs/          # activity-sync — single-day / single-session post-hoc records
  races/          # race-plan and race-review files
```

**The active doc of each type is the newest file in its subfolder** (lexicographic sort on the `YYYY-MM-DD` prefix). No symlinks, no INDEX file — the sort *is* the query. So to orient at the start of a session:

- Current preferences: `ls analyses/preferences/ | tail -1`
- Current season plan: `ls analyses/season-plan/ | tail -1`
- Current detailed schedule for the upcoming period: `ls analyses/schedule/ | tail -1`
- Latest activity sync: `ls analyses/syncs/ | tail -1`

**Where to write a new file:** decide which question it answers.

- New standing-schedule / preference fact → `preferences/`
- New season-level plan → `season-plan/`
- New forward-prescribing file (block, weekly review, mid-block re-prescription) → `schedule/`
- Post-hoc record of a single training day / week's actual execution → `syncs/`
- Race-day plan or post-race review → `races/`

Weekly reviews combine "what happened" and "next 14 days" in one file in `schedule/` — they prescribe upcoming days, so they live with the schedule. Don't split them.

If a preference is being **updated in place** (not adding a new dated entry), edit the latest file in `preferences/` directly — same pattern `2026-05-15-schedule-clarifications.md` used for standing-schedule clarifications.

### Storing analyses and recommendations
- Filename: `YYYY-MM-DD-short-slug.md`. Dated filenames give a natural chronological history; the subfolder (see "Folder layout" above) decides where it goes.
- Start each file with a short YAML-ish header: date, type (e.g. `weekly-review`, `race-plan`, `training-preferences`), and a one-line summary. Keep the body focused on observations, reasoning, and the recommendation itself.
- Before producing a new recommendation, read the active doc of each relevant type (newest per subfolder) so the advice is continuous with what was said before. Note explicitly when changing prior guidance and why.

### Strava data
- When training data from Strava is needed, use the `stravalib` Python package (auth via Strava OAuth tokens — ask the user where credentials live before assuming).
- Prefer pulling raw activity data into a short scratch session, then summarising into a file in the relevant `analyses/` subfolder (usually `syncs/` for single-session records). Don't commit raw activity dumps.
- After downloading an activity, always run the `characterize-activity` skill on it before classifying or writing it up. Averages alone routinely mislabel sessions (an "easy" run with a long surge, a tempo masked as steady, etc.) — the skill's zone breakdown and load metrics are what catch this.
- Always run `characterize-activity` in a **separate sub-agent** (Agent tool) and have it report back a short characterization — effort tag, primary focus, key zone percentages, load relative to other recent sessions, and any structural notes. Don't run the CLI in the main thread; the JSON dump and per-session number-crunching belong off the main context. The sub-agent's summary is what the analysis is written from.

### Keeping the plan visualization in sync
- A human-readable single-page visualization of the forward training plan lives at `viz/plan.html`. It is generated from the current state of `analyses/` (latest season-plan + current training-block + any newer weekly/race reviews) plus `config/training.json`. A stale visualization is worse than none — it looks authoritative while lying about what the plan actually says.
- Whenever an analysis file is added or modified that changes the **forward** training plan — weekly reviews, race reviews, training-block files, season-plan files — regenerate `viz/plan.html` via a **remote one-shot Claude Code session** fired from the local thread after the analysis commit is pushed (procedure below). The remote agent runs the `update-plan-visualization` skill and pushes a follow-up commit. Don't run the skill locally — neither in the main thread nor in a local sub-agent — because the regeneration is slow and blocks the local session. The point of the remote path is that the local sync returns control immediately.
- Pure observation files (activity characterizations, niggle logs, sleep notes, post-hoc race-review summaries that don't extend the plan) do **not** trigger a regeneration. The trigger rule: if the change rewrites or extends what the user is going to *do* in the future, regenerate; if it only records what already happened, don't.
- The analysis commit and the viz commit are **paired but separate**: the analysis change lands first, the remote agent pushes `Regenerate viz/plan.html for <analysis-slug>` on top. Both commits must exist before the repo is consistent. The window between them (the remote agent's runtime, typically minutes) is an accepted eventual-consistency window — don't try to close it by running the skill locally.
- **Offline / no-network fallback**: if the local session can't push (no network) or the remote-routine mechanism is unavailable, fall back to the legacy flow — invoke `update-plan-visualization` in a local sub-agent and commit `viz/plan.html` + the new snapshot + `viz/index.html` together with the analysis file in a single commit. Note in the commit message that the viz was regenerated locally.

#### Triggering the remote viz regeneration
After writing a forward-plan-changing analysis file:
1. Stage + commit the analysis file by itself: `git add analyses/<type>/<slug>.md && git commit -m "<msg>"`. Do not include `viz/` in this commit.
2. `git push` so the remote agent can see the analysis.
3. Invoke the `schedule` skill in **one-shot mode** with a prompt like:
   > Run the `update-plan-visualization` skill in repo `akselsson/ClaudeCoach` on branch `<branch>`. Triggering analysis: `analyses/<type>/<slug>.md`. After the skill stages the viz files, create a commit with message `Regenerate viz/plan.html for <slug>` and push.
4. Report back to the user that the viz regeneration is queued in a remote session and will land as a follow-up commit. Don't wait.

### Training profile and project-scoped config
- Project-scoped training settings live in `config/` at the repo root and are checked in. The change history of those files is itself part of the coaching record — when zones shift between blocks or max HR is recalibrated, that's a training event worth a commit message.
- Currently this is just `config/training.json` (max HR, resting HR, HR zone bands), used by the `characterize-activity` skill. Future training-data settings (pace zones, lifetime PRs, threshold history) belong here too.
- Strava API credentials live in `<project_root>/.env` as `STRAVA_CLIENT_ID` / `STRAVA_CLIENT_SECRET` (and an optional bootstrap `STRAVA_REFRESH_TOKEN`). `.env` is gitignored — see `.env.example` for the template. The rotating OAuth tokens (access/refresh/expires) are cached at `.cache/strava/token.json`, also gitignored and treated as regenerable state.
- When an analysis cites HR zones (e.g. "threshold session at 158–163"), it is implicitly written against whatever `config/training.json` said at the time. Old analyses are not retroactively wrong when zones change — they were correct in their moment.

## Working in this repo

- This is a notebook, not a codebase. There are no build, lint, or test commands.
- Updates are almost always: read the active doc of each relevant type (newest in each `analyses/<type>/` subfolder) → fetch any new data → write a new dated analysis file into the matching subfolder.
- Keep markdown lean and skimmable — these files are read by future Claude sessions, not just the user.
