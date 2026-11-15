# Submission drafts

Drafts for the team to edit. Every number below comes from the 14 November
2026 build; rerun `make data` and update them if the data changes.

## Links

- Live site: https://rehaan12355.github.io/field-report-card/
- Methods and checks: https://rehaan12355.github.io/field-report-card/methods.html
- Code: https://github.com/Rehaan12355/field-report-card
- Demo field: https://rehaan12355.github.io/field-report-card/#f5764

## High-level summary

Click any field and NASA satellites tell you how many weeks a year it has no
green cover, how that lines up with heavy rain, and which planting plan would
protect it. Most rotation tools ask the farmer to type in what they grow.
Field Report Card reads the rotation and the bare weeks from space, then
grades the field and compares three plans.

## Detailed description

**The problem.** Soil with nothing growing on it loses topsoil and water,
most of all when heavy rain arrives. Farmers rarely see their own bare-week
pattern laid out year by year.

**The method.** For all 6,685 fields (326,655 hectares of cropland) in Whitman
County, Washington, we read weekly greenness from NASA HLS (Harmonized
Landsat and Sentinel-2) for 2019 to 2025, mark weeks below
0.25 NDVI as bare, and cross them with heavy-rain weeks from NASA POWER
(the top 10% of weeks since 1991 in each climate grid cell, 19.8 to 35.0 mm
or more). USDA crop maps give each year's crop and the USDA soil survey gives
soil properties. Each field gets a grade from A to F and three plans: keep
the rotation, add a cover crop, or swap one year for another crop. Every plan
lists its rationale, evidence, benefits, data gaps and risks to check locally.

**The evidence.** 61% of 45,734 field-years have a greenness curve
that best matches the crop USDA mapped, against 6% by chance. Fields mapped
as fallow were bare for a median of 36 weeks that year, cropped fields
21.

**The impact.** In an average heavy-rain week, 46% of the county's
cropland has no green cover. The map shows a clear pattern: the drier west of
the county, where wheat alternates with fallow, grades worst. The inputs
cover the contiguous United States, so the same pipeline can run for any
county.

**The limits.** NDVI cannot see crop residue, so stubble reads as bare. The
grade is sensitive to the bare threshold: mean bare weeks a year run from
8.8 at 0.20 to 31.1 at 0.30. Cloud hides most of December and January,
so many winter weeks are inferred and shown as "likely". Field outlines are
approximate. Climate grid cells are about 50 km wide. The aerial photo spot
check has not been done. The grade is a screening tool, not a soil test.

## 30-second demo script

1. Open the site and show the whole county coloured by grade. Click "Open
   an example field". The card reads grade D: bare about 28 weeks a year (24 seen, 4 likely), 4 of them during heavy rain.
2. Point at the ribbon: one row per year, brown for bare weeks, red where
   heavy rain fell on bare soil, hatched where cloud hid the field.
3. Click "Add a cover crop". The brown shrinks and the grade becomes B:
   bare about 11 weeks a year (9 seen, 2 likely), 1 of them during heavy rain.
4. Say that this is a best case, and that the card lists the water trade-off.
5. End on: "Every field in Whitman County, graded from space. The data
   covers the whole country."

The handoff's closing line, "Every field in America, graded from space", is
not true of the demo, which covers one county. Use the wording above or
similar.

## NASA and partner data to list on the form

- NASA: HLS vegetation indices (HLSL30_VI, HLSS30_VI v2.0, LP DAAC); NASA POWER.
- Partner and other: Landsat (NASA/USGS) and Sentinel-2 (ESA) inside HLS;
  USDA Cropland Data Layer; USDA soil survey (SSURGO); US Census Bureau
  county boundary; USGS aerial imagery; OpenStreetMap basemap.

## Still for the team

- Do the 20-field NAIP spot check and add the result to the methods page.
- Check the planting and harvest dates in `pipeline/crop_traits.csv` against
  the Handbook 628 PDF (Washington page); they were read by text extraction.
- Check WSU EM108 Table 5-A3 (water use ranks) the same way.
- Edit `AI_USE.md` until it is true, then paste it into the form.
- Record the demo and add English subtitles.
