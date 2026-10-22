import numpy as np
import pandas as pd

import utils
from csv_manager import CSVManager

DEFAULT_WEIGHTS = {
    "aqi": 30,
    "temperature": 25,
    "events": 25,
    "green_flood": 10,
    "density": 10,
}


class CityManager(CSVManager):
    filename = "city_profiles.csv"
    id_column = "city_id"
    id_prefix = "C"
    columns = ["city_id", "city", "population", "area_km2", "green_cover_pct", "avg_temperature", "avg_temp_10yr", "avg_aqi", "flood_prone"]
    duplicate_keys = ["city"]
    fields = [
        {"name": "city", "label": "City", "kind": "text", "title": True},
        {"name": "population", "label": "Population", "kind": "int", "min": 1, "max": 50000000},
        {"name": "area_km2", "label": "Area (km²)", "kind": "float", "min": 1, "max": 20000},
        {"name": "green_cover_pct", "label": "Green cover (%)", "kind": "float", "min": 0, "max": 100},
        {"name": "avg_temperature", "label": "Average temperature (°C)", "kind": "float", "min": -50, "max": 60},
        {"name": "avg_temp_10yr", "label": "10-year average temperature (°C)", "kind": "float", "min": -50, "max": 60},
        {"name": "avg_aqi", "label": "Average AQI", "kind": "float", "min": 0, "max": 500},
        {"name": "flood_prone", "label": "Flood prone", "kind": "select", "options": ["Yes", "No"]},
    ]

    @staticmethod
    def normalise(weights):
        total = sum(weights.values())
        if total == 0:
            return {k: 1 / len(weights) for k in weights}
        return {k: v / total for k, v in weights.items()}

    def score(self, cities, events, weights=None):
        weights = self.normalise(weights or DEFAULT_WEIGHTS)
        df = cities.copy()
        score_cols = ["event_count", "aqi_score", "temp_score", "event_score", "green_flood_score", "density_score", "risk_score", "risk_class", "rank"]
        if df.empty:
            for col in score_cols:
                df[col] = []
            return df
        counts = events["city"].str.lower().value_counts() if not events.empty else {}
        df["event_count"] = df["city"].str.lower().map(counts).fillna(0).astype(int)
        aqi = df["avg_aqi"].astype(float)
        deviation = (df["avg_temperature"].astype(float) - df["avg_temp_10yr"].astype(float)).abs()
        green = df["green_cover_pct"].astype(float).clip(0, 40) / 40 * 100
        density = df["population"].astype(float) / df["area_km2"].astype(float)
        df["aqi_score"] = 100 - aqi.clip(0, 300) / 3
        df["temp_score"] = 100 - deviation.clip(0, 3) / 3 * 100
        df["event_score"] = 100 - df["event_count"].clip(0, 8) / 8 * 100
        df["green_flood_score"] = (green - np.where(df["flood_prone"] == "Yes", 30, 0)).clip(0, 100)
        df["density_score"] = 100 - density.clip(0, 20000) / 20000 * 100
        df["risk_score"] = (
            weights["aqi"] * df["aqi_score"]
            + weights["temperature"] * df["temp_score"]
            + weights["events"] * df["event_score"]
            + weights["green_flood"] * df["green_flood_score"]
            + weights["density"] * df["density_score"]
        )
        for col in ["aqi_score", "temp_score", "event_score", "green_flood_score", "density_score", "risk_score"]:
            df[col] = df[col].round(1)
        df["risk_class"] = df["risk_score"].map(utils.risk_label)
        df["rank"] = df["risk_score"].rank(ascending=False, method="min").astype("Int64")
        return df

    def summary(self, scored):
        if scored.empty or scored["risk_score"].notna().sum() == 0:
            return None
        counts = scored["risk_class"].value_counts()
        return {
            "cities": len(scored),
            "safe": int(counts.get("Safe", 0)),
            "moderate": int(counts.get("Moderate", 0)),
            "high": int(counts.get("High Risk", 0)),
            "avg_score": scored["risk_score"].mean(),
            "safest": scored.loc[scored["risk_score"].idxmax(), "city"],
            "riskiest": scored.loc[scored["risk_score"].idxmin(), "city"],
        }
