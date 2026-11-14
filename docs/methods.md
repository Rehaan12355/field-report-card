# Methods

The live methods page shows the same method with the latest check results:
https://rehaan12355.github.io/field-report-card/methods.html

The grade is a screening tool, not a soil test. The method uses data that
covers the contiguous US; this demo runs it on one study box in Whitman
County, Washington.

## Fields

There is no free national map of field boundaries. A field here is a group of
touching 30 m pixels that grew the same crops in each of 2023, 2024 and 2025
in the USDA Cropland Data Layer, at least 5 hectares in size. Outlines are
approximate. Outlines outside the study box, or seen clearly in under 25% of
weeks, are left off.

## Crop history

For each field and year, the most common CDL crop. If no crop covers half the
field, the year is "mixed".

## Bare weeks

1. For each field and satellite pass, take the median NDVI of pixels that the
   HLS quality layer (Fmask) marks free of cloud, cloud shadow and snow.
   Pixels within 15 m of the field edge are left out.
2. Keep one value per week (52 weeks a year; the last takes the extra days).
3. A week is bare when NDVI is below 0.25.

NDVI sees living green plants. "Bare" means no green cover; it cannot tell
tilled soil from soil under dry stubble.

Cloud hides these fields for most of December and January, so gaps are
handled in two tiers:

- Gaps of up to 3 weeks are filled by a straight line between the clear views
  on either side.
- Longer gaps, up to 16 weeks, are bridged only when both ends agree. Both
  bare: "likely bare". Both green: "likely green". Otherwise "unknown".

Likely weeks are an inference. They are drawn hatched and counted separately.
Snowy views never count as bare.

## Rain risk

A heavy-rain week is in the top 10% of weekly rain totals since 1991 in NASA
POWER. An exposed week is a bare week that is also a heavy-rain week.

## Climate trend

The last 10 years against 1991 to 2020: days above 32 C, last spring frost,
first fall frost, yearly rain.

## Grade

```
score = 40 * (1 - bare_weeks / 52)
      + 30 * (1 - exposed_weeks / most_exposed_field_in_the_box)
      + 30 * crop_variety
crop_variety = 0.75 * (distinct crops - 1) / 3, capped, + 0.25 if a legume or perennial
grade: A >= 80, B >= 65, C >= 50, D >= 35, F below
```

Weights live in `pipeline/config.py` and are a starting point.

## The three plans

1. **Keep the current rotation.**
2. **Add a cover crop.** Each bare stretch is filled from 3 weeks after it
   starts, except between the usual sowing and harvest weeks of winter wheat.
   A best case: it assumes the cover crop comes up every time.
3. **Change the rotation.** One year is swapped: the latest fallow year, or
   else the latest year of the most repeated crop. The new crop is the box's
   most-grown legume, or, if the field already has a legume, the most widely
   grown crop it lacks. The swapped year takes that crop's typical weekly
   pattern, measured from fields in the box.

Every plan is rescored with the same formula and carries rationale, evidence,
benefits, data gaps and risks needing local review. The sliders reorder the
plans and never change a number.

## Validation (14 November 2026 build)

1. **Crop curve check:** 2820 of 4013 field-years (70%) look most like the typical curve of the crop USDA mapped; chance is 11%.
2. **Bare-soil spot check against NAIP photos:** not done. It needs a person.
3. **Fallow check:** fallow field-years were bare for a median of 34 weeks, cropped field-years 21.
4. **Threshold test:** mean bare weeks a year are 7.6 at 0.20, 22.5 at 0.25 and 30.2 at 0.30. Only 5% of fields keep their grade at 0.20 and 34% at 0.30. **The grade is sensitive to the threshold.** We kept 0.25 because it separates fallow from cropped fields.

## Limits

- NDVI cannot see crop residue.
- Grades shift strongly with the bare threshold; read them as a ranking within the box.
- Winter weeks are mostly inferred, and that is when most heavy rain falls.
- Field outlines are approximate.
- One climate grid cell covers the box.
- Slope, tillage and soil type are not part of the grade.
