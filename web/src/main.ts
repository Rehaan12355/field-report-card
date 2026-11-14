import "@fontsource-variable/bitter";
import "@fontsource-variable/public-sans";
import "maplibre-gl/dist/maplibre-gl.css";
import "./style.css";
import { initCard, showError, showField, showIntro } from "./card";
import { patternDefs } from "./charts";
import { createMap } from "./map";
import type { Field, Meta } from "./types";

async function getJson<T>(url: string): Promise<T> {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url} returned ${r.status}`);
  return r.json() as Promise<T>;
}

async function start(): Promise<void> {
  document.body.insertAdjacentHTML("beforeend", patternDefs());
  initCard();
  let meta: Meta;
  try {
    meta = await getJson<Meta>("./data/meta.json");
  } catch {
    showError("The field data could not be reached. Check your connection and reload the page.");
    return;
  }

  // The field id lives in the address, so a report card can be linked to.
  const pick = async (id: string | null) => {
    history.replaceState(null, "", id ? `#${id}` : location.pathname);
    view.select(id);
    if (!id) return showIntro(meta);
    try {
      showField(await getJson<Field>(`./data/fields/${id}.json`), meta);
    } catch {
      showError("That field's record could not be loaded. Click the field again, or reload the page.");
    }
  };
  const view = createMap("map", meta, pick);

  const aerial = document.getElementById("aerial") as HTMLInputElement;
  aerial.addEventListener("change", () => view.setAerial(aerial.checked));

  const fromHash = location.hash.slice(1);
  if (/^f\d+$/.test(fromHash)) view.map.once("load", () => pick(fromHash));
  else showIntro(meta);
}

start();
