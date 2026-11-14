"""Step 2: count clear HLS looks per month over a box for one year.

Run with: .venv/bin/python -m pipeline.clear_counts WEST SOUTH EAST NORTH YEAR TILE
"""

import json
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

from pipeline import config, hls

# A scene counts as a clear look when at least this share of the box is clear.
CLEAR_LOOK_SHARE = 0.5


def scene_shares(scene, box):
    try:
        fmask, _, _ = hls.read_window(scene["links"]["Fmask"], box)
        return scene, hls.clear_share(fmask)
    except Exception as e:
        return scene, {"error": repr(e)}


def main(box, year, tile):
    t0 = time.time()
    scenes = hls.search(box, f"{year}-01-01", f"{year}-12-31", tile=tile)
    with ThreadPoolExecutor(8) as pool:
        results = list(pool.map(lambda s: scene_shares(s, box), scenes))
    clear, snowy, errors = Counter(), Counter(), []
    rows = []
    for scene, shares in results:
        if "error" in shares:
            errors.append((scene["id"], shares["error"]))
            continue
        m = scene["date"].month
        if shares["clear"] >= CLEAR_LOOK_SHARE:
            clear[m] += 1
        if shares["snow"] >= CLEAR_LOOK_SHARE:
            snowy[m] += 1
        rows.append({"id": scene["id"], "date": str(scene["date"]), **{k: round(v, 3) for k, v in shares.items()}})
    summary = {
        "box": box,
        "year": year,
        "tile": tile,
        "scenes": len(scenes),
        "read_errors": len(errors),
        "seconds": round(time.time() - t0),
        "clear_looks_by_month": {m: clear[m] for m in range(1, 13)},
        "snowy_looks_by_month": {m: snowy[m] for m in range(1, 13)},
    }
    out = config.RAW_DIR / f"clear_counts_{tile}_{year}_{'_'.join(str(v) for v in box)}.json"
    out.write_text(json.dumps({"summary": summary, "scenes": rows, "errors": errors}, indent=1))
    print(json.dumps(summary, indent=1))
    for e in errors[:3]:
        print("ERROR", e)


if __name__ == "__main__":
    a = sys.argv[1:]
    main(tuple(float(v) for v in a[:4]), int(a[4]), a[5])
