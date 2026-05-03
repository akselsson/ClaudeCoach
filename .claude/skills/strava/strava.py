#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["stravalib>=1.7"]
# ///
"""Strava read CLI for the ClaudeCoach coaching notebook.

Reads ~/.config/claudecoach/strava.json for credentials, auto-refreshes the
access token when stale (writing the new one back to disk), and exposes
a small set of read operations as JSON-on-stdout subcommands.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from stravalib.client import Client

DEFAULT_CONFIG = Path.home() / ".config" / "claudecoach" / "strava.json"
TOKEN_REFRESH_BUFFER_SECONDS = 300

# Cache lives under the ClaudeCoach project root so all notebook state stays in one
# place. The script lives at <project_root>/.claude/skills/strava/strava.py, so
# parents[3] resolves to the project root regardless of CWD.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CACHE = PROJECT_ROOT / ".cache" / "strava"

# Activities younger than this still get title/description edits in practice,
# so we bypass the cache for them. Strava exposes no last-modified field,
# making this the only reliable way to avoid serving stale data right after
# an activity is uploaded.
RECENT_WINDOW_DAYS = 2


def load_config(path: Path) -> dict:
    if not path.exists():
        sys.exit(
            f"error: config file not found at {path}\n"
            'create it with at least: {"client_id": "...", "client_secret": "..."}'
        )
    return json.loads(path.read_text())


def save_config(path: Path, config: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2) + "\n")
    os.chmod(path, 0o600)


def _token_fields(token_response):
    """stravalib returns dict-like in v1 and dict/typeddict in v2 — read both shapes."""
    if isinstance(token_response, dict):
        return (
            token_response["access_token"],
            token_response["refresh_token"],
            token_response["expires_at"],
        )
    return (
        token_response.access_token,
        token_response.refresh_token,
        token_response.expires_at,
    )


def authed_client(config_path: Path) -> Client:
    """Return a Client with a fresh access token. Refreshes and persists when stale."""
    config = load_config(config_path)
    for required in ("client_id", "client_secret", "refresh_token"):
        if required not in config:
            sys.exit(
                f"error: '{required}' missing from {config_path}\n"
                "if you have client_id/client_secret but no refresh_token, "
                "run `auth-code <code>` first (see SKILL.md)."
            )

    expires_at = config.get("expires_at", 0)
    now = int(time.time())
    needs_refresh = (
        not config.get("access_token")
        or expires_at - now < TOKEN_REFRESH_BUFFER_SECONDS
    )

    if needs_refresh:
        token = Client().refresh_access_token(
            client_id=config["client_id"],
            client_secret=config["client_secret"],
            refresh_token=config["refresh_token"],
        )
        access, refresh, exp = _token_fields(token)
        config["access_token"] = access
        config["refresh_token"] = refresh
        config["expires_at"] = exp
        save_config(config_path, config)

    return Client(access_token=config["access_token"])


def parse_relative(spec: str) -> datetime:
    match = re.fullmatch(r"(\d+)([dwh])", spec)
    if not match:
        sys.exit(f"error: --since must look like '7d', '4w', or '12h'; got {spec!r}")
    n, unit = int(match.group(1)), match.group(2)
    delta = {"d": timedelta(days=n), "w": timedelta(weeks=n), "h": timedelta(hours=n)}[unit]
    return datetime.now(timezone.utc) - delta


def to_meters(value) -> float:
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(value.magnitude)


def to_seconds(value) -> int:
    if value is None:
        return 0
    if isinstance(value, timedelta):
        return int(value.total_seconds())
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(float(value))


def _type_value(t) -> str:
    """Stravalib v2 wraps activity/sport types as Pydantic RootModels whose str()
    looks like "root='Run'". Unwrap to the bare value so callers see "Run"."""
    if t is None:
        return ""
    root = getattr(t, "root", None)
    if root is not None:
        return str(root)
    s = str(t)
    match = re.match(r"root='([^']*)'", s)
    return match.group(1) if match else s


def matches_type(activity, type_filter: str | None) -> bool:
    if not type_filter:
        return True
    return type_filter in (
        _type_value(activity.type),
        _type_value(getattr(activity, "sport_type", None)),
    )


def summary_dict(activity) -> dict:
    return {
        "id": activity.id,
        "start_date_local": activity.start_date_local.isoformat() if activity.start_date_local else None,
        "type": _type_value(activity.type) or None,
        "sport_type": _type_value(getattr(activity, "sport_type", None)) or None,
        "name": activity.name,
        "description": getattr(activity, "description", None),
        "distance_km": round(to_meters(activity.distance) / 1000, 3),
        "moving_time_s": to_seconds(activity.moving_time),
        "elapsed_time_s": to_seconds(activity.elapsed_time),
        "average_heartrate": activity.average_heartrate,
        "max_heartrate": activity.max_heartrate,
        "suffer_score": getattr(activity, "suffer_score", None),
        "total_elevation_gain_m": to_meters(activity.total_elevation_gain),
    }


def build_detail_dict(activity) -> dict:
    """Shape a DetailedActivity into our JSON output. Used for both live fetches
    and cache writes so the on-disk format matches what `cmd_activity` emits."""
    detail = summary_dict(activity)
    detail["calories"] = getattr(activity, "calories", None)
    detail["average_speed_mps"] = float(activity.average_speed) if activity.average_speed is not None else None
    detail["max_speed_mps"] = float(activity.max_speed) if activity.max_speed is not None else None
    detail["average_cadence"] = getattr(activity, "average_cadence", None)
    detail["average_watts"] = getattr(activity, "average_watts", None)
    detail["weighted_average_watts"] = getattr(activity, "weighted_average_watts", None)
    detail["splits_metric"] = [
        {
            "split": s.split,
            "distance_m": to_meters(s.distance),
            "elapsed_time_s": to_seconds(s.elapsed_time),
            "moving_time_s": to_seconds(s.moving_time),
            "average_speed_mps": float(s.average_speed) if s.average_speed is not None else None,
            "elevation_difference_m": to_meters(s.elevation_difference),
            "average_heartrate": s.average_heartrate,
        }
        for s in (activity.splits_metric or [])
    ]
    detail["laps"] = [
        {
            "lap_index": lap.lap_index,
            "name": lap.name,
            "distance_m": to_meters(lap.distance),
            "elapsed_time_s": to_seconds(lap.elapsed_time),
            "moving_time_s": to_seconds(lap.moving_time),
            "average_speed_mps": float(lap.average_speed) if lap.average_speed is not None else None,
            "average_heartrate": lap.average_heartrate,
            "max_heartrate": lap.max_heartrate,
        }
        for lap in (activity.laps or [])
    ]
    return detail


def _atomic_write_json(path: Path, data) -> None:
    """Write JSON via temp file + rename so a crash mid-write can't corrupt the cache."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, default=str))
    tmp.replace(path)


