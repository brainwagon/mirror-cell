"""Test coupons — the ABS print that unblocks the cell.

`FIT` in mirror_cell.py is a 0.25 mm placeholder for hex-pocket clearance and no
assertion can verify it: ABS shrinks 0.6–0.8 %, and how much of that reaches a small
internal pocket depends on the slicer profile, not on the geometry. These coupons
measure it, plus the handful of other fits that are printed rather than calculated.

    python3 test_coupon.py       # verify + write build/coupon_*.step, *.stl

Two parts:

  coupon_fit     a 100.000 x 50.000 mm plate carrying a ladder of six hex pockets at
                 each of the two sizes the cell uses, plus the printed-to-printed and
                 printed-to-steel fits (pocket cap, landing pad, spring seat, bolt
                 clearance). The outline is a shrink gauge: it is drawn at exactly
                 100.000 x 50.000 so the plate itself tells you the linear shrink.

  coupon_insert  a block at the real tube-plate thickness carrying the two heat-set
                 insert bores in their real print orientations — the 10-24 bore
                 HORIZONTAL, which is the one that prints out of round.

Every pocket here is cut with mirror_cell's own hex_prism() at mirror_cell's own
depths, so the coupon cannot drift away from the parts it stands in for. Read
TEST-COUPON.md for what to do with it once it is off the bed.
"""

from math import sqrt
from pathlib import Path
from build123d import *

import mirror_cell as mc


# ---------------------------------------------------------------- PARAMETERS

# The ladder. Brackets the current placeholder on both sides: two steps tighter than
# 0.25 in case ABS shrinkage closes a pocket less than feared, two looser in case a
# nut has to be driven. 0.05 mm steps in the middle, where the answer is expected to
# lie; the top of the ladder jumps to 0.40 because past ~0.30 the question stops being
# "does it fit" and becomes "does it rattle".
FIT_LADDER = (0.10, 0.15, 0.20, 0.25, 0.30, 0.40)

GAUGE_X, GAUGE_Y = 100.0, 50.0  # DRAWN EXACT. This is the shrink gauge — see verify().
COUPON_T = 6.0

COL_PITCH = 15.0
NUT_Y = 16.0     # 10-24 hex NUT pockets (tube plate, captured push-bolt nut)
HEAD_Y = -1.0    # 10-24 hex HEAD pockets (mirror plate pull bolt, and the knob)
MISC_Y = -17.5   # everything that is not a hex pocket
LABEL_Y = 7.5    # engraved fit value, between the two rows it applies to

ENGRAVE = 0.6    # deep enough to survive a 0.2 mm layer height and still read
LABEL_H = 4.5
NOTCH = 6.0      # orientation key, at the tightest-fit corner

# Landing pad: the #4 washer recess is on the plate's REAR face, which is the face
# that prints against the bed. Elephant foot lands on exactly this feature, so the
# coupon reproduces it on ITS bed face too — testing it on a top face would prove
# nothing. Two clearances: the designed one, and one step looser.
PAD_FITS = (0.15, 0.30)

# --- insert coupon ------------------------------------------------------------
IC_X = 34.0
IC_T = mc.TUBE_PLATE_T          # the real roof over the radial bore is what is at risk
# Each bore is reinforced by a solid modifier the width of the tube plate's, and the
# coupon is sized so those two blocks stay ISLANDS in sparse infill, as they are in the
# plate. At the old 24 mm the two 12.3 mm blocks met in the middle and ran off both rims,
# so the coupon would have printed solid throughout -- reproducing the dense region but
# not the 40 % field it sits in, and quietly making the "coupon exercises sparse infill"
# check below a fiction. 8 mm of sparse, split between the gap and the two rims.
IC_BOSS_W = mc.INSERT_OD + 2 * mc.INSERT_MIN_WALL
IC_Y = 2 * IC_BOSS_W + 8.0
RIB_W, RIB_H, RIB_L = mc.POST_T, 8.0, 30.0   # stands in for a centering post top
BORE_10_24 = (mc.INSERT_BORE_D, mc.INSERT_BORE_D + 0.1)
BORE_M3 = (mc.M3_INSERT_D, mc.M3_INSERT_D + 0.1)


