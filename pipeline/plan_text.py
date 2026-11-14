"""Plain-language text for the grade and the three plans.

Numbers in these sentences come from the field's own record. Statements about
farming practice carry a source id from SOURCES; anything we could not source
is listed as a data gap instead of being asserted.
"""

from collections import Counter

from pipeline import config
from pipeline.cdl import FALLOW

REVIEW_LINE = "Check with your local extension office or conservation district before changing practice."

# Filled from pipeline/sources.json by run.py so the web app can link them.
SOURCES = {}

# Relative effect on water and income against the current rotation:
# -1 worse, 0 about the same, +1 better, None not known.
TITLES = {"current": "Keep the current rotation", "cover": "Add a cover crop", "rotation": "Change the rotation"}


def weeks(x):
    n = round(x)
    return f"{n} week" if n == 1 else f"{n} weeks"


def reason(plan):
    c = plan["counts"]
    text = f"bare about {weeks(c['bare'])} a year"
    if c["bare_likely"] >= 0.5:
        text += f" ({round(c['bare_seen'])} seen, {round(c['bare_likely'])} likely)"
    if c["exposed"] >= 0.5:
        text += f", {round(c['exposed'])} of them during heavy rain"
    else:
        text += ", almost none during heavy rain"
    return text


def rotation_summary(crops, ctx):
    counts = Counter(crops)
    parts = [f"{ctx['crops'][c]['name'].lower()} in {n} of {len(crops)} years" for c, n in counts.most_common()]
    return ", ".join(parts)


def cite(*ids):
    return [i for i in ids if i in SOURCES]


WATER_RANK = {"low": 0, "medium": 1, "high": 2}


def water_compare(old, new, ctx):
    """Water effect of swapping one crop for another, from the water-need
    classes in crop_traits.csv."""
    a, b = ctx["crops"][old]["water_need"], ctx["crops"][new]["water_need"]
    if a is None or b is None:
        return {"effect": None, "note": "Not in our data."}
    effect = (WATER_RANK[a] > WATER_RANK[b]) - (WATER_RANK[a] < WATER_RANK[b])
    word = {1: "less water than", 0: "about the same water as", -1: "more water than"}[effect]
    new_name, old_name = ctx["crops"][new]["name"].lower(), ctx["crops"][old]["name"].lower()
    return {"effect": effect, "note": f"WSU ranks {new_name} as using {word} {old_name}."}


def describe(plan, current, ctx):
    key = plan["key"]
    c, base = plan["counts"], current["counts"]
    years = ctx["years"]
    saved = base["bare"] - c["bare"]
    saved_rain = base["exposed"] - c["exposed"]
    data_line = (
        f"Crops: USDA Cropland Data Layer, {years[0]} to {years[-1]}. Bare weeks: NASA HLS greenness "
        f"below {config.NDVI_BARE_THRESHOLD} NDVI. Heavy-rain weeks: NASA POWER."
    )
    out = {"title": TITLES[key], "review": REVIEW_LINE}

    if key == "current":
        out.update(
            rationale=f"What the field has been doing: {rotation_summary(plan['crops'], ctx)}.",
            evidence=data_line,
            benefits="No new cost and nothing to learn.",
            gaps=(
                f"About {weeks(c['unknown'])} a year were hidden by cloud or snow. "
                f"About {weeks(c['bare_likely'])} a year are counted as likely bare across cloudy gaps, not seen."
            ),
            risks=(
                "Crop residue, tillage and slope are not measured. A field with good residue cover is "
                "better protected than its bare-week count suggests."
            ),
            water={"effect": 0, "note": "No change."},
            income={"effect": 0, "note": "No change."},
            cites=[],
        )
    elif key == "cover":
        out.update(
            rationale=(
                "Plant a cover crop after harvest so the soil is not left open. We fill each bare "
                f"stretch from {config.COVER_CROP_LAG_WEEKS} weeks after it starts, and leave alone the months winter wheat is in the ground."
            ),
            evidence=data_line + " The cover is applied to this field's own bare weeks.",
            benefits=(
                f"About {round(saved)} fewer bare weeks a year, {round(max(saved_rain, 0))} of them in heavy rain."
                if saved >= 0.5
                else "Little to gain: this field has few bare weeks a cover crop could fill."
            ),
            gaps=(
                "This is a best case. We do not model whether a cover crop would come up in a dry late "
                "summer, or how much ground it would really cover."
            ),
            risks=TEXT.get("cover_risk", "How a cover crop affects soil water for the next crop is not in our data."),
            water=TEXT.get("cover_water", {"effect": None, "note": "Not in our data."}),
            income=TEXT.get("cover_income", {"effect": None, "note": "Not in our data."}),
            cites=cite("em108", "cover_water", "cover_review"),
        )
    else:
        swap = plan.get("swap_year")
        if swap is None:
            out.update(
                rationale="We found no crop to swap in that this field has not already grown.",
                evidence=data_line,
                benefits="None beyond the current rotation.",
                gaps="None added.",
                risks="None added.",
                water={"effect": 0, "note": "No change."},
                income={"effect": 0, "note": "No change."},
                cites=[],
            )
            return out
        new = plan["new_crop"]
        new_name = ctx["crops"][new]["name"].lower()
        is_legume = ctx["crops"][new]["legume"]
        old = current["crops"][swap]
        fallow = old == FALLOW
        old_name = "the fallow year" if fallow else f"one {ctx['crops'][old]['name'].lower()} year"
        gain = plan["variety"] - current["variety"]
        why = "a crop that fixes its own nitrogen" if is_legume else "a crop this field has not grown"
        tail = " and puts a crop on ground that sat empty." if fallow else ", to break up a repeated crop."
        out.update(
            rationale=f"Swap {old_name} ({years[swap]}) for {new_name}, {why}{tail}",
            evidence=(
                data_line + f" The {new_name} year uses the typical weekly pattern of "
                f"{ctx['field_years'][new]} {new_name} field-years measured in this study area."
            ),
            benefits=(
                (f"About {round(saved)} fewer bare {'week' if round(saved) == 1 else 'weeks'} a year. " if saved >= 0.5 else "")
                + ("More crop variety, which lifts the grade. " if gain > 0 else "")
                + (TEXT.get("rotation_benefit", "") if is_legume else "")
            ).strip()
            or "Little change in bare weeks.",
            gaps=(
                "The swapped year is a typical pattern, not a forecast for this field. Effects on the "
                "following crop are not modelled."
            ),
            risks=TEXT.get("rotation_risk", "Markets, equipment and disease history for the new crop are not in our data."),
            water=(
                TEXT.get("rotation_water_fallow" if is_legume else "rotation_water_fallow_other", {"effect": None, "note": "Not in our data."})
                if fallow
                else water_compare(old, new, ctx)
            ),
            income=TEXT.get("rotation_income_fallow" if fallow else "rotation_income", {"effect": None, "note": "Not in our data."}),
            cites=cite("em108") if is_legume else [],
        )
    return out


# Sourced statements, loaded from pipeline/sources.json by run.py. Each entry
# there names the source it rests on.
TEXT = {}
