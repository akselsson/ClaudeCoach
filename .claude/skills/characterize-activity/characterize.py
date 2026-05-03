#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Characterize a single Strava activity for the ClaudeCoach notebook.

Reads the user's training profile from <project_root>/config/training.json,
fetches the activity detail and stream data via the existing strava CLI
(reusing its OAuth + on-disk cache), and emits a single JSON object on
stdout describing effort, primary training focus, time-in-zone histograms,
training-load numbers, lap structure, and HR/pace drift.

This script is intentionally dependency-free — the math is small and the
notebook keeps deps to zero. It does not talk to Strava directly; the
strava CLI handles auth, rate limiting, and caching.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import subprocess
import sys
from pathlib import Path

# Project root resolves the same way as strava.py: this script lives at
# <project_root>/.claude/skills/characterize-activity/characterize.py, so
# parents[3] is the project root regardless of CWD.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "training.json"
DEFAULT_STRAVA = PROJECT_ROOT / ".claude" / "skills" / "strava" / "strava.py"

# Below this velocity (m/s) we treat a sample as walking/standing and drop
# it from pace zones and pace-drift fits — a 30 s walk break would otherwise
# pin the median pace and dominate the histogram.
WALKING_VELOCITY_MPS = 1.4


# --------------------------------------------------------------------------
# config + data fetch
# --------------------------------------------------------------------------

BOOTSTRAP_HINT = (
    "this CLI needs max HR, resting HR, and HR zone bands.\n"
    "see .claude/skills/characterize-activity/SKILL.md for the bootstrap:\n"
    "  ask the user for max HR + resting HR, propose zones consistent with\n"
    "  the most recent analyses/*-block-*.md, write the file, then commit it."
)


def load_config(path: Path) -> dict:
    if not path.exists():
        sys.exit(f"error: training config not found at {path}\n\n{BOOTSTRAP_HINT}")
    try:
        config = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"error: {path} is not valid JSON: {e}\n\n{BOOTSTRAP_HINT}")

    for required in ("max_hr", "hr_zones"):
        if required not in config:
            sys.exit(f"error: '{required}' missing from {path}\n\n{BOOTSTRAP_HINT}")

    zones = config["hr_zones"]
    if not isinstance(zones, list) or not zones:
        sys.exit(f"error: 'hr_zones' in {path} must be a non-empty list\n\n{BOOTSTRAP_HINT}")
    for z in zones:
        if not all(k in z for k in ("name", "min", "max")):
            sys.exit(f"error: each hr_zone needs name/min/max; got {z!r}")
    return config


def _run_strava(strava_path: Path, args: list[str]) -> dict:
    """Invoke the strava CLI and parse its JSON stdout. Surface its stderr
    on failure so an auth or rate-limit problem is legible to the caller."""
    cmd = [str(strava_path), *args]
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    except FileNotFoundError:
        sys.exit(f"error: strava CLI not found at {strava_path}")
    except subprocess.CalledProcessError as e:
        sys.exit(
            f"error: strava CLI failed ({' '.join(cmd)})\n"
            f"--- stderr ---\n{e.stderr}\n--- stdout ---\n{e.stdout}"
        )
    return json.loads(result.stdout)


def fetch_activity(strava_path: Path, activity_id: int, refresh: bool) -> dict:
    args = ["activity", str(activity_id)]
    if refresh:
        args.append("--refresh")
    return _run_strava(strava_path, args)


def fetch_streams(strava_path: Path, activity_id: int, resolution: str, refresh: bool) -> dict:
    args = [
        "streams", str(activity_id),
        "--types", "time,heartrate,velocity_smooth,distance",
        "--resolution", resolution,
    ]
    if refresh:
        args.append("--refresh")
    return _run_strava(strava_path, args)


# --------------------------------------------------------------------------
# stream-driven computations
# --------------------------------------------------------------------------

def _zone_index(value: float, zones: list[dict]) -> int | None:
    for i, z in enumerate(zones):
        if z["min"] <= value < z["max"]:
            return i
    # The last zone's `max` is normally a sentinel (e.g. 999); but if the
    # observed value is exactly at the top edge of the last zone we still
    # want it counted there rather than dropped.
    last = zones[-1]
    if value >= last["min"]:
        return len(zones) - 1
    return None


