#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pytest"]
# ///
"""Tests for characterize.py.

Function-based pytest, runnable as a standalone script — the PEP-723 inline
metadata makes uv install pytest on demand. The bulk of the suite covers the
pure-math helpers (zone bucketing, TRIMP, lap classification, effort tagging),
with lighter monkeypatched coverage of the IO layer (config loading, the
strava CLI subprocess wrapper).

Run:
    .claude/skills/characterize-activity/test_characterize.py
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

import pytest

# characterize.py lives in the same directory as this test file. Running
# under uv run --script puts CWD wherever the user invoked from, so resolve
# explicitly rather than relying on import side-effects.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import characterize as c  # noqa: E402


# ---------------------------------------------------------------------------
# _zone_index
# ---------------------------------------------------------------------------

def test_zone_index_in_first_zone():
    zones = [{"min": 0, "max": 140}, {"min": 140, "max": 999}]
    assert c._zone_index(120, zones) == 0


def test_zone_index_at_boundary_goes_to_upper_zone():
    """Zone min is inclusive, max is exclusive — HR exactly at the boundary
    must fall into the upper zone, not the lower."""
    zones = [{"min": 0, "max": 140}, {"min": 140, "max": 999}]
    assert c._zone_index(140, zones) == 1


def test_zone_index_above_last_zone_clamps_to_last():
    """If HR exceeds the sentinel max of the last zone (e.g. 999), we still
    want it counted in the last zone rather than dropped — otherwise a freak
    sample would silently disappear from the totals."""
    zones = [{"min": 0, "max": 140}, {"min": 140, "max": 999}]
    assert c._zone_index(1500, zones) == 1


def test_zone_index_below_lowest_returns_none():
    zones = [{"min": 100, "max": 140}]
    assert c._zone_index(50, zones) is None


# ---------------------------------------------------------------------------
# time_in_hr_zones
# ---------------------------------------------------------------------------

def test_time_in_hr_zones_attributes_dt_to_correct_zone():
    zones = [{"min": 0, "max": 140}, {"min": 140, "max": 999}]
    # 10 s @ HR 130 (zone 0), then 20 s @ HR 150 (zone 1)
    out = c.time_in_hr_zones([0, 10, 30], [130, 150, 150], zones)
    assert out == [10.0, 20.0]


def test_time_in_hr_zones_skips_none_hr():
    zones = [{"min": 0, "max": 999}]
    out = c.time_in_hr_zones([0, 5, 10], [None, 130, 130], zones)
    # The (0,5) interval is skipped because the leading HR sample is None.
    assert out == [5.0]


def test_time_in_hr_zones_handles_empty_streams():
    zones = [{"min": 0, "max": 140}]
    assert c.time_in_hr_zones([], [], zones) == [0.0]


def test_time_in_hr_zones_skips_nonpositive_dt():
    """Clock glitches in stream data can produce non-monotonic time samples;
    we skip those rather than letting negative dt subtract from totals."""
    zones = [{"min": 0, "max": 999}]
    # Pairs: (0,10)=+10 OK, (10,5)=-5 skipped, (5,20)=+15 OK → 25 s.
    out = c.time_in_hr_zones([0, 10, 5, 20], [130, 130, 130, 130], zones)
    assert out == [25.0]


# ---------------------------------------------------------------------------
# derive_pace_zones
# ---------------------------------------------------------------------------

def test_derive_pace_zones_returns_5_bands_in_order():
    # Uniform velocity → median pace = 250 s/km. Five bands, fastest first.
    zones = c.derive_pace_zones([4.0] * 100)
    assert [z["name"] for z in zones] == [
        "very_fast", "fast", "steady", "easy", "very_easy",
    ]
    # Bounds must be strictly increasing in s/km (faster pace = smaller).
    for prev, curr in zip(zones, zones[1:]):
        assert prev["pace_max"] == curr["pace_min"]


def test_derive_pace_zones_excludes_walking_from_median():
    """A long walk break must not drag the median pace into walking
    territory — the histogram is meant to describe running effort variation,
    not "how much of the run was a walk"."""
    zones = c.derive_pace_zones([4.0] * 100 + [0.5] * 50)
    steady = next(z for z in zones if z["name"] == "steady")
    # Median of running samples is 250 s/km; steady band is ±5 % around it.
    assert 230 < steady["pace_min"] < 250 < steady["pace_max"] < 270


def test_derive_pace_zones_returns_empty_when_no_running():
    assert c.derive_pace_zones([]) == []
    assert c.derive_pace_zones([0.5, 0.6, 0.4]) == []  # all walking


# ---------------------------------------------------------------------------
# time_in_pace_zones
# ---------------------------------------------------------------------------

def test_time_in_pace_zones_buckets_by_pace():
    zones = [
        {"name": "fast", "pace_min": 0.0, "pace_max": 240.0},
        {"name": "slow", "pace_min": 240.0, "pace_max": math.inf},
    ]
    # 5 s @ 5 m/s (200 s/km, fast), 5 s @ 3 m/s (333 s/km, slow)
    out = c.time_in_pace_zones([0, 5, 10], [5.0, 3.0, 3.0], zones)
    assert out == [5.0, 5.0]


def test_time_in_pace_zones_excludes_walking():
    zones = [{"name": "any", "pace_min": 0.0, "pace_max": math.inf}]
    out = c.time_in_pace_zones([0, 10], [0.5, 0.5], zones)
    assert out == [0.0]


# ---------------------------------------------------------------------------
# trimp_banister
# ---------------------------------------------------------------------------

def test_trimp_at_resting_hr_is_zero():
    # HRr = 0 → contribution = 0 regardless of duration.
    assert c.trimp_banister([0, 60], [50, 50], max_hr=180, resting_hr=50) == 0.0


def test_trimp_handles_degenerate_max_eq_resting():
    """Bad config (max <= resting) must not divide by zero."""
    assert c.trimp_banister([0, 60], [180, 180], max_hr=50, resting_hr=50) == 0.0


def test_trimp_monotonic_in_intensity():
    """Same duration, higher avg HR must produce strictly higher TRIMP —
    that's the whole point of an intensity-weighted load metric."""
    low = c.trimp_banister([0, 60], [120, 120], max_hr=180, resting_hr=50)
    high = c.trimp_banister([0, 60], [160, 160], max_hr=180, resting_hr=50)
    assert 0 < low < high


