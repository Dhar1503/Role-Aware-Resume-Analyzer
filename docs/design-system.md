# Design system

The visual identity for the Resume Strength Analyzer. Every rule here exists as a CSS
custom property in [`app.css`](../resume_analyzer/web/static/css/app.css); nothing in a
template should invent a colour, a radius or a pixel gap of its own.

## 1. The idea

The product reads a document and tells you an uncomfortable truth about it. The interface
should feel like an **instrument**, not a form: bright, precise and optimistic, with
colour used only where it carries meaning.

So: a warm cream canvas lit by a soft gradient mesh, content floating on frosted white
panels, one vivid signature gradient, and a strict colour language for scores.

**Texture language: frosted panels on a gradient mesh.** One language, used everywhere. No
flat blocks, no skeuomorphic depth, no mixing. Panels are `--surface` (translucent white)
with a hairline `--line` border and a soft warm-tinted shadow; the canvas behind them
carries three fixed radial blooms that never scroll.

The canvas is deliberately **not** `#FFFFFF`. Stark white reads as clinical and glares next
to the signature gradient; a warm cream keeps the page bright without that, and makes the
white panels register as raised surfaces rather than as the page itself.

## 2. Colour

### Canvas and ink

| Token | Value | Use |
|---|---|---|
| `--bg` | `#FDF9F4` | Warm cream page canvas, under the mesh |
| mesh blooms | violet / pink / amber | Fixed radial gradients on `body::before` |
| `--surface` | `rgba(255, 255, 255, .86)` | Panels, frosted white |
| `--surface-2` | `rgba(38, 28, 62, .045)` | Wells: inputs, evidence, code |
| `--surface-3` | `rgba(38, 28, 62, .085)` | Hover wells, track fills |
| `--line` | `rgba(38, 28, 62, .12)` | Hairline borders |
| `--line-strong` | `rgba(38, 28, 62, .26)` | Focused / hovered borders |
| `--ink` | `#1E1830` | Primary text — **14.9:1** on `--bg` |
| `--ink-2` | `#57506E` | Secondary text — **7.0:1** |
| `--ink-3` | `#6E6685` | Tertiary, captions, table headers — **5.2:1** |

The ink colours are chosen for light, not inverted from the previous dark set. A palette
that reads well as light-on-dark goes muddy when flipped, because the eye tolerates far
less contrast loss against a bright background.

This is a **single light theme**. There is no dark mode: two themes means two sets of
screenshots to verify and twice the surface for a contrast mistake to hide in. Print is the
exception — `@media print` drops to plain black on white.

### Signature gradient

```css
--signature: linear-gradient(120deg, #7C3AED 0%, #DB2777 52%, #EA580C 100%);
```

Violet → pink → orange. Used for: the brand mark, the primary button, the hero headline's
emphasised clause, the numbered step markers on the two forms, and the thin rule under
section eyebrows. Nowhere else — a gradient that appears on every surface stops being a
signature.

These stops are deeper than the dark theme's pastel version of the same ramp. Against cream
a pastel gradient washes out; against black it glowed. The gradient now carries **white**
text on the primary button, where the dark theme used near-black.

### Score dimensions

Each of the four scores owns a hue, used **consistently everywhere that score appears** —
its card icon, its section heading, and the source tag on any improvement it suggests.

| Dimension | Token | Hue |
|---|---|---|
| Overall match | `--dim-overall` | `#7C3AED` violet |
| Strength | `--dim-strength` | `#DB2777` pink |
| ATS compatibility | `--dim-ats` | `#0E7490` cyan |
| Job-description fit | `--dim-jd` | `#4D7C0F` lime |

Dimension hue is always used **quietly**: as a glyph colour on a ~13%-alpha tile of the
same hue, or as a thin rule. It identifies; it does not shout.

Each is a darkened version of the dark theme's hue, because these are used as *glyph and
label colours against white*. The old cyan `#22D3EE` and lime `#A3E635` were right on
black and are close to illegible on cream.

### Score bands

Quality is a separate axis from identity. Bands colour the **arcs, the bars and the band
pill** — the things that say *how good is this number*.

Each band has **two** variants, and confusing them is the single easiest way to break a
light theme:

| Band | Fill (`--band-*`) | Ink (`--band-*-ink`) | Range |
|---|---|---|---|
| Excellent | `#0D9488` | `#0F766E` | ≥ 85 |
| Strong | `#16A34A` | `#15803D` | ≥ 70 |
| Fair | `#D97706` | `#B45309` | ≥ 55 |
| Weak | `#EA580C` | `#C2410C` | ≥ 35 |
| Poor | `#DC2626` | `#B91C1C` | < 35 |

The **fill** variant colours large shapes — score arcs, breakdown bars, the group progress
rule — where saturation reads as energy. The **ink** variant colours small text — band
pills, status pills, score numerals, the status column of the keyword table — where the
requirement is ≥ 4.5:1 against white, not mere visibility. A `.band-*` class sets both
`--band` and `--band-ink`, so each component takes whichever its job needs.

