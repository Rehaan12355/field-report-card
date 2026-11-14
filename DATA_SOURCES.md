# Data sources

Every dataset the project uses, with each download logged at the bottom. No
number in the app comes from anywhere else. Checked on 14 November 2026.

## Study box

**Box 1, confirmed by the team on 14 November 2026.**

| | West | South | East | North | HLS tile |
|---|---|---|---|---|---|
| Box 1 (used): Colfax to Pullman | -117.48 | 46.71 | -117.22 | 46.89 | T11TMM |
| Box 2 (compared only): Endicott and LaCrosse | -117.93 | 46.76 | -117.67 | 46.94 | T11TMM |

Years: 2019 to 2025. 591 fields, 33,361 hectares.

### Clear satellite passes per month, Box 1

Passes (Landsat and Sentinel-2 together) in which at least half the fields
had a clear view.

| Year | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | 3 | 0 | 1 | 1 | 7 | 9 | 10 | 8 | 4 | 5 | 5 | 0 |
| 2020 | 1 | 1 | 2 | 6 | 6 | 4 | 9 | 11 | 7 | 5 | 2 | 2 |
| 2021 | 1 | 1 | 5 | 8 | 7 | 9 | 11 | 9 | 10 | 6 | 2 | 0 |
| 2022 | 0 | 4 | 3 | 3 | 4 | 5 | 10 | 8 | 7 | 11 | 2 | 0 |
| 2023 | 3 | 3 | 6 | 3 | 9 | 6 | 13 | 9 | 4 | 8 | 2 | 1 |
| 2024 | 1 | 1 | 7 | 3 | 4 | 6 | 12 | 11 | 8 | 8 | 2 | 0 |
| 2025 | 4 | 1 | 4 | 11 | 9 | 9 | 13 | 7 | 17 | 6 | 3 | 1 |

**Finding:** December and January have almost no clear views in any year.

### Box 2 comparison, 2024

Counted in step 2 with a stricter test (half the whole box clear):
Box 1 had 1, 2, 9, 4, 6, 7, 12, 11, 8, 8, 2, 0 clear passes from January to
December; Box 2 had 0, 2, 12, 7, 8, 7, 16, 15, 11, 9, 3, 1. Box 2 sees a
little more in summer but does not fix winter, so Box 1 was kept.

### Heavy-rain timing, NASA POWER 1991 to 2025

A heavy-rain week is in the top 10% of weekly rain totals at the box centre
(-117.35, 46.80): 29.4 mm or more, 182 weeks in all.
77% of them fall between November and March.

**Finding:** most heavy rain falls in the months the satellites see least. The
team chose to bridge long cloudy gaps when both ends agree and to report those
weeks separately as "likely"; see docs/methods.md.

## Datasets

| Data | Provider | What it gives us | Access | Licence | Status |
|------|----------|------------------|--------|---------|--------|
| HLS Vegetation Indices (HLSL30_VI, HLSS30_VI v2.0) | NASA LP DAAC (Landsat: NASA/USGS, Sentinel-2: ESA) | NDVI and cloud mask (Fmask) at 30 m | HTTPS window reads over the box, Earthdata login | Open NASA data, no restrictions on use | Used: 1101 scenes |
| NASA POWER, Agroclimatology | NASA LaRC | Daily rain and temperature since 1991, about 0.5 degree grid | REST API, no login | Open NASA data, no restrictions on use | Used |
| Cropland Data Layer (CDL) | USDA NASS | Crop per 30 m pixel per year, with class names and colours | National zip per year, cropped to the box | Public domain (USDA) | Used: 2019 to 2025 |
| Soil survey (SSURGO) | USDA NRCS | Erodibility (Kw), organic matter, water-holding capacity | Soil Data Access REST query | Public domain (USDA) | Used |
| Field Crops Usual Planting and Harvesting Dates, Handbook 628 | USDA NASS | Planting and harvest weeks in `crop_traits.csv` | PDF | Public domain (USDA) | Used; table read by text extraction, to be checked by eye |
| WSU Extension EM108 ch. 5 and other extension sources | Washington State University and others | Water ranks and plan statements; listed in `pipeline/sources.json` | Web | Cited, not redistributed | Used |
| CDL accuracy tables, Washington 2023 | USDA NASS | Published accuracy shown on the methods page | Web | Public domain (USDA) | Used |
| OpenFreeMap basemap | OpenFreeMap, OpenMapTiles, OpenStreetMap contributors | Background map | Tiles, no key | ODbL for OpenStreetMap data | Used |
| USGS Imagery Only | USGS The National Map | Aerial photo layer | Tiles, no key | Public domain (USGS) | Used |
| NAIP aerial photos | USDA | Spot check of bare fields | Public | Public domain (USDA) | Not used yet: spot check not done |

