#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["stravalib>=1.7"]
# ///
"""Strava read CLI for the rungpt coaching notebook.

Reads ~/.config/rungpt/strava.json for credentials, auto-refreshes the
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

DEFAULT_CONFIG = Path.home() / ".config" / "rungpt" / "strava.json"
TOKEN_REFRESH_BUFFER_SECONDS = 300


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


def matches_type(activity, type_filter: str | None) -> bool:
    if not type_filter:
        return True
    return type_filter in (str(activity.type or ""), str(getattr(activity, "sport_type", "") or ""))


def summary_dict(activity) -> dict:
    return {
        "id": activity.id,
        "start_date_local": activity.start_date_local.isoformat() if activity.start_date_local else None,
        "type": str(activity.type) if activity.type else None,
        "sport_type": str(getattr(activity, "sport_type", "") or "") or None,
        "name": activity.name,
        "distance_km": round(to_meters(activity.distance) / 1000, 3),
        "moving_time_s": to_seconds(activity.moving_time),
        "elapsed_time_s": to_seconds(activity.elapsed_time),
        "average_heartrate": activity.average_heartrate,
        "max_heartrate": activity.max_heartrate,
        "suffer_score": getattr(activity, "suffer_score", None),
        "total_elevation_gain_m": to_meters(activity.total_elevation_gain),
    }


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
    after = parse_relative(args.since)
    out = [summary_dict(act) for act in client.get_activities(after=after) if matches_type(act, args.type)]
    json.dump(out, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")


def cmd_activity(args: argparse.Namespace) -> None:
    client = authed_client(Path(args.config).expanduser())
    activity = client.get_activity(args.id)
    detail = summary_dict(activity)
    detail["description"] = activity.description
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
    json.dump(detail, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")


def cmd_streams(args: argparse.Namespace) -> None:
    client = authed_client(Path(args.config).expanduser())
    types = [t.strip() for t in args.types.split(",") if t.strip()]
    streams = client.get_activity_streams(args.id, types=types, resolution=args.resolution) or {}
    out = {str(k): v.data for k, v in streams.items()}
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
        description="rungpt Strava read CLI (uses stravalib + ~/.config/rungpt/strava.json)",
    )
    parser.add_argument("--config", default=str(DEFAULT_CONFIG),
                        help=f"Path to credentials JSON (default: {DEFAULT_CONFIG})")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("auth-code", help="One-time: exchange an OAuth code for refresh+access tokens")
    p.add_argument("code", help="The 'code' query param from the OAuth redirect URL")
    p.set_defaults(func=cmd_auth_code)

    p = sub.add_parser("whoami", help="Print the authenticated athlete (sanity check)")
    p.set_defaults(func=cmd_whoami)

    p = sub.add_parser("recent", help="List activities in a relative time window")
    p.add_argument("--since", default="14d", help="Time window: 7d, 4w, 12h (default: 14d)")
    p.add_argument("--type", default=None, help="Filter by activity type (e.g. Run, Ride, TrailRun)")
    p.set_defaults(func=cmd_recent)

    p = sub.add_parser("activity", help="Fetch one activity's full detail (incl. splits and laps)")
    p.add_argument("id", type=int, help="Strava activity ID")
    p.set_defaults(func=cmd_activity)

    p = sub.add_parser("streams", help="Fetch time-series streams for one activity (HR/pace/altitude/etc.)")
    p.add_argument("id", type=int, help="Strava activity ID")
    p.add_argument("--types", default="time,heartrate,velocity_smooth,altitude",
                   help="Comma-separated stream types (default: time,heartrate,velocity_smooth,altitude)")
    p.add_argument("--resolution", default="medium", choices=["low", "medium", "high"],
                   help="Stream resolution (default: medium)")
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
