#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["plotly>=5.20", "pandas>=2.0"]
# ///
"""Render the shoe-speed-vs-effort scatter from dataset.json.

Reads dataset.json (produced by build_dataset.py) and writes a self-contained
HTML file with a Plotly scatter plot: x = average HR, y = grade-adjusted pace,
color = shoe. Hover shows the per-run context.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = PROJECT_ROOT / "config" / "training.json"
DATASET_PATH = PROJECT_ROOT / ".cache" / "shoe-speed-vs-effort" / "dataset.json"
OUTPUT_PATH = PROJECT_ROOT / "viz" / "shoe-speed-vs-effort.html"

# Default distance-band cut points (km) when config doesn't set them.
DEFAULT_DISTANCE_CUTS = [12, 20, 35]

# In-browser controller for the drift-adjusted-HR build. Both dropdowns are
# method="skip" UI; this is the SOLE writer of x/y/customdata/marker, so the band
# filter and the HR-axis toggle compose (two static restyle menus would clobber
# each other's x). It never touches `visible`, so legend toggles on the hidden
# ⚠ series survive a filter change. Placeholders (__SHOE_DATA__ etc.) are filled
# by str.replace; `{plot_id}` is left for Plotly's own post_script substitution.
_DRIFT_CONTROLLER = """
    var gd = document.getElementById('{plot_id}');
    gd.style.cursor = 'pointer';
    var SHOE_DATA = __SHOE_DATA__;
    var BAND_LABELS = __BAND_LABELS__;
    var BANDS = __BANDS__;
    var X_TITLES = __X_TITLES__;
    var state = { bandIdx: 0, hrMode: 'raw' };

    function pickX(t) {
        if (state.hrMode === 'adj') {
            return t.xAdj.map(function(v, i) { return v == null ? t.xRaw[i] : v; });
        }
        return t.xRaw;
    }
    function applyState() {
        var lo = BANDS[state.bandIdx][0], hi = BANDS[state.bandIdx][1];
        var X = [], Y = [], CD = [], S = [], C = [];
        for (var ti = 0; ti < SHOE_DATA.length; ti++) {
            var t = SHOE_DATA[ti], xs = pickX(t), keep = [];
            for (var k = 0; k < t.dist.length; k++) {
                if (t.dist[k] > lo && t.dist[k] <= hi) keep.push(k);
            }
            X.push(keep.map(function(k) { return xs[k]; }));
            Y.push(keep.map(function(k) { return t.y[k]; }));
            CD.push(keep.map(function(k) { return t.cd[k]; }));
            S.push(Array.isArray(t.size) ? keep.map(function(k) { return t.size[k]; }) : t.size);
            C.push(Array.isArray(t.color) ? keep.map(function(k) { return t.color[k]; }) : t.color);
        }
        Plotly.restyle(gd, {x: X, y: Y, customdata: CD, 'marker.size': S, 'marker.color': C});
        Plotly.relayout(gd, {'xaxis.title.text': X_TITLES[state.hrMode]});
    }
    gd.on('plotly_buttonclicked', function(e) {
        var label = e.button.label;
        if (label === 'Raw HR') { state.hrMode = 'raw'; }
        else if (label === 'Drift-adjusted HR') { state.hrMode = 'adj'; }
        else { var idx = BAND_LABELS.indexOf(label); if (idx >= 0) state.bandIdx = idx; }
        applyState();
    });
    applyState();
    gd.on('plotly_click', function(data) {
        var pt = data.points[0];
        if (!pt || !pt.customdata) return;
        var id = pt.customdata[pt.customdata.length - 1];
        if (id) window.open('https://www.strava.com/activities/' + id, '_blank');
    });
