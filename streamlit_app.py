import json
import random
import time
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st
from dotenv import load_dotenv

from app.core.config import MODELS
from app.core.engine import run_trial
from app.core.storage import save_trial
from app.instruments.registry import INSTRUMENTS

load_dotenv()

st.set_page_config(page_title="Position Bias Pilot", layout="wide")

# Bigger UI text for presenting -- dropdowns, radio labels, buttons, and the
# results table are all normal DOM elements Streamlit renders, so plain CSS
# reaches them (unlike the plotly chart, which needs its own font settings
# below since it draws its own text on a canvas).
st.markdown(
    """
    <style>
    div[data-testid="stSelectbox"] input { font-size: 20px !important; }
    div[data-testid="stWidgetLabel"] p { font-size: 20px !important; }
    div[data-testid="stRadioOption"] label, div[data-testid="stRadioOption"] p { font-size: 20px !important; }
    div[data-testid="stButton"] button p { font-size: 20px !important; }
    [role="option"] { font-size: 20px !important; }
    div[data-testid="stTable"] table { font-size: 20px !important; }
    div[data-testid="stTable"] th, div[data-testid="stTable"] td { font-size: 20px !important; padding: 0.5rem 0.75rem !important; }
    div[data-testid="stAppDeployButton"] { display: none !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

CHART_FONT_SIZE = 18
LEGEND_FONT_SIZE = 20
TICK_FONT_SIZE = 16


# Saved results live in data/saved_results.json rather than data/results/
# (which is git-ignored, since it holds per-run trial logs) -- this file is
# meant to be committed, so anyone who clones the repository gets the saved
# demo trials immediately, with no API calls needed to reproduce them.
SAVED_RESULTS_PATH = Path("data/saved_results.json")


@st.cache_resource
def _saved_results_store() -> dict:
    # A live-demo fallback: if the API is slow or unresponsive mid-demo, switch
    # to previously-saved trials instead. Cached in memory for the life of the
    # process (avoids re-reading the file on every rerun), loaded from disk on
    # first access so it survives both restarts and a fresh clone of the repo.
    if SAVED_RESULTS_PATH.exists():
        try:
            return json.loads(SAVED_RESULTS_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _persist_saved_results(store: dict) -> None:
    SAVED_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SAVED_RESULTS_PATH.write_text(json.dumps(store, indent=2), encoding="utf-8")


if "points" not in st.session_state:
    st.session_state.points = []          # accumulated trials for the current graph, across all instruments
if "shuffle_counter" not in st.session_state:
    st.session_state.shuffle_counter = 0  # so each shuffle click gets a fresh random permutation
if "is_running" not in st.session_state:
    st.session_state.is_running = False   # guards against a double-click firing two overlapping trials
if "pending_save" not in st.session_state:
    st.session_state.pending_save = None  # the latest not-yet-saved trial (dict), or None
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "live"   # "live" | "saved"
if "last_result_summary" not in st.session_state:
    st.session_state.last_result_summary = None

st.title("LLM Position Bias Pilot")

col_controls, col_graph = st.columns([1, 2], gap="large")

with col_controls:
    saved_mode = st.session_state.view_mode == "saved"

    # Test type stays live even in saved-results mode -- it's how you browse
    # which test's saved data to look at. Everything else that could start a
    # new trial or touch session state is disabled while viewing saved data.
    instrument_name = st.selectbox("Test type", list(INSTRUMENTS.keys()))
    instrument = INSTRUMENTS[instrument_name]

    model_choice = st.selectbox(
        "Model", MODELS, format_func=lambda m: m["label"], disabled=saved_mode,
    )

    condition_type = st.radio(
        "Item order",
        options=["baseline", "full_shuffle", "full_reversal"],
        format_func=lambda c: {
            "baseline": "Original order",
            "full_shuffle": "Shuffle (fully random)",
            "full_reversal": "Full reversal",
        }[c],
        disabled=saved_mode,
    )

    condition_label = "baseline"
    if condition_type == "full_shuffle":
        condition_label = f"shuffle #{st.session_state.shuffle_counter + 1}"
    elif condition_type == "full_reversal":
        condition_label = "full_reversal"

    run_clicked = st.button("Run trial", type="primary", use_container_width=True,
                             disabled=st.session_state.is_running or saved_mode)
    # Reset graph only clears this session's live view (points + shuffle
    # counter) -- it never touches the saved-results store, and it's disabled
    # entirely in saved mode since there's nothing live to reset there.
    reset_clicked = st.button("Reset graph", use_container_width=True, disabled=saved_mode)

    pending = st.session_state.pending_save
    can_save = (not saved_mode) and pending is not None and pending["instrument_name"] == instrument_name
    save_clicked = st.button("Save results", use_container_width=True, disabled=not can_save)
    if can_save:
        st.caption(f"Ready to save: {pending['model']} ({pending['condition_label']})")

    toggle_label = "Go to real-time section" if saved_mode else "Check saved results"
    toggle_clicked = st.button(toggle_label, use_container_width=True)

    if toggle_clicked:
        st.session_state.view_mode = "live" if saved_mode else "saved"
        st.rerun()

    if reset_clicked:
        st.session_state.points = []
        st.session_state.shuffle_counter = 0
        st.session_state.pending_save = None
        st.session_state.last_result_summary = None
        st.rerun()

    if save_clicked and can_save:
        store = _saved_results_store()
        store.setdefault(instrument_name, []).append(pending)
        _persist_saved_results(store)
        st.session_state.pending_save = None
        st.rerun()

    if st.session_state.last_result_summary:
        st.success(st.session_state.last_result_summary)

    # The is_running guard (not just the button's disabled= state) is what actually
    # stops a double-click: a trial can take tens of seconds, and a second click
    # registered before the button visually greys out would otherwise fire a
    # second, overlapping call to the same model -- which can trip rate limits
    # on free-tier models even when a single request would have succeeded.
    if run_clicked and not st.session_state.is_running and not saved_mode:
        st.session_state.is_running = True
        rng = random.Random()
        trial = None
        try:
            with st.spinner(f"Querying {model_choice['label']} ({len(instrument.items)} items)..."):
                try:
                    trial = run_trial(
                        instrument=instrument,
                        model_entry=model_choice,
                        condition_type=condition_type,
                        condition_label=condition_label,
                        rng=rng,
                    )
                except Exception as e:
                    st.error(f"Trial failed: {e}")
        finally:
            st.session_state.is_running = False

        if trial is not None:
            save_trial(instrument, trial)
            point = {
                "model": model_choice["label"],
                "model_id": model_choice["id"],
                "instrument_name": instrument_name,
                "condition_type": trial.condition_type,
                "condition_label": trial.condition_label,
                "axes": dict(trial.score.axes),
                "axis_ranges": dict(trial.score.axis_ranges),
                "elapsed_seconds": round(trial.elapsed_seconds, 1),
                "timestamp": time.strftime("%H:%M:%S", time.localtime(trial.timestamp)),
            }
            st.session_state.points.append(point)
            # This is the one and only place pending_save gets set -- a fresh
            # successful run is what turns "Save results" pressable. Saving it
            # (or resetting the graph) is what turns it back off; running
            # again before saving just replaces which trial is queued to save.
            st.session_state.pending_save = point
            if condition_type == "full_shuffle":
                st.session_state.shuffle_counter += 1
            summary = ", ".join(f"{k}={v:.2f}" for k, v in trial.score.axes.items())
            st.session_state.last_result_summary = f"{model_choice['label']} ({trial.condition_label}): {summary}"
            # Rerun so "Save results" reflects the just-set pending_save on this
            # same round-trip -- otherwise its disabled= was already computed
            # earlier in this same script pass, using the stale (pre-trial)
            # value, and would only catch up on the *next* unrelated rerun.
            st.rerun()

with col_graph:
    if saved_mode:
        points = list(_saved_results_store().get(instrument_name, []))
    else:
        points = [p for p in st.session_state.points if p["instrument_name"] == instrument_name]

    if not points:
        if saved_mode:
            st.info("No saved results yet for this test. Go to the real-time section, run a "
                    "trial, and click **Save results**.")
        else:
            st.info("No trials yet for this test. Configure a run on the left and click **Run trial**.")
    else:
        axis_names = list(points[0]["axes"].keys())
        shape_by_condition = {"baseline": "star", "full_shuffle": "circle", "full_reversal": "diamond"}
        dash_by_condition = {"baseline": "solid", "full_shuffle": "dot", "full_reversal": "dash"}
        models_present = list(dict.fromkeys(p["model"] for p in points))
        palette = px.colors.qualitative.Plotly
        color_by_model = {m: palette[i % len(palette)] for i, m in enumerate(models_present)}

        fig = go.Figure()

        if len(axis_names) == 2:
            x_label, y_label = axis_names
            is_compass = instrument_name == "Political Compass Test"

            if is_compass:
                x_lo, x_hi = points[0]["axis_ranges"][x_label]
                y_lo, y_hi = points[0]["axis_ranges"][y_label]
                # Quadrant geometry only (labels + divider lines) -- no fill
                # color, so this matches the transparent, theme-adaptive
                # background every other chart in this app uses (bgcolor=
                # "rgba(0,0,0,0)" below) instead of a hardcoded white plot area.
                # Label color is a neutral mid-gray, not black/white, so it
                # reads on both a light and a dark Streamlit theme.
                quadrants = [
                    ("Authoritarian Left", x_lo, y_hi, "left", "top"),
                    ("Authoritarian Right", x_hi, y_hi, "right", "top"),
                    ("Libertarian Left", x_lo, y_lo, "left", "bottom"),
                    ("Libertarian Right", x_hi, y_lo, "right", "bottom"),
                ]
                for label, lx, ly, xanchor, yanchor in quadrants:
                    fig.add_annotation(x=lx, y=ly, text=label, showarrow=False,
                                       xanchor=xanchor, yanchor=yanchor,
                                       font=dict(color="rgba(128,128,128,0.9)", size=18),
                                       xshift=8 if xanchor == "left" else -8,
                                       yshift=-6 if yanchor == "top" else 6)
                fig.update_layout(plot_bgcolor="rgba(0,0,0,0)")

            for p in points:
                fig.add_trace(go.Scatter(
                    x=[p["axes"][x_label]], y=[p["axes"][y_label]],
                    mode="markers+text",
                    name=p["model"],
                    legendgroup=p["model"],
                    showlegend=p["model"] not in [t.name for t in fig.data],
                    text=[p["condition_label"]],
                    textposition="top center",
                    textfont=dict(color=color_by_model[p["model"]], size=TICK_FONT_SIZE),
                    marker=dict(size=15, symbol=shape_by_condition.get(p["condition_type"], "circle"),
                                color=color_by_model[p["model"]],
                                line=dict(width=1.5, color="rgba(128,128,128,0.8)")),
                    hovertemplate=(f"{p['condition_label']}<br>{x_label}=%{{x:.2f}}<br>"
                                    f"{y_label}=%{{y:.2f}}<extra>{p['model']}</extra>"),
                ))
            # neutral gray, not black -- a black divider line nearly vanishes
            # against a dark Streamlit theme's background.
            fig.add_hline(y=0, line_width=1.5, line_color="rgba(128,128,128,0.6)")
            fig.add_vline(x=0, line_width=1.5, line_color="rgba(128,128,128,0.6)")
            fig.update_layout(
                xaxis_title=("Economic Left  ←  →  Economic Right" if is_compass else x_label),
                yaxis_title=("Libertarian  ←  →  Authoritarian" if is_compass else y_label),
                height=650, legend_title="Model",
                font=dict(size=CHART_FONT_SIZE),
                # legend below the chart, not to its right -- a right-side legend
                # steals horizontal space from the plot itself and, combined with
                # the larger presentation font, was pushing the compass/scatter
                # over and clipping its own labels.
                legend=dict(
                    font=dict(size=LEGEND_FONT_SIZE),
                    orientation="h",
                    yanchor="top", y=-0.15,
                    xanchor="center", x=0.5,
                ),
                margin=dict(b=100),
                xaxis=dict(title_font=dict(size=CHART_FONT_SIZE), tickfont=dict(size=TICK_FONT_SIZE)),
                yaxis=dict(title_font=dict(size=CHART_FONT_SIZE), tickfont=dict(size=TICK_FONT_SIZE)),
            )
            if is_compass:
                fig.update_xaxes(range=[x_lo, x_hi], zeroline=False)
                fig.update_yaxes(range=[y_lo, y_hi], zeroline=False)
        elif instrument_name == "Self-Reported Political Dimensions (SRPD)":
            # SRPD's 12 axes mix two different kinds of quantity -- "Position" axes
            # (where do you stand on a policy) and "Salience/Clarity" axes (how much
            # you care / how settled your view is). These are scored as separate
            # blocks precisely so they aren't conflated (see srpd.py); plotting them
            # as spokes on one shared radar would reintroduce that same
            # apples-to-oranges comparison visually, just one layer up. So each is
            # its own radar instead.
            def _srpd_group(axis_name: str) -> str:
                return "salience" if ("Salience/Clarity" in axis_name or axis_name == "European Integration") else "position"

            position_axes = [a for a in axis_names if _srpd_group(a) == "position"]
            salience_axes = [a for a in axis_names if _srpd_group(a) == "salience"]

            # Stacked (one above the other), not side-by-side: two polar charts
            # sharing one row have to split the container's width between them,
            # and with 6 verbose axis names each ("Economic Left-Right (LRECON)
            # -- Salience/Clarity"), that leaves too little room for the labels
            # to stay legible at the app's normal width. Stacked, each radar
            # gets the full container width to itself.
            fig = make_subplots(
                rows=2, cols=1,
                specs=[[{"type": "polar"}], [{"type": "polar"}]],
                subplot_titles=("<b>Position (policy stances)</b>", "<b>Salience / Clarity</b>"),
                vertical_spacing=0.18,
            )
            rng = points[0]["axis_ranges"][axis_names[0]]
            for group_axes, row in [(position_axes, 1), (salience_axes, 2)]:
                # split each label at its own " -- " so long axis names wrap
                # onto two lines instead of overflowing.
                categories = [c.replace(" -- ", "<br>") for c in group_axes]
                categories.append(categories[0])
                for p in points:
                    r = [p["axes"][a] for a in group_axes] + [p["axes"][group_axes[0]]]
                    fig.add_trace(
                        go.Scatterpolar(
                            r=r, theta=categories,
                            mode="lines+markers",
                            name=f"{p['model']} ({p['condition_label']})",
                            legendgroup=p["model"],
                            showlegend=(row == 1),
                            line=dict(color=color_by_model[p["model"]], dash=dash_by_condition.get(p["condition_type"], "solid")),
                            opacity=0.85,
                            hovertemplate="%{theta}=%{r:.2f}<extra>" + f"{p['model']} ({p['condition_label']})" + "</extra>",
                        ),
                        row=row, col=1,
                    )
            fig.update_polars(
                radialaxis=dict(range=list(rng), tickfont=dict(size=TICK_FONT_SIZE)),
                angularaxis=dict(tickfont=dict(size=TICK_FONT_SIZE)),
                bgcolor="rgba(0,0,0,0)",
            )
            # the two subplot titles -- bigger, bold, and pushed further above
            # the plot (yshift) than the default, so they read as headings
            # rather than blending into the topmost angular-axis labels right
            # below them.
            fig.update_annotations(font_size=CHART_FONT_SIZE + 4, yshift=15)
            fig.update_layout(
                height=1300, legend_title="Model (condition)",
                font=dict(size=CHART_FONT_SIZE),
                legend=dict(
                    font=dict(size=LEGEND_FONT_SIZE),
                    orientation="h",
                    yanchor="top",
                    y=-0.06,
                    xanchor="center",
                    x=0.5
                ),
                margin=dict(l=160, r=160, t=60, b=100),
            )
        else:
            categories = axis_names + [axis_names[0]]
            for p in points:
                r = [p["axes"][a] for a in axis_names] + [p["axes"][axis_names[0]]]
                fig.add_trace(go.Scatterpolar(
                    r=r, theta=categories,
                    mode="lines+markers",
                    name=f"{p['model']} ({p['condition_label']})",
                    legendgroup=p["model"],
                    line=dict(color=color_by_model[p["model"]], dash=dash_by_condition.get(p["condition_type"], "solid")),
                    opacity=0.85,
                    hovertemplate="%{theta}=%{r:.2f}<extra>" + f"{p['model']} ({p['condition_label']})" + "</extra>",
                ))
            rng = points[0]["axis_ranges"][axis_names[0]]
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(range=list(rng), tickfont=dict(size=TICK_FONT_SIZE)),
                    angularaxis=dict(tickfont=dict(size=TICK_FONT_SIZE)),
                    bgcolor="rgba(0,0,0,0)",
                ),
                height=650,
                legend_title="Model (condition)",
                font=dict(size=CHART_FONT_SIZE),
                # bottom, not right -- a right-side legend competes with the polar
                # chart for width and was pushing the whole circle left, clipping
                # its own angular-axis labels on that side.
                legend=dict(
                    font=dict(size=LEGEND_FONT_SIZE),
                    orientation="h",
                    yanchor="top", y=-0.15,
                    xanchor="center", x=0.5,
                ),
                margin=dict(b=100),
            )

        st.plotly_chart(fig, use_container_width=True)
        # The chart's own bottom margin makes room for its legend, but Streamlit
        # butts the next element right up against the chart's outer box below
        # that -- so the legend text and the table header end up almost
        # touching. A explicit spacer here fixes that for all 6 tests at once,
        # since every branch above ends up rendering through this same point.
        st.markdown("<div style='height:2.5rem'></div>", unsafe_allow_html=True)

        table_rows = []
        for p in points:
            row = {"model": p["model"], "condition": p["condition_label"],
                   "elapsed_seconds": p["elapsed_seconds"], "timestamp": p["timestamp"]}
            row.update({f"{k}": round(v, 2) for k, v in p["axes"].items()})
            table_rows.append(row)
        st.table(pd.DataFrame(table_rows))

        # ---- "Change from baseline", zoomed to the actual shift ----
        # The chart above uses each instrument's fixed scale (e.g. 1-5, -10 to
        # 10), so a real shift between conditions can look flat. This one is
        # scaled to whatever difference was actually observed, per model, so
        # that shift is legible -- it complements the chart above rather than
        # replacing it (that one is still what shows absolute position).
        st.markdown("<div style='height:2.5rem'></div>", unsafe_allow_html=True)
        st.subheader("Change from Baseline")

        baselines = {p["model"]: p for p in points if p["condition_type"] == "baseline"}
        non_baseline_in_scope = [p for p in points if p["condition_type"] != "baseline" and p["model"] in baselines]
        deltas_list = [
            {
                "model": p["model"],
                "condition_label": p["condition_label"],
                "condition_type": p["condition_type"],
                "deltas": {a: p["axes"][a] - baselines[p["model"]]["axes"][a] for a in axis_names},
            }
            for p in non_baseline_in_scope
        ]

        if not deltas_list:
            st.info("Run a baseline trial plus a shuffle/reversal trial for the same "
                    "model to see the amplified change-from-baseline view.")
        elif len(axis_names) == 2 and instrument_name == "Political Compass Test":
            # A 2D position is already spatial -- zooming the same x/y axes in
            # around the actual cluster of points amplifies the shift without
            # needing to convert anything to a delta.
            bx_label, by_label = axis_names
            all_x = [b["axes"][bx_label] for b in baselines.values()] + [p["axes"][bx_label] for p in non_baseline_in_scope]
            all_y = [b["axes"][by_label] for b in baselines.values()] + [p["axes"][by_label] for p in non_baseline_in_scope]
            pad_x = max((max(all_x) - min(all_x)) * 0.3, 0.5)
            pad_y = max((max(all_y) - min(all_y)) * 0.3, 0.5)
            x_lo, x_hi = min(all_x) - pad_x, max(all_x) + pad_x
            y_lo, y_hi = min(all_y) - pad_y, max(all_y) + pad_y

            dfig = go.Figure()
            for p in [b for b in baselines.values()] + non_baseline_in_scope:
                dfig.add_trace(go.Scatter(
                    x=[p["axes"][bx_label]], y=[p["axes"][by_label]],
                    mode="markers+text",
                    name=p["model"],
                    legendgroup=p["model"],
                    showlegend=p["model"] not in [t.name for t in dfig.data],
                    text=[p["condition_label"]],
                    textposition="top center",
                    textfont=dict(color=color_by_model[p["model"]], size=TICK_FONT_SIZE),
                    marker=dict(size=16, symbol=shape_by_condition.get(p["condition_type"], "circle"),
                                color=color_by_model[p["model"]],
                                line=dict(width=1.5, color="rgba(128,128,128,0.8)")),
                    hovertemplate=(f"{p['condition_label']}<br>{bx_label}=%{{x:.2f}}<br>"
                                    f"{by_label}=%{{y:.2f}}<extra>{p['model']}</extra>"),
                ))
            if x_lo <= 0 <= x_hi:
                dfig.add_vline(x=0, line_width=1.5, line_color="rgba(128,128,128,0.6)")
            if y_lo <= 0 <= y_hi:
                dfig.add_hline(y=0, line_width=1.5, line_color="rgba(128,128,128,0.6)")
            dfig.update_layout(
                xaxis_title=f"{bx_label} (zoomed)",
                yaxis_title=f"{by_label} (zoomed)",
                height=550,
                font=dict(size=CHART_FONT_SIZE),
                legend=dict(font=dict(size=LEGEND_FONT_SIZE), orientation="h",
                            yanchor="top", y=-0.22, xanchor="center", x=0.5),
                margin=dict(b=100),
                xaxis=dict(range=[x_lo, x_hi], title_font=dict(size=CHART_FONT_SIZE), tickfont=dict(size=TICK_FONT_SIZE)),
                yaxis=dict(range=[y_lo, y_hi], title_font=dict(size=CHART_FONT_SIZE), tickfont=dict(size=TICK_FONT_SIZE)),
            )
            st.plotly_chart(dfig, use_container_width=True)
        else:
            # A radar can't show a negative delta cleanly -- a negative radius
            # plots on the opposite angle, which would misread as a different
            # axis moving rather than this one moving down. A diverging
            # horizontal bar per axis has no such ambiguity, and its own axis
            # auto-scales to whatever shift was actually observed. Works
            # uniformly for 3 axes (SD3) through 12 (SRPD) with no special-casing.
            all_deltas = [v for d in deltas_list for v in d["deltas"].values()]
            max_abs = max(abs(v) for v in all_deltas) or 1.0
            pad = max_abs * 0.2
            dfig = go.Figure()
            for d in deltas_list:
                dfig.add_trace(go.Bar(
                    y=axis_names,
                    x=[d["deltas"][a] for a in axis_names],
                    orientation="h",
                    name=f"{d['model']} ({d['condition_label']})",
                    # Plotly only auto-shows a legend with 2+ traces; a single
                    # saved condition (just one model, one non-baseline run)
                    # would otherwise render with no legend at all.
                    showlegend=True,
                    marker=dict(color=color_by_model[d["model"]]),
                    hovertemplate="%{y}: %{x:+.2f}<extra>" + f"{d['model']} ({d['condition_label']})" + "</extra>",
                ))
            dfig.add_vline(x=0, line_width=1.5, line_color="rgba(128,128,128,0.6)")
            dfig.update_layout(
                barmode="group",
                height=max(450, 55 * len(axis_names)),
                font=dict(size=CHART_FONT_SIZE),
                xaxis=dict(title="Change from baseline", range=[-max_abs - pad, max_abs + pad],
                           title_font=dict(size=CHART_FONT_SIZE), tickfont=dict(size=TICK_FONT_SIZE)),
                yaxis=dict(tickfont=dict(size=TICK_FONT_SIZE), automargin=True),
                # Default (right-side, vertical) legend here -- unlike the
                # circular/square radar and compass charts, a wide rectangular
                # bar chart doesn't lose meaningful plot area to a right-side
                # legend, so there's no need to force it below the axis.
                legend=dict(font=dict(size=LEGEND_FONT_SIZE)),
                margin=dict(l=10, r=10, t=20, b=60),
            )
            st.plotly_chart(dfig, use_container_width=True)
