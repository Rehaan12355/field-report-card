import type { Field, Meta, Plan } from "./types";

const WEEKS = 52;
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

const STATE_WORDS: Record<string, string> = {
  G: "green",
  g: "likely green (cloudy gap)",
  B: "bare",
  b: "likely bare (cloudy gap)",
  S: "snow, not counted",
  U: "unknown, hidden by cloud",
  C: "cover crop (plan)",
  T: "green in a typical year of this crop (plan)",
  t: "bare in a typical year of this crop (plan)",
};

/** CSS class for one week cell: its state, and whether heavy rain fell on bare soil. */
export function cellClass(state: string, heavy: boolean): string {
  switch (state) {
    case "B":
      return heavy ? "wk-exposed" : "wk-bare";
    case "b":
    case "t":
      return heavy ? "wk-exposed-likely" : "wk-bare-likely";
    case "G":
      return "wk-green";
    case "g":
    case "T":
      return "wk-green-likely";
    case "C":
      return "wk-cover";
    case "S":
      return "wk-snow";
    default:
      return "wk-unknown";
  }
}

function weekStart(year: number, week: number): string {
  const d = new Date(Date.UTC(year, 0, 1 + week * 7));
  return `${MONTHS[d.getUTCMonth()]} ${d.getUTCDate()}, ${year}`;
}

/** Shared hatch patterns for inferred weeks. Added to the page once. */
export function patternDefs(): string {
  const hatch = (id: string, cls: string) =>
    `<pattern id="${id}" width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
       <rect width="4" height="4" class="hatch-ground"/><rect width="2" height="4" class="${cls}"/>
     </pattern>`;
  return `<svg width="0" height="0" aria-hidden="true" style="position:absolute"><defs>
    ${hatch("hatch-bare", "hatch-bare")}${hatch("hatch-green", "hatch-green")}
    ${hatch("hatch-exposed", "hatch-exposed")}${hatch("hatch-unknown", "hatch-unknown")}
  </defs></svg>`;
}

/** The week ribbon: one row per year, 52 cells, with the year's crop at the left. */
export function ribbon(field: Field, plan: Plan, meta: Meta): string {
  const cw = 10;
  const cell = meta.cells[field.cell];
  const months = MONTHS.map((m, i) => {
    const x = (((Date.UTC(2023, i, 1) - Date.UTC(2023, 0, 1)) / 864e5 / 7) * cw).toFixed(1);
    return `<text x="${x}" y="9">${m[0]}</text>`;
  }).join("");
  const rows = field.years
    .map((year, yi) => {
      const crop = meta.crops[String(plan.crops[yi])];
      const swapped = plan.swap_year === yi;
      const cells = [...plan.weeks[yi]]
        .map((s, w) => {
          const heavy = cell.heavy[yi][w] === "1";
          const rain = cell.rain[yi][w];
          const tip = `Week of ${weekStart(year, w)}: ${STATE_WORDS[s] ?? s}${heavy ? `. Heavy rain, ${rain} mm` : ""}`;
          return `<rect class="wk ${cellClass(s, heavy)}" x="${w * cw + 0.5}" y="4" width="${cw - 1}" height="16" rx="1.5"><title>${tip}</title></rect>${
            heavy ? `<rect class="wk-rain" x="${w * cw + 0.5}" y="0" width="${cw - 1}" height="3"/>` : ""
          }`;
        })
        .join("");
      return `<div class="ribbon-row${swapped ? " is-swapped" : ""}" data-yi="${yi}">
        <span class="ribbon-year">${year}</span>
        <span class="ribbon-crop"><i style="background:${crop.color}"></i>${crop.name}</span>
        <svg viewBox="0 0 ${WEEKS * cw} 20" preserveAspectRatio="none" role="img"
             aria-label="${year}, ${crop.name}">${cells}</svg>
      </div>`;
    })
    .join("");
  return `<div class="ribbon">
    <div class="ribbon-row ribbon-months"><span></span><span></span>
      <svg viewBox="0 0 ${WEEKS * cw} 12" preserveAspectRatio="none" aria-hidden="true">${months}</svg></div>
    ${rows}</div>`;
}