def col_x(i):
    return (i - (len(FIT_LADDER) - 1) / 2.0) * COL_PITCH


def engrave(part, txt, x, y, size=LABEL_H):
    """Sunk lettering in the top face."""
    return part - Pos(x, y, COUPON_T - ENGRAVE) * extrude(
        Text(txt, font_size=size, align=(Align.CENTER, Align.CENTER)), ENGRAVE)


# ---------------------------------------------------------------- FIT COUPON

NUT_POCKET_H = mc.NUT_T + 0.4     # identical to tube_plate()
HEAD_POCKET_H = mc.HEAD_T + 0.4   # identical to mirror_plate() and knob()


def misc_features():
    """(label, x, diameter, z_from, z_to) for every round feature on the MISC row.

    One expression per feature, read by the cut below AND by the check that proves the
    cut landed. Written as a table for that reason: the insert coupon shipped with two
    bores that were never cut, because the numbers describing them were correct and
    nothing asked the solid whether the holes were there.
    """
    return [
        # Both sides shrink, so this fit is not verifiable on paper. It is MEANT to be
        # loose (CAP_CLEAR); the coupon proves the disc still drops in, not that it grips.
        ("cap counterbore", -37.5, mc.CAP_D, COUPON_T - mc.CAP_T, COUPON_T),
        # Landing pads open DOWNWARD, into the bed face -- see PAD_FITS.
        *[(f"pad recess +{pf:.2f}", -17.0 + j * 15.0, mc.PAD_OD + 2 * pf,
           0.0, mc.PAD_T + 0.15) for j, pf in enumerate(PAD_FITS)],
        ("spring seat", 15.0, mc.SPRING_SEAT_D,
         COUPON_T - mc.SPRING_SEAT_DEPTH, COUPON_T),
        # The push bolt must slide freely through the whole of its travel.
        ("clearance hole", 35.0, mc.BOLT_CLEAR_D, 0.0, COUPON_T),
    ]


def fit_coupon():
    """Top face at z=COUPON_T. Pockets open UP, as they do in every real part."""
    p = extrude(Rectangle(GAUGE_X, GAUGE_Y), COUPON_T)

    # Orientation key at the 0.10 end. Without it a coupon that has been handled for
    # ten minutes is a symmetric slab with six identical-looking holes.
    p -= Pos(-GAUGE_X / 2, -GAUGE_Y / 2) * extrude(
        Rectangle(NOTCH, NOTCH, align=(Align.MIN, Align.MIN)), COUPON_T)

    for i, f in enumerate(FIT_LADDER):
        x = col_x(i)
        for y, af, h in ((NUT_Y, mc.NUT_AF, NUT_POCKET_H),
                         (HEAD_Y, mc.HEAD_AF, HEAD_POCKET_H)):
            p -= Pos(x, y, COUPON_T - h) * mc.hex_prism(af, h, fit=f)
            # Through hole, so a fastener that turns out to be a press fit can be
            # pushed back out with a punch instead of being lost in the coupon.
            p -= Pos(x, y) * extrude(Circle(mc.BOLT_CLEAR_D / 2), COUPON_T)
        p = engrave(p, f"{f:.2f}", x, LABEL_Y)

    p = engrave(p, "N", -GAUGE_X / 2 + 3.4, NUT_Y)
    p = engrave(p, "H", -GAUGE_X / 2 + 3.4, HEAD_Y)

    # --- everything that is not a hex pocket, from the one table ---------------
    for _, x, d, z0, z1 in misc_features():
        p -= Pos(x, MISC_Y, z0) * extrude(Circle(d / 2), z1 - z0)

    return p


# ---------------------------------------------------------------- INSERT COUPON

def ic_bores():
    """(sx, y, diameter) for each radial bore -- one rim each, one diameter each.

    The single expression for where the bores go. The cut, the solid modifier that
    reinforces it, and the checks that prove both landed all read it, so they cannot end
    up describing different holes.
    """
    return [(-1 if j == 0 else 1, (-1 if j == 0 else 1) * IC_Y / 4, d)
            for j, d in enumerate(BORE_10_24)]


