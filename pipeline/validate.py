"""Run the validation checks and write validation.json."""

import json
from collections import Counter

import numpy as np

from pipeline import config, export, power, score
from pipeline.cdl import FALLOW
from pipeline.hls import WEEKS

# A field-year needs this many clear weeks before we compare its curve.
MIN_WEEKS_FOR_CURVE = 15


def crop_curve_check(ndvi, history, profiles, classes):
    """Does each field-year's greenness curve look most like the typical curve
    of the crop USDA says it grew? Compared against every major crop's median
    curve, on the weeks that field-year was actually seen."""
    codes = sorted(profiles)
    curves = np.stack([profiles[c]["ndvi"] for c in codes])  # [crop, week]
    hits, totals = Counter(), Counter()
    for i, yi in zip(*np.nonzero(np.isin(history, codes))):
        row = ndvi[i, yi]
        seen = ~np.isnan(row)
        if seen.sum() < MIN_WEEKS_FOR_CURVE:
            continue
        ok = seen & ~np.isnan(curves).any(axis=0)
        if ok.sum() < MIN_WEEKS_FOR_CURVE:
            continue
        rmse = np.sqrt(((curves[:, ok] - row[ok]) ** 2).mean(axis=1))
        truth = int(history[i, yi])
        totals[truth] += 1
        hits[truth] += codes[int(rmse.argmin())] == truth
    crops = [
        {
            "crop": classes[c]["name"],
            "color": classes[c]["color"],
            "field_years": totals[c],
            "matched": hits[c],
            "share": round(hits[c] / totals[c], 3) if totals[c] else None,
            "curve": [None if np.isnan(v) else round(float(v), 3) for v in profiles[c]["ndvi"]],
        }
        for c in codes
    ]
    total = sum(totals.values())
    return {
        "crops": crops,
        "field_years": total,
        "matched": sum(hits.values()),
        "share": round(sum(hits.values()) / total, 3) if total else None,
        "chance": round(1 / len(codes), 3),
    }


def fallow_check(statuses, history):
    """Fields USDA marks as fallow should be bare far longer that year."""
    bare = np.isin(statuses, (score.BARE, score.LIKELY_BARE)).sum(axis=2)  # [field, year]
    fallow = history == FALLOW
    cropped = (history != FALLOW) & (history != 0)
    stats = lambda m: {
        "field_years": int(m.sum()),
        "median_bare_weeks": float(np.median(bare[m])) if m.any() else None,
        "mean_bare_weeks": round(float(bare[m].mean()), 1) if m.any() else None,
    }
    return {"fallow": stats(fallow), "cropped": stats(cropped)}


def threshold_test(fields, history, ndvi, snow, heavy, classes, traits, base_records, base_statuses):
    """Rerun the grades with a lower and a higher bare threshold."""
    order = "ABCDF"
    base = [r["plans"][0] for r in base_records]
    out = {}
    for threshold in (0.20, 0.30):
        records, extra = export.build(fields, history, ndvi, snow, heavy, classes, traits, threshold)
        fallow = fallow_check(extra["statuses"], history)
        moved = Counter()
        for b, r in zip(base, records):
            moved[abs(order.index(b["grade"]) - order.index(r["plans"][0]["grade"]))] += 1
        n = len(base)
        out[f"{threshold:.2f}"] = {
            "same_grade": round(moved[0] / n, 3),
            "one_letter": round(moved[1] / n, 3),
            "two_or_more": round(sum(v for k, v in moved.items() if k >= 2) / n, 3),
            "mean_bare_weeks": round(float(np.mean([r["plans"][0]["counts"]["bare"] for r in records])), 1),
            "fallow_median_bare_weeks": fallow["fallow"]["median_bare_weeks"],
            "cropped_median_bare_weeks": fallow["cropped"]["median_bare_weeks"],
        }
    out[f"{config.NDVI_BARE_THRESHOLD:.2f}"] = {
        "same_grade": 1.0,
        "one_letter": 0.0,
        "two_or_more": 0.0,
        "mean_bare_weeks": round(float(np.mean([p["counts"]["bare"] for p in base])), 1),
        "fallow_median_bare_weeks": fallow_check(base_statuses, history)["fallow"]["median_bare_weeks"],
        "cropped_median_bare_weeks": fallow_check(base_statuses, history)["cropped"]["median_bare_weeks"],
    }
    return dict(sorted(out.items()))


