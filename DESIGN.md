# Design System: Field Report Card

## 1. Visual Theme & Atmosphere

A calm survey instrument: a full-bleed map with one floating report card,
like a clean field notebook laid on a light table. Density is daily-app
balanced (5 of 10), layout is offset and asymmetric (6 of 10: map left, card
right, everything left-aligned), and motion is fluid but restrained (5 of
10). Neutral surfaces stay quiet so the data colours do the talking. The one
signature element is the week ribbon: a row per year, a cell per week.

## 2. Color Palette & Roles

Interface (one neutral family, one accent):

- **Canvas Mist** (#F4F4F5) — page background behind the map and panels
- **Pure Surface** (#FFFFFF) — floating card, top bar, map legend
- **Soft Well** (#F4F4F5) — inset areas inside the card: plan detail, charts
- **Charcoal Ink** (#18181B) — primary text, selected-field outline
- **Muted Steel** (#71717A) — secondary text, notes, axis labels
- **Whisper Border** (#E4E4E7) — 1px structural lines and dividers
- **Evergreen** (#17694B) — the single accent: primary button, selected plan,
  focus ring, links

Data colours (encodings, never decoration, always paired with a word or letter):

- **Canopy** (#2F7D3B) — green weeks
- **Bare Soil** (#6B4A2B) — bare weeks
- **Washout Red** (#C2362B) — bare weeks under heavy rain
- **Rain Blue** (#2C6FA6) — heavy-rain marks
- **Cover Mint** (#8FC9A8) — weeks filled by a cover crop in a plan
- **Grades** A #1F7A3A, B #7FB04A, C #E0B93B, D #D07A2A, F #A8321F

No purple, no neon, no gradients, no pure black.

## 3. Typography Rules

- **Display and body:** Geist — tight tracking (-0.02em) on headings,
  hierarchy from weight (600 to 700) and colour, not size. Body 15 to 16px,
  line-height 1.55, lines under 65 characters.
- **Mono:** Geist Mono — years, week counts and table numbers.
- **Scale:** 12 / 13 / 15 / 18 / 22 / 28px. The grade letter is the only
  large glyph (44px).
- **Banned:** Inter, serif faces, uppercase tracked labels.

## 4. Component Stylings

- **Buttons:** flat. Primary is Evergreen fill with white text, 10px radius,
  44px tall. Secondary is a white pill with a Whisper Border. Active state
  moves down 1px. No glows.
- **Floating card:** Pure Surface, 20px radius, 1px Whisper Border and a
  soft shadow tinted to the canvas (rgba(24,24,27,0.08)). It is the only
  elevated surface besides the legend, because it sits above the map.
- **Sections inside the card:** separated by space and a hairline, not
  nested cards. Soft Well insets hold the plan detail and charts.
- **Plan picker:** a comparison table whose column heads are buttons. The
  selected column gets an Evergreen head and a tinted column.
- **Sliders:** native range inputs with Evergreen accent, label above.
- **Grade block:** rounded square (14px radius) in the grade colour with the
  letter in Geist 700.
- **Loaders:** skeleton blocks shaped like the card header and ribbon, with
  a slow shimmer. No spinners.
- **Empty state:** the overview: what the map shows, one real headline
  number, the grade spread as clickable filters, one button to open an
  example field.
- **Errors:** inline in the card, saying what failed and what to do.

## 5. Layout Principles

- The map fills the viewport under a 56px top bar. The card floats at the
  right, 440px wide, 16px from the edges, scrolling inside itself.
- A grade legend floats at the bottom left of the map.
- CSS Grid for structure; no percentage maths. No element overlaps text.
- Below 768px the card becomes a bottom sheet (48% of the height), the top
  bar keeps only the name and the two controls, and tap targets are at
  least 44px.

## 6. Motion & Interaction

- Easing is a soft spring curve, cubic-bezier(0.22, 1, 0.36, 1), 350 to
  500ms. Only transform and opacity animate, plus fill on ribbon cells.
- One orchestrated moment: when a field opens, its story plays in the card.
  Seven captioned scenes, about 40 seconds: the crops, every week seen from
  space, the weeks under heavy rain, the grade, then each plan recolouring
  the ribbon in place. A segmented bar shows progress; Pause, Read aloud
  (the browser's own voice, off by default) and Skip are always in reach.
  The report card follows, with a button to play the story again.
- Picking a plan recolours the ribbon cells and the grade block in place.
- One perpetual micro-loop: a slow pulse on the dot beside the example-field
  button. The skeleton shimmer runs only while loading.
- Hovering a field shows a small tooltip with its grade, crop and size.
- Everything stops under prefers-reduced-motion.

## 7. Anti-Patterns (Banned)

- No emojis, no Inter, no serif, no pure black
- No neon glows, gradient text or purple accents
- No three-equal-card rows; comparisons are tables
- No fabricated numbers: every figure comes from the pipeline output
- No uppercase eyebrow labels, no "LABEL // YEAR"
- No marketing words ("seamless", "elevate", "next-gen")
- No scroll hints, bouncing arrows or custom cursors
- No colour without a word or letter beside it
