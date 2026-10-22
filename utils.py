from datetime import date, datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from csv_manager import MISSING_EXCLUDE, MISSING_MEDIAN

AQI_BANDS = [
    (50, "Good"),
    (100, "Moderate"),
    (150, "Unhealthy for Sensitive Groups"),
    (200, "Unhealthy"),
    (300, "Very Unhealthy"),
]
AQI_ORDER = [label for _, label in AQI_BANDS] + ["Hazardous"]
AQI_COLORS = {
    "Good": "#2e9e4f",
    "Moderate": "#e6b800",
    "Unhealthy for Sensitive Groups": "#f28c28",
    "Unhealthy": "#d64545",
    "Very Unhealthy": "#8e44ad",
    "Hazardous": "#7e2a3a",
}
HEAT_ORDER = ["Comfortable", "Caution", "Extreme Caution", "Danger", "Extreme Danger"]
HEAT_COLORS = {
    "Comfortable": "#2e9e4f",
    "Caution": "#e6b800",
    "Extreme Caution": "#f28c28",
    "Danger": "#d64545",
    "Extreme Danger": "#7e2a3a",
}
RISK_COLORS = {"Safe": "#2e9e4f", "Moderate": "#e6b800", "High Risk": "#d64545"}
EVENT_COLORS = {"Flood": "#1f77b4", "Heatwave": "#d64545", "Storm": "#6c5ce7"}

NICE_NAMES = {
    "record_id": "Record ID", "event_id": "Event ID", "city_id": "City ID",
    "city": "City", "date": "Date",
    "temperature": "Temperature (°C)", "humidity": "Humidity (%)", "rainfall": "Rainfall (mm)",
    "wind_speed": "Wind Speed (km/h)", "visibility": "Visibility (km)",
    "heat_index": "Feels-Like Temperature (°C)", "heat_category": "Heat Level",
    "aqi": "Air Quality Index", "pm25": "PM2.5 (µg/m³)", "pm10": "PM10 (µg/m³)", "no2": "NO₂ (µg/m³)",
    "category": "Air Quality Level",
    "type": "Event Type", "severity": "Severity (1-5)", "casualties": "Casualties",
    "alert_issued": "Alert Issued", "alert_level": "Alert Level",
    "population": "Population", "area_km2": "Area (km²)", "green_cover_pct": "Green Cover (%)",
    "avg_temperature": "Average Temperature (°C)", "avg_temp_10yr": "10-Year Average Temperature (°C)",
    "avg_aqi": "Average Air Quality Index", "flood_prone": "Flood Prone",
    "risk_score": "Risk Score", "risk_class": "Risk Level", "rank": "Safety Rank",
    "event_count": "Extreme Events", "aqi_score": "Air Quality Score", "temp_score": "Temperature Score",
    "event_score": "Event Score", "green_flood_score": "Green Cover and Flood Score", "density_score": "Crowding Score",
    "records": "Records", "avg_temp": "Average Temperature (°C)", "avg_humidity": "Average Humidity (%)",
    "total_rain": "Total Rainfall (mm)", "events": "Number of Events", "cities": "Number of Cities",
    "average": "Average (µg/m³)", "pollutant": "Pollutant", "measure": "Measure",
    "factor": "Factor", "score": "Score", "temperature_measure": "Measure",
}
STAT_NAMES = {"count": "Count", "mean": "Average", "std": "Std Dev", "min": "Lowest", "50%": "Median", "max": "Highest"}
TABS = ["📋 Records", "➕ Add", "✏️ Edit", "🗑️ Delete", "📊 Charts", "📄 Report"]

px.defaults.template = "plotly_white"
#px.defaults.color_discrete_sequence = ["#2e9e4f", "#1f77b4", "#f28c28", "#8e44ad", "#d64545", "#16a2b8", "#e6b800", "#7e2a3a"]
px.defaults.color_discrete_sequence = ["#0f766e", "#2563eb", "#f59e0b", "#7c3aed", "#e11d48", "#06b6d4", "#84cc16", "#475569"]
px.defaults.labels = NICE_NAMES

