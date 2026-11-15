import "@fontsource-variable/geist";
import "@fontsource-variable/geist-mono";
import "./style.css";
import type { Meta } from "./types";

type CropCheck = { crop: string; color: string; field_years: number; matched: number; share: number | null; curve: (number | null)[] };
type Threshold = {
  same_grade: number;
  one_letter: number;
  two_or_more: number;
  mean_bare_weeks: number;
  fallow_median_bare_weeks: number;
  cropped_median_bare_weeks: number;
};
type Validation = {
  crop_curve_check: { crops: CropCheck[]; field_years: number; matched: number; share: number; chance: number };
  bare_soil_spot_check: { status: string; note: string };
  fallow_check: Record<"fallow" | "cropped", { field_years: number; median_bare_weeks: number; mean_bare_weeks: number }>;
  threshold_test: Record<string, Threshold>;
  plan_checks: {
    fields: number;
    cover_fewer_bare: number;
    cover_same_bare: number;
    exposed_never_exceeds_bare: boolean;
    mean_bare_current: number;
    mean_bare_cover: number;
  };
  rain_season_check: { since: number; heavy_weeks: number; share_november_to_march: number };
  week_states: Record<"seen" | "likely" | "snow" | "unknown", number>;
  clear_looks_by_month: Record<string, number[]>;
  cdl_accuracy_wa_2023: { overall_fsa_crops: number; kappa: number; producer: Record<string, number>; user: Record<string, number> } | null;
};

const pct = (x: number) => `${Math.round(x * 100)}%`;
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function curve(c: CropCheck, threshold: number): string {
  const w = 200;
  const h = 70;
  const x = (i: number) => (i / 51) * w;
  const y = (v: number) => 4 + (1 - v) * (h - 8);
  let d = "";
  let pen = false;
  c.curve.forEach((v, i) => {
    if (v === null) return void (pen = false);
    d += `${pen ? "L" : "M"}${x(i).toFixed(1)} ${y(v).toFixed(1)}`;
    pen = true;
  });
  return `<figure class="mini">
    <svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Typical greenness through the year for ${c.crop}">
      <rect class="curve-bare" x="0" y="${y(threshold)}" width="${w}" height="${h - 4 - y(threshold)}"/>
      <line class="curve-threshold" x1="0" x2="${w}" y1="${y(threshold)}" y2="${y(threshold)}"/>
      <path class="curve-line" d="${d}"/>
    </svg>
    <figcaption><b>${c.crop}</b><br />${c.matched} of ${c.field_years} field-years fit${
      c.share === null ? "" : ` (${pct(c.share)})`
    }</figcaption>
  </figure>`;
}

