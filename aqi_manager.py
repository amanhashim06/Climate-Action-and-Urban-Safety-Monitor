import pandas as pd

import utils
from csv_manager import CSVManager

ADVICE = {
    "Good": "Air quality is good. Enjoy outdoor activities.",
    "Moderate": "Air quality is acceptable. Unusually sensitive people should consider limiting long outdoor exertion.",
    "Unhealthy for Sensitive Groups": "Children, older adults and people with asthma or heart disease should reduce outdoor activity.",
    "Unhealthy": "Everyone may feel effects. Limit outdoor exertion and wear a mask outside.",
    "Very Unhealthy": "Health warning. Avoid outdoor activity and keep windows closed.",
    "Hazardous": "Emergency conditions. Stay indoors and use an air purifier if possible.",
}


class AQIManager(CSVManager):
    filename = "air_quality.csv"
    id_column = "record_id"
    id_prefix = "A"
    columns = ["record_id", "city", "date", "aqi", "pm25", "pm10", "no2", "category"]
    duplicate_keys = ["city", "date"]
    fields = [
        {"name": "city", "label": "City", "kind": "text", "title": True},
        {"name": "date", "label": "Date", "kind": "date"},
        {"name": "aqi", "label": "AQI", "kind": "int", "min": 0, "max": 500},
        {"name": "pm25", "label": "PM2.5 (µg/m³)", "kind": "float", "min": 0, "max": 1000},
        {"name": "pm10", "label": "PM10 (µg/m³)", "kind": "float", "min": 0, "max": 1500},
        {"name": "no2", "label": "NO2 (µg/m³)", "kind": "float", "min": 0, "max": 2000},
    ]

    def prepare(self, cleaned):
        cleaned["category"] = utils.aqi_label(cleaned["aqi"])
        return cleaned

    def with_category(self, df):
        df = df.copy()
        df["category"] = df["aqi"].map(utils.aqi_label)
        return df

    def latest_record(self, df, city):
        rows = df[df["city"] == city].sort_values("date")
        if rows.empty:
            return None
        return rows.iloc[-1]

    def advice(self, category):
        return ADVICE.get(category, "No advice available.")

    def pollutant_means(self, df):
        means = df.groupby("city")[["pm25", "pm10", "no2"]].mean().round(1).reset_index()
        result = means.melt(id_vars="city", var_name="pollutant", value_name="average")
        result["pollutant"] = result["pollutant"].map({"pm25": "PM2.5", "pm10": "PM10", "no2": "NO₂"})
        return result

    def summary(self, df):
        if df.empty or df["aqi"].notna().sum() == 0:
            return None
        worst = df.loc[df["aqi"].idxmax()]
        return {
            "records": len(df),
            "avg_aqi": df["aqi"].mean(),
            "max_aqi": int(worst["aqi"]),
            "worst_city": worst["city"],
            "unhealthy_records": int((df["aqi"] > 150).sum()),
            "avg_pm25": df["pm25"].mean(),
        }
