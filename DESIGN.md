---
name: leiðarljós
description: Write one claim. Search it back.
colors:
  ink: "#0b0b0a"
  ink-2: "#12110f"
  cream: "#f4f0e6"
  cream-2: "#e8e2d4"
  gold: "#e6a23c"
  gold-dim: "#9a6410"
  fault: "#c45c4a"
  line: "#2a2824"
  line-2: "#3a3428"
  mute: "#b9b3a6"
  mute-2: "#8d877b"
  panel: "#141310"
  panel-2: "#1a1814"
  paper: "#f6f2e8"
  paper-ink: "#15130f"
  paper-ink-2: "#2a2620"
  paper-gold: "#7f520b"
  paper-gold-soft: "#b07a22"
  paper-line: "#ddd5c3"
  paper-line-2: "#c8bda5"
  paper-mute: "#47423a"
  paper-mute-2: "#5c564b"
  paper-panel: "#efe9dc"
  paper-panel-2: "#e7e0d0"
typography:
  display:
    fontFamily: "Source Serif 4, Iowan Old Style, Palatino, Palatino Linotype, Charter, Georgia, serif"
    fontSize: "clamp(2.1rem, 5vw, 3.4rem)"
    fontWeight: 600
    lineHeight: 1.08
    letterSpacing: "-0.03em"
  headline:
    fontFamily: "Source Serif 4, Iowan Old Style, Palatino, Palatino Linotype, Charter, Georgia, serif"
    fontSize: "clamp(1.45rem, 2.6vw, 1.9rem)"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "-0.03em"
  body:
    fontFamily: "Source Sans 3, system-ui, Segoe UI, Roboto, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 400
    lineHeight: 1.7
  label:
    fontFamily: "Source Serif 4, Iowan Old Style, Palatino, Palatino Linotype, Charter, Georgia, serif"
    fontSize: "0.95rem"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "0"
  nav:
    fontFamily: "Source Sans 3, system-ui, Segoe UI, Roboto, sans-serif"
    fontSize: "0.95rem"
    fontWeight: 400
    lineHeight: 1.4
  ui:
    fontFamily: "Source Sans 3, system-ui, Segoe UI, Roboto, sans-serif"
    fontSize: "0.92rem"
    fontWeight: 400
    lineHeight: 1.3
  button:
    fontFamily: "Source Sans 3, system-ui, Segoe UI, Roboto, sans-serif"
    fontSize: "0.98rem"
    fontWeight: 600
    lineHeight: 1.2
  title:
    fontFamily: "Source Serif 4, Iowan Old Style, Palatino, Palatino Linotype, Charter, Georgia, serif"
    fontSize: "1.2rem"
    fontWeight: 600
    lineHeight: 1.2
  card-title:
    fontFamily: "Source Serif 4, Iowan Old Style, Palatino, Palatino Linotype, Charter, Georgia, serif"
    fontSize: "1.15rem"
    fontWeight: 600
    lineHeight: 1.2
  lead:
    fontFamily: "Source Serif 4, Iowan Old Style, Palatino, Palatino Linotype, Charter, Georgia, serif"
    fontSize: "clamp(1.25rem, 2.4vw, 1.55rem)"
    fontWeight: 400
    lineHeight: 1.45
  figure:
    fontFamily: "Source Serif 4, Iowan Old Style, Palatino, Palatino Linotype, Charter, Georgia, serif"
    fontSize: "clamp(3.2rem, 7vw, 5rem)"
    fontWeight: 600
    lineHeight: 0.9
  docs-title:
    fontFamily: "Source Serif 4, Iowan Old Style, Palatino, Palatino Linotype, Charter, Georgia, serif"
    fontSize: "clamp(2.2rem, 5vw, 3.2rem)"
    fontWeight: 600
    lineHeight: 1.08
  walk:
    fontFamily: "Source Serif 4, Iowan Old Style, Palatino, Palatino Linotype, Charter, Georgia, serif"
    fontSize: "1.35rem"
    fontWeight: 600
    lineHeight: 1.2
  handbook-title:
    fontFamily: "Source Serif 4, Iowan Old Style, Palatino, Palatino Linotype, Charter, Georgia, serif"
    fontSize: "clamp(1.9rem, 4vw, 2.6rem)"
    fontWeight: 600
    lineHeight: 1.1
  section:
    fontFamily: "Source Serif 4, Iowan Old Style, Palatino, Palatino Linotype, Charter, Georgia, serif"
    fontSize: "1.45rem"
    fontWeight: 600
    lineHeight: 1.2
  caption:
    fontFamily: "Source Sans 3, system-ui, Segoe UI, Roboto, sans-serif"
    fontSize: "0.88rem"
    fontWeight: 400
    lineHeight: 1.4
  meta:
    fontFamily: "Source Sans 3, system-ui, Segoe UI, Roboto, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 700
    lineHeight: 1.2
  fig-label:
    fontFamily: "Source Sans 3, system-ui, Segoe UI, Roboto, sans-serif"
    fontSize: "0.72rem"
    fontWeight: 700
    lineHeight: 1.2
  table:
    fontFamily: "Source Sans 3, system-ui, Segoe UI, Roboto, sans-serif"
    fontSize: "0.85rem"
    fontWeight: 600
    lineHeight: 1.3
  mono:
    fontFamily: "IBM Plex Mono, ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
    fontSize: "0.86rem"
    fontWeight: 400
    lineHeight: 1.55
