"""Download CDL years for the study box and build approximate field outlines."""

import json
import zipfile

import geopandas as gpd
import numpy as np
import rasterio
from rasterio import features
from rasterio.warp import transform_bounds
from rasterio.windows import from_bounds
from shapely.geometry import shape

from pipeline import config

# CropScape's GetCDLFile service was returning errors on 14 Nov 2026, so we use
# the fallback: the national file from USDA NASS (pipeline/fetch_cdl.sh),
# cropped to the study box.
CDL_DIR = config.RAW_DIR / "cdl"

FALLOW = 61
# CDL codes that are cropland. Everything else (grass, forest, towns, water)
# is left out of the field outlines.
CROP_CODES = np.array(sorted(set(range(1, 62)) | set(range(66, 78)) | set(range(204, 255))))


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
        profile = dict(
            driver="GTiff",
            dtype=data.dtype,
            count=1,
            crs=src.crs,
            height=data.shape[0],
            width=data.shape[1],
            transform=src.window_transform(window),
            compress="deflate",
        )
    with rasterio.open(out, "w", **profile) as dst:
        dst.write(data, 1)
    return out


def class_table(year):
    """Crop names and map colours for each CDL code, read from the attribute
    table USDA ships inside the national zip."""
    out = CDL_DIR / "cdl_classes.json"
    if out.exists():
        return {int(k): v for k, v in json.loads(out.read_text()).items()}
    zpath = national_zip(year)
    with zipfile.ZipFile(zpath) as z:
        inner = next(n for n in z.namelist() if n.lower().endswith(".vat.dbf"))
    table = gpd.read_file(f"/vsizip/{zpath}/{inner}")
    cols = {c.upper(): c for c in table.columns}
    classes = {}
    for _, row in table.iterrows():
        name = row[cols["CLASS_NAME"]]
        if not isinstance(name, str) or not name.strip():
            continue
        rgb = [row[cols[c]] for c in ("RED", "GREEN", "BLUE")]
        if max(rgb) <= 1:  # some years store colours as 0 to 1
            rgb = [v * 255 for v in rgb]
        classes[int(row[cols["VALUE"]])] = {
            "name": name.strip(),
            "color": "#%02x%02x%02x" % tuple(int(round(v)) for v in rgb),
        }
    out.write_text(json.dumps(classes, indent=1))
    return classes


def read_years(years, box):
    """CDL for each year as one array [year, row, col], plus the grid."""
    layers = []
    for year in years:
        with rasterio.open(crop_to_box(year, box)) as src:
            layers.append(src.read(1))
            transform, crs = src.transform, src.crs
    return np.stack(layers), transform, crs


def build_fields(years, box):
    """Approximate field outlines: touching pixels that grew the same crops in
    each of config.FIELD_YEARS, at least MIN_FIELD_HECTARES in size.

    Returns (fields GeoDataFrame in lon/lat, label raster on the CDL grid,
    crop history table [field, year] of codes with 0 meaning mixed, shares)."""
    cdl, transform, crs = read_years(years, box)
    seg_idx = [list(years).index(y) for y in config.FIELD_YEARS]
    cleaned = [features.sieve(cdl[i], size=config.CDL_SPECKLE_PIXELS, connectivity=4) for i in seg_idx]
    cropland = np.isin(cleaned[-1], CROP_CODES)
    # One number per pixel that encodes its crop in every segmentation year.
    key = np.zeros(cdl.shape[1:], dtype=np.int32)
    for layer in cleaned:
        key = key * 256 + layer.astype(np.int32)

    pixel_ha = abs(transform.a * transform.e) / 10_000
    geoms = []
    for geom, _ in features.shapes(key, mask=cropland, connectivity=4, transform=transform):
        poly = shape(geom)
        if poly.area / 10_000 >= config.MIN_FIELD_HECTARES:
            geoms.append(poly)
    fields = gpd.GeoDataFrame(geometry=geoms, crs=crs)
    fields["ha"] = (fields.area / 10_000).round(1)
    # Stable ids: sort north to south, then west to east.
    c = fields.geometry.centroid
    fields = fields.assign(_y=-c.y.round(-2), _x=c.x).sort_values(["_y", "_x"]).drop(columns=["_y", "_x"])
    fields = fields.reset_index(drop=True)
    fields["id"] = [f"f{i + 1:04d}" for i in range(len(fields))]

    labels = features.rasterize(
        ((g, i + 1) for i, g in enumerate(fields.geometry)), out_shape=key.shape, transform=transform, dtype="int32"
    )
    # Most common crop per field per year.
    n = len(fields)
    inside = labels > 0
    history = np.zeros((n, len(years)), dtype=np.int16)
    shares = np.zeros((n, len(years)), dtype=np.float32)
    size = np.bincount(labels[inside], minlength=n + 1)[1:]
    for yi in range(len(years)):
        counts = np.bincount(
            (labels[inside] - 1) * 256 + cdl[yi][inside], minlength=n * 256
        ).reshape(n, 256)
        top = counts.argmax(axis=1)
        share = counts.max(axis=1) / np.maximum(size, 1)
        history[:, yi] = np.where(share >= config.MIN_CROP_SHARE, top, 0)
        shares[:, yi] = share
    assert abs(size.sum() * pixel_ha - fields.ha.sum()) / fields.ha.sum() < 0.05
    return fields, history, shares


def run():
    years = list(config.YEARS)
    fields, history, shares = build_fields(years, config.STUDY_BOX)
    config.WORK_DIR.mkdir(parents=True, exist_ok=True)
    fields.to_file(config.WORK_DIR / "fields.gpkg", driver="GPKG")
    np.savez(config.WORK_DIR / "crop_history.npz", years=np.array(years), history=history, shares=shares)
    classes = class_table(years[-1])
    print(f"{len(fields)} fields, {fields.ha.sum():.0f} ha, median {fields.ha.median():.0f} ha")
    latest = history[:, -1]
    for code in np.argsort(-np.bincount(latest, minlength=256))[:8]:
        name = classes.get(int(code), {}).get("name", "mixed")
        print(f"  {years[-1]} {name}: {(latest == code).sum()} fields")
    return fields, history


if __name__ == "__main__":
    run()
