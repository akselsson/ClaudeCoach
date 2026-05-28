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

    fig = px.scatter(
        df,
        x="avg_gap_min_per_km",
        y="avg_hr",
        color="model_label",
        color_discrete_sequence=px.colors.qualitative.Light24,
        size="distance_km",
        size_max=22,
        hover_name="name",
        custom_data=["date", "distance_km", "elev_gain_m", "pace_label", "gap_label", "avg_hr", "max_hr", "gear_label"],
        title=f"Shoe speed vs. effort — last {payload.get('window_days', '?')} days",
    )
    fig.update_traces(
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "%{customdata[0]} · %{customdata[1]:.1f} km · +%{customdata[2]:.0f} m<br>"
            "Pace %{customdata[3]} · GAP %{customdata[4]}<br>"
            "HR avg %{customdata[5]:.0f} (max %{customdata[6]:.0f})<br>"
            "Gear: %{customdata[7]}<extra></extra>"
        ),
        marker=dict(line=dict(width=0.5, color="rgba(255,255,255,0.35)")),
    )
    fig.update_xaxes(
        title="Grade-adjusted pace (min/km, faster →)",
        autorange="reversed",
    )
    fig.update_yaxes(title="Average heart rate (bpm)")
    fig.update_layout(
        legend_title="Shoe model",
        template="plotly_dark",
        annotations=[
            dict(
                xref="paper", yref="paper", x=0, y=1.08, showarrow=False,
                text=(
                    f"Minetti GAP from altitude+distance streams · "
                    f"runs ≥ {payload.get('min_distance_km', 0)} km with HR · "
                    f"point size ∝ distance · n={len(df)}"
                ),
                font=dict(size=11, color="rgba(255,255,255,0.65)"),
            )
        ],
        margin=dict(l=70, r=30, t=110, b=70),
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(OUTPUT_PATH), include_plotlyjs="cdn", full_html=True)
    print(f"Wrote {OUTPUT_PATH}", file=sys.stderr)


if __name__ == "__main__":
    main()
