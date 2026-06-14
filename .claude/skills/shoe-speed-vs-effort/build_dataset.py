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
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
STRAVA_CLI = PROJECT_ROOT / ".claude" / "skills" / "strava" / "strava.py"
CACHE_DIR = PROJECT_ROOT / ".cache" / "strava"
CONFIG_PATH = PROJECT_ROOT / "config" / "training.json"
ARTIFACT_DIR = PROJECT_ROOT / ".cache" / "shoe-speed-vs-effort"
OUTPUT_PATH = ARTIFACT_DIR / "dataset.json"
GEAR_CACHE_PATH = ARTIFACT_DIR / "gear_cache.json"

STREAM_RESOLUTION = "medium"
STREAM_TYPES = "time,distance,altitude,heartrate"
ALT_SMOOTH_WINDOW = 5

# --- Configurable knobs (config/training.json → `shoe_chart`) ----------------
# Everything in this section is athlete-specific and loaded from config at
# startup by configure(), with these literals as fallback defaults so a missing
# or partial `shoe_chart` block still runs. configure() overwrites these module
# globals so the rest of the file keeps referring to them by name. See SKILL.md
# for the bootstrap interview that proposes and writes them.
WINDOW_DAYS = 520
MIN_DISTANCE_KM = 2.0

# --- Low-HR outlier detection (wrist-optical cold-day dropouts) -------------
# Only relevant for athletes whose monitor under-reads — the whole block is gated
# on `shoe_chart.hr_correction.enabled`. A dropout makes a run look like "fast
# pace at low effort", which would wrongly flatter whatever shoe was on that day,
# so we flag them before the chart is read. The watch's wrist-based optical HR
# under-read on cold days until a Coros armband (upper-arm optical) was adopted;
# the switch date comes from `hr_data.monitor_order_date`. See config/training.json
# `hr_data` and the project memory project_hr_monitor_wrist_unreliable.
HR_CORRECTION_ENABLED = True
COROS_ORDER_DATE = "2025-09-19"    # = hr_data.monitor_order_date
SWITCH_SEARCH_END = "2025-11-03"   # order date + ~6 weeks: latest plausible adoption (derived)
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
#
# The R1/R2 avg-HR ceilings are NOT stored in `shoe_chart`: they coincide exactly
# with the easy- and steady-zone ceilings in `hr_zones`, so configure() reads them
# live from there (one source of truth — retuning a zone moves the rule). The GAP
# cutoffs and R4's max-HR don't sit on any zone boundary, so they are explicit
# `shoe_chart.hr_correction` numbers.
R1_GAP_MAX, R1_HR_MAX = 5.0, 140    # easy-low:  GAP ≤ 5:00 and avg HR < easy-zone ceiling
R2_GAP_MAX, R2_HR_MAX = 4.75, 150   # fast-low:  GAP ≤ 4:45 and avg HR < steady-zone ceiling
R4_GAP_MAX, R4_MAXHR_MAX = 5.0, 155  # max-hr sanity: GAP ≤ 5:00 and max HR < 155

# --- Cardiac-drift HR adjustment (long-run decoupling) ----------------------
# Longer-DURATION runs show a higher whole-run average HR for the same GAP
# (cardiac drift: HR creeps up with time on feet). On the chart that pushes long
# runs rightward, so they can only be compared within one distance band. The fix
# is a duration-driven adjustment, avg_hr_adj = avg_hr − c·(minutes − ref_min),
# where the drift coefficient c (bpm/min) is FITTED from the athlete's own trusted
# runs — never a textbook constant — and ref_min recenters on the median trusted
# duration so the cloud doesn't shift wholesale. See fit_hr_drift(). Defaults to
# on whenever HR-correction is on (it shares the same trusted population), gated on
# `shoe_chart.hr_drift.enabled`.
HR_DRIFT_ENABLED = True
DRIFT_MIN_TRUSTED = 8               # too few trusted runs ⇒ don't fit, leave HR raw