**Why two axes.** A score card carries both: the arc is band-coloured, so a weak ATS score
looks alarming whatever dimension it belongs to, while the icon tile is dimension-coloured,
so you can find the ATS number at a glance on a crowded page. Keeping them separate means
neither has to compromise. Status pills (`pass` / `warn` / `fail` / `na`) reuse the band
palette: pass → strong, warn → fair, fail → poor, na → `--ink-3`.

## 3. Typography

Loaded from Google Fonts, but treated as an **enhancement, never a dependency**:

- `app.css` is linked first, so our own styles never wait on a third party;
- the Google stylesheet is fetched non-render-blocking (`media="print"`, promoted to `all`
  on load, with a `<noscript>` fallback), so a slow or blocked `fonts.googleapis.com`
  costs the typeface, not the page;
- `display=swap` means text paints immediately in the fallback;
- every `--font-*` token carries a full fallback chain, and no rule anywhere names a
  Google font without one.

Verified by blocking `fonts.googleapis.com` and `fonts.gstatic.com` with a cold cache: the
page still loads (faster, in fact — 0.20s to `load` against 0.66s), renders completely, and
the display stack resolves to Segoe UI. The fallback render is near-indistinguishable from
the webfont one at headline size.

| Role | Family | Weights | Notes |
|---|---|---|---|
| Display | **Bricolage Grotesque** | 600, 700, 800 | Headings, score numerals, the brand. A grotesque with deliberate quirks — it gives the product a face instead of a default. |
| Body | **Public Sans** | 400, 500, 600 | Body copy, labels, tables. Built for dense government forms, which is exactly the job here. |
| Mono | **JetBrains Mono** | 400 | The parser view, evidence lines, file names. |

Scale, all `rem`, all tokens:

```
--t-xs: .78rem    captions, table headers, pills
--t-sm: .875rem   secondary copy, hints
--t-base: 1rem    body
--t-md: 1.125rem  lede
--t-lg: 1.4rem    card headings
--t-xl: 1.95rem   page headings
```

The scale sits one notch above the dark theme's. 15px body was thin for a page this
text-dense, and dark-on-light wants marginally more size to read as comfortably as
light-on-dark did.

The hero headline is the one size outside the scale: `clamp(1.95rem, 3.5vw, 2.7rem)`, so it
fills a desktop column without swallowing the first screen on a phone.

Score numerals use `font-variant-numeric: tabular-nums` so a count-up animation does not
make the layout jitter.

## 4. Spacing and radius

One scale, no ad-hoc pixels:

```
--s-1: 4px   --s-2: 8px   --s-3: 12px  --s-4: 16px  --s-5: 24px
--s-6: 32px  --s-7: 48px  --s-8: 64px  --s-9: 96px

--r-sm: 10px   pills, small controls
--r-md: 14px   inputs, wells, rows
--r-lg: 20px   panels
--r-xl: 28px   hero, feature panels
--r-full: 999px
```

Elevation is two shadows only: `--shadow` for resting panels, `--shadow-lift` for hover.

## 5. Motion

Polish, not noise. Every animation is ≤ 900ms, eased, and runs **once** on load.

| Interaction | Behaviour |
|---|---|
| Score arcs | `stroke-dashoffset` animates from empty to the value over 900ms, staggered 90ms per card. The glow is a soft drop-shadow; the dark theme's bloom only worked against black |
| Score numerals | Count up from 0, `requestAnimationFrame`, same duration as the arc |
| Breakdown bars | Width grows from 0 on load |
| Cards | `translateY(-2px)` + `--shadow-lift` on hover, 180ms |
| Accordions | Content fades and slides 6px on open, CSS-only |
| Buttons | Signature gradient shifts on hover; press dips 1px |

All of it sits behind `@media (prefers-reduced-motion: reduce)`, which sets every duration
to `0.01ms`. The **final state is always what the server rendered** — arcs carry their real
`stroke-dasharray` and numerals their real value in the HTML, so with JavaScript off or
animation disabled the page is correct, just static.

## 6. No-JavaScript contract

Core functionality never depends on `app.js`:

- upload, category choice, JD paste and submit are a plain `<form method="post">`;
- category-specific inputs ship `hidden` and `disabled`, and JavaScript reveals the set
  belonging to the chosen category. Without it they stay hidden and the analysis still runs —
  those fields only feed eligibility gates, which then report `unknown` rather than failing;
- accordions are native `<details>`;
- the builder's "add another row" is the only JS-only affordance, and the form ships with enough blank rows to be usable without it;
- every score, bar and arc renders at its true value server-side.

## 7. Responsive

Fluid down to **320px**, verified at 320 / 390 / 480 / 768 / 1024 / 1280 / 1600 with a check
that nothing overflows the viewport. Every `auto-fit` grid uses `minmax(min(Npx, 100%), 1fr)`
so a fixed column floor can never be wider than the screen.

Breakpoints:

| Width | Change |
|---|---|
| 1024px | Hero stacks; the preview card drops its tilt and float |
| 760px | Score grid goes two across, brand wordmark hides, check rows stack |
| 560px | Score cards turn horizontal — arc left, text right — so four scores are not four full screens |
| 460px | Single column throughout, panel padding tightens |

Tables that cannot compress — the keyword match, the extracted facts — scroll horizontally
inside their panel rather than forcing the page to.
