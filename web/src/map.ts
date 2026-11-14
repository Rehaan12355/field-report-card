import * as maplibregl from "maplibre-gl";
// The bundler does not pick up MapLibre's worker on its own, so bundle it
// here and tell MapLibre where it ended up.
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url";
import type { Meta } from "./types";

maplibregl.setWorkerUrl(workerUrl);

// OpenFreeMap: free vector basemap, no API key. The pale style keeps the
// field grade colours as the loudest thing on the map.
const BASEMAP_STYLE = "https://tiles.openfreemap.org/styles/positron";
// USGS aerial imagery, public domain, no API key.
const AERIAL_TILES = "https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}";

const GRADE_COLORS = ["A", "#1f7a3a", "B", "#7fb04a", "C", "#e0b93b", "D", "#d07a2a", "F", "#a8321f"];

export function createMap(container: string, meta: Meta, onPick: (id: string | null) => void) {
  const [w, s, e, n] = meta.box;
  const map = new maplibregl.Map({
    container,
    style: BASEMAP_STYLE,
    bounds: [w, s, e, n],
    fitBoundsOptions: { padding: 24 },
  });
  map.addControl(new maplibregl.NavigationControl(), "top-right");
  map.addControl(new maplibregl.ScaleControl({ unit: "metric" }));

  map.on("load", () => {
    map.addSource("aerial", {
      type: "raster",
      tiles: [AERIAL_TILES],
      tileSize: 256,
      maxzoom: 16,
      attribution: "Aerial imagery: USGS The National Map",
    });
    map.addLayer({ id: "aerial", type: "raster", source: "aerial", layout: { visibility: "none" } });
    map.addSource("fields", { type: "geojson", data: "./data/fields.geojson", promoteId: "id" });
    map.addLayer({
      id: "fields-fill",
      type: "fill",
      source: "fields",
      paint: {
        "fill-color": ["match", ["get", "grade"], ...GRADE_COLORS, "#999999"] as never,
        "fill-opacity": ["case", ["boolean", ["feature-state", "hover"], false], 0.95, 0.72],
      },
    });
    map.addLayer({
      id: "fields-line",
      type: "line",
      source: "fields",
      paint: {
        "line-color": ["case", ["boolean", ["feature-state", "selected"], false], "#d9a521", "#1c2b22"],
        "line-width": ["case", ["boolean", ["feature-state", "selected"], false], 4, 0.5],
        "line-opacity": ["case", ["boolean", ["feature-state", "selected"], false], 1, 0.45],
      },
    });
    map.addLayer({
      id: "study-box",
      type: "line",
      source: {
        type: "geojson",
        data: {
          type: "Feature",
          properties: {},
          geometry: { type: "LineString", coordinates: [[w, s], [e, s], [e, n], [w, n], [w, s]] },
        },
      },
      paint: { "line-color": "#1c2b22", "line-width": 1.5, "line-dasharray": [3, 3] },
    });
  });

  let hovered: string | null = null;
  let selected: string | null = null;
  const setState = (id: string | null, state: Record<string, boolean>) => {
    if (id !== null) map.setFeatureState({ source: "fields", id }, state);
  };

  map.on("mousemove", "fields-fill", (ev) => {
    const id = (ev.features?.[0]?.properties?.id as string) ?? null;
    if (id === hovered) return;
    setState(hovered, { hover: false });
    hovered = id;
    setState(hovered, { hover: true });
    map.getCanvas().style.cursor = "pointer";
  });
  map.on("mouseleave", "fields-fill", () => {
    setState(hovered, { hover: false });
    hovered = null;
    map.getCanvas().style.cursor = "";
  });
  map.on("click", "fields-fill", (ev) => {
    const id = ev.features?.[0]?.properties?.id as string | undefined;
    if (id) onPick(id);
  });
  // A click on empty map closes the report card.
  map.on("click", (ev) => {
    if (!map.getLayer("fields-fill")) return;
    if (map.queryRenderedFeatures(ev.point, { layers: ["fields-fill"] }).length === 0) onPick(null);
  });

  return {
    map,
    select(id: string | null) {
      setState(selected, { selected: false });
      selected = id;
      // Feature state needs the source loaded; retry once it is.
      const apply = () => setState(selected, { selected: true });
      if (map.getSource("fields") && map.isSourceLoaded("fields")) apply();
      else map.once("idle", apply);
    },
    setAerial(on: boolean) {
      map.setLayoutProperty("aerial", "visibility", on ? "visible" : "none");
      map.setPaintProperty("fields-fill", "fill-opacity", on ? 0.35 : 0.72);
    },
  };
}
