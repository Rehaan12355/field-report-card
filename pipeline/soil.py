"""Query soil survey values per field."""

import json

import requests

from pipeline import config

SDA_URL = "https://sdmdataaccess.sc.egov.usda.gov/Tabular/post.rest"
CHUNK = 100


def sda(query):
    r = requests.post(SDA_URL, json={"query": query, "format": "JSON+COLUMNNAME"}, timeout=180)
    r.raise_for_status()
    table = r.json().get("Table", [])
    return [dict(zip(table[0], row)) for row in table[1:]]


def map_units(fields):
    """Soil map unit under each field's centre point."""
    points = fields.to_crs(4326).geometry.representative_point()
    found = {}
    ids = list(fields.id)
    for start in range(0, len(ids), CHUNK):
        values = ",".join(
            f"('{fid}', geometry::Point({p.x:.6f}, {p.y:.6f}, 4326))"
            for fid, p in zip(ids[start : start + CHUNK], points[start : start + CHUNK])
        )
        rows = sda(
            f"SELECT p.id, mu.mukey, mu.muname FROM (VALUES {values}) AS p(id, g) "
            "JOIN mupolygon mp ON mp.mupolygongeo.STIntersects(p.g) = 1 "
            "JOIN mapunit mu ON mu.mukey = mp.mukey"
        )
        for row in rows:
            found[row["id"]] = (row["mukey"], row["muname"])
    return found


def surface_properties(mukeys):
    """Erodibility, organic matter and water-holding capacity of the top soil
    layer of each map unit's main component."""
    keys = ",".join(sorted(set(mukeys)))
    rows = sda(
        "SELECT c.mukey, c.comppct_r, h.hzdept_r, h.kwfact, h.om_r, h.awc_r "
        "FROM component c JOIN chorizon h ON h.cokey = c.cokey "
        f"WHERE c.mukey IN ({keys}) AND c.majcompflag = 'Yes' "
        "ORDER BY c.mukey, c.comppct_r DESC, h.hzdept_r ASC"
    )
    props = {}
    for row in rows:
        # Skip surface litter layers that have no mineral-soil values.
        if row["mukey"] in props or row["om_r"] is None and row["kwfact"] is None:
            continue
        props[row["mukey"]] = row
    return props


def run(fields):
    units = map_units(fields)
    props = surface_properties([m for m, _ in units.values()])
    num = lambda v: None if v in (None, "") else float(v)
    out = {}
    for fid, (mukey, name) in units.items():
        p = props.get(mukey)
        if p:
            out[fid] = {"name": name, "kw": num(p["kwfact"]), "om": num(p["om_r"]), "awc": num(p["awc_r"])}
    (config.WORK_DIR / "soil.json").write_text(json.dumps(out))
    print(f"soil: {len(out)} of {len(fields)} fields matched")
    return out
