# Design system

The visual identity for the Resume Strength Analyzer. Every rule here exists as a CSS
custom property in [`app.css`](../resume_analyzer/web/static/css/app.css); nothing in a
template should invent a colour, a radius or a pixel gap of its own.

## 1. The idea

The product reads a document and tells you an uncomfortable truth about it. The interface
should feel like an **instrument**, not a form: dark, precise, and confident, with colour
used only where it carries meaning.

So: a deep navy canvas lit by a soft gradient mesh, content floating on translucent glass
panels, one vivid signature gradient, and a strict colour language for scores.

**Texture language: glass on a gradient mesh.** One language, used everywhere. No flat
blocks, no skeuomorphic depth, no mixing. Panels are `--surface` (a translucent slate) with
a hairline `--line` border and a soft shadow; the canvas behind them carries three fixed
radial blooms that never scroll.

## 2. Colour

### Canvas and ink

| Token | Value | Use |
|---|---|---|
| `--bg` | `#080B16` | Page canvas, under the mesh |
| `--bg-mesh-a/b/c` | violet / pink / cyan blooms | Fixed radial gradients on `body::before` |
| `--surface` | `rgba(19, 24, 43, .72)` | Panels, glass |
| `--surface-2` | `rgba(255, 255, 255, .045)` | Wells: inputs, evidence, code |
| `--surface-3` | `rgba(255, 255, 255, .08)` | Hover wells, track fills |
| `--line` | `rgba(255, 255, 255, .10)` | Hairline borders |
| `--line-strong` | `rgba(255, 255, 255, .18)` | Focused / hovered borders |
| `--ink` | `#EEF1F8` | Primary text |
| `--ink-2` | `#9AA6BF` | Secondary text |
| `--ink-3` | `#6B7691` | Tertiary, captions, table headers |

This is a **single-mode dark interface**. There is no light theme: two themes means two
sets of screenshots to verify and twice the surface for a contrast mistake to hide in.
Print is the exception — `@media print` flips to black on white, because a report someone
prints should not empty an ink cartridge.

### Signature gradient

```css
--signature: linear-gradient(120deg, #A78BFA 0%, #F472B6 52%, #FF9F6B 100%);
```

Violet → pink → warm amber. Used for: the brand mark, the primary button, the hero
headline's emphasised clause, and the thin rule under section eyebrows. Nowhere else —
a gradient that appears on every surface stops being a signature.

### Score dimensions

Each of the four scores owns a hue, used **consistently everywhere that score appears** —
its card icon, its section heading, and the source tag on any improvement it suggests.

| Dimension | Token | Hue |
|---|---|---|
| Overall match | `--dim-overall` | `#A78BFA` violet |
| Strength | `--dim-strength` | `#F472B6` pink |
| ATS compatibility | `--dim-ats` | `#22D3EE` cyan |
| Job-description fit | `--dim-jd` | `#A3E635` lime |

Dimension hue is always used **quietly**: as a glyph colour on a 12%-alpha tile of the same
hue, or as a 1px rule. It identifies; it does not shout.

### Score bands

Quality is a separate axis from identity. Bands colour the **arcs, the bars and the band
pill** — the things that say *how good is this number*.

| Band | Token | Range |
|---|---|---|
| Excellent | `--band-excellent` `#2EE6A8` | ≥ 85 |
| Strong | `--band-strong` `#7EE787` | ≥ 70 |
| Fair | `--band-fair` `#F5C451` | ≥ 55 |
| Weak | `--band-weak` `#FF9A5A` | ≥ 35 |
| Poor | `--band-poor` `#FF6B6B` | < 35 |

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
--t-xs: .75rem    captions, table headers, pills
--t-sm: .8125rem  secondary copy, hints
--t-base: .9375rem body
--t-md: 1.0625rem lede
--t-lg: 1.375rem  card headings
--t-xl: 1.875rem  page headings
```

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
| Score arcs | `stroke-dashoffset` animates from empty to the value over 900ms, staggered 90ms per card |
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