def _load_json_or_none(path: Path):
    """Return parsed JSON or None on missing/corrupt files. Corrupt cache should
    behave like a miss, not crash the run."""
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def _is_within_recent_window(start_date_local) -> bool:
    """True if the activity is too fresh to cache (still within the user-edit window)."""
    if start_date_local is None:
        return False
    if isinstance(start_date_local, str):
        try:
            start_date_local = datetime.fromisoformat(start_date_local)
        except ValueError:
            return False
    # Strip tz so we can subtract regardless of whether the datetime is aware or naive.
    if start_date_local.tzinfo is not None:
        start_date_local = start_date_local.replace(tzinfo=None)
    age = datetime.utcnow() - start_date_local
    return age < timedelta(days=RECENT_WINDOW_DAYS)


def _activity_cache_path(cache_dir: Path, activity_id: int) -> Path:
    return cache_dir / "activities" / f"{activity_id}.json"


def _streams_cache_path(cache_dir: Path, activity_id: int, resolution: str) -> Path:
    return cache_dir / "streams" / f"{activity_id}.{resolution}.json"


def cached_activity_detail(
    client,
    activity_id: int,
    *,
    cache_dir: Path,
    refresh: bool = False,
    expected_name: str | None = None,
) -> dict:
    """Return the detail dict for `activity_id`, served from cache when safe.

    Three reasons we'll bypass the cache and refetch:
    - `refresh=True` (caller asked explicitly)
    - cached entry's `start_date_local` is within RECENT_WINDOW_DAYS (the user
      may still be editing the title/description)
    - `expected_name` is given and disagrees with the cached `name` — Strava
      gives no last-modified field, but the list endpoint exposes `name`, so a
      mismatch is our cheapest "this activity was edited" signal.

    The freshly-fetched detail is only persisted if the activity is past the
    recent window, otherwise we'd cache something that may immediately go stale.
    """
    path = _activity_cache_path(cache_dir, activity_id)

    if not refresh:
        cached = _load_json_or_none(path)
        if cached is not None:
            recent = _is_within_recent_window(cached.get("start_date_local"))
            renamed = expected_name is not None and cached.get("name") != expected_name
            if not recent and not renamed:
                return cached

    activity = client.get_activity(activity_id)
    detail = build_detail_dict(activity)
    if not _is_within_recent_window(detail.get("start_date_local")):
        _atomic_write_json(path, detail)
    return detail


