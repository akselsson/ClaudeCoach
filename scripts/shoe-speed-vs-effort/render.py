#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["plotly>=5.20", "pandas>=2.0"]
# ///
"""Render the shoe-speed-vs-effort scatter from dataset.json.

Reads dataset.json (produced by build_dataset.py) and writes a self-contained
HTML file with a Plotly scatter plot: x = grade-adjusted pace, y = average HR,
color = shoe. Hover shows the per-run context.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = Path(__file__).resolve().parent / "dataset.json"
OUTPUT_PATH = PROJECT_ROOT / "viz" / "shoe-speed-vs-effort.html"


def pace_to_label(min_per_km: float) -> str:
    m = int(min_per_km)
    s = round((min_per_km - m) * 60)
    if s == 60:
        m, s = m + 1, 0
    return f"{m}:{s:02d}/km"


def main() -> None:
    if not DATASET_PATH.exists():
        sys.exit(f"dataset not found at {DATASET_PATH} — run build_dataset.py first")

    payload = json.loads(DATASET_PATH.read_text())
    activities = payload.get("activities", [])
    if not activities:
        sys.exit("dataset has no activities")

    df = pd.DataFrame(activities)
    df["pace_label"] = df["avg_pace_min_per_km"].map(pace_to_label)
    df["gap_label"] = df["avg_gap_min_per_km"].map(pace_to_label)
    for col, default in (("hr_suspect", False), ("hr_suspect_reason", ""),
                         ("is_interval", False), ("interval_hr_suspect", False)):
        if col not in df.columns:
            df[col] = default
    # These flags are absent on rows they don't apply to → object dtype with NaN.
    # Cast to real bool so `~`/`&` do boolean (not bitwise-int) ops.
    for col in ("hr_suspect", "is_interval", "interval_hr_suspect"):
        df[col] = df[col].fillna(False).astype(bool)

    # Explicit shoe→colour map (sorted, stable) so the per-shoe circles and the
    # interval diamonds drawn later share the same colour per shoe.
    palette = px.colors.qualitative.Light24
    models = sorted(df["model_label"].dropna().unique())
    cmap = {m: palette[i % len(palette)] for i, m in enumerate(models)}

    # Three populations, each in its own trace(s) so they're independently
    # toggleable: steady runs (per-shoe circles), wrist-optical suspects (red
    # rings), and interval/workout runs (work-rep diamonds). A run is never in
    # more than one — interval and suspect runs are pulled out of the per-shoe
    # scatter so they don't pollute a shoe's cluster or sit at a misleading point.
    df_steady = df[~df["hr_suspect"] & ~df["is_interval"]]

    fig = px.scatter(
        df_steady,
        x="avg_gap_min_per_km",
        y="avg_hr",
        color="model_label",
        color_discrete_map=cmap,
        size="distance_km",
        size_max=22,
        hover_name="name",
        custom_data=["date", "distance_km", "elev_gain_m", "pace_label", "gap_label", "avg_hr", "max_hr", "gear_label", "id"],
        title=f"Shoe speed vs. effort — last {payload.get('window_days', '?')} days",
    )
    fig.update_traces(
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "%{customdata[0]} · %{customdata[1]:.1f} km · +%{customdata[2]:.0f} m<br>"
            "Pace %{customdata[3]} · GAP %{customdata[4]}<br>"
            "HR avg %{customdata[5]:.0f} (max %{customdata[6]:.0f})<br>"
            "Gear: %{customdata[7]}<br>"
            "<i>click to open in Strava</i><extra></extra>"
        ),
        marker=dict(line=dict(width=0.5, color="rgba(255,255,255,0.35)")),
    )
    fig.update_xaxes(
        title="Grade-adjusted pace (min/km, faster →)",
        autorange="reversed",
    )
    fig.update_yaxes(title="Average heart rate (bpm)")

    # Flagged low-HR wrist-optical dropouts as their own toggleable trace (red
    # rings). Uncheck it in the legend to view the chart without outliers. Size
    # uses the same area-sizeref as the per-shoe dots so distances stay
    # comparable; sizemin keeps short runs visible next to the 100km+ ultras.
    sizeref = 2.0 * df["distance_km"].max() / (22.0 ** 2)
    suspect = df[df["hr_suspect"]]
    hr_meta = payload.get("hr_outliers", {})
    if not suspect.empty:
        fig.add_trace(go.Scatter(
            x=suspect["avg_gap_min_per_km"],
            y=suspect["avg_hr"],
            mode="markers",
            name="⚠ Suspect HR (wrist optical)",
            hovertext=suspect["name"],
            customdata=suspect[[
                "date", "distance_km", "elev_gain_m", "pace_label", "gap_label",
                "avg_hr", "max_hr", "gear_label", "hr_suspect_reason", "id",
            ]].values,
            marker=dict(
                symbol="circle-open",
                size=suspect["distance_km"] * 1.6,
                sizemode="area",
                sizeref=sizeref,
                sizemin=9,
                color="rgba(255,80,80,0.95)",
                line=dict(width=2, color="rgba(255,80,80,0.95)"),
            ),
            hovertemplate=(
                "<b>%{hovertext}</b> — ⚠ suspect HR<br>"
                "%{customdata[0]} · %{customdata[1]:.1f} km · +%{customdata[2]:.0f} m<br>"
                "Pace %{customdata[3]} · GAP %{customdata[4]}<br>"
                "HR avg %{customdata[5]:.0f} (max %{customdata[6]:.0f})<br>"
                "Gear: %{customdata[7]}<br>"
                "Flagged: %{customdata[8]} · likely cold-day wrist-optical drop<br>"
                "<i>click to open in Strava</i><extra></extra>"
            ),
        ))

    # Interval/workout runs at the work-rep pace × mean per-rep max HR (rest laps
    # removed) so they sit at their true effort, not the misleading lower-right
    # blend. Split into TWO traces — clean reps vs rep-dropouts — so the dropout
    # series is the dropouts' SOLE home and unchecking it removes them outright
    # (same pattern as the steady "Suspect HR" toggle), not just a ring overlay.
    interval = df[df["is_interval"]].copy()
    interval["work_gap_label"] = interval["work_gap_min_per_km"].map(pace_to_label)
    interval_clean = interval[~interval["interval_hr_suspect"]]
    rep_drop = interval[interval["interval_hr_suspect"]]

    if not interval_clean.empty:
        fig.add_trace(go.Scatter(
            x=interval_clean["work_gap_min_per_km"],
            y=interval_clean["work_maxhr_mean"],
            mode="markers",
            name="◆ Interval (work-rep)",
            hovertext=interval_clean["name"],
            customdata=interval_clean[[
                "date", "n_work_reps", "work_gap_label", "work_maxhr_mean",
                "gear_label", "description", "id",
            ]].values,
            marker=dict(
                symbol="diamond",
                size=interval_clean["distance_km"],
                sizemode="area",
                sizeref=sizeref,
                sizemin=8,
                color=[cmap.get(m, "#888") for m in interval_clean["model_label"]],
                line=dict(width=1.2, color="rgba(255,255,255,0.55)"),
            ),
            hovertemplate=(
                "<b>%{hovertext}</b> — ◆ interval/workout<br>"
                "%{customdata[0]} · %{customdata[1]} work reps<br>"
                "Work GAP %{customdata[2]} · mean rep max-HR %{customdata[3]:.0f}<br>"
                "Gear: %{customdata[4]}<br>"
                "%{customdata[5]}<br>"
                "<i>click to open in Strava</i><extra></extra>"
            ),
        ))

    if not rep_drop.empty:
        # Their own trace (orange diamonds) → uncheck "Interval rep dropout" to
        # drop them entirely. These are runs whose work reps had impossible HR
        # (sensor drops the whole-run average/max hide).
        fig.add_trace(go.Scatter(
                x=rep_drop["work_gap_min_per_km"],
                y=rep_drop["work_maxhr_mean"],
                mode="markers",
                name="⚠ Interval rep dropout",
                hovertext=rep_drop["name"],
                customdata=rep_drop[[
                    "date", "n_work_reps", "work_gap_label", "work_maxhr_mean",
                    "interval_hr_reason", "id",
                ]].values,
                marker=dict(
                    symbol="diamond",
                    size=rep_drop["distance_km"],
                    sizemode="area",
                    sizeref=sizeref,
                    sizemin=8,
                    color="rgba(255,165,0,0.95)",
                    line=dict(width=1.5, color="rgba(120,70,0,0.9)"),
                ),
                hovertemplate=(
                    "<b>%{hovertext}</b> — ⚠ interval rep dropout<br>"
                    "%{customdata[0]} · %{customdata[1]} work reps<br>"
                    "Work GAP %{customdata[2]} · mean rep max-HR %{customdata[3]:.0f}<br>"
                    "Flagged: %{customdata[4]} · a work rep's HR is implausibly low<br>"
                    "<i>click to open in Strava</i><extra></extra>"
                ),
            ))

    footnote = (
        f"Minetti GAP from altitude+distance streams · "
        f"runs ≥ {payload.get('min_distance_km', 0)} km with HR · "
        f"point size ∝ distance · n={len(df)}"
    )
    if not suspect.empty:
        footnote += (
            f" · {len(suspect)} flagged low-HR "
            f"(wrist optical, pre-{hr_meta.get('wrist_optical_until', '?')})"
        )
    if not interval.empty:
        footnote += (
            f" · {len(interval_clean)} interval/workout ◆ at work-rep pace × mean "
            f"per-rep max-HR (rest laps removed)"
        )
        if not rep_drop.empty:
            footnote += f", + {len(rep_drop)} with rep-HR dropouts (orange)"
    footnote += " — uncheck any series in the legend to hide it"

    fig.update_layout(
        legend_title="Shoe model",
        template="plotly_dark",
        annotations=[
            dict(
                xref="paper", yref="paper", x=0, y=1.08, showarrow=False,
                text=footnote,
                font=dict(size=11, color="rgba(255,255,255,0.65)"),
            )
        ],
        margin=dict(l=70, r=30, t=110, b=70),
    )

    # Open the corresponding Strava activity in a new tab when a point is clicked.
    # The Strava activity id is the last entry of customdata per the array above.
    click_handler = """
    var gd = document.getElementById('{plot_id}');
    gd.style.cursor = 'pointer';
    gd.on('plotly_click', function(data) {
        var pt = data.points[0];
        if (!pt || !pt.customdata) return;
        var id = pt.customdata[pt.customdata.length - 1];
        if (id) window.open('https://www.strava.com/activities/' + id, '_blank');
    });
    """

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(
        str(OUTPUT_PATH),
        include_plotlyjs="cdn",
        full_html=True,
        post_script=click_handler,
    )
    print(f"Wrote {OUTPUT_PATH}", file=sys.stderr)


if __name__ == "__main__":
    main()
