---
name: strava
description: Read the user's Strava training data via the bundled stravalib-backed CLI. Use whenever the user asks about their runs, rides, training volume, weekly mileage, recent workouts, individual activity details, or heart-rate/pace data — anything that needs to look up what the user has actually done athletically. Handles OAuth token refresh transparently.
---

# Strava read CLI

This skill exposes a small, read-only CLI over the user's Strava data. It exists because rungpt analyses (in `analyses/`) need to be grounded in real training data, not memory or guesses.

The script lives at `.claude/skills/strava/strava.py` and is self-installing via `uv` (PEP-723 inline metadata pulls `stravalib`). Run it directly — no `uv run` prefix needed.

## When to use

Use this skill whenever an analysis or recommendation requires looking at what the user actually trained:

- "How was my volume last week?" → `weekly-volume`
- "What runs have I done recently?" → `recent`
- "Look at my long run from Sunday" → `recent` to find the id, then `activity <id>` (and `streams <id>` if HR/pace breakdown is needed)
- Before writing a weekly review or race plan in `analyses/`, pull recent data first.

## Prerequisites: credentials at `~/.config/rungpt/strava.json`

The skill reads/writes one config file. Format:

```json
{
  "client_id": "12345",
  "client_secret": "...",
  "refresh_token": "...",
  "access_token": "...",
  "expires_at": 1700000000
}
```

Only `client_id` and `client_secret` are required to start; the others are populated by `auth-code` (first time) and refreshed automatically thereafter. Required scope: `activity:read_all`.

### One-time bootstrap (if `refresh_token` is missing)

The user has registered a Strava API app but has not yet exchanged a code for a refresh token. To do so:

1. Confirm `~/.config/rungpt/strava.json` exists with at least `client_id` and `client_secret`.
2. Have the user open this URL in a browser (substitute the real client_id):
   ```
   https://www.strava.com/oauth/authorize?client_id=<CLIENT_ID>&redirect_uri=http://localhost&response_type=code&scope=activity:read_all
   ```
3. After authorizing, Strava redirects to `http://localhost/?state=&code=<CODE>&scope=read,activity:read_all`. The browser will show a connection-refused error — that's fine. The `code` value is in the address bar.
4. Run `.claude/skills/strava/strava.py auth-code <CODE>` (codes are single-use and expire in ~10 min).
5. The skill prints "authenticated as <name>" to stderr and persists the refresh_token. Done forever.

## Subcommands

All commands print JSON to stdout. Diagnostic output (errors, the auth-code success line) goes to stderr.

| Command | Use for |
|---|---|
| `whoami` | Sanity check that auth works. Prints the athlete profile. |
| `recent --since 7d [--type Run] [--with-description]` | List activities in the last N days/weeks (`7d`, `4w`, `12h`). Filter by type optional. Pass `--with-description` to also fetch each activity's description — this is where workout structure usually lives ("4 x 1 km", "2 x 3 km tröskel"), and it's the most reliable signal that a run was a quality session. Costs one extra API call per activity. |
| `activity <id>` | Full detail for one activity: splits, laps, cadence, watts, **description**. Use this whenever a run looks structured (description hints at intervals, max HR ≫ avg HR, name like "intervals" or "threshold"). The lap and `splits_metric` arrays expose the per-rep HR profile that the activity-level average masks. |
| `streams <id>` | Time-series data (HR, pace, altitude). **Do not paste raw output into analyses/** — summarize. |
| `weekly-volume --weeks 8 [--type Run]` | ISO-week buckets of distance, time, and elevation. The primary tool for volume reviews. |

### Examples

```bash
# Quick sanity check
.claude/skills/strava/strava.py whoami

# Last week of running
.claude/skills/strava/strava.py recent --since 7d --type Run

# Last 14 days of running, with descriptions (reveals interval/threshold structure)
.claude/skills/strava/strava.py recent --since 14d --type Run --with-description

# Last 12 weeks of run volume
.claude/skills/strava/strava.py weekly-volume --weeks 12 --type Run

# Drill into one activity (use this when a run's description or HR profile looks structured)
.claude/skills/strava/strava.py activity 12345678901

# HR/pace streams for interval analysis
.claude/skills/strava/strava.py streams 12345678901 --types time,heartrate,velocity_smooth
```

### Spotting hidden quality sessions

Strava's average heart rate over a 60-90 minute run often hides 4×1km or 2×3km work. Treat any of these as a strong "drill into `activity <id>`" signal:

- The description contains numbers and × / x ("4 x 1 km", "6×400m"), Swedish/English workout terms ("tröskel", "threshold", "intervals", "fartlek", "tempo"), or pace targets.
- `max_heartrate - average_heartrate` is large (≳ 25 bpm). Steady runs have a tighter band; interval workouts have a wide one.
- Suffer score is high relative to distance (e.g. 60+ on a 7k run).

When in doubt, fetch `activity <id>` and look at the per-km HR in `splits_metric`. A clear sawtooth (high → low → high → low) is interval structure; a smooth ramp from warmup to higher steady HR is a threshold or progression.

Pipe through `jq` for ad-hoc reshaping:

```bash
.claude/skills/strava/strava.py recent --since 14d --type Run | jq '[.[] | {date: .start_date_local, km: .distance_km, hr: .average_heartrate}]'
```

## What NOT to do

- **Don't write raw JSON dumps into `analyses/`.** Per the repo's CLAUDE.md, analysis files are summaries — pull data, then write a short markdown narrative referencing the relevant numbers and activity ids. The analysis should be readable to the user, not a JSON paste.
- **Don't fetch streams unless the analysis genuinely needs intra-activity detail** (intervals, HR zones, fade analysis). Stream payloads can be thousands of points.
- **Don't write through Strava.** This skill is read-only by design. If the user asks to update an activity title or post a comment, push back and ask whether they really want that — and if so, do it manually rather than extending this skill.
- **Don't hand-roll OAuth refresh in a one-off `python -c`.** If you find yourself writing `client.refresh_access_token(...)` inline, stop and use this skill instead — it already handles the refresh and persists the new token.