def insert_bosses():
    """The coupon's bores forced solid -- the tube plate's insert_bosses(), locally.

    Without these the coupon prints its roof over 40 % gyroid while the plate prints
    its over 100 %, so the single thing this coupon exists to measure is the one thing
    it would not reproduce. Same width as the plate's blocks, and spanning the full
    thickness for the same reason.
    """
    return [Pos(sx * (IC_X / 2 - mc.INSERT_DEPTH / 2), y, IC_T / 2)
            * Box(mc.INSERT_DEPTH, IC_BOSS_W, IC_T, align=(Align.CENTER,) * 3)
            for sx, y, _ in ic_bores()]


# Passed to write_3mf() explicitly: mirror_cell.py cannot hold this entry, because it
# would have to import this module and this module imports it.
IC_MODIFIERS = (insert_bosses, "insert_solid", {"sparse_infill_density": "100%"})
MODIFIERS = {"coupon_insert": IC_MODIFIERS}


def insert_coupon():
    """Heat-set insert bores in their real orientations, at the real wall thicknesses.

    The 10-24 bore is radial in the tube plate: axis horizontal, drilled into the rim
    of a 12.7 mm plate. Printed that way it is an unsupported round hole with 3.25 mm
    of roof over it, and it is the only bore in the design whose printed shape is not
    its drawn shape. Reproduce the orientation or the coupon is worthless.
    """
    b = extrude(Rectangle(IC_X, IC_Y), IC_T)

    for sx, y, d in ic_bores():
        # Mouth in the rim, cutting INWARD. The direction comes from the alignment rather
        # than from a rotation applied after placement: a cut aimed outward still yields a
        # perfectly valid solid -- one with no bore in it at all, which is what shipped.
        # Every check here was arithmetic on constants, so all five passed a coupon whose
        # only holes were the two vertical M3 ones. See the bore checks in verify().
        bore = Rot(0, 90, 0) * Cylinder(
            radius=d / 2, height=mc.INSERT_DEPTH,
            align=(Align.CENTER, Align.CENTER, Align.MIN if sx < 0 else Align.MAX))
        b -= Pos(sx * IC_X / 2, y, IC_T / 2) * bore

    # Rib standing in for a centering post top: same 8 mm wall, so an insert that
    # bulges a post wall bulges this one.
    b += Pos(0, 0, IC_T) * extrude(
        Rectangle(RIB_L, RIB_W), RIB_H)
    for j, d in enumerate(BORE_M3):
        b -= Pos(-8.0 + j * 16.0, 0, IC_T + RIB_H - mc.M3_INSERT_DEPTH) * extrude(
            Circle(d / 2), mc.M3_INSERT_DEPTH)

    return b


COUPONS = {"coupon_fit": fit_coupon, "coupon_insert": insert_coupon}

# The coupons print at the TUBE PLATE's settings, and this is that reference rather than a
# copy of it. TEST-COUPON.md used to say "matching the tube plate" in prose while the
# numbers lived in mirror_cell.py, so changing the plate would have left the sentence true
# and the coupon wrong -- and a coupon printed at settings the real part does not use
# measures the wrong thing. Reading FIT off a coupon only means something if the walls,
# shells and infill above the pocket are the ones the part will actually have.
COUPON_SLICE = mc.PRINT["tube_plate"][0]

# Shown in the viewer's download list. mirror_cell.py writes its own parts into
# assembly.json and cannot write these -- it must not import this file, since this file
# imports it -- so the coupons arrive as a second manifest the page loads if it is there.
LABELS = {"coupon_fit": "Fit coupon", "coupon_insert": "Insert coupon"}
NOTES = {"coupon_fit": "hex pocket ladder + shrink gauge",
         "coupon_insert": "heat-set bores, as printed"}


def manifest():
    return {"downloads": [
        {"name": n, "label": LABELS[n], "note": NOTES[n], "kind": "coupon", "qty": 1,
         "step": f"build/{n}.step", "stl": f"build/{n}.stl",
         "3mf": f"build/3mf/{n}.3mf"} for n in COUPONS]}


# ---------------------------------------------------------------- VERIFY

