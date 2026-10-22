import pandas as pd
import streamlit as st

import utils

utils.setup_page("Climate Action and Urban Safety Monitor", "🌍", "How safe is your city? Weather, air quality, extreme events and city profiles in one place.")

st.write(
    "Weather readings alone do not show whether a city is safe. Air quality, extreme events, heat trends and "
    "city characteristics matter too. This app combines them into clear, explainable risk scores."
)
st.info("Supports **SDG 13 (Climate Action)** and **SDG 11 (Sustainable Cities and Communities)**. Course: 22AIE205 Introduction to Python.")

st.header("Pages")
col1, col2, col3, col4 = st.columns(4)
col1.page_link("pages/1_Weather_Dashboard.py", label="Weather Dashboard", icon="🌦️", width="stretch")
col2.page_link("pages/2_AQI_Monitor.py", label="AQI Monitor", icon="🌫️", width="stretch")
col3.page_link("pages/3_Extreme_Event_Tracker.py", label="Extreme Event Tracker", icon="⛈️", width="stretch")
col4.page_link("pages/4_City_Risk_Analytics.py", label="City Risk Analytics", icon="🏙️", width="stretch")

st.header("Who owns what")
owners = pd.DataFrame([
    ["Aman Hashim", "Weather Dashboard", "weather_records.csv", "pages/1_Weather_Dashboard.py", "weather_manager.py"],
    ["Harigovind M", "AQI Monitor", "air_quality.csv", "pages/2_AQI_Monitor.py", "aqi_manager.py"],
    ["Ithihas Suresh", "Extreme Event Tracker", "extreme_events.csv", "pages/3_Extreme_Event_Tracker.py", "event_manager.py"],
    ["Amal Sankar K", "City Risk Analytics", "city_profiles.csv", "pages/4_City_Risk_Analytics.py", "city_manager.py"],
], columns=["Student", "Page", "CSV file", "Page file", "Class file"])
st.dataframe(owners, width="stretch", hide_index=True)
st.caption("Shared code: csv_manager.py (base class CSVManager) and utils.py (labels, styling, shared tabs).")

st.header("Datasets and fields")
datasets = {
    "weather_records.csv": "record_id, city, date, temperature, humidity, rainfall, wind_speed, visibility",
    "air_quality.csv": "record_id, city, date, aqi, pm25, pm10, no2, category",
    "extreme_events.csv": "event_id, city, date, type (Flood / Heatwave / Storm), severity (1-5), casualties, alert_issued",
    "city_profiles.csv": "city_id, city, population, area_km2, green_cover_pct, avg_temperature, avg_temp_10yr, avg_aqi, flood_prone",
}
for name, fields in datasets.items():
    with st.expander(name):
        st.code(fields, language="text")
st.caption("The sample data in /data is for demonstration and can be replaced with a real export.")

st.header("How scores are calculated")
st.subheader("City risk score (0 to 100, higher is safer)")
st.table(pd.DataFrame([
    ["Average AQI", "30%", "100 at AQI 0, falling to 0 at AQI 300 or more"],
    ["Temperature deviation from 10-year average", "25%", "100 at no deviation, 0 at 3 °C or more"],
    ["Extreme event frequency", "25%", "100 with no events, 0 at 8 or more events"],
    ["Flood-prone and green cover", "10%", "Green cover up to 40% scores 100, minus 30 if flood prone"],
    ["Population density", "10%", "100 at zero density, 0 at 20,000 people per km² or more"],
], columns=["Factor", "Default weight", "Factor score"]))
st.write("Classes: **Safe** 75 to 100, **Moderate** 50 to 74.9, **High Risk** below 50. Weights can be changed on the City Risk Analytics page.")
st.subheader("AQI category")
st.write("Good (0-50), Moderate (51-100), Unhealthy for Sensitive Groups (101-150), Unhealthy (151-200), Very Unhealthy (201-300), Hazardous (301+).")
st.subheader("Heat index category")
st.write("Heat index uses the standard NWS formula from temperature and humidity: Comfortable (below 27 °C), Caution (27-32), Extreme Caution (32-39), Danger (39-51), Extreme Danger (51+).")
