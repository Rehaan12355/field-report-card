# Data sources

Every dataset the project uses. Each downloaded file gets a row in the log at
the bottom: URL, date fetched, size and licence. No numbers in the app come
from anywhere else.

## Study box

**Box 1, confirmed by the team on 14 November 2026.** Box 2 was checked for comparison.

| | West | South | East | North | HLS tile |
|---|---|---|---|---|---|
| Box 1 (default): Colfax to Pullman | -117.48 | 46.71 | -117.22 | 46.89 | T11TMM |
| Box 2 (compared): Endicott and LaCrosse | -117.93 | 46.76 | -117.67 | 46.94 | T11TMM |

Years planned: 2019 to 2025.

### Clear HLS looks per month, 2024

A scene counts as a clear look when at least half the box is free of cloud,
cloud shadow and snow in the HLS quality layer (Fmask). Counts cover both
Landsat (HLSL30) and Sentinel-2 (HLSS30) scenes. Four scenes per box failed to
read on the first try and are not counted; a retry of one worked, so these
were network hiccups, not missing data.

| Box | Scenes | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|-----|--------|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|
| Box 1 | 170 | 1 | 2 | 9 | 4 | 6 | 7 | 12 | 11 | 8 | 8 | 2 | 0 |
| Box 2 | 193 | 0 | 2 | 12 | 7 | 8 | 7 | 16 | 15 | 11 | 9 | 3 | 1 |

**Finding:** both boxes have almost no clear looks in December and January.
Box 2 sees a little more in the growing season but does not fix winter.

### Heavy-rain timing, NASA POWER 1991 to 2025

For the Box 1 centre (-117.35, 46.80): a heavy-rain week is one in the top 10%
of weekly rain totals, which is 28.7 mm or more (183 weeks). Their share by
month: Jan 19%, Feb 10%, Mar 10%, Apr 5%, May 6%, Jun 4%, Jul 1%, Aug 1%,
Sep 1%, Oct 5%, Nov 19%, Dec 21%.

**Finding:** 59% of heavy-rain weeks fall in November to January, the months
the satellites see least. How winter gaps are treated decides the exposed-weeks
number. The team chose to bridge long gaps when both ends agree and report
those weeks separately as "likely"; see docs/methods.md.

## Datasets

| Data | Provider | What it gives us | Access | Licence | Status |
|------|----------|------------------|--------|---------|--------|
| HLS Vegetation Indices (HLSL30_VI, HLSS30_VI v2.0) | NASA LP DAAC (Landsat: NASA/USGS, Sentinel-2: ESA) | Greenness (NDVI) at 30 m | HTTPS window reads with Earthdata login | To be recorded | Working: 319 scenes found for Box 1 in 2024, Fmask windows read |
| NASA POWER, Agroclimatology | NASA LaRC | Daily temperature and rain since the 1980s, about 0.5 degree grid | REST API, no login | To be recorded | Working: 12,784 daily values, 1991 to 2025 |
| Cropland Data Layer (CDL) | USDA NASS | Crop per 30 m pixel per year | National file from USDA NASS, cropped to the box (fallback) | To be recorded | Downloading |
| CDL code list | USDA NASS | Crop names for CDL numbers | `cdl_codes_names.xlsx` | To be recorded | Not pulled yet |
| Soil survey (SSURGO) | USDA NRCS | Erodibility, organic matter, water-holding capacity | Soil Data Access REST | To be recorded | Not checked |
| NAIP aerial photos | USDA | About 1 m photos for spot checks | Public | To be recorded | Not checked |

## Fallbacks used

- **CDL:** the CropScape `GetCDLFile` service timed out and then returned HTTP 500 on 14 November 2026. Using the handoff's fallback: the national 30 m file for each year from USDA NASS (`https://www.nass.usda.gov/sites/default/files/Research_and_Science/Cropland/Release/datasets/<year>_30m_cdls.zip`), cropped to the study box.

## Download log

| File | URL | Date fetched | Size | Licence |
|------|-----|--------------|------|---------|
| `data/raw/power/power_daily_-117.35_46.8_1991_2025.json` | https://power.larc.nasa.gov/api/temporal/daily/point?parameters=PRECTOTCORR,T2M_MAX,T2M_MIN&community=AG&longitude=-117.35&latitude=46.8&start=19910101&end=20251231&format=JSON | 2026-11-14 | 624,996 bytes | To be recorded |