def verify():
    ok = []

    def chk(cond, msg):
        ok.append((bool(cond), msg))

    # --- the coupon must test what the parts actually have --------------------
    chk(NUT_POCKET_H == mc.NUT_T + 0.4,
        f"nut pocket depth {NUT_POCKET_H:.2f} mm == tube_plate()")
    chk(HEAD_POCKET_H == mc.HEAD_T + 0.4,
        f"head pocket depth {HEAD_POCKET_H:.2f} mm == mirror_plate() and knob()")
    chk(mc.FIT_PRESS in FIT_LADDER and mc.FIT_SLIP in FIT_LADDER,
        f"both fits are rungs on the ladder: press {mc.FIT_PRESS}, slip {mc.FIT_SLIP}")
    chk(len(set(FIT_LADDER)) == len(FIT_LADDER), "ladder values are distinct")

    # --- the outline is the shrink gauge: it must be drawn EXACT --------------
    # (OCC's bounding box carries a ~2e-7 mm tolerance of its own; 1e-3 is still three
    # orders below anything a caliper can see, which is what "exact" has to mean here.)
    bb = fit_coupon().bounding_box()
    chk(abs(bb.size.X - GAUGE_X) < 1e-3 and abs(bb.size.Y - GAUGE_Y) < 1e-3,
        f"gauge outline {bb.size.X:.3f} x {bb.size.Y:.3f} mm, drawn exact")
    chk(abs(bb.size.Z - COUPON_T) < 1e-3,
        f"coupon thickness {bb.size.Z:.2f} mm — nothing protrudes")

    # --- pockets must not undermine each other or the floor -------------------
    worst_af = max(mc.NUT_AF, mc.HEAD_AF) + max(FIT_LADDER)
    corners = 2 * worst_af / sqrt(3.0)
    chk(COL_PITCH - corners >= 2.5,
        f"wall between adjacent pockets = {COL_PITCH - corners:.2f} mm (>= 2.5)")
    chk(NUT_Y - HEAD_Y - corners >= 2.5,
        f"wall between the two rows = {NUT_Y - HEAD_Y - corners:.2f} mm")
    chk(GAUGE_Y / 2 - NUT_Y - corners / 2 >= 2.0,
        f"nut row to plate edge = {GAUGE_Y/2 - NUT_Y - corners/2:.2f} mm")
    floor = COUPON_T - NUT_POCKET_H
    chk(floor >= 1.0, f"floor under the deepest pocket = {floor:.2f} mm")
    chk(COUPON_T - mc.CAP_T - (mc.PAD_T + 0.15) > 1.0,
        "cap counterbore and the bed-face pads do not meet through the coupon")

    # --- labels must be legible and must not cut into a pocket ----------------
    chk(ENGRAVE >= 0.4, f"engraving {ENGRAVE} mm deep — at least two layers")
    label_gap = LABEL_Y + LABEL_H / 2
    chk(HEAD_Y + corners / 2 < LABEL_Y - LABEL_H / 2 and
        label_gap < NUT_Y - corners / 2,
        "labels sit clear of both pocket rows")

    # --- every feature is actually cut ----------------------------------------
    # Asked of the solid, because everything above this point is arithmetic on constants
    # and would pass a plain slab. The two bounding-box checks only see the outline. This
    # is the class of check the insert coupon did not have, and it shipped without its
    # bores as a result -- so each advertised feature is probed here with a body slightly
    # smaller than the cut, which must come back empty.
    body = fit_coupon()
    blank = extrude(Rectangle(GAUGE_X, GAUGE_Y), COUPON_T)

    def empty(probe, label, tol=1.0):
        """Two conditions, and the second is the one worth the words.

        The probe is placed from the same table that cuts the feature, so a table entry
        describing a hole OUTSIDE the plate would move the cut and the probe together:
        the cut would remove nothing, the probe would find nothing, and the check would
        pass. So the feature is also required to lie in the blank -- where there is ABS
        to remove -- before it is required to be gone from the finished part.
        """
        inside = (blank & probe).volume
        chk(inside > 0.5 * probe.volume,
            f"{label} lies inside the plate ({inside/probe.volume:.0%} of it does)")
        chk((body & probe).volume < tol,
            f"{label} is cut ({(body & probe).volume:.2f} mm^3 of ABS in it)")

    for i, f in enumerate(FIT_LADDER):
        for row, y, af, h in (("nut", NUT_Y, mc.NUT_AF, NUT_POCKET_H),
                              ("head", HEAD_Y, mc.HEAD_AF, HEAD_POCKET_H)):
            # Inscribed cylinder: inside the hex at any rotation, so this tests presence
            # and depth without re-deriving the hexagon's corners.
            empty(Pos(col_x(i), y, COUPON_T - h / 2)
                  * Cylinder(radius=(af + f) / 2 * 0.9, height=h - 0.1),
                  f"{row} pocket at fit {f:.2f}")
        # The punch-out hole under both pockets in the column.
        for row, y in (("nut", NUT_Y), ("head", HEAD_Y)):
            empty(Pos(col_x(i), y, COUPON_T / 2)
                  * Cylinder(radius=mc.BOLT_CLEAR_D / 2 - 0.1, height=COUPON_T),
                  f"{row} pocket at fit {f:.2f} punches through")

    for label, x, d, z0, z1 in misc_features():
        empty(Pos(x, MISC_Y, (z0 + z1) / 2)
              * Cylinder(radius=d / 2 - 0.1, height=(z1 - z0) - 0.1), label)

    empty(Pos(-GAUGE_X / 2, -GAUGE_Y / 2, COUPON_T / 2)
          * Box(NOTCH - 0.2, NOTCH - 0.2, COUPON_T,
                align=(Align.MIN, Align.MIN, Align.CENTER)),
          "the orientation notch")

    # --- the real hardware must pass at the chosen rung -----------------------
    # Solid against solid, the check this project trusts: hardware lowered into the pocket
    # cut at the fit the design has settled on must not touch it. Both rows, because
    # FIT_SLIP is the value still predicted rather than measured, and it was the one with
    # no solid check at all. (This proves the coupon is drawn right. It cannot prove the
    # print; that is the whole reason the coupon exists.)
    #
    # The intersections are deliberately NOT wrapped in a blanket except. One here used to
    # be, and that construct reported PASS on four separately broken models elsewhere in
    # this project -- an exception here should be a crash, not a green tick.
    for row, y, h, fit, part in (
            ("10-24 nut", NUT_Y, NUT_POCKET_H, mc.FIT_PRESS, mc.hex_nut()),
            ("10-24 head", HEAD_Y, HEAD_POCKET_H, mc.FIT_SLIP, mc.hex_head())):
        chk(fit in FIT_LADDER, f"{row}: the design's {fit:.2f} is a rung on the ladder")
        if fit not in FIT_LADDER:
            continue
        placed = Pos(col_x(FIT_LADDER.index(fit)), y, COUPON_T - h) * part
        assert placed.volume > 0 and body.volume > 0, f"{row}: empty operand"
        clash = (placed & body).volume
        chk(clash < 1.0,
            f"a real {row} seats in the {fit:.2f} pocket (overlap {clash:.2f} mm^3)")

    # --- insert coupon --------------------------------------------------------
    roof = IC_T / 2 - max(BORE_10_24) / 2
    chk(abs(roof - (mc.TUBE_PLATE_T / 2 - mc.INSERT_BORE_D / 2)) < 0.06,
        f"roof over the radial bore = {roof:.2f} mm, as in the tube plate")
    chk(max(BORE_10_24) * 2 + 2.0 < IC_Y,
        f"the two radial bores do not break into each other across {IC_Y:.0f} mm")
    chk(mc.INSERT_DEPTH * 2 < IC_X,
        f"both {mc.INSERT_DEPTH:.0f} mm bores fit end-to-end in {IC_X:.0f} mm")

    # The bores are actually THERE, asked of the solid.
    #
    # Everything above this is arithmetic on constants, and all of it passed a coupon that
    # had no radial bores at all: the cut was aimed outward from the rim, removed nothing,
    # and left a valid solid whose only holes were the two vertical M3 ones. Nothing in
    # the numbers could have noticed -- the numbers were all correct. So the check is put
    # where it can be answered: intersect each intended bore with the coupon and require
    # the material to be gone.
    ic = insert_coupon()
    for sx, y, d in ic_bores():
        probe = (Pos(sx * IC_X / 2, y, IC_T / 2) * Rot(0, 90, 0)
                 * Cylinder(radius=d / 2 - 0.05, height=mc.INSERT_DEPTH - 0.1,
                            align=(Align.CENTER, Align.CENTER,
                                   Align.MIN if sx < 0 else Align.MAX)))
        left = (ic & probe).volume
        rim = "-x" if sx < 0 else "+x"
        chk(left < 1.0,
            f"the {d:g} mm bore in the {rim} rim is open through "
            f"{mc.INSERT_DEPTH:g} mm ({left:.1f} mm^3 of ABS left in it)")

    # ...and open at the rim, not a sealed pocket -- a heat-set insert goes in from
    # outside. A bore cut inward from 1 mm INSIDE the face would pass the check above.
    for sx, y, d in ic_bores():
        face = (Pos(sx * (IC_X / 2 - 0.15), y, IC_T / 2) * Rot(0, 90, 0)
                * Cylinder(radius=d / 2 - 0.05, height=0.3,
                           align=(Align.CENTER,) * 3))
        chk((ic & face).volume < 0.2,
            f"the {d:g} mm bore breaks the {'-x' if sx < 0 else '+x'} rim face")
    chk((RIB_W - max(BORE_M3)) / 2 >= 1.8,
        f"wall around the M3 insert = {(RIB_W - max(BORE_M3))/2:.2f} mm, as in a post")
    chk(RIB_H > mc.M3_INSERT_DEPTH,
        f"rib {RIB_H:.0f} mm tall takes a {mc.M3_INSERT_DEPTH:.0f} mm insert")

    # --- the coupons print at the settings of the part they stand in for -------
    # The whole value of a fit coupon is that its pocket sees what the real pocket sees.
    # Asserted against the tube plate's Slice rather than against copied numbers, so the
    # two cannot drift; if the plate's settings change, this coupon changes with them.
    chk(COUPON_SLICE is mc.PRINT["tube_plate"][0],
        f"coupons print at the tube plate's settings ({COUPON_SLICE.prose()})")
    chk(COUPON_SLICE.walls is not None and COUPON_SLICE.density < 100,
        f"the reference part is one with real walls and sparse infill, so the coupon "
        f"exercises them ({COUPON_SLICE.prose()})")

    # --- and at the reinforcement the real part gets ---------------------------
    # The tube plate forces the region around each insert solid. A coupon without that
    # measures a roof printed over gyroid and reports it as the plate's -- the settings
    # would match while the material above the bore did not.
    _, ic_mod_name, ic_over = IC_MODIFIERS
    chk(ic_over.get("sparse_infill_density") == "100%",
        f"coupon modifier '{ic_mod_name}' fills its region solid "
        f"({ic_over.get('sparse_infill_density')})")
    chk(ic_over == mc.MODIFIERS["tube_plate"][2],
        "the coupon's overrides are the tube plate's, so the reinforcement it tests is "
        "the reinforcement the plate gets")
    bosses = insert_bosses()
    chk(len(bosses) == len(BORE_10_24),
        f"{len(bosses)} solid regions for {len(BORE_10_24)} bores")
    # Each block must actually contain its bore -- placed by hand from IC_X rather than
    # cut by the same expression, so this is the check that they meet.
    for (sx, y, d), box in zip(ic_bores(), bosses):
        want = (Pos(sx * IC_X / 2, y, IC_T / 2) * Rot(0, 90, 0)
                * Cylinder(radius=d / 2, height=mc.INSERT_DEPTH,
                           align=(Align.CENTER, Align.CENTER,
                                  Align.MIN if sx < 0 else Align.MAX)))
        outside = want.volume - (want & box).volume
        chk(outside < 1.0,
            f"the solid region encloses the {d:g} mm bore in the "
            f"{'-x' if sx < 0 else '+x'} rim ({outside:.1f} mm^3 outside it)")
    # ...while leaving sparse infill to be sparse. Two blocks that merge and reach both
    # rims turn the whole coupon solid, which is not what the plate does.
    gap = IC_Y / 2 - IC_BOSS_W          # between the two blocks
    margin = IC_Y / 4 - IC_BOSS_W / 2   # from each block to the rim
    chk(gap >= 2.0 and margin >= 2.0,
        f"the two solid regions stay islands: {gap:.1f} mm of sparse infill between "
        f"them, {margin:.1f} mm at each rim")
    for name in COUPONS:
        z0 = COUPONS[name]().bounding_box().min.Z
        chk(abs(z0) < 1e-6, f"{name} rests on the bed (z_min = {z0:+.3f} mm)")

    # --- the viewer's coupon manifest -----------------------------------------
    D = manifest()["downloads"]
    chk({d["name"] for d in D} == set(COUPONS),
        f"manifest offers every coupon: {sorted(d['name'] for d in D)}")
    chk(all(d["step"] == f"build/{d['name']}.step" and
            d["stl"] == f"build/{d['name']}.stl" and
            d["3mf"] == f"build/3mf/{d['name']}.3mf" for d in D),
        "manifest points at the files this script actually writes")
    chk(all(d["label"] and d["note"] for d in D),
        "every coupon carries a label and a note for the panel")

    # --- printable ------------------------------------------------------------
    for name, fn in COUPONS.items():
        s = fn().bounding_box().size
        chk(s.X < mc.BED[0] and s.Y < mc.BED[1] and s.Z < mc.BED[2],
            f"{name} fits bed: {s.X:.0f} x {s.Y:.0f} x {s.Z:.0f} mm")

    for good, msg in ok:
        print(f"  {'PASS' if good else 'FAIL'}  {msg}")
    failed = [m for g, m in ok if not g]
    if failed:
        raise SystemExit(f"\n{len(failed)} CHECK(S) FAILED")
    print(f"\n  all {len(ok)} checks passed")


