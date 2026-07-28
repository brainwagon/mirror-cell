# Handoff — 6" mirror cell

Written 2026-07-28. State of play, what is settled, what is not, and where the traps are.
Read [README.md](./README.md) for how to run things, [mirror-cell-spec.md](./mirror-cell-spec.md)
for the design and its reasoning, [CONTEXT.md](./CONTEXT.md) for vocabulary.

**Not a git repo.** Nothing here is under version control yet — `git init` before making
substantial changes if you want to be able to back out.

## Where it stands

Design is complete and internally consistent. **71 assertions pass.** Nothing has been
printed from this model.

```sh
cd ~/mirror-cell
python3 mirror_cell.py            # verify + export build/*.step, *.stl, assembly.json
python3 -m http.server 8018       # then open http://localhost:8018/
```

| Part | Qty | Volume | Notes |
|---|---|---|---|
| tube_plate | 1 | 204.7 cc | biggest print, ~3½ h |
| mirror_plate | 1 | 166.0 cc | posts + root chamfer integral |
| clip | 3 | 1.8 cc | separate — see traps |
| knob | 3 | 8.0 cc | captures a hex head |
| pocket_cap | 3 | 0.16 cc | bedded in RTV, loose fit |
| shim | 3 | 0.57 cc | assembly aid, removed after cure |

Purchased: 6 × 10-24 × 2" hex-head bolts · 3 × 10-24 wing nuts (**McMaster 90866A011**,
solid in repo) · 3 × 10-24 hex nuts · 3 × #10 washers · 3 springs (0.9 mm wire × 9 mm OD ×
20 mm FL ≈ 13 lb/in) · 3 × 10-24 heat-set inserts · 3 × M3 inserts + M3 cap screws ·
3 × #10 screws + 1" fender washers · black ABS · RTV silicone.

## The one thing blocking a print

**`FIT` (mirror_cell.py) is a 0.25 mm placeholder** for hex-pocket clearance. ABS shrinks
0.6–0.8% and no assertion can verify it. **Print an ABS test coupon with the 10-24 nut
pocket and the hex-head pocket before committing to the tube plate.** Everything else that
could have needed dialling in has been deliberately engineered out (the pocket caps became
a loose fit bedded in RTV precisely for this reason).

## Suggested slicer settings

0.4 mm nozzle, 0.2 mm layers, both plates **rear-face-down, posts up, no supports needed**.

| Part | Walls | Top/bottom | Infill |
|---|---|---|---|
| tube_plate | 5 | 5 | 40% gyroid |
| mirror_plate | 6 | **8** | 40% gyroid |
| clip | 5 | 6 | 100% |
| knob | 4 | 5 | 30% |
| pocket_cap, shim | — | — | 100% |

ABS: 250–255 °C, bed 100–110 °C, **enclosure closed, cooling 0–20%**, 8–10 mm brim. Don't
push infill past ~40% on the plates — it adds internal stress and *increases* warping,
which is their main failure mode. The mirror plate's 8 bottom layers are not a nicety:
the pull-bolt bearing floor is only 3.45 mm (17 layers) and carries the mirror's weight,
and the landing-pad recess ceilings are bridged.

## Traps — things that look wrong but are deliberate

- **Clips are separate parts.** Integral, they leave a 142.4 mm opening for a 152.4 mm
  mirror — the mirror could never be installed. Do not "simplify" them back onto the posts.
- **Captured nut pockets open FORWARD**, into the gap between the plates. A push bolt's
  reaction drives its nut rearward into solid plastic. Every steel-to-plastic interface in
  this design is in compression, because ABS creeps under sustained tension.
- **The pull bolt is reversed** relative to the push bolt: head forward, captured in the
  mirror plate; wing nut outside at the rear.
- **`_ring(..., orient=False)`** on the hex nuts. Pockets are cut by `at()`, a pure
  translation, so they all share one orientation; rotating a hex part to its station angle
  lands 30° out (90/210/330 are all 30 mod 60).
- **The post root chamfer is a loft, not a tapered extrude.** OCC's `extrude_taper` throws
  `Standard_TypeMismatch` on this profile above ~1 mm. It worked silently at 1.0 mm.
- **Tube plate OD is drawn at nominal 7.500"** with no shrinkage compensation — confirmed
  by a real test fit. Do not pre-compensate any tube-referenced dimension.
- **Mirror plate has its own `MP_CENTER_BORE`.** The tube plate's bore is set by the 40 mm
  fan screw circle; the two constraints are unrelated and must stay decoupled.

## Open items / candidate tweaks

- **`FIT`** — see above. The only blocker.
- **Knob and plate outlines are functional but aesthetically provisional.** Never styled.
- **Fan** — mounting holes exist on the tube plate, unpopulated. No fan specified or bought.
- **Bolt heads, knob and springs are procedural stand-ins in the viewer.** Their hex phase
  is not matched to anything, so a mis-keyed bolt head would still look fine. The wing nut,
  hex nut and washer are real solids and *are* checked. Consider importing vendor solids
  for the bolts too.
- **Seating checks cover hex_nut, washer, pocket_cap only.** Extending the same
  solid-vs-solid test to the bolt heads in their pockets and the clips on the post tops
  would close the last unchecked fits.
- **Mirror plate thickness 0.375"** is resolved but tight — 3.45 mm of floor under the
  pull-bolt head. Any change to the RTV well or cap depths eats into it.

## Method note

Assertions in `verify()` encode the spec, and several of them were **verified by
reintroducing the bug on purpose** — that is worth continuing. In this project three
checks initially passed a broken model because the *check* was wrong, so a new assertion
is not trustworthy until it has been seen to fail.

The strongest checks are the ones that test **solids against solids** (does this part fit
in that recess; is the mirror's volume clear) rather than comparing numbers that were
typed in. Prefer those.
