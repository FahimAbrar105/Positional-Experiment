import random
import time

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

from app.core.config import MODELS
from app.core.engine import run_trial
from app.core.storage import save_trial
from app.instruments.registry import INSTRUMENTS

load_dotenv()

st.set_page_config(page_title="Position Bias Pilot", layout="wide")

if "points" not in st.session_state:
    st.session_state.points = []          # accumulated trials for the current graph, across all instruments
if "shuffle_counter" not in st.session_state:
    st.session_state.shuffle_counter = 0  # so each shuffle click gets a fresh random permutation
if "is_running" not in st.session_state:
    st.session_state.is_running = False   # guards against a double-click firing two overlapping trials

st.title("LLM Position Bias Pilot")
st.caption(
    "Pick a test, pick a model, run it in original order, then shuffle and run again. "
    "Points accumulate on the graph below so you can see how far each model moves."
)

col_controls, col_graph = st.columns([1, 2], gap="large")

with col_controls:
    instrument_name = st.selectbox("Test type", list(INSTRUMENTS.keys()))
    instrument = INSTRUMENTS[instrument_name]

    model_choice = st.selectbox(
        "Model", MODELS, format_func=lambda m: m["label"]
    )

    condition_type = st.radio(
        "Item order",
        options=["baseline", "full_shuffle", "full_reversal"],
        format_func=lambda c: {
            "baseline": "Original order",
            "full_shuffle": "Shuffle (fully random)",
            "full_reversal": "Full reversal",
        }[c],
    )

    condition_label = "baseline"
    if condition_type == "full_shuffle":
        condition_label = f"shuffle #{st.session_state.shuffle_counter + 1}"
    elif condition_type == "full_reversal":
        condition_label = "full_reversal"

    run_clicked = st.button("Run trial", type="primary", use_container_width=True,
                             disabled=st.session_state.is_running)
    reset_clicked = st.button("Reset graph", use_container_width=True)

    if reset_clicked:
        st.session_state.points = []
        st.session_state.shuffle_counter = 0
        st.rerun()

    # The is_running guard (not just the button's disabled= state) is what actually
    # stops a double-click: a trial can take tens of seconds, and a second click
    # registered before the button visually greys out would otherwise fire a second,
    # overlapping call to the same model -- which is exactly what tripped a 429 on a
    # rate-limited free model in testing (two near-simultaneous requests where one
    # alone would have been fine).
    if run_clicked and not st.session_state.is_running:
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
            st.session_state.points.append({
                "model": model_choice["label"],
                "model_id": model_choice["id"],
                "instrument_name": instrument_name,
                "condition_type": trial.condition_type,
                "condition_label": trial.condition_label,
                "axes": dict(trial.score.axes),
                "axis_ranges": dict(trial.score.axis_ranges),
                "elapsed_seconds": round(trial.elapsed_seconds, 1),
                "timestamp": time.strftime("%H:%M:%S", time.localtime(trial.timestamp)),
            })
            if condition_type == "full_shuffle":
                st.session_state.shuffle_counter += 1
            summary = ", ".join(f"{k}={v:.2f}" for k, v in trial.score.axes.items())
            st.success(f"{model_choice['label']} ({trial.condition_label}): {summary}")

with col_graph:
    points = [p for p in st.session_state.points if p["instrument_name"] == instrument_name]
    if not points:
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
                # classic politicalcompass.org quadrant colors
                quadrants = [
                    (x_lo, 0, 0, y_hi, "rgba(239,148,148,0.55)", "Authoritarian Left", x_lo, y_hi, "left", "top"),
                    (0, x_hi, 0, y_hi, "rgba(120,190,225,0.55)", "Authoritarian Right", x_hi, y_hi, "right", "top"),
                    (x_lo, 0, y_lo, 0, "rgba(150,205,150,0.55)", "Libertarian Left", x_lo, y_lo, "left", "bottom"),
                    (0, x_hi, y_lo, 0, "rgba(205,170,215,0.55)", "Libertarian Right", x_hi, y_lo, "right", "bottom"),
                ]
                for x0, x1, y0, y1, color, label, lx, ly, xanchor, yanchor in quadrants:
                    fig.add_shape(type="rect", x0=x0, x1=x1, y0=y0, y1=y1,
                                  fillcolor=color, line_width=0, layer="below")
                    fig.add_annotation(x=lx, y=ly, text=label, showarrow=False,
                                       xanchor=xanchor, yanchor=yanchor,
                                       font=dict(color="rgba(0,0,0,0.55)", size=12),
                                       xshift=8 if xanchor == "left" else -8,
                                       yshift=-6 if yanchor == "top" else 6)
                fig.update_layout(plot_bgcolor="white")

            for p in points:
                fig.add_trace(go.Scatter(
                    x=[p["axes"][x_label]], y=[p["axes"][y_label]],
                    mode="markers+text",
                    name=p["model"],
                    legendgroup=p["model"],
                    showlegend=p["model"] not in [t.name for t in fig.data],
                    text=[p["condition_label"]],
                    textposition="top center",
                    textfont=dict(color=color_by_model[p["model"]]),
                    marker=dict(size=15, symbol=shape_by_condition.get(p["condition_type"], "circle"),
                                color=color_by_model[p["model"]],
                                line=dict(width=1.5, color="rgba(0,0,0,0.6)")),
                    hovertemplate=(f"{p['condition_label']}<br>{x_label}=%{{x:.2f}}<br>"
                                    f"{y_label}=%{{y:.2f}}<extra>{p['model']}</extra>"),
                ))
            fig.add_hline(y=0, line_width=1.5, line_color="black")
            fig.add_vline(x=0, line_width=1.5, line_color="black")
            fig.update_layout(
                xaxis_title=("Economic Left  ←  →  Economic Right" if is_compass else x_label),
                yaxis_title=("Libertarian  ←  →  Authoritarian" if is_compass else y_label),
                height=650, legend_title="Model",
            )
            if is_compass:
                fig.update_xaxes(range=[x_lo, x_hi], zeroline=False)
                fig.update_yaxes(range=[y_lo, y_hi], zeroline=False)
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
                polar=dict(radialaxis=dict(range=list(rng))),
                height=650,
                legend_title="Model (condition)",
            )

        st.plotly_chart(fig, use_container_width=True)

        table_rows = []
        for p in points:
            row = {"model": p["model"], "condition": p["condition_label"],
                   "elapsed_seconds": p["elapsed_seconds"], "timestamp": p["timestamp"]}
            row.update({f"{k}": round(v, 2) for k, v in p["axes"].items()})
            table_rows.append(row)
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True)

st.divider()
st.caption(
    "Every trial is also permanently logged to data/results/trials.csv, "
    "data/results/item_responses.csv (item-level, for the SD / mixed-effects analysis), "
    "and the model's exact raw reply under data/results/raw/ -- regardless of "
    "'Reset graph', which only clears this view."
)
