"""Compute bare weeks, exposed weeks, climate trend, grade and the three plans."""

import numpy as np

from pipeline import config
from pipeline.cdl import FALLOW
from pipeline.hls import WEEKS

# One letter per week. Capital letters are weeks the satellites saw (or a gap
# of up to MAX_GAP_WEEKS filled between two clear looks); small letters are
# inferred.
GREEN, BARE = "G", "B"
LIKELY_GREEN, LIKELY_BARE = "g", "b"
SNOW, UNKNOWN = "S", "U"
COVER = "C"  # plan only: bare week filled by a cover crop
TYPICAL_GREEN, TYPICAL_BARE = "T", "t"  # plan only: typical pattern of a swapped-in crop

BARE_LIKE = (BARE, LIKELY_BARE, TYPICAL_BARE)
WINTER_WHEAT = 24


def classify(ndvi, snow, threshold=None):
    """Turn one field's weekly NDVI (all years end to end, NaN for no clear
    look) into one status letter per week."""
    threshold = config.NDVI_BARE_THRESHOLD if threshold is None else threshold
    n = len(ndvi)
    status = np.full(n, UNKNOWN, dtype="<U1")
    seen = np.flatnonzero(~np.isnan(ndvi))
    filled = ndvi.copy()
    for i in seen:
        status[i] = BARE if ndvi[i] < threshold else GREEN
    for a, b in zip(seen[:-1], seen[1:]):
        gap = b - a - 1
        if gap == 0:
            continue
        between = slice(a + 1, b)
        if gap <= config.MAX_GAP_WEEKS:
            filled[between] = np.interp(np.arange(a + 1, b), [a, b], [ndvi[a], ndvi[b]])
            status[between] = np.where(filled[between] < threshold, BARE, GREEN)
        elif config.BRIDGE_AGREEING_GAPS and gap <= config.MAX_BRIDGE_WEEKS and status[a] == status[b]:
            status[between] = LIKELY_BARE if status[a] == BARE else LIKELY_GREEN
    # A snowy look is never bare, whatever the gap rules said.
    status[snow & np.isnan(ndvi)] = SNOW
    return status, filled


def count(status, heavy):
    """Average weeks per year in each state. status and heavy are [year, week]."""
    years = status.shape[0]
    bare_seen = (status == BARE).sum() / years
    bare_inferred = np.isin(status, (LIKELY_BARE, TYPICAL_BARE)).sum() / years
    exposed_seen = ((status == BARE) & heavy).sum() / years
    exposed_inferred = (np.isin(status, (LIKELY_BARE, TYPICAL_BARE)) & heavy).sum() / years
    return {
        "bare_seen": bare_seen,
        "bare_likely": bare_inferred,
        "bare": bare_seen + bare_inferred,
        "exposed_seen": exposed_seen,
        "exposed_likely": exposed_inferred,
        "exposed": exposed_seen + exposed_inferred,
        "unknown": np.isin(status, (UNKNOWN, SNOW)).sum() / years,
    }


def variety_score(crops, traits):
    """0 to 1: how many different crops, plus a bonus for a legume or perennial.
    Fallow and mixed years are not crops."""
    distinct = {c for c in crops if c not in (0, FALLOW)}
    spread = (min(len(distinct), config.VARIETY_FULL_CROPS) - 1) / (config.VARIETY_FULL_CROPS - 1)
    bonus = any(traits.get(c, {}).get("nitrogen_fixing") or traits.get(c, {}).get("perennial") for c in distinct)
    return max(spread, 0) * config.VARIETY_CROP_WEIGHT + bonus * config.VARIETY_BONUS


def grade(counts, variety, max_exposed):
    w = config.GRADE_WEIGHTS
    parts = {
        "bare": w["bare"] * (1 - counts["bare"] / WEEKS),
        "exposed": w["exposed"] * (1 - min(counts["exposed"] / max_exposed, 1)) if max_exposed > 0 else w["exposed"],
        "variety": w["variety"] * variety,
    }
    score = sum(parts.values())
    letter = next((g for g, cut in config.GRADE_CUTOFFS.items() if score >= cut), "F")
    return score, letter, parts