# --- Intra-run efficiency decay (within-run m/beat fade) ---------------------
# Powers Chart A: a per-run series of grade-adjusted distance-per-heartbeat
# (m/beat) vs distance INTO the run, so a shoe's within-run fade can be seen and
# shoes compared by how steeply their lines droop. Steady runs only (intervals
# are sawtooth, not a fade line). The opening WARMUP_TRIM_KM is dropped so the
# HR-from-rest ramp — which makes early m/beat read spuriously high — doesn't fake
# a downslope in every run. Grade is handled by the GAP factor, so terrain bumps
# don't masquerade as fade. Gated on `shoe_chart.intra_run_efficiency.enabled`.
INTRA_RUN_ENABLED = True
INTRA_DOWNSAMPLE_POINTS = 30        # target points per run after distance-binning
INTRA_SMOOTH_WINDOW_S = 90          # trailing window (s) for the rolling m/beat
INTRA_WARMUP_TRIM_KM = 0.6          # drop this opening distance (HR-from-rest ramp)
INTRA_MIN_POINTS = 6                # fewer downsampled points ⇒ no series/slope

# --- Interval / workout detection (dynamic, relative to each run) -----------
# A whole-run avg GAP/HR is meaningless for interval sessions — fast reps + slow
# recovery jogs + standing time blend into a fastish pace at a low HR, landing in
# the "free pace at low effort" corner. We instead represent an interval run by
# its WORK reps. Classification is entirely relative to the run's own laps, so it
# works whether reps are 3:55/km or a deliberately-easy 5:00/km; thresholds keyed
# off absolute pace would miss sub-threshold sessions. Classification + the
# work-rep transform are always on (a representation fix, not error correction);
# only the rep-HR-dropout *flagging* is gated on hr_correction.enabled.
INTERVAL_SUBST_M = 400          # a "substantial" lap (excludes jog/standing rests)
INTERVAL_REST_RATIO = 1.5       # lap slower than 1.5× the run's median substantial pace…
INTERVAL_REST_MIN_M = 200       # …or shorter than this ⇒ a recovery/standing lap
INTERVAL_WORK_MARGIN = 0.5      # work reps lie within this (min/km) of the fastest sub. lap
INTERVAL_MAX_WORKOUT_S = 95 * 60  # >95 min ⇒ long run/race (aid stops mimic rests), not intervals
INTERVAL_MIN_REC = 2            # need ≥2 recovery laps…
INTERVAL_MIN_WORK = 2           # …and ≥2 work reps
INTERVAL_REC_FALLBACK = 3       # ≥3 rests classifies even without a workout-keyword description
# Work-rep HR dropout (wrist drops on hard reps; whole-run avg/max hide them).
# The pace→max-HR floor is two-tier: faster reps demand a higher peak. A uniform
# drop (every rep low) won't trip the intra-run spread test, so the absolute
# floors are what catch easy-paced sessions like 4x4min "lugnt" at 4:45/km whose
# reps read max 110–123 — impossible for this athlete (easy HR ~135–145).
REP_DROP_BELOW_BEST = 20        # a rep ≥20 bpm below the run's best rep-max = intra-run drop
REP_FAST_PACE = 4.25            # a sub-4:15/km rep…
REP_FAST_MAXHR = 150            # …whose max HR stays under this is implausible
REP_EASY_PACE = 5.0             # an easy/sub-threshold rep (≤5:00/km, still faster than easy)…
REP_EASY_MAXHR = 135            # …whose max HR sits below easy-run HR is implausibly low
WORKOUT_KW = re.compile(
    r"(\d\s*[x×]\s*\d|[x×]\s*\d|\bmin\b|tröskel|threshold|interval|intervall"
    r"|tempo|fartlek|\brep|vila|vo2|backe|halvmara)",
    re.I,
)


def _zone_ceiling(hr_zones: list[dict], name: str, fallback: float) -> float:
    """Return the `max` of the named HR zone (case-insensitive), else fallback.

    R1/R2's avg-HR ceilings are the easy/steady zone tops — read them live so the
    rule tracks the configured zones instead of duplicating their numbers."""
    for z in hr_zones or []:
        if str(z.get("name", "")).lower() == name and z.get("max") is not None:
            return float(z["max"])
    return fallback


