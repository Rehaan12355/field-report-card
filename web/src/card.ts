import { greennessCurve, ribbon, ribbonKey } from "./charts";
import { planDetail, planTable, priorities, sliders } from "./plans";
import { playStory, stopStory } from "./story";
import type { Cell, Field, Measure, Meta, Plan } from "./types";

type Handlers = {
  onClose: () => void;
  onExample: () => void;
  onGradeFilter: (grade: string | null) => void;
};

const el = () => document.getElementById("card") as HTMLElement;

let handlers: Handlers;
let current: { field: Field; meta: Meta; selected: Plan["key"] } | null = null;
let gradeFilter: string | null = null;

function dayOfYear(doy: number): string {
  const d = new Date(Date.UTC(2023, 0, Math.round(doy)));
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", timeZone: "UTC" });
}

function climatePanel(cell: Cell): string {
  const m = cell.climate.measures;
  const [n0, n1] = cell.climate.normal_years;
  const [r0, r1] = cell.climate.recent_years;
  const row = (label: string, v: Measure, fmt: (x: number) => string, more: string, fewer: string, unit: string) => {
    const diff = v.recent - v.normal;
    const word = Math.abs(diff) < 0.5 ? "no change" : `${Math.abs(Math.round(diff))} ${unit} ${diff > 0 ? more : fewer}`;
    return `<tr><th scope="row">${label}</th><td>${fmt(v.normal)}</td><td>${fmt(v.recent)}</td><td class="words">${word}</td></tr>`;
  };
  const num = (x: number) => String(Math.round(x));
  return `<section><h3>Climate here</h3>
    <table class="facts">
      <thead><tr><td></td><th scope="col">${n0} to ${n1}</th><th scope="col">${r0} to ${r1}</th><td></td></tr></thead>
      <tbody>
        ${row("Days above 32 °C", m.hot_days, num, "more", "fewer", "days")}
        ${row("Last spring frost", m.last_spring_frost, dayOfYear, "later", "earlier", "days")}
        ${row("First fall frost", m.first_fall_frost, dayOfYear, "later", "earlier", "days")}
        ${row("Rain a year", m.rain_mm, (x) => `${num(x)} mm`, "more", "less", "mm")}
      </tbody>
    </table>
    <p class="note">NASA POWER. The climate grid is coarse: one cell of about 50 km covers this field and its
      neighbours. A heavy-rain week here is ${cell.heavy_mm} mm or more.</p>
  </section>`;
}

function soilPanel(field: Field): string {
  const s = field.soil;
  if (!s) return "";
  const val = (v: number | null, unit: string) => (v === null ? "Not reported" : `${v}${unit}`);
  return `<section><h3>Soil</h3>
    <table class="facts"><tbody>
      <tr><th scope="row">Main soil</th><td class="words">${s.name}</td></tr>
      <tr><th scope="row">Erodibility (K factor)</th><td>${val(s.kw, "")}</td></tr>
      <tr><th scope="row">Organic matter, topsoil</th><td>${val(s.om, "%")}</td></tr>
      <tr><th scope="row">Water held, topsoil</th><td>${val(s.awc, " cm per cm")}</td></tr>
    </tbody></table>
    <p class="note">USDA soil survey (SSURGO), read at the centre of the field. K factor runs from about 0.02
      to 0.69; higher erodes more easily.</p>
  </section>`;
}

function render(animate: boolean): void {
  if (!current) return;
  const { field, meta, selected } = current;
  const plan = field.plans.find((p) => p.key === selected) ?? field.plans[0];
  const lastYear = field.years[field.years.length - 1];
  const latest = meta.crops[String(field.plans[0].crops[field.years.length - 1])];
  const scroll = el().scrollTop;
  el().innerHTML = `<div class="${animate ? "rise" : ""}">
    <div class="card-top">
      <p class="note">${Math.round(field.ha)} hectares, ${latest.name.toLowerCase()} in ${lastYear}</p>
      <span class="card-actions">
        <button type="button" class="button button-quiet" data-replay>Play the story</button>
        <button type="button" class="button button-quiet" data-close>All fields</button>
      </span>
    </div>
    <header class="grade-head">
      <div class="grade-block grade-${plan.grade}" aria-label="Grade ${plan.grade}">${plan.grade}</div>
      <div>
        <h2>${plan.key === "current" ? "This field today" : plan.title}</h2>
        <p class="reason">Grade ${plan.grade}: ${plan.reason}.</p>
      </div>
    </header>

    <section>
      <h3>Every week, ${field.years[0]} to ${lastYear}</h3>
      ${ribbon(field, plan, meta)}
      ${ribbonKey(plan)}
    </section>

    <section>
      <h3>Three plans to compare</h3>
      ${sliders(priorities)}
      <div class="table-scroll">${planTable(field.plans, plan.key, priorities)}</div>
      <p class="note">Pick a plan to see it on the timeline above. The sliders only reorder the plans.</p>
      ${planDetail(plan, meta)}
    </section>

    <section>
      <h3>Greenness seen from space</h3>
      ${greennessCurve(field, meta)}
      <p class="note">Each dot is a week with a clear view from NASA's Landsat and Sentinel-2 record (HLS).
        Below the dashed line (NDVI ${meta.ndvi_threshold}) counts as bare.</p>
    </section>

    ${climatePanel(meta.cells[field.cell])}
    ${soilPanel(field)}

    <section><p class="note">The field outline is approximate. The grade is a screening tool, not a soil test.
      <a href="./methods.html">How it works and how we checked it</a></p></section>
  </div>`;
  el().scrollTop = animate ? 0 : scroll;
}