def bare_runs(flat):
    """Start and end (inclusive) of each stretch of bare weeks. Snowy and
    unknown weeks inside a stretch do not break it."""
    runs, start, last_bare = [], None, None
    for i, s in enumerate(flat):
        if s in BARE_LIKE:
            start = i if start is None else start
            last_bare = i
        elif s in (SNOW, UNKNOWN) and start is not None:
            continue
        elif start is not None:
            runs.append((start, last_bare))
            start = None
    if start is not None:
        runs.append((start, last_bare))
    return runs


def cover_crop_plan(status, crops, traits):
    """Fill bare stretches with a cover crop after an establishment lag.

    Winter wheat harvested in one year is sown the autumn before, so from its
    usual sowing week to its usual harvest week the ground belongs to the
    wheat and cannot take a cover crop. This is a best case: it assumes the
    cover crop comes up every time."""
    flat = status.reshape(-1).copy()
    wheat = traits.get(WINTER_WHEAT, {})
    sow, harvest = wheat.get("plant_week"), wheat.get("harvest_week")
    blocked = np.zeros(len(flat), dtype=bool)
    if sow is not None and harvest is not None:
        for yi, crop in enumerate(crops):
            if crop == WINTER_WHEAT:
                blocked[max((yi - 1) * WEEKS + sow, 0) : yi * WEEKS + harvest + 1] = True
    for a, b in bare_runs(flat):
        for i in range(a + config.COVER_CROP_LAG_WEEKS, b + 1):
            if blocked[i]:
                break
            if flat[i] in BARE_LIKE:
                flat[i] = COVER
    return flat.reshape(status.shape)


def pick_swap_year(crops):
    """Which year to change in the rotation plan: the latest fallow year, else
    the latest year of the field's most repeated crop."""
    crops = list(crops)
    if FALLOW in crops:
        return len(crops) - 1 - crops[::-1].index(FALLOW)
    grown = [c for c in crops if c != 0]
    if not grown:
        return None
    most = max(set(grown), key=lambda c: (grown.count(c), c))
    return len(crops) - 1 - crops[::-1].index(most)


def pick_new_crop(crops, traits, options, top_legume):
    """Which crop to swap in. options are the box's crops with a measured
    typical pattern, most widely grown first.

    A fallow year, or a rotation with no legume, gets the box's main legume.
    A rotation that already has a legume gets the most widely grown crop the
    field has not grown, to add variety."""
    has_legume = any(traits.get(c, {}).get("nitrogen_fixing") for c in crops)
    if top_legume is not None and (FALLOW in crops or not has_legume):
        return top_legume
    return next((c for c in options if c not in crops), None)


def rotation_plan(status, crops, new_crop, profile):
    """Swap one year for another crop. That year's weeks take the new crop's
    typical pattern, measured from fields in the box that grew it."""
    yi = pick_swap_year(crops)
    if yi is None or new_crop is None:
        return status.copy(), list(crops), None
    new_status = status.copy()
    new_status[yi] = np.where(profile >= 0.5, TYPICAL_BARE, TYPICAL_GREEN)
    new_crops = list(crops)
    new_crops[yi] = new_crop
    return new_status, new_crops, yi


def crop_profiles(status, ndvi, history):
    """Typical year for each crop, from every field-year in the box that grew
    it: share of known weeks that were bare, and median NDVI, per week."""
    profiles = {}
    known = ~np.isin(status, (UNKNOWN, SNOW))
    bare = np.isin(status, (BARE, LIKELY_BARE))
    for code in np.unique(history):
        if code == 0:
            continue
        pick = history == code  # [field, year]
        if pick.sum() < config.MIN_PROFILE_FIELD_YEARS:
            continue
        k = known[pick].sum(axis=0)
        with np.errstate(invalid="ignore", divide="ignore"):
            share = np.where(k > 0, bare[pick].sum(axis=0) / k, np.nan)
            import warnings

            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                median = np.nanmedian(ndvi[pick], axis=0)
        profiles[int(code)] = {"field_years": int(pick.sum()), "bare_share": share, "ndvi": median}
    return profiles
