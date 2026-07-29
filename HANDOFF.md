# Handoff — 6" mirror cell

Written 2026-07-28. State of play, what is settled, what is not, and where the traps are.
Read [README.md](./README.md) for how to run things, [mirror-cell-spec.md](./mirror-cell-spec.md)
for the design and its reasoning, [CONTEXT.md](./CONTEXT.md) for vocabulary.

Under git as of 2026-07-28 (one commit, `826a4ab`, the verified model).

## Where it stands

Design is complete and internally consistent. **163 assertions pass.** Nothing has been
printed from this model.

```sh
cd ~/mirror-cell
python3 mirror_cell.py            # verify + export build/*.step, *.stl, assembly.json, bom.md
python3 mirror_cell.py --check    # verify only; refuses a stale BOM.md, writes nothing
python3 -m http.server 8018       # then open http://localhost:8018/
```

**The tube-screw inserts are ruthex RX-10-24x9.5**, and the model now carries their
published numbers (`INSERT_OD`, `INSERT_HOLE_D`, `INSERT_MIN_WALL`, `INSERT_L`) because
assertions depend on them. The 6.5 mm bore is drawn nominal and shrinks onto ruthex's
6.4 mm recommended hole — **do not compensate it**. The tight dimension is the roof over
the seated insert: **2.80 mm against a 2.6 mm minimum**, and it is measured over the
7.1 mm insert, not the 6.5 mm bore it melts into, which would flatter it at 3.10 mm.

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
6 × 10-24 hex nuts · 3 × **#4** washers (landing pads — see traps) · 3 springs (0.9 mm wire × 9 mm OD × 20 mm FL
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

These live in `PRINT` in `mirror_cell.py` as **values, not prose** — the sentence in the
BOM is generated from them — and they are also written into the parts themselves:
`build/3mf/<part>.3mf` carries walls, top/bottom shells, infill density and pattern, so
opening one in AnycubicSlicerNext or OrcaSlicer needs no dialling in. This table is the
same data, kept here because it is what you scan before a print. **Change `PRINT`, not
this table.**

**Select your own process preset first, at 0.2 mm layers, then open the 3MF.** The
settings are **per-object overrides** (`Metadata/model_settings.config` in the zip), an
Orca/Bambu-family convention and *not* part of the 3MF standard — the core spec has no
notion of a perimeter count, so these open as plain geometry in Cura and other slicers.
Overrides overlay the selected preset, so your speeds, accelerations and temperatures are
untouched and they survive switching presets. Only the part-specific keys are in the file;
the machine settings below are ranges, so they stay prose here and are dialled in by hand.

**`tube_plate.3mf` also carries three modifier blocks**, one per heat-set insert, forcing
100% infill around each bore. Without them the 2.80 mm roof the minimum-wall assertion
checks is only about 2 mm of solid with ~1.1 mm of 40% gyroid in between — and heat-set
inserts want material to displace into, not voids. Raising infill globally is not the
alternative (it warps the plate) and extra walls never reach the roof above a void, so
local density is the only lever. The blocks are drawn off the same expression that cuts
the bore. **Watch for this failure mode:** `Mesher.add_shape()` on a compound of disjoint
solids silently writes only the *first*, which shipped a plate with one insert reinforced
out of three and looked correct everywhere except the slice preview. Each modifier is now
its own mesh object, and `verify()` reads the meshes back out of the zip rather than
trusting the geometry that went in.

**This was `project_settings.config` for one afternoon and it was a trap.** A project
config *replaces* the process profile: the five keys applied and the other ~275 fell back
to `fdm_process_common`, taking inner wall speed from 180 to 80 and acceleration from 4000
to 1000. The tube plate estimated **11 h instead of 7**, and time was the least of it —
seam, brim and overhang handling had reverted too, so it was a different print, not a slow
one. Nothing in the file looked wrong; the only symptom was the estimate. Layer height is
absent for a related reason: it has no per-object form, so the preset must supply it.

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

