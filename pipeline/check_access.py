"""Step 2 data access check: pull one CDL year, search HLS and call NASA POWER
for a candidate study box, and print what came back.

Run with: .venv/bin/python -m pipeline.check_access
"""

import json
import re
import sys

import earthaccess
import requests
from pyproj import Transformer

from pipeline import config

# Candidate box, (west, south, east, north): about 20 by 20 km of farmland
# between Colfax and Pullman.
BOX = (-117.48, 46.71, -117.22, 46.89)
YEAR = 2024

CDL_URL = "https://nassgeodata.gmu.edu/axis2/services/CDLService/GetCDLFile"
POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
HLS_PRODUCTS = ("HLSL30_VI", "HLSS30_VI")


def check_cdl(box, year):
    # CropScape wants the box in its own map projection (EPSG:5070).
    to_albers = Transformer.from_crs(4326, 5070, always_xy=True)
    x1, y1 = to_albers.transform(box[0], box[1])
    x2, y2 = to_albers.transform(box[2], box[3])
    r = requests.get(
        CDL_URL, params={"year": year, "bbox": f"{x1:.0f},{y1:.0f},{x2:.0f},{y2:.0f}"}, timeout=120
    )
    r.raise_for_status()
    tif_url = re.search(r"<returnURL>(.*?)</returnURL>", r.text).group(1)
    tif = requests.get(tif_url, timeout=120)
    tif.raise_for_status()
    out = config.RAW_DIR / "cdl" / f"cdl_{year}_check.tif"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(tif.content)
    return {"url": tif_url, "bytes": len(tif.content), "path": str(out)}


def check_power(box):
    lon, lat = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    params = {
        "parameters": "PRECTOTCORR,T2M_MAX,T2M_MIN",
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "start": f"{YEAR}0101",
        "end": f"{YEAR}1231",
        "format": "JSON",
    }
    r = requests.get(POWER_URL, params=params, timeout=120)
    r.raise_for_status()
    rain = r.json()["properties"]["parameter"]["PRECTOTCORR"]
    good = [v for v in rain.values() if v > -900]
    return {"url": r.url, "days": len(rain), "valid_days": len(good), "rain_mm": round(sum(good), 1)}


def check_hls(box, year):
    earthaccess.login(strategy="netrc")
    out = {}
    for product in HLS_PRODUCTS:
        granules = earthaccess.search_data(
            short_name=product, bounding_box=box, temporal=(f"{year}-01-01", f"{year}-12-31")
        )
        tiles = sorted({g["umm"]["GranuleUR"].split(".")[2] for g in granules})
        files = sorted({u.rsplit(".", 2)[-2] for u in granules[0].data_links()}) if granules else []
        out[product] = {"granules": len(granules), "tiles": tiles, "files": files}
    return out


if __name__ == "__main__":
    checks = {
        "cdl": lambda: check_cdl(BOX, YEAR),
        "power": lambda: check_power(BOX),
        "hls": lambda: check_hls(BOX, YEAR),
    }
    failed = False
    for name, run in checks.items():
        try:
            print(name, json.dumps(run(), indent=1))
        except Exception as e:  # report every source, even if one fails
            failed = True
            print(name, "FAILED:", repr(e))
    sys.exit(1 if failed else 0)