export function ribbonKey(plan: Plan): string {
  const item = (cls: string, label: string) =>
    `<li><svg viewBox="0 0 12 12" aria-hidden="true"><rect class="${cls}" width="12" height="12"/></svg>${label}</li>`;
  const all = plan.weeks.join("");
  return `<ul class="key">
    ${item("wk-green", "Green")}
    ${item("wk-bare", "Bare")}
    ${item("wk-exposed", "Bare in heavy rain")}
    ${item("wk-bare-likely", "Likely, across a cloudy gap")}
    ${all.includes("C") ? item("wk-cover", "Cover crop") : ""}
    ${item("wk-unknown", "Unknown")}
    ${all.includes("S") ? item("wk-snow", "Snow") : ""}
    <li><svg viewBox="0 0 12 12" aria-hidden="true"><rect class="wk-rain" width="12" height="4"/></svg>Heavy-rain week</li>
  </ul>`;
}

/** Greenness (NDVI) across every year, with the bare threshold marked. */
export function greennessCurve(field: Field, meta: Meta): string {
  const n = field.years.length * WEEKS;
  const w = 520;
  const h = 96;
  const top = 6;
  const bottom = 16;
  const x = (i: number) => (i / (n - 1)) * w;
  const y = (v: number) => top + (1 - Math.max(0, Math.min(1, v))) * (h - top - bottom);
  const flat = field.ndvi.flat();
  let path = "";
  let pen = false;
  flat.forEach((v, i) => {
    if (v === null) {
      pen = false;
      return;
    }
    path += `${pen ? "L" : "M"}${x(i).toFixed(1)} ${y(v).toFixed(1)}`;
    pen = true;
  });
  const dots = flat
    .map((v, i) => (v === null ? "" : `<circle cx="${x(i).toFixed(1)}" cy="${y(v).toFixed(1)}" r="1.3"/>`))
    .join("");
  const ty = y(meta.ndvi_threshold);
  const years = field.years
    .map((yr, yi) => {
      const x0 = x(yi * WEEKS);
      return `<line class="curve-grid" x1="${x0}" x2="${x0}" y1="${top}" y2="${h - bottom}"/>
              <text x="${x0 + 3}" y="${h - 4}">${yr}</text>`;
    })
    .join("");
  return `<svg class="curve" viewBox="0 0 ${w} ${h}" role="img"
      aria-label="Greenness by week, ${field.years[0]} to ${field.years[field.years.length - 1]}">
    <rect class="curve-bare" x="0" y="${ty}" width="${w}" height="${h - bottom - ty}"/>
    ${years}
    <line class="curve-threshold" x1="0" x2="${w}" y1="${ty}" y2="${ty}"/>
    <path class="curve-line" d="${path}"/><g class="curve-dots">${dots}</g>
  </svg>`;
}

/** Recolour a ribbon already on the page to show another plan, so the cells
 *  change in place instead of being redrawn. */
export function recolorRibbon(root: HTMLElement, field: Field, plan: Plan, meta: Meta): void {
  const cell = meta.cells[field.cell];
  root.querySelectorAll<HTMLElement>(".ribbon-row[data-yi]").forEach((row) => {
    const yi = Number(row.dataset.yi);
    const crop = meta.crops[String(plan.crops[yi])];
    row.classList.toggle("is-swapped", plan.swap_year === yi);
    (row.querySelector(".ribbon-crop") as HTMLElement).innerHTML = `<i style="background:${crop.color}"></i>${crop.name}`;
    row.querySelectorAll("rect.wk").forEach((rect, w) => {
      rect.setAttribute("class", `wk ${cellClass(plan.weeks[yi][w], cell.heavy[yi][w] === "1")}`);
    });
  });
}
