import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Gorton on a page (overview)",
    layout="wide",
)

METRICS = ["CLC", "TT", "PSED", "F", "PD", "Pre-school"]
TARGETS = {
    "CLC": 80,
    "TT": 85,
    "PSED": 78,
    "F": 82,
    "PD": 80,
    "Pre-school": 75,
}

# Deliberately small, reproducible demo data for the prototype.
DATA = [
    ["Gorton", 76, 82, 79, 84, 81, 68],
    ["Ardwick", 72, 79, 75, 80, 77, 63],
    ["Longsight", 81, 86, 82, 85, 83, 74],
    ["Levenshulme", 78, 84, 80, 79, 80, 71],
    ["Moss Side", 69, 77, 73, 76, 74, 59],
    ["Rusholme", 83, 88, 85, 87, 86, 78],
]
df = pd.DataFrame(DATA, columns=["Ward"] + METRICS).set_index("Ward")


def validate_data(frame):
    """Run cheap integrity checks so a malformed prototype fails clearly."""
    assert list(frame.columns) == METRICS
    assert "Gorton" in frame.index
    assert frame.index.is_unique
    assert frame[METRICS].apply(lambda column: column.between(0, 100).all()).all()


def metric_summary(metric, selected_wards):
    gorton_value = df.loc["Gorton", metric]
    comparison = df.loc[selected_wards, metric]
    average = comparison.mean()
    target = TARGETS[metric]
    target_word = "above" if gorton_value >= target else "below"
    difference = gorton_value - average
    comparison_word = "above" if difference >= 0 else "below"
    return (
        f"{metric} is {gorton_value}% ({target_word} the {target}% target), "
        f"{abs(difference):.1f} points {comparison_word} the comparison average."
    )


def build_key_messages(selected_wards):
    """Create four concise, data-driven messages covering every metric."""
    summaries = {metric: metric_summary(metric, selected_wards) for metric in METRICS}
    target_met = [metric for metric in METRICS if df.loc["Gorton", metric] >= TARGETS[metric]]
    target_missed = [metric for metric in METRICS if metric not in target_met]
    differences = (df.loc["Gorton", METRICS] - df.loc[selected_wards, METRICS].mean()).sort_values(ascending=False)
    strongest = differences.index[0]
    weakest = differences.index[-1]
    best_metric = df.loc["Gorton", METRICS].idxmax()
    return [
        f"Gorton meets {len(target_met)} of {len(METRICS)} bespoke targets: {', '.join(target_met) or 'none'}.",
        f"Target watchlist: {', '.join(target_missed) or 'none'}; {summaries[target_missed[0]] if target_missed else 'all metrics are on target.'}",
        f"Against the selected wards, Gorton is strongest on {strongest} (+{differences[strongest]:.1f} points) and has the largest gap on {weakest} ({differences[weakest]:+.1f} points).",
        f"Gorton's highest result is {best_metric} at {df.loc['Gorton', best_metric]}%. " + " ".join(summaries[metric] for metric in METRICS if metric != best_metric),
    ]


validate_data(df)
if "comparison_wards" not in st.session_state:
    st.session_state.comparison_wards = ["Longsight", "Levenshulme"]

st.markdown("<style>h1 { color: #12343b; letter-spacing: 0; } .block-container { padding-top: 2rem; }</style>", unsafe_allow_html=True)
st.title("Gorton on a page (overview) - high-level")
st.caption("A compact view of performance against nearby wards and bespoke thresholds.")

available_wards = [ward for ward in df.index if ward != "Gorton"]
selected_wards = st.multiselect(
    "Comparison wards",
    options=available_wards,
    default=st.session_state.comparison_wards,
    help="Gorton is always included as the primary ward.",
)
if not selected_wards:
    selected_wards = [available_wards[0]]
    st.info(f"Showing Gorton against {selected_wards[0]} until another comparison ward is selected.")
st.session_state.comparison_wards = selected_wards

chart_wards = ["Gorton"] + selected_wards
colors = {"Gorton": "#e4572e"}
colors.update({ward: "#2a9d8f" for ward in selected_wards})


def make_chart(metric):
    figure = go.Figure()
    for ward in chart_wards:
        figure.add_trace(go.Bar(
            name=ward,
            x=[ward],
            y=[df.loc[ward, metric]],
            marker_color=colors[ward],
            text=[f"{df.loc[ward, metric]}%"],
            textposition="outside",
            hovertemplate=f"{ward}: %{{y}}%<extra></extra>",
        ))
    figure.add_hline(
        y=TARGETS[metric],
        line_dash="dot",
        line_color="#f2a541",
        annotation_text=f"Target {TARGETS[metric]}%",
        annotation_position="top left",
    )
    figure.update_layout(
        title={"text": metric, "x": 0.02, "xanchor": "left", "font": {"size": 18, "color": "#12343b"}},
        barmode="group",
        height=300,
        margin={"l": 12, "r": 12, "t": 52, "b": 35},
        yaxis={"range": [0, 105], "ticksuffix": "%", "gridcolor": "#e5e7e9", "title": None},
        xaxis={"title": None},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="white",
        legend={"orientation": "h", "y": -0.18},
        font={"family": "sans-serif", "color": "#334e52"},
    )
    return figure


st.subheader("Performance by metric")
chart_columns = st.columns(2)
for index, metric in enumerate(METRICS):
    with chart_columns[index % 2]:
        st.plotly_chart(make_chart(metric), use_container_width=True, config={"displayModeBar": False})

st.subheader("Key messages (inc. comparisons)")
for message in build_key_messages(selected_wards):
    st.markdown(f"- {message}")
