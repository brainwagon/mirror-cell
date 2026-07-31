# Test coupon — printing and reading it

This print is the only thing standing between the model and a real cell. `FIT` (hex
pocket clearance) is a 0.25 mm placeholder, and no assertion can check it: ABS shrinks
0.6–0.8 %, how much of that reaches a small internal pocket depends on the slicer
profile rather than the geometry, and a pocket that is 0.15 mm tight cracks a plate you
spent three and a half hours printing.

```sh
python3 test_coupon.py     # 101 checks, then build/coupon_fit.* and build/coupon_insert.*
```

It also writes `build/coupons.json`, which puts both coupons in the viewer's
**Download STEP** list alongside the cell parts.

Geometry is in [test_coupon.py](./test_coupon.py). Every pocket is cut by `mirror_cell`'s
own `hex_prism()` at `mirror_cell`'s own depths, so the coupon cannot drift away from the
parts it stands in for.

## What is on it

**`coupon_fit`** — 100.000 × 50.000 × 6 mm plate, ~25 cc.

| Feature | Where | What it decides |
|---|---|---|
| Six 10-24 **nut** pockets, row `N` | top face, fits 0.10 → 0.40 | `FIT` for the captured push-bolt nut (tube plate) |
| Six 10-24 **head** pockets, row `H` | top face, same ladder | `FIT` for the captured pull-bolt head (mirror plate) *and* the push knob |
| Ø12.0 × 1.5 counterbore | bottom left | printed cap disc into printed bore |
| Two Ø8.24 / Ø8.54 pad recesses | **bed face** | the #4 washer landing pad |
| Ø9.8 × 2.5 seat | bottom right | the spring drops in and does not bind |
| Ø5.50 through hole | far right | the **pull** hole: prints at Ø5.16, the collimation range |
| Ø5.95 through hole | far right | the **pass-through** hole: prints at Ø5.60 |
| The outline itself | — | **shrink gauge**: drawn at exactly 100.000 × 50.000 |

The engraved number above each column is the clearance added to across-flats. The notched
corner marks the tight (0.10) end. Every hex pocket has a through hole so a fastener that
turns out to be a press fit can be punched back out.

**`coupon_insert`** — 34 × 32.6 × 20.7 mm block, ~15 cc. Both heat-set insert bores in
their **real print orientations**, at the real wall thicknesses:

- Two horizontal 10-24 bores (Ø6.5 and Ø6.6 × 14 deep) entering opposite ends of a block
  drawn at the tube plate's own 12.7 mm thickness. **Axis parallel to the layers** — the
  bore is radial in the real part, so it prints as an unsupported round hole with only
  3.1 mm of roof over it. It is the one bore in the design whose printed shape is not its
  drawn shape, and reproducing that orientation is the entire point of this coupon.
- Two vertical M3 bores (Ø4.0 and Ø4.1 × 6 deep) — axis *perpendicular* to the layers,
  which is also how they print in the real part — in an 8 mm rib, a centering post top in
  all the ways that matter to a melting insert.
- A solid **modifier** around each 10-24 bore, the same 12.3 mm wide block the tube plate
  carries, so the roof over the bore prints into 100 % infill here exactly as it does
  there. The block is 32.6 mm wide rather than 24 so those two regions stay islands in
  40 % gyroid instead of merging and printing the whole coupon solid. Present only in the
  **3MF** — the STL is geometry alone.

Print two spare `pocket_cap.stl` alongside; you need a printed disc to test the printed
counterbore.

## Slicing

**Use the same profile, the same spool and the same enclosure temperature you will use
for the plates.** A coupon sliced as a fast draft answers a question you are not asking:
wall count and flow set hole size, so a 3-wall coupon does not predict a 5-wall plate.
In particular, whatever XY hole compensation / horizontal expansion is in the profile
must be identical in both — if you change it later, the coupon is void.

- 0.4 mm nozzle, 0.2 mm layers, **flat on the bed**, no supports needed by either part
- Walls **5**, top/bottom **5**, 40 % gyroid — matching the tube plate. This is no longer
  a claim you have to keep true by hand: `COUPON_SLICE` in `test_coupon.py` *is*
  `PRINT["tube_plate"]`, an assertion pins it, and `build/3mf/coupon_*.3mf` carries these
  settings into the slicer for you