- **The landing pads are #4 washers under #10 bolts.** Not a typo, and not an upsizing
  opportunity. A #10 washer's bore *is* clearance for a #10 bolt, so the push-bolt tip
  drops through it onto plastic and the pad does nothing — that was the real state of
  this design until 2026-07-29. A #6 washer leaves 0.9 mm² of contact and `verify()`
  rejects it; the #4 leaves 5.3 mm².
- **Clips are separate parts.** Integral, they leave a 142.4 mm opening for a 152.4 mm
  mirror — the mirror could never be installed. Do not "simplify" them back onto the posts.
- **The mirror plate is laterally unregistered on purpose, and the collimation range
  depends on it.** Tilt needs the plate to slide ~0.26 mm sideways: a pull bolt swings
  0.52 mm at the tube plate over the full 1.42°, against 0.15 mm of slop per side, so the
  plate does not tilt about a fixed point. Adding any pilot, boss or centring feature
  between the two plates — which reads as an obvious improvement — collapses the range,
  and **no assertion would catch it**. Spec §7 and §11 carry the numbers.
- **`TILT_MAX = 3.0` is not the mechanism's range.** It is a conservative envelope for the
  tube-wall swing check. The real limit is ±1.42° as printed, set by `BOLT_CLEAR_D`. The
  two are deliberately not wired together — see the comments on both.
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

Reviewed 2026-07-29. What is left that actually gates a print is the coupon work above —
everything in the first group below resolves with the coupon in hand plus one bolt.

**Blocking:**

- **`FIT_SLIP`** — predicted, not measured. Blocks the mirror plate only. Row H, one
  10-24 hex bolt.
- **The press fit in a 2.2 mm knob wall** — see above. Blocks the knobs only.
- **`coupon_insert` has never been read.** Both heat-set bores are unmeasured and the
  10-24 one is horizontal with 3.1 mm of roof. Those three screws carry the whole cell.
  Do this *before* the tube plate goes on the bed — it is the 3½ hour print.

**Closed or downgraded:**

- ~~Fan~~ — future-proofing, not vital. Holes exist, envelope is checked, nothing is
  bought. The solid in the viewer remains a stand-in — see the traps.
- ~~Tube-mount screw length~~ — ½", or ⅝" once the fender washer is on. Hole positions
  evaluated; confirmed at assembly rather than modelled.
- ~~Springs~~ — bought. 1.0 mm wire × 9 mm OD × 20 mm 304 stainless, the substitute
  recorded in spec §7: ≈18 lb/in against the specified 13, so ≈1.4× preload and knobs
  that turn ~40% stiffer. Error runs the safe way. Confirm the feel on first assembly.
- ~~Knob geometry~~ — 2.5 cc and ~15 min each, so iterating is cheap. A fitting session,
  not a design unknown. Outlines are still unstyled if you want them prettier.
- ~~Seating checks for bolt heads and clips~~ — **added, and both were verified by
  breaking the model.** See the method note.
- ~~Mirror plate thickness~~ — resolved at 0.375", and now commented at the constant with
  the reason. It is pinned by **bolt length, not stiffness**: the pull-bolt head is
  captured in this plate with its nut outside, so thickness comes straight off the thread
  the nut runs on. At 0.500" with the same 1½" bolts the thread runs out **+0.23 mm**
  past nominal instead of +3.41 mm — one collimation and no second chance. 1⅝" pull bolts
  restore it but break the one-length rule; 1¾" overshoots and the spring goes slack
  first. All three were run. Do not thicken it without re-opening ADR-0002.

**Still open, non-blocking:**

- **Bolt and spring solids in the viewer are still procedural.** The heads are now checked
  against their pockets by `verify()`, but what the *viewer* draws is unmatched. A vendor
  solid would close the cosmetic gap.
- **Spring rate is still inferred, not published.** No vendor at this price states active
  coil count; across a plausible 4.5–6 coil spread the bought spring lands 16–21 lb/in.
  Resolves by feel on first assembly.

## Method note