def configure(config: dict) -> None:
    """Overwrite the athlete-specific module globals from config/training.json.

    Reads `shoe_chart` (window, HR-correction knobs) with the literal module
    defaults as fallback, the R1/R2 HR ceilings live from `hr_zones`, and the
    monitor switch date from `hr_data`. Leaves everything at its default when a
    key is absent, so a partial or missing `shoe_chart` block still runs."""
    global WINDOW_DAYS, MIN_DISTANCE_KM
    global HR_CORRECTION_ENABLED, COROS_ORDER_DATE, SWITCH_SEARCH_END, HR_ANCHOR_WINDOW_DAYS
    global FAST_GAP_MAX, RESID_DROP_FAST, RESID_Z
    global R1_GAP_MAX, R1_HR_MAX, R2_GAP_MAX, R2_HR_MAX, R4_GAP_MAX, R4_MAXHR_MAX
    global REP_DROP_BELOW_BEST, REP_FAST_PACE, REP_FAST_MAXHR, REP_EASY_PACE, REP_EASY_MAXHR
    global HR_DRIFT_ENABLED, DRIFT_MIN_TRUSTED
    global INTRA_RUN_ENABLED, INTRA_DOWNSAMPLE_POINTS, INTRA_SMOOTH_WINDOW_S
    global INTRA_WARMUP_TRIM_KM, INTRA_MIN_POINTS

    sc = config.get("shoe_chart") or {}
    WINDOW_DAYS = sc.get("window_days", WINDOW_DAYS)
    MIN_DISTANCE_KM = sc.get("min_distance_km", MIN_DISTANCE_KM)

    hr = sc.get("hr_correction") or {}
    hr_data = config.get("hr_data") or {}
    # Disabled when explicitly off, or when there's no monitor history to model.
    HR_CORRECTION_ENABLED = bool(hr.get("enabled", bool(hr_data.get("monitor_order_date"))))

    COROS_ORDER_DATE = hr_data.get("monitor_order_date", COROS_ORDER_DATE)
    SWITCH_SEARCH_END = _date_plus_days(COROS_ORDER_DATE, 45)  # ~6 weeks after the switch
    HR_ANCHOR_WINDOW_DAYS = hr.get("anchor_window_days", HR_ANCHOR_WINDOW_DAYS)
    FAST_GAP_MAX = hr.get("fast_gap_max", FAST_GAP_MAX)
    RESID_DROP_FAST = hr.get("resid_drop_bpm", RESID_DROP_FAST)
    RESID_Z = hr.get("resid_z", RESID_Z)

    R1_GAP_MAX = hr.get("r1_gap_max", R1_GAP_MAX)
    R2_GAP_MAX = hr.get("r2_gap_max", R2_GAP_MAX)
    R4_GAP_MAX = hr.get("r4_gap_max", R4_GAP_MAX)
    R4_MAXHR_MAX = hr.get("r4_maxhr", R4_MAXHR_MAX)
    # R1/R2 avg-HR ceilings come straight from the configured zones.
    hr_zones = config.get("hr_zones") or []
    R1_HR_MAX = _zone_ceiling(hr_zones, "easy", R1_HR_MAX)
    R2_HR_MAX = _zone_ceiling(hr_zones, "steady", R2_HR_MAX)

    rep_fast = hr.get("rep_fast") or {}
    rep_easy = hr.get("rep_easy") or {}
    REP_DROP_BELOW_BEST = hr.get("rep_drop_below_best", REP_DROP_BELOW_BEST)
    REP_FAST_PACE = rep_fast.get("pace", REP_FAST_PACE)
    REP_FAST_MAXHR = rep_fast.get("maxhr", REP_FAST_MAXHR)
    REP_EASY_PACE = rep_easy.get("pace", REP_EASY_PACE)
    REP_EASY_MAXHR = rep_easy.get("maxhr", REP_EASY_MAXHR)

    # Cardiac-drift adjustment shares the trusted population with HR-correction,
    # so it defaults to on whenever that is and off otherwise — but can be flipped
    # independently via `shoe_chart.hr_drift.enabled`.
    drift = sc.get("hr_drift") or {}
    HR_DRIFT_ENABLED = bool(drift.get("enabled", HR_CORRECTION_ENABLED))
    DRIFT_MIN_TRUSTED = drift.get("min_trusted", DRIFT_MIN_TRUSTED)

    ire = sc.get("intra_run_efficiency") or {}
    INTRA_RUN_ENABLED = bool(ire.get("enabled", INTRA_RUN_ENABLED))
    INTRA_DOWNSAMPLE_POINTS = ire.get("downsample_points", INTRA_DOWNSAMPLE_POINTS)
    INTRA_SMOOTH_WINDOW_S = ire.get("smooth_window_s", INTRA_SMOOTH_WINDOW_S)
    INTRA_WARMUP_TRIM_KM = ire.get("warmup_trim_km", INTRA_WARMUP_TRIM_KM)
    INTRA_MIN_POINTS = ire.get("min_points", INTRA_MIN_POINTS)


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


