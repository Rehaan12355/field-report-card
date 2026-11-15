# Data sources

Every dataset the project uses, with each download logged at the bottom. No
number in the app comes from anywhere else. Checked on 14 November 2026.

## Study area

**All of Whitman County, Washington**, built on 14 November 2026: 6,685 fields,
326,655 hectares of cropland, 2019 to 2025. The county outline is the US Census
Bureau boundary (TIGERweb, GEOID 53075), saved as `pipeline/whitman_county.geojson`.
Two HLS tiles cover it: T11TMM (south) and T11TMN (north).

The first build covered a 20 by 20 km pilot box between Colfax and Pullman
(-117.48, 46.71, -117.22, 46.89), chosen after comparing it with a second box
near Endicott and LaCrosse. Both boxes had almost no clear views in December
and January 2024, which is why long cloudy gaps are bridged (docs/methods.md).

### Clear satellite passes per month, tile T11TMM

Passes (Landsat and Sentinel-2 together) in which at least half of the
tile's fields had a clear view.

| Year | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | 3 | 0 | 1 | 1 | 7 | 10 | 10 | 8 | 5 | 7 | 6 | 0 |
| 2020 | 1 | 1 | 3 | 7 | 6 | 4 | 8 | 11 | 7 | 5 | 2 | 2 |
| 2021 | 1 | 1 | 5 | 8 | 7 | 9 | 11 | 9 | 10 | 6 | 1 | 0 |
| 2022 | 0 | 5 | 2 | 3 | 5 | 5 | 12 | 8 | 9 | 11 | 2 | 0 |
| 2023 | 3 | 5 | 6 | 3 | 10 | 7 | 13 | 10 | 5 | 8 | 2 | 1 |
| 2024 | 0 | 1 | 9 | 4 | 5 | 7 | 13 | 11 | 7 | 8 | 2 | 0 |
| 2025 | 4 | 1 | 6 | 10 | 9 | 9 | 17 | 9 | 19 | 11 | 3 | 4 |

### NASA POWER grid cells

Each field uses the grid cell it sits in. A heavy-rain week is in the top 10%
of that cell's weekly rain totals since 1991.

| Cell centre lon | lat | Fields | Heavy-rain week, mm or more |
|---|---|---|---|
| -118.125 | 46.5 | 318 | 23.2 |
| -117.5 | 46.5 | 495 | 26.3 |
| -116.875 | 46.5 | 515 | 30.3 |
| -118.125 | 47.0 | 393 | 19.8 |
| -117.5 | 47.0 | 3,979 | 29.4 |
| -116.875 | 47.0 | 886 | 33.6 |
| -118.125 | 47.5 | 1 | 21.9 |
| -117.5 | 47.5 | 72 | 26.9 |
| -116.875 | 47.5 | 26 | 35.0 |

Pooled over the cells, 71% of heavy-rain weeks fall between November
and March, the months the satellites see least.

## Datasets

| Data | Provider | What it gives us | Access | Licence | Status |
|------|----------|------------------|--------|---------|--------|
| HLS Vegetation Indices (HLSL30_VI, HLSS30_VI v2.0) | NASA LP DAAC (Landsat: NASA/USGS, Sentinel-2: ESA) | NDVI and cloud mask (Fmask) at 30 m | HTTPS window reads over the box, Earthdata login | Open NASA data, no restrictions on use | Used: 2,954 scenes |
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
| `data/raw/cdl/2019_30m_cdls.zip` | https://www.nass.usda.gov/sites/default/files/Research_and_Science/Cropland/Release/datasets/2019_30m_cdls.zip | 2026-11-14 | 1,964,882,898 bytes | Public domain (USDA) |
| `data/raw/cdl/2020_30m_cdls.zip` | https://www.nass.usda.gov/sites/default/files/Research_and_Science/Cropland/Release/datasets/2020_30m_cdls.zip | 2026-11-14 | 2,007,640,337 bytes | Public domain (USDA) |
| `data/raw/cdl/2021_30m_cdls.zip` | https://www.nass.usda.gov/sites/default/files/Research_and_Science/Cropland/Release/datasets/2021_30m_cdls.zip | 2026-11-14 | 2,021,909,155 bytes | Public domain (USDA) |
| `data/raw/cdl/2022_30m_cdls.zip` | https://www.nass.usda.gov/sites/default/files/Research_and_Science/Cropland/Release/datasets/2022_30m_cdls.zip | 2026-11-14 | 2,070,138,298 bytes | Public domain (USDA) |
| `data/raw/cdl/2023_30m_cdls.zip` | https://www.nass.usda.gov/sites/default/files/Research_and_Science/Cropland/Release/datasets/2023_30m_cdls.zip | 2026-11-14 | 2,059,094,665 bytes | Public domain (USDA) |
| `data/raw/cdl/2024_30m_cdls.zip` | https://www.nass.usda.gov/sites/default/files/Research_and_Science/Cropland/Release/datasets/2024_30m_cdls.zip | 2026-11-14 | 1,656,243,429 bytes | Public domain (USDA) |
| `data/raw/cdl/2025_30m_cdls.zip` | https://www.nass.usda.gov/sites/default/files/Research_and_Science/Cropland/Release/datasets/2025_30m_cdls.zip | 2026-11-14 | 1,887,184,211 bytes | Public domain (USDA) |
| `data/raw/power/power_daily_<lon>_<lat>_1991_2025.json` (9 files) | `https://power.larc.nasa.gov/api/temporal/daily/point?parameters=PRECTOTCORR,T2M_MAX,T2M_MIN&community=AG&longitude=<lon>&latitude=<lat>&start=19910101&end=20251231&format=JSON`, one per grid cell above | 2026-11-14 | 6,251,254 bytes | Open NASA data |
| `data/raw/hls_county/<tile>/*.npz` (2,954 files) | NDVI and Fmask windows from `https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/`; every scene's URLs are listed in `data/raw/hls_county/scenes_<year>.json` | 2026-11-14 | 11,007,699,178 bytes | Open NASA data |
| `data/work/soil.json` | `https://sdmdataaccess.sc.egov.usda.gov/Tabular/post.rest`, queries in `pipeline/soil.py` | 2026-11-14 | 660,500 bytes | Public domain (USDA) |
| `pipeline/whitman_county.geojson` | `https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer/1/query` with `GEOID='53075'` | 2026-11-14 | 191,899 bytes | Public domain (US Census Bureau) |
