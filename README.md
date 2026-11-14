# Field Report Card

Click a farm field and see its crop history read from space, how many weeks a
year its soil sits bare, how that lines up with heavy rain, a soil-health
grade, and three planting plans to compare.

Built for the NASA Space Apps Challenge 2026 (Seattle), challenge
*Field Shift: Adapting Farms with NASA Data*.

**Live site:** https://rehaan12355.github.io/field-report-card/

> Status: early build. The map loads; field data is not in yet.

## How it works

A Python pipeline runs on a laptop over one study box in Whitman County,
Washington, and writes small JSON and GeoJSON files. A static web map loads
them. Nothing runs on a server.

- **NASA HLS** (Harmonized Landsat and Sentinel-2) vegetation indices: weekly greenness per field
- **NASA POWER**: daily climate, used to find heavy-rain weeks
- **USDA Cropland Data Layer**: the crop grown each year
- **USDA soil survey (SSURGO)**: soil properties

See [docs/methods.md](docs/methods.md) for the science and
[DATA_SOURCES.md](DATA_SOURCES.md) for every dataset.

The grade is a screening tool, not a soil test. Check any plan with your local
extension office or conservation district.

## Run it

Needs Python 3.11 or newer and Node 20 or newer.

```sh
make setup   # Python virtual environment and web dependencies
make test    # pipeline tests
make web     # local map at http://localhost:5173
make build   # production build in web/dist
make data    # run the pipeline (needs a NASA Earthdata login, see .env.example)
```

## AI use

This project was built with help from AI tools. See [AI_USE.md](AI_USE.md).

## License

MIT, see [LICENSE](LICENSE).
