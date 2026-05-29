#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Build a per-run dataset of GAP, HR, and gear for the last N days.

Calls the existing `strava` CLI (which already handles OAuth, caching of
activities under .cache/strava/activities/, and caching of streams under
.cache/strava/streams/). Activity details and streams are read from cache
on disk when present; the CLI is only invoked for entries the cache does
not yet have. The resulting dataset.json is what render.py consumes.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STRAVA_CLI = PROJECT_ROOT / ".claude" / "skills" / "strava" / "strava.py"
CACHE_DIR = PROJECT_ROOT / ".cache" / "strava"
CONFIG_PATH = PROJECT_ROOT / "config" / "training.json"
OUTPUT_PATH = Path(__file__).resolve().parent / "dataset.json"
GEAR_CACHE_PATH = Path(__file__).resolve().parent / "gear_cache.json"

WINDOW_DAYS = 520
STREAM_RESOLUTION = "medium"
STREAM_TYPES = "time,distance,altitude,heartrate"
MIN_DISTANCE_KM = 2.0
ALT_SMOOTH_WINDOW = 5
GRADE_CLAMP = 0.30  # ±30%, well past where Minetti's polynomial stays sane

# --- Low-HR outlier detection (wrist-optical cold-day dropouts) -------------
# The watch's wrist-based optical HR under-read on cold days through late 2024
# → Sep 2025. A Coros HR armband (upper-arm optical) was ordered 2025-09-19 and
# is the reliable source after delivery. Dropouts make a run look like "fast
# pace at low effort", which would wrongly flatter whatever shoe was on that
# day — so we flag them before the chart is read. See config/training.json
# `hr_data` and the project memory project_hr_monitor_wrist_unreliable.
COROS_ORDER_DATE = "2025-09-19"
SWITCH_SEARCH_END = "2025-11-03"   # order date + ~6 weeks: latest plausible adoption
HR_ANCHOR_WINDOW_DAYS = 120        # most-recent trusted runs used to fit HR≈a+b·GAP
# Residual rule (R3): the linear HR≈a+b·GAP trend over-predicts HR on slow easy
# runs, so a moderate negative residual is only a dropout signal in the fast band
# (where the trend is well-sampled and HR-for-pace is tight). A ~2σ plunge at ANY
# pace is a catastrophic sensor flatline (e.g. the HR 104/105 runs) — caught
# regardless of GAP.
FAST_GAP_MAX = 5.0                 # min/km — GAP band where the residual is trusted
RESID_DROP_FAST = 10.0             # bpm below trend (fast band) → dropout
RESID_Z = -2.0                     # ~2σ below trend at any pace → catastrophic flatline
# Absolute rules (GAP in min/km; on flat easy/interval runs GAP ≈ raw pace). The
# avg-HR rules (R1/R2) stay strict — widening them sweeps in genuine runs with a
# healthy max HR (sensor clearly working). Near-miss dropouts like the 4:45/140/
# max-152 run are instead caught by R4 (low max for a fast effort, now covering
# GAP ≤ 5:00) and R3 (below trend), which key off the actual dropout signature:
# a suppressed peak, not just a low average.
R1_GAP_MAX, R1_HR_MAX = 5.0, 140    # easy-low:  GAP ≤ 5:00 and avg HR < 140
R2_GAP_MAX, R2_HR_MAX = 4.75, 150   # fast-low:  GAP ≤ 4:45 and avg HR < 150
R4_GAP_MAX, R4_MAXHR_MAX = 5.0, 155  # max-hr sanity: GAP ≤ 5:00 and max HR < 155