def strava_factor(grade: float) -> float:
    """Pace-adjustment factor at a given grade (rise/run), digitized from
    Strava's empirically HR-fitted GAP curve (4th-order fit over ±25% grade).
    Replaces Minetti et al. 2002, whose constant-effort assumption over-credits
    steep downhills (its 'free speed' peak sits at ~-20% grade vs the empirical
    ~-10%). Normalised against f(0) by the caller.
    See https://educatedguesswork.org/posts/grade-vs-pace/."""
    p = max(-25.0, min(25.0, grade * 100.0))  # rise/run -> percent, clamp to fit range
    return 0.98462 + 0.030266 * p + 0.0018814 * p**2 - 3.3882e-6 * p**3 - 4.5704e-7 * p**4


STRAVA_F0 = strava_factor(0.0)


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
        ga_distance += dx * (strava_factor(grade) / STRAVA_F0)

    if ga_distance <= 0:
        return avg_pace_min_per_km, avg_pace_min_per_km

    avg_gap_min_per_km = (total_time / 60.0) / (ga_distance / 1000.0)
    return avg_pace_min_per_km, avg_gap_min_per_km


def _downsample_xy(
    xs: list[float], ys: list[float], target: int
) -> tuple[list[float], list[float]]:
    """Bin (xs, ys) into ~`target` evenly-spaced x-bins; mean x, median y per bin.

    Keeps the per-run series compact and smooth without dropping the shape. xs are
    assumed sorted ascending (distance into the run). Median y per bin resists the
    odd GPS/HR spike."""
    if len(xs) <= target:
        return list(xs), list(ys)
    lo, hi = xs[0], xs[-1]
    if hi <= lo:
        return list(xs), list(ys)
    width = (hi - lo) / target
    bins: dict[int, list[tuple[float, float]]] = {}
    for x, y in zip(xs, ys):
        idx = min(target - 1, int((x - lo) / width))
        bins.setdefault(idx, []).append((x, y))
    out_x: list[float] = []
    out_y: list[float] = []
    for idx in sorted(bins):
        pts = bins[idx]
        out_x.append(sum(p[0] for p in pts) / len(pts))
        out_y.append(_median([p[1] for p in pts]))
    return out_x, out_y


def compute_intra_run_efficiency(
    streams: dict,
) -> tuple[list[float], list[float], float] | None:
    """Within-run efficiency decay: rolling distance-per-heartbeat vs distance.

    Returns (km[], mbeat[], fade_slope) or None when the streams lack the
    HR/distance/time needed. m/beat at a point = grade-adjusted metres covered per
    heartbeat over a trailing INTRA_SMOOTH_WINDOW_S window (equivalent to the chart's
    1000/(GAP×HR), in its natural rolling form). The series is downsampled evenly
    along distance to ~INTRA_DOWNSAMPLE_POINTS, and fade_slope is a robust Theil–Sen
    fit of mbeat vs km (m/beat per km; negative = efficiency fades through the run).

    The first INTRA_WARMUP_TRIM_KM is dropped before anything is emitted: HR ramps
    from rest over the opening minutes, so early m/beat reads spuriously high and
    would fake a downslope in every run. Grade is handled via strava_factor, so
    terrain bumps don't masquerade as fade; what remains is drift + fatigue.
    """
    time_s = streams.get("time") or []
    distance = streams.get("distance") or []
    hr = streams.get("heartrate") or []
    n = len(time_s)
    if n < 3 or len(distance) != n or len(hr) != n or distance[-1] <= distance[0]:
        return None

    altitude = streams.get("altitude")
    smoothed = (
        smooth_altitude(altitude, ALT_SMOOTH_WINDOW)
        if altitude and len(altitude) == n
        else None
    )

    # Per-sample cumulative grade-adjusted distance (m) and cumulative beats.
    ga = [0.0] * n
    beats = [0.0] * n
    for i in range(1, n):
        dx = distance[i] - distance[i - 1]
        if dx < 0:
            dx = 0.0
        if smoothed is not None and dx > 0:
            grade = (smoothed[i] - smoothed[i - 1]) / dx
            ga[i] = ga[i - 1] + dx * (strava_factor(grade) / STRAVA_F0)
        else:
            ga[i] = ga[i - 1] + dx
        dt = time_s[i] - time_s[i - 1]
        if dt < 0:
            dt = 0.0
        beats[i] = beats[i - 1] + (hr[i] + hr[i - 1]) / 2.0 / 60.0 * dt

    # Skip the warmup distance, then build a trailing-window rolling m/beat.
    start_dist = distance[0]
    warmup_m = INTRA_WARMUP_TRIM_KM * 1000.0
    i0 = 0
    while i0 < n and (distance[i0] - start_dist) < warmup_m:
        i0 += 1
    if i0 >= n - 1:
        return None  # whole run inside the warmup trim

    km_series: list[float] = []
    mbeat_series: list[float] = []
    j = i0
    for i in range(i0 + 1, n):
        while j < i and (time_s[i] - time_s[j]) > INTRA_SMOOTH_WINDOW_S:
            j += 1
        d_ga = ga[i] - ga[j]
        d_beats = beats[i] - beats[j]
        if d_ga <= 0 or d_beats <= 0:
            continue
        km_series.append((distance[i] - start_dist) / 1000.0)
        mbeat_series.append(d_ga / d_beats)

    if len(km_series) < INTRA_MIN_POINTS:
        return None

    ds_km, ds_mbeat = _downsample_xy(km_series, mbeat_series, INTRA_DOWNSAMPLE_POINTS)
    if len(ds_km) < INTRA_MIN_POINTS:
        return None

    # theil_sen returns (intercept, slope); we want the slope.
    _, slope = theil_sen(ds_km, ds_mbeat)
    return (
        [round(v, 2) for v in ds_km],
        [round(v, 3) for v in ds_mbeat],
        round(slope, 4),
    )


