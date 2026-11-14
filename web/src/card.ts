import { greennessCurve, ribbon, ribbonKey } from "./charts";
import { planDetail, planTable, priorities, sliders } from "./plans";
import type { Field, Measure, Meta, Plan } from "./types";

const el = () => document.getElementById("card") as HTMLElement;

let current: { field: Field; meta: Meta; selected: Plan["key"] } | null = null;

function dayOfYear(doy: number): string {
  const d = new Date(Date.UTC(2023, 0, Math.round(doy)));
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", timeZone: "UTC" });
}

function climatePanel(meta: Meta): string {
  const m = meta.climate.measures;
  const [n0, n1] = meta.climate.normal_years;
  const [r0, r1] = meta.climate.recent_years;
  const row = (label: string, v: Measure, fmt: (x: number) => string, more: string, fewer: string, unit: string) => {
    const diff = v.recent - v.normal;
    const word = Math.abs(diff) < 0.5 ? "no change" : `${Math.abs(Math.round(diff))} ${unit} ${diff > 0 ? more : fewer}`;
    return `<tr><th scope="row">${label}</th><td>${fmt(v.normal)}</td><td>${fmt(v.recent)}</td><td>${word}</td></tr>`;
  };
  const num = (x: number) => String(Math.round(x));
  return `<section><h3>Climate here</h3>
    <table class="climate">
      <thead><tr><td></td><th scope="col">${n0} to ${n1}</th><th scope="col">${r0} to ${r1}</th><td></td></tr></thead>
      <tbody>
        ${row("Days above 32 °C", m.hot_days, num, "more", "fewer", "days")}
        ${row("Last spring frost", m.last_spring_frost, dayOfYear, "later", "earlier", "days")}
        ${row("First fall frost", m.first_fall_frost, dayOfYear, "later", "earlier", "days")}
        ${row("Rain a year", m.rain_mm, (x) => `${num(x)} mm`, "more", "less", "mm")}
      </tbody>
    </table>
    <p class="note">NASA POWER, one grid cell of about 50 km covering the whole study area.</p>
  </section>`;
}

function soilPanel(field: Field): string {
  const s = field.soil;
  if (!s) return "";
  const val = (v: number | null, unit: string) => (v === null ? "Not reported" : `${v}${unit}`);
  return `<section><h3>Soil</h3>
    <table class="climate"><tbody>
      <tr><th scope="row">Main soil</th><td>${s.name}</td></tr>
      <tr><th scope="row">Erodibility (K factor)</th><td>${val(s.kw, "")}</td></tr>
      <tr><th scope="row">Organic matter, topsoil</th><td>${val(s.om, "%")}</td></tr>
      <tr><th scope="row">Water held, topsoil</th><td>${val(s.awc, " cm per cm")}</td></tr>
    </tbody></table>
    <p class="note">USDA soil survey (SSURGO), read at the centre of the field. K factor runs from about 0.02
      to 0.69; higher erodes more easily.</p>
  </section>`;
}

function render(): void {
  if (!current) return;
  const { field, meta, selected } = current;
  const plan = field.plans.find((p) => p.key === selected) ?? field.plans[0];
  const latest = meta.crops[String(field.plans[0].crops[field.years.length - 1])];
  const scroll = el().scrollTop;
  el().innerHTML = `
    <header class="grade-head">
      <div class="grade-block grade-${plan.grade}" aria-label="Grade ${plan.grade}">${plan.grade}</div>
      <div>
        <h2>${plan.key === "current" ? "This field today" : plan.title}</h2>
        <p class="reason">Grade ${plan.grade}: ${plan.reason}.</p>
        <p class="note">${Math.round(field.ha)} hectares, ${latest.name.toLowerCase()} in ${field.years[field.years.length - 1]}.
          Approximate field outline.</p>
      </div>
    </header>

    <section>
      <h3>Every week, ${field.years[0]} to ${field.years[field.years.length - 1]}</h3>
      ${ribbon(field, plan, meta)}
      ${ribbonKey(plan)}
    </section>

    <section>
      <h3>Three plans to compare</h3>
      ${sliders(priorities)}
      <div class="table-scroll">${planTable(field.plans, plan.key, priorities)}</div>
      <p class="note">Pick a plan to see it on the timeline. The sliders only reorder the plans.</p>
      ${planDetail(plan, meta)}
    </section>

    <section>
      <h3>Greenness seen from space</h3>
      ${greennessCurve(field, meta)}
      <p class="note">Each dot is a week with a clear view from NASA's Landsat and Sentinel-2 record (HLS).
        Below the line (NDVI ${meta.ndvi_threshold}) counts as bare.</p>
    </section>

    ${climatePanel(meta)}
    ${soilPanel(field)}

    <p class="note">The grade is a screening tool, not a soil test.
      <a href="./methods.html">How it works and how we checked it</a></p>`;
  el().scrollTop = scroll;
}

export function showField(field: Field, meta: Meta): void {
  current = { field, meta, selected: "current" };
  render();
  el().scrollTop = 0;
}

export function showIntro(meta: Meta): void {
  current = null;
  const total = Object.values(meta.grades).reduce((a, b) => a + b, 0);
  const bars = Object.entries(meta.grades)
    .map(
      ([g, n]) => `<li><b class="grade-chip grade-${g}">${g}</b>
        <span class="bar"><i class="grade-${g}" style="width:${((n / total) * 100).toFixed(1)}%"></i></span>
        <span>${n}</span></li>`,
    )
    .join("");
  el().innerHTML = `
    <h2>Click a field to read its report card</h2>
    <p>${meta.fields} fields between Colfax and Pullman, graded on how long their soil sits bare and
      whether that lines up with heavy rain.</p>
    <p class="headline"><b>${Math.round(meta.bare_in_heavy_rain_share * 100)}%</b>
      of this cropland is bare in an average heavy-rain week.</p>
    <h3>Grades in this area</h3>
    <ul class="grade-bars">${bars}</ul>
    <p class="note">Read from NASA satellite greenness (HLS) and NASA POWER rain,
      ${meta.years[0]} to ${meta.years[meta.years.length - 1]}, with USDA crop maps. The grade is a screening tool,
      not a soil test. <a href="./methods.html">How it works and how we checked it</a></p>`;
}

export function showError(message: string): void {
  current = null;
  el().innerHTML = `<h2>The report card did not load</h2><p>${message}</p>`;
}

export function initCard(): void {
  el().addEventListener("click", (e) => {
    const btn = (e.target as HTMLElement).closest<HTMLButtonElement>("button[data-plan]");
    if (!btn || !current) return;
    current.selected = btn.dataset.plan as Plan["key"];
    render();
    el().querySelector<HTMLButtonElement>(`button[data-plan="${current.selected}"]`)?.focus();
  });
  el().addEventListener("change", (e) => {
    const input = e.target as HTMLInputElement;
    const key = input.dataset?.priority as keyof typeof priorities | undefined;
    if (!key) return;
    priorities[key] = Number(input.value);
    render();
    el().querySelector<HTMLInputElement>(`input[data-priority="${key}"]`)?.focus();
  });
}
