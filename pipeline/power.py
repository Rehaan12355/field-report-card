"""Pull NASA POWER daily climate for the study box since 1991."""

import json

import numpy as np
import pandas as pd
import requests

from pipeline import config
from pipeline.hls import WEEKS

POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
POWER_DIR = config.RAW_DIR / "power"
START_YEAR = config.CLIMATE_BASELINE_YEARS[0]
RECENT_YEARS = 10


def daily(box, end_year):
    """Daily rain (mm), max and min temperature (deg C) at the box centre.
    NASA POWER's grid is about 0.5 degrees, so one point stands for the box."""
    lon, lat = round((box[0] + box[2]) / 2, 2), round((box[1] + box[3]) / 2, 2)
    cache = POWER_DIR / f"power_daily_{lon}_{lat}_{START_YEAR}_{end_year}.json"
    if not cache.exists():
        params = {
            "parameters": "PRECTOTCORR,T2M_MAX,T2M_MIN",
            "community": "AG",
            "longitude": lon,
            "latitude": lat,
            "start": f"{START_YEAR}0101",
            "end": f"{end_year}1231",
            "format": "JSON",
        }
        r = requests.get(POWER_URL, params=params, timeout=180)
        r.raise_for_status()
        POWER_DIR.mkdir(parents=True, exist_ok=True)
        cache.write_bytes(r.content)
    p = json.loads(cache.read_text())["properties"]["parameter"]
    df = pd.DataFrame({"rain": p["PRECTOTCORR"], "tmax": p["T2M_MAX"], "tmin": p["T2M_MIN"]})
    df.index = pd.to_datetime(df.index)
    return df.where(df > -900)  # POWER marks missing values as -999


def weekly_rain(df):
    """Rain total per year and week, on the same 52-week calendar as HLS."""
    week = np.minimum((df.index.day_of_year - 1) // 7, WEEKS - 1)
    return df["rain"].groupby([df.index.year, week]).sum(min_count=1).unstack()


def heavy_weeks(df, years):
    """True for weeks whose rain total is in the top share of all weeks since
    1991. Returns (mask [year, week], threshold in mm, weekly totals)."""
    weekly = weekly_rain(df)
    threshold = float(np.nanquantile(weekly.values, 1 - config.HEAVY_RAIN_TOP_SHARE))
    chosen = weekly.loc[list(years)]
    return (chosen.values >= threshold), threshold, chosen.values


def _frost_days(year_df):
    doy = year_df.index.day_of_year
    frost = year_df["tmin"] < 0
    spring = doy[frost & (doy < 182)]
    fall = doy[frost & (doy >= 182)]
    return (spring.max() if len(spring) else np.nan), (fall.min() if len(fall) else np.nan)


def climate_trend(df, last_year):
    """Recent years against the 1991 to 2020 normal."""
    rows = []
    for year, ydf in df.groupby(df.index.year):
        spring, fall = _frost_days(ydf)
        rows.append(
            {
                "year": year,
                "hot_days": int((ydf["tmax"] > config.HOT_DAY_C).sum()),
                "last_spring_frost": spring,
                "first_fall_frost": fall,
                "rain_mm": float(ydf["rain"].sum()),
            }
        )
    yearly = pd.DataFrame(rows).set_index("year")
    b0, b1 = config.CLIMATE_BASELINE_YEARS
    normal = yearly.loc[b0:b1].mean()
    recent = yearly.loc[last_year - RECENT_YEARS + 1 : last_year].mean()
    return {
        "normal_years": [b0, b1],
        "recent_years": [last_year - RECENT_YEARS + 1, last_year],
        "measures": {k: {"normal": round(float(normal[k]), 1), "recent": round(float(recent[k]), 1)} for k in yearly},
    }


def run():
    years = list(config.YEARS)
    df = daily(config.STUDY_BOX, years[-1])
    heavy, threshold, totals = heavy_weeks(df, years)
    trend = climate_trend(df, years[-1])
    print(f"heavy-rain week: {threshold:.1f} mm or more; {heavy.sum()} heavy weeks in {years[0]} to {years[-1]}")
    print("climate", json.dumps(trend["measures"]))
    return heavy, threshold, totals, trend


if __name__ == "__main__":
    run()
