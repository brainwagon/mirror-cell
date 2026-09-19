# The collimation hardware is a config option; the tube mounts are not

The six push/pull bolts and their nuts are now selected by `--bolts` (`10-24`, the default,
or `1/4-20`), and every dimension they touch is derived from that choice. The three radial
tube-mount heat-set inserts and the #10 screws into them do **not** switch, and that split
is the whole decision.

## Why the tube mounts stay 10-24

A ruthex 1/4-20 insert is **8.7 mm across** (`RX-1/4"-20x12.7`) and wants a **3.3 mm** wall.
The tube plate is 0.500" (12.7 mm) thick, so the roof over the seated insert would be
`(12.7 − 8.7)/2 = 2.0 mm` — well under ruthex's minimum. Giving it the wall it asks for
means a 0.625" plate, and the plate's thickness is not free: ADR-0002 pins it to the pull
bolt's thread range. Thickening it re-opens the axial stack, the spring span and both bolt
lengths, for a screw that carries no adjustment and sees a static load. So the tube mounts
stay 10-24, and the model says so in three places rather than leaving it to be inferred.

## What does follow the collimation fastener

The 1/4-20 nut and head are both **7/16" across flats**, against 3/8" and 5/16" at 10-24.
Nothing downstream is typed; each follows:

- **Knob diameters** are the smallest that leave `KNOB_WALL_MIN` (2.0 mm) of material at a
  flute over the hex they capture, rounded up to 0.5 mm. At 10-24 this reproduces the
  16/18 the cell has always had, bit for bit; at 1/4-20 both knobs come out **19.5**.
- **The knob budget** — the radial gap between the push and pull circles (ADR-0002) — grows
  from 0.750" to **0.860"**. 0.860" is not arbitrary: it is the widest the push circle can
  go inboard before the landing pad eats the strap to the mirror plate's centre bore, which
  is the binding constraint at 6". The push circle moves in, and `verify()` checks both the
  knob-to-knob gap and the pad-to-bore strap.
- **The cap counterbore** opens from 12 to **16 mm**, because a 1/4-20 head is 12.95 mm
  across corners and has to pass through it during assembly, leaving a ledge the cap cannot
  fall past.
- **The mirror plate thickens** from 0.375" to **10.1 mm**. The 1/4-20 head is 0.8 mm taller
  and cuts a deeper pocket; the floor under it carries the mirror's weight and the spring's
  sustained preload, so the plate grows to keep `MP_FLOOR_MIN` (3.2 mm). The 6" cell's
  0.375" already clears it, so its plate does not move.
- **The clearance and pass-through holes** come from the bolt's own `clear` and `pass_d`
  figures, still drawn through `drawn_hole()` so they print at the size the bolt finds.
- **The spring** is overridden per aperture, because the spring rides on the shank and a
  6.35 mm 1/4-20 needs a larger coil bore than the 9 mm springs give. See
  [ADR-0005](./0005-the-1-4-20-cell-uses-a-larger-bore-spring.md).

## Consequences

- **`FIT_PRESS` is not re-measured for 1/4-20, and cannot be.** It is an *added* across-flats
  clearance, and the clearance a nut actually sees is `fit·(1−S) − AF·S`: the same 0.10 mm
  leaves ≈0.023 mm at 10-24 but ≈0.010 mm at 1/4-20, i.e. proportionally tighter. The fit
  coupon is laid out around the 10-24 hexes and **refuses `--bolts 1/4-20`** rather than
  emit a gauge that no longer measures the right thing. A 1/4-20 cell wants a purpose-built
  coupon before its pockets are trusted — the same open item `FIT_SLIP` was.
- The 1/4-20 variant builds to `build-<ap>-q20/` (e.g. `build-6-q20/`) and, like a thickness
  variant, has no committed BOM snapshot; `build/bom.md` is still written. The viewer opens
  it as `?cell=6-q20`.
- The fan's clearance to the push knobs is now a **solid-vs-solid** check. The old radial
  comparison of the fan corner against the knob ring reads as a collision at 1/4-20 even
  though the two occupy different z-bands, and it would miss a real one from a shorter push
  bolt.
- A **spring-vs-bolt** check is added: the spring rides on the pull bolt shank, so its coil
  bore must clear the bolt. At 10-24 this was true by luck (4.83 mm in ~7.1); at 1/4-20 it
  is 6.35 mm in the same 7.0–7.2 mm bore, and it is now asserted.
- **Reversible.** 10-24 remains the default and its geometry is bit-identical: every derived
  value reproduces the constant it replaced.