def test_trimp_monotonic_in_duration():
    """Same intensity, longer must produce higher TRIMP."""
    short = c.trimp_banister([0, 60], [150, 150], max_hr=180, resting_hr=50)
    long_ = c.trimp_banister([0, 600], [150, 150], max_hr=180, resting_hr=50)
    assert long_ > short > 0


# ---------------------------------------------------------------------------
# edwards_load
# ---------------------------------------------------------------------------

def test_edwards_load_weights_by_zone_index():
    # 60 s in zone 0 (×1) + 60 s in zone 1 (×2) + 60 s in zone 4 (×5)
    # = 1 + 2 + 5 = 8 minutes-of-load.
    out = c.edwards_load([60.0, 60.0, 0.0, 0.0, 60.0])
    assert out == pytest.approx(8.0)


def test_edwards_load_zero_when_empty():
    assert c.edwards_load([0.0, 0.0]) == 0.0


# ---------------------------------------------------------------------------
# linear_slope
# ---------------------------------------------------------------------------

def test_linear_slope_perfect_line():
    assert c.linear_slope([0, 1, 2, 3], [0, 2, 4, 6]) == pytest.approx(2.0)


def test_linear_slope_constant_y_is_zero():
    assert c.linear_slope([0, 1, 2], [5, 5, 5]) == 0.0


def test_linear_slope_degenerate_inputs_return_zero():
    """Underdetermined fits must return 0, not NaN — NaN propagates into
    output JSON and breaks downstream consumers."""
    assert c.linear_slope([], []) == 0.0
    assert c.linear_slope([1], [2]) == 0.0
    assert c.linear_slope([1, 1, 1], [1, 2, 3]) == 0.0  # zero variance in x


# ---------------------------------------------------------------------------
# lap_classify
# ---------------------------------------------------------------------------

def _lap(speed_mps, moving_time_s=300):
    return {"average_speed_mps": speed_mps, "moving_time_s": moving_time_s}


def test_lap_classify_no_laps_unknown():
    out = c.lap_classify([])
    assert out == {"classification": "unknown", "lap_count": 0, "reason": "no laps"}


def test_lap_classify_single_lap_unknown():
    out = c.lap_classify([_lap(4.0)])
    assert out["classification"] == "unknown"
    assert out["lap_count"] == 1


