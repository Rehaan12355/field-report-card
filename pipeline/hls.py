"""Read HLS greenness windows over the study box and make weekly NDVI per field."""

from datetime import datetime

import earthaccess
import numpy as np
import rasterio
from rasterio.warp import transform_bounds
from rasterio.windows import from_bounds

from pipeline import config

PRODUCTS = ("HLSL30_VI", "HLSS30_VI")

# Fmask bits that make a pixel unusable: cloud, next to cloud, cloud shadow.
FMASK_CLOUD_BITS = 0b00001110
FMASK_SNOW_BIT = 0b00010000
FMASK_FILL = 255

# GDAL reads the Earthdata login from ~/.netrc and needs a cookie file to
# follow the login redirect. Only the small window we ask for is downloaded.
_COOKIES = str(config.RAW_DIR / "earthdata_cookies.txt")
GDAL_ENV = {
    "GDAL_HTTP_COOKIEFILE": _COOKIES,
    "GDAL_HTTP_COOKIEJAR": _COOKIES,
    "GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR",
    "CPL_VSIL_CURL_ALLOWED_EXTENSIONS": "TIF",
    "GDAL_HTTP_MAX_RETRY": "5",
    "GDAL_HTTP_RETRY_DELAY": "2",
}


def search(box, start, end, tile=None):
    """Find HLS vegetation index scenes over the box. Returns one dict per
    scene with its id, product, date and a URL for each layer."""
    earthaccess.login(strategy="netrc")
    scenes = []
    for product in PRODUCTS:
        for g in earthaccess.search_data(short_name=product, bounding_box=box, temporal=(start, end)):
            # Scene ids look like HLS-VI.S30.T11TMM.2024005T185801.v2.0
            scene_id = g["umm"]["GranuleUR"]
            parts = scene_id.split(".")
            if tile and parts[2] != tile:
                continue
            scenes.append(
                {
                    "id": scene_id,
                    "product": product,
                    "tile": parts[2],
                    "date": datetime.strptime(parts[3][:7], "%Y%j").date(),
                    "links": {u.rsplit(".", 2)[-2]: u for u in g.data_links()},
                }
            )
    return sorted(scenes, key=lambda s: (s["date"], s["id"]))


def read_window(url, box):
    """Read only the part of a remote HLS layer that covers the box."""
    with rasterio.Env(**GDAL_ENV):
        with rasterio.open(url) as src:
            bounds = transform_bounds("EPSG:4326", src.crs, *box)
            window = from_bounds(*bounds, transform=src.transform).round_offsets().round_lengths()
            return src.read(1, window=window), src.window_transform(window), src.crs


def clear_share(fmask):
    """Share of the box that is clear, snowy and missing in one Fmask window."""
    valid = fmask != FMASK_FILL
    cloudy = (fmask & FMASK_CLOUD_BITS) > 0
    snowy = (fmask & FMASK_SNOW_BIT) > 0
    n = fmask.size
    return {
        "clear": float(np.sum(valid & ~cloudy & ~snowy)) / n,
        "snow": float(np.sum(valid & ~cloudy & snowy)) / n,
        "missing": float(np.sum(~valid)) / n,
    }
