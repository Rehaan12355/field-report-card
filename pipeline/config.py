"""Settings shared by every pipeline step."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
WORK_DIR = ROOT / "data" / "work"
WEB_DATA_DIR = ROOT / "web" / "public" / "data"

# Map centre for the demo county (Whitman County, Washington): lon, lat.
COUNTY_CENTER = (-117.52, 46.90)

# The study area: all of Whitman County, Washington. The outline is the US
# Census Bureau county boundary (TIGERweb, GEOID 53075, fetched 14 Nov 2026).
REGION_NAME = "Whitman County, Washington"
BOUNDARY_FILE = ROOT / "pipeline" / "whitman_county.geojson"
# Box around the county as (west, south, east, north) in degrees.
STUDY_BOX = (-118.25, 46.416, -117.039, 47.261)
# HLS tiles that together cover the county.
HLS_TILES = ("T11TMM", "T11TMN")
# The first build covered only this box between Colfax and Pullman.
PILOT_BOX = (-117.48, 46.71, -117.22, 46.89)

YEARS = range(2019, 2026)

# A week is bare when the field's median NDVI is below this.
NDVI_BARE_THRESHOLD = 0.25
# Gaps up to this many weeks are filled by linear interpolation.
MAX_GAP_WEEKS = 3
# Longer gaps (mostly cloudy winters) are bridged only when the last clear look
# before and the first after agree: both bare gives "likely bare", both green
# gives "likely green". Otherwise the weeks stay unknown. Likely weeks are
# always reported separately from weeks actually seen.
BRIDGE_AGREEING_GAPS = True
# Gaps longer than this are never bridged, even when both ends agree.
MAX_BRIDGE_WEEKS = 16

# A week is heavy rain when its total is in the top share of weeks since 1991.
HEAVY_RAIN_TOP_SHARE = 0.10
CLIMATE_BASELINE_YEARS = (1991, 2020)
HOT_DAY_C = 32.0

# Grade: weights sum to 100, cutoffs are minimum scores.
GRADE_WEIGHTS = {"bare": 40, "exposed": 30, "variety": 30}
GRADE_CUTOFFS = {"A": 80, "B": 65, "C": 50, "D": 35}

# Crop variety part of the grade: 1 crop scores 0, VARIETY_FULL_CROPS or more
# scores full marks; a legume or perennial in the history adds the bonus.
VARIETY_FULL_CROPS = 4
VARIETY_CROP_WEIGHT = 0.75
VARIETY_BONUS = 0.25

MIN_FIELD_HECTARES = 5
# Fields are groups of touching pixels that grew the same crops in each of
# these years. Using three years splits neighbours that share one year's crop.
FIELD_YEARS = (2023, 2024, 2025)
# CDL patches smaller than this many pixels are treated as speckle.
CDL_SPECKLE_PIXELS = 6
# A year's crop must cover at least this share of the field, else "mixed".
MIN_CROP_SHARE = 0.5
# A field is left off the map when the satellites saw it clearly in fewer than
# this share of weeks: too little to grade.
MIN_SEEN_SHARE = 0.25
# Field outlines are pulled in by this much before sampling satellite pixels,
# so pixels that straddle a field edge are left out.
FIELD_EDGE_BUFFER_M = 15
COVER_CROP_LAG_WEEKS = 3
# A crop needs this many field-years in the box before we trust its typical
# weekly pattern.
MIN_PROFILE_FIELD_YEARS = 15
