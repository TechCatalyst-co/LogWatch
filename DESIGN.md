---
name: TheLogWatch
description: Every device is a line, every log a stop, every verdict a line colour.
colors:
  porcelain: "#F4F1EA"
  porcelain-dim: "#C9CEE4"
  porcelain-faint: "#8F98BC"
  line-green: "#22B14C"
  line-cobalt: "#2F6BFF"
  line-amber: "#FFC20E"
  line-scarlet: "#E21D2D"
  line-green-tint: "#5FD884"
  line-cobalt-tint: "#8DABFF"
  line-amber-tint: "#FFD45C"
  line-scarlet-tint: "#FF7A82"
  on-line-green: "#05200E"
  on-line-amber: "#2A1E00"
  midnight: "#0B1230"
  midnight-panel: "#0F1940"
  midnight-raised: "#15214F"
  midnight-sunk: "#070C22"
  hairline: "rgba(244,241,234,.14)"
  hairline-strong: "rgba(244,241,234,.26)"
typography:
  display:
    fontFamily: "Overpass, Helvetica Neue, Arial, system-ui, sans-serif"
    fontSize: "52px"
    fontWeight: 800
    lineHeight: 1
    letterSpacing: "-0.02em"
    fontFeature: "tnum"
  headline:
    fontFamily: "Overpass, Helvetica Neue, Arial, system-ui, sans-serif"
    fontSize: "26px"
    fontWeight: 800
    lineHeight: 1.15
  title:
    fontFamily: "Overpass, Helvetica Neue, Arial, system-ui, sans-serif"
    fontSize: "15.5px"
    fontWeight: 700
    lineHeight: 1.3
  body:
    fontFamily: "Overpass, Helvetica Neue, Arial, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.45
    fontFeature: "tnum"
  label:
    fontFamily: "Overpass, Helvetica Neue, Arial, system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 800
    lineHeight: 1.2
    letterSpacing: "0.11em"
  button:
    fontFamily: "Overpass, Helvetica Neue, Arial, system-ui, sans-serif"
    fontSize: "12.5px"
    fontWeight: 700
    letterSpacing: "0.08em"
  pill:
    fontFamily: "Overpass, Helvetica Neue, Arial, system-ui, sans-serif"
    fontSize: "11.5px"
    fontWeight: 800
    lineHeight: 1.4
    letterSpacing: "0.07em"
  station:
    fontFamily: "Overpass, Helvetica Neue, Arial, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 800
    letterSpacing: "0.05em"
  mono:
    fontFamily: "Overpass Mono, ui-monospace, SF Mono, Consolas, monospace"
    fontSize: "12.5px"
    fontWeight: 400
    lineHeight: 1.55
rounded:
  badge: "4px"
  pill: "5px"
  code: "6px"
  button: "7px"
  field: "8px"
  card: "10px"
  panel: "12px"
  sheet: "14px"
  round: "999px"
spacing:
  xs: "6px"
  sm: "8px"
  md: "12px"
  gutter: "14px"
  lg: "16px"
  xl: "20px"
  2xl: "24px"
