# Both rear controls are printed knobs, clearing each other radially

The Push knob and the Pull knob sit on the same Station ray, 19.05 mm apart, and something
has to give. The cell previously gave axially: a Ø30 printed knob on the push bolt overlaps
a 0.875″ wing nut on the pull bolt by **7.06 mm radially**, so the push bolts were
lengthened to 2″ purely to drop the knob 10.16 mm below the wing nut. Both rear controls
are now **printed knobs** — Ø16 on the push station, Ø18 on the pull, the latter capturing
a plain 10-24 hex nut in place of the wing nut — sized so they clear each other **radially,
by 2.05 mm**.

The argument is not that a printed knob is nicer than a wing nut. It is that **radial
clearance is unconditional and axial clearance is not.** The axial escape depended on the
push bolt's length *and on where the adjusters happened to be set*: advancing the push
screw carries its knob back toward the plate and into the wing nut's z-band. Nothing in the
model checked the second dependency, because with a knob 22.9 mm behind the plate it never
bound. A radial clearance between two circular knobs on fixed bolt circles cannot be
violated by any adjustment, any bolt length, or any assembly error.

Buying the clearance radially requires controlling *both* parts, which is why the wing nut
has to go rather than merely shrink. A ½″ knurled thumb screw on the push station would
also have cleared it (1.46 mm after shrink), and remains a valid alternate — but it leaves
the pull side dictating the push bolt's length, and it makes the build depend on a
specialty fastener.

## Consequences

- **All six bolts become 10-24 × 1½″**, one type and one length, and a ½″ multiple, which
  is what is actually stocked. `verify()` asserts both properties so they cannot rot. Buy
  **machine screws**: a #10 hex *cap* screw carries an unthreaded shank about 19 mm long,
  exactly where the captured nut needs thread.
- **One nut type, six of them.** Three captured in the tube plate, three in the pull knobs.
  The wing nut leaves the bill of materials.
- **Rear stack-out falls from 36.9 mm to 24.2 mm.**
- **The pull knob joins the load path.** Its nut stands `PULL_NUT_PROUD` = 0.4 mm out of
  the knob's face, so steel bears on the tube plate exactly as the wing nut's steel did and
  the printed body never touches it. An ABS face rotating on an ABS face under sustained
  tension is the one loading this design refuses everywhere (spec §6): ABS creeps.
- **Grip is the thing given up.** A Ø18 fluted ABS knob is worse with cold fingers than a
  0.875″ steel wing nut, and the pull knob is the control you turn in the dark. That is the
  price of the radial solution, paid knowingly. Height is the cheap dimension now — nothing
  lives behind the knobs — so if grip disappoints, make them taller before wider.
- **The diameters are not free choices.** The 19.05 mm budget splits so the two walls come
  out equal: the pull knob captures a nut (11.11 mm across corners), the push knob only a
  head (9.28), so the pull knob takes the larger share. Flute depth, not flute phase, is
  what protects the wall at 12 flutes.
- **The wing nut's vendor solid stays in the repo** as the evidence for the 7.06 mm figure
  above. It measured 22.225 × 12.700 mm; the catalogue-derived estimates it replaced (19.0
  × 11.0) were both undersized, which is why the number is worth keeping checkable. Nothing
  imports it any more.
- **This is reversible**, unlike ADR-0001. Both knobs are ~2 cc prints. Going back to a
  wing nut means 2″ push bolts and a push knob no larger than Ø15.7.