def test_lap_classify_steady_when_low_variation():
    laps = [_lap(4.0 + 0.005 * i) for i in range(10)]
    out = c.lap_classify(laps)
    assert out["classification"] == "steady"
    assert out["lap_pace_cv"] < 0.05


def test_lap_classify_intervals_with_sawtooth():
    # 4 work reps (5 m/s, 240 s) alternating with 4 recoveries (3 m/s, 120 s).
    laps = []
    for _ in range(4):
        laps.append(_lap(5.0, moving_time_s=240))
        laps.append(_lap(3.0, moving_time_s=120))
    out = c.lap_classify(laps)
    assert out["classification"] == "intervals"
    assert out["interval_guess"]["work_reps"] == 4
    assert out["interval_guess"]["mean_work_s"] == pytest.approx(240.0)
    assert out["interval_guess"]["mean_rec_s"] == pytest.approx(120.0)


def test_lap_classify_negative_split_when_speeds_up():
    laps = [_lap(3.5 + 0.05 * i) for i in range(10)]
    out = c.lap_classify(laps)
    assert out["classification"] == "negative_split"
    # Second-half pace value (s/km) should be smaller — faster.
    assert out["second_half_avg_pace_s_per_km"] < out["first_half_avg_pace_s_per_km"]


def test_lap_classify_positive_split_when_slows_down():
    laps = [_lap(4.0 - 0.05 * i) for i in range(10)]
    out = c.lap_classify(laps)
    assert out["classification"] == "positive_split"


def test_lap_classify_skips_zero_velocity_laps():
    """A lap with avg_speed_mps = 0 (paused / GPS dropout) must not crash
    the classifier with a div-by-zero, and must not contribute to pace stats."""
    laps = [_lap(4.0), {"average_speed_mps": 0, "moving_time_s": 30}, _lap(4.0)]
    out = c.lap_classify(laps)
    assert out["lap_count"] == 3  # raw lap count includes the skipped lap
    assert out["lap_pace_cv"] == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# drift_metrics
# ---------------------------------------------------------------------------

def test_drift_metrics_constant_hr_zero_slope():
    n = 100
    time_ = list(range(n))
    hr = [140] * n
    vel = [4.0] * n
    dist = [4.0 * i for i in range(n)]
    out = c.drift_metrics(time_, hr, vel, dist)
    assert out["hr_per_km_bpm"] == pytest.approx(0.0)
    assert out["first_half_avg_hr"] == 140.0
    assert out["second_half_avg_hr"] == 140.0


def test_drift_metrics_rising_hr_positive_slope():
    """Cardiac drift: HR climbs over distance on a steady-paced run. Slope
    must be positive and split-half means must reflect the trend."""
    n = 100
    time_ = list(range(n))
    hr = [130 + 0.5 * i for i in range(n)]
    vel = [4.0] * n
    dist = [4.0 * i for i in range(n)]
    out = c.drift_metrics(time_, hr, vel, dist)
    assert out["hr_per_km_bpm"] > 0
    assert out["second_half_avg_hr"] > out["first_half_avg_hr"]


def test_drift_metrics_pace_excludes_walking():
    """Walking samples must be filtered from the pace fit — otherwise a
    long hill walk would fake "pace fade" that wasn't actually a fade."""
    n = 50
    time_ = list(range(n))
    hr = [140] * n
    # First half running (4 m/s), second half walking (0.5 m/s).
    vel = [4.0] * 25 + [0.5] * 25
    dist, cum = [], 0.0
    for v in vel:
        cum += v
        dist.append(cum)
    out = c.drift_metrics(time_, hr, vel, dist)
    # All retained pace samples have identical pace → slope ~0.
    assert out["pace_per_km_s"] == pytest.approx(0.0)


def test_drift_metrics_no_distance_returns_empty():
    """Manual-entry activities have no distance stream — the output should
    be an empty dict, not a crash or a misleading slope."""
    assert c.drift_metrics([0, 1], [140, 140], [4, 4], []) == {}


# ---------------------------------------------------------------------------
# effort_rating
# ---------------------------------------------------------------------------

def test_effort_rating_empty_zones_unknown():
    assert c.effort_rating([], 150, 180) == ("unknown", "no zone data")


def test_effort_rating_recovery_dominantly_easy_low_peak():
    out = c.effort_rating([90.0, 10.0, 0.0, 0.0, 0.0],
                          max_hr_observed=150, max_hr_config=180)
    assert out[0] == "recovery"


