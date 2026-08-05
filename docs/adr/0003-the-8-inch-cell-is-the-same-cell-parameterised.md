# The 8″ cell is the same cell, parameterised — not a second design

An 8.000″ × 1.330″ mirror in a 10.000″ ID tube is now built from `mirror_cell.py` by
`--aperture 8`. It is the **same cell**: the same three stations, the same push/pull
mechanism, the same landing pads, captured nuts, heat-set inserts, knobs, clips, pocket
caps and shims. Three numbers change in `CELLS` — mirror diameter, mirror thickness, tube
ID — and everything geometric follows from them. One purchased item changes with the
load, and one manufacturing constraint bites.

The alternative was a branch or a copied file per aperture. Both were rejected for the
same reason: this model's value is in its **171 assertions**, several of which were only
trusted after being watched to fail (see HANDOFF's method note). A fork duplicates the
assertions and then lets the two copies drift, so a check repaired on one cell silently
stays broken on the other. One file with a config table keeps the 6″ cell — the one that
has actually been printed and measured — as a permanently verified control.

## What scales, and what deliberately does not

| | Rule | 6″ | 8″ |
|---|---|---|---|
| Pull-bolt / support circle | `0.375 × MIRROR_D` (0.75R, ADR-0001) | 2.250″ | 3.000″ |
| Push-bolt circle | `R_PULL − 0.750″` | 1.500″ | 2.250″ |
| Tube plate rim | `TUBE_ID / 2` | 95.25 | 127.0 |
| Tube plate flat | 6″ cell's proportion of the rim | 60.0 | 80.0 |
| Mirror plate rim | `POST_IR + POST_T + 3.04` | 88.0 | 113.4 |
| Post height | `RTV_T + MIRROR_T + CLIP_GAP` | 28.1 | 36.1 |

**The push circle does not scale, and that is the point.** Its distance inboard of the
pull circle is set by the two knobs clearing each other radially (ADR-0002), and the knobs
are identical in both cells because the hardware inside them is. Holding the 0.750″ budget
reproduces the 2.05 mm gap exactly at 8″; scaling it proportionally would have thrown away
19 mm of clearance to buy nothing.

**All the hardware is unchanged**: 10-24 throughout, six 1½″ machine screws, six hex nuts,
#4 landing washers, ruthex RX-10-24×9.5 inserts, M3 post inserts, the 40 mm fan pattern,
and the measured `FIT_PRESS` / `FIT_SLIP` / `HOLE_LOSS` numbers. So does `TUBE_PLATE_T`,
which means the insert roof stays at 2.80 mm and the collimation range stays at ±1.62°
— it is set by the bolt hole and the plate thickness, neither of which moved.

## Why 0.75R still holds

ADR-0001 records a tripwire: *"This reasoning does not transfer. It holds only because the
blank is full-thickness and small."* That tripwire is respected rather than ignored, and
the reason it does not fire here is the **thickness the user specified**.

Both blanks are 6:1 — 6.000/1.000 and 8.000/1.330. At constant diameter-to-thickness
ratio, self-weight deflection of a plate goes as `R⁴/t³`, i.e. **linearly in R**, so the
8″ blank deflects about **1.33×** the 6″ one. Against `~/blip`'s finding that the whole
span from 0.40R to the extreme edge is under 1/40 wave at 6″, that is roughly 1/30 wave at
8″ — still optically indifferent, so the load-path argument still decides and the support
points still belong over the pull bolts.

**This is where the file stops.** 8″ is at the edge of the 3-point validity range, and a
thinner 8″ blank (a 1″ plate glass disc, say, at 8:1) is *not* covered by the arithmetic
above — it deflects 2.4× the 6″ cell, and support placement starts to matter again. A
third `CELLS` entry is not a licence; it needs its own version of this paragraph.

## The spring is the one purchased item that changes

8″ × 1.33″ glass is **2574 g against 1089 g**, and the moving assembly goes from 2.68 lb
to 6.11 lb. The 6″ cell's spring makes 1.92 lb per station and **fails the preload check
outright** here — 5.77 lb of spring against a requirement of 9.2. That failure is correct
and was the first thing the new configuration reported.

The force is bought with **free length, not rate**: the seat and the plate gap consume a
fixed 16.24 mm of any spring fitted, so a longer spring arrives further compressed. At
25 mm free length the compression goes 3.76 → 8.76 mm, and a spring *no stiffer than the
6″ cell's* (12 lb/in against 13) makes **4.14 lb per station, 12.4 lb total, 2.03×** the
moving assembly — the same margin the 6″ cell carries.

Buying it as rate instead would have meant ~27.5 lb/in in the 20 mm envelope, roughly
double the torque at the knob. HANDOFF already names grip as this design's weakest point:
a Ø18 fluted ABS knob turned with cold fingers in the dark. Doubling what it takes to turn
it, to avoid changing a part number, would have been the wrong trade.

The longer spring also *widens* a margin that was tight at 6″: the thread runs out
3.41 mm before the spring goes slack there with only 0.35 mm to spare, and 5.35 mm to
spare at 8″.

## Consequences

- **The bed is now the binding constraint, and it is close.** The tube plate must reach
  the tube wall to take its screws, so a 10″ tube puts a **237 × 207 mm** part on a
  250 × 250 mm bed. The 8–10 mm ABS brim the 6″ cell prints with does not fit; the
  8″ cell is specified at **5 mm**, leaving 6.5 mm of bed. `BRIM` is therefore part of
  the bed-fit assertion rather than a slicer note, so any part that grows fails a check
  instead of failing on the bed.
- **Warp risk goes up and is not modelled.** A 237 mm ABS plate at 40% gyroid is a
  materially harder print than the 178 mm one, and it gets *less* brim, not more. Nothing
  in `verify()` can catch this — it is the one place where the 8″ cell is riskier in a way
  no assertion covers. Print it first, before anything else in the cell.
- **Outputs are separated.** `build/` and `BOM.md` for the 6″, `build-8/` and `BOM-8.md`
  for the 8″, so neither cell can overwrite the other's exports or snapshot. The viewer
  takes `?cell=8`.
- **The coupons are shared and stay in `build/`.** They test hardware fits — hex pockets,
  insert bores — and that hardware is identical in both cells, so `FIT_PRESS = 0.10` and
  the passed insert coupon carry over unchanged. This is the main thing the 8″ cell
  inherits for free.
- **Nothing about the 8″ cell has been printed**, including the tube plate that is the
  reason for the bed caveat above.