Assertions in `verify()` encode the spec, and several of them were **verified by
reintroducing the bug on purpose** — that is worth continuing. In this project three
checks initially passed a broken model because the *check* was wrong, so a new assertion
is not trustworthy until it has been seen to fail.

**2026-07-29 — a fourth check joined that list, and the cause is worth knowing.** The new
bolt-head test was written above `solid(nm)`, and `verify()` also bound `solid` as a float
(`free, solid = 20.0, 6.2`) further up. The check therefore intersected against a float,
threw, and a blanket `except Exception: clash = 0.0` reported **PASS on four separately
broken models**. The float is now `solid_h`, the check sits below `solid(nm)`, and its
intersection is deliberately *not* wrapped — an exception there should be a crash, not a
green tick. The other seating checks still carry that `except`; it is load-bearing for
genuinely disjoint solids, but it is the reason this bug was invisible.

**A check must be asked where it can also be answered.** The BOM snapshot check lived in
`verify()`, which raises `SystemExit` before the write — so editing any BOM note failed the
run that would have fixed it, and every rerun failed identically. It is now a query
(`bom_snapshot_stale()`) asked *after* the write: the default run repairs the file and says
which rows moved, and `--check` refuses a stale one and writes nothing. Same guarantee,
minus the deadlock.

The strongest checks are the ones that test **solids against solids** (does this part fit
in that recess; is the mirror's volume clear) rather than comparing numbers that were
typed in. Prefer those.

**2026-07-29 — the clearest demonstration yet of why.** `insert_coupon()` aimed both
radial bore cuts *outward* from the rim. They removed nothing, and the coupon shipped with
no 10-24 bores at all — its only holes were the two vertical M3 ones. All five insert
checks passed, because all five were arithmetic on constants: roof depth, bore spacing,
bore depth against the block. Every one of those numbers was correct. Nothing asked the
solid whether the hole was there. It is now asked directly — each intended bore is
intersected with the coupon and must come back empty, and must break the rim face — and
both were confirmed by restoring the old direction and watching four checks fail. If the
coupon had been printed first, the print would have looked fine and taught nothing.

Two smaller things fell out of the same fix:

- `write_3mf()` named modifier `<part>` entries by iterating `STATIONS`, so it emitted
  three however many modifier solids it was handed. A caller with two got a dangling
  `<part id="4">`. Numbering now comes off the modifier list itself.
- The coupon's modifier blocks are 12.3 mm wide and were about to merge across a 24 mm
  block, which would have printed the whole coupon solid — reproducing the dense region
  but not the 40 % field it sits in, and making the "coupon exercises sparse infill"
  assertion a fiction. `IC_Y` is derived from the block width now, not typed.

**The fit coupon was then audited for the same weakness and had it, without the bug.**
All nineteen of its features are genuinely cut — probed and confirmed — but only three of
its fourteen checks touched the solid, and none asked whether any feature existed. A plain
slab would have passed everything except the two bounding-box checks, which only see the
outline. The head row had no solid check at all, which is the row that decides `FIT_SLIP`
— still the one predicted rather than measured. `test_coupon.py` is now 101 checks.

Two things in that fix are worth copying elsewhere:

- **A probe placed from the same table that cuts the feature cannot, alone, prove the
  feature is real.** A table entry describing a hole outside the plate moves the cut and
  the probe together: the cut removes nothing, the probe finds nothing, both agree, and
  the check passes. Each feature is therefore required to lie in the *uncut blank* first,
  and to be gone from the finished part second. Only the pair means anything. All four
  failure modes — sunk below the plate, off the edge, never cut, and hardware too big for
  its pocket — were reintroduced and watched to fail.
- `hex_head()` is now a function in `mirror_cell.py` beside `hex_nut()`. It is not a
  printed part and not in `PARTS`; it exists so checks can put real hardware into a real
  recess. It was an expression written out inside `verify()`, and the coupon needed the
  same one.

The blanket `except Exception: clash = 0.0` around the coupon's nut seating check is gone.
It was not inert — the intersection ran — but it is the construct that reported PASS on
four broken models here, and there is no reason to keep it.