# CSS = """
# <style>
# .banner {
#     background: linear-gradient(120deg, #1b6b3a, #2e9e4f 55%, #3fb6a8);
#     color: white;
#     padding: 22px 28px;
#     border-radius: 14px;
#     margin-bottom: 18px;
# }
# .banner-title { font-size: 2rem; font-weight: 700; line-height: 1.2; }
# .banner p { margin: 6px 0 0 0; font-size: 1.02rem; opacity: 0.92; }
# div[data-testid="stMetric"] {
#     background: white;
#     border: 1px solid #dbe7e1;
#     border-left: 6px solid #2e9e4f;
#     border-radius: 12px;
#     padding: 12px 16px;
#     box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
# }
# div[data-testid="stMetricValue"] { color: #1b6b3a; }
# button[data-baseweb="tab"] { font-size: 1rem; font-weight: 600; }
# section[data-testid="stSidebar"] { background: #eef5f1; }
# </style>
# """

CSS = """
<style>
.banner {
    background: linear-gradient(120deg, #0b4f6c, #0f766e 55%, #2a9d8f);
    color: white;
    padding: 22px 28px;
    border-radius: 14px;
    margin-bottom: 18px;
}
.banner-title { font-size: 2rem; font-weight: 700; line-height: 1.2; }
.banner p { margin: 6px 0 0 0; font-size: 1.02rem; opacity: 0.92; }
div[data-testid="stMetric"] {
    background: white;
    border: 1px solid #d3e6e4;
    border-left: 6px solid #0f766e;
    border-radius: 12px;
    padding: 12px 16px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}
div[data-testid="stMetricValue"] { color: #0b4f6c; }
button[data-baseweb="tab"] { font-size: 1rem; font-weight: 600; }
section[data-testid="stSidebar"] { background: #e6f2f1; }
</style>
"""


def aqi_label(aqi):
    if pd.isna(aqi):
        return "Unknown"
    for upper, label in AQI_BANDS:
        if aqi <= upper:
            return label
    return "Hazardous"


def heat_label(heat_index):
    if pd.isna(heat_index):
        return "Unknown"
    if heat_index < 27:
        return "Comfortable"
    if heat_index < 32:
        return "Caution"
    if heat_index < 39:
        return "Extreme Caution"
    if heat_index < 51:
        return "Danger"
    return "Extreme Danger"


def risk_label(score):
    if pd.isna(score):
        return "Unknown"
    if score >= 75:
        return "Safe"
    if score >= 50:
        return "Moderate"
    return "High Risk"


def severity_label(severity):
    if pd.isna(severity):
        return "Unknown"
    if severity >= 5:
        return "Critical"
    if severity >= 4:
        return "High"
    if severity >= 3:
        return "Moderate"
    return "Low"


def nice(name):
    return NICE_NAMES.get(name, str(name).replace("_", " ").title())


pretty = nice


def show_table(df, hide_index=True):
    config = {}
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            config[nice(col)] = st.column_config.DateColumn(format="DD MMM YYYY")
    st.dataframe(df.rename(columns=nice), column_config=config, width="stretch", hide_index=hide_index)


