"""Pull NASA POWER daily climate for the study area since 1991."""

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
# NASA POWER's weather grid (from MERRA-2): cells of 0.5 degrees of latitude
# by 0.625 degrees of longitude, centred on multiples of those steps.
LAT_STEP, LON_STEP = 0.5, 0.625


def cell_centres(box):
    """Centres of the POWER grid cells that touch the box, as (lon, lat)."""
    w, s, e, n = box
    lons = np.arange(np.round(w / LON_STEP), np.round(e / LON_STEP) + 1) * LON_STEP
    lats = np.arange(np.round(s / LAT_STEP), np.round(n / LAT_STEP) + 1) * LAT_STEP
    return [(float(lon), float(lat)) for lat in lats for lon in lons]


def daily(lon, lat, end_year):
    """Daily rain (mm), max and min temperature (deg C) for one grid cell."""
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
    1991 in that cell. Returns (mask [year, week], threshold in mm, totals)."""
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


def nearest_cell(fields, centres):
    """Index of the grid cell each field's centre falls nearest to."""
    pts = fields.to_crs(4326).geometry.representative_point()
    xy = np.column_stack([pts.x.values, pts.y.values])
    c = np.array(centres)
    # Scale by the cell size so "nearest" means "inside that cell".
    d = ((xy[:, None, 0] - c[None, :, 0]) / LON_STEP) ** 2 + ((xy[:, None, 1] - c[None, :, 1]) / LAT_STEP) ** 2
    return d.argmin(axis=1)


def run(fields):
    """Climate for every grid cell that holds fields. Returns the list of
    cells and each field's cell index."""
    years = list(config.YEARS)
    centres = cell_centres(config.STUDY_BOX)
    which = nearest_cell(fields, centres)
    used = sorted(set(which.tolist()))
    cells = []
    for ci in used:
        lon, lat = centres[ci]
        df = daily(lon, lat, years[-1])
        heavy, threshold, totals = heavy_weeks(df, years)
        cells.append(
            {
                "lon": lon,
                "lat": lat,
                "heavy": heavy,
                "heavy_mm": threshold,
                "rain": totals,
                "climate": climate_trend(df, years[-1]),
                "fields": int((which == ci).sum()),
            }
        )
        print(f"  cell {lon}, {lat}: {cells[-1]['fields']} fields, heavy week {threshold:.1f} mm or more, {heavy.sum()} heavy weeks")
    remap = {ci: i for i, ci in enumerate(used)}
    return cells, np.array([remap[c] for c in which.tolist()])


if __name__ == "__main__":
    import geopandas as gpd

    run(gpd.read_file(config.WORK_DIR / "fields.gpkg"))