def _lap_pace(lap: dict) -> float | None:
    s = lap.get("average_speed_mps")
    return (1000.0 / s) / 60.0 if s and s > 0 else None


def classify_workout(detail: dict) -> tuple[bool, list[tuple], int]:
    """Decide if a run is an interval/workout, relative to its own lap structure.

    Returns (is_interval, work_laps, recovery_count) where each work lap is a
    (pace_min_per_km, distance_m, max_heartrate) tuple. Recovery laps are laps
    dramatically slower than this run's own median rep pace (7–27 min/km standing/
    jog rests never occur in a steady run) or very short. Work reps are the
    substantial laps within INTERVAL_WORK_MARGIN of the run's fastest substantial
    lap — so warm-up/cool-down (slower) drop out. The dynamic median anchor is why
    this catches sub-threshold reps at 5:00/km as well as 3:55/km track reps.
    """
    laps = detail.get("laps") or []
    parsed = [
        (_lap_pace(l), l.get("distance_m") or 0, l.get("max_heartrate"))
        for l in laps
    ]
    parsed = [(p, d, m) for (p, d, m) in parsed if p is not None and d > 20]
    subst = [t for t in parsed if t[1] >= INTERVAL_SUBST_M]
    if len(subst) < 2:
        return False, [], 0

    median_pace = _median([p for p, _, _ in subst])
    rest_pace = INTERVAL_REST_RATIO * median_pace
    recoveries = [t for t in parsed if t[0] > rest_pace or t[1] < INTERVAL_REST_MIN_M]
    fastest = min(p for p, _, _ in subst)
    work = [t for t in subst if t[0] <= fastest + INTERVAL_WORK_MARGIN and t[0] <= rest_pace]

    moving_s = detail.get("moving_time_s") or 0
    has_keyword = bool(WORKOUT_KW.search(detail.get("description") or ""))
    is_interval = (
        moving_s < INTERVAL_MAX_WORKOUT_S
        and len(recoveries) >= INTERVAL_MIN_REC
        and len(work) >= INTERVAL_MIN_WORK
        and (has_keyword or len(recoveries) >= INTERVAL_REC_FALLBACK)
    )
    return is_interval, work, len(recoveries)


def work_rep_point(
    work_laps: list[tuple], avg_pace: float, avg_gap: float
) -> tuple[float, float, int] | None:
    """Collapse work reps into one comparable point: (work_gap, mean rep-max HR, n).

    x = distance-weighted work-rep pace, scaled by the run's overall GAP/pace ratio
    so it lands on the same grade-adjusted-pace axis as steady runs without the
    fragility of slicing streams per lap (flat/treadmill reps → ratio ≈ 1).
    y = mean of per-rep MAX HR — a work rep's *average* HR understates effort
    because HR lags at rep start, so the per-rep max is the closest apples-to-apples
    to a steady run's average HR.
    """
    reps = [(p, d, m) for (p, d, m) in work_laps if p and d > 0 and m]
    if len(reps) < INTERVAL_MIN_WORK:
        return None
    total_d = sum(d for _, d, _ in reps)
    work_pace = sum(p * d for p, d, _ in reps) / total_d
    gap_factor = (avg_gap / avg_pace) if avg_pace else 1.0
    work_gap = work_pace * gap_factor
    maxhr_mean = sum(m for _, _, m in reps) / len(reps)
    return work_gap, maxhr_mean, len(reps)