def setup_page(title, icon, subtitle=""):
    st.set_page_config(page_title=f"{title} | Climate Monitor", page_icon=icon, layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(
        f'<div class="banner"><div class="banner-title">{icon} {title}</div><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )
    show_flash()


def flash(message, ok=True):
    st.session_state["flash"] = (message, ok)


def show_flash():
    item = st.session_state.pop("flash", None)
    if item:
        message, ok = item
        if ok:
            st.success(message)
        else:
            st.error(message)


def show_load_message(manager, ok, message):
    if not ok:
        st.error(message)
    for warning in manager.warnings:
        st.warning(warning)


def metric_row(items):
    columns = st.columns(len(items))
    for column, (label, value) in zip(columns, items):
        column.metric(label, value)


def missing_choice(prefix, missing_rows):
    st.sidebar.header("Missing values")
    mode = st.sidebar.radio(
        "How should missing values be handled?",
        [MISSING_EXCLUDE, MISSING_MEDIAN],
        key=f"{prefix}_missing",
    )
    st.sidebar.caption(f"{missing_rows} row(s) in the current selection have missing values.")
    return mode


def sidebar_filters(df, select_cols=(), number_cols=()):
    applied = {}
    out = df
    st.sidebar.header("Search and filters")
    search = st.sidebar.text_input("Search", placeholder="ID, city, type...").strip()
    if search:
        text = out.astype(str)
        mask = text.apply(lambda col: col.str.contains(search, case=False, na=False, regex=False)).any(axis=1)
        out = out[mask]
        applied["Search"] = search
    for col in select_cols:
        options = sorted(df[col].dropna().unique().tolist())
        chosen = st.sidebar.multiselect(pretty(col), options)
        if chosen:
            out = out[out[col].isin(chosen)]
            applied[pretty(col)] = ", ".join(str(c) for c in chosen)
    if "date" in df.columns and df["date"].notna().any():
        low, high = df["date"].min().date(), df["date"].max().date()
        picked = st.sidebar.date_input("Date range", value=(low, high), min_value=low, max_value=high)
        if len(picked) == 2 and tuple(picked) != (low, high):
            start, end = picked
            out = out[(out["date"] >= pd.Timestamp(start)) & (out["date"] <= pd.Timestamp(end))]
            applied["Date range"] = f"{start} to {end}"
    for col in number_cols:
        series = df[col].dropna().astype(float)
        if series.empty or series.min() == series.max():
            continue
        low, high = float(series.min()), float(series.max())
        picked = st.sidebar.slider(pretty(col), low, high, (low, high))
        if picked != (low, high):
            out = out[out[col].astype(float).between(picked[0], picked[1])]
            applied[pretty(col)] = f"{picked[0]:.1f} to {picked[1]:.1f}"
    return out, applied


def field_input(field, key, default=None):
    kind, label = field["kind"], field["label"]
    if kind == "select":
        options = field["options"]
        index = options.index(default) if default in options else 0
        return st.selectbox(label, options, index=index, key=key)
    if kind == "date":
        if default is None or pd.isna(default):
            default = date.today()
        elif isinstance(default, pd.Timestamp):
            default = default.date()
        return st.date_input(label, value=default, key=key)
    shown = "" if default is None or pd.isna(default) else str(default)
    help_text = None
    if field.get("min") is not None and field.get("max") is not None:
        help_text = f"Allowed range: {field['min']} to {field['max']}"
    return st.text_input(label, value=shown, key=key, help=help_text)


def record_labels(manager):
    df = manager.data
    labels = {}
    for _, row in df.iterrows():
        parts = [row[manager.id_column]]
        if "city" in df.columns:
            parts.append(str(row["city"]))
        if "date" in df.columns and pd.notna(row["date"]):
            parts.append(row["date"].strftime("%Y-%m-%d"))
        labels[row[manager.id_column]] = " | ".join(parts)
    return labels


def render_records_tab(df, prefix):
    if df.empty:
        st.info("No records match the current filters.")
        return
    left, right = st.columns([2, 1])
    sort_col = left.selectbox("Sort by", list(df.columns), format_func=nice, key=f"{prefix}_sort")
    order = right.radio("Order", ["Ascending", "Descending"], horizontal=True, key=f"{prefix}_order")
    shown = df.sort_values(sort_col, ascending=(order == "Ascending"))
    st.caption(f"Showing {len(shown)} record(s)")
    show_table(shown)
    numbers = shown.select_dtypes("number")
    if not numbers.empty:
        st.subheader("Summary statistics")
        stats = numbers.describe().T.round(2).rename(index=nice, columns=STAT_NAMES)
        st.dataframe(stats, width="stretch")


def render_add_tab(manager, prefix):
    st.subheader("Add a new record")
    new_id = manager.next_id()
    with st.form(f"{prefix}_add_form"):
        record_id = st.text_input(nice(manager.id_column), value=new_id, key=f"{prefix}_add_{new_id}_id")
        values = {}
        for field in manager.fields:
            values[field["name"]] = field_input(field, f"{prefix}_add_{new_id}_{field['name']}")
        submitted = st.form_submit_button("Add record")
    if submitted:
        ok, message = manager.add_record(record_id, values)
        if ok:
            flash(message)
            st.rerun()
        else:
            st.error(message)


def render_edit_tab(manager, prefix):
    st.subheader("Edit a record")
    labels = record_labels(manager)
    if not labels:
        st.info("There are no records to edit yet.")
        return
    record_id = st.selectbox("Choose a record", list(labels), format_func=labels.get, key=f"{prefix}_edit_pick")
    record = manager.get_record(record_id)
    if record is None:
        st.error(f"Record {record_id} was not found. Reload the page and try again.")
        return
    with st.form(f"{prefix}_edit_form_{record_id}"):
        values = {}
        for field in manager.fields:
            values[field["name"]] = field_input(field, f"{prefix}_edit_{record_id}_{field['name']}", record[field["name"]])
        submitted = st.form_submit_button("Save changes")
    if submitted:
        ok, message = manager.update_record(record_id, values)
        if ok:
            flash(message)
            st.rerun()
        else:
            st.error(message)


def render_delete_tab(manager, prefix):
    st.subheader("Delete a record")
    labels = record_labels(manager)
    if not labels:
        st.info("There are no records to delete.")
        return
    record_id = st.selectbox("Choose a record", list(labels), format_func=labels.get, key=f"{prefix}_delete_pick")
    record = manager.get_record(record_id)
    if record is None:
        st.error(f"Record {record_id} was not found. Reload the page and try again.")
        return
    show_table(pd.DataFrame([record]))
    confirmed = st.checkbox("Yes, I want to permanently delete this record", key=f"{prefix}_confirm_{record_id}")
    if st.button("Delete record", key=f"{prefix}_delete_btn"):
        if not confirmed:
            st.warning("Tick the confirmation box first.")
        else:
            ok, message = manager.delete_record(record_id)
            flash(message, ok)
            st.rerun()


def build_report(title, df, applied, missing_mode, summary_lines):
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [title, "=" * len(title), f"Generated: {stamp}", f"Rows in report: {len(df)}", f"Missing values: {missing_mode}", "Filters applied:"]
    if applied:
        lines += [f"  - {name}: {value}" for name, value in applied.items()]
    else:
        lines.append("  - none")
    lines += ["", "Summary:"] + [f"  - {line}" for line in summary_lines]
    numbers = df.select_dtypes("number")
    if not numbers.empty:
        lines += ["", "Numeric columns (count, mean, min, max):"]
        for col in numbers.columns:
            series = numbers[col].dropna()
            if len(series):
                lines.append(f"  {nice(col)}: {len(series)}, {series.mean():.2f}, {series.min():.2f}, {series.max():.2f}")
    return "\n".join(lines)


def render_report_tab(title, df, applied, missing_mode, summary_lines, prefix):
    st.subheader("Summary report")
    if df.empty:
        st.info("Nothing to report with the current filters.")
        return
    report = build_report(title, df, applied, missing_mode, summary_lines)
    st.code(report, language="text")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    left, right = st.columns(2)
    left.download_button("Download report (.txt)", report, file_name=f"{prefix}_report_{stamp}.txt", mime="text/plain")
    right.download_button("Download filtered data (.csv)", df.to_csv(index=False), file_name=f"{prefix}_data_{stamp}.csv", mime="text/csv")
