import * as maplibregl from "maplibre-gl";

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
