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

## Working in this repo

- This is a notebook, not a codebase. There are no build, lint, or test commands.
- Updates are almost always: read recent `analyses/` files → fetch any new data → write a new dated analysis file.
- Keep markdown lean and skimmable — these files are read by future Claude sessions, not just the user.