- ABS 250–255 °C, bed 100–110 °C, **enclosure closed, cooling 0–20 %**, 8–10 mm brim
- Do **not** scale the model, and do not let the slicer "fix" the 100.000 mm outline

Both parts fit one plate; call it roughly an hour and a half and 35 g. Put them near the
middle of the bed, not at the edge where the chamber is coolest.

**If the coupon warps, throw the results away and fix the enclosure first.** A lifted
corner distorts every pocket over it, and a plate printed under the same conditions will
warp too — with more leverage.

Let it cool fully off the bed before measuring. ABS keeps moving for a while; two hours
minimum, overnight is better, and measure at room temperature.

## Reading it

Work from the tight end toward the loose end and stop at the first rung that passes.
Measure with the real hardware, not with calipers — the pockets are hexagonal and the
question is functional.

1. **Shrink gauge.** Caliper the outline at mid-height (avoid the elephant foot), a few
   places along each edge. `shrink % = (100.000 − measured X) / 100`. Record it; it is
   the number that explains everything else, and it is worth having on paper the next
   time this printer prints something that has to fit.
2. **Nut row `N`.** Push a real 10-24 hex nut into each pocket. Accept the tightest rung
   that seats fully flat under firm thumb pressure or a light squeeze in smooth vise
   jaws, **without whitening or cracking the wall**, and that will not rotate by hand.
   That is the press value.
3. **Head row `H`.** Drop a 10-24 hex head in. This one is fitted with silicone already
   curing on the other side of the plate, so it must **fall in under its own weight** and
   sit flat — accept the tightest rung that does, with no more than a few degrees of
   rotational slop. That is the slip value.
4. **Knobs.** Both knobs capture rather than accept on a timer, so they take the press
   value from step 2, not the slip value from step 3. They are ~2 cc each; this is a cheap
   thing to be wrong about, unlike the plates — but see the thin-wall caveat at the end,
   because their pockets are not in a plate.
5. **Cap counterbore.** A printed `pocket_cap` must drop in with obvious slack. It is
   bedded in RTV and is *supposed* to be loose — if it is a nice fit, that is a defect.
6. **Landing pads (bed face).** A **#4** washer should drop into the Ø8.24 recess and sit
   flush or slightly proud, never rock. If only the Ø8.54 one takes it, the first-layer
   squish is eating the recess: either dial the elephant-foot compensation or open
   `mirror_plate()`'s `+ 0.15` to what worked.
7. **Spring seat and the two bolt holes. READ THIS RUNG.** It was skipped on the first
   coupon and it is the one that mattered: the tube plate went to the bed with its pull
   holes drawn nominal, and they printed at 0.19" — the bolt's own major diameter, zero
   clearance, no collimation range at all. Both holes are now drawn oversize by
   `HOLE_LOSS` so they *print* at Ø5.16 and Ø5.60.
   - Spring drops into the seat and does not bind.
   - A 10-24 slides through **both** holes under its own weight, with no thread drag.
   - **Caliper the Ø5.50 rung.** It must come off the bed at 5.16 ± 0.05. Smaller means
     `HOLE_LOSS` is low for this profile — raise it and reprint the coupon **before** the
     tube plate, because the plate is 5.5–7 h and this coupon is twenty minutes.
   A caliper on a Ø5 hole reads low; if you have a pin gauge or a 13/64" drill shank, use
   that instead and trust it over the caliper.