def test_effort_rating_high_peak_disqualifies_recovery():
    """Even with 90 % easy time, peaking ≥85 % of max means the user worked
    at some point — that's not recovery, regardless of dominant zone."""
    out = c.effort_rating([90.0, 10.0, 0.0, 0.0, 0.0],
                          max_hr_observed=170, max_hr_config=180)
    assert out[0] != "recovery"


def test_effort_rating_easy_aerobic_when_70pct_easy():
    assert c.effort_rating([75.0, 20.0, 5.0, 0.0, 0.0], 160, 180)[0] == "easy_aerobic"


def test_effort_rating_steady_aerobic_fallback():
    # Mostly steady, no rule fires until the steady-aerobic fallback.
    assert c.effort_rating([20.0, 60.0, 15.0, 5.0, 0.0], 160, 180)[0] == "steady_aerobic"


def test_effort_rating_threshold_at_15pct_threshold_plus():
    out = c.effort_rating([20.0, 40.0, 20.0, 18.0, 2.0], 165, 180)
    assert out[0] == "threshold"


def test_effort_rating_vo2_at_10pct_above_threshold():
    out = c.effort_rating([20.0, 30.0, 20.0, 18.0, 12.0], 175, 180)
    assert out[0] == "vo2_or_race"


def test_effort_rating_short_vo2_burst_does_not_trigger_vo2():
    """Calibration regression: the original >5 % vo2 trigger mislabeled
    long runs with a single hill push as race-effort. The bumped 10 %
    threshold must let a 5 % vo2 burst fall through to the threshold tag."""
    out = c.effort_rating([15.0, 30.0, 20.0, 30.0, 5.0], 170, 180)
    assert out[0] == "threshold"


def test_effort_rating_tempo_at_30pct_above_steady():
    """Calibration regression: original >15 % above-steady mislabeled a
    hilly social 10 k as tempo. Must require ≥30 % above steady."""
    out = c.effort_rating([20.0, 35.0, 35.0, 8.0, 2.0], 165, 180)
    assert out[0] == "tempo"


# ---------------------------------------------------------------------------
# primary_focus
# ---------------------------------------------------------------------------

def test_primary_focus_recovery_passthrough():
    assert c.primary_focus("recovery", "steady", 1800) == "recovery"


def test_primary_focus_long_endurance_for_long_aerobic():
    """≥90 min easy/steady → long_endurance regardless of structure tag."""
    assert c.primary_focus("easy_aerobic", "steady", 5400) == "long_endurance"
    assert c.primary_focus("steady_aerobic", "mixed", 5400) == "long_endurance"


def test_primary_focus_short_easy_stays_easy():
    assert c.primary_focus("easy_aerobic", "steady", 1800) == "easy_aerobic"


def test_primary_focus_long_with_threshold():
    """Quality finish in a long run keeps both signals visible — flat
    threshold_continuous would lose the "long" part of "long-with-quality"."""
    assert c.primary_focus("threshold", "negative_split", 6000) == "long_with_threshold"


def test_primary_focus_threshold_intervals():
    assert c.primary_focus("threshold", "intervals", 2400) == "threshold_intervals"


def test_primary_focus_threshold_continuous():
    assert c.primary_focus("threshold", "steady", 2400) == "threshold_continuous"


def test_primary_focus_vo2max_intervals():
    assert c.primary_focus("vo2_or_race", "intervals", 2400) == "vo2max_intervals"


def test_primary_focus_race_or_hard_continuous():
    assert c.primary_focus("vo2_or_race", "steady", 2400) == "race_or_hard_continuous"


def test_primary_focus_race_or_hard_long():
    assert c.primary_focus("vo2_or_race", "steady", 6000) == "race_or_hard_long"


def test_primary_focus_long_with_tempo():
    assert c.primary_focus("tempo", "steady", 6000) == "long_with_tempo"


# ---------------------------------------------------------------------------
# load_config
# ---------------------------------------------------------------------------

def test_load_config_missing_file_exits_with_pointer_to_skill_md(tmp_path):
    with pytest.raises(SystemExit) as exc:
        c.load_config(tmp_path / "nope.json")
    msg = str(exc.value)
    assert "training config not found" in msg
    # The error message must guide the next step, not just say "missing":
    assert "SKILL.md" in msg


