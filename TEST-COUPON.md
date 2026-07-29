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
| Ø5.16 through hole | far right | the push bolt slides freely |
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
7. **Spring seat and clearance hole.** Spring drops in, bolt slides freely through the
   Ø5.16 hole with no thread drag. Both should pass without drama; if they do not, the
   profile is over-extruding and everything above is suspect.
8. **Insert coupon.** Install a 10-24 insert in each horizontal bore with a soldering
   iron at 230–250 °C, going in slowly and square. Watch the 3.1 mm roof: if it bulges
   or splits, that is the tube plate's tube screw failing in miniature. Then run a bolt
   in and pull on it. Same for M3 in the rib. Keep the bore that goes in square and
   holds; the difference between them is only 0.1 mm and heat-set inserts are forgiving,
   so if both work, take the smaller.

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

Still unread on this coupon: cap disc, landing pads, spring seat, clearance hole, and
both bores on `coupon_insert`. The insert bores are worth doing before the tube plate
goes on the bed, since the tube screws are what hold the cell in the telescope.

**What this coupon does not test.** Every pocket here sits in a 6 mm plate with material
all around it. Both knobs put the same pocket inside a **2.2 mm wall**
([ADR-0002](./docs/adr/0002-both-rear-controls-are-printed-knobs.md)), where a press can
bulge the wall instead of gripping. Print one `pull_knob` — the worse case, bigger nut,
same wall — and press a nut into it before committing to six.
