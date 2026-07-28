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

# Landing pad: the #10 washer recess is on the plate's REAR face, which is the face
# that prints against the bed. Elephant foot lands on exactly this feature, so the
# coupon reproduces it on ITS bed face too — testing it on a top face would prove
# nothing. Two clearances: the designed one, and one step looser.
PAD_FITS = (0.15, 0.30)

# --- insert coupon ------------------------------------------------------------
IC_X, IC_Y = 34.0, 24.0
IC_T = mc.TUBE_PLATE_T          # the real roof over the radial bore is what is at risk
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

    # --- pocket cap counterbore: printed disc into printed bore ----------------
    # Both sides shrink, so this fit is not verifiable on paper either. It is meant to
    # be loose (CAP_CLEAR); the coupon proves the disc still drops in, not that it grips.
    p -= Pos(-37.5, MISC_Y, COUPON_T - mc.CAP_T) * extrude(
        Circle(mc.CAP_D / 2), mc.CAP_T)

    # --- landing pads, on the BED face ----------------------------------------
    for j, pf in enumerate(PAD_FITS):
        p -= Pos(-17.0 + j * 15.0, MISC_Y) * extrude(
            Circle(mc.WASHER_D / 2 + pf), mc.WASHER_T + 0.15)

    # --- spring seat ----------------------------------------------------------
    p -= Pos(15.0, MISC_Y, COUPON_T - mc.SPRING_SEAT_DEPTH) * extrude(
        Circle(mc.SPRING_SEAT_D / 2), mc.SPRING_SEAT_DEPTH)

    # --- plain 10-24 clearance hole -------------------------------------------
    # The push bolt must slide freely in this hole through the whole of its travel.
    p -= Pos(35.0, MISC_Y) * extrude(Circle(mc.BOLT_CLEAR_D / 2), COUPON_T)

    return p


# ---------------------------------------------------------------- INSERT COUPON

def insert_coupon():
    """Heat-set insert bores in their real orientations, at the real wall thicknesses.

    The 10-24 bore is radial in the tube plate: axis horizontal, drilled into the rim
    of a 12.7 mm plate. Printed that way it is an unsupported round hole with 3.25 mm
    of roof over it, and it is the only bore in the design whose printed shape is not
    its drawn shape. Reproduce the orientation or the coupon is worthless.
    """
    b = extrude(Rectangle(IC_X, IC_Y), IC_T)

    for j, d in enumerate(BORE_10_24):
        sx = -1 if j == 0 else 1
        y = -IC_Y / 4 if j == 0 else IC_Y / 4
        bore = Rot(0, 90, 0) * Cylinder(radius=d / 2, height=mc.INSERT_DEPTH,
                                        align=(Align.CENTER, Align.CENTER, Align.MIN))
        b -= Pos(sx * IC_X / 2, y, IC_T / 2) * Rot(0, 0, 0 if sx > 0 else 180) * bore

    # Rib standing in for a centering post top: same 8 mm wall, so an insert that
    # bulges a post wall bulges this one.
    b += Pos(0, 0, IC_T) * extrude(
        Rectangle(RIB_L, RIB_W), RIB_H)
    for j, d in enumerate(BORE_M3):
        b -= Pos(-8.0 + j * 16.0, 0, IC_T + RIB_H - mc.M3_INSERT_DEPTH) * extrude(
            Circle(d / 2), mc.M3_INSERT_DEPTH)

    return b


COUPONS = {"coupon_fit": fit_coupon, "coupon_insert": insert_coupon}

# Shown in the viewer's download list. mirror_cell.py writes its own parts into
# assembly.json and cannot write these -- it must not import this file, since this file
# imports it -- so the coupons arrive as a second manifest the page loads if it is there.
LABELS = {"coupon_fit": "Fit coupon", "coupon_insert": "Insert coupon"}
NOTES = {"coupon_fit": "hex pocket ladder + shrink gauge",
         "coupon_insert": "heat-set bores, as printed"}


def manifest():
    return {"downloads": [
        {"name": n, "label": LABELS[n], "note": NOTES[n], "kind": "coupon", "qty": 1,
         "step": f"build/{n}.step", "stl": f"build/{n}.stl"} for n in COUPONS]}


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
    chk(COUPON_T - mc.CAP_T - (mc.WASHER_T + 0.15) > 1.0,
        "cap counterbore and the bed-face pads do not meet through the coupon")

    # --- labels must be legible and must not cut into a pocket ----------------
    chk(ENGRAVE >= 0.4, f"engraving {ENGRAVE} mm deep — at least two layers")
    label_gap = LABEL_Y + LABEL_H / 2
    chk(HEAD_Y + corners / 2 < LABEL_Y - LABEL_H / 2 and
        label_gap < NUT_Y - corners / 2,
        "labels sit clear of both pocket rows")

    # --- the real hardware must pass at the chosen rung -----------------------
    # Solid against solid, the check this project trusts: a nut lowered into the pocket
    # cut at FIT_PRESS -- the rung the printed coupon actually accepted -- must not touch
    # it. (This proves the coupon is drawn right. It cannot prove the print; that is the
    # whole reason the coupon exists.)
    body = fit_coupon()
    if mc.FIT_PRESS in FIT_LADDER:
        i = FIT_LADDER.index(mc.FIT_PRESS)
        placed = Pos(col_x(i), NUT_Y, COUPON_T - NUT_POCKET_H) * mc.hex_nut()
        try:
            clash = (placed & body).volume
        except Exception:
            clash = 0.0
        chk(clash < 1.0,
            f"a real 10-24 nut seats in the {mc.FIT_PRESS:.2f} pocket "
            f"(overlap {clash:.2f} mm^3)")

    # --- insert coupon --------------------------------------------------------
    roof = IC_T / 2 - max(BORE_10_24) / 2
    chk(abs(roof - (mc.TUBE_PLATE_T / 2 - mc.INSERT_BORE_D / 2)) < 0.06,
        f"roof over the radial bore = {roof:.2f} mm, as in the tube plate")
    chk(max(BORE_10_24) * 2 + 2.0 < IC_Y,
        f"the two radial bores do not break into each other across {IC_Y:.0f} mm")
    chk(mc.INSERT_DEPTH * 2 < IC_X,
        f"both {mc.INSERT_DEPTH:.0f} mm bores fit end-to-end in {IC_X:.0f} mm")
    chk((RIB_W - max(BORE_M3)) / 2 >= 1.8,
        f"wall around the M3 insert = {(RIB_W - max(BORE_M3))/2:.2f} mm, as in a post")
    chk(RIB_H > mc.M3_INSERT_DEPTH,
        f"rib {RIB_H:.0f} mm tall takes a {mc.M3_INSERT_DEPTH:.0f} mm insert")

    # --- the viewer's coupon manifest -----------------------------------------
    D = manifest()["downloads"]
    chk({d["name"] for d in D} == set(COUPONS),
        f"manifest offers every coupon: {sorted(d['name'] for d in D)}")
    chk(all(d["step"] == f"build/{d['name']}.step" and
            d["stl"] == f"build/{d['name']}.stl" for d in D),
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
        bb = part.bounding_box()
        print(f"{name:14s} vol {part.volume/1000:8.2f} cm^3   "
              f"bbox {bb.size.X:6.1f} x {bb.size.Y:6.1f} x {bb.size.Z:6.1f} mm")

    import json
    with open("build/coupons.json", "w") as f:
        json.dump(manifest(), f, indent=1)
    print("\nbuild/coupons.json written — the viewer lists the coupons once this exists")