def test_load_config_invalid_json_exits(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json {{")
    with pytest.raises(SystemExit) as exc:
        c.load_config(bad)
    assert "not valid JSON" in str(exc.value)


def test_load_config_missing_max_hr_exits(tmp_path):
    p = tmp_path / "config.json"
    p.write_text(json.dumps({"hr_zones": [{"name": "easy", "min": 0, "max": 140}]}))
    with pytest.raises(SystemExit) as exc:
        c.load_config(p)
    assert "max_hr" in str(exc.value)


def test_load_config_empty_zones_exits(tmp_path):
    p = tmp_path / "config.json"
    p.write_text(json.dumps({"max_hr": 180, "hr_zones": []}))
    with pytest.raises(SystemExit) as exc:
        c.load_config(p)
    assert "non-empty list" in str(exc.value)


def test_load_config_zone_missing_field_exits(tmp_path):
    p = tmp_path / "config.json"
    p.write_text(json.dumps({"max_hr": 180,
                              "hr_zones": [{"name": "easy", "min": 0}]}))  # no max
    with pytest.raises(SystemExit) as exc:
        c.load_config(p)
    assert "name/min/max" in str(exc.value)


def test_load_config_valid_returns_dict(tmp_path):
    cfg = {
        "max_hr": 184,
        "resting_hr": 48,
        "hr_zones": [
            {"name": "easy",   "min": 0,   "max": 140},
            {"name": "steady", "min": 140, "max": 999},
        ],
    }
    p = tmp_path / "config.json"
    p.write_text(json.dumps(cfg))
    assert c.load_config(p) == cfg


# ---------------------------------------------------------------------------
# _run_strava (subprocess wrapper)
# ---------------------------------------------------------------------------

def test_run_strava_returns_parsed_stdout(monkeypatch):
    class Fake:
        stdout = '{"id": 1, "name": "x"}'
        stderr = ""
        returncode = 0

    def fake_run(cmd, check, capture_output, text):
        return Fake()

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert c._run_strava(Path("/whatever"), ["activity", "1"]) == {"id": 1, "name": "x"}


def test_run_strava_missing_binary_exits_with_clear_message(monkeypatch):
    def raise_fnf(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(subprocess, "run", raise_fnf)
    with pytest.raises(SystemExit) as exc:
        c._run_strava(Path("/missing/strava.py"), ["whoami"])
    assert "strava CLI not found" in str(exc.value)


def test_run_strava_nonzero_exit_surfaces_stderr(monkeypatch):
    """When the strava CLI fails (auth, rate limit, network), its stderr is
    the only useful diagnostic — it must reach the user, not get swallowed."""
    def boom(cmd, check, capture_output, text):
        raise subprocess.CalledProcessError(2, cmd, output="", stderr="auth failed")

    monkeypatch.setattr(subprocess, "run", boom)
    with pytest.raises(SystemExit) as exc:
        c._run_strava(Path("/strava.py"), ["activity", "1"])
    assert "auth failed" in str(exc.value)


# ---------------------------------------------------------------------------
# _pace_zone_out
# ---------------------------------------------------------------------------

def test_pace_zone_out_renders_zero_lower_bound_as_none():
    """The fastest band has pace_min = 0 (open bottom). JSON has no concept
    of "no lower bound", so we render that as null rather than "0 s/km"."""
    z = {"name": "very_fast", "pace_min": 0.0, "pace_max": 250.0}
    out = c._pace_zone_out(z, time_s=100.0, total_s=1000.0)
    assert out["pace_s_per_km_min"] is None
    assert out["pace_s_per_km_max"] == 250.0
    assert out["pct"] == 10.0


def test_pace_zone_out_renders_inf_upper_bound_as_none():
    z = {"name": "very_easy", "pace_min": 400.0, "pace_max": math.inf}
    out = c._pace_zone_out(z, time_s=50.0, total_s=1000.0)
    assert out["pace_s_per_km_max"] is None


def test_pace_zone_out_pct_is_zero_when_total_zero():
    """No running samples (rest day cycling, manual entry) → don't divide
    by zero, just report 0 %."""
    z = {"name": "fast", "pace_min": 100.0, "pace_max": 200.0}
    out = c._pace_zone_out(z, time_s=0.0, total_s=0.0)
    assert out["pct"] == 0.0


# ---------------------------------------------------------------------------
# script entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