8. **Insert coupon.** Install a 10-24 insert in each horizontal bore with a soldering
   iron at 230–250 °C, going in slowly and square. Keep the bore that goes in square and
   holds; the difference between them is only 0.1 mm and heat-set inserts are forgiving,
   so if both work, **take the smaller** — 6.5 prints at 6.448 mm against ruthex's 6.4 mm
   recommendation, while 6.6 prints at 6.547 and *fails* the bore assertion in `verify()`.
   Then, in order:
   - **Flush at the mouth, never proud.** The bore mouth is on the plate's arc at
     r = 95.25 mm, which *is* `TUBE_ID/2` — no relief, no countersink. An insert standing
     proud holds the whole plate off the tube wall, and you would discover it while
     drilling in situ with the plate already in the tube. Straightedge or caliper depth
     blade. (The coupon's rim is flat; the plate's is convex with a 0.20 mm crown across
     the boss, so on the real part reference the arc, not a straightedge over the boss.)
   - **Caliper the roof, don't just look at it.** 2.80 mm over the seated insert against a
     2.6 mm minimum — 0.2 mm of margin. Measure the block over each bore and again 10 mm
     away; any difference is the roof lifting. Look for whitening or a split line along
     the crown, which ABS shows before it fails.
   - **Load it by tightening, not by pulling.** The cell is 3.0 lb, so each insert carries
     1.0 lb static and ~10 lb under the 10 g transport knock of §7 — and that arrives as
     *shear*, since the screws are radial while the weight acts along or across the tube.
     Tension is self-inflicted: a hand driver puts 50+ lb of preload on a 10-24 screw,
     five times the worst transport load, so **stripping it during assembly is the real
     failure mode**. Put a screw through a 1″ fender washer, tighten against the rim face
     as if it were the tube wall to the torque you will actually use, and watch for the
     insert turning. Back it off and re-check flushness: one that migrated 0.1 mm is
     telling you something.
   - **Then break it open.** The coupon is expendable and this is the only way to see
     whether the 100 % modifier region really materialised around the bore. Snap or cut
     through one bore: gyroid touching the insert means the modifier did not apply, and
     the minimum-wall assertion is measuring material that is not there.

   Same sequence for M3 in the rib — 1.95 mm of wall each side, as in a real post, so a
   bulge there is a bulge in a centering post.

## Feeding the answer back

Four call sites cut hex pockets, and `hex_prism()` takes a per-call `fit=`:

| Call site | Pocket | Wants |
|---|---|---|
| `tube_plate()` | captured 10-24 nut | press (step 2) |
| `mirror_plate()` | captured pull-bolt head | slip (step 3) |
| `push_knob()` | captured push-bolt head | press (step 4) |
| `pull_knob()` | captured 10-24 nut, 0.4 mm proud | press (step 4) |

**This has been done** — `FIT` is now `FIT_PRESS = 0.10` (nuts and both knobs) and
`FIT_SLIP = 0.20` (pull-bolt head), passed explicitly at every call site. The one
thing to watch if you touch them again: `verify()` uses the fit to check that a bolt head
passes through the cap bore and that the ledge under the cap survives, and that check is
about the *mirror plate* pocket, so it is given `FIT_SLIP`. Pointed at the wrong constant
it would still pass, and would be checking nothing. There is room — the ledge fails only
past about 0.63 mm, well beyond the top of this ladder.

After any change, re-run `python3 mirror_cell.py` and confirm all checks still pass.

Do **not** touch any tube-referenced dimension on the strength of the measured shrink.
The tube plate OD is drawn at nominal 7.500" deliberately, confirmed by a real test fit;
shrinkage is what supplies that fit. See the traps in [HANDOFF.md](./HANDOFF.md).

## Results — 2026-07-28, first coupon

| | Measured | Reading |
|---|---|---|
| Gauge X | 3.91″ = 99.31 mm (drawn 3.937″) | **0.69 % shrink** (0.56–0.81 at ±0.005″) |
| Gauge Y | 1.95″ = 49.53 mm (drawn 1.969″) | 0.94 % (0.69–1.19 at ±0.005″) |
| **10-24 nut, row N** | **0.10 rung: seats flat, will not rotate, no whitening** | `FIT_PRESS = 0.10`, **confirmed** |
| Hex head, row H | not tested — no 10-24 hex bolt on hand | `FIT_SLIP = 0.20`, **predicted, unverified** |

Both gauge readings sit in the 0.6–0.8 % band ABS was expected to shrink by, which is
the result that matters most: nothing about the design has to be re-thought. Take the X
number as the better one — it is twice the gauge length for the same ±0.005″ of reading
error, and at 0.01″ resolution that error is most of the spread between the two axes.
Measuring in mm, or on a caliper reading to 0.001″, would settle whether the difference
between X and Y is real anisotropy or just the last digit.

**Why 0.10 rather than the 0.25 placeholder.** Work the shrink through the pocket: a
pocket drawn at `AF + fit` prints at about `(AF + fit)(1 − S)`, so the clearance the nut
actually sees is `fit·(1 − S) − AF·S`. At S = 0.008 the 0.10 rung leaves ≈ 0.02–0.03 mm —
a snug, no-rock capture — and the printed pocket bears that out on all three acceptance
criteria at once: the nut seats flat, will not rotate by hand, and the wall shows no
stress whitening, so the pocket is not being wedged open. The old 0.25 placeholder
would have left ≈ 0.17 mm, and a captured nut with 0.17 mm of play can rock in its pocket
under the push bolt's reaction. The coupon paid for itself on this rung alone.

