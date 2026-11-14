# Design notes

How the site should look, so every part built later matches. Tokens live in
`web/src/style.css`.

## Idea

Feed-sack lettering and a school report card, coloured by the data itself.
The map is the main surface; the report card docks on the right (bottom sheet
on phones). Everything is left-aligned.

## Colour

| Name | Hex | Used for |
|------|-----|----------|
| Lichen paper | `#F1F4EE` | Page background |
| Ink | `#1C2B22` | Text, top bar |
| Bare soil | `#6B4A2B` | Bare weeks |
| Canopy | `#2F7D3B` | Green weeks |
| Washout red | `#C2362B` | Bare weeks that overlap heavy rain |
| Rain | `#2C6FA6` | Heavy-rain marks, climate panel |
| Wheat gold | `#D9A521` | The one accent: selected field, focus ring |

Grades A to F run green, light green, gold, orange, red-brown
(`--grade-a` to `--grade-f`). Always show the letter with the colour, never
colour alone.

## Type

- **Bitter** (slab serif): site name, headings, the grade letter.
- **Public Sans**: everything else, including numbers.
- Scale is 1.25 from 16px. Sentence case everywhere.

## The one bold element

The week ribbon: one row per year, 52 cells across. Green for growing, soil
brown for bare, washout red for bare under heavy rain, hatched for unknown.
Keep everything around it quiet.

## Rules

- The three plans are one comparison table read across rows, not three cards.
- No uppercase labels, no monospace numbers, no decorative dividers.
- No legend or key until the data it explains is on screen.
- Motion only in answer to a click: the ribbon and grade changing when a plan
  is picked. Respect `prefers-reduced-motion`.
- Empty and error states say what is happening and what to do next.