export function showLoading(): void {
  stopStory();
  current = null;
  el().innerHTML = `<div class="skeleton" aria-label="Loading this field">
    <div class="sk sk-title"></div><div class="sk sk-line"></div><div class="sk sk-line short"></div>
    <div class="sk sk-block"></div><div class="sk sk-block"></div></div>`;
}

function story(): void {
  if (!current) return;
  const { field, meta } = current;
  current.selected = "current";
  playStory(el(), field, meta, () => render(true));
}

export function showField(field: Field, meta: Meta): void {
  current = { field, meta, selected: "current" };
  // The story plays first, unless the visitor has asked for less motion.
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) render(true);
  else story();
}

/** A four-cell ribbon set inline in the headline. */
const MINI_RIBBON = `<svg viewBox="0 0 58 20" aria-hidden="true">
  <rect class="wk-green" x="0" width="12" height="20" rx="3"/><rect class="wk-bare" x="15" width="12" height="20" rx="3"/>
  <rect class="wk-exposed" x="30" width="12" height="20" rx="3"/><rect class="wk-green" x="45" width="12" height="20" rx="3"/></svg>`;

export function showIntro(meta: Meta): void {
  stopStory();
  current = null;
  const total = Object.values(meta.grades).reduce((a, b) => a + b, 0);
  const bars = Object.entries(meta.grades)
    .map(
      ([g, n]) => `<li><button type="button" data-grade="${g}" aria-pressed="${gradeFilter === g}">
        <b class="grade-chip grade-${g}">${g}</b>
        <span class="bar"><i class="grade-${g}" style="width:${((n / total) * 100).toFixed(1)}%"></i></span>
        <span class="num">${n.toLocaleString("en-US")}</span></button></li>`,
    )
    .join("");
  el().innerHTML = `<div class="intro rise">
    <h2>Every field, graded ${MINI_RIBBON} from space</h2>
    <p>${meta.fields.toLocaleString("en-US")} farm fields in ${meta.region ?? "the study area"}, graded on how
      long their soil sits without green cover and whether that lines up with heavy rain.</p>
    <div class="stat"><b>${Math.round(meta.bare_in_heavy_rain_share * 100)}%</b>
      <span>of this cropland has no green cover in an average heavy-rain week.</span></div>
    <button type="button" class="button" data-example><span class="pulse"></span>Open an example field</button>

    <section>
      <h3>Grades on the map</h3>
      <ul class="grade-bars">${bars}</ul>
      <p class="note">Click a grade to show only those fields. Click it again to show all.</p>
    </section>

    <section>
      <h3>How to use it</h3>
      <ol class="steps">
        <li><div><b>Click a field</b>Its report card opens here.</div></li>
        <li><div><b>Read its weeks</b>One row per year: green, bare, and bare under heavy rain.</div></li>
        <li><div><b>Compare three plans</b>Keep the rotation, add a cover crop, or change a crop, and watch the grade move.</div></li>
      </ol>
    </section>

    <section><p class="note">Read from NASA satellite greenness (HLS) and NASA POWER rain,
      ${meta.years[0]} to ${meta.years[meta.years.length - 1]}, with USDA crop maps. The grade is a screening tool,
      not a soil test. <a href="./methods.html">How it works and how we checked it</a></p></section>
  </div>`;
}

export function showError(message: string): void {
  stopStory();
  current = null;
  el().innerHTML = `<h2>The report card did not load</h2><p>${message}</p>
    <p><button type="button" class="button button-quiet" data-close>Back to all fields</button></p>`;
}

export function initCard(h: Handlers): void {
  handlers = h;
  el().addEventListener("click", (e) => {
    const target = e.target as HTMLElement;
    if (target.closest("[data-close]")) return handlers.onClose();
    if (target.closest("[data-replay]")) return story();
    if (target.closest("[data-example]")) return handlers.onExample();
    const grade = target.closest<HTMLElement>("[data-grade]");
    if (grade) {
      gradeFilter = gradeFilter === grade.dataset.grade ? null : (grade.dataset.grade as string);
      handlers.onGradeFilter(gradeFilter);
      el()
        .querySelectorAll<HTMLElement>("[data-grade]")
        .forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.grade === gradeFilter)));
      return;
    }
    const btn = target.closest<HTMLButtonElement>("button[data-plan]");
    if (!btn || !current) return;
    current.selected = btn.dataset.plan as Plan["key"];
    render(false);
    el().querySelector<HTMLButtonElement>(`button[data-plan="${current.selected}"]`)?.focus();
  });
  el().addEventListener("change", (e) => {
    const input = e.target as HTMLInputElement;
    const key = input.dataset?.priority as keyof typeof priorities | undefined;
    if (!key) return;
    priorities[key] = Number(input.value);
    render(false);
    el().querySelector<HTMLInputElement>(`input[data-priority="${key}"]`)?.focus();
  });
}