rounded:
  sm: "4px"
  md: "8px"
  term: "2px"
  mark: "6px"
  pill: "999px"
  none: "0"
spacing:
  nav: "1.15rem"
  section: "2.6rem"
  wrap: "2.5rem"
components:
  button-primary:
    backgroundColor: "{colors.gold}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    padding: "0.7rem 1.2rem"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.cream}"
    rounded: "{rounded.sm}"
    padding: "0.7rem 1.2rem"
  nav:
    backgroundColor: "transparent"
    textColor: "{colors.cream}"
    padding: "1.15rem 0 1rem"
---

# Design System: leiðarljós

## Overview

**Creative North Star: "A field journal on a dark desk"**

The page is a night desk: near-black ink, warm cream type, one gold rule. Serif headlines carry the claim. Sans carries the reading. Mono carries the specimen and the install lines. Density is a journal, not a dashboard. The pin mark sits behind the page at low opacity, below the nav so it never covers the search box, and does not compete with the claim.

**Key Characteristics:**

- Ink ground, cream text, gold used as a rule, a kicker, and the primary action.
- Source Serif 4 for headings, Source Sans 3 for reading, IBM Plex Mono for commands.
- One nav and one stylesheet across the landing page, the docs, and the handbook.
- Flat panels. Depth is a 1px line, not a shadow.

## Colors

The palette is the custom properties in `site.css`. Gold is the only accent.

### Primary

- **Desk gold** (`#e6a23c`): the primary button, the kicker, the current nav item, the rule under the claim, and the large measurement figures.
- **Dim gold** (`#9a6410`): hover borders on cards. Not body text.
- **Fault** (`#c45c4a`): a failed line in the sitting specimen. Not body text.

### Neutral

- **Ink** (`#0b0b0a`): page ground and primary-button text.
- **Ink 2** (`#12110f`): a slightly lifted ink, reserved.
- **Cream** (`#f4f0e6`): headings, buttons' ghost text, and code.
- **Cream 2** (`#e8e2d4`): the lead line when it is not the serif hero.
- **Mute** (`#b9b3a6`): body copy, captions, footer.
- **Mute 2** (`#8d877b`): small labels on the install bar and the specimen title.
- **Panel** (`#141310`) and **Panel 2** (`#1a1814`): specimen, install block, and cards.
- **Line** (`#2a2824`) and **Line 2** (`#3a3428`): hairline borders.

**The One Accent Rule.** Gold marks the action and the figure. It does not recolor body paragraphs.

### Paper scheme (prefers-color-scheme: light)

The same page on paper: cream ground, ink type. Pages use role tokens (`--bg`, `--fg`, `--accent`, `--accent-fill`, `--line`, `--mute`, `--panel`), and the light media query swaps their values. Terminal surfaces (specimen, install block, `pre`) stay ink in both schemes.

