# Handoff — 6" mirror cell

Written 2026-07-28. State of play, what is settled, what is not, and where the traps are.
Read [README.md](./README.md) for how to run things, [mirror-cell-spec.md](./mirror-cell-spec.md)
for the design and its reasoning, [CONTEXT.md](./CONTEXT.md) for vocabulary.

Under git as of 2026-07-28 (one commit, `826a4ab`, the verified model).

## Where it stands

Design is complete and internally consistent. **113 assertions pass.** Nothing has been
printed from this model.

```sh
cd ~/mirror-cell
python3 mirror_cell.py            # verify + export build/*.step, *.stl, assembly.json, bom.md
python3 -m http.server 8018       # then open http://localhost:8018/
```

| Part | Qty | Volume | Notes |
|---|---|---|---|
| tube_plate | 1 | 204.7 cc | biggest print, ~3½ h |
| mirror_plate | 1 | 166.0 cc | posts + root chamfer integral |
| clip | 3 | 1.8 cc | separate — see traps |
| push_knob | 3 | 1.9 cc | captures a hex head |
| pull_knob | 3 | 2.5 cc | captures a hex NUT — this is the ex-wing-nut |
| pocket_cap | 3 | 0.16 cc | bedded in RTV, loose fit |
| shim | 3 | 0.57 cc | assembly aid, removed after cure |

**The buy list is generated.** [BOM.md](./BOM.md) — also `build/bom.csv`, and a download
button in the viewer — is written by `bom()` from the model's own numbers, with a line of
reasoning on every row. Take that to the shop rather than the summary below, which is here
only so this page reads as a whole: 6 × 10-24 × 1½" hex-head **machine screws** (not cap screws — see spec §7) ·
6 × 10-24 hex nuts · 3 × #10 washers · 3 springs (0.9 mm wire × 9 mm OD × 20 mm FL
≈ 13 lb/in) · 3 × 10-24 heat-set inserts · 3 × M3 inserts + M3 cap screws ·
3 × #10 screws + 1" fender washers · black ABS · RTV silicone.

## The print blocker, mostly cleared

`FIT` was a 0.25 mm placeholder for hex-pocket clearance, unverifiable by any assertion.
**`coupon_fit` has now been printed and read** (2026-07-28): on the **0.10** rung the 10-24
nut seats flat, will not rotate by hand, and leaves no stress whitening in the wall —
all three acceptance criteria. The gauge outline measured 3.91″ × 1.95″ against a drawn
3.937″ × 1.969″ — **0.7–0.9 % linear shrink**, inside the band the design assumed. The
model now carries `FIT_PRESS = 0.10` (captured nuts and both knobs) and `FIT_SLIP = 0.20`
(pull-bolt head), passed explicitly at every `hex_prism()` call site.

**The tube plate is printable now.** Its only hex pocket is the nut pocket, and that
number is measured. Read the two bores on `coupon_insert` first, though — the 10-24 one
is horizontal with 3.1 mm of roof over it, and the tube screws are what hold the cell in
the telescope.

**The mirror plate is not.** `FIT_SLIP` is predicted from the measured shrink, not
measured: no 10-24 hex bolt was on hand. One bolt in row H of the coupon settles it, and
six are on the buy list anyway. Full working in [TEST-COUPON.md](./TEST-COUPON.md), which
also has the slicer settings and what is still unread on the coupon (cap disc, landing
pads, spring seat, both insert bores).

Everything else that could have needed dialling in was deliberately engineered out — the
pocket caps became a loose fit bedded in RTV precisely for this reason.

**One new unknown, added deliberately.** `FIT_PRESS` was measured in a 6 mm coupon plate
with material all around the pocket. Both knobs now put that pocket inside a **2.2 mm
wall**, where a press can bulge the wall instead of gripping. Print **one pull knob**
(~2.5 cc, ~15 min) and press a nut into it before committing to six. If it bulges, the fix
is diameter.

## The rear end was reworked, 2026-07-28

See [ADR-0002](./docs/adr/0002-both-rear-controls-are-printed-knobs.md). Both rear controls
are printed knobs — push Ø16, pull Ø18 capturing a plain hex nut — clearing each other
**radially by 2.05 mm** instead of the old axial escape, which depended on bolt length *and
on where the adjusters were set*. Consequences: the wing nut is gone, all six bolts are
**10-24 × 1½" machine screws** (one length, a ½" multiple), six identical hex nuts, and
rear stack-out falls from 36.9 mm to 24.2 mm.