def work_rep_dropout(work_laps: list[tuple]) -> str:
    """Reason string if any work rep's max HR is implausibly low (else "").

    Era-agnostic: a sub-4:15/km rep that never clears 150, or a rep whose max sits
    far below the run's best rep, is a sensor drop whenever it happens — and the
    whole-run average/max hide it."""
    reps = [(p, d, m) for (p, d, m) in work_laps if m]
    if len(reps) < 2:
        return ""
    best = max(m for _, _, m in reps)
    reasons: list[str] = []
    if any(best - m >= REP_DROP_BELOW_BEST for _, _, m in reps):
        reasons.append("rep-spread")
    if any(
        (p <= REP_FAST_PACE and m < REP_FAST_MAXHR)
        or (p <= REP_EASY_PACE and m < REP_EASY_MAXHR)
        for p, _, m in reps
    ):
        reasons.append("rep-floor")
    return "+".join(reasons)


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

    # Interval runs are excluded: their whole-run avg GAP/HR is a meaningless blend,
    # so they neither anchor the trend nor get judged by the steady rules. They are
    # handled separately via the work-rep transform.
    usable = [
        r for r in rows
        if r.get("avg_hr") and r.get("avg_gap_min_per_km") and not r.get("is_interval")
    ]
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


def _percentile(values: list[float], pct: float) -> float:
    """Linear-interpolated percentile (pct in 0..100) of a non-empty list."""
    s = sorted(values)
    if len(s) == 1:
        return s[0]
    rank = (pct / 100.0) * (len(s) - 1)
    lo = int(rank)
    frac = rank - lo
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + frac * (s[hi] - s[lo])


def fit_hr_drift(
    rows: list[dict], cutoff: str
) -> tuple[float, float, int, float, float] | None:
    """Fit cardiac-drift coefficient c (bpm/min), ref duration, and clamp bounds.

    Two robust passes on the SAME trusted population that anchors HR-suspect
    detection (post-cutoff steady runs with HR + GAP + duration, not flagged):

      1. HR ≈ a + b·GAP via Theil–Sen — the normal HR-for-pace trend.
      2. (HR − predicted) regressed on duration via Theil–Sen → slope c, the bpm
         the average rises per extra minute on feet, with the pace effect already
         removed (so c isn't just long-runs-are-slower leaking back in).

    ref_min = median trusted duration, so normalising to it recenters rather than
    shifts the whole cloud. We also return (lo_min, hi_min) = the 5th/95th-percentile
    trusted durations: the adjustment clamps each run's duration into this band
    before shifting, so the linear coefficient is never extrapolated past the range
    it was fit on (otherwise a 14-hour ultra would get a −30 bpm fantasy shift).
    Theil–Sen itself is robust to such outliers, but the clamp keeps the *applied*
    correction inside the data's support too.

    Returns None when there are too few trusted runs to fit (caller leaves HR
    unadjusted). Must run AFTER annotate_hr_suspects so hr_suspect flags exist.
    """
    trusted = [
        r for r in rows
        if r.get("avg_hr") and r.get("avg_gap_min_per_km") and r.get("moving_time_s")
        and not r.get("is_interval") and not r.get("hr_suspect")
        and r["date"] >= cutoff
    ]
    if len(trusted) < DRIFT_MIN_TRUSTED:
        return None

    a, b = theil_sen(
        [r["avg_gap_min_per_km"] for r in trusted],
        [float(r["avg_hr"]) for r in trusted],
    )
    minutes = [r["moving_time_s"] / 60.0 for r in trusted]
    residuals = [
        float(r["avg_hr"]) - (a + b * r["avg_gap_min_per_km"]) for r in trusted
    ]
    _, c = theil_sen(minutes, residuals)
    ref_min = _median(minutes)
    lo_min = _percentile(minutes, 5)
    hi_min = _percentile(minutes, 95)
    return round(c, 4), round(ref_min, 1), len(trusted), round(lo_min, 1), round(hi_min, 1)


