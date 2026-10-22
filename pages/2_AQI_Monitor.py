import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import utils
from aqi_manager import AQIManager

utils.setup_page("AQI Monitor", "🌫️", "Track air quality across cities and see what it means for your health.")

manager = AQIManager()
ok, message = manager.load()
utils.show_load_message(manager, ok, message)

filtered, applied = utils.sidebar_filters(manager.data, ["city"], ["aqi"])
mode = utils.missing_choice("aqi", manager.missing_count(filtered))
view = manager.with_category(manager.handle_missing(filtered, mode))
st.caption(f"Missing values: {mode}")

stats = manager.summary(view)
if stats:
    utils.metric_row([
        ("Records", stats["records"]),
        ("Average AQI", f"{stats['avg_aqi']:.0f}"),
        ("Worst AQI", f"{stats['max_aqi']} ({stats['worst_city']})"),
        ("Unhealthy readings (>150)", stats["unhealthy_records"]),
        ("Average PM2.5", f"{stats['avg_pm25']:.1f}"),
    ])

st.subheader("Health advisory")
if view.empty:
    st.info("No records available for an advisory.")
else:
    city = st.selectbox("City", sorted(view["city"].unique()))
    latest = manager.latest_record(view, city)
    text = f"**{city}** on {latest['date'].strftime('%d %b %Y')}: AQI {int(latest['aqi'])} - {latest['category']}. {manager.advice(latest['category'])}"
    if latest["aqi"] <= 50:
        st.success(text)
    elif latest["aqi"] <= 100:
        st.info(text)
    elif latest["aqi"] <= 150:
        st.warning(text)
    else:
        st.error(text)

records, add, edit, delete, charts, report = st.tabs(utils.TABS)

with records:
    utils.render_records_tab(view, "aqi")

with add:
    utils.render_add_tab(manager, "aqi")
    st.caption("The AQI category is worked out automatically from the AQI value.")

with edit:
    utils.render_edit_tab(manager, "aqi")

with delete:
    utils.render_delete_tab(manager, "aqi")

with charts:
    if view.empty:
        st.info("No data to chart with the current filters.")
    else:
        trend = view.sort_values("date")
        top = max(300, float(trend["aqi"].max()) * 1.1)
        fig = px.line(trend, x="date", y="aqi", color="city", markers=True, title="AQI over time with warning bands")
        low = 0
        for upper, label in utils.AQI_BANDS + [(500, "Hazardous")]:
            if low >= top:
                break
            fig.add_hrect(y0=low, y1=min(upper, top), fillcolor=utils.AQI_COLORS[label], opacity=0.12, line_width=0, layer="below")
            low = upper
        fig.update_yaxes(range=[0, top])
        st.plotly_chart(fig, use_container_width=True)
        left, right = st.columns(2)
        fig = px.bar(manager.pollutant_means(view), x="city", y="average", color="pollutant", barmode="group", title="Pollutant comparison across cities")
        left.plotly_chart(fig, use_container_width=True)
        counts = view["category"].value_counts().reindex(utils.AQI_ORDER).dropna().reset_index()
        counts.columns = ["category", "records"]
        fig = px.pie(counts, names="category", values="records", color="category", color_discrete_map=utils.AQI_COLORS, title="Records by AQI category")
        right.plotly_chart(fig, use_container_width=True)

with report:
    lines = []
    if stats:
        lines = [
            f"Average AQI: {stats['avg_aqi']:.0f}",
            f"Worst AQI: {stats['max_aqi']} in {stats['worst_city']}",
            f"Readings above 150 (unhealthy): {stats['unhealthy_records']}",
            f"Average PM2.5: {stats['avg_pm25']:.1f}",
        ]
    utils.render_report_tab("AQI Monitor Report", view, applied, mode, lines, "aqi")
