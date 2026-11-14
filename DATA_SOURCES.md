# Data sources

Every dataset the project uses. Each downloaded file gets a row in the log at
the bottom: URL, date fetched, size and licence. No numbers in the app come
from anywhere else.

## Study box

Not chosen yet. Set in step 2 (data access check) and recorded here with the
years used and the count of clear HLS observations per month.

## Datasets

| Data | Provider | What it gives us | Access | Licence | Status |
|------|----------|------------------|--------|---------|--------|
| HLS Vegetation Indices (HLSL30_VI, HLSS30_VI v2.0) | NASA LP DAAC (Landsat: NASA/USGS, Sentinel-2: ESA) | Greenness (NDVI) at 30 m | `earthaccess`, Earthdata login | To be recorded | Not pulled yet |
| NASA POWER, Agroclimatology | NASA LaRC | Daily temperature and rain since the 1980s, about 0.5 degree grid | REST API, no login | To be recorded | Not pulled yet |
| Cropland Data Layer (CDL) | USDA NASS | Crop per 30 m pixel per year | CropScape `GetCDLFile` | To be recorded | Not pulled yet |
| CDL code list | USDA NASS | Crop names for CDL numbers | `cdl_codes_names.xlsx` | To be recorded | Not pulled yet |
| Soil survey (SSURGO) | USDA NRCS | Erodibility, organic matter, water-holding capacity | Soil Data Access REST | To be recorded | Not checked |
| NAIP aerial photos | USDA | About 1 m photos for spot checks | Public | To be recorded | Not checked |

## Fallbacks used

None so far. If a source fails and a fallback is used, it is recorded here.

## Download log

| File | URL | Date fetched | Size | Licence |
|------|-----|--------------|------|---------|
