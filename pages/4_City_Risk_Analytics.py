import pandas as pd
import plotly.express as px
import streamlit as st

import utils
from city_manager import CityManager, DEFAULT_WEIGHTS
from event_manager import EventManager

utils.setup_page("City Risk Analytics", "🏙️", "Which cities are safest? Scores combine air quality, heat, extreme events, green space and crowding.")

manager = CityManager()
ok, message = manager.load()
utils.show_load_message(manager, ok, message)

events = EventManager()
events_ok, events_message = events.load()
if not events_ok:
    st.warning("Event history could not be read, so event frequency counts as zero. " + events_message)

st.sidebar.header("Score weights")
weights = {
    "aqi": st.sidebar.slider("Average AQI", 0, 100, DEFAULT_WEIGHTS["aqi"]),
    "temperature": st.sidebar.slider("Temperature deviation", 0, 100, DEFAULT_WEIGHTS["temperature"]),
    "events": st.sidebar.slider("Extreme event frequency", 0, 100, DEFAULT_WEIGHTS["events"]),
    "green_flood": st.sidebar.slider("Flood-prone and green cover", 0, 100, DEFAULT_WEIGHTS["green_flood"]),
    "density": st.sidebar.slider("Population density", 0, 100, DEFAULT_WEIGHTS["density"]),
}
st.sidebar.caption("Weights are scaled to add up to 100%.")

filtered, applied = utils.sidebar_filters(manager.data, ["city", "flood_prone"], ["population"])
mode = utils.missing_choice("city", manager.missing_count(filtered))
view = manager.handle_missing(filtered, mode)
scored = manager.score(view, events.data, weights)
st.caption(f"Missing values: {mode}")

stats = manager.summary(scored)
if stats:
    utils.metric_row([
        ("Cities", stats["cities"]),
        ("Safe", stats["safe"]),
        ("Moderate", stats["moderate"]),
        ("High Risk", stats["high"]),
        ("Average risk score", f"{stats['avg_score']:.1f}"),
    ])

shown = scored[manager.columns + ["risk_score", "risk_class", "rank"]] if not scored.empty else scored

records, add, edit, delete, charts, report, compare = st.tabs(utils.TABS + ["🏆 Ranking and Compare"])

with records:
    utils.render_records_tab(shown, "city")

with add:
    utils.render_add_tab(manager, "city")

with edit:
    utils.render_edit_tab(manager, "city")

with delete:
    utils.render_delete_tab(manager, "city")

with charts:
    if scored.empty:
        st.info("No data to chart with the current filters.")
    else:
        left, right = st.columns(2)
        ranked = scored.sort_values("risk_score", ascending=False)
        fig = px.bar(ranked, x="city", y="risk_score", color="risk_class", color_discrete_map=utils.RISK_COLORS, title="City risk score (higher is safer)")
        fig.add_hline(y=75, line_dash="dot")
        fig.add_hline(y=50, line_dash="dot")
        left.plotly_chart(fig, use_container_width=True)
        classes = scored["risk_class"].value_counts().reset_index()
        classes.columns = ["risk_class", "cities"]
        fig = px.pie(classes, names="risk_class", values="cities", color="risk_class", color_discrete_map=utils.RISK_COLORS, title="Cities by risk class")
        right.plotly_chart(fig, use_container_width=True)
        temps = scored.melt(id_vars="city", value_vars=["avg_temperature", "avg_temp_10yr"], var_name="measure", value_name="temperature")
        temps["measure"] = temps["measure"].map({"avg_temperature": "Current average", "avg_temp_10yr": "10-year average"})
        fig = px.bar(temps, x="city", y="temperature", color="measure", barmode="group", title="Temperature against the 10-year average")
        st.plotly_chart(fig, use_container_width=True)

with report:
    lines = []
    if stats:
        lines = [
            f"Cities: {stats['cities']} (Safe {stats['safe']}, Moderate {stats['moderate']}, High Risk {stats['high']})",
            f"Average risk score: {stats['avg_score']:.1f}",
            f"Safest city: {stats['safest']}",
            f"Highest risk city: {stats['riskiest']}",
        ]
    utils.render_report_tab("City Risk Report", shown, applied, mode, lines, "city")

with compare:
    if scored.empty:
        st.info("No cities to rank or compare.")
    else:
        st.subheader("Ranking")
        utils.show_table(scored.sort_values("rank")[["rank", "city", "risk_score", "risk_class", "avg_aqi", "event_count"]])
        st.subheader("Compare two cities")
        names = scored["city"].tolist()
        if len(names) < 2:
            st.info("Add at least two cities to compare them.")
        else:
            pick_a, pick_b = st.columns(2)
            first = pick_a.selectbox("First city", names, index=0)
            second = pick_b.selectbox("Second city", names, index=1)
            for column, name in ((pick_a, first), (pick_b, second)):
                row = scored[scored["city"] == name].iloc[0]
                column.metric("Risk score", f"{row['risk_score']:.1f}", row["risk_class"], delta_color="off")
                column.write(f"Average AQI: {row['avg_aqi']:.0f}")
                column.write(f"Temperature: {row['avg_temperature']:.1f} °C vs 10-year {row['avg_temp_10yr']:.1f} °C")
                column.write(f"Extreme events: {row['event_count']}")
                column.write(f"Green cover: {row['green_cover_pct']:.0f} % | Flood prone: {row['flood_prone']}")
                column.write(f"Population: {int(row['population']):,}")
            parts = ["aqi_score", "temp_score", "event_score", "green_flood_score", "density_score"]
            two = scored[scored["city"].isin([first, second])].melt(id_vars="city", value_vars=parts, var_name="factor", value_name="score")
            two["factor"] = two["factor"].str.replace("_score", "").str.replace("_", " ").str.title()
            fig = px.bar(two, x="factor", y="score", color="city", barmode="group", title="Factor scores (higher is safer)")
            st.plotly_chart(fig, use_container_width=True)
