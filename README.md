# Climate Action and Urban Safety Monitor

22AIE205 Introduction to Python - Term Project (Semester 3, B.Tech CSE-AI)

A Streamlit multi-page app that combines weather, air quality, extreme events and city profiles into explainable climate risk scores. Supports SDG 13 (Climate Action) and SDG 11 (Sustainable Cities).

## Setup (Python 3.10+)

```bash
python -m venv venv
# Windows:  venv\Scripts\activate
# Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
streamlit run Home.py
```

The app opens at http://localhost:8501. It works fully offline: all data is in the `data` folder.

## Who owns what

| Student | Page | CSV file | Page file | Class file |
|---|---|---|---|---|
| Aman Hashim | Weather Dashboard | weather_records.csv | pages/1_Weather_Dashboard.py | weather_manager.py |
| Harigovind M | AQI Monitor | air_quality.csv | pages/2_AQI_Monitor.py | aqi_manager.py |
| Ithihas Suresh | Extreme Event Tracker | extreme_events.csv | pages/3_Extreme_Event_Tracker.py | event_manager.py |
| Amal Sankar K | City Risk Analytics | city_profiles.csv | pages/4_City_Risk_Analytics.py | city_manager.py |

Shared: `csv_manager.py` (base class `CSVManager`) and `utils.py` (labels, styling, shared tabs and filters).
City Risk Analytics reads `extreme_events.csv` (read only) to count events per city. It never writes to it.

## Project structure

```
Home.py                 home page (entry point)
csv_manager.py          base class: load, clean types, safe save, validate, add/update/delete
utils.py                labels, page setup, sidebar filters, CRUD tabs, reports
weather_manager.py      WeatherManager (heat index)
aqi_manager.py          AQIManager (AQI category, advisories)
event_manager.py        EventManager (severity alerts)
city_manager.py         CityManager (risk score)
pages/                  one page per student
data/                   the four CSV files
requirements.txt
```

## How it meets the requirements

- Inheritance: each manager extends `CSVManager`. The loaded table is kept in a protected `_data` attribute and exposed through the `data` property.
- Safe saving: every write goes to a temp file first, then `os.replace` swaps it in, so the CSV is never half written.
- Error handling: `load` and `save` use try/except/else/finally. Missing file, empty file, wrong column types, invalid record ID and duplicate entries all give a friendly on-page message.
- Each CSV is loaded fresh every time a page runs.
- Missing values: choose "exclude rows" or "fill numbers with the median" in the sidebar.
- Reports: a .txt summary (timestamp, row count, filters, statistics) and the filtered data as .csv.

## Scoring

City risk score (0-100, higher is safer): Average AQI 30%, temperature deviation from 10-year average 25%, extreme event frequency 25%, flood-prone and green cover 10%, population density 10%.
Safe 75-100, Moderate 50-74.9, High Risk below 50. Each factor is turned into a 0-100 score first (see the home page for the exact rules). Weights can be changed in the City Risk sidebar.

AQI uses the standard bands: Good, Moderate, Unhealthy for Sensitive Groups, Unhealthy, Very Unhealthy, Hazardous.
Heat index uses the NWS Rothfusz formula.

Note: `city_profiles.csv` has an extra `area_km2` column, needed to calculate population density.

## Going live later (optional)

1. Get a free OpenWeatherMap API key. Put it in `.streamlit/secrets.toml` (do not upload this file to GitHub).
2. Add `requests` to requirements.txt and create `live_data.py` with functions that call the Current Weather and Air Pollution APIs and return a dict matching the CSV columns.
3. Add a "Fetch live data" button on the page that passes those values to `manager.add_record(...)`, inside try/except so the app falls back to the CSV when offline.
4. Wrap the API call in `st.cache_data(ttl=600)` to respect rate limits. For auto-refresh use `@st.fragment(run_every="60s")`.
5. For several readings per day, change `date` to a datetime and update `duplicate_keys`.