def time_in_hr_zones(time_stream: list, hr_stream: list, zones: list[dict]) -> list[float]:
    """Walk samples in lockstep, attributing each inter-sample dt to the
    zone of the leading sample's HR. We use the time stream's deltas, not
    a fixed 1 Hz assumption — Strava's stream resolution is variable and
    a "medium" stream can be sparser than 1 Hz."""
    if not time_stream or not hr_stream:
        return [0.0] * len(zones)
    n = min(len(time_stream), len(hr_stream))
    out = [0.0] * len(zones)
    for i in range(n - 1):
        dt = time_stream[i + 1] - time_stream[i]
        if dt is None or dt <= 0:
            continue
        hr = hr_stream[i]
        if hr is None:
            continue
        zi = _zone_index(hr, zones)
        if zi is not None:
            out[zi] += dt
    return out


def derive_pace_zones(velocity_stream: list) -> list[dict]:
    """Build a 5-bucket pace zone scheme as multipliers around the median
    moving pace. The user does not coach by absolute pace, so we report
    pace-zone time as a relative-effort histogram: how much of the run was
    notably faster/slower than the run's own median.

    Walking samples are excluded so the median reflects "running pace" and
    isn't dragged by stops at lights / hike-walks on hills.
    """
    paces = [1000.0 / v for v in velocity_stream
             if v is not None and v >= WALKING_VELOCITY_MPS]
    if not paces:
        return []
    m = statistics.median(paces)
    bounds = [0.0, m * 0.85, m * 0.95, m * 1.05, m * 1.20, math.inf]
    names = ["very_fast", "fast", "steady", "easy", "very_easy"]
    return [
        {"name": names[i], "pace_min": bounds[i], "pace_max": bounds[i + 1]}
        for i in range(5)
    ]


def time_in_pace_zones(time_stream: list, velocity_stream: list,
                       pace_zones: list[dict]) -> list[float]:
    if not pace_zones or not time_stream or not velocity_stream:
        return [0.0] * len(pace_zones)
    n = min(len(time_stream), len(velocity_stream))
    out = [0.0] * len(pace_zones)
    for i in range(n - 1):
        dt = time_stream[i + 1] - time_stream[i]
        if dt is None or dt <= 0:
            continue
        v = velocity_stream[i]
        if v is None or v < WALKING_VELOCITY_MPS:
            continue
        pace = 1000.0 / v
        for zi, z in enumerate(pace_zones):
            if z["pace_min"] <= pace < z["pace_max"]:
                out[zi] += dt
                break
    return out


def trimp_banister(time_stream: list, hr_stream: list,
                   max_hr: float, resting_hr: float) -> float:
    """Banister TRIMP, summed across stream samples. Uses the male
    coefficients (0.64, 1.92) — these are heuristics, not lab-calibrated;
    the absolute number is less interesting than its trend across sessions.
    """
    if not time_stream or not hr_stream or max_hr <= resting_hr:
        return 0.0
    n = min(len(time_stream), len(hr_stream))
    total = 0.0
    span = max_hr - resting_hr
    for i in range(n - 1):
        dt = time_stream[i + 1] - time_stream[i]
        if dt is None or dt <= 0:
            continue
        hr = hr_stream[i]
        if hr is None:
            continue
        hrr = (hr - resting_hr) / span
        if hrr <= 0:
            continue
        if hrr > 1.0:
            hrr = 1.0
        total += (dt / 60.0) * hrr * 0.64 * math.exp(1.92 * hrr)
    return round(total, 1)


def edwards_load(zone_seconds: list[float]) -> float:
    """Σ (minutes_in_zone_i × (i+1)). Maps directly onto the configured
    zones; no max-HR estimate dependency, unlike TRIMP."""
    return round(sum((s / 60.0) * (i + 1) for i, s in enumerate(zone_seconds)), 1)


def linear_slope(xs: list[float], ys: list[float]) -> float:
    """Least-squares slope. Returns 0 if degenerate."""
    if len(xs) < 2:
        return 0.0
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    return num / den if den else 0.0


