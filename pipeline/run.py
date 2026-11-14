"""Run the whole pipeline: python -m pipeline.run

Needs the national CDL zips (pipeline/fetch_cdl.sh) and cached HLS scenes
(python -m pipeline.hls) in data/raw first.
"""

import json

import numpy as np

from pipeline import cdl, config, export, hls, plan_text, power, soil, validate


def load_sources():
    path = config.ROOT / "pipeline" / "sources.json"
    if path.exists():
        data = json.loads(path.read_text())
        plan_text.SOURCES.update(data.get("sources", {}))
        plan_text.TEXT.update(data.get("text", {}))


def main():
    load_sources()
    fields, history = cdl.run()
    ndvi, snow, pixels = hls.run(fields)
    # Leave out fields too small to sample or too rarely seen to grade.
    seen_share = (~np.isnan(ndvi)).mean(axis=(1, 2))
    keep = (pixels >= hls.MIN_FIELD_PIXELS) & (seen_share >= config.MIN_SEEN_SHARE)
    print(f"{(~keep).sum()} of {len(keep)} outlines left out: outside the study box, or seen in under {config.MIN_SEEN_SHARE:.0%} of weeks")
    fields, history, ndvi, snow = fields[keep].reset_index(drop=True), history[keep], ndvi[keep], snow[keep]
    looks = np.load(config.WORK_DIR / "weekly.npz")["looks"]
    heavy, threshold, rain, trend = power.run()
    classes = cdl.class_table(list(config.YEARS)[-1])
    soil_path = config.WORK_DIR / "soil.json"
    try:
        soils = json.loads(soil_path.read_text()) if soil_path.exists() else soil.run(fields)
        if set(soils) - set(fields.id):  # cached for an older set of outlines
            soils = soil.run(fields)
    except Exception as e:  # the soil panel is optional; the rest must still build
        print("soil step failed, leaving the soil panel out:", repr(e)[:200])
        soils = None
    records, extra, meta = export.write(fields, history, ndvi, snow, heavy, rain, threshold, trend, classes, looks, soils)
    validate.run(fields, history, ndvi, snow, heavy, classes, records, extra, looks)
    print("grades", meta["grades"], "| legume:", classes[extra["legume"]]["name"] if extra["legume"] else None)
    print(f"cropland bare in an average heavy-rain week: {meta['bare_in_heavy_rain_share']:.0%}")


if __name__ == "__main__":
    main()