"""


def pace_to_label(min_per_km: float) -> str:
    m = int(min_per_km)
    s = round((min_per_km - m) * 60)
    if s == 60:
        m, s = m + 1, 0
    return f"{m}:{s:02d}/km"


def build_distance_bands(cuts: list[float]) -> list[tuple]:
    """Turn a list of cut points into dropdown bands: (label, lo-excl, hi-incl) km.

    Cuts [12, 20, 35] → "All distances", "≤ 12 km", "12–20 km", "20–35 km", "> 35 km".
    "All distances" always leads so the chart opens unfiltered."""
    cuts = sorted(float(c) for c in cuts) if cuts else []
    bands = [("All distances", -1.0, 1e9)]
    prev = -1.0
    for c in cuts:
        label = f"≤ {c:g} km" if prev < 0 else f"{prev:g}–{c:g} km"
        bands.append((label, prev, c))
        prev = c
    if prev >= 0:
        bands.append((f"> {prev:g} km", prev, 1e9))
    return bands


def _is_array(v) -> bool:
    """True if a marker prop is per-point (a sequence) rather than a scalar."""
    return hasattr(v, "__len__") and not isinstance(v, str)


def _native(v):
    """Coerce numpy scalars to JSON-serialisable Python natives (no-op otherwise)."""
    return v.item() if hasattr(v, "item") else v


def build_trace_payload(fig, adj_by_id: dict) -> list[dict]:
    """Snapshot every trace's per-point arrays for the in-browser filter controller.

    The drift toggle and the distance filter must COMPOSE, which two static Plotly
    restyle menus can't do (each rebuilds x from scratch, clobbering the other). So
    instead of precomputing button payloads we hand the browser one uniform
    structure per trace and let a single JS controller own the restyle.

    Each entry mirrors what the old `distance_band_buttons` read off `fig.data`:
    dist (customdata[0], the band key), the raw x, y, full customdata rows, and the
    marker size/colour (array or scalar). It adds `xAdj` — the drift-adjusted x —
    looked up per point by the Strava id at customdata[-1], so a trace's HR mode can
    flip without touching its hovertemplate (which keeps reading the real measured
    HR from its existing customdata index). Heterogeneous trace layouts (steady /
    suspect / interval) need no special-casing because raw x is read straight off
    the trace and adj x is keyed by id.
    """
    payload = []
    for tr in fig.data:
        cd = [[_native(v) for v in row] for row in (tr.customdata if tr.customdata is not None else [])]
        ids = [row[-1] for row in cd]
        msize = tr.marker.size
        mcolor = tr.marker.color
        payload.append({
            "dist": [row[0] for row in cd],
            "xRaw": [_native(v) for v in (tr.x if tr.x is not None else [])],
            "xAdj": [adj_by_id.get(int(i)) if i is not None else None for i in ids],
            "y": [_native(v) for v in (tr.y if tr.y is not None else [])],
            "cd": cd,
            "size": [_native(v) for v in msize] if _is_array(msize) else msize,
            "color": [_native(v) for v in mcolor] if _is_array(mcolor) else mcolor,
        })
    return payload


def distance_band_buttons(fig, bands: list[tuple]) -> list[dict]:
    """Build native Plotly dropdown buttons that filter every trace to a distance
    band. Each point carries its distance at customdata[0], so for a band we keep
    the matching indices and emit a `restyle` that rebuilds x / y / customdata
    (and the per-point marker.size / marker.color arrays) for all traces at once.
    """
    buttons = []
    for label, lo, hi in bands:
        xs, ys, cds, sizes, colors = [], [], [], [], []
        for tr in fig.data:
            cd = list(tr.customdata) if tr.customdata is not None else []
            keep = [k for k, row in enumerate(cd) if lo < row[0] <= hi]
            xs.append([tr.x[k] for k in keep])
            ys.append([tr.y[k] for k in keep])
            cds.append([cd[k] for k in keep])
            msize = tr.marker.size
            sizes.append([msize[k] for k in keep] if _is_array(msize) else msize)
            mcolor = tr.marker.color
            colors.append([mcolor[k] for k in keep] if _is_array(mcolor) else mcolor)
        buttons.append(dict(
            label=label,
            method="restyle",
            args=[{"x": xs, "y": ys, "customdata": cds,
                   "marker.size": sizes, "marker.color": colors}],
        ))
    return buttons


def main() -> None:
    if not DATASET_PATH.exists():
        sys.exit(f"dataset not found at {DATASET_PATH} — run build_dataset.py first")

    payload = json.loads(DATASET_PATH.read_text())
    activities = payload.get("activities", [])
    if not activities:
        sys.exit("dataset has no activities")

    config = json.loads(CONFIG_PATH.read_text()) if CONFIG_PATH.exists() else {}
    cuts = (config.get("shoe_chart") or {}).get("distance_bands_km", DEFAULT_DISTANCE_CUTS)
    bands = build_distance_bands(cuts)

    # Cardiac-drift HR adjustment (build_dataset fits it from trusted runs). When
    # on, the chart gains a "HR axis: Raw / Drift-adjusted" toggle that composes
    # with the distance dropdown; when off (disabled or too few trusted runs) the
    # chart renders exactly as before, with no HR-axis control.
    hr_drift = payload.get("hr_drift") or {}
    drift_on = bool(hr_drift.get("enabled"))

    df = pd.DataFrame(activities)
    df["pace_label"] = df["avg_pace_min_per_km"].map(pace_to_label)
    df["gap_label"] = df["avg_gap_min_per_km"].map(pace_to_label)
    for col, default in (("hr_suspect", False), ("hr_suspect_reason", ""),
                         ("is_interval", False), ("interval_hr_suspect", False),
                         ("drift_clamped", False)):
        if col not in df.columns:
            df[col] = default
    # These flags are absent on rows they don't apply to → object dtype with NaN.
    # Cast to real bool so `~`/`&` do boolean (not bitwise-int) ops.
    for col in ("hr_suspect", "is_interval", "interval_hr_suspect", "drift_clamped"):
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
        x="avg_hr",
        y="avg_gap_min_per_km",
        color="model_label",
        color_discrete_map=cmap,
        size="distance_km",
        size_max=22,
        hover_name="name",
        # distance_km is kept at customdata[0] in EVERY trace so the distance-band
        # filter (see post_script) can read each point's distance uniformly; the
        # Strava id stays last for the click handler.
        custom_data=["distance_km", "date", "elev_gain_m", "pace_label", "gap_label", "avg_hr", "max_hr", "gear_label", "id"],
        title=f"Shoe speed vs. effort — last {payload.get('window_days', '?')} days",
    )
    fig.update_traces(
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "%{customdata[1]} · %{customdata[0]:.1f} km · +%{customdata[2]:.0f} m<br>"
            "Pace %{customdata[3]} · GAP %{customdata[4]}<br>"
            "HR avg %{customdata[5]:.0f} (max %{customdata[6]:.0f})<br>"
            "Gear: %{customdata[7]}<br>"
            "<i>click to open in Strava</i><extra></extra>"
        ),
        marker=dict(line=dict(width=0.5, color="rgba(255,255,255,0.35)")),
    )
    fig.update_xaxes(title="Average heart rate (bpm)")
    fig.update_yaxes(
        title="Grade-adjusted pace (min/km, faster ↑)",
        autorange="reversed",
    )

    # Match the overlay traces to the exact marker scale px computed for the
    # steady dots (same sizeref + sizemin), so a given distance renders at the
    # same size in every series — no inflated rings/diamonds.
    base_sizeref = next(
        (t.marker.sizeref for t in fig.data if getattr(t.marker, "sizeref", None)),
        2.0 * df_steady["distance_km"].max() / (22.0 ** 2),
    )
    base_sizemin = next(
        (t.marker.sizemin for t in fig.data if getattr(t.marker, "sizemin", None)),
        0,
    )

    # Flagged low-HR wrist-optical dropouts as their own trace (red rings),
    # hidden by default (visible="legendonly") — click the legend entry to show
    # them. Same marker scale as the steady dots so a distance reads the same size.
    suspect = df[df["hr_suspect"]]
    hr_meta = payload.get("hr_outliers", {})
    if not suspect.empty:
        fig.add_trace(go.Scatter(
            x=suspect["avg_hr"],
            y=suspect["avg_gap_min_per_km"],
            mode="markers",
            name="⚠ Suspect HR (wrist optical)",
            visible="legendonly",
            hovertext=suspect["name"],
            customdata=suspect[[
                "distance_km", "date", "elev_gain_m", "pace_label", "gap_label",
                "avg_hr", "max_hr", "gear_label", "hr_suspect_reason", "id",
            ]].values,
            marker=dict(
                symbol="circle-open",
                size=suspect["distance_km"],
                sizemode="area",
                sizeref=base_sizeref,
                sizemin=base_sizemin,
                color="rgba(255,80,80,0.95)",
                line=dict(width=2, color="rgba(255,80,80,0.95)"),
            ),
            hovertemplate=(
                "<b>%{hovertext}</b> — ⚠ suspect HR<br>"
                "%{customdata[1]} · %{customdata[0]:.1f} km · +%{customdata[2]:.0f} m<br>"
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
            x=interval_clean["work_maxhr_mean"],
            y=interval_clean["work_gap_min_per_km"],
            mode="markers",
            name="◆ Interval (work-rep)",
            hovertext=interval_clean["name"],
            customdata=interval_clean[[
                "distance_km", "date", "n_work_reps", "work_gap_label", "work_maxhr_mean",
                "gear_label", "description", "id",
            ]].values,
            marker=dict(
                symbol="diamond",
                size=interval_clean["distance_km"],
                sizemode="area",
                sizeref=base_sizeref,
                sizemin=base_sizemin,
                color=[cmap.get(m, "#888") for m in interval_clean["model_label"]],
                line=dict(width=1.2, color="rgba(255,255,255,0.55)"),
            ),
            hovertemplate=(
                "<b>%{hovertext}</b> — ◆ interval/workout<br>"
                "%{customdata[1]} · %{customdata[2]} work reps · %{customdata[0]:.1f} km<br>"
                "Work GAP %{customdata[3]} · mean rep max-HR %{customdata[4]:.0f}<br>"
                "Gear: %{customdata[5]}<br>"
                "%{customdata[6]}<br>"
                "<i>click to open in Strava</i><extra></extra>"
            ),
        ))

    if not rep_drop.empty:
        # Their own trace (orange diamonds) → uncheck "Interval rep dropout" to
        # drop them entirely. These are runs whose work reps had impossible HR
        # (sensor drops the whole-run average/max hide).
        fig.add_trace(go.Scatter(
                x=rep_drop["work_maxhr_mean"],
                y=rep_drop["work_gap_min_per_km"],
                mode="markers",
                name="⚠ Interval rep dropout",
                visible="legendonly",
                hovertext=rep_drop["name"],
                customdata=rep_drop[[
                    "distance_km", "date", "n_work_reps", "work_gap_label", "work_maxhr_mean",
                    "interval_hr_reason", "id",
                ]].values,
                marker=dict(
                    symbol="diamond",
                    size=rep_drop["distance_km"],
                    sizemode="area",
                    sizeref=base_sizeref,
                    sizemin=base_sizemin,
                    color="rgba(255,165,0,0.95)",
                    line=dict(width=1.5, color="rgba(120,70,0,0.9)"),
                ),
                hovertemplate=(
                    "<b>%{hovertext}</b> — ⚠ interval rep dropout<br>"
                    "%{customdata[1]} · %{customdata[2]} work reps · %{customdata[0]:.1f} km<br>"
                    "Work GAP %{customdata[3]} · mean rep max-HR %{customdata[4]:.0f}<br>"
                    "Flagged: %{customdata[5]} · a work rep's HR is implausibly low<br>"
                    "<i>click to open in Strava</i><extra></extra>"
                ),
            ))

    # Very subtle halo on runs longer than the drift fit's ceiling: their HR
    # adjustment was capped (we don't extrapolate the linear coefficient to a
    # 14-hour ultra), so they're under-corrected and out of the chart's regime —
    # and GAP can't capture an ultra's walking/terrain/fuelling cost anyway. A faint
    # open ring just outside the dot marks them without stealing the dot's hover
    # (hoverinfo skipped). Added before build_trace_payload so the controller filters
    # and HR-switches it with everything else; sits exactly on the underlying point.
    clamped = df[df["drift_clamped"]] if drift_on else df.iloc[0:0]
    if not clamped.empty:
        cx = clamped.apply(
            lambda r: r["work_maxhr_mean"] if r["is_interval"] else r["avg_hr"], axis=1)
        cy = clamped.apply(
            lambda r: r["work_gap_min_per_km"] if r["is_interval"] else r["avg_gap_min_per_km"],
            axis=1)
        fig.add_trace(go.Scatter(
            x=cx, y=cy, mode="markers",
            name="drift adj. capped (long run)",
            hoverinfo="skip",
            customdata=clamped[["distance_km", "id"]].values,
            marker=dict(
                symbol="circle-open",
                size=clamped["distance_km"] * 1.8,  # ~1.3× dot diameter → faint halo
                sizemode="area",
                sizeref=base_sizeref,
                sizemin=base_sizemin,
                color="rgba(220,220,220,0.28)",
                line=dict(width=1.0, color="rgba(220,220,220,0.28)"),
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
    footnote += " — flagged (⚠) series are hidden by default; click them in the legend to show"
    ref_min = hr_drift.get("ref_min")
    if drift_on:
        footnote += (
            f" · drift-adjusted HR available ({hr_drift.get('c_bpm_per_min'):+.2f} "
            f"bpm/min vs {ref_min:.0f}-min reference — toggle above)"
        )

    # The x-axis title travels with the toggle, so the axis label never lies about
    # which HR is plotted. Both strings are baked into the controller below.
    x_titles = {
        "raw": "Average heart rate (bpm)",
        "adj": f"Drift-adjusted HR (bpm, @ {ref_min:.0f}-min ref)" if drift_on else "",
    }

    annotations = [
        dict(
            xref="paper", yref="paper", x=0, y=1.10, showarrow=False,
            text=footnote,
            font=dict(size=11, color="rgba(255,255,255,0.65)"),
        ),
        dict(
            xref="paper", yref="paper", x=0, y=1.20, showarrow=False,
            text="Distance band:", xanchor="left",
            font=dict(size=12, color="rgba(255,255,255,0.85)"),
        ),
    ]
    _menu_style = dict(
        bgcolor="#2a2a2a", bordercolor="#666", font=dict(color="#eee", size=12),
    )

    if drift_on:
        # Both dropdowns are pure UI (method="skip"): a single JS controller owns
        # the restyle so the band filter and HR mode compose. The button order here
        # must match BAND_LABELS/BANDS handed to the controller.
        updatemenus = [
            dict(type="dropdown", direction="down", x=0.085, xanchor="left",
                 y=1.235, yanchor="top", showactive=True, active=0, **_menu_style,
                 buttons=[dict(label=b[0], method="skip", args=[]) for b in bands]),
            dict(type="dropdown", direction="down", x=0.40, xanchor="left",
                 y=1.235, yanchor="top", showactive=True, active=0, **_menu_style,
                 buttons=[dict(label="Raw HR", method="skip", args=[]),
                          dict(label="Drift-adjusted HR", method="skip", args=[])]),
        ]
        annotations.append(dict(
            xref="paper", yref="paper", x=0.40, y=1.20, showarrow=False,
            text="HR axis:", xanchor="left",
            font=dict(size=12, color="rgba(255,255,255,0.85)"),
        ))
    else:
        # No drift adjustment: keep the original static restyle dropdown.
        updatemenus = [dict(
            type="dropdown", direction="down", x=0.085, xanchor="left",
            y=1.235, yanchor="top", showactive=True, **_menu_style,
            buttons=distance_band_buttons(fig, bands),
        )]

    fig.update_layout(
        legend_title="Shoe model",
        template="plotly_dark",
        annotations=annotations,
        updatemenus=updatemenus,
        margin=dict(l=70, r=30, t=150, b=70),
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

    if drift_on:
        # Map each Strava id to its drift-adjusted x (intervals carry their own
        # adjusted work-rep value); the controller looks this up per point.
        adj_by_id: dict[int, float] = {}
        for _, r in df.iterrows():
            adj = r.get("work_maxhr_mean_adj") if r.get("is_interval") else r.get("avg_hr_adj")
            if pd.notna(adj):
                adj_by_id[int(r["id"])] = float(adj)
        shoe_data = build_trace_payload(fig, adj_by_id)
        post_script = (
            _DRIFT_CONTROLLER
            .replace("__SHOE_DATA__", json.dumps(shoe_data))
            .replace("__BAND_LABELS__", json.dumps([b[0] for b in bands]))
            .replace("__BANDS__", json.dumps([[b[1], b[2]] for b in bands]))
            .replace("__X_TITLES__", json.dumps(x_titles))
        )
    else:
        post_script = click_handler

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(
        str(OUTPUT_PATH),
        include_plotlyjs="cdn",
        full_html=True,
        post_script=post_script,
    )
    print(f"Wrote {OUTPUT_PATH}", file=sys.stderr)


if __name__ == "__main__":
    main()
