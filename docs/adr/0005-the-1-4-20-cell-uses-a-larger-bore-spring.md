# The 1/4-20 cell uses a larger-bore spring

The spring rides on the pull bolt's shank. The 9 mm springs both cells were designed
around have a **7.0–7.2 mm** coil bore (OD − 2·wire), which clears the 10-24 shank
(4.83 mm) by about **1.1 mm per side**. A 1/4-20 shank is **6.35 mm**, which the same
spring clears by only **0.33–0.43 mm per side** — it slides on, but the margin is gone.

That matters because the pull bolt **leans**. It is the one that tilts for collimation, and
at full range it moves the shank sideways across the spring's 16.24 mm span by
`span·tan(tilt)` ≈ **0.55 mm**. At 10-24 that is well inside the 1.1 mm of clearance. At
1/4-20 it is larger than the 0.33 mm/side the 8" spring had, so the spring would bear on
the bolt where it previously cleared it — rubbing, and a lateral load the spring was never
sized for.

## The fix

Same wire, larger **OD — 9 → 10.5 mm**, which takes the coil bore to **8.5–8.7 mm** and the
clearance back to **~1.1 mm/side**, matching the 10-24 cell. A larger OD makes the spring
softer (`k ∝ 1/D³`, so ~40 % less), and the preload is bought back with **free length**,
exactly as ADR-0003 did for the 8" cell:

| | wire | OD | free length | bore | clearance/side | preload/station |
|---|---|---|---|---|---|---|
| 6", 10-24 | 0.9 mm | 9 mm | 20 mm | 7.2 mm | 1.19 mm | 1.92 lb |
| 6", 1/4-20 | 0.9 mm | 10.5 mm | **23 mm** | 8.7 mm | 1.17 mm | 2.08 lb |
| 8", 10-24 | 1.0 mm | 9 mm | 25 mm | 7.0 mm | 1.09 mm | 4.14 lb |
| 8", 1/4-20 | 1.0 mm | 10.5 mm | **31 mm** | 8.5 mm | 1.08 mm | 4.18 lb |

The free lengths are what hold the preload: at the cell's 16.24 mm of seat + gap, the
longer spring is compressed further and makes up for the softer rate. Both 1/4-20 springs
land at roughly **2× the moving assembly**, the same place the 10-24 ones do, and the
preload check in `verify()` computes it from geometry rather than trusting the table.

The springs are a per-bolt override in the `BOLTS` entry (`spring={6: …, 8: …}`), not in
`CELLS`: the cell's own spring is the 10-24 one, and a larger bolt replaces it.

## Consequences

- **The spring assertion now means something.** It used to say only that the bore was
  0.2 mm larger than the bolt — true of the too-tight 9 mm spring as well. It now requires
  the per-side clearance to exceed the shank's sway at full tilt (`span·tan(pull_bolt_tilt())`),
  which is the number that was actually at risk. It passes at ~1.1 mm/side against 0.46 mm
  of sway (10-24) and 0.55 mm (1/4-20).
- **The bill of materials has four possible springs**, one per aperture × bolt size. The
  two 1/4-20 ones are a separate purchase; the rate and solid height are inferred from the
  geometry, as they are for the originals, because no vendor at this price states a coil
  count (see HANDOFF).
- **The tube plate's spring seat opens** from Ø9.8 to Ø11.3 mm (`SPRING_SEAT_D`), so the
  1/4-20 tube plate is a different part from the 10-24 one. The 10-24 geometry is
  untouched and bit-identical.
- **Reversible**: select 10-24 and the 9 mm springs come back.
