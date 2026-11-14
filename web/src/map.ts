import * as maplibregl from "maplibre-gl";
// The bundler does not pick up MapLibre's worker on its own, so bundle it
// here and tell MapLibre where it ended up.
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url";

maplibregl.setWorkerUrl(workerUrl);

// OpenFreeMap: free vector basemap, no API key. The pale style keeps the
// field grade colours as the loudest thing on the map.
const BASEMAP_STYLE = "https://tiles.openfreemap.org/styles/positron";
// USGS aerial imagery, public domain, no API key.
const AERIAL_TILES = "https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}";

const GRADE_COLORS = ["A", "#1f7a3a", "B", "#7fb04a", "C", "#e0b93b", "D", "#d07a2a", "F", "#a8321f"];

export type FieldProps = { id: string; grade: string; ha: number; crop: string; bare: number; exposed: number };
type FieldCollection = GeoJSON.FeatureCollection<GeoJSON.Polygon | GeoJSON.MultiPolygon, FieldProps>;

function bboxOf(geometry: GeoJSON.Polygon | GeoJSON.MultiPolygon): [number, number, number, number] {
  let [w, s, e, n] = [180, 90, -180, -90];
  const rings = geometry.type === "Polygon" ? geometry.coordinates : geometry.coordinates.flat();
  for (const ring of rings)
    for (const [x, y] of ring) {
      w = Math.min(w, x);
      e = Math.max(e, x);
      s = Math.min(s, y);
      n = Math.max(n, y);
    }
  return [w, s, e, n];
}

/** Room to leave for the report card, so the map never hides behind it. */
function cardPadding() {
  const card = document.getElementById("card") as HTMLElement;
  const wide = window.matchMedia("(min-width: 768px)").matches;
  return { top: 40, bottom: 40, left: 40, right: wide ? card.offsetWidth + 56 : 40 };
}

export function createMap(container: string, fields: FieldCollection, onPick: (id: string | null) => void) {
  const boxes = new Map(fields.features.map((f) => [f.properties.id, bboxOf(f.geometry)]));
  const home = fields.features.reduce<[number, number, number, number]>(
    (b, f) => {
      const [w, s, e, n] = boxes.get(f.properties.id)!;
      return [Math.min(b[0], w), Math.min(b[1], s), Math.max(b[2], e), Math.max(b[3], n)];
    },
    [180, 90, -180, -90],
  );
  const map = new maplibregl.Map({
    container,
    style: BASEMAP_STYLE,
    bounds: home,
    fitBoundsOptions: { padding: cardPadding() },
  });
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-left");
  map.addControl(new maplibregl.ScaleControl({ unit: "metric" }), "bottom-left");

  let filter: string | null = null;
  let aerial = false;
  const fillOpacity = () => {
    const base = aerial ? 0.4 : 0.78;
    const shown: unknown = filter ? ["case", ["==", ["get", "grade"], filter], base, 0.08] : base;
    return ["case", ["boolean", ["feature-state", "hover"], false], 1, shown] as never;
  };

  map.on("load", () => {
    map.addSource("aerial", {
      type: "raster",
      tiles: [AERIAL_TILES],
      tileSize: 256,
      maxzoom: 16,
      attribution: "Aerial imagery: USGS The National Map",
    });
    map.addLayer({ id: "aerial", type: "raster", source: "aerial", layout: { visibility: "none" } });
    map.addSource("fields", { type: "geojson", data: fields, promoteId: "id" });
    map.addLayer({
      id: "fields-fill",
      type: "fill",
      source: "fields",
      paint: {
        "fill-color": ["match", ["get", "grade"], ...GRADE_COLORS, "#999999"] as never,
        "fill-opacity": fillOpacity(),
      },
    });
    map.addLayer({
      id: "fields-line",
      type: "line",
      source: "fields",
      paint: { "line-color": "#ffffff", "line-width": 0.6, "line-opacity": 0.7 },
    });
    // The selected field: a dark outline over a white halo, readable on any grade colour.
    map.addLayer({
      id: "selected-halo",
      type: "line",
      source: "fields",
      paint: {
        "line-color": "#ffffff",
        "line-width": 7,
        "line-opacity": ["case", ["boolean", ["feature-state", "selected"], false], 1, 0],
      },
    });
    map.addLayer({
      id: "selected-line",
      type: "line",
      source: "fields",
      paint: {
        "line-color": "#18181b",
        "line-width": 3,
        "line-opacity": ["case", ["boolean", ["feature-state", "selected"], false], 1, 0],
      },
    });
  });

  let hovered: string | null = null;
  let selected: string | null = null;
  const setState = (id: string | null, state: Record<string, boolean>) => {
    if (id !== null && map.getSource("fields")) map.setFeatureState({ source: "fields", id }, state);
  };
  const tip = new maplibregl.Popup({ closeButton: false, closeOnClick: false, offset: 14, className: "tip" });

  map.on("mousemove", "fields-fill", (ev) => {
    const p = ev.features?.[0]?.properties as FieldProps | undefined;
    if (!p) return;
    tip
      .setLngLat(ev.lngLat)
      .setHTML(
        `<b class="grade-chip grade-${p.grade}">${p.grade}</b>
         <span>${p.crop}<small>${Math.round(p.ha)} ha, bare ${Math.round(p.bare)} weeks a year</small></span>`,
      )
      .addTo(map);
    if (p.id === hovered) return;
    setState(hovered, { hover: false });
    hovered = p.id;
    setState(hovered, { hover: true });
    map.getCanvas().style.cursor = "pointer";
  });
  map.on("mouseleave", "fields-fill", () => {
    setState(hovered, { hover: false });
    hovered = null;
    tip.remove();
    map.getCanvas().style.cursor = "";
  });
  map.on("click", "fields-fill", (ev) => {
    const id = ev.features?.[0]?.properties?.id as string | undefined;
    if (id) onPick(id);
  });

  return {
    map,
    select(id: string | null) {
      setState(selected, { selected: false });
      selected = id;
      const apply = () => setState(selected, { selected: true });
      if (map.getSource("fields") && map.isSourceLoaded("fields")) apply();
      else map.once("idle", apply);
      const box = id ? boxes.get(id) : home;
      if (box) map.fitBounds(box, { padding: cardPadding(), maxZoom: 12.5, duration: 900 });
    },
    setAerial(on: boolean) {
      aerial = on;
      map.setLayoutProperty("aerial", "visibility", on ? "visible" : "none");
      map.setPaintProperty("fields-fill", "fill-opacity", fillOpacity());
    },
    setGradeFilter(grade: string | null) {
      filter = grade;
      map.setPaintProperty("fields-fill", "fill-opacity", fillOpacity());
    },
  };
}
