import utils
from csv_manager import CSVManager

ACTIONS = {
    "Flood": "Move to higher ground, avoid flooded roads and switch off electricity at the mains.",
    "Heatwave": "Stay indoors in the afternoon, drink water often and check on older neighbours.",
    "Storm": "Stay indoors away from windows, secure loose objects and avoid travel.",
}


class EventManager(CSVManager):
    filename = "extreme_events.csv"
    id_column = "event_id"
    id_prefix = "E"
    columns = ["event_id", "city", "date", "type", "severity", "casualties", "alert_issued"]
    duplicate_keys = ["city", "date", "type"]
    fields = [
        {"name": "city", "label": "City", "kind": "text", "title": True},
        {"name": "date", "label": "Date", "kind": "date"},
        {"name": "type", "label": "Event type", "kind": "select", "options": ["Flood", "Heatwave", "Storm"]},
        {"name": "severity", "label": "Severity (1-5)", "kind": "int", "min": 1, "max": 5},
        {"name": "casualties", "label": "Casualties", "kind": "int", "min": 0, "max": 100000},
        {"name": "alert_issued", "label": "Alert issued", "kind": "select", "options": ["Yes", "No"]},
    ]

    def with_alert_level(self, df):
        df = df.copy()
        df["alert_level"] = df["severity"].map(utils.severity_label)
        return df

    def missing_alerts(self, df):
        return df[(df["severity"] >= 4) & (df["alert_issued"] == "No")]

    def action_for(self, event_type):
        return ACTIONS.get(event_type, "Follow instructions from local authorities.")

    def summary(self, df):
        if df.empty:
            return None
        return {
            "events": len(df),
            "avg_severity": df["severity"].mean(),
            "casualties": int(df["casualties"].fillna(0).sum()),
            "alert_rate": (df["alert_issued"] == "Yes").mean() * 100,
            "most_common": df["type"].mode().iloc[0],
        }

    def counts_by_type(self, df):
        return df.groupby("type").size().reset_index(name="events")

    def counts_by_city(self, df):
        return df.groupby(["city", "type"]).size().reset_index(name="events")