- **Paper** (`#f6f2e8`): page ground. **Paper panel** (`#efe9dc`) and **Paper panel 2** (`#e7e0d0`): cards and inputs.
- **Paper ink** (`#15130f`): headings and strong text. **Paper ink 2** (`#2a2620`): the lead line.
- **Paper gold** (`#7f520b`): gold as text on paper (kicker, nav item, timeline line, figure labels); 6.0:1 on paper. Desk gold (`#e6a23c`) stays the fill for the primary button and the rule under the claim.
- **Paper gold soft** (`#b07a22`): hover borders. Not text.
- **Paper mute** (`#47423a`): body copy, 8.9:1. **Paper mute 2** (`#5c564b`): small labels, 6.5:1.
- **Paper line** (`#ddd5c3`) and **Paper line 2** (`#c8bda5`): hairline borders.
- The crate marks keep their ink tiles on paper; the timeline line runs behind them and shows only between icons.

## Typography

**Display Font:** Source Serif 4 (with Iowan Old Style, Palatino, Charter, Georgia)
**Body Font:** Source Sans 3 (with system-ui)
**Label/Mono Font:** IBM Plex Mono (with ui-monospace)

**Character:** A serif claim, a sans explanation, a mono specimen. The three faces stay the ones `site.css` already names.

### Hierarchy

- **Display** (600, `clamp(2.1rem, 5vw, 3.4rem)`, 1.08): the claim heading.
- **Headline** (600, `clamp(1.45rem, 2.6vw, 1.9rem)`): section headings.
- **Body** (400, 1.0625rem, 1.7, tracking 0.008em): reading text, measure 66ch.
- **Label** (600, 0.95rem, serif, no tracking): the line above a heading. It is a sentence, not a chip.
- **Mono** (400, 0.86rem, 1.55): install lines and the sitting specimen.

**The Recorded Faces Rule.** Do not swap these faces for another display family. The serif, the sans, and the mono in `site.css` are the system.

## Layout

The page is a centered column: `min(72rem, calc(100% - 2.5rem))` on the landing, `min(44rem, calc(100% - 2.5rem))` on docs and the handbook. The nav is a wrapping row: brand, links, search. At 880px the three-step loop and the measure pair stack. At 720px the docs cards and the field map stack, and table cells may wrap. Command blocks scroll inside the column rather than widening the page.

## Elevation & Depth

The system is flat. Panels are a darker ink with a 1px line. The pin is a fixed watermark, not a layer the reader clicks.

### Named Rules

**The Flat Desk Rule.** Do not add drop shadows. A border is the edge of a plate.

## Shapes

Buttons and the search field use a 4px corner. Cards, the install block, and docs cards use 8px. The specimen frame uses 2px, closer to a terminal. Doc chips use a full pill.

## Components

### Buttons

- **Shape:** a short corner (4px).
- **Primary:** gold ground, ink text, padding 0.7rem 1.2rem.
- **Hover / Focus:** the gold button brightens slightly. Focus is a 2px gold outline, 3px offset.
- **Ghost:** transparent, cream text, line-2 border. Hover turns the border and the text gold.

### Cards / Containers

- **Corner Style:** 8px on docs cards and handbook notes.
- **Background:** panel.
- **Shadow Strategy:** none. A 1px line.
- **Internal Padding:** about 1.15rem to 1.3rem.

### Inputs / Fields

- **Style:** panel ground, line border, 4px corner, cream text.
- **Focus:** 2px gold outline.

### Navigation

One bar: the serif brand leiðarljós, the same link list, a search field that submits to `/docs/search/`. The current page is gold. The bar wraps instead of overflowing. The handbook copies this bar from `org/templates/nav.html`.

## Do's and Don'ts

### Do:

- **Do** keep ink, cream, and gold as defined in `site.css`.
- **Do** keep Source Serif 4, Source Sans 3, and IBM Plex Mono.
- **Do** use the same nav and `site.css` on the landing page, the docs, and the handbook.

### Don't:

- **Don't** replace the palette with a different gold or a paper-white page.
- **Don't** replace the serif, the sans, or the mono with another display family.
- **Don't** publish a handbook page whose nav or stylesheet bypasses the org templates.