def drift_metrics(time_stream: list, hr_stream: list,
                  velocity_stream: list, distance_stream: list) -> dict:
    """HR-vs-distance and pace-vs-distance slopes, plus split-half means.

    Filters out walking samples for pace, but keeps them for HR — a hill
    walk is still cardiovascular load worth counting in the cardiac drift
    fit.
    """
    if not (time_stream and distance_stream):
        return {}
    n = min(len(time_stream), len(distance_stream))

    hr_xs: list[float] = []
    hr_ys: list[float] = []
    pace_xs: list[float] = []
    pace_ys: list[float] = []
    for i in range(n):
        d_m = distance_stream[i]
        if d_m is None:
            continue
        d_km = d_m / 1000.0
        if hr_stream and i < len(hr_stream) and hr_stream[i] is not None:
            hr_xs.append(d_km)
            hr_ys.append(hr_stream[i])
        if velocity_stream and i < len(velocity_stream):
            v = velocity_stream[i]
            if v is not None and v >= WALKING_VELOCITY_MPS:
                pace_xs.append(d_km)
                pace_ys.append(1000.0 / v)

    def _halves(ys: list[float]):
        if len(ys) < 4:
            return None, None
        mid = len(ys) // 2
        return statistics.fmean(ys[:mid]), statistics.fmean(ys[mid:])

    hr_first, hr_second = _halves(hr_ys)
    pace_first, pace_second = _halves(pace_ys)

    return {
        "hr_per_km_bpm": round(linear_slope(hr_xs, hr_ys), 2),
        "pace_per_km_s": round(linear_slope(pace_xs, pace_ys), 2),
        "first_half_avg_hr": round(hr_first, 1) if hr_first is not None else None,
        "second_half_avg_hr": round(hr_second, 1) if hr_second is not None else None,
        "first_half_avg_pace_s_per_km": round(pace_first, 1) if pace_first is not None else None,
        "second_half_avg_pace_s_per_km": round(pace_second, 1) if pace_second is not None else None,
    }


# --------------------------------------------------------------------------
# lap-driven computations
# --------------------------------------------------------------------------

