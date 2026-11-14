"""Write fields.geojson and one JSON per field for the web app."""

import csv
import json
import shutil
from collections import Counter
from datetime import date

import numpy as np

from pipeline import config, plan_text, score
from pipeline.cdl import CROP_CODES, FALLOW
from pipeline.hls import WEEKS


def load_traits():
    """crop_traits.csv as {cdl_code: {...}}. Blank cells stay None."""
    traits = {}
    with open(config.ROOT / "pipeline" / "crop_traits.csv") as f:
        for row in csv.DictReader(f):
            if not row["cdl_code"]:
                continue
            traits[int(row["cdl_code"])] = {
                "crop": row["crop"],
                "plant_week": int(row["plant_week"]) if row["plant_week"] else None,
                "harvest_week": int(row["harvest_week"]) if row["harvest_week"] else None,
                "water_need": row["water_need"] or None,
                "nitrogen_fixing": row["nitrogen_fixing"] == "yes",
                "perennial": row["perennial"] == "yes",
            }
    return traits


def pick_legume(history, traits, profiles):
    """The nitrogen-fixing crop grown most in the box, so its typical weekly
    pattern is measured from plenty of local fields."""
    counts = Counter(int(c) for c in history.reshape(-1))
    options = [c for c in profiles if traits.get(c, {}).get("nitrogen_fixing") and not traits[c]["perennial"]]
    return max(options, key=lambda c: counts[c]) if options else None


def _r(x, digits=1):
    return round(float(x), digits)


def plan_record(key, status, crops, heavy, traits, max_exposed, classes):
    counts = score.count(status, heavy)
    variety = score.variety_score(crops, traits)
    total, letter, parts = score.grade(counts, variety, max_exposed)
    return {
        "key": key,
        "weeks": ["".join(row) for row in status],
        "crops": [int(c) for c in crops],
        "counts": {k: _r(v) for k, v in counts.items()},
        "variety": _r(variety, 2),
        "score": _r(total),
        "grade": letter,
        "parts": {k: _r(v) for k, v in parts.items()},
    }


def build(fields, history, ndvi, snow, heavy, classes, traits, threshold=None):
    """Score every field and its three plans. Returns (records, extras)."""
    n, years = history.shape
    statuses = np.empty((n, years, WEEKS), dtype="<U1")
    for i in range(n):
        s, _ = score.classify(ndvi[i].reshape(-1), snow[i].reshape(-1), threshold)
        statuses[i] = s.reshape(years, WEEKS)
    profiles = score.crop_profiles(statuses, ndvi, history)
    legume = pick_legume(history, traits, profiles)
    current = [score.count(statuses[i], heavy) for i in range(n)]
    max_exposed = max(c["exposed"] for c in current)
    # Crops that could be swapped in: annual crops with a measured pattern,
    # most widely grown in the box first.
    box_counts = Counter(int(c) for c in history.reshape(-1))
    options = sorted(
        (c for c in profiles if c in CROP_CODES and c != FALLOW and not traits.get(c, {}).get("perennial")),
        key=lambda c: -box_counts[c],
    )

    records = []
    for i in range(n):
        crops = [int(c) for c in history[i]]
        plans = [plan_record("current", statuses[i], crops, heavy, traits, max_exposed, classes)]
        cover = score.cover_crop_plan(statuses[i], crops, traits)
        plans.append(plan_record("cover", cover, crops, heavy, traits, max_exposed, classes))
        new_crop = score.pick_new_crop(crops, traits, options, legume)
        rot_status, rot_crops, swap = score.rotation_plan(
            statuses[i], crops, new_crop, profiles[new_crop]["bare_share"] if new_crop else None
        )
        rotation = plan_record("rotation", rot_status, rot_crops, heavy, traits, max_exposed, classes)
        rotation["swap_year"] = swap
        rotation["new_crop"] = new_crop if swap is not None else None
        plans.append(rotation)
        records.append({"plans": plans, "ndvi": ndvi[i]})
    return records, {"statuses": statuses, "profiles": profiles, "legume": legume, "max_exposed": max_exposed}


