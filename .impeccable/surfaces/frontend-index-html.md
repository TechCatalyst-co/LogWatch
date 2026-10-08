---
version: 1
slug: "frontend-index-html"
primary_target: "frontend/index.html"
related_targets: ["frontend/phone.html"]
---

# Surface brief: booth dashboard + visitor phone page

Scope: `frontend/index.html` (big-screen dashboard, operator sign-in) and `frontend/phone.html` (visitor phone page). Mode: Operate.
Audience/job: visitors read verdicts from metres away; student operators drive cases, Challenge mode, Ask AI, Reset. Sign-in password field must offer show/hide.
Constraints: static HTML, no build step; verdict vocabulary fixed; never colour alone.

## Direction contract

THESIS: Every device is a line, every log a stop, every verdict a line colour. Refuses the graphite SOC dashboard with one blue accent.

OWN-WORLD: Midnight-blue enamel ground (#0B1230 family), porcelain-white type and hairline-ruled panels, four line inks that ARE the verdicts: green Normal, cobalt FYI, amber Worth a look, scarlet Act now. Overpass (Highway Gothic lineage) in tracked caps for labels, Overpass Mono only for raw log text. Line pills ("ACT NOW" on scarlet) and drawn verdict glyphs, interchange rings.

STORY: Visitor sees the network status at a glance (how many stops on each line), spots the red interchange, reads the plain-English next step; operator runs rounds from the header.

FIRST VIEWPORT: Header: TheLogWatch roundel mark + wordmark, game name, now-playing, controls, clock. Line-status strip of five tiles with huge numerals and an ink rule. Three columns: device roster (each a vertical line strip), live feed with line pills, right column with "What to do next" alerts above the signature: the Line diagram, one horizontal line per device over the last 10 minutes, stops coloured by verdict, Act-now stops as interchange rings.

FORM: Midnight Transit Diagram (catalog challenger wayfinding-cartography-signage-midnight-transit-diagram, chosen by user over assigned #6). Seed key 60963418.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