Grip is what this cost: a Ø18 fluted ABS knob is worse with cold fingers than a 0.875"
steel wing nut, on the control you turn in the dark. Height is the free dimension now —
nothing lives behind the knobs — so make them **taller before wider** if it disappoints.
Wider spends the 2.05 mm the whole scheme rests on.

**The spring preload was wrong and is fixed.** `SPRING_SEAT_DEPTH` had grown from 1.0 to
2.5 mm, and the seat is part of the spring's span, so it silently threw away 40% of the
preload: 1.16 lb per station against the 1.9 lb §7 claimed. Back to 1.0 mm → 1.92 lb per
station, 5.77 lb total, 2.18× the moving assembly. `verify()` now computes preload from
geometry, and `assembly.json` draws the spring from the seat bottom rather than the plate
face, which was hiding 2.5 mm of its length in the viewer.

## Suggested slicer settings

These now live in `PRINT` in `mirror_cell.py` and come out in `build/bom.md` next to the
part they belong to — this table is the same data, kept here because it is what you scan
before a print. **Change `PRINT`, not this table.**

0.4 mm nozzle, 0.2 mm layers, both plates **rear-face-down, posts up, no supports needed**.

| Part | Walls | Top/bottom | Infill |
|---|---|---|---|
| tube_plate | 5 | 5 | 40% gyroid |
| mirror_plate | 6 | **8** | 40% gyroid |
| clip | 5 | 6 | 100% |
| push_knob, pull_knob | 4 | 5 | 100% |
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
  mirror plate; nut outside at the rear, inside the pull knob.
- **The pull knob's nut pocket is SHALLOWER than the nut** (`NUT_T - PULL_NUT_PROUD`), so
  the nut stands 0.4 mm proud. That is not a mistake to "correct" to a flush fit: it is
  what keeps steel, not ABS, bearing on the tube plate under sustained tension.
- **The fan is a stand-in, and the tube is scenery.** Neither is part of the cell. The fan
  in `fan()` was drawn here, not downloaded — GrabCAD and the like need an account, and
  putting a made-up shape behind a real part number would be worse than saying this. Trust
  its 40 × 40 × 10 envelope on a 32 mm pattern, which is standard, and nothing finer. Both
  are flagged `context` in `assembly.json` so they are drawn but **excluded from the
  camera framing** — include the 202 mm tube in the fit and the cell becomes a speck in
  every step.
- **Only the PULL knob is bored through.** Its bore is real work — tightening drives the
  bolt end into it. The push knob is blind: its shank leaves through the pocket opening
  (the plate-facing face), so a bore there would only be a hole out the back. Pressing a
  head into it is therefore one-way. Both pockets face FORWARD, and the push knob's cannot
  be flipped: a rear-facing pocket needs the body to reach 14 mm forward of the head into
  10.16 mm of standoff, so it would bury itself in the tube plate.
- **Knob flute depth is set directly, not by the cutter radius.** The cutters sit outside
  the rim. Centred on the rim, as they were at Ø30, a Ø5 cutter would cut 2.5 mm and leave
  0.9 mm of wall. The 30° phase is cosmetic at 12 flutes — depth is what protects the wall.
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

- **`FIT_SLIP`** — predicted, not measured. Blocks the mirror plate only.
- **The press fit in a 2.2 mm knob wall** — see above. Blocks the knobs only.
- **Knob and plate outlines are functional but aesthetically provisional.** Never styled.
  The knobs are now the *only* thing you touch, so they are the ones worth styling.
- **Fan** — mounting holes exist on the tube plate; **no fan is bought**. The viewer shows
  a 40 mm one so the assembled cell can be seen whole, and it fits (corners clear the push
  knobs by 3.06 mm), but that solid is a stand-in drawn in `fan()` — see the traps.
- **Bolt heads and springs are procedural stand-ins in the viewer.** Their hex phase is not
  matched to anything, so a mis-keyed bolt head would still look fine. The hex nut and
  washer are real solids and *are* checked. Consider importing a vendor solid for the bolts.
- **Seating checks cover hex_nut (in both hosts), washer and pocket_cap.** Extending the
  same solid-vs-solid test to the bolt heads in their knob pockets and the clips on the
  post tops would close the last unchecked fits.
- **§7's spring numbers are now computed, but the spring itself is still unbought.** The
  rate is inferred from geometry (≈5.4 active coils at 0.9 mm wire, 8.1 mm mean coil); a
  real spring's coil count may differ and moves the preload proportionally.
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
