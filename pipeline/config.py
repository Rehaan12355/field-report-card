"""Settings shared by every pipeline step."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
WEB_DATA_DIR = ROOT / "web" / "public" / "data"

# Map centre for the demo county (Whitman County, Washington): lon, lat.
COUNTY_CENTER = (-117.52, 46.90)

# Study box as (west, south, east, north) in degrees: about 20 by 20 km of
# farmland between Colfax and Pullman. Confirmed by the team on 14 Nov 2026.
STUDY_BOX = (-117.48, 46.71, -117.22, 46.89)
HLS_TILE = "T11TMM"

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

# A week is heavy rain when its total is in the top share of weeks since 1991.
HEAVY_RAIN_TOP_SHARE = 0.10
CLIMATE_BASELINE_YEARS = (1991, 2020)
HOT_DAY_C = 32.0

# Grade: weights sum to 100, cutoffs are minimum scores.
GRADE_WEIGHTS = {"bare": 40, "exposed": 30, "variety": 30}
GRADE_CUTOFFS = {"A": 80, "B": 65, "C": 50, "D": 35}

MIN_FIELD_HECTARES = 5
COVER_CROP_LAG_WEEKS = 3