def cached_activity_streams(
    client,
    activity_id: int,
    *,
    types: list[str],
    resolution: str,
    cache_dir: Path,
    refresh: bool = False,
) -> dict:
    """Return `{stream_type: data}` for the requested types at `resolution`.

    Streams are FIT-derived and immutable, so the only reasons to bypass the
    cache are `refresh=True` or types we haven't seen before. On a partial-
    overlap request we fetch only the missing types from Strava and merge them
    into the existing per-(id, resolution) cache file."""
    path = _streams_cache_path(cache_dir, activity_id, resolution)

    if refresh:
        cached: dict = {}
        missing = list(types)
    else:
        cached = _load_json_or_none(path) or {}
        missing = [t for t in types if t not in cached]

    if missing:
        fetched = client.get_activity_streams(activity_id, types=missing, resolution=resolution) or {}
        for k, v in fetched.items():
            cached[str(k)] = v.data
        _atomic_write_json(path, cached)

    return {t: cached[t] for t in types if t in cached}


def cmd_auth_code(args: argparse.Namespace) -> None:
    config_path = Path(args.config).expanduser()
    config = load_config(config_path)
    for required in ("client_id", "client_secret"):
        if required not in config:
            sys.exit(f"error: '{required}' missing from {config_path}")

    client = Client()
    token = client.exchange_code_for_token(
        client_id=config["client_id"],
        client_secret=config["client_secret"],
        code=args.code,
    )
    access, refresh, exp = _token_fields(token)
    config["access_token"] = access
    config["refresh_token"] = refresh
    config["expires_at"] = exp
    save_config(config_path, config)

    client.access_token = access
    athlete = client.get_athlete()
    print(f"authenticated as {athlete.firstname} {athlete.lastname} (id={athlete.id})", file=sys.stderr)
    print(f"refresh_token saved to {config_path}", file=sys.stderr)


def cmd_whoami(args: argparse.Namespace) -> None:
    client = authed_client(Path(args.config).expanduser())
    athlete = client.get_athlete()
    json.dump({
        "id": athlete.id,
        "firstname": athlete.firstname,
        "lastname": athlete.lastname,
        "username": athlete.username,
        "city": athlete.city,
        "country": athlete.country,
    }, sys.stdout, indent=2)
    sys.stdout.write("\n")


