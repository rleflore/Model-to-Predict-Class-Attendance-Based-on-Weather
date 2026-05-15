import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry

# Setup the Open-Meteo API client
cache_session = requests_cache.CachedSession(".cache", expire_after=-1)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

with open("dates.txt", "r") as f:
    dates = [line.strip() for line in f if line.strip()]

start_date = min(dates)
end_date = max(dates)

url = "https://archive-api.open-meteo.com/v1/archive"

params = {
    "latitude": 38.9897,
    "longitude": -76.9378,
    "start_date": start_date,
    "end_date": end_date,
    "daily": ["temperature_2m_mean", "precipitation_sum"],
    "temperature_unit": "fahrenheit",
    "precipitation_unit": "inch",
    "timezone": "America/New_York"
}

responses = openmeteo.weather_api(url, params=params)
response = responses[0]
daily = response.Daily()

weather_df = pd.DataFrame({
    "date": pd.date_range(
        start=pd.to_datetime(daily.Time(), unit="s"),
        end=pd.to_datetime(daily.TimeEnd(), unit="s"),
        freq=pd.Timedelta(seconds=daily.Interval()),
        inclusive="left"
    ),
    "avg_temp": daily.Variables(0).ValuesAsNumpy(),
    "rain_inches": daily.Variables(1).ValuesAsNumpy()
})

weather_df["date"] = weather_df["date"].dt.strftime("%Y-%m-%d")

weather_df = weather_df[weather_df["date"].isin(dates)]

weather_df["rain_flag"] = (weather_df["rain_inches"] > 0).astype(int)

weather_df["bad_weather"] = (
    (weather_df["rain_inches"] > 0) |
    (weather_df["avg_temp"] < 40)
).astype(int)

print(weather_df)

weather_df.to_csv("weather_data.csv", index=False)