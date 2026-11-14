import "@fontsource-variable/geist";
import "@fontsource-variable/geist-mono";
import "maplibre-gl/dist/maplibre-gl.css";
import "./style.css";
import { initCard, showError, showField, showIntro, showLoading } from "./card";
import { patternDefs } from "./charts";
import { createMap, type FieldProps } from "./map";
import type { Field, Meta } from "./types";

type FieldCollection = GeoJSON.FeatureCollection<GeoJSON.Polygon | GeoJSON.MultiPolygon, FieldProps>;

async function getJson<T>(url: string): Promise<T> {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url} returned ${r.status}`);
  return r.json() as Promise<T>;
}

/** A field that shows the idea well: a large D-grade field with the most bare weeks under heavy rain. */
function exampleField(fields: FieldCollection): string | null {
  const pool = fields.features.map((f) => f.properties).filter((p) => p.grade === "D" && p.ha >= 40);
  pool.sort((a, b) => b.exposed - a.exposed || b.bare - a.bare);
  return (pool[0] ?? fields.features[0]?.properties)?.id ?? null;
}

function legend(): void {
  const el = document.getElementById("legend") as HTMLElement;
  el.innerHTML = `<b>Field grade</b>
    <ol>${["A", "B", "C", "D", "F"].map((g) => `<li><span class="grade-chip grade-${g}">${g}</span></li>`).join("")}</ol>
    <div class="ends"><span>Less bare</span><span>More bare</span></div>`;
  el.hidden = false;
}

async function start(): Promise<void> {
  document.body.insertAdjacentHTML("beforeend", patternDefs());
  let meta: Meta;
  let fields: FieldCollection;
  try {
    [meta, fields] = await Promise.all([
      getJson<Meta>("./data/meta.json"),
      getJson<FieldCollection>("./data/fields.geojson"),
    ]);
  } catch {
    initCard({ onClose: () => location.reload(), onExample: () => {}, onGradeFilter: () => {} });
    showError("The field data could not be reached. Check your connection and reload the page.");
    return;
  }
  const region = meta.region ?? "";
  (document.getElementById("region") as HTMLElement).textContent = region.charAt(0).toUpperCase() + region.slice(1);
  legend();

  // The field id lives in the address, so a report card can be linked to.
  const pick = async (id: string | null) => {
    history.replaceState(null, "", id ? `#${id}` : location.pathname + location.search);
    view.select(id);
    if (!id) return showIntro(meta);
    showLoading();
    try {
      showField(await getJson<Field>(`./data/fields/${id}.json`), meta);
    } catch {
      showError("That field's record could not be loaded. Click the field again, or reload the page.");
    }
  };
  const view = createMap("map", fields, pick);
  initCard({
    onClose: () => pick(null),
    onExample: () => pick(exampleField(fields)),
    onGradeFilter: (grade) => view.setGradeFilter(grade),
  });

  const aerial = document.getElementById("aerial") as HTMLInputElement;
  aerial.addEventListener("change", () => view.setAerial(aerial.checked));

  const fromHash = location.hash.slice(1);
  if (/^f\d+$/.test(fromHash)) view.map.once("load", () => pick(fromHash));
  else showIntro(meta);
}

start();