def county_summary(statuses, heavy, ha):
    """Share of the box's cropland (by area, where the state is known) that is
    bare in an average heavy-rain week."""
    known = ~np.isin(statuses, (score.UNKNOWN, score.SNOW))
    bare = np.isin(statuses, (score.BARE, score.LIKELY_BARE))
    w = ha[:, None, None] * heavy[None, :, :]
    return float((bare * w).sum() / max((known * w).sum(), 1e-9))


def write(fields, history, ndvi, snow, heavy, rain, rain_threshold, trend, classes, looks, soil=None):
    years = list(config.YEARS)
    traits = load_traits()
    records, extra = build(fields, history, ndvi, snow, heavy, classes, traits)
    out = config.WEB_DATA_DIR
    if (out / "fields").exists():
        shutil.rmtree(out / "fields")
    (out / "fields").mkdir(parents=True)

    used = sorted({int(c) for c in history.reshape(-1)} | set(extra["profiles"]))
    crop_info = {
        c: {
            "name": classes[c]["name"] if c else "Mixed",
            "color": classes[c]["color"] if c else "#b9bdb4",
            "legume": bool(traits.get(c, {}).get("nitrogen_fixing")),
            "perennial": bool(traits.get(c, {}).get("perennial")),
            "water_need": traits.get(c, {}).get("water_need"),
        }
        for c in used
    }
    context = {
        "years": years,
        "crops": crop_info,
        "legume": extra["legume"],
        "field_years": {c: v["field_years"] for c, v in extra["profiles"].items()},
        "traits": traits,
    }

    grades = Counter()
    props = []
    for i, rec in enumerate(records):
        fid = fields.id.iloc[i]
        plans = rec["plans"]
        for plan in plans:
            plan.update(plan_text.describe(plan, plans[0], context))
            plan["reason"] = plan_text.reason(plan)
        current = plans[0]
        grades[current["grade"]] += 1
        doc = {
            "id": fid,
            "ha": float(fields.ha.iloc[i]),
            "years": years,
            "ndvi": [[None if np.isnan(v) else _r(v, 2) for v in row] for row in rec["ndvi"]],
            "plans": plans,
            "soil": soil.get(fid) if soil else None,
        }
        (out / "fields" / f"{fid}.json").write_text(json.dumps(doc, separators=(",", ":")))
        props.append(
            {
                "id": fid,
                "grade": current["grade"],
                "score": current["score"],
                "ha": float(fields.ha.iloc[i]),
                "crop": crop_info[int(history[i, -1])]["name"],
                "bare": current["counts"]["bare"],
                "exposed": current["counts"]["exposed"],
            }
        )

    web = fields.copy()
    web["geometry"] = web.geometry.simplify(12)
    web = web.to_crs(4326)[["geometry"]]
    for key in props[0]:
        web[key] = [p[key] for p in props]
    web.to_file(out / "fields.geojson", driver="GeoJSON", COORDINATE_PRECISION=5)

    ha = fields.ha.values
    meta = {
        "generated": date.today().isoformat(),
        "region": getattr(config, "REGION_NAME", "the Colfax to Pullman area of Whitman County, Washington"),
        "box": list(config.STUDY_BOX),
        "years": years,
        "fields": len(fields),
        "hectares": _r(ha.sum(), 0),
        "ndvi_threshold": config.NDVI_BARE_THRESHOLD,
        "heavy": ["".join("1" if h else "0" for h in row) for row in heavy],
        "heavy_mm": _r(rain_threshold),
        "rain": [[None if np.isnan(v) else _r(v) for v in row] for row in rain],
        "climate": trend,
        "crops": crop_info,
        "legume": extra["legume"],
        "max_exposed": _r(extra["max_exposed"]),
        "grades": {g: grades[g] for g in "ABCDF"},
        "grade_weights": config.GRADE_WEIGHTS,
        "grade_cutoffs": config.GRADE_CUTOFFS,
        "bare_in_heavy_rain_share": _r(county_summary(extra["statuses"], heavy, ha), 3),
        "clear_looks": {str(y): [int(v) for v in looks[yi]] for yi, y in enumerate(years)},
        "sources": plan_text.SOURCES,
    }
    (out / "meta.json").write_text(json.dumps(meta, indent=1))
    return records, extra, meta