def plan_checks(records):
    cur = np.array([r["plans"][0]["counts"]["bare"] for r in records])
    cov = np.array([r["plans"][1]["counts"]["bare"] for r in records])
    exposed_ok = all(
        p["counts"]["exposed"] <= p["counts"]["bare"] + 1e-9 for r in records for p in r["plans"]
    )
    return {
        "fields": len(records),
        "cover_fewer_bare": int((cov < cur).sum()),
        "cover_same_bare": int((cov == cur).sum()),
        "cover_more_bare": int((cov > cur).sum()),
        "exposed_never_exceeds_bare": bool(exposed_ok),
        "mean_bare_current": round(float(cur.mean()), 1),
        "mean_bare_cover": round(float(cov.mean()), 1),
    }


def rain_season_check():
    df = power.daily(config.STUDY_BOX, list(config.YEARS)[-1])
    weekly = power.weekly_rain(df)
    threshold = np.nanquantile(weekly.values, 1 - config.HEAVY_RAIN_TOP_SHARE)
    by_week = (weekly.values >= threshold).sum(axis=0)
    # Week w starts on day 7w+1; day 305 is 1 November, day 90 is 31 March.
    wet = np.array([(w * 7 + 1 >= 305) or (w * 7 + 1 <= 90) for w in range(WEEKS)])
    return {
        "since": int(weekly.index.min()),
        "heavy_weeks": int(by_week.sum()),
        "share_november_to_march": round(float(by_week[wet].sum() / by_week.sum()), 3),
    }


def run(fields, history, ndvi, snow, heavy, classes, records, extra, looks):
    traits = export.load_traits()
    statuses = extra["statuses"]
    states = Counter(statuses.reshape(-1).tolist())
    total = statuses.size
    sources = json.loads((config.ROOT / "pipeline" / "sources.json").read_text())
    result = {
        "crop_curve_check": crop_curve_check(ndvi, history, extra["profiles"], classes),
        "bare_soil_spot_check": {
            "status": "not done",
            "note": "Needs a person to compare 20 fields against NAIP aerial photos from the same summer.",
        },
        "fallow_check": fallow_check(statuses, history),
        "threshold_test": threshold_test(fields, history, ndvi, snow, heavy, classes, traits, records, statuses),
        "plan_checks": plan_checks(records),
        "rain_season_check": rain_season_check(),
        "week_states": {
            "seen": round((states[score.GREEN] + states[score.BARE]) / total, 3),
            "likely": round((states[score.LIKELY_GREEN] + states[score.LIKELY_BARE]) / total, 3),
            "snow": round(states[score.SNOW] / total, 3),
            "unknown": round(states[score.UNKNOWN] / total, 3),
        },
        "clear_looks_by_month": {str(y): [int(v) for v in looks[yi]] for yi, y in enumerate(config.YEARS)},
        "cdl_accuracy_wa_2023": sources.get("cdl_accuracy_wa_2023"),
    }
    (config.WEB_DATA_DIR / "validation.json").write_text(json.dumps(result, indent=1))
    c = result["crop_curve_check"]
    print(f"crop curve check: {c['matched']} of {c['field_years']} field-years match ({c['share']:.0%}; chance {c['chance']:.0%})")
    print("fallow check:", result["fallow_check"])
    print("threshold test:", result["threshold_test"])
    print("plan checks:", result["plan_checks"])
    print("rain season:", result["rain_season_check"], "| week states:", result["week_states"])
    return result


