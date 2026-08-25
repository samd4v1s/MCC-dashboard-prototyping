import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from html import escape

TLG_COLOURS = {
    "background": "#faf7f8",
    "text": "#313130",
    "lines": ["#1a2792", "#ffb7ff", "#c7ef00", "#f7574b", "#21fa90", "#7f96ff"],
}

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


BREAKDOWN_COLUMNS = pd.MultiIndex.from_tuples([
    ("CLL", "LA"),
    ("CLL", "S"),
    ("PSE", "SR"),
    ("PSE", "MS"),
    ("PSE", "BR"),
    ("PD", "GM"),
    ("PD", "FM"),
])
BREAKDOWN_DATA = pd.DataFrame(
    [
        ["58%", "61%", "70%", "73%", "68%", "76%", "72%"],
        ["64%", "67%", "75%", "78%", "74%", "80%", "77%"],
        ["55%", "59%", "62%", "65%", "60%", "69%", "66%"],
        ["49%", "53%", "57%", "60%", "55%", "63%", "61%"],
        ["71%", "74%", "79%", "82%", "77%", "85%", "83%"],
    ],
    index=["Boy", "Girl", "EAL", "SEND", "NAT %"],
    columns=BREAKDOWN_COLUMNS,
)


def validate_breakdown(frame):
    assert list(frame.index) == ["Boy", "Girl", "EAL", "SEND", "NAT %"]
    assert frame.columns.equals(BREAKDOWN_COLUMNS)
    assert frame.map(lambda value: isinstance(value, str) and value.endswith("%")).all().all()


def build_breakdown_summary(frame):
    """Explain the table using calculated values rather than fixed prose."""
    boy_cll_la = int(frame.loc["Boy", ("CLL", "LA")].rstrip("%"))
    girl_cll_la = int(frame.loc["Girl", ("CLL", "LA")].rstrip("%"))
    gender_gap = girl_cll_la - boy_cll_la
    direction = "higher" if gender_gap > 0 else "lower" if gender_gap < 0 else "the same as"
    gap_text = f"{abs(gender_gap)} percentage points {direction} than Boys"
    group_averages = frame.apply(lambda column: column.str.rstrip("%").astype(float).mean())
    strongest_metric = group_averages.idxmax()
    strongest_value = group_averages[strongest_metric]
    return (
        f"For CLL - LA, Girls are at {girl_cll_la}% and Boys are at {boy_cll_la}%, "
        f"so Girls are {gap_text}. Across all five groups, the strongest average "
        f"result is {strongest_metric[0]} - {strongest_metric[1]} at {strongest_value:.1f}%."
    )


TRAFFIC_LIGHT_STYLES = {
    "red": "background-color:#f8d7da; color:#842029;",
    "amber": "background-color:#fff3cd; color:#664d03;",
    "green": "background-color:#d1e7dd; color:#0f5132;",
}


def traffic_light(value):
    percentage = int(str(value).rstrip("%"))
    if percentage < 60:
        return "red"
    if percentage < 75:
        return "amber"
    return "green"


def render_breakdown_table(frame):
    """Render the MultiIndex as a table with merged parent headers."""
    parent_headers = []
    start = 0
    for column_index, (parent, _) in enumerate(frame.columns):
        if column_index == 0 or parent != frame.columns[column_index - 1][0]:
            if column_index:
                parent_headers[-1]["colspan"] = column_index - start
            parent_headers.append({"label": parent, "colspan": 1})
            start = column_index
    parent_headers[-1]["colspan"] = len(frame.columns) - start

    header_html = "".join(
        f'<th colspan="{header["colspan"]}">{escape(header["label"])}</th>'
        for header in parent_headers
    )
    subheader_html = "".join(f"<th>{escape(subcategory)}</th>" for _, subcategory in frame.columns)
    rows_html = "".join(
        "<tr>"
        f'<th scope="row">{escape(str(index))}</th>'
        + "".join(
            f'<td style="{TRAFFIC_LIGHT_STYLES[traffic_light(value)]} font-weight:600;">'
            f"{escape(str(value))}</td>"
            for value in values
        )
        + "</tr>"
        for index, values in frame.iterrows()
    )
    return (
        '<table style="width:100%; border-collapse:collapse; text-align:center;">'
        '<thead><tr><th rowspan="2" style="text-align:left; padding:8px;">Group</th>'
        f"{header_html}</tr><tr>{subheader_html}</tr></thead>"
        f"<tbody>{rows_html}</tbody></table>"
    )


def render_traffic_light_key():
    key_items = [
        ("red", "Below 60%"),
        ("amber", "60% to 74%"),
        ("green", "75% or above"),
    ]
    return "<div style='display:flex; gap:18px; flex-wrap:wrap; margin:12px 0 4px;'>" + "".join(
        f'<span><span style="display:inline-block; width:13px; height:13px; '
        f'border-radius:50%; background:{style.split(";")[0].split(":")[1]}; '
        f'margin-right:6px; vertical-align:-1px;"></span>{label}</span>'
        for colour, label in key_items
        for style in [TRAFFIC_LIGHT_STYLES[colour]]
    ) + "</div>"


