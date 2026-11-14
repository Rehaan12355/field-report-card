"""Download CDL years for the study box and build approximate field outlines."""

import zipfile

import rasterio
import requests
from rasterio.warp import transform_bounds
from rasterio.windows import from_bounds

from pipeline import config

# CropScape's GetCDLFile service was returning errors on 14 Nov 2026, so we use
# the fallback: the national file from USDA NASS, cropped to the study box.
NASS_URL = (
    "https://www.nass.usda.gov/sites/default/files/Research_and_Science/"
    "Cropland/Release/datasets/{year}_30m_cdls.zip"
)
CDL_DIR = config.RAW_DIR / "cdl"


def national_zip(year):
    return CDL_DIR / f"{year}_30m_cdls.zip"


def box_tif(year, box):
    return CDL_DIR / f"cdl_{year}_{'_'.join(str(v) for v in box)}.tif"


def crop_to_box(year, box):
    """Cut the study box out of a downloaded national CDL zip and save it as a
    small GeoTIFF. Returns the path."""
    out = box_tif(year, box)
    if out.exists():
        return out
    zpath = national_zip(year)
    with zipfile.ZipFile(zpath) as z:
        inner = next(n for n in z.namelist() if n.lower().endswith(".tif"))
    with rasterio.open(f"/vsizip/{zpath}/{inner}") as src:
        bounds = transform_bounds("EPSG:4326", src.crs, *box)
        window = from_bounds(*bounds, transform=src.transform).round_offsets().round_lengths()
        data = src.read(1, window=window)
        profile = src.profile.copy()
        profile.update(
            driver="GTiff",
            height=data.shape[0],
            width=data.shape[1],
            transform=src.window_transform(window),
            compress="deflate",
            tiled=False,
        )
        colormap = src.colormap(1) if src.colorinterp[0].name == "palette" else None
    profile.pop("blockxsize", None)
    profile.pop("blockysize", None)
    with rasterio.open(out, "w", **profile) as dst:
        dst.write(data, 1)
        if colormap:
            dst.write_colormap(1, colormap)
    return out
