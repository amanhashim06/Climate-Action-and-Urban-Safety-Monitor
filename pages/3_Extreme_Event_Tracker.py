import plotly.express as px
import streamlit as st

import utils
from event_manager import EventManager

utils.setup_page("Extreme Event Tracker", "⛈️", "Floods, heatwaves and storms: what happened, how serious it was and whether people were warned.")

manager = EventManager()
ok, message = manager.load()
utils.show_load_message(manager, ok, message)


@st.dialog("Extreme event alert")
def alert_popup(event):
    level = utils.severity_label(event["severity"])
    st.subheader(f"{level} {event['type']} - {event['city']}")
    st.write(f"Date: {event['date'].strftime('%d %b %Y')}")
    st.write(f"Severity: {event['severity']} / 5")
    st.write(f"Casualties: {event['casualties']}")
    st.write(f"Alert issued: {event['alert_issued']}")
    if event["alert_issued"] == "No" and event["severity"] >= 4:
        st.error("No alert has been issued for this serious event.")
    st.info(manager.action_for(event["type"]))


gaps = manager.missing_alerts(manager.data)
if len(gaps) and not st.session_state.get("event_toast_shown"):
    st.toast(f"{len(gaps)} severe event(s) have no alert issued. Check the Alerts tab.", icon="🚨")
    st.session_state["event_toast_shown"] = True

filtered, applied = utils.sidebar_filters(manager.data, ["city", "type"], ["severity"])
mode = utils.missing_choice("events", manager.missing_count(filtered))
view = manager.with_alert_level(manager.handle_missing(filtered, mode))
st.caption(f"Missing values: {mode}")

stats = manager.summary(view)
if stats:
    utils.metric_row([
        ("Events", stats["events"]),
        ("Average severity", f"{stats['avg_severity']:.1f}"),
        ("Total casualties", stats["casualties"]),
        ("Alerts issued", f"{stats['alert_rate']:.0f} %"),
        ("Most common type", stats["most_common"]),
    ])

records, add, edit, delete, charts, report, alerts = st.tabs(utils.TABS + ["🚨 Alerts"])

with records:
    utils.render_records_tab(view, "events")

with add:
    utils.render_add_tab(manager, "events")

with edit:
    utils.render_edit_tab(manager, "events")

with delete:
    utils.render_delete_tab(manager, "events")

with charts:
    if view.empty:
        st.info("No data to chart with the current filters.")
    else:
        left, right = st.columns(2)
        fig = px.pie(manager.counts_by_type(view), names="type", values="events", color="type", color_discrete_map=utils.EVENT_COLORS, title="Events by type")
        left.plotly_chart(fig, use_container_width=True)
        fig = px.bar(manager.counts_by_city(view), x="city", y="events", color="type", color_discrete_map=utils.EVENT_COLORS, title="Events by city")
        right.plotly_chart(fig, use_container_width=True)
        timeline = view.sort_values("date")
        fig = px.scatter(
            timeline, x="date", y="city", color="type", size="severity", hover_data=["event_id", "casualties", "alert_issued"],
            color_discrete_map=utils.EVENT_COLORS, title="Timeline of past events (bubble size = severity)",
        )
        st.plotly_chart(fig, use_container_width=True)

with report:
    lines = []
    if stats:
        lines = [
            f"Events: {stats['events']}",
            f"Average severity: {stats['avg_severity']:.1f}",
            f"Total casualties: {stats['casualties']}",
            f"Alerts issued: {stats['alert_rate']:.0f} %",
        ]
    utils.render_report_tab("Extreme Event Report", view, applied, mode, lines, "events")

with alerts:
    st.subheader("Severity based alerts")
    serious = view[view["severity"] >= 3].sort_values(["severity", "date"], ascending=False)
    if serious.empty:
        st.info("No events with severity 3 or higher in the current selection.")
    else:
        for _, event in serious.head(8).iterrows():
            text = f"**{event['alert_level']}** {event['type']} in {event['city']} on {event['date'].strftime('%d %b %Y')} (severity {event['severity']}, alert issued: {event['alert_issued']})"
            if event["severity"] >= 5:
                st.error(text)
            elif event["severity"] >= 4:
                st.warning(text)
            else:
                st.info(text)
        labels = {row["event_id"]: f"{row['event_id']} | {row['city']} | {row['type']} | severity {row['severity']}" for _, row in serious.iterrows()}
        picked = st.selectbox("Open an alert pop-up", list(labels), format_func=labels.get)
        if st.button("Show alert pop-up"):
            event = manager.get_record(picked)
            if event is None:
                st.error("That event could not be found.")
            else:
                alert_popup(event)