components:
  button-primary:
    backgroundColor: "{colors.porcelain}"
    textColor: "{colors.midnight}"
    typography: "{typography.button}"
    rounded: "{rounded.button}"
    padding: "8px 12px 7px"
  button-primary-hover:
    backgroundColor: "#FFFFFF"
    textColor: "{colors.midnight}"
  button-outline:
    backgroundColor: "transparent"
    textColor: "{colors.porcelain}"
    typography: "{typography.button}"
    rounded: "{rounded.button}"
    padding: "8px 12px 7px"
  button-outline-hover:
    backgroundColor: "rgba(244,241,234,.06)"
    textColor: "{colors.porcelain}"
  pill-normal:
    backgroundColor: "{colors.line-green}"
    textColor: "{colors.on-line-green}"
    typography: "{typography.pill}"
    rounded: "{rounded.pill}"
    padding: "3px 8px 2px 6px"
  pill-fyi:
    backgroundColor: "{colors.line-cobalt}"
    textColor: "#FFFFFF"
    typography: "{typography.pill}"
    rounded: "{rounded.pill}"
    padding: "3px 8px 2px 6px"
  pill-worth-a-look:
    backgroundColor: "{colors.line-amber}"
    textColor: "{colors.on-line-amber}"
    typography: "{typography.pill}"
    rounded: "{rounded.pill}"
    padding: "3px 8px 2px 6px"
  pill-act-now:
    backgroundColor: "{colors.line-scarlet}"
    textColor: "#FFFFFF"
    typography: "{typography.pill}"
    rounded: "{rounded.pill}"
    padding: "3px 8px 2px 6px"
  filter-chip:
    backgroundColor: "transparent"
    textColor: "{colors.porcelain-dim}"
    rounded: "{rounded.round}"
    padding: "4px 11px 3px"
  filter-chip-on:
    backgroundColor: "{colors.porcelain}"
    textColor: "{colors.midnight}"
    rounded: "{rounded.round}"
  panel:
    backgroundColor: "{colors.midnight-panel}"
    textColor: "{colors.porcelain}"
    rounded: "{rounded.panel}"
  input-field:
    backgroundColor: "{colors.midnight-sunk}"
    textColor: "{colors.porcelain}"
    rounded: "{rounded.field}"
    padding: "12px 14px 11px"
  fare-card:
    backgroundColor: "{colors.porcelain}"
    textColor: "{colors.midnight}"
    rounded: "{rounded.card}"
    padding: "26px 22px 20px"
  stop:
    size: "20px"
    rounded: "{rounded.round}"
---

# Design System: TheLogWatch

## Overview

**Creative North Star: "The Midnight Transit Diagram"**

TheLogWatch is drawn as a night-time metro map. Each device is a line, each log is a stop on it, and each verdict is a line colour. The ground is midnight-blue enamel with porcelain-white type and hairline-ruled panels, the way a station sign or line diagram is lettered. The world rejects the graphite SOC dashboard with a single blue accent: here colour is never decoration and never brand chrome. The four line inks *are* the four verdicts (Normal, FYI, Worth a look, Act now), and everything that is not a verdict is porcelain.

The enamel finish is adapted on purpose: it renders as a flat midnight field, not as gloss, grain or sheen, so text and line inks keep their contrast on a bright booth TV read from metres away. Density is a working big-screen diagram (dashboard fills exactly one viewport, panels scroll internally), and the visitor phone page is the same world at a single narrow column.

The signature moves are transit-native: vertical line strips threading a device roster, a horizontal line diagram with stops coloured by worst verdict, Act-now stops drawn as interchange rings, line pills with drawn glyphs, and the four-ink band that appears only as the complete network.

**Key Characteristics:**
- Flat midnight enamel field; depth by tonal steps and porcelain hairlines, not shadows.
- Four line inks reserved for verdicts; porcelain carries every chrome state.
- Overpass (Highway Gothic lineage) in tracked caps for labels, signs and station names; Overpass Mono only for raw log text.
- Every verdict carries ink + drawn glyph + word; never colour alone.
- Big, readable-across-the-room numerals and titles; tabular figures throughout.

## Colors

A midnight enamel ground, porcelain ink, and four saturated transit line colours that mean exactly one thing each.