def main() -> None:
    if not CONFIG_PATH.exists():
        sys.exit(
            f"error: training config not found at {CONFIG_PATH}\n"
            "Run the shoe-speed-vs-effort skill's bootstrap (see SKILL.md) to create it."
        )
    config = json.loads(CONFIG_PATH.read_text())
    configure(config)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    gear_lookup = load_gear_lookup()
    gear_cache = load_gear_cache()

    if HR_CORRECTION_ENABLED:
        print(
            f"      HR-dropout correction ON (monitor switch {COROS_ORDER_DATE}, "
            f"R1 HR<{R1_HR_MAX:.0f}, R2 HR<{R2_HR_MAX:.0f})",
            file=sys.stderr,
        )
    else:
        print("      HR-dropout correction OFF (shoe_chart.hr_correction disabled)", file=sys.stderr)

    print(f"[1/3] Listing runs in the last {WINDOW_DAYS} days...", file=sys.stderr)
    summaries = run_strava("recent", "--since", f"{WINDOW_DAYS}d", "--type", "Run")
    print(f"      found {len(summaries)} run(s)", file=sys.stderr)

    print("[2/3] Fetching details + streams (cache-first)...", file=sys.stderr)
    rows: list[dict] = []
    skipped: dict[str, int] = {"no_hr": 0, "too_short": 0, "no_streams": 0, "treadmill": 0}

    for i, s in enumerate(summaries, 1):
        aid = s["id"]
        # Treadmill/indoor runs never record their incline, so GAP silently
        # collapses to raw pace (a hill session reads as flat) — drop them
        # rather than place them at a distorted GAP. Strava's `trainer` flag is
        # the canonical signal; it's set reliably by the user's watch.
        if s.get("trainer"):
            skipped["treadmill"] += 1
            continue
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
        row = {
            "id": aid,
            "date": start[:10],
            "name": s.get("name"),
            "description": detail.get("description") or "",
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
            "is_interval": False,
        }

        # Interval/workout runs: represent by their work reps instead of the
        # meaningless whole-run blend. A classified-interval run with no usable
        # work reps falls back to a steady point.
        is_interval, work_laps, _ = classify_workout(detail)
        if is_interval:
            point = work_rep_point(work_laps, avg_pace, avg_gap)
            if point:
                work_gap, work_maxhr_mean, n_reps = point
                dropout = work_rep_dropout(work_laps) if HR_CORRECTION_ENABLED else ""
                row.update({
                    "is_interval": True,
                    "n_work_reps": n_reps,
                    "work_gap_min_per_km": round(work_gap, 3),
                    "work_maxhr_mean": round(work_maxhr_mean, 1),
                    "interval_hr_suspect": bool(dropout),
                    "interval_hr_reason": dropout,
                })

        # Within-run efficiency decay series (Chart A) — steady runs only; a
        # sawtooth interval isn't a fade line. Absent on runs whose streams are
        # too sparse; render.py just skips runs without it.
        if INTRA_RUN_ENABLED and not row["is_interval"]:
            intra = compute_intra_run_efficiency(streams)
            if intra:
                km_s, mbeat_s, fade = intra
                row["intra_km"] = km_s
                row["intra_mbeat"] = mbeat_s
                row["intra_fade_slope"] = fade

        rows.append(row)
        if i % 5 == 0:
            print(f"      processed {i}/{len(summaries)}", file=sys.stderr)

    if HR_CORRECTION_ENABLED:
        print("[3/3] Flagging low-HR outliers + writing dataset.json...", file=sys.stderr)
        wrist_optical_until = annotate_hr_suspects(rows)
    else:
        print("[3/3] Writing dataset.json (HR correction off, nothing flagged)...", file=sys.stderr)
        for r in rows:
            r["hr_suspect"] = False
            r["hr_suspect_reason"] = ""
            r["hr_residual"] = None
        wrist_optical_until = None

    # Cardiac-drift adjustment: fit c (bpm/min) + ref duration from trusted runs,
    # then store a duration-normalised avg_hr_adj (and work_maxhr_mean_adj for
    # intervals) per row so render.py can offer a drift-adjusted HR axis. The fit
    # excludes suspects, so it must run after annotate_hr_suspects; when correction
    # is off there's no cutoff, so every row is trusted (cutoff = "").
    drift = fit_hr_drift(rows, wrist_optical_until or "") if HR_DRIFT_ENABLED else None
    if drift:
        c, ref_min, n_trusted, lo_min, hi_min = drift
        for r in rows:
            mins = (r.get("moving_time_s") or 0) / 60.0
            if r.get("avg_hr") and mins:
                # Clamp duration into the fitted band before shifting so the linear
                # coefficient is never extrapolated beyond the data's support. A run
                # past the ceiling (a long run / ultra) is therefore deliberately
                # under-corrected — flag it so render.py can mark it as out-of-regime.
                clamped = min(hi_min, max(lo_min, mins))
                shift = c * (clamped - ref_min)
                r["avg_hr_adj"] = round(r["avg_hr"] - shift, 1)
                r["drift_clamped"] = mins > hi_min
                if r.get("work_maxhr_mean") is not None:
                    r["work_maxhr_mean_adj"] = round(r["work_maxhr_mean"] - shift, 1)
            else:
                r["avg_hr_adj"] = None
        print(
            f"      drift fit: c={c:+.3f} bpm/min, ref={ref_min:.0f} min, "
            f"clamp=[{lo_min:.0f},{hi_min:.0f}] min, n_trusted={n_trusted}",
            file=sys.stderr,
        )
    else:
        for r in rows:
            r["avg_hr_adj"] = None
        if HR_DRIFT_ENABLED:
            print("      drift fit skipped: too few trusted runs", file=sys.stderr)

    suspects = [r for r in rows if r.get("hr_suspect")]
    intervals = [r for r in rows if r.get("is_interval")]
    interval_drops = [r for r in intervals if r.get("interval_hr_suspect")]

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "window_days": WINDOW_DAYS,
        "stream_resolution": STREAM_RESOLUTION,
        "min_distance_km": MIN_DISTANCE_KM,
        "hr_outliers": {
            "enabled": HR_CORRECTION_ENABLED,
            "wrist_optical_until": wrist_optical_until,
            "monitor_order_date": COROS_ORDER_DATE if HR_CORRECTION_ENABLED else None,
            "anchor_window_days": HR_ANCHOR_WINDOW_DAYS,
            "resid_drop_bpm": RESID_DROP_FAST,
            "n_suspect": len(suspects),
        },
        "intervals": {
            "n_interval": len(intervals),
            "n_rep_dropout": len(interval_drops),
            "note": "interval runs are plotted at work-rep pace × mean per-rep max HR",
        },
        "hr_drift": {
            "enabled": bool(drift),
            "driver": "duration_min",
            "c_bpm_per_min": drift[0] if drift else None,
            "ref_min": drift[1] if drift else None,
            "n_trusted": drift[2] if drift else None,
            "clamp_min": [drift[3], drift[4]] if drift else None,
        },
        "intra_run_efficiency": {
            "enabled": INTRA_RUN_ENABLED,
            "n_series": sum(1 for r in rows if r.get("intra_km")),
            "downsample_points": INTRA_DOWNSAMPLE_POINTS,
            "smooth_window_s": INTRA_SMOOTH_WINDOW_S,
            "warmup_trim_km": INTRA_WARMUP_TRIM_KM,
            "note": "per-run grade-adjusted m/beat vs distance into the run; warmup trimmed; steady runs only",
        },
        "activities": rows,
    }
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2) + "\n")

    if INTRA_RUN_ENABLED:
        n_intra = sum(1 for r in rows if r.get("intra_km"))
        print(
            f"      intra-run efficiency series built for {n_intra} steady run(s) "
            f"(~{INTRA_DOWNSAMPLE_POINTS} pts each, warmup {INTRA_WARMUP_TRIM_KM} km trimmed)",
            file=sys.stderr,
        )

    print(
        f"\nIncluded {len(rows)} runs. Skipped: "
        f"no_hr={skipped['no_hr']}, too_short={skipped['too_short']}, "
        f"no_streams={skipped['no_streams']}, treadmill={skipped['treadmill']}.",
        file=sys.stderr,
    )
    if HR_CORRECTION_ENABLED:
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

    drop_suffix = (
        f"; {len(interval_drops)} with a work-rep HR dropout"
        if HR_CORRECTION_ENABLED else ""
    )
    print(
        f"\nClassified {len(intervals)} interval/workout run(s){drop_suffix}:",
        file=sys.stderr,
    )
    for r in sorted(intervals, key=lambda x: x["date"]):
        drop = f"  <DROP {r['interval_hr_reason']}>" if r.get("interval_hr_suspect") else ""
        print(
            f"  {r['date']}  {r['n_work_reps']}×reps  workGAP {r['work_gap_min_per_km']:.2f}  "
            f"repMaxHR̄ {r['work_maxhr_mean']:.0f}  ({(r.get('description') or '')[:24]}){drop}",
            file=sys.stderr,
        )
    print(f"\nWrote {OUTPUT_PATH}", file=sys.stderr)


if __name__ == "__main__":
    main()
