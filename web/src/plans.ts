import type { Effect, Meta, Plan } from "./types";

export type Priorities = { water: number; soil: number; income: number };

export const priorities: Priorities = { water: 5, soil: 5, income: 5 };

const EFFECT_WORDS: Record<string, string> = { "1": "Better", "0": "Same", "-1": "Worse" };

function effectScore(e: Effect): number {
  return e.effect === null ? 0.5 : (e.effect + 1) / 2;
}

/** How well a plan matches the sliders. The sliders only reorder the plans;
 *  they never change a plan's numbers. */
function match(plan: Plan, p: Priorities): number {
  return p.soil * (plan.score / 100) + p.water * effectScore(plan.water) + p.income * effectScore(plan.income);
}

export function ordered(plans: Plan[], p: Priorities): Plan[] {
  return plans
    .map((plan, i) => ({ plan, i, m: match(plan, p) }))
    .sort((a, b) => b.m - a.m || a.i - b.i)
    .map((x) => x.plan);
}

export function sliders(p: Priorities): string {
  const one = (key: keyof Priorities, label: string) =>
    `<label class="slider">${label}
       <input type="range" min="0" max="10" step="1" value="${p[key]}" data-priority="${key}" />
     </label>`;
  return `<fieldset class="sliders"><legend>What matters most to you?</legend>
    ${one("soil", "Protect soil")}${one("water", "Save water")}${one("income", "Add income")}
  </fieldset>`;
}

function effectCell(e: Effect): string {
  const word = e.effect === null ? "Not known" : EFFECT_WORDS[String(e.effect)];
  const cls = e.effect === null ? "is-unknown" : e.effect > 0 ? "is-better" : e.effect < 0 ? "is-worse" : "";
  return `<td class="${cls}">${word}<small>${e.note}</small></td>`;
}

const round = (x: number) => Math.round(x);

/** The three plans as one table, read across the rows. */
export function planTable(plans: Plan[], selected: string, p: Priorities): string {
  const cols = ordered(plans, p);
  const head = cols
    .map(
      (plan, i) => `<th scope="col" class="${plan.key === selected ? "is-selected" : ""}">
        ${i === 0 ? `<span class="best">Best match</span>` : ""}
        <button type="button" data-plan="${plan.key}" aria-pressed="${plan.key === selected}">${plan.title}</button>
      </th>`,
    )
    .join("");
  const row = (label: string, cell: (plan: Plan) => string) =>
    `<tr><th scope="row">${label}</th>${cols.map(cell).join("")}</tr>`;
  const sel = (plan: Plan) => (plan.key === selected ? "is-selected" : "");
  return `<table class="plans">
    <thead><tr><td></td>${head}</tr></thead>
    <tbody>
      ${row("Grade", (plan) => `<td class="${sel(plan)}"><b class="grade-chip grade-${plan.grade}">${plan.grade}</b></td>`)}
      ${row("Bare weeks a year", (plan) => `<td class="${sel(plan)}">${round(plan.counts.bare)}</td>`)}
      ${row("In heavy rain", (plan) => `<td class="${sel(plan)}">${round(plan.counts.exposed)}</td>`)}
      ${row("Water", (plan) => effectCell(plan.water))}
      ${row("Income", (plan) => effectCell(plan.income))}
    </tbody>
  </table>`;
}

export function planDetail(plan: Plan, meta: Meta): string {
  const item = (term: string, text: string) => `<dt>${term}</dt><dd>${text}</dd>`;
  const cites = plan.cites
    .map((id) => meta.sources[id])
    .filter(Boolean)
    .map((s) => `<li><a href="${s.url}" target="_blank" rel="noopener">${s.title}</a></li>`)
    .join("");
  return `<section class="plan-detail">
    <h3>${plan.title}</h3>
    <dl>
      ${item("Why", plan.rationale)}
      ${item("Evidence", plan.evidence)}
      ${item("Benefits", plan.benefits)}
      ${item("Data gaps", plan.gaps)}
      ${item("Risks to check locally", plan.risks)}
    </dl>
    ${cites ? `<p class="note">Sources</p><ul class="cites">${cites}</ul>` : ""}
    <p class="review">${plan.review}</p>
  </section>`;
}