### Primary
- **Porcelain** (#F4F1EA): all type of record, the primary button fill, active toggles and filters, the Challenge-mode banner, selection, caret, focus ring, the PATTERN badge, and the fare-card face. The colour of the system's voice.
- **Porcelain Dim** (#C9CEE4): secondary text, labels, panel asides, inactive filter text, advice icons.
- **Porcelain Faint** (#8F98BC): timestamps, metadata, sub-captions, chart axis text, and the band on non-verdict line-status tiles.

### Secondary (the four line inks; verdicts only)
- **Line Green** (#22B14C): Normal. Text on it uses Deep Green Ink (#05200E).
- **Line Cobalt** (#2F6BFF): FYI. Text on it is white.
- **Line Amber** (#FFC20E): Worth a look. Text on it uses Deep Amber Ink (#2A1E00).
- **Line Scarlet** (#E21D2D): Act now. Text on it is white. Also used as a low wash for Act-now state: feed rows (rgba(226,29,45,.09)) and the hot Act-now tile (a 22% to 4% vertical scarlet wash).
- **Line Tints** (green #5FD884, cobalt #8DABFF, amber #FFD45C, scarlet #FF7A82): the readable-on-midnight versions, used when a verdict colours *text* (Worth a look and Act now numerals, error messages, danger-hover text).

### Neutral
- **Midnight Enamel** (#0B1230): the page field, theme-color, logo tile, and text on porcelain.
- **Midnight Panel** (#0F1940): panels, line-status strip, modal sheets, phone cards.
- **Midnight Raised** (#15214F): row/device hover and selection, case rows, notes, phone result boxes.
- **Midnight Sunk** (#070C22): input wells, raw-log blocks, tooltips.
- **Hairline** (rgba(244,241,234,.14)): internal rules between rows and tiles.
- **Hairline Strong** (rgba(244,241,234,.26)): panel, button, chip and field outlines; idle line track in the diagram.

### Named Rules
**The Line Ink Rule.** Green, cobalt, amber and scarlet are verdicts and nothing else. Active toggles, banners, selection, caret, focus and badges are porcelain. If a coloured thing isn't telling you a verdict, it's wrong.

**The Full Network Rule.** The four inks appear together only as the complete set in verdict order (green, cobalt, amber, scarlet): the logo mark, the fare-card top band, the phone lockup strip, the diagram legend. Never a subset as decoration.

**The Tint-For-Text Rule.** When a line ink colours text on midnight, use its tint, not the raw ink. Raw inks are for fills, rails, rules and stops.

## Typography

**Display Font:** Overpass (with Helvetica Neue, Arial, system-ui)
**Body Font:** Overpass (same stack)
**Label/Mono Font:** Overpass Mono (with ui-monospace, SF Mono, Consolas), raw log text only

**Character:** Overpass is a free Highway Gothic descendant, so labels read like wayfinding signage: tracked caps for signs, heavy weights for numerals, plain sentence case for explanations. Overpass Mono marks evidence: the raw log line a visitor is asked to read.

Fonts load from Google Fonts (Overpass 400/600/700/800, Overpass Mono 400/500). This is a user-waived floor exception: the user declined self-hosted font files ("No, keep Google Fonts"). Offline, pages fall back to Helvetica Neue or Arial, and the `logo.svg` / `logo-light.svg` wordmarks are live text that falls back the same way; the PNG rasters are the portable logo.

### Hierarchy
- **Display** (800, 52px; 40px at ≤1380px, 36px at ≤600px; line-height 1; -0.02em): line-status numerals only.
- **Headline** (800, 26px, 1.15): the phone page heading; modal section heads use the same weight at 20px.
- **Wordmark** (800 "LogWatch" with 400 "The", 28px header / 30px sign-in / 22px phone, -0.01em): brand lockup only.
- **Title** (700, 15 to 15.5px, 1.3): log row titles, device names, alert titles.
- **Body** (400, 15px/1.45 dashboard, 16px/1.5 phone and modals at 16px/1.6): plain-English explanations and advice. Tabular figures on.
- **Label** (800, 13px, 0.1 to 0.11em, uppercase): panel heads, phone card heads, sign-in heading. Tile labels use 700 at 12.5px, 0.09em.
- **Button** (700, 12.5px, 0.08em, uppercase): all dashboard buttons; the phone send button is 800 at 14px, 0.09em.
- **Pill** (800, 11.5px, 0.07em, uppercase): verdict line pills; the PATTERN badge at 10.5px, 0.08em.
- **Station** (800, 15px, 0.05em, uppercase): device names on the line diagram.
- **Mono** (400, 12.5px/1.55): raw log blocks, commands, the phone paste field (13px).

### Named Rules
**The Signage Caps Rule.** Uppercase with tracking is for signs (labels, buttons, pills, station names). Sentences, advice and titles stay sentence case.

**The Mono-Is-Evidence Rule.** Overpass Mono is used only for raw log text and commands. Never for UI labels, numbers or chrome.

## Layout

The dashboard is a single-viewport grid: header, line-status strip, then a three-column main area (300px device roster, fluid live feed, 430px right column), all with a 14px gutter and 16px/20px outer padding. Panels scroll internally; the page does not scroll on a booth display. The right column splits 0.75fr / 1.25fr between "What to do next" and the line diagram.

At ≤1380px the columns tighten to 250px / fluid / 360px. At ≤980px the app becomes a scrolling single column, the five-tile strip becomes two-up with the last tile spanning, panels cap at 70vh, and feed rows drop to two columns. At ≤600px panels release their height caps.

The phone page is one column, max 520px, 16px padding, cards stacked with 14px between them. Spacing rhythm across both: 6px between controls, 8px small gaps, 12px in-row gaps, 14px gutters, 16px panel padding, 20px tile/modal padding, 24px modal body.

## Elevation & Depth

Flat enamel. Resting surfaces never cast shadows; depth comes from tonal steps (sunk #070C22 below field #0B1230 below panel #0F1940 below raised #15214F) and 1.5px porcelain hairline outlines. Shadows exist only on layers that float above the diagram.

### Shadow Vocabulary
- **Floating tooltip** (`box-shadow: 0 10px 30px rgba(0,0,0,.45)`): chart tooltip.
- **Modal sheet** (`box-shadow: 0 24px 70px rgba(0,0,0,.5)`): sign-in, Cases, Digest, Connect sheets, over a rgba(4,7,22,.78) scrim.
- **Inset underline** (`box-shadow: inset 0 -3px 0 #F4F1EA`): active toggle button, the transit-nav active bar.
- **Inset outline** (`box-shadow: inset 0 0 0 1.5px #F4F1EA`): selected device row.
- **Focus halo** (`box-shadow: 0 0 0 3px rgba(244,241,234,.14)`): focused password field, with a porcelain border.

### Named Rules
**The Flat Enamel Rule.** The field stays flat midnight: no gloss, grain, glass or sheen. Depth is tone and hairline; shadow is reserved for things that float.

## Shapes

Softly squared signage. Controls and badges have small radii (4px badge, 5px pill, 7px button, 8px field), containers are a little rounder (10px card, 12px panel, 14px sheet and phone card), and anything that is a stop, a station or a filter is fully round (999px chips, 50% stops, device icon rings). Lines are 4px rails with round caps; the diagram track is 3px, a device's active span 8px. The logo tile is a 64px square at 14px radius with an inset porcelain hairline at 22% opacity.

## Components

### Buttons
Signage plates: outlined, tracked caps, quiet until touched.
- **Shape:** gently squared (7px), 1.5px outline in Hairline Strong.
- **Primary:** porcelain fill, midnight text (8px 12px 7px). Hover lifts to pure white.
- **Outline (default):** transparent, porcelain text; hover sets a porcelain border and a 6% porcelain wash. Transitions 0.2s on border and background.
- **Toggle on (Background, Challenge mode):** porcelain border plus a 3px inset porcelain underline; `aria-pressed` carries the state.
- **Danger (Reset):** outline at rest; hover turns border Line Scarlet and text the scarlet tint.
- **Disabled:** 45% opacity, not-allowed cursor.
- **Phone send:** full width, porcelain fill, 10px radius, 14px padding, 800 caps.

### Chips (filters and phone choices)
- **Style:** fully round, 1.5px Hairline Strong outline, Porcelain Dim text (600).
- **State:** hover takes a porcelain border and text; on is a solid porcelain fill with midnight text. The device-filter clear chip carries an x glyph.

### Line Pills (verdict badges)
A metro line badge ("ACT NOW" on scarlet). Line-ink fill, 5px radius, a drawn verdict glyph (check, info, single bang, double bang) then the word in 11.5px tracked caps. The glyph and word are mandatory.

### Stops and Interchange Rings
20px round station markers carrying the verdict glyph and a screen-reader word. Normal, FYI and Worth a look are filled in their ink. Act now inverts: a porcelain disc with a 3px inset scarlet ring and a scarlet glyph, the interchange. On the line diagram, stops are filled circles with a 3px panel-coloured stroke; Act-now stops are 11px porcelain circles with a 5px scarlet stroke.

### Cards / Containers
- **Panels:** Midnight Panel, 12px radius, 1.5px Hairline Strong border, head row with an 800 tracked-caps label and a 1px Hairline rule beneath (13px 16px 11px padding).
- **Line-status tiles:** five tiles in one bordered strip, Hairline dividers, a 4px ink band hanging from the top edge (verdict ink for verdict tiles, Porcelain Faint otherwise), small caps label with a stop, huge numeral, faint caption.
- **Notes / cases:** Midnight Raised, 8 to 10px radius, Hairline Strong border.
- **Phone cards:** Midnight Panel, 14px radius, numbered with a 24px porcelain roundel.

### Inputs / Fields
- **Style:** Midnight Sunk well, 1.5px Hairline Strong border, 8px radius (9px on phone), porcelain text and caret, 16px text.
- **Hover:** border to 45% porcelain.
- **Focus:** porcelain border plus a 3px 14% porcelain halo.
- **Password:** a 40x36 eye toggle sits inside the right edge; it swaps eye / eye-off drawn icons, uses `aria-pressed` and an updated label.
- **Error:** message text in the scarlet tint below the field.

### Navigation (operator header)
Roundel mark plus wordmark, game name and event theme in Porcelain Faint, a round "now playing" capsule (status word in tracked caps), a row of signage buttons, and the live dot with a tabular clock at 20px.

### Device Roster (signature)
Each device row has a vertical 4px line strip in its worst verdict's ink, with that verdict's stop threaded on it; strips join row to row and stop at the first and last stations. Row: rail, a 36px round outlined device icon (drawn SVG), bold name, faint meta. Hover and selection use Midnight Raised.

### Line Diagram (signature)
One horizontal line per device over the last 10 minutes: a 3px Hairline Strong track, an 8px span in the worst verdict's ink, stops per time bucket coloured by verdict, Act-now stops as interchange rings, station names above in Station caps, faint axis labels below. The empty state is a dotted track with a sentence.

### Fare Card (case card)
Porcelain card with midnight text, 10px radius, 18px/1.55 body, and an 8px four-ink band across the top in verdict order. It is a top band from the transit world, not a side tab; the detector's `side-tab` rule is ignored for `frontend/index.html` in `.impeccable/config.json` for this reason.

### Live Dot
10px Line Green dot with a 2s pulse ring that mirrors the real SSE connection; it turns static scarlet on disconnect and stops under reduced motion. The detector's `pulsing-dot` rule is ignored for `frontend/index.html` for this reason.

### Brand Mark
Four verdict lines in ink order converge on one porcelain interchange ring (the watch) inside a midnight 64px tile. Primary lockup `logo.svg` is porcelain on midnight; `logo-light.svg` is midnight on light; the PNG and @2x rasters are the portable versions.

### Motion
Ease `cubic-bezier(.16,1,.3,1)`. New feed rows draw a 3px ink rule left to right along their base over 1.4s, then fade. State transitions are 0.2s on colour, border and background. `prefers-reduced-motion` removes all animation and transitions.

## Do's and Don'ts

### Do:
- **Do** keep every verdict as ink + drawn glyph + word (line pill or stop with screen-reader word).
- **Do** put every chrome state (active toggle, banner, selection, caret, focus, badge) in porcelain (#F4F1EA).
- **Do** use the line tints (#5FD884, #8DABFF, #FFD45C, #FF7A82) when a verdict colours text on midnight.
- **Do** draw Act now as an interchange ring: porcelain disc, scarlet ring.
- **Do** set labels, buttons, pills and station names in Overpass tracked caps; keep sentences in sentence case.
- **Do** build depth from the midnight tonal steps and 1.5px porcelain hairlines.

### Don't:
- **Don't** use green, cobalt, amber or scarlet for anything that is not a verdict: not links, focus, active states or brand accents.
- **Don't** turn the world into a graphite SOC dashboard with one blue accent.
- **Don't** render the enamel as gloss, grain, glass or sheen; the field stays flat midnight for booth-TV contrast.
- **Don't** show a verdict by colour alone.
- **Don't** use Overpass Mono outside raw log text and commands.
- **Don't** show a subset of the four inks as decoration; together they appear only as the full set in verdict order.