EYFS_DATA = {
    "manchester": {
        "areas": {
            "Gorton": {
                "metrics": {"Communication": 72, "Physical": 78, "PSED": 74, "Literacy": 69},
                "schools": {
                    "St. James": {"Communication": 76, "Physical": 81, "PSED": 79, "Literacy": 72, "Pre School Ready": 74, "Toilet Trained": 82, "Feed Independently": 87},
                    "Gorton South Primary": {"Communication": 68, "Physical": 75, "PSED": 70, "Literacy": 66, "Pre School Ready": 71, "Toilet Trained": 78, "Feed Independently": 84},
                },
            },
            "Ardwick": {
                "metrics": {"Communication": 67, "Physical": 73, "PSED": 70, "Literacy": 64},
                "schools": {
                    "Ardwick Green": {"Communication": 70, "Physical": 76, "PSED": 72, "Literacy": 67, "Pre School Ready": 69, "Toilet Trained": 75, "Feed Independently": 81},
                },
            },
            "Longsight": {
                "metrics": {"Communication": 81, "Physical": 84, "PSED": 82, "Literacy": 78},
                "schools": {
                    "St. Edmunds": {"Communication": 83, "Physical": 86, "PSED": 84, "Literacy": 80, "Pre School Ready": 79, "Toilet Trained": 88, "Feed Independently": 91},
                },
            },
            "Levenshulme": {
                "metrics": {"Communication": 76, "Physical": 80, "PSED": 78, "Literacy": 74},
                "schools": {
                    "Levenshulme Primary": {"Communication": 78, "Physical": 82, "PSED": 80, "Literacy": 75, "Pre School Ready": 76, "Toilet Trained": 84, "Feed Independently": 89},
                },
            },
        },
    },
}
EYFS_AREA_METRICS = ["Communication", "Physical", "PSED", "Literacy"]
EYFS_SCHOOL_METRICS = EYFS_AREA_METRICS + ["Pre School Ready", "Toilet Trained", "Feed Independently"]


def validate_eyfs_data(data):
    assert "manchester" in data
    assert data["manchester"]["areas"]
    for area in data["manchester"]["areas"].values():
        assert set(area["metrics"]) == set(EYFS_AREA_METRICS)
        assert area["schools"]
        for school in area["schools"].values():
            assert set(school) == set(EYFS_SCHOOL_METRICS)
            assert all(0 <= value <= 100 for value in school.values())


def traffic_colour(value):
    if value < 60:
        return TLG_COLOURS["lines"][3]
    if value < 75:
        return TLG_COLOURS["lines"][1]
    return TLG_COLOURS["lines"][2]


def make_eyfs_overview_chart(area_data):
    area_names = list(area_data)
    averages = [sum(area_data[name]["metrics"].values()) / len(EYFS_AREA_METRICS) for name in area_names]
    figure = go.Figure(go.Bar(
        x=averages,
        y=area_names,
        orientation="h",
        marker_color=[traffic_colour(value) for value in averages],
        text=[f"{value:.0f}%" for value in averages],
        textposition="outside",
        hovertemplate="%{y}: %{x:.1f}%<extra></extra>",
    ))
    figure.add_vline(x=75, line_dash="dash", line_color=TLG_COLOURS["lines"][0], annotation_text="75% target")
    figure.update_layout(
        title="EYFS Areas Ranked",
        xaxis={"range": [0, 105], "ticksuffix": "%", "title": None},
        yaxis={"title": None, "autorange": "reversed"},
        height=390,
        margin={"l": 10, "r": 35, "t": 55, "b": 35},
        paper_bgcolor=TLG_COLOURS["background"],
        plot_bgcolor=TLG_COLOURS["background"],
        font={"family": "Arial, Helvetica, sans-serif", "color": TLG_COLOURS["text"]},
    )
    return figure


def make_eyfs_school_chart(metrics):
    values = [metrics[name] for name in EYFS_SCHOOL_METRICS]
    figure = go.Figure(go.Bar(
        x=EYFS_SCHOOL_METRICS,
        y=values,
        marker_color=[traffic_colour(value) for value in values],
        text=[f"{value}%" for value in values],
        textposition="outside",
    ))
    figure.add_hline(y=75, line_dash="dash", line_color=TLG_COLOURS["lines"][0], annotation_text="75% target")
    figure.update_layout(
        title="School Level Metrics",
        yaxis={"range": [0, 105], "ticksuffix": "%", "title": None},
        xaxis={"title": None},
        height=390,
        margin={"l": 10, "r": 20, "t": 55, "b": 100},
        paper_bgcolor=TLG_COLOURS["background"],
        plot_bgcolor=TLG_COLOURS["background"],
        font={"family": "Arial, Helvetica, sans-serif", "color": TLG_COLOURS["text"]},
    )
    return figure


validate_data(df)
validate_breakdown(BREAKDOWN_DATA)
validate_eyfs_data(EYFS_DATA)
if "comparison_wards" not in st.session_state:
    st.session_state.comparison_wards = ["Longsight", "Levenshulme"]