def cmd_recent(args: argparse.Namespace) -> None:
    client = authed_client(Path(args.config).expanduser())
    cache_dir = Path(args.cache).expanduser()
    after = parse_relative(args.since)
    out = []
    for act in client.get_activities(after=after):
        if not matches_type(act, args.type):
            continue
        row = summary_dict(act)
        # Strava's list endpoint omits description; fetch detail when asked.
        # Workout structure ("4 x 1 km", "tröskel", etc.) lives in the description,
        # so reviewers analysing past training usually want this on. The cache
        # absorbs the per-activity detail call after the first run.
        if args.with_description:
            detail = cached_activity_detail(
                client,
                act.id,
                cache_dir=cache_dir,
                refresh=args.refresh,
                expected_name=act.name,
            )
            row["description"] = detail.get("description")
        out.append(row)
    json.dump(out, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")


def cmd_activity(args: argparse.Namespace) -> None:
    client = authed_client(Path(args.config).expanduser())
    cache_dir = Path(args.cache).expanduser()
    detail = cached_activity_detail(
        client,
        args.id,
        cache_dir=cache_dir,
        refresh=args.refresh,
    )
    json.dump(detail, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")


def cmd_streams(args: argparse.Namespace) -> None:
    client = authed_client(Path(args.config).expanduser())
    cache_dir = Path(args.cache).expanduser()
    types = [t.strip() for t in args.types.split(",") if t.strip()]
    out = cached_activity_streams(
        client,
        args.id,
        types=types,
        resolution=args.resolution,
        cache_dir=cache_dir,
        refresh=args.refresh,
    )
    json.dump(out, sys.stdout, default=str)
    sys.stdout.write("\n")


def cmd_weekly_volume(args: argparse.Namespace) -> None:
    client = authed_client(Path(args.config).expanduser())
    after = datetime.now(timezone.utc) - timedelta(weeks=args.weeks)
    buckets: dict[str, dict] = defaultdict(
        lambda: {"n_activities": 0, "distance_m": 0.0, "moving_time_s": 0, "elev_gain_m": 0.0}
    )
    for act in client.get_activities(after=after):
        if not matches_type(act, args.type) or not act.start_date_local:
            continue
        d = act.start_date_local.date()
        week_start = (d - timedelta(days=d.weekday())).isoformat()
        b = buckets[week_start]
        b["n_activities"] += 1
        b["distance_m"] += to_meters(act.distance)
        b["moving_time_s"] += to_seconds(act.moving_time)
        b["elev_gain_m"] += to_meters(act.total_elevation_gain)

    out = [
        {
            "week_start": ws,
            "n_activities": b["n_activities"],
            "distance_km": round(b["distance_m"] / 1000, 2),
            "moving_time_h": round(b["moving_time_s"] / 3600, 2),
            "elevation_gain_m": round(b["elev_gain_m"], 0),
        }
        for ws, b in sorted(buckets.items())
    ]
    json.dump(out, sys.stdout, indent=2)
    sys.stdout.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="strava",
        description="ClaudeCoach Strava read CLI (uses stravalib + ~/.config/claudecoach/strava.json)",
    )
    parser.add_argument("--config", default=str(DEFAULT_CONFIG),
                        help=f"Path to credentials JSON (default: {DEFAULT_CONFIG})")
    parser.add_argument("--cache", default=str(DEFAULT_CACHE),
                        help=f"Cache directory for activity details and streams "
                             f"(default: {DEFAULT_CACHE})")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("auth-code", help="One-time: exchange an OAuth code for refresh+access tokens")
    p.add_argument("code", help="The 'code' query param from the OAuth redirect URL")
    p.set_defaults(func=cmd_auth_code)

    p = sub.add_parser("whoami", help="Print the authenticated athlete (sanity check)")
    p.set_defaults(func=cmd_whoami)

    p = sub.add_parser("recent", help="List activities in a relative time window")
    p.add_argument("--since", default="14d", help="Time window: 7d, 4w, 12h (default: 14d)")
    p.add_argument("--type", default=None, help="Filter by activity type (e.g. Run, Ride, TrailRun)")
    p.add_argument("--with-description", action="store_true",
                   help="Fetch each activity's description (extra API call per activity, "
                        "but reveals workout structure like '4 x 1 km' or 'tröskel'). "
                        "Cached after first fetch — see --cache and --refresh.")
    p.add_argument("--refresh", action="store_true",
                   help="Force-refetch description details, ignoring any cached entries")
    p.set_defaults(func=cmd_recent)

    p = sub.add_parser("activity", help="Fetch one activity's full detail (incl. splits and laps)")
    p.add_argument("id", type=int, help="Strava activity ID")
    p.add_argument("--refresh", action="store_true",
                   help="Force-refetch from Strava, ignoring any cached entry")
    p.set_defaults(func=cmd_activity)

    p = sub.add_parser("streams", help="Fetch time-series streams for one activity (HR/pace/altitude/etc.)")
    p.add_argument("id", type=int, help="Strava activity ID")
    p.add_argument("--types", default="time,heartrate,velocity_smooth,altitude",
                   help="Comma-separated stream types (default: time,heartrate,velocity_smooth,altitude)")
    p.add_argument("--resolution", default="medium", choices=["low", "medium", "high"],
                   help="Stream resolution (default: medium)")
    p.add_argument("--refresh", action="store_true",
                   help="Force-refetch from Strava, ignoring any cached entry")
    p.set_defaults(func=cmd_streams)

    p = sub.add_parser("weekly-volume", help="Bucket activities into ISO weeks and total volume per week")
    p.add_argument("--weeks", type=int, default=8, help="How many weeks back to include (default: 8)")
    p.add_argument("--type", default="Run", help="Filter by type (default: Run; pass empty string for all)")
    p.set_defaults(func=cmd_weekly_volume)

    args = parser.parse_args()
    if getattr(args, "type", None) == "":
        args.type = None
    args.func(args)


if __name__ == "__main__":
    main()
