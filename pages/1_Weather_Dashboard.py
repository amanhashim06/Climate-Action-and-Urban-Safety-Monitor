import plotly.express as px
import streamlit as st

import utils
from weather_manager import WeatherManager

utils.setup_page("Weather Dashboard", "🌦️", "Temperature, rainfall and humidity trends, with a feels-like temperature for every reading.")

manager = WeatherManager()
ok, message = manager.load()
utils.show_load_message(manager, ok, message)

filtered, applied = utils.sidebar_filters(manager.data, ["city"], ["temperature", "humidity"])
mode = utils.missing_choice("weather", manager.missing_count(filtered))
view = manager.add_heat_index(manager.handle_missing(filtered, mode))
st.caption(f"Missing values: {mode}")

stats = manager.summary(view)
if stats:
    utils.metric_row([
        ("Records", stats["records"]),
        ("Average temperature", f"{stats['avg_temp']:.1f} °C"),
        ("Hottest reading", f"{stats['max_temp']:.1f} °C", ),
        ("Average humidity", f"{stats['avg_humidity']:.0f} %"),
        ("Total rainfall", f"{stats['total_rain']:.0f} mm"),
    ])
    st.caption(f"Hottest city in this selection: {stats['hottest_city']}")

records, add, edit, delete, charts, report = st.tabs(utils.TABS)

with records:
    utils.render_records_tab(view, "weather")
    if not view.empty:
        st.subheader("Statistics by city")
        utils.show_table(manager.city_stats(view))

with add:
    utils.render_add_tab(manager, "weather")

with edit:
    utils.render_edit_tab(manager, "weather")

with delete:
    utils.render_delete_tab(manager, "weather")

with charts:
    if view.empty:
        st.info("No data to chart with the current filters.")
    else:
        trend = view.sort_values("date")
        left, right = st.columns(2)
        fig = px.line(trend, x="date", y="temperature", color="city", markers=True, title="Temperature trend")
        left.plotly_chart(fig, use_container_width=True)
        fig = px.line(trend, x="date", y="rainfall", color="city", markers=True, title="Rainfall trend")
        right.plotly_chart(fig, use_container_width=True)
        left, right = st.columns(2)
        fig = px.scatter(
            view, x="humidity", y="temperature", color="heat_category", hover_data=["city", "date"],
            color_discrete_map=utils.HEAT_COLORS, category_orders={"heat_category": utils.HEAT_ORDER},
            title="Temperature vs humidity",
        )
        left.plotly_chart(fig, use_container_width=True)
        counts = view["heat_category"].value_counts().reindex(utils.HEAT_ORDER).dropna().reset_index()
        counts.columns = ["heat_category", "records"]
        fig = px.bar(counts, x="heat_category", y="records", color="heat_category", color_discrete_map=utils.HEAT_COLORS, title="Feels-like temperature levels")
        right.plotly_chart(fig, use_container_width=True)

with report:
    lines = []
    if stats:
        lines = [
            f"Average temperature: {stats['avg_temp']:.1f} C",
            f"Hottest reading: {stats['max_temp']:.1f} C in {stats['hottest_city']}",
            f"Average humidity: {stats['avg_humidity']:.0f} %",
            f"Total rainfall: {stats['total_rain']:.0f} mm over {stats['rainy_records']} rainy record(s)",
        ]
    utils.render_report_tab("Weather Dashboard Report", view, applied, mode, lines, "weather")