## Fallbacks used

- **CDL:** the CropScape `GetCDLFile` service timed out and then returned HTTP 500 on 14 November 2026. We used the handoff's fallback: the national 30 m file for each year from USDA NASS, cropped to the study box (`pipeline/fetch_cdl.sh`).
- **CDL code names:** `cdl_codes_names.xlsx` was not at its old address. Names and colours come from the attribute table inside each national zip instead.

## Download log

| File | URL | Date fetched | Size | Licence |
|------|-----|--------------|------|---------|
| `data/raw/power/power_daily_-117.35_46.8_1991_2025.json` | https://power.larc.nasa.gov/api/temporal/daily/point?parameters=PRECTOTCORR,T2M_MAX,T2M_MIN&community=AG&longitude=-117.35&latitude=46.8&start=19910101&end=20251231&format=JSON | 2026-11-14 | 624,996 bytes | Open NASA data |
| `data/raw/cdl/2019_30m_cdls.zip` | https://www.nass.usda.gov/sites/default/files/Research_and_Science/Cropland/Release/datasets/2019_30m_cdls.zip | 2026-11-14 | 1,964,882,898 bytes | Public domain (USDA) |
| `data/raw/cdl/2020_30m_cdls.zip` | https://www.nass.usda.gov/sites/default/files/Research_and_Science/Cropland/Release/datasets/2020_30m_cdls.zip | 2026-11-14 | 2,007,640,337 bytes | Public domain (USDA) |
| `data/raw/cdl/2021_30m_cdls.zip` | https://www.nass.usda.gov/sites/default/files/Research_and_Science/Cropland/Release/datasets/2021_30m_cdls.zip | 2026-11-14 | 2,021,909,155 bytes | Public domain (USDA) |
| `data/raw/cdl/2022_30m_cdls.zip` | https://www.nass.usda.gov/sites/default/files/Research_and_Science/Cropland/Release/datasets/2022_30m_cdls.zip | 2026-11-14 | 2,070,138,298 bytes | Public domain (USDA) |
| `data/raw/cdl/2023_30m_cdls.zip` | https://www.nass.usda.gov/sites/default/files/Research_and_Science/Cropland/Release/datasets/2023_30m_cdls.zip | 2026-11-14 | 2,059,094,665 bytes | Public domain (USDA) |
| `data/raw/cdl/2024_30m_cdls.zip` | https://www.nass.usda.gov/sites/default/files/Research_and_Science/Cropland/Release/datasets/2024_30m_cdls.zip | 2026-11-14 | 1,656,243,429 bytes | Public domain (USDA) |
| `data/raw/cdl/2025_30m_cdls.zip` | https://www.nass.usda.gov/sites/default/files/Research_and_Science/Cropland/Release/datasets/2025_30m_cdls.zip | 2026-11-14 | 1,887,184,211 bytes | Public domain (USDA) |
| `data/raw/hls/*.npz` (1101 files) | NDVI and Fmask windows from `https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/`; every scene's URLs are listed in `data/raw/hls/scenes_<year>.json` | 2026-11-14 | 415,044,753 bytes | Open NASA data |
| `data/work/soil.json` | `https://sdmdataaccess.sc.egov.usda.gov/Tabular/post.rest`, queries in `pipeline/soil.py` | 2026-11-14 | 58,423 bytes | Public domain (USDA) |