if __name__ == "__main__":
    import os
    verify()
    print()
    os.makedirs("build", exist_ok=True)
    for name, fn in COUPONS.items():
        part = fn()
        export_step(part, f"build/{name}.step")
        export_stl(part, f"build/{name}.stl")
        p3 = Path(f"build/3mf/{name}.3mf")
        mc.write_3mf(part, p3, COUPON_SLICE, part_number=name,
                     modifiers=MODIFIERS.get(name))
        got = mc.read_3mf_config(p3)
        if got != COUPON_SLICE.config():
            raise SystemExit(f"\n3MF SETTINGS DID NOT ROUND-TRIP for {name}\n"
                             f"  wrote:  {got}\n  meant:  {COUPON_SLICE.config()}")

        # Read the MODIFIER MESHES back out of the file. verify() checked the geometry
        # going in; only the file says what came out, and a compound handed to add_shape()
        # once wrote one mesh out of three while every input check passed.
        found = mc.read_3mf_modifiers(p3)
        want = MODIFIERS.get(name)
        if not want:
            if found:
                raise SystemExit(f"\n{p3} has {len(found)} unexpected modifier(s)")
        else:
            make, _, over = want
            if len(found) != len(make()):
                raise SystemExit(
                    f"\n{p3} carries {len(found)} modifier meshes, expected "
                    f"{len(make())} -- one per bore.\n  found: {[f[0] for f in found]}")
            for (sx, y, d), (nm, ov, bb) in zip(ic_bores(), found):
                if ov != over:
                    raise SystemExit(f"\n{p3}: modifier {nm} carries {ov}, meant {over}")
                cx = sx * (IC_X / 2 - mc.INSERT_DEPTH / 2)
                if abs((bb[0] + bb[3]) / 2 - cx) > 1.0 or abs((bb[1] + bb[4]) / 2 - y) > 1.0:
                    raise SystemExit(
                        f"\n{p3}: modifier {nm} sits at "
                        f"({(bb[0]+bb[3])/2:.1f}, {(bb[1]+bb[4])/2:.1f}), "
                        f"not on the bore at ({cx:.1f}, {y:.1f})")
                if not (bb[2] <= 1e-6 and bb[5] >= IC_T - 1e-6):
                    raise SystemExit(f"\n{p3}: modifier {nm} spans z "
                                     f"{bb[2]:.2f}..{bb[5]:.2f}, not the full thickness")
        bb = part.bounding_box()
        print(f"{name:14s} vol {part.volume/1000:8.2f} cm^3   "
              f"bbox {bb.size.X:6.1f} x {bb.size.Y:6.1f} x {bb.size.Z:6.1f} mm")

    import json
    with open("build/coupons.json", "w", encoding="utf-8") as f:
        json.dump(manifest(), f, indent=1)
    print("\nbuild/coupons.json written — the viewer lists the coupons once this exists")