def run_strava(*args: str) -> dict | list:
    proc = subprocess.run(
        [str(STRAVA_CLI), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout)


def load_gear_lookup() -> dict[str, str]:
    cfg = json.loads(CONFIG_PATH.read_text())
    out: dict[str, str] = {}
    for g in cfg.get("gear", []):
        gid = g.get("id")
        if not gid:
            continue
        nickname = g.get("nickname")
        name = g.get("name")
        out[gid] = nickname or name or gid
    return out


def load_gear_cache() -> dict[str, dict]:
    if GEAR_CACHE_PATH.exists():
        try:
            return json.loads(GEAR_CACHE_PATH.read_text())
        except (OSError, json.JSONDecodeError):
            return {}
    return {}


def save_gear_cache(cache: dict[str, dict]) -> None:
    GEAR_CACHE_PATH.write_text(json.dumps(cache, indent=2, sort_keys=True) + "\n")


def _normalise_model_token(tok: str) -> str:
    """Case-normalise a single model-name token without clobbering acronyms.

    Strava's gear strings mix user typos (`TORIN`, lowercase `speed`) with
    intentional styling (`SL`, `X3`, `UltraBoost`). Plain `.title()` destroys
    the latter, so apply per-token rules instead.
    """
    if not tok:
        return tok
    if any(c.isdigit() for c in tok):
        return tok  # "X3", "13", "6" — keep
    has_upper = any(c.isupper() for c in tok)
    has_lower = any(c.islower() for c in tok)
    if has_upper and has_lower:
        return tok  # mixed-case is already styled ("UltraBoost", "Evo")
    if tok.isupper():
        return tok if len(tok) <= 3 else tok.title()  # "SL" stays, "TORIN" → "Torin"
    if tok.islower():
        return tok.title()  # "speed" → "Speed"
    return tok


def _normalise_model_name(model: str) -> str:
    return " ".join(_normalise_model_token(t) for t in model.split())


def resolve_model_label(
    gear_id: str | None,
    gear_lookup: dict[str, str],
    gear_cache: dict[str, dict],
) -> str:
    """Return a model-level label for a gear id, e.g. "Adidas Evo SL".

    Sources brand_name + model_name from Strava via `strava gear <id>` and
    caches the result locally. Falls back to the config-defined friendly name
    when Strava returns blanks (placeholder gear like g1902237).
    """
    if not gear_id:
        return "unspecified"
    cached = gear_cache.get(gear_id)
    if cached is None:
        cached = run_strava("gear", gear_id)
        gear_cache[gear_id] = cached
        save_gear_cache(gear_cache)
    brand = " ".join((cached.get("brand_name") or "").split())
    model = _normalise_model_name(cached.get("model_name") or "")
    label = f"{brand} {model}".strip()
    if label:
        return label
    return gear_lookup.get(gear_id) or f"unknown ({gear_id})"


def load_activity_detail(activity_id: int) -> dict:
    """Read activity detail from disk if cached, else invoke the CLI.

    If the cached entry has `gear_id is None` we force a refresh: gear is
    typically assigned to a run *after* it uploads, but the strava CLI only
    bypasses the cache for activities younger than 2 days. Without this
    refresh, null-gear stays burned in forever even after the user attaches
    a shoe in the Strava UI.
    """
    cached_path = CACHE_DIR / "activities" / f"{activity_id}.json"
    if cached_path.exists():
        cached = json.loads(cached_path.read_text())
        if cached.get("gear_id") is not None:
            return cached
        return run_strava("activity", str(activity_id), "--refresh")
    return run_strava("activity", str(activity_id))


def load_streams(activity_id: int) -> dict:
    """Read merged streams from disk if all requested types are present, else
    invoke the CLI (which performs the partial-overlap merge for us)."""
    cached = CACHE_DIR / "streams" / f"{activity_id}.{STREAM_RESOLUTION}.json"
    needed = set(STREAM_TYPES.split(","))
    if cached.exists():
        existing = json.loads(cached.read_text())
        if needed.issubset(existing.keys()):
            return existing
    return run_strava(
        "streams", str(activity_id),
        "--types", STREAM_TYPES,
        "--resolution", STREAM_RESOLUTION,
    )


def smooth_altitude(altitudes: list[float], window: int) -> list[float]:
    if window <= 1 or len(altitudes) < window:
        return list(altitudes)
    out: list[float] = []
    half = window // 2
    n = len(altitudes)
    for i in range(n):
        lo = max(0, i - half)
        hi = min(n, i + half + 1)
        chunk = altitudes[lo:hi]
        out.append(sum(chunk) / len(chunk))
    return out


def minetti_cost(grade: float) -> float:
    """Energetic cost of running per metre at a given grade (rise/run).
    Minetti et al. 2002. Normalised against C(0) by the caller."""
    g = max(-GRADE_CLAMP, min(GRADE_CLAMP, grade))
    return 155.4 * g**5 - 30.4 * g**4 - 43.3 * g**3 + 46.3 * g**2 + 19.5 * g + 3.6


MINETTI_C0 = minetti_cost(0.0)


def compute_gap(streams: dict) -> tuple[float | None, float | None]:
    """Return (avg_pace_min_per_km, avg_gap_min_per_km) from streams.
    Either may be None if the streams are too sparse to be useful."""
    time_s = streams.get("time") or []
    distance = streams.get("distance") or []
    altitude = streams.get("altitude")

    if len(time_s) < 2 or len(distance) < 2 or distance[-1] <= 0:
        return None, None

    total_time = time_s[-1] - time_s[0]
    total_dist = distance[-1] - distance[0]
    if total_time <= 0 or total_dist <= 0:
        return None, None

    avg_pace_min_per_km = (total_time / 60.0) / (total_dist / 1000.0)

    if not altitude or len(altitude) != len(distance):
        # No altitude → treat GAP as raw pace rather than dropping the run.
        return avg_pace_min_per_km, avg_pace_min_per_km

    smoothed = smooth_altitude(altitude, ALT_SMOOTH_WINDOW)
    ga_distance = 0.0
    for i in range(1, len(distance)):
        dx = distance[i] - distance[i - 1]
        if dx <= 0:
            continue
        dy = smoothed[i] - smoothed[i - 1]
        grade = dy / dx
        ga_distance += dx * (minetti_cost(grade) / MINETTI_C0)

    if ga_distance <= 0:
        return avg_pace_min_per_km, avg_pace_min_per_km

    avg_gap_min_per_km = (total_time / 60.0) / (ga_distance / 1000.0)
    return avg_pace_min_per_km, avg_gap_min_per_km


def _median(values: list[float]) -> float:
    s = sorted(values)
    n = len(s)
    mid = n // 2
    return s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2.0


def theil_sen(xs: list[float], ys: list[float]) -> tuple[float, float]:
    """Robust line y ≈ a + b·x via the median of pairwise slopes (Theil–Sen).

    Pure-Python (no numpy), O(n²) over the anchor window — fine for a couple
    hundred points. Robust to the very dropouts we're trying to detect, so the
    trend reflects normal HR-for-GAP rather than being dragged down by them.
    """
    slopes = [
        (ys[j] - ys[i]) / (xs[j] - xs[i])
        for i in range(len(xs))
        for j in range(i + 1, len(xs))
        if xs[j] != xs[i]
    ]
    if not slopes:
        return _median(ys), 0.0
    b = _median(slopes)
    a = _median([y - b * x for x, y in zip(xs, ys)])
    return a, b


def annotate_hr_suspects(rows: list[dict]) -> str:
    """Flag low-HR wrist-optical dropouts in place; return the detected cutoff.

    Fits a robust HR≈a+b·GAP trend on the most-recent (trusted, post-Coros)
    runs, detects the wrist→Coros switch date from where dropout-like runs stop
    (bounded by the order date), then flags only pre-cutoff runs that trip any
    of the absolute/residual rules. Each row gains hr_suspect / hr_suspect_reason
    / hr_residual.
    """
    for r in rows:
        r["hr_suspect"] = False
        r["hr_suspect_reason"] = ""
        r["hr_residual"] = None

    usable = [r for r in rows if r.get("avg_hr") and r.get("avg_gap_min_per_km")]
    if len(usable) < 5:
        return COROS_ORDER_DATE  # too little data to model — flag nothing

    # Trusted anchor = most-recent HR_ANCHOR_WINDOW_DAYS of runs (post-Coros,
    # warm season). Dates are YYYY-MM-DD strings, so lexicographic max is latest.
    latest = max(r["date"] for r in usable)
    cutoff_anchor = _date_minus_days(latest, HR_ANCHOR_WINDOW_DAYS)
    anchor = [r for r in usable if r["date"] >= cutoff_anchor] or usable

    a, b = theil_sen(
        [r["avg_gap_min_per_km"] for r in anchor],
        [float(r["avg_hr"]) for r in anchor],
    )
    for r in usable:
        r["hr_residual"] = round(r["avg_hr"] - (a + b * r["avg_gap_min_per_km"]), 1)
    resid_sd = _stdev([r["hr_residual"] for r in anchor]) or 1.0

    # Detect the switch date: the day after the last *flag-worthy* run inside the
    # plausible window [order date, order date + ~6 weeks]. Using the same strict
    # criteria as flagging (not a looser residual-only test) keeps a genuine slow
    # recovery run — low HR at slow pace, large negative residual but no rule
    # tripped — from dragging the cutoff to the window end. Falls back to the
    # order date when nothing flag-worthy follows it.
    in_window = [
        r for r in usable
        if COROS_ORDER_DATE <= r["date"] <= SWITCH_SEARCH_END
        and _flag_reasons(r, resid_sd)
    ]
    cutoff = _date_plus_days(max(r["date"] for r in in_window), 1) if in_window else COROS_ORDER_DATE

    for r in usable:
        if r["date"] >= cutoff:
            continue  # post-Coros: trusted, never flagged
        reasons = _flag_reasons(r, resid_sd)
        if reasons:
            r["hr_suspect"] = True
            r["hr_suspect_reason"] = "+".join(reasons)
    return cutoff


def _flag_reasons(r: dict, resid_sd: float) -> list[str]:
    """Which dropout rules a run trips (empty = clean). GAP in min/km.

    R1/R2 absolute thresholds, R4 max-HR sanity, R3 the data-driven residual
    rule: a moderate drop only counts in the fast band (slow easy runs sit below
    the linear trend by design), but a ~2σ plunge at any pace is a flatline."""
    gap, hr, max_hr = r["avg_gap_min_per_km"], r["avg_hr"], r.get("max_hr")
    resid = r["hr_residual"]
    reasons: list[str] = []
    if gap <= R1_GAP_MAX and hr < R1_HR_MAX:
        reasons.append("R1")
    if gap <= R2_GAP_MAX and hr < R2_HR_MAX:
        reasons.append("R2")
    if (resid < -RESID_DROP_FAST and gap <= FAST_GAP_MAX) or (resid / resid_sd) < RESID_Z:
        reasons.append("R3")
    if max_hr is not None and gap <= R4_GAP_MAX and max_hr < R4_MAXHR_MAX:
        reasons.append("R4")
    return reasons


def _stdev(values: list[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    mean = sum(values) / n
    return (sum((v - mean) ** 2 for v in values) / (n - 1)) ** 0.5


def _date_minus_days(date_str: str, days: int) -> str:
    from datetime import date, timedelta
    return (date.fromisoformat(date_str) - timedelta(days=days)).isoformat()


def _date_plus_days(date_str: str, days: int) -> str:
    from datetime import date, timedelta
    return (date.fromisoformat(date_str) + timedelta(days=days)).isoformat()


def main() -> None:
    gear_lookup = load_gear_lookup()
    gear_cache = load_gear_cache()

    print(f"[1/3] Listing runs in the last {WINDOW_DAYS} days...", file=sys.stderr)
    summaries = run_strava("recent", "--since", f"{WINDOW_DAYS}d", "--type", "Run")
    print(f"      found {len(summaries)} run(s)", file=sys.stderr)

    print("[2/3] Fetching details + streams (cache-first)...", file=sys.stderr)
    rows: list[dict] = []
    skipped: dict[str, int] = {"no_hr": 0, "too_short": 0, "no_streams": 0}

    for i, s in enumerate(summaries, 1):
        aid = s["id"]
        if s.get("average_heartrate") is None:
            skipped["no_hr"] += 1
            continue
        if (s.get("distance_km") or 0) < MIN_DISTANCE_KM:
            skipped["too_short"] += 1
            continue

        detail = load_activity_detail(aid)
        streams = load_streams(aid)
        avg_pace, avg_gap = compute_gap(streams)
        if avg_pace is None:
            skipped["no_streams"] += 1
            continue

        gear_id = detail.get("gear_id")
        gear_label = gear_lookup.get(gear_id, f"unknown ({gear_id})") if gear_id else "unspecified"
        model_label = resolve_model_label(gear_id, gear_lookup, gear_cache)

        start = s.get("start_date_local") or ""
        rows.append({
            "id": aid,
            "date": start[:10],
            "name": s.get("name"),
            "distance_km": s.get("distance_km"),
            "moving_time_s": s.get("moving_time_s"),
            "avg_hr": s.get("average_heartrate"),
            "max_hr": s.get("max_heartrate"),
            "elev_gain_m": s.get("total_elevation_gain_m"),
            "elev_per_km": round((s.get("total_elevation_gain_m") or 0) / max(s.get("distance_km") or 1, 0.001), 1),
            "avg_pace_min_per_km": round(avg_pace, 3),
            "avg_gap_min_per_km": round(avg_gap, 3),
            "gear_id": gear_id,
            "gear_label": gear_label,
            "model_label": model_label,
        })
        if i % 5 == 0:
            print(f"      processed {i}/{len(summaries)}", file=sys.stderr)

    print("[3/3] Flagging low-HR outliers + writing dataset.json...", file=sys.stderr)
    wrist_optical_until = annotate_hr_suspects(rows)
    suspects = [r for r in rows if r.get("hr_suspect")]

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "window_days": WINDOW_DAYS,
        "stream_resolution": STREAM_RESOLUTION,
        "min_distance_km": MIN_DISTANCE_KM,
        "hr_outliers": {
            "wrist_optical_until": wrist_optical_until,
            "monitor_order_date": COROS_ORDER_DATE,
            "anchor_window_days": HR_ANCHOR_WINDOW_DAYS,
            "resid_drop_bpm": RESID_DROP_FAST,
            "n_suspect": len(suspects),
        },
        "activities": rows,
    }
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2) + "\n")

    print(
        f"\nIncluded {len(rows)} runs. Skipped: "
        f"no_hr={skipped['no_hr']}, too_short={skipped['too_short']}, "
        f"no_streams={skipped['no_streams']}.",
        file=sys.stderr,
    )
    print(
        f"\nWrist-optical cutoff detected at {wrist_optical_until} "
        f"(order date {COROS_ORDER_DATE}). Flagged {len(suspects)} low-HR run(s):",
        file=sys.stderr,
    )
    for r in sorted(suspects, key=lambda x: x["date"]):
        print(
            f"  {r['date']}  HR {r['avg_hr']:.0f} (max {r.get('max_hr') or 0:.0f})  "
            f"GAP {r['avg_gap_min_per_km']:.2f}  resid {r['hr_residual']:+.0f}  "
            f"[{r['hr_suspect_reason']}]  {r.get('name', '')} ({r['id']})",
            file=sys.stderr,
        )
    print(f"\nWrote {OUTPUT_PATH}", file=sys.stderr)


if __name__ == "__main__":
    main()
