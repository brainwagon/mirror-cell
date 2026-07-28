# 6" Mirror Cell

A 3-point primary mirror cell for a 6" f/7.33 Newtonian — 3D printed in black ABS,
assembled with 10-24 hardware. Designed for one specific telescope; see
[mirror-cell-spec.md](./mirror-cell-spec.md) for why it is deliberately not parametric.

| File | Purpose |
|---|---|
| `HANDOFF.md` | **Start here when resuming** — state, blockers, and the traps |
| `CONTEXT.md` | Glossary. Tube plate, Mirror plate, Station, Support point, Silicone dab, … |
| `mirror-cell-spec.md` | The design, its numbers, and the reasoning behind them |
| `docs/adr/0001-…md` | Why the support points sit at 0.75R rather than the PLOP optimum |
| `mirror_cell.py` | The model. All dimensions are named variables at the top |
| `index.html` | Assembly viewer — assembled/exploded, in the browser |
| `90866A011_….STEP` | Vendor wing-nut solid (McMaster). Imported so clearances are checked against the real part |

## Build the geometry

```sh
python3 mirror_cell.py
```

Runs 71 assertions, then writes `build/*.step`, `build/*.stl` and `build/assembly.json`.
The assertions encode the spec — the three gaps that must never close, both fastener
bearing floors, assembly clearances, spring travel, post placement, and printer bed fit.
**If a check fails, the geometry is wrong; do not print it.** Several real defects were
caught this way rather than at the print bed — including a version whose mirror could
never have been installed, because the clips were printed onto the posts.

Requires `build123d` (`pip install --user build123d`).

## View it

The page fetches STLs, so it needs to be served over HTTP — `file://` will not work.

```sh
python3 -m http.server 8018
# then open http://localhost:8018/
```

Two modes:

- **Build it** — steps through the 13-stage assembly sequence. Parts fly in as they are
  fitted, the mirror-plate sub-assembly is held clear while it is worked on, and the
  shims come back out at step 8. Each step carries its instructions, and the
  order-critical ones carry a caution. Prev/Next, a Play button, ←/→ keys, and a
  clickable step list. Linkable as `#step=7`.
- **Explore** — the explode slider and per-part visibility toggles.

Drag to orbit, scroll to zoom, right-drag to pan.

**The instructions are not written in the HTML.** `sequence()` in `mirror_cell.py` emits
them alongside the geometry, and assertions check that every step names a part that
actually exists and that the last step shows the finished cell. Instructions and parts
cannot drift apart.

three.js is vendored under `js/vendor/` (copied from `~/dob`); there is no CDN or network
dependency, and no STL loader — `parseSTL` reads build123d's binary STLs directly.

## One source of truth

Every position in the viewer comes from `build/assembly.json`, which `mirror_cell.py`
writes from the same variables that cut the geometry. No dimension is typed into the
JavaScript, so the picture cannot drift away from the parts.

## Status

Geometry is checked but **nothing has been printed from this model**. Before committing to
a multi-hour tube plate print, dial `FIT` (the hex pocket clearance, currently a 0.25 mm
placeholder) on an ABS test coupon — ABS shrinks 0.6–0.8% and nominal pockets will not
fit. Plate and knob outlines are functional but aesthetically provisional.
