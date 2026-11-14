"""Read HLS greenness windows over the study box and make weekly NDVI per field."""

import json
import time
import warnings
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import earthaccess
import numpy as np
import pandas as pd
import rasterio
from rasterio import features
from rasterio.warp import transform_bounds
from rasterio.windows import Window, from_bounds

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
            # Keep to the part of the box this tile actually covers.
            window = window.intersection(Window(0, 0, src.width, src.height))
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


HLS_DIR = config.RAW_DIR / "hls_county"


def _read_with_retry(url, box, tries=4):
    for attempt in range(tries):
        try:
            return read_window(url, box)
        except rasterio.errors.RasterioIOError:
            if attempt == tries - 1:
                raise
            time.sleep(2 * (attempt + 1))


def cache_scene(scene, box):
    """Save one scene's NDVI and Fmask windows over the box to
    data/raw/hls/<tile>. NDVI stays as stored by NASA (integer, scale 0.0001,
    fill -19999)."""
    out = HLS_DIR / scene["tile"] / f"{scene['id']}.npz"
    if out.exists():
        return "cached"
    ndvi, transform, crs = _read_with_retry(scene["links"]["NDVI"], box)
    fmask, _, _ = _read_with_retry(scene["links"]["Fmask"], box)
    tmp = out.with_suffix(".tmp.npz")
    np.savez_compressed(
        tmp, ndvi=ndvi, fmask=fmask, transform=np.array(transform)[:6], crs=crs.to_string(), date=str(scene["date"])
    )
    tmp.rename(out)  # a half-written file never looks finished
    return "downloaded"


def cache_years(box, years, tiles):
    """Download every scene over the box for the given years and tiles. Safe
    to rerun: scenes already saved are skipped."""
    for tile in tiles:
        (HLS_DIR / tile).mkdir(parents=True, exist_ok=True)
    for year in years:
        scenes = [s for s in search(box, f"{year}-01-01", f"{year}-12-31") if s["tile"] in tiles]
        (HLS_DIR / f"scenes_{year}.json").write_text(
            json.dumps([{**s, "date": str(s["date"])} for s in scenes], indent=1)
        )
        results, failed = Counter(), []

        def one(scene):
            try:
                return cache_scene(scene, box)
            except Exception as e:
                failed.append((scene["id"], repr(e)[:200]))
                return "failed"

        with ThreadPoolExecutor(12) as pool:
            results.update(pool.map(one, scenes))
        print(year, len(scenes), "scenes", dict(results), flush=True)
        for f in failed:
            print("  FAILED", *f, flush=True)


WEEKS = 52
NDVI_FILL = -19999
NDVI_SCALE = 0.0001
# A field counts as seen in a scene when at least this share of its sampled
# pixels are clear (or, for a snow reading, snowy).
MIN_FIELD_SHARE = 0.5
# Fewest satellite pixels a field needs to be sampled at all.
MIN_FIELD_PIXELS = 5


def week_of_year(date):
    """Week 0 to 51. Week 51 takes the last 8 or 9 days of the year."""
    return min((date.timetuple().tm_yday - 1) // 7, WEEKS - 1)


def field_pixels(fields):
    """Which HLS pixel belongs to which field: an array on the HLS grid holding
    the field number (1-based) or 0. Outlines are pulled in first so edge
    pixels that mix two fields are left out."""
    first = np.load(next(iter(sorted(HLS_DIR.glob("*.npz")))))
    transform = rasterio.Affine(*first["transform"])
    local = fields.to_crs(str(first["crs"]))
    inner = local.geometry.buffer(-config.FIELD_EDGE_BUFFER_M)
    shape = first["ndvi"].shape
    shapes = [(g, i + 1) for i, g in enumerate(inner) if not g.is_empty]
    labels = features.rasterize(shapes, out_shape=shape, transform=transform, dtype="int32")
    # Narrow fields can vanish when pulled in. Sample those from the full
    # outline instead, without taking pixels from a neighbour.
    counts = np.bincount(labels.reshape(-1), minlength=len(fields) + 1)[1:]
    thin = [(g, i + 1) for i, g in enumerate(local.geometry) if counts[i] < MIN_FIELD_PIXELS]
    if thin:
        full = features.rasterize(thin, out_shape=shape, transform=transform, dtype="int32")
        labels = np.where((labels == 0) & (full > 0), full, labels)
    return labels


def weekly_ndvi(fields, years):
    """Median NDVI per field per week from the cached scenes.

    Returns ndvi [field, year, week] (NaN where no clear look), snow
    [field, year, week] (True where the only looks that week were snowy) and
    looks [year, month] (count of scenes with at least half the fields seen)."""
    labels = field_pixels(fields)
    n = len(fields)
    inside = labels > 0
    fid = labels[inside] - 1
    size = np.bincount(fid, minlength=n)
    years = list(years)
    sums = [[[] for _ in range(WEEKS)] for _ in years]
    snows = np.zeros((n, len(years), WEEKS), dtype=bool)
    looks = np.zeros((len(years), 12), dtype=int)
    for path in sorted(HLS_DIR.glob("*.npz")):
        scene = np.load(path)
        date = datetime.strptime(str(scene["date"]), "%Y-%m-%d").date()
        if date.year not in years:
            continue
        yi, w = years.index(date.year), week_of_year(date)
        ndvi, fmask = scene["ndvi"][inside], scene["fmask"][inside]
        valid = (ndvi != NDVI_FILL) & (fmask != FMASK_FILL)
        cloudy = (fmask & FMASK_CLOUD_BITS) > 0
        snowy = (fmask & FMASK_SNOW_BIT) > 0
        clear = valid & ~cloudy & ~snowy
        n_clear = np.bincount(fid[clear], minlength=n)
        n_snow = np.bincount(fid[valid & ~cloudy & snowy], minlength=n)
        seen = (n_clear >= np.maximum(5, MIN_FIELD_SHARE * size)) & (size > 0)
        snows[:, yi, w] |= (n_snow >= np.maximum(5, MIN_FIELD_SHARE * size)) & (size > 0)
        if seen.any():
            med = pd.Series(ndvi[clear].astype(np.float32) * NDVI_SCALE).groupby(fid[clear]).median()
            row = np.full(n, np.nan, dtype=np.float32)
            row[med.index.values] = med.values
            row[~seen] = np.nan
            sums[yi][w].append(row)
        if seen.sum() >= 0.5 * n:
            looks[yi, date.month - 1] += 1
    out = np.full((n, len(years), WEEKS), np.nan, dtype=np.float32)
    for yi in range(len(years)):
        for w in range(WEEKS):
            if sums[yi][w]:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", RuntimeWarning)  # all-NaN columns
                    out[:, yi, w] = np.nanmedian(np.stack(sums[yi][w]), axis=0)
    snows &= np.isnan(out)
    return out, snows, looks, size


def run(fields):
    years = list(config.YEARS)
    ndvi, snow, looks, size = weekly_ndvi(fields, years)
    np.savez_compressed(
        config.WORK_DIR / "weekly.npz", years=np.array(years), ndvi=ndvi, snow=snow, looks=looks, pixels=size
    )
    seen = ~np.isnan(ndvi)
    print(f"weekly NDVI: {seen.mean():.0%} of field-weeks seen, {snow.mean():.1%} snowy")
    return ndvi, snow, size


if __name__ == "__main__":
    cache_years(config.STUDY_BOX, config.YEARS, config.HLS_TILES)
