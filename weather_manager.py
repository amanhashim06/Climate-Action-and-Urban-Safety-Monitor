import math

import numpy as np
import pandas as pd

import utils
from csv_manager import CSVManager


class WeatherManager(CSVManager):
    filename = "weather_records.csv"
    id_column = "record_id"
    id_prefix = "W"
    columns = ["record_id", "city", "date", "temperature", "humidity", "rainfall", "wind_speed", "visibility"]
    duplicate_keys = ["city", "date"]
    fields = [
        {"name": "city", "label": "City", "kind": "text", "title": True},
        {"name": "date", "label": "Date", "kind": "date"},
        {"name": "temperature", "label": "Temperature (°C)", "kind": "float", "min": -50, "max": 60},
        {"name": "humidity", "label": "Humidity (%)", "kind": "float", "min": 0, "max": 100},
        {"name": "rainfall", "label": "Rainfall (mm)", "kind": "float", "min": 0, "max": 1000},
        {"name": "wind_speed", "label": "Wind speed (km/h)", "kind": "float", "min": 0, "max": 200},
        {"name": "visibility", "label": "Visibility (km)", "kind": "float", "min": 0, "max": 50},
    ]

    @staticmethod
    def heat_index(temp_c, humidity):
        if pd.isna(temp_c) or pd.isna(humidity):
            return np.nan
        t = temp_c * 9 / 5 + 32
        rh = humidity
        simple = 0.5 * (t + 61 + (t - 68) * 1.2 + rh * 0.094)
        if (simple + t) / 2 < 80:
            hi = simple
        else:
            hi = (-42.379 + 2.04901523 * t + 10.14333127 * rh - 0.22475541 * t * rh
                  - 0.00683783 * t * t - 0.05481717 * rh * rh + 0.00122874 * t * t * rh
                  + 0.00085282 * t * rh * rh - 0.00000199 * t * t * rh * rh)
            if rh < 13 and 80 <= t <= 112:
                hi -= ((13 - rh) / 4) * math.sqrt((17 - abs(t - 95)) / 17)
            elif rh > 85 and 80 <= t <= 87:
                hi += ((rh - 85) / 10) * ((87 - t) / 5)
        return (hi - 32) * 5 / 9

    def add_heat_index(self, df):
        df = df.copy()
        df["heat_index"] = [self.heat_index(t, h) for t, h in zip(df["temperature"], df["humidity"])]
        df["heat_index"] = df["heat_index"].astype(float).round(1)
        df["heat_category"] = df["heat_index"].map(utils.heat_label)
        return df

    def summary(self, df):
        if df.empty or df["temperature"].notna().sum() == 0:
            return None
        hottest = df.loc[df["temperature"].idxmax()]
        return {
            "records": len(df),
            "avg_temp": df["temperature"].mean(),
            "max_temp": hottest["temperature"],
            "hottest_city": hottest["city"],
            "avg_humidity": df["humidity"].mean(),
            "total_rain": df["rainfall"].sum(),
            "rainy_records": int((df["rainfall"] > 0).sum()),
        }

    def city_stats(self, df):
        stats = df.groupby("city").agg(
            records=("record_id", "count"),
            avg_temp=("temperature", "mean"),
            avg_humidity=("humidity", "mean"),
            total_rain=("rainfall", "sum"),
        )
        return stats.round(1).reset_index()
