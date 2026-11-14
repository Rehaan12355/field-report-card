import * as maplibregl from "maplibre-gl";
// The bundler does not pick up MapLibre's worker on its own, so bundle it
// here and tell MapLibre where it ended up.
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url";

maplibregl.setWorkerUrl(workerUrl);

// OpenFreeMap: free vector basemap, no API key.
const BASEMAP_STYLE = "https://tiles.openfreemap.org/styles/liberty";

// Whitman County, Washington. Keep in step with pipeline/config.py.
const COUNTY_CENTER: [number, number] = [-117.52, 46.9];

export function createMap(container: string): maplibregl.Map {
  const map = new maplibregl.Map({
    container,
    style: BASEMAP_STYLE,
    center: COUNTY_CENTER,
    zoom: 9,
  });
  map.addControl(new maplibregl.NavigationControl(), "top-right");
  map.addControl(new maplibregl.ScaleControl({ unit: "metric" }));
  return map;
}