if "current_level" not in st.session_state:
    st.session_state.current_level = "manchester"
if "selected_entity" not in st.session_state:
    st.session_state.selected_entity = None

st.markdown(f"<style>h1 {{ color: {TLG_COLOURS['text']}; letter-spacing: 0; }} .block-container {{ padding-top: 2rem; }}</style>", unsafe_allow_html=True)
st.title("Gorton on a page (overview) - high-level")
st.caption("A compact view of performance against nearby wards and bespoke thresholds.")

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
        line_color=TLG_COLOURS["lines"][0],
        annotation_text=f"Target {TARGETS[metric]}%",
        annotation_position="top left",
    )
    figure.update_layout(
        title={"text": metric, "x": 0.02, "xanchor": "left", "font": {"size": 18, "color": TLG_COLOURS["text"]}},
        barmode="group",
        height=300,
        margin={"l": 12, "r": 12, "t": 52, "b": 35},
        yaxis={"range": [0, 105], "ticksuffix": "%", "gridcolor": "#e5e7e9", "title": None},
        xaxis={"title": None},
        paper_bgcolor=TLG_COLOURS["background"],
        plot_bgcolor=TLG_COLOURS["background"],
        legend={"orientation": "h", "y": -0.18},
        font={"family": "Arial, Helvetica, sans-serif", "color": TLG_COLOURS["text"]},
    )
    return figure


overview_tab, breakdown_tab, eyfs_tab = st.tabs([
    "Ward Overview",
    "At a Glance Breakdown",
    "EYFS Performance",
])

with overview_tab:
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
    colors = {"Gorton": TLG_COLOURS["lines"][3]}
    colors.update({
        ward: TLG_COLOURS["lines"][index % len(TLG_COLOURS["lines"])]
        for index, ward in enumerate(selected_wards)
    })

    st.subheader("Performance by metric")
    chart_columns = st.columns(2)
    for index, metric in enumerate(METRICS):
        with chart_columns[index % 2]:
            st.plotly_chart(make_chart(metric), use_container_width=True, config={"displayModeBar": False})

    st.subheader("Key messages (inc. comparisons)")
    for message in build_key_messages(selected_wards):
        st.markdown(f"- {message}")

with breakdown_tab:
    st.markdown(render_breakdown_table(BREAKDOWN_DATA), unsafe_allow_html=True)
    st.markdown("**Traffic light key**", unsafe_allow_html=False)
    st.markdown(render_traffic_light_key(), unsafe_allow_html=True)
    st.markdown("### Data Summary")
    st.write(build_breakdown_summary(BREAKDOWN_DATA))

with eyfs_tab:
    manchester_data = EYFS_DATA["manchester"]
    area_data = manchester_data["areas"]

    if st.session_state.current_level == "manchester":
        st.subheader("Manchester EYFS Performance")
        overview_columns = st.columns([2, 1])
        with overview_columns[0]:
            st.plotly_chart(
                make_eyfs_overview_chart(area_data),
                use_container_width=True,
                config={"displayModeBar": False},
            )
        with overview_columns[1]:
            st.markdown("#### Drill Down")
            st.caption("Select an area, then a school, to inspect its detailed measures.")
            for area_name, area in area_data.items():
                if st.button(area_name, key=f"eyfs-area-{area_name}", use_container_width=True):
                    st.session_state.current_level = "area"
                    st.session_state.selected_entity = area_name
                    st.rerun()
                for school_name in area["schools"]:
                    if st.button(
                        f"  {school_name}",
                        key=f"eyfs-school-{area_name}-{school_name}",
                        use_container_width=True,
                    ):
                        st.session_state.current_level = "school"
                        st.session_state.selected_entity = (area_name, school_name)
                        st.rerun()

    elif st.session_state.current_level == "area":
        area_name = st.session_state.selected_entity
        area = area_data[area_name]
        st.subheader(f"{area_name} Area Performance")
        st.write("Choose a school to view its detailed EYFS metrics.")
        for school_name in area["schools"]:
            if st.button(school_name, key=f"area-school-{school_name}"):
                st.session_state.current_level = "school"
                st.session_state.selected_entity = (area_name, school_name)
                st.rerun()
        if st.button("Back to Overview", key="back-from-area"):
            st.session_state.current_level = "manchester"
            st.session_state.selected_entity = None
            st.rerun()

    else:
        area_name, school_name = st.session_state.selected_entity
        school_metrics = area_data[area_name]["schools"][school_name]
        st.subheader(f"{school_name} - {area_name}")
        metric_columns = st.columns(3)
        for column, metric_name in zip(metric_columns, ["Pre School Ready", "Toilet Trained", "Feed Independently"]):
            column.metric(metric_name, f"{school_metrics[metric_name]}%")
        st.plotly_chart(
            make_eyfs_school_chart(school_metrics),
            use_container_width=True,
            config={"displayModeBar": False},
        )
        if st.button("Back to Overview", key="back-from-school"):
            st.session_state.current_level = "manchester"
            st.session_state.selected_entity = None
            st.rerun()