**Why the head pocket is not simply 0.10 too.** Same arithmetic on the smaller
across-flats: `AF·S` is 0.06 mm rather than 0.08, so the head pocket comes out about
0.01 mm looser than the nut pocket at the same rung — nowhere near enough to turn a
press fit into something a bolt head falls into on its own. The pull-bolt head is fitted
while the silicone is curing, so it must drop in; 0.20 is predicted to leave ≈ 0.13 mm,
about 2° of rotational slop, which the pull knob takes out anyway. **Confirm it on row H
before printing the mirror plate** — one 10-24 hex bolt settles it, and six of them are
on the buy list regardless.

Still unread on this coupon: cap disc, landing pads, spring seat.

## Results — 2026-07-31, the clearance hole, read off the tube plate instead

**The rung above went unread, and the tube plate paid for it.** With the plate printed and
being assembled, the push bolts had to be forced through their holes. Measured: **0.19"
(4.83 mm)** against Ø5.159 drawn — the bolt's own major diameter, **zero clearance.**

Linear shrink accounts for 0.04 mm of the 0.33 mm lost. The other **0.29 mm** is what a
small round hole gives up to the slicer: chords cutting inside the true circle, and an
inner perimeter laid on a tight radius where it over-fills. Both scale with extrusion
width, not with diameter, so it is an offset — `HOLE_LOSS = 0.30`, rounded up because a
hole 0.01 mm too big costs nothing here and one 0.01 mm too small cost a 7-hour reprint.

**It applies to round holes only, and the same coupon proves it.** The hex pockets
measured clean at `FIT_PRESS = 0.10`, whose entire clearance is 0.02–0.03 mm. Had they
lost 0.29 mm as well they would have been a quarter-millimetre of interference and no nut
would have entered, let alone seated flat with no whitening. Flat walls have neither
chords nor tight radii. `PRINT_SHRINK` was never wrong; it was just not the whole story.

The real cost was not the fit. It was the **collimation range**: `pull_bolt_tilt()`
reported ±1.42° for a plate whose holes could not let a bolt lean at all. Every step of
that arithmetic was correct and rested on an unstated assumption that a bolt fits the
hole. `verify()` now asserts it — the cheapest check in the file, and the last one anybody
thought to write.

## Results — 2026-07-29, insert coupon

**Printed and both 10-24 inserts installed. Everything checked passed.** That clears the
last geometric unknown in front of the tube plate: the bore diameter is right, the roof
holds a seated insert, and `INSERT_BORE_D = 6.5` stands as drawn — the 6.6 rung was not
needed, which is the good outcome, since 6.6 would have failed the bore assertion.

This was the first print of the coupon **with the `insert_solid` modifiers**, so it is also
the first evidence that the reinforcement scheme works in practice and not just in the
file. The bores were printed in their real orientation — axis parallel to the layers,
unsupported round hole, 3.05 mm of roof — which is the condition the tube plate will be in.

| | Result |
|---|---|
| Ø6.5 bore | insert seated, **kept** — `INSERT_BORE_D` unchanged |
| Ø6.6 bore | also seated; not needed, and out of tolerance against ruthex's 6.4 mm |
| Roof over the bore | held |
| M3 bores in the rib | held |

**Not done: sectioning the coupon.** Breaking a bore open is the only way to confirm the
100 % modifier region actually materialised around it rather than leaving gyroid against
the insert, and the minimum-wall assertion assumes it did. The coupon is expendable and the
inserts are cheap; worth doing before the tube plate rather than after. Until then, treat
the modifier as verified *in the file* (`verify()` reads the meshes back out of the zip)
but not verified *in the plastic*.

**What this coupon does not test.** Every pocket here sits in a 6 mm plate with material
all around it. Both knobs put the same pocket inside a **2.2 mm wall**
([ADR-0002](./docs/adr/0002-both-rear-controls-are-printed-knobs.md)), where a press can
bulge the wall instead of gripping. Print one `pull_knob` — the worse case, bigger nut,
same wall — and press a nut into it before committing to six.