function render(meta: Meta, v: Validation): string {
  const y0 = meta.years[0];
  const y1 = meta.years[meta.years.length - 1];
  const w = (meta as unknown as { grade_weights: Record<string, number> }).grade_weights;
  const cuts = (meta as unknown as { grade_cutoffs: Record<string, number> }).grade_cutoffs;
  const t = v.threshold_test;
  const thresholdRows = Object.entries(t)
    .map(
      ([k, r]) => `<tr><th scope="row">${k}${Number(k) === meta.ndvi_threshold ? " (used)" : ""}</th>
        <td>${r.mean_bare_weeks}</td><td>${r.fallow_median_bare_weeks}</td><td>${r.cropped_median_bare_weeks}</td>
        <td>${Number(k) === meta.ndvi_threshold ? "" : pct(r.same_grade)}</td>
        <td>${Number(k) === meta.ndvi_threshold ? "" : pct(r.one_letter)}</td>
        <td>${Number(k) === meta.ndvi_threshold ? "" : pct(r.two_or_more)}</td></tr>`,
    )
    .join("");
  const looks = Object.entries(v.clear_looks_by_month)
    .map(([yr, row]) => `<tr><th scope="row">${yr}</th>${row.map((n) => `<td class="${n < 2 ? "is-low" : ""}">${n}</td>`).join("")}</tr>`)
    .join("");
  const acc = v.cdl_accuracy_wa_2023;
  const accRows = acc
    ? Object.keys(acc.producer)
        .map((c) => `<tr><th scope="row">${c}</th><td>${pct(acc.producer[c])}</td><td>${pct(acc.user[c])}</td></tr>`)
        .join("")
    : "";
  const mm = meta.cells.map((c) => c.heavy_mm);
  const heavyMm = mm.length > 1 ? `${Math.min(...mm)} to ${Math.max(...mm)} mm or more, depending on the grid cell` : `${mm[0]} mm or more`;
  const src = (id: string) => {
    const s = meta.sources[id];
    return s ? `<a href="${s.url}" target="_blank" rel="noopener">${s.title}</a>` : "";
  };
  return `
  <h2>How Field Report Card works</h2>
  <p class="lede">Every number on the map comes from public NASA and USDA data. This page says how each one is
    made, what we checked, and where it falls short. The grade is a screening tool, not a soil test.</p>

  <h3>What you are looking at</h3>
  <p>${meta.fields.toLocaleString("en-US")} fields covering ${Math.round(meta.hectares).toLocaleString("en-US")}
    hectares of cropland in ${meta.region}, ${y0} to ${y1}. The method uses data that covers the contiguous
    United States; this demo runs it on one county.</p>

  <h3>The data</h3>
  <table class="facts">
    <tbody>
      <tr><th scope="row">NASA HLS</th><td class="words">Harmonized Landsat and Sentinel-2 vegetation indices (HLSL30_VI and
        HLSS30_VI, version 2.0) from NASA's LP DAAC: greenness (NDVI) and a cloud mask at 30 m, every few days.
        Landsat is a NASA and USGS mission; Sentinel-2 is from the European Space Agency.</td></tr>
      <tr><th scope="row">NASA POWER</th><td class="words">Daily rain and temperature since 1991, on a grid of about 50 km.
        ${meta.cells.length} grid cells cover the fields; each field uses the cell it sits in.</td></tr>
      <tr><th scope="row">USDA Cropland Data Layer</th><td class="words">The crop grown on each 30 m pixel, each year.</td></tr>
      <tr><th scope="row">USDA soil survey</th><td class="words">SSURGO soil properties, read at the centre of each field.</td></tr>
    </tbody>
  </table>

  <h3>Fields</h3>
  <p>There is no free national map of field boundaries, so the outlines are approximate. A field is a group of
    touching pixels that grew the same crops in each of the last three years, at least 5 hectares in size.
    Real fields that share a rotation with a neighbour are merged, and real fields with mixed pixels can split.</p>

  <h3>Bare weeks</h3>
  <p>For each field and each satellite pass we take the middle NDVI value of its cloud-free pixels, then keep one
    value per week. A week with NDVI below ${meta.ndvi_threshold} counts as bare. NDVI sees living green plants,
    so "bare" here means no green cover: it cannot tell tilled soil from soil under dry stubble, which is better
    protected.</p>
  <p>Cloud hides these fields for most of December and January. Gaps are handled in two steps. A gap of up to
    3 weeks is filled by a straight line between the clear views on either side. A longer gap, up to 16 weeks,
    is bridged only when both ends agree: bare on both sides gives "likely bare", green on both sides gives
    "likely green". Anything else stays unknown. Snowy views never count as bare. Across all fields and weeks,
    ${pct(v.week_states.seen)} were seen, ${pct(v.week_states.likely)} are likely, ${pct(v.week_states.snow)} were
    snow and ${pct(v.week_states.unknown)} stayed unknown.</p>
  <div class="table-scroll"><table class="facts looks">
    <caption>Satellite passes with at least half the fields in clear view, by month (the southern of the
      two image tiles, which holds most fields)</caption>
    <thead><tr><td></td>${MONTHS.map((m) => `<th scope="col">${m}</th>`).join("")}</tr></thead>
    <tbody>${looks}</tbody>
  </table></div>

  <h3>Heavy rain and exposed weeks</h3>
  <p>A heavy-rain week is one whose rain total is in the top 10% of all weeks since ${v.rain_season_check.since}
    in that grid cell:
    ${heavyMm}. ${pct(v.rain_season_check.share_november_to_march)} of those weeks fall between
    November and March. An exposed week is a bare week that is also a heavy-rain week. In an average heavy-rain
    week, ${pct(meta.bare_in_heavy_rain_share)} of this cropland (by area, where its state is known) is bare.</p>

  <h3>The grade</h3>
  <p>The score is out of 100: up to ${w.bare} points for few bare weeks, up to ${w.exposed} for few exposed weeks
    (against the worst field in the county), and up to ${w.variety} for crop variety, with a bonus for a
    legume or a perennial. Likely weeks count the same as seen weeks. Grades: A from ${cuts.A}, B from ${cuts.B},
    C from ${cuts.C}, D from ${cuts.D}, F below. These weights are a starting point, not a tested standard.</p>

  <h3>The three plans</h3>
  <p><b>Keep the current rotation</b> is the field as measured. <b>Add a cover crop</b> fills each bare stretch
    from 3 weeks after it starts, except while winter wheat is in the ground. It is a best case: it assumes the
    cover crop comes up every time. <b>Change the rotation</b> swaps one year, a fallow year first, for a crop
    the field lacks, a legume first. The swapped year uses that crop's typical weekly pattern, measured from
    fields in this study area that grew it. Every plan is scored with the same formula. The sliders reorder the
    plans; they never change a number.</p>
  <p>Planting and harvest weeks come from ${src("handbook628")}. Water ranks and statements about cover crops
    and pulses come from ${src("em108")}, ${src("cover_water")} and ${src("cover_review")}.</p>

  <h3>What we checked</h3>

  <h4>1. Do the crop maps match the greenness curves?</h4>
  <p>For each field and year, we asked which crop's typical curve its own greenness looked most like.
    ${v.crop_curve_check.matched.toLocaleString("en-US")} of ${v.crop_curve_check.field_years.toLocaleString("en-US")}
    field-years (${pct(v.crop_curve_check.share)}) matched the crop USDA mapped; guessing would get
    ${pct(v.crop_curve_check.chance)}. Winter wheat, chickpeas and fallow are distinct. Spring wheat and barley
    have nearly the same curve and are often confused with each other.</p>
  <div class="minis">${v.crop_curve_check.crops.map((c) => curve(c, meta.ndvi_threshold)).join("")}</div>

  <h4>2. Do "bare" fields look bare in aerial photos?</h4>
  <p><b>Not done yet.</b> ${v.bare_soil_spot_check.note}</p>

  <h4>3. Are fallow fields bare for longer?</h4>
  <p>Yes. Fields USDA mapped as fallow were bare for a median of ${v.fallow_check.fallow.median_bare_weeks} weeks
    that year (${v.fallow_check.fallow.field_years} field-years), against ${v.fallow_check.cropped.median_bare_weeks}
    weeks for cropped fields (${v.fallow_check.cropped.field_years.toLocaleString("en-US")} field-years).</p>

  <h4>4. How much does the bare threshold matter?</h4>
  <p><b>A lot, and this is the main weakness.</b> Outside the growing season these fields sit at an NDVI of
    about 0.19 to 0.25, right around the threshold, so moving it changes many weeks at once. We kept
    ${meta.ndvi_threshold} because it separates fallow from cropped fields; at 0.20 that gap nearly disappears.
    Treat grades as a ranking within this area, not an absolute measure.</p>
  <div class="table-scroll"><table class="facts">
    <thead><tr><th scope="col">Threshold</th><th scope="col">Mean bare weeks</th><th scope="col">Fallow median</th>
      <th scope="col">Cropped median</th><th scope="col">Same grade</th><th scope="col">Moved one letter</th>
      <th scope="col">Moved two or more</th></tr></thead>
    <tbody>${thresholdRows}</tbody>
  </table></div>

  <h4>Built-in checks</h4>
  <p>Exposed weeks never exceed bare weeks. The cover crop plan has fewer bare weeks than the current rotation
    on ${v.plan_checks.cover_fewer_bare} of ${v.plan_checks.fields} fields and the same on
    ${v.plan_checks.cover_same_bare}.</p>

  ${
    acc
      ? `<h4>How accurate are the crop maps?</h4>
  <p>USDA's own check for Washington in 2023 put the Cropland Data Layer at ${pct(acc.overall_fsa_crops)} overall
    for crops (kappa ${acc.kappa}). Source: ${src("cdl_accuracy")}.</p>
  <table class="facts narrow"><thead><tr><td></td><th scope="col">Producer's accuracy</th><th scope="col">User's accuracy</th></tr></thead>
    <tbody>${accRows}</tbody></table>`
      : ""
  }

  <h3>Limits</h3>
  <ul>
    <li>NDVI cannot see crop residue, so stubble-covered soil reads as bare.</li>
    <li>Grades shift strongly with the bare threshold.</li>
    <li>Winter weeks are mostly inferred, and that is when most heavy rain falls.</li>
    <li>Field outlines are approximate.</li>
    <li>Climate grid cells are about 50 km wide, so rain timing is regional, not per field.</li>
    <li>Slope, tillage and soil type are not part of the grade.</li>
    <li>The aerial photo spot check has not been done.</li>
  </ul>

  <h3>How this was built</h3>
  <p>We used Claude (Anthropic), through Claude Code, to help plan the project, write and debug most of the code,
    and draft documentation. The app contains no AI-generated images, video or audio. Code and data sources are
    in the <a href="https://github.com/Rehaan12355/field-report-card">public repository</a>.
    Data last built on ${meta.generated}.</p>`;
}

async function start(): Promise<void> {
  const main = document.getElementById("methods") as HTMLElement;
  try {
    const [meta, v] = await Promise.all([
      fetch("./data/meta.json").then((r) => r.json() as Promise<Meta>),
      fetch("./data/validation.json").then((r) => r.json() as Promise<Validation>),
    ]);
    main.innerHTML = render(meta, v);
  } catch {
    main.innerHTML = "<h2>This page did not load</h2><p>Check your connection and reload.</p>";
  }
}

start();