def lap_classify(laps: list[dict]) -> dict:
    """Classify the lap structure using lap pace as the primary signal.

    Laps come from the user's watch, so the meaning of "a lap" varies:
    auto-1km laps obscure short intervals (a 6×400m repeats workout will
    look uniform if the watch lapped every km), whereas manually pressed
    laps reveal interval structure cleanly. The SKILL.md should warn
    callers about that ambiguity — we report the classification and the
    raw stats so the caller can decide whether to trust them.
    """
    if not laps:
        return {"classification": "unknown", "lap_count": 0, "reason": "no laps"}

    paces: list[float] = []
    for lap in laps:
        v = lap.get("average_speed_mps")
        if v is None or v <= 0:
            continue
        paces.append(1000.0 / v)
    if len(paces) < 2:
        return {
            "classification": "unknown",
            "lap_count": len(laps),
            "reason": "insufficient lap pace data",
        }

    mean_pace = statistics.fmean(paces)
    pace_cv = statistics.pstdev(paces) / mean_pace if mean_pace else 0.0
    median_pace = statistics.median(paces)

    # Sawtooth signal: how often consecutive laps cross the median (i.e.
    # alternate between work and recovery sides).
    transitions = sum(
        1 for a, b in zip(paces, paces[1:])
        if (a < median_pace) != (b < median_pace)
    )

    half = len(paces) // 2
    first = statistics.fmean(paces[:half]) if half else mean_pace
    second = statistics.fmean(paces[half:]) if half else mean_pace
    # positive = sped up over time (smaller s/km in the second half)
    half_diff_pct = (first - second) / mean_pace if mean_pace else 0.0

    # Classification thresholds picked to be robust to typical run lap counts:
    # - intervals: high pace variation AND many transitions (sawtooth)
    # - progression / split: meaningful first-vs-second-half pace shift
    # - mixed: some variation but no clean structure
    # - steady: low variation
    classification = "steady"
    transitions_threshold = max(2, len(paces) // 3)
    if pace_cv > 0.15 and transitions >= transitions_threshold:
        classification = "intervals"
    elif abs(half_diff_pct) > 0.05:
        classification = "negative_split" if half_diff_pct > 0 else "positive_split"
    elif pace_cv > 0.10:
        classification = "mixed"

    out = {
        "classification": classification,
        "lap_count": len(laps),
        "lap_pace_cv": round(pace_cv, 3),
        "transitions": transitions,
        "first_half_avg_pace_s_per_km": round(first, 1),
        "second_half_avg_pace_s_per_km": round(second, 1),
    }

    if classification == "intervals":
        # Heuristic split: laps faster than median = "work" reps. Their count
        # and mean duration usually echoes the prescription ("4 x 8 min" should
        # show ~4 work reps of ~480 s).
        work, rec = [], []
        for lap, p in zip(laps, paces):
            dur = lap.get("moving_time_s") or 0
            (work if p < median_pace else rec).append(dur)
        out["interval_guess"] = {
            "work_reps": len(work),
            "mean_work_s": round(statistics.fmean(work), 1) if work else 0.0,
            "mean_rec_s": round(statistics.fmean(rec), 1) if rec else 0.0,
        }
    return out


# --------------------------------------------------------------------------
# effort + focus tagging
# --------------------------------------------------------------------------

def effort_rating(zone_pcts: list[float], max_hr_observed: float,
                  max_hr_config: float) -> tuple[str, str]:
    """Map the time-in-zone histogram to a coarse effort tag.

    We tag from time-in-zone rather than total load because load conflates
    duration and intensity — a 3-hour easy run has similar TRIMP to a 45-min
    threshold session, but they're different stimuli and a coach should
    describe them differently.

    The thresholds here are calibrated to filter out incidental HR pushes
    (a single hill, a finish-line surge, a steep stretch) from genuine
    intentional intensity work. A 60 min run with one 2-min hill push will
    show ~3 % above threshold — the prescription was clearly aerobic, the
    HR push doesn't make it threshold work. The thresholds need to be high
    enough that "you spent meaningful time at this intensity" is a true
    statement, not just "you touched this intensity once".

    The tagging uses zone *positions* (index 0 = lowest), not names, so a
    custom 4-zone or 6-zone profile in config/training.json still works.
    """
    n = len(zone_pcts)
    if n == 0:
        return "unknown", "no zone data"

    pct_easy = zone_pcts[0]
    pct_steady = zone_pcts[1] if n >= 2 else 0.0
    pct_above_steady = sum(zone_pcts[2:]) if n >= 3 else 0.0
    pct_threshold_plus = sum(zone_pcts[3:]) if n >= 4 else 0.0
    pct_vo2_plus = sum(zone_pcts[4:]) if n >= 5 else 0.0

    max_hr_pct = (max_hr_observed / max_hr_config) if max_hr_config else 0.0

    if pct_easy >= 80 and max_hr_pct < 0.85:
        return "recovery", (f"{pct_easy:.0f}% in easy zone, "
                            f"peak HR {max_hr_observed:.0f}")
    if pct_vo2_plus >= 10:
        return "vo2_or_race", (f"{pct_vo2_plus:.0f}% above threshold, "
                               f"peak HR {max_hr_observed:.0f}")
    if pct_threshold_plus >= 15:
        return "threshold", f"{pct_threshold_plus:.0f}% at/above threshold zone"
    if pct_above_steady >= 30:
        return "tempo", f"{pct_above_steady:.0f}% above steady"
    if pct_easy >= 70:
        return "easy_aerobic", f"{pct_easy:.0f}% in easy zone"
    return "steady_aerobic", f"{pct_steady:.0f}% in steady zone"


# Long runs (≥ this many minutes of moving time) get a duration-aware focus
# tag. The dominant stimulus of a 90+ min run is aerobic; late-run surges
# or hilly sections shouldn't relabel it as a tempo or race effort.
LONG_RUN_MIN = 90


def primary_focus(effort: str, structure_class: str, duration_s: int) -> str:
    """Combine effort + structure + duration into a one-token training focus.

    For long runs (≥90 min), surface that the run was long even when the
    effort tag is high — `long_with_threshold` is more useful to a coach
    than `threshold_continuous` for a 2-hour run with a hard finish.
    """
    duration_min = duration_s / 60.0 if duration_s else 0
    is_long = duration_min >= LONG_RUN_MIN
    is_intervals = structure_class == "intervals"
    if effort == "recovery":
        return "recovery"
    if effort in ("easy_aerobic", "steady_aerobic"):
        return "long_endurance" if is_long else effort
    if effort == "tempo":
        if is_long:
            return "long_with_tempo"
        return "tempo_intervals" if is_intervals else "tempo_continuous"
    if effort == "threshold":
        if is_long:
            return "long_with_threshold"
        return "threshold_intervals" if is_intervals else "threshold_continuous"
    if effort == "vo2_or_race":
        if is_long:
            return "race_or_hard_long"
        return "vo2max_intervals" if is_intervals else "race_or_hard_continuous"
    return "unknown"


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def _pace_zone_out(z: dict, time_s: float, total_s: float) -> dict:
    """Render a pace-zone bucket. JSON has no Infinity, so the open upper
    bound becomes None."""
    pmax = z["pace_max"]
    return {
        "name": z["name"],
        "pace_s_per_km_min": round(z["pace_min"], 1) if z["pace_min"] > 0 else None,
        "pace_s_per_km_max": round(pmax, 1) if math.isfinite(pmax) else None,
        "time_s": round(time_s, 1),
        "pct": round(time_s / total_s * 100, 1) if total_s else 0.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="characterize",
        description=(
            "Characterize a Strava activity: effort, primary training focus, "
            "time-in-zone, training load, lap structure, and HR/pace drift. "
            "Reuses the strava CLI's auth + cache."
        ),
    )
    parser.add_argument("activity_id", type=int, help="Strava activity ID")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG),
                        help=f"Path to training profile (default: {DEFAULT_CONFIG})")
    parser.add_argument("--strava", default=str(DEFAULT_STRAVA),
                        help=f"Path to the strava CLI (default: {DEFAULT_STRAVA})")
    parser.add_argument("--resolution", default="medium",
                        choices=["low", "medium", "high"],
                        help="Stream resolution to request (default: medium)")
    parser.add_argument("--refresh", action="store_true",
                        help="Force-refetch activity + streams from Strava, "
                             "ignoring any cached entries")
    args = parser.parse_args()

    config = load_config(Path(args.config).expanduser())
    max_hr = float(config["max_hr"])
    resting_hr = float(config.get("resting_hr", 50))
    zones = config["hr_zones"]

    strava_path = Path(args.strava).expanduser()
    detail = fetch_activity(strava_path, args.activity_id, args.refresh)
    streams = fetch_streams(strava_path, args.activity_id, args.resolution, args.refresh)

    time_stream = streams.get("time", []) or []
    hr_stream = streams.get("heartrate", []) or []
    velocity_stream = streams.get("velocity_smooth", []) or []
    distance_stream = streams.get("distance", []) or []

    hr_zone_seconds = time_in_hr_zones(time_stream, hr_stream, zones)
    total_hr_time = sum(hr_zone_seconds)
    hr_zones_out = [
        {
            "name": z["name"],
            "min": z["min"],
            "max": z["max"],
            "time_s": round(s, 1),
            "pct": round(s / total_hr_time * 100, 1) if total_hr_time else 0.0,
        }
        for z, s in zip(zones, hr_zone_seconds)
    ]

    pace_zones = derive_pace_zones(velocity_stream)
    pace_zone_seconds = time_in_pace_zones(time_stream, velocity_stream, pace_zones)
    total_pace_time = sum(pace_zone_seconds)
    pace_zones_out = [
        _pace_zone_out(z, s, total_pace_time)
        for z, s in zip(pace_zones, pace_zone_seconds)
    ]

    trimp = trimp_banister(time_stream, hr_stream, max_hr, resting_hr)
    edwards = edwards_load(hr_zone_seconds)

    structure = lap_classify(detail.get("laps", []) or [])
    drift = drift_metrics(time_stream, hr_stream, velocity_stream, distance_stream)

    zone_pcts = [hz["pct"] for hz in hr_zones_out]
    max_hr_observed = max((hr for hr in hr_stream if hr is not None), default=0.0)
    rating, rationale = effort_rating(zone_pcts, max_hr_observed, max_hr)
    focus = primary_focus(rating, structure.get("classification", "unknown"),
                          detail.get("moving_time_s", 0) or 0)

    out = {
        "activity_id": args.activity_id,
        "summary": {
            "name": detail.get("name"),
            "type": detail.get("type"),
            "sport_type": detail.get("sport_type"),
            "start_date_local": detail.get("start_date_local"),
            "distance_km": detail.get("distance_km"),
            "moving_time_s": detail.get("moving_time_s"),
            "average_heartrate": detail.get("average_heartrate"),
            "max_heartrate": detail.get("max_heartrate"),
            "description": detail.get("description"),
        },
        "config_used": {
            "max_hr": max_hr,
            "resting_hr": resting_hr,
            "zones": zones,
        },
        "effort": {"rating": rating, "rationale": rationale},
        "primary_focus": focus,
        "load": {
            "trimp": trimp,
            "edwards": edwards,
            "strava_suffer_score": detail.get("suffer_score"),
        },
        "hr_zones": hr_zones_out,
        "pace_zones": pace_zones_out,
        "structure": structure,
        "drift": drift,
    }
    json.dump(out, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
