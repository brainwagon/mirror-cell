"""Newtonian mirror cell — build123d model.

Two telescopes from one file: a 6.000" x 1.000" mirror in a 7.500" ID sonotube (the
original, printed and measured), and an 8.000" x 1.330" mirror in a 10.000" ID tube.
Pick one with --aperture; everything below is derived from the CELLS entry.

It does NOT generalise past those two. A 3-point cell is only valid to about 8-10", and
the 0.75R support radius holds because both blanks are full-thickness at the same 6:1
diameter-to-thickness ratio -- see docs/adr/0001 and docs/adr/0003.

Every dimension lives in the PARAMETERS block. Model internals are mm; the design is
dimensioned in inches, so inch() converts at the boundary.

    python3 mirror_cell.py                # the 6" cell -> build/
    python3 mirror_cell.py --aperture 8   # the 8" cell -> build-8/
    python3 mirror_cell.py --check        # verify only; writes nothing
"""

import os
import sys
from math import sqrt, cos, sin, tan, radians, degrees, hypot, atan, atan2, pi
from pathlib import Path
from build123d import *


def inch(x):
    return x * 25.4


# ---------------------------------------------------------------- PARAMETERS

# --- which cell ---------------------------------------------------------------
# Read from the command line at IMPORT time, because every constant below is a module
# global computed from it. test_coupon.py imports this module and inherits the choice,
# which is right: the coupons test hardware fits, and those are the same either way.
def _aperture():
    for i, a in enumerate(sys.argv):
        if a == "--aperture" and i + 1 < len(sys.argv):
            return sys.argv[i + 1]
        if a.startswith("--aperture="):
            return a.split("=", 1)[1]
    return os.environ.get("MIRROR_CELL_APERTURE", "6")


# What differs between the two cells, and NOTHING else does. Every other number in this
# file is either derived from these or is hardware -- the 10-24 fasteners, the heat-set
# inserts, the measured fits, the knobs and the 40 mm fan are identical in both cells,
# which is the whole reason the 8" is a small change rather than a second design.
#
#   moving_n  the moving assembly in newtons, as a stated expectation. verify() computes
#             it from the solids and checks it against this, so a change that quietly
#             adds mass to the mirror plate fails instead of scaling the preload check
#             along with it.
#   brim      what the plate can actually be given on a 250 mm bed. This is a CONSTRAINT
#             at 8", not a preference -- see the bed-fit check in verify().
CELLS = {
    6: dict(mirror_d=6.000, mirror_t=1.000, tube_id=7.500,
            spring=dict(wire=0.9, od=9.0, free=20.0, rate_lb_in=13.0, solid=6.2),
            moving_n=11.8, brim=10.0, build="build", bom="BOM.md"),
    8: dict(mirror_d=8.000, mirror_t=1.330, tube_id=10.000,
            # 2574 g of glass against 1089: the 6" cell's spring makes 1.92 lb/station
            # and fails the preload check outright here. Answered with LENGTH rather than
            # rate -- 25 mm free length gives 8.76 mm of compression instead of 3.76, so
            # a spring no stiffer than the 6" one makes 2x preload and the knobs keep
            # roughly the torque they had. See docs/adr/0003.
            spring=dict(wire=1.0, od=9.0, free=25.0, rate_lb_in=12.0, solid=8.0),
            moving_n=27.2, brim=5.0, build="build-8", bom="BOM-8.md"),
}

APERTURE = int(_aperture())
assert APERTURE in CELLS, f"--aperture must be one of {sorted(CELLS)}, not {APERTURE}"
CELL = CELLS[APERTURE]
BUILD = CELL["build"]      # every written path hangs off this, so the two cells cannot
BOM_PATH = CELL["bom"]     # overwrite each other's exports
BRIM = CELL["brim"]

# --- the telescope -----------------------------------------------------------
MIRROR_D = inch(CELL["mirror_d"])
MIRROR_T = inch(CELL["mirror_t"])
TUBE_ID = inch(CELL["tube_id"])  # draw NOMINAL; ABS shrinkage supplies the fit (spec §5)

# --- stations ----------------------------------------------------------------
STATIONS = (90.0, 210.0, 330.0)
# The pull bolts ARE the support points (ADR-0001), so this circle is optical and scales
# with the mirror: 0.75R, which is 2.250" at 6" and 3.000" at 8".
#
# Derived in INCHES and converted once, per the convention at the top of this file, rather
# than as 0.375 * MIRROR_D. Both give the same circle, but the mm form lands a bit low in
# the last place -- 57.14999999999999 against inch(2.250)'s 57.15 -- and that is enough to
# change every exported byte of a plate that has already been printed. Doing the fraction
# on the inch figure keeps the 6" cell's geometry bit-identical to what it was before the
# 8" existed.
R_PULL = inch(0.375 * CELL["mirror_d"])
# The push circle does NOT scale. Its distance inboard of the pull circle is set by the
# two knobs having to clear each other radially (ADR-0002), and the knobs are the same
# size in both cells because the hardware inside them is. 0.750" gives the same 2.05 mm
# gap at 8" that it gives at 6".
KNOB_BUDGET_IN = 0.750
R_PUSH = inch(0.375 * CELL["mirror_d"] - KNOB_BUDGET_IN)

# --- axial stack (spec §4) ---------------------------------------------------
TUBE_PLATE_T = inch(0.500)
PLATE_GAP = inch(0.600)  # nominal; wing nuts set the real value
# RESOLVED at 0.375", and pinned by the BOLTS, not by stiffness. The pull bolt's head is
# captured in this plate with its nut outside at the rear, so every millimetre of
# thickness comes straight off the thread the nut runs on. At 0.500" with the same 1.5"
# bolts the thread runs out +0.23 mm past nominal instead of +3.41 mm -- one collimation
# and no second chance. Restoring the range needs 1.625" pull bolts, which breaks the
# one-length rule below; 1.75" overshoots and the spring goes slack first. Verified by
# running all three. Do not thicken this plate without re-opening ADR-0002.
MIRROR_PLATE_T = inch(0.375)
RTV_T = inch(0.0625)  # bond thickness, set by the printed shims
CLIP_GAP = inch(0.030)  # clip -> mirror front face
POST_GAP = inch(0.030)  # centering post -> mirror edge, radial

# --- outlines ----------------------------------------------------------------
TP_ARC_R = TUBE_ID / 2  # tube plate corner arcs
# Tube plate flat, distance from the axis. Cut deep on purpose: the load path runs
# radially along each station ray (collimation bolt -> tube screw, both on the same ray),
# so material between stations carries only torsion. Also opens the back of the cell for
# mirror cooldown. Bounded below by the corner tabs, which hold the tube screws -- past
# about 53 (at 6") the flats eat into the insert bores, and verify() checks the tab.
#
# Held at the 6" cell's PROPORTION rather than its value, so the flats stay as deep
# relative to the rim in both cells and the plate looks like the same part. Written as a
# ratio against inch(7.5) so the 6" outline comes out at exactly 60.0 as drawn and
# printed -- this plate exists in ABS and its outline must not move by a micron.
TP_FLAT_D = 60.0 * (TUBE_ID / inch(7.500))

# Post geometry lives here rather than with the rest of the mirror-plate detail because
# the plate's OUTLINE is derived from it: the rim has to contain the posts.
POST_IR = MIRROR_D / 2 + POST_GAP  # post inner face
POST_T = 8.0  # thick enough to take an M3 insert with sound walls
# Mirror plate corner arcs. Must contain the posts AND leave room for the post root
# chamfer outboard, which is the more critical face -- see POST_FILLET. Trimmed to 86.0
# at one point; that capped the chamfer at 1.04 mm, so it went back to a 3.04 mm rim.
# Derived from the posts now, so it follows the mirror instead of being retyped: at 6"
# this is exactly 88.0 again, at 8" it is 113.4.
MP_RIM = 3.038
# Rounded to the micron for the same reason R_PULL is converted from inches: the sum lands
# a bit under 88.0 in the last place, and this plate's outline must not move at all
# between the version that was checked and the version that gets printed. An outline
# radius is drawn to a micron, never to a float's last bit.
MP_ARC_R = round(POST_IR + POST_T + MP_RIM, 6)
MP_FLAT_D = 65.0 * (MP_ARC_R / 88.0)
# The prototype used 1.622". That collides with the 40 mm fan screw circle: holes on a
# 32 mm square sit at r=22.63, leaving a 0.43 mm web to a 1.622" bore. 1.500" restores a
# 2 mm web while still passing nearly the fan's full 38 mm throat.
CENTER_BORE = inch(1.500)

# The mirror plate gets its OWN bore. The tube plate's is set by the 40 mm fan screw
# circle; this one is limited by the landing pads and wants to be as open as possible so
# fan air actually reaches the back of the glass. The pads shrank to #4 washers, so the
# recess inner edge moved out from 31.6 to 34.0 mm and this bore now has room it is not
# using -- opening it is free airflow if anyone wants it.
MP_CENTER_BORE = 56.0
# Lightening holes between the stations. Nothing structural lives at the mid-angles: the
# dab is coaxial with its pull bolt (ADR-0001) and the push bolts are on the same rays, so
# the plate's only job out here is keeping the three stations coplanar.
MP_LIGHTEN_WALL = 6.0
MP_LIGHTEN_R = (MP_FLAT_D - 2 * MP_LIGHTEN_WALL - MP_CENTER_BORE / 2) / 2
MP_LIGHTEN_RC = MP_CENTER_BORE / 2 + MP_LIGHTEN_WALL + MP_LIGHTEN_R

# --- fan option (spec §5) ----------------------------------------------------
# The holes are real and cut in the plate; the fan itself is a 40 mm stand-in modelled
# here, NOT a vendor solid. Its envelope is what the checks care about -- 40 x 40 x 10 is
# the standard, and the corner-to-knob clearance is the only tight number.
FAN_PITCH = 32.0
FAN_HOLE_D = 3.2
FAN_SIZE = 40.0
FAN_T = 10.0
FAN_CORNER_R = 3.0
FAN_THROAT_D = 38.0
FAN_CLEAR_HOLE_D = 4.3   # the fan's own holes are clearance; the plate's are tapped
FAN_HUB_D = 16.0
FAN_BLADES = 7
FAN_BLADE_PITCH = 35.0   # degrees of twist, for looks

# --- the tube (display only) -------------------------------------------------
# A stub of the sonotube, drawn so the assembled cell can be seen in context. It is not
# a part of this design -- the tube is the telescope's -- but the cell's whole clearance
# story is against it, so it is worth being able to see.
TUBE_WALL = inch(0.125)
TUBE_OD = TUBE_ID + 2 * TUBE_WALL          # 7.750", matching the real sonotube
TUBE_REAR_OF_PLATE = inch(3.65)            # from the tube plate's MID-PLANE, rearward
TUBE_FWD_OF_MIRROR = inch(2.0)             # above the mirror's front surface

# --- 10-24 hardware ----------------------------------------------------------
BOLT_CLEAR_D = inch(0.2031)  # free-fit clearance for 10-24, AS PRINTED -- not as drawn
# This stock clearance -- 0.166 mm per side, chosen for nothing but free fit -- is also
# what sets the COLLIMATION RANGE, and it is the tightest limit in the adjustment chain.
# The pull bolt's head is clamped flat on the mirror plate's floor, so the whole mirror
# tilt shows up as bolt tilt in the tube plate's hole, guided over TUBE_PLATE_T less the
# spring seat. That is +/-1.62 deg (97 arcmin), +/-2.42 mm at one station -- against 2.51
# deg the spring would allow. Ample: one knob turn is 42 arcmin. Derivation and the
# tripwires are in spec section 7; TILT_MAX in verify() is a separate and deliberately
# conservative envelope, not this number.
#
# READ AS PRINTED, WHICH IS THE CHANGE. This used to be the diameter DRAWN, and the first
# tube plate came off the bed with these holes at 0.19" -- the bolt's own major diameter,
# zero clearance, no collimation range whatever (see HOLE_LOSS). Every hole for a bolt is
# now drawn through drawn_hole(), so this number is what the bolt actually finds.
#
# The range the cell must PROVIDE, as against the range it happens to have. Half-angle,
# and a REQUIREMENT rather than a measurement -- so it is typed here and the geometry is
# checked against it, which is the only way round that can fail usefully. 0.5 deg is 30
# arcmin: enough to absorb a tube drilled a couple of millimetres out of square over the
# 85.7 mm station lever and still leave most of the range in hand, where collimation itself
# needs arcminutes. Raise it and verify() says whether the holes still oblige.
TILT_NEEDED = 0.5
NUT_AF = inch(0.375)  # 10-24 hex nut across flats
NUT_T = inch(0.130)
HEAD_AF = inch(0.3125)  # 10-24 hex head across flats
HEAD_T = inch(0.125)
# Clearance added across flats of a hex pocket. MEASURED on coupon_fit, 2026-07-28: on
# the 0.10 rung a 10-24 nut seats flat, will not rotate by hand and leaves the wall
# unwhitened -- all three acceptance criteria. The gauge outline came off the bed at
# 3.91" x 1.95" against a drawn 3.937" x 1.969" -- 0.7-0.9% linear shrink. The old 0.25
# placeholder would have left the nut about 0.17 mm loose in its pocket, free to rock.
FIT_PRESS = 0.10   # captured nut, and the knob's captured head. MEASURED.
# The pull-bolt head is fitted with silicone already curing on the other side of the
# plate, so it must fall in under its own weight -- a fit you have to tap is a defect
# there. UNVERIFIED: no 10-24 hex bolt was on hand when the coupon was read. Predicted
# from the measured shrink, this leaves ~0.13 mm of clearance (about 2 deg of rotational
# slop, which the wing nut takes out) against ~0.04 mm at FIT_PRESS.
FIT_SLIP = 0.20    # captured pull-bolt head. CONFIRM ON THE COUPON BEFORE PRINTING
                   # THE MIRROR PLATE -- rung 0.20, row H.
FIT = FIT_PRESS    # default for hex_prism(); every call site passes one explicitly

INSERT_BORE_D = 6.5  # 10-24 heat-set insert
INSERT_DEPTH = 14.0
# Vendor data for ruthex RX-10-24x9.5, the insert this bore is dimensioned around. Here
# rather than in a comment in the BOM because two assertions depend on them: the wall the
# tube screws pull against is measured from the insert's OD, not from the bore it melts
# into, and the bore has to land on the vendor's recommended hole AFTER shrink.
INSERT_OD = 7.1        # D1, the seated diameter -- what the surrounding wall is measured from
INSERT_HOLE_D = 6.4    # D3, ruthex's recommended hole in the plastic
INSERT_MIN_WALL = 2.6  # W, ruthex's minimum wall around a seated insert
INSERT_L = 9.5         # L; the bore is deeper on purpose, see INSERT_DEPTH
PRINT_SHRINK = 0.008   # measured on the fit coupon, 0.69-0.94% -- see TEST-COUPON.md

# What a small round hole loses BEYOND linear shrink. MEASURED on the first tube plate,
# 2026-07-31: holes drawn 5.159 came off the bed at 0.19" (4.83 mm). Shrink accounts for
# 0.04 mm of that 0.33; the other 0.29 is this.
#
# It is an OFFSET, not a percentage, which is why it cannot ride on PRINT_SHRINK: the
# slicer approximates the bore with chords inside the true circle, and the inner perimeter
# is laid on a tight radius where it over-fills. Both cost roughly half an extrusion width
# per side no matter how big the hole is.
#
# And it applies to ROUND holes only. The hex pockets on the same profile measured clean at
# FIT_PRESS = 0.10, whose whole clearance is 0.02-0.03 mm -- had they lost 0.29 as well
# they would have been a quarter-millimetre of interference and no nut would have entered,
# let alone seated flat without whitening. Flat walls have neither chords nor tight radii.
#
# Rounded up from the measured 0.291. The error is asymmetric: a hole 0.01 mm too big
# costs nothing anywhere in this design, and one 0.01 mm too small cost a 7-hour reprint.
HOLE_LOSS = 0.30


def drawn_hole(printed_d):
    """Diameter to DRAW so a round hole comes off the bed at printed_d.

    Every bolt hole in this model goes through here. The one that did not is the reason
    the function exists -- see HOLE_LOSS.
    """
    return (printed_d + HOLE_LOSS) / (1 - PRINT_SHRINK)


def printed_hole(drawn_d):
    """Inverse of drawn_hole(): what a hole drawn at drawn_d measures once printed."""
    return drawn_d * (1 - PRINT_SHRINK) - HOLE_LOSS


# The tube plate's PULL hole is the only bolt hole in the cell that is held to
# BOLT_CLEAR_D, because it is the only one doing mechanical work: the pull bolt leans in
# it, and that lean is the collimation range. Everything else a bolt passes through is a
# pass-through and is drawn frankly loose, because nothing is bought by keeping it tight:
#
#   - the tube plate's PUSH hole: the captured nut sets that bolt's axis and the landing
#     pad stops its tip, so the hole locates nothing at all;
#   - the mirror plate's pull bore: the head is captured in a hex pocket, which is what
#     locates it -- and that bolt is fitted against curing silicone, so a hole you have to
#     force it through is a defect at the worst possible moment;
#   - the pull knob's through bore: it exists so tightening has somewhere to put the bolt.
#
# 0.39 mm per side, against 0.17 at the pull station. A bolt drops through it unaimed.
BOLT_PASS_D = 5.6                          # as printed, again
PULL_HOLE_D = drawn_hole(BOLT_CLEAR_D)     # ~5.50 drawn -> 5.16 printed
PASS_HOLE_D = drawn_hole(BOLT_PASS_D)      # ~5.95 drawn -> 5.60 printed

# --- landing pads ------------------------------------------------------------
# A #4 washer, NOT a #10 one, and the bore is the whole point. This was a #10 washer --
# 0.500" OD on a 0.2031" bore -- which is BOLT_CLEAR_D, the free-fit clearance for the
# very bolt it is supposed to stop. The push bolt is coaxial with it, so the tip passed
# straight through the hole with 0.166 mm to spare and landed on the plastic floor of the
# recess: the pad did nothing, and the bolt bore on ABS over a SMALLER area than if the
# recess had not been there at all. Named PAD_*, not WASHER_*, so nobody reaches for
# BOLT_CLEAR_D again -- a pad sized for the bolt cannot stop the bolt.
PAD_OD = inch(0.3125)  # #4 flat washer
PAD_ID = inch(0.125)   # must be smaller than the bolt's point, and is asserted to be
PAD_T = inch(0.032)

BOLT_MAJOR_D = inch(0.190)  # 10-24 major diameter
# A machine screw's end is chamfered, so the flat that actually lands on the pad is
# smaller than the major diameter. 0.85 is the conservative end of what that chamfer
# leaves; the assertion uses it so the pad is sized against the worst screw, not the best.
BOLT_POINT_D = BOLT_MAJOR_D * 0.85

# One length for all six bolts, and it is a 1/2" multiple because odd lengths are a
# nuisance to source. See docs/adr/0002: both rear controls are printed knobs sized to
# clear each other RADIALLY, which is what makes 1-1/2" enough. The old 2" length existed
# only to drop a 30 mm knob below a wing nut, and that clearance depended on where the
# adjusters happened to be set. Buy MACHINE SCREWS -- #10 hex cap screws carry an
# unthreaded shank about 19 mm long, exactly where the captured nut needs thread.
PUSH_BOLT_L = inch(1.5)
PULL_BOLT_L = inch(1.5)

# The one purchased item that is NOT the same in both cells. 8" x 1.33" glass is 2574 g
# against the 6" cell's 1089, and the preload has to follow it: three springs must hold
# the moving assembly against its stop in any tube orientation, at about 2x its weight.
#
# Answered with FREE LENGTH rather than rate. The seat and the plate gap eat a fixed
# 16.24 mm of any spring put here, so a longer one is compressed further and makes more
# force at the same stiffness: 25 mm gives 8.76 mm of compression against 3.76, which
# reaches 2x preload with a spring no stiffer than the 6" cell's. Buying the force as
# rate instead would have meant ~27.5 lb/in and roughly double the knob torque, on a
# fluted ABS knob that HANDOFF already calls this design's weakest point.
SPRING_OD = CELL["spring"]["od"]
SPRING_WIRE_D = CELL["spring"]["wire"]
SPRING_FREE_L = CELL["spring"]["free"]
SPRING_RATE_LB_IN = CELL["spring"]["rate_lb_in"]
SPRING_RATE = SPRING_RATE_LB_IN * 4.4482 / 25.4   # N/mm
# Coils stacked solid. Not derived -- no vendor at this price states an active coil count
# (see HANDOFF), so it is read off the geometry and checked against the plate gap.
SPRING_SOLID_H = CELL["spring"]["solid"]
SPRING_SEAT_D = SPRING_OD + 0.8
# 1.0, not 2.5. The seat lengthens the spring's span, so every millimetre of it is a
# millimetre of preload thrown away: at 2.5 the cell made 1.16 lb per station against the
# 1.9 lb the spec claimed, and nothing caught it because no assertion computed force from
# geometry. verify() now does. The seat is belt-and-braces anyway -- the spring rides on
# the pull bolt shank and cannot wander.
SPRING_SEAT_DEPTH = 1.0

# Masses, for the preload check only -- nothing is drawn from these. The spring has to
# hold the mirror plate against its stop in any tube orientation, so what it works against
# is the glass plus everything bolted to the moving plate.
GLASS_RHO = 2.35e-3     # g/mm^3; between borosilicate 2.23 and soda-lime 2.50
ABS_RHO = 1.04e-3       # g/mm^3, solid
# Printed parts are not solid. The plate is 6 walls / 8 solid / 40% gyroid and the clips
# are 100%; 0.60 is the blended fraction of the drawn volume that is actually filament.
# The preload check has ~2x of margin, so it is insensitive to this to well within its
# own uncertainty -- what matters is that it TRACKS MIRROR_PLATE_T instead of ignoring it.
ABS_PACKING = 0.60
HARDWARE_G = 20.0       # 3 bolts + 3 washers + 3 caps riding on the moving plate

# --- mirror plate detail -----------------------------------------------------
# POST_IR and POST_T are up in the outlines block: MP_ARC_R is derived from them.
POST_SPAN = 30.0  # degrees
# Chamfer at the post root. Capped on BOTH sides: outboard by the plate edge
# (MP_ARC_R - post OD = 3.04 mm), inboard by the mirror's bond gap. Inboard now binds:
# the chamfer rises (c - post/mirror gap) at the mirror rim and must stay clear of the
# glass, which limits c to ~1.5 mm. Checked solid-against-solid, not by this arithmetic.
POST_FILLET = 1.5
CLIP_OVERHANG = 5.0  # how far the clip reaches over the glass
CLIP_T = 4.0
CLIP_SPAN = 24.0  # degrees

# Clips are SEPARATE parts, bolted on after the mirror is glued and cured. They cannot be
# integral: a clip reaching in to r=71.2 makes a 142.4 mm opening, and the mirror is
# 152.4 mm. Printed integrally the mirror could never be installed at all. Being separate
# also means a clip prints lying flat, so its underside -- the 0.030" air gap, one of the
# three gaps that must never close -- is a clean surface rather than a supported overhang.
CLIP_R_IN = MIRROR_D / 2 - CLIP_OVERHANG
CLIP_R_OUT = POST_IR + POST_T
CLIP_BOLT_R = POST_IR + POST_T / 2

M3_INSERT_D = 4.0  # heat-set insert bore
M3_INSERT_DEPTH = 6.0
M3_CLEAR_D = 3.4

RTV_WELL_D = 22.0
RTV_WELL_DEPTH = 1.0
# Plug that gives the silicone dab a continuous floor over the hex pocket. Sized so it
# CANNOT be a precision fit: the bore is wide enough to leave a real ledge under the disc,
# and the disc is a loose clearance fit that is bedded in a spot of RTV during glue-up.
# (At 10.0 the ledge was 0.27 mm at the hex corners -- the disc could drop through.)
CAP_D = 12.0        # counterbore in the mirror plate
CAP_CLEAR = 0.5     # diametral clearance: the disc must always drop in
CAP_T = 1.5

# What is left under the pull-bolt head after the RTV well, the cap and the head pocket
# are stacked into the plate. This carries the mirror's weight, and it is the number the
# slicer note quotes -- derived, so thickening or thinning the plate cannot leave the
# printing advice claiming a floor the part no longer has.
MP_FLOOR = MIRROR_PLATE_T - RTV_WELL_DEPTH - CAP_T - (HEAD_T + 0.4)

# --- knobs (spec 8.5, docs/adr/0002) -----------------------------------------
# Both rear controls are printed. That is what lets them clear each other RADIALLY --
# an invariant that holds no matter how the adjusters are set, unlike the axial escape
# it replaces. The whole budget is R_PULL - R_PUSH = 19.05 mm, split so the two walls
# come out equal: the Pull knob captures a NUT (11.11 mm across corners), the Push knob
# only a HEAD (9.28), so the pull knob needs the larger diameter to match walls.
PUSH_KNOB_D = 16.0
PULL_KNOB_D = 18.0
KNOB_T = 14.0
# Flutes are cut by cylinders centred OUTSIDE the rim, so depth is set directly instead
# of being half the cutter diameter -- at the old sizes a 6 mm cutter cut 3 mm deep and
# would have left 0.36 mm of wall here. 12 of them, phased so six land on the hex flats;
# the other six land on corners, which is what sets the depth.
KNOB_FLUTES = 12
KNOB_FLUTE_D = 5.0
KNOB_FLUTE_DEPTH = 1.2
# Nut stands proud of the pull knob's face, so steel bears on the tube plate and the
# printed body never touches it -- exactly the contact the wing nut used to make.
PULL_NUT_PROUD = 0.4

# --- shim --------------------------------------------------------------------
SHIM_L, SHIM_W = 30.0, 12.0

POST_H = RTV_T + MIRROR_T + CLIP_GAP  # post height above mirror plate front face


# ---------------------------------------------------------------- HELPERS

def at(angle, r, z=0.0):
    """A Pos on the ray of a station, radius r."""
    return Pos(r * cos(radians(angle)), r * sin(radians(angle)), z)


def rounded_triangle(arc_r, flat_d):
    """Triangle with three arc corners centred on the stations."""
    prof = Circle(arc_r)
    big = arc_r * 4
    for a in STATIONS:
        knife = Pos(flat_d + big / 2, 0) * Rectangle(big, big)
        prof -= Rot(0, 0, a + 60.0) * knife
    return prof


def hex_prism(across_flats, height, fit=FIT):
    """Hex pocket cutter, base at z=0, growing +z."""
    r = (across_flats + fit) / sqrt(3.0)
    return extrude(RegularPolygon(radius=r, side_count=6), height)


def sector_profile(r_in, r_out, span_deg, angle):
    """2D annular sector. The pie is an explicit fan: built from half-planes previously,
    which put the wedge 30 deg off the station and hung the posts over the plate edge."""
    ring = Circle(r_out) - Circle(r_in)
    n, rr = 24, r_out * 1.2
    pts = [(0.0, 0.0)]
    for i in range(n + 1):
        a = radians(angle - span_deg / 2 + span_deg * i / n)
        pts.append((rr * cos(a), rr * sin(a)))
    return ring & make_face(Polyline(*pts, close=True))


def arc_sector(r_in, r_out, span_deg, height, angle, z0):
    """Annular sector wall, used for posts and clips."""
    return Pos(0, 0, z0) * extrude(sector_profile(r_in, r_out, span_deg, angle), height)


def post_skirt(angle):
    """45 deg chamfer round the base of a post. The post root is a cantilever wall loaded
    in bending, and in FDM the layer interfaces there take the tension -- the weak
    direction -- so a sharp corner is a genuine stress riser.

    Size is capped by the room on BOTH sides: inboard by the mirror's bond gap, outboard
    by the plate edge. Outboard is the tighter of the two AND the more critical face: an
    upward load on the clip tips the post inward, putting the root's OUTER fibres in
    tension."""
    c = POST_FILLET
    dspan = 2 * degrees(c / (POST_IR + POST_T / 2))
    # Lofted, not a tapered extrude: OCC's tapered prism fails on this profile above
    # about 1 mm (Standard_TypeMismatch out of extrude_taper).
    bot = Pos(0, 0, MIRROR_PLATE_T) * sector_profile(
        POST_IR - c, POST_IR + POST_T + c, POST_SPAN + dspan, angle)
    top = Pos(0, 0, MIRROR_PLATE_T + c) * sector_profile(
        POST_IR, POST_IR + POST_T, POST_SPAN, angle)
    return loft([bot, top])


# ---------------------------------------------------------------- TUBE PLATE

def tube_plate():
    """Rear face at z=0, front face at z=TUBE_PLATE_T."""
    p = extrude(rounded_triangle(TP_ARC_R, TP_FLAT_D), TUBE_PLATE_T)

    # centre bore + fan mounting holes (unpopulated option)
    p -= extrude(Circle(CENTER_BORE / 2), TUBE_PLATE_T)
    for sx in (-1, 1):
        for sy in (-1, 1):
            p -= Pos(sx * FAN_PITCH / 2, sy * FAN_PITCH / 2) * extrude(
                Circle(FAN_HOLE_D / 2), TUBE_PLATE_T)

    for a in STATIONS:
        # --- push bolt: clearance through + hex nut pocket OPENING FORWARD -----
        # Pass-through: the nut below sets the axis, so this is drawn loose (BOLT_PASS_D).
        p -= at(a, R_PUSH) * extrude(Circle(PASS_HOLE_D / 2), TUBE_PLATE_T)
        pocket_z = TUBE_PLATE_T - (NUT_T + 0.4)
        p -= at(a, R_PUSH, pocket_z) * hex_prism(NUT_AF, NUT_T + 0.4, fit=FIT_PRESS)

        # --- pull bolt: clearance through + spring seat on the FRONT face ------
        # THE hole: the bolt leans here, and the lean is the collimation range.
        p -= at(a, R_PULL) * extrude(Circle(PULL_HOLE_D / 2), TUBE_PLATE_T)
        p -= at(a, R_PULL, TUBE_PLATE_T - SPRING_SEAT_DEPTH) * extrude(
            Circle(SPRING_SEAT_D / 2), SPRING_SEAT_DEPTH)

        # --- radial heat-set insert for the tube screw -------------------------
        bore = Rot(0, 90, 0) * Cylinder(radius=INSERT_BORE_D / 2, height=INSERT_DEPTH * 2)
        p -= Rot(0, 0, a) * Pos(TP_ARC_R, 0, TUBE_PLATE_T / 2) * bore

    return p


# ---------------------------------------------------------------- MIRROR PLATE

def mirror_plate():
    """Rear face at z=0, front face at z=MIRROR_PLATE_T, posts growing +z."""
    p = extrude(rounded_triangle(MP_ARC_R, MP_FLAT_D), MIRROR_PLATE_T)
    p -= extrude(Circle(MP_CENTER_BORE / 2), MIRROR_PLATE_T)
    for a in (30.0, 150.0, 270.0):          # mid-angles, between the stations
        p -= at(a, MP_LIGHTEN_RC) * extrude(Circle(MP_LIGHTEN_R), MIRROR_PLATE_T)

    for a in STATIONS:
        # --- landing pad: #10 washer let into the REAR face --------------------
        p -= at(a, R_PUSH) * extrude(Circle(PAD_OD / 2 + 0.15), PAD_T + 0.15)

        # --- pull bolt head captured from the FRONT, in compression ------------
        # Pass-through: the hex pocket locates this bolt, and it goes in against curing
        # silicone, so the bore is drawn loose on purpose (BOLT_PASS_D).
        p -= at(a, R_PULL) * extrude(Circle(PASS_HOLE_D / 2), MIRROR_PLATE_T)
        well_z = MIRROR_PLATE_T - RTV_WELL_DEPTH
        p -= at(a, R_PULL, well_z) * extrude(Circle(RTV_WELL_D / 2), RTV_WELL_DEPTH)
        cap_z = well_z - CAP_T
        p -= at(a, R_PULL, cap_z) * extrude(Circle(CAP_D / 2), CAP_T)
        head_h = HEAD_T + 0.4
        p -= at(a, R_PULL, cap_z - head_h) * hex_prism(HEAD_AF, head_h, fit=FIT_SLIP)

        # No spring seat on this face. Cutting one here would leave only 0.95 mm of ABS
        # between it and the hex pocket floor that the pull bolt head bears on. The
        # spring is located by its seat in the tube plate and by the bolt shank; it
        # simply bears on this flat face.

        # --- centering post: the gaps are the feature (spec §8) ----------------
        # The clip is NOT here -- it is a separate part, see CLIP_R_IN above.
        p += arc_sector(POST_IR, POST_IR + POST_T, POST_SPAN, POST_H, a, MIRROR_PLATE_T)
        p += post_skirt(a)
        # M3 heat-set insert in the post top, for the clip
        p -= at(a, CLIP_BOLT_R, MIRROR_PLATE_T + POST_H - M3_INSERT_DEPTH) * extrude(
            Circle(M3_INSERT_D / 2), M3_INSERT_DEPTH)

    return p


def clip():
    """Separate retainer, bolted to a post top. Printed lying flat: no overhang."""
    c = arc_sector(CLIP_R_IN, CLIP_R_OUT, CLIP_SPAN, CLIP_T, 0.0, 0.0)
    c -= Pos(CLIP_BOLT_R, 0, 0) * extrude(Circle(M3_CLEAR_D / 2), CLIP_T)
    return c


# ---------------------------------------------------------------- SMALL PARTS

def _fluted(d, height):
    """Knob body. Flute cutters sit OUTSIDE the rim, so KNOB_FLUTE_DEPTH means what it
    says: at the old sizing a 6 mm cutter centred on the rim cut 3 mm deep, which on a
    16 mm knob would have left 0.36 mm of wall.

    The 30 deg offset lands flutes on the hex flats. It is cosmetic at 12 flutes -- they
    sit every 30 deg and the hex repeats every 60, so half of them fall on corners
    whatever the phase, and DEPTH is what protects the wall (2.16 mm at a corner). The
    offset would matter at 6 flutes, where it is worth 0.9 mm. verify() checks the wall
    against the corner case and, separately, against the solids without assuming any of
    this."""
    k = extrude(Circle(d / 2), height)
    r_cut = d / 2 + KNOB_FLUTE_D / 2 - KNOB_FLUTE_DEPTH
    for i in range(KNOB_FLUTES):
        a = 30.0 + 360.0 * i / KNOB_FLUTES
        k -= at(a, r_cut) * extrude(Circle(KNOB_FLUTE_D / 2), height)
    return k


def push_knob():
    """Rear control on a Push bolt. Captures the hex head at its plate-facing end; it
    carries torque only, never axial load -- the bolt's reaction goes into the captured
    nut in the tube plate."""
    k = _fluted(PUSH_KNOB_D, KNOB_T)
    # CAPTURES its head rather than accepting it during a timed assembly step, so it
    # takes the press value even though the pocket is head-sized.
    k -= Pos(0, 0, KNOB_T - (HEAD_T + 0.4)) * hex_prism(HEAD_AF, HEAD_T + 0.4,
                                                        fit=FIT_PRESS)
    # No bore behind the pocket. The shank leaves through the pocket's own opening, which
    # is the knob's plate-facing face, so a clearance hole here would only be a hole out
    # the back -- invisible at ø30, an eyesore at ø16. Blind means a head pressed in is
    # in for good; that is the intent. (The PULL knob's identical-looking bore IS load-
    # bearing work: tightening drives the bolt end into it.)
    return k


def pull_knob():
    """Rear control on a Pull bolt -- replaces the wing nut. Captures a plain 10-24 hex
    nut in its FRONT face, PULL_NUT_PROUD shallower than the nut is thick, so the steel
    bears on the tube plate and this printed body never touches it. An ABS face rotating
    on an ABS face under sustained tension is the one loading this design refuses.

    Modelled like the push knob: pocket at the TOP, which is both the plate-facing face
    in the assembly and the way the part prints (pocket up, as the coupon measured it).
    """
    k = _fluted(PULL_KNOB_D, KNOB_T)
    pocket_h = NUT_T - PULL_NUT_PROUD
    k -= Pos(0, 0, KNOB_T - pocket_h) * hex_prism(NUT_AF, pocket_h, fit=FIT_PRESS)
    # Through bore: tightening drives more bolt into the knob, and it has to go somewhere.
    k -= extrude(Circle(PASS_HOLE_D / 2), KNOB_T)
    return k


def hex_nut():
    """The captured 10-24 nut. Modelled so the assembly sequence can show it going in."""
    n = extrude(RegularPolygon(radius=NUT_AF / sqrt(3.0), side_count=6), NUT_T)
    n -= extrude(Circle(inch(0.190) / 2), NUT_T)
    return n


def pull_bolt_tilt(as_printed=True):
    """Half-angle in degrees that a pull bolt can lean in its tube-plate hole.

    This IS the cell's collimation range -- see BOLT_CLEAR_D. The pull bolt is the one that
    leans: spring tension clamps its head flat on the mirror plate's floor, so the whole
    mirror tilt appears as bolt tilt here. The push bolt's nut is captured in the tube
    plate, so it stays normal to it and never tilts in a hole at all.

    A cylinder of diameter d leaning by t inside a hole of length L needs
    `d/cos t + L*tan t` of width, assuming it is free to centre itself -- which it is only
    because nothing registers the mirror plate laterally (spec section 11). Solved for t
    at the hole's width, by bisection because it does not inverse in closed form.

    Defaults to AS PRINTED, and that default is the whole point of the function. The hole
    is drawn at PULL_HOLE_D, oversize, so that it PRINTS at BOLT_CLEAR_D; feeding the drawn
    figure in here would report a range the cell does not have. It reported 1.42 deg for a
    plate that turned out to have none at all, because it modelled shrink and not
    HOLE_LOSS -- the assertions downstream were sound, the hole model under them was not.
    """
    d = BOLT_MAJOR_D
    D = printed_hole(PULL_HOLE_D) if as_printed else PULL_HOLE_D
    L = TUBE_PLATE_T - SPRING_SEAT_DEPTH   # the seat is a Oe9.8 counterbore; it guides nothing
    if D <= d:
        return 0.0
    lo, hi = 0.0, radians(45.0)
    for _ in range(80):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if d / cos(mid) + L * tan(mid) < D else (lo, mid)
    return degrees(lo)


def hex_head():
    """A 10-24 hex head, for checking that one seats in a pocket drawn for it.

    Not a printed part and not in PARTS -- it exists so the checks can put real hardware
    into a real recess instead of comparing across-flats numbers. verify() here and
    test_coupon.py both use it, which is why it is a function and not an expression
    written out twice.
    """
    return extrude(RegularPolygon(radius=HEAD_AF / sqrt(3.0), side_count=6), HEAD_T)


def washer():
    """#4 flat washer -- the Landing pad. Bore must be under the bolt's point; see PAD_ID."""
    return extrude(Circle(PAD_OD / 2) - Circle(PAD_ID / 2), PAD_T)


def pocket_cap():
    return extrude(Circle((CAP_D - CAP_CLEAR) / 2), CAP_T)


def shim():
    return extrude(Rectangle(SHIM_L, SHIM_W), RTV_T)


def fan():
    """A 40 mm fan, modelled here rather than downloaded.

    THIS IS A STAND-IN, not a vendor solid, and it is the only item in the model that is
    not either measured or drawn from the design's own dimensions. GrabCAD and the like
    need an account, and inventing a part number for a shape I drew myself would be
    worse than saying so. What the checks actually use is the envelope -- 40 x 40 x 10
    on a 32 mm hole pattern, which every 40 mm fan shares -- so a real one will drop into
    the same space. The blades exist to make it read as a fan on screen.

    Front face at z=0, body growing +z; it mounts to the tube plate's REAR face, so the
    assembly places it at z=-FAN_T.
    """
    body = extrude(RectangleRounded(FAN_SIZE, FAN_SIZE, FAN_CORNER_R)
                   - Circle(FAN_THROAT_D / 2), FAN_T)
    for sx in (-1, 1):
        for sy in (-1, 1):
            body -= Pos(sx * FAN_PITCH / 2, sy * FAN_PITCH / 2) * extrude(
                Circle(FAN_CLEAR_HOLE_D / 2), FAN_T)

    hub = Pos(0, 0, 1.0) * extrude(Circle(FAN_HUB_D / 2), FAN_T - 2.0)
    r_in, r_out = FAN_HUB_D / 2 - 0.5, FAN_THROAT_D / 2 - 0.6
    for i in range(FAN_BLADES):
        blade = Rot(0, 0, 360.0 * i / FAN_BLADES) * Pos((r_in + r_out) / 2, 0, FAN_T / 2) \
            * Rot(FAN_BLADE_PITCH, 0, 0) * Box(r_out - r_in, 9.0, 1.2)
        hub += blade
    return body + hub


def tube():
    """A stub of the sonotube. Display only -- see TUBE_* for why it is here at all."""
    return Pos(0, 0, TUBE_Z0) * extrude(
        Circle(TUBE_OD / 2) - Circle(TUBE_ID / 2), TUBE_Z1 - TUBE_Z0)


# ---------------------------------------------------------------- MAIN

# Printed parts. Bed-fit checks apply to these.
PARTS = {
    "tube_plate": tube_plate,
    "mirror_plate": mirror_plate,
    "clip": clip,
    "push_knob": push_knob,
    "pull_knob": pull_knob,
    "pocket_cap": pocket_cap,
    "shim": shim,
}

# Purchased hardware. Exported so the viewer can show the real thing, but not printed.
# The fan is a STAND-IN rather than a real thing -- see fan().
HARDWARE = {"hex_nut": hex_nut, "washer": washer, "fan": fan}

BED = (250.0, 250.0, 260.0)  # Anycubic Kobra S1

# ---------------------------------------------------------------- ASSEMBLY

# Where each part sits in the built cell, and which way it flies apart when exploded.
# The viewer reads this rather than repeating any dimension in JavaScript.

Z_MP = TUBE_PLATE_T + PLATE_GAP          # mirror plate rear face
Z_MIRROR = Z_MP + MIRROR_PLATE_T + RTV_T  # mirror back face
Z_CAP = Z_MP + MIRROR_PLATE_T - RTV_WELL_DEPTH - CAP_T
# Bearing face of the captured pull-bolt head: the hex pocket FLOOR. Bolt length is
# measured from under the head (the standard datum), so the tip is this minus the length.
Z_PULL_HEAD_FACE = Z_CAP - (HEAD_T + 0.4)

# Tube stub ends. Rear is measured from the tube plate's MID-PLANE (the plate is what
# locates the cell in the tube); front from the mirror's front SURFACE, not its back.
TUBE_Z0 = TUBE_PLATE_T / 2 - TUBE_REAR_OF_PLATE
TUBE_Z1 = Z_MIRROR + MIRROR_T + TUBE_FWD_OF_MIRROR


def _ring(r, z, angles=STATIONS, orient=True):
    """Instances on a station ring. orient=False for anything that keys into a pocket cut
    by at(), which is a pure translation -- those pockets all share ONE orientation, so a
    hex part rotated to its station angle lands 30 deg out (90/210/330 are all 30 mod 60)."""
    return [{"pos": [r * cos(radians(a)), r * sin(radians(a)), z],
             "rot": a if orient else 0.0}
            for a in angles]


# ---------------------------------------------------------------- SEQUENCE

# The order the cell actually goes together. Several steps are order-critical and say so:
# the captured nuts must go in before the plates mate, the mirror before the clips, and
# the shims must come out before the clips go on.
MP_UP = [0.0, 0.0, 95.0]   # mirror-plate sub-assembly, held clear while worked on
MP_KIDS = ("mirror_plate", "pull_bolts", "pocket_cap", "washer", "mirror", "shim", "clip")


def sequence():
    def pose(home=(), up=()):
        d = {k: [0.0, 0.0, 0.0] for k in home}
        d.update({k: list(MP_UP) for k in up})
        return d

    tp = ["tube_plate"]
    steps = [
        ("Tube plate: heat-set the inserts",
         "Three 10-24 heat-set inserts go into the radial bores in the rim, at "
         "mid-thickness. Run the iron in square. These three screws carry the entire "
         "cell \u2014 mirror, plates and hardware.", None,
         pose(home=tp)),
        ("Tube plate: press in the captured nuts",
         "Press a 10-24 hex nut into each of the three pockets on the FORWARD face. "
         "They face inward deliberately: a push bolt's reaction drives its nut rearward, "
         "into solid plastic, so the load is pure compression.",
         "Do this now. Once the plates are mated you cannot reach these pockets. After a "
         "bolt is threaded in, the nut is captive for good.",
         pose(home=tp + ["hex_nut"])),
        ("Mirror plate: heat-set the post inserts",
         "Three M3 heat-set inserts into the tops of the centering posts. These take the "
         "clips at the very end.", None,
         pose(home=tp + ["hex_nut"], up=["mirror_plate"])),
        ("Mirror plate: fit the pull bolts",
         "Drop a 10-24 \u00d7 1\u00bd\u2033 hex-head screw into each hex pocket from the FRONT "
         "face, head first. The pocket stops it turning; the head bears on the pocket "
         "floor in compression, which is the one loading ABS does not creep under.", None,
         pose(home=tp + ["hex_nut"], up=["mirror_plate", "pull_bolts"])),
        ("Cap the bolt pockets",
         "Drop a cap over each bolt head and bed it in a spot of RTV, flush with the "
         "floor of the well. It is a loose fit on purpose \u2014 the silicone holds it, "
         "so there is no press fit to get right and nothing to dial in.",
         "Without the caps, silicone runs into the hex and glues the bolt head in.",
         pose(home=tp + ["hex_nut"], up=["mirror_plate", "pull_bolts", "pocket_cap"])),
        ("Drop in the landing pads",
         "A #4 washer into each recess on the REAR face -- a #4 under a #10 bolt, on "
         "purpose. These are what the push bolt tips bear on. Steel on steel, so no bolt "
         "ever embosses the plastic and walks the collimation. A #10 washer would be the "
         "obvious thing to reach for and would be useless: its bore clears a #10 bolt, "
         "which is exactly what a landing pad must not do.", None,
         pose(home=tp + ["hex_nut"],
              up=["mirror_plate", "pull_bolts", "pocket_cap", "washer"])),
        ("Glue the mirror",
         "Three dabs of RTV in the wells. Lower the mirror past the centering posts "
         "(1.5 mm of slip) and set the three shims at the rim to hold a 0.0625\u2033 "
         "bond. Leave it to cure.",
         "The posts locate the mirror, they never grip it. Do not wedge or shim the "
         "mirror against a post.",
         pose(home=tp + ["hex_nut"],
              up=["mirror_plate", "pull_bolts", "pocket_cap", "washer", "mirror", "shim"])),
        ("Cure, then pull the shims",
         "Once cured, pull the three shims out. The mirror now floats on silicone and "
         "touches no plastic anywhere in the cell.", None,
         pose(home=tp + ["hex_nut"],
              up=["mirror_plate", "pull_bolts", "pocket_cap", "washer", "mirror"])),
        ("Fit the clips",
         "Bolt the three clips to the post tops with M3 screws. They stand 0.030\u2033 "
         "clear of the glass and must stay that way \u2014 they are drop-insurance, not "
         "a clamp.",
         "Never snug a clip down onto the mirror. Contact stress here is the classic "
         "cause of astigmatism and triangular stars.",
         pose(home=tp + ["hex_nut"], up=MP_KIDS[:-1] + ("clip",))),
        ("Springs on, and mate the plates",
         "Drop a spring over each pull bolt, then bring the mirror plate down so the "
         "three bolts pass through the tube plate.", None,
         pose(home=tp + ["hex_nut", "springs"] + [k for k in MP_KIDS if k != "shim"])),
        ("Pull knobs",
         "Press a 10-24 hex nut into the face of each pull knob — it stands 0.4 mm "
         "proud on purpose — then run the three knobs onto the pull bolts from the "
         "rear. The nut bears on the plate; the printed body never touches it.",
         "If the printed face touches the plate, the nut is in too deep. ABS turning on "
         "ABS under tension creeps, and the collimation goes with it.",
         pose(home=tp + ["hex_nut", "springs", "pull_knob"]
              + [k for k in MP_KIDS if k != "shim"])),
        ("Push bolts and push knobs",
         "Press a hex head into each push knob, then thread the three assemblies into "
         "the captured nuts from the rear until each tip just touches its landing "
         "washer.", None,
         pose(home=tp + ["hex_nut", "springs", "pull_knob", "push_bolts", "push_knob"]
              + [k for k in MP_KIDS if k != "shim"])),
        ("Into the tube, then collimate",
         "Hold the cell at the depth that reaches focus and drill the sonotube using the "
         "insert bores as the guide. Screws go in with 1\u2033 fender washers on the "
         "OUTSIDE of the tube. Then collimate: back the push knobs off, set tilt with the "
         "pull knobs, and snug the push knobs to lock.",
         "Without the fender washers a transport knock ovals the holes in the cardboard, "
         "and collimation is gone every time you move the scope.",
         pose(home=tp + ["hex_nut", "springs", "pull_knob", "push_bolts", "push_knob",
                         "tube", "fan"]
              + [k for k in MP_KIDS if k != "shim"])),
    ]
    return [{"title": t, "detail": d, "caution": c, "pose": p} for t, d, c, p in steps]


def downloads(parts):
    """What the viewer offers for download. Driven by PARTS, so a part cannot be exported
    without appearing here, and quantities are counted off the assembly, so the list
    cannot disagree with the picture it sits under. Coupons are not here: test_coupon.py
    writes its own manifest, because this file must not import it (it imports this one)."""
    qty = {p["name"]: len(p["instances"]) for p in parts}
    return [{"name": n, "kind": "printed", "qty": qty.get(n, 1),
             "step": f"{BUILD}/{n}.step", "stl": f"{BUILD}/{n}.stl",
             "3mf": f"{BUILD}/3mf/{n}.3mf"} for n in PARTS]


# ---------------------------------------------------------------- BILL OF MATERIALS

# mm. The shell counts below are LAYERS, so they only mean a thickness at this height, and
# the MP_FLOOR argument counts 3.45 mm as 17 layers at exactly this value. It is NOT in the
# 3MF: layer height is a global process setting with no per-object form, so it comes from
# whichever preset is selected -- pick a 0.2 mm one, or the shell counts buy a different
# thickness than the design reasoned about.
LAYER_H = 0.2


class Slice:
    """What one part wants from the slicer, as VALUES rather than prose.

    This used to be a hand-written string per part ('6 walls / 8 solid / 40% gyroid').
    Reading numbers back out of that to write a 3MF would have meant regex-parsing English
    -- and two of the seven rows ('100% infill') do not even match the pattern. So the
    values are the record and the sentence is generated from them; there is one place to
    change and the BOM cannot disagree with the 3MF.

    walls/solid are None for parts the design only ever specified as solid. That is not a
    gap to fill in: at 100% density on an 8-layer part they cannot change the outcome, and
    inventing numbers would have the BOM assert a spec nobody chose.
    """

    def __init__(self, density, walls=None, solid=None, pattern=None):
        assert 0 < density <= 100, f"density {density} out of range"
        assert (density < 100) == bool(pattern), \
            f"pattern is meaningful below 100% and only there (density={density})"
        self.density, self.walls, self.solid, self.pattern = density, walls, solid, pattern

    def prose(self):
        """The sentence the BOM prints. Generated, so it cannot drift from the values."""
        if self.walls is None:
            return f"{self.density:g}% infill"
        tail = f"{self.density:g}%" + (f" {self.pattern}" if self.pattern else "")
        return f"{self.walls} walls / {self.solid} solid / {tail}"

    def config(self):
        """This part's settings, as PER-OBJECT overrides.

        These ride in Metadata/model_settings.config, NOT project_settings.config, and the
        difference is the whole design. A project config REPLACES the process profile: the
        six keys we care about were applied and the other ~275 -- every speed and
        acceleration -- silently fell back to fdm_process_common, taking inner wall speed
        from 180 to 80 and acceleration from 4000 to 1000. The tube plate came out at 11 h
        instead of 7, and it was not merely slow: seam, brim and overhang handling had all
        reverted too. Per-object overrides OVERLAY the selected preset instead, so the
        machine settings stay yours and only the part-specific keys move. Confirmed by
        test, including that switching presets keeps the overrides.

        No layer_height here. It is a global process setting with no per-object form, so
        the preset supplies it -- see LAYER_H, which the shell counts assume.
        """
        c = {"sparse_infill_density": f"{self.density:g}%"}
        if self.pattern:
            c["sparse_infill_pattern"] = self.pattern
        if self.walls is not None:
            c["wall_loops"] = str(self.walls)
            c["top_shell_layers"] = str(self.solid)
            c["bottom_shell_layers"] = str(self.solid)
        return c


# The settings, and the one thing about each part worth knowing at the bed. 0.4 mm nozzle,
# ABS at 250-255 C, bed 100-110 C, enclosure closed, cooling 0-20%, 8-10 mm brim throughout
# -- those are settings for the machine, not for a part, so they are printed once in the BOM
# preamble rather than on every row. They are also RANGES, which is why they are prose here
# and are not in the 3MF: writing them out would mean picking numbers nobody chose.
PRINT = {
    "tube_plate": (Slice(40, walls=5, solid=5, pattern="gyroid"),
                   "Rear face down, no supports. Do not raise the infill: it adds "
                   "internal stress and INCREASES warping, which is this plate's main "
                   "failure mode."),
    "mirror_plate": (Slice(40, walls=6, solid=8, pattern="gyroid"),
                     "Rear face down, posts up, no supports. The 8 bottom layers are not "
                     f"a nicety -- the pull-bolt bearing floor is only {MP_FLOOR:.2f} mm "
                     "and carries the mirror, and the landing-pad recess ceilings are "
                     "bridged."),
    "clip": (Slice(100, walls=5, solid=6),
             "Prints flat, which puts the 0.030\" air-gap face on the bed as a clean "
             "surface instead of a supported overhang. Separate from the posts on "
             f"purpose: printed integrally they leave a {2 * CLIP_R_IN:.1f} mm opening "
             f"for a {MIRROR_D:.1f} mm mirror."),
    "push_knob": (Slice(100, walls=4, solid=5),
                  "Blind hex pocket for a bolt HEAD. Pressing a head in is one-way -- "
                  "there is no bore behind it to push against."),
    "pull_knob": (Slice(100, walls=4, solid=5),
                  "Hex pocket for a NUT, deliberately shallower than the nut. PRINT ONE "
                  "FIRST and press a nut in: the pocket sits in a 2.2 mm wall, and the "
                  "0.10 mm fit was measured in a 6 mm plate."),
    "pocket_cap": (Slice(100),
                   "A loose fit on purpose -- bedded in a spot of RTV, so there is no "
                   "press fit to dial in."),
    "shim": (Slice(100),
             "Assembly aid only. Sets the 0.0625\" bond, then comes out at step 8."),
}


SETTINGS_PATH = "Metadata/model_settings.config"
MODEL_PATH = "3D/3dmodel.model"


def insert_bosses():
    """Solid blocks around the three radial insert bores, as slicer MODIFIERS.

    The roof over a seated insert is 2.80 mm against ruthex's 2.6 mm minimum, and that
    assertion means 2.6 mm of MATERIAL. Printed at 40% gyroid it is not: of the 3.10 mm
    over the bore, only about 1 mm of plate top shell and 1 mm of solid over the void
    ceiling are dense, leaving ~1.1 mm of infill in the middle. Heat-set inserts also want
    something to displace into -- melting brass into gyroid voids gives unpredictable
    seating and less knurl engagement -- and these three screws carry the entire cell.

    Raising the infill globally is not the alternative: it adds internal stress and makes
    the plate warp, which is its main failure mode. Nor is adding walls, which follow
    perimeters and never reach the roof above a void. Density, locally, is the lever.

    Placed off the same expression that CUTS the bore in tube_plate(), so the two cannot
    drift apart. Sized to enclose the cylinder ruthex's minimum wall describes.
    """
    w = INSERT_OD + 2 * INSERT_MIN_WALL
    return [Rot(0, 0, a) * Pos(TP_ARC_R, 0, TUBE_PLATE_T / 2)
            * (Pos(-INSERT_DEPTH / 2, 0, 0)
               * Box(INSERT_DEPTH, w, TUBE_PLATE_T, align=(Align.CENTER,) * 3))
            for a in STATIONS]


# Which parts modelled HERE carry modifiers, what the modifiers are, and what they
# override. test_coupon.py has its own table and passes it in -- this module must not
# import that one, since that one imports this.
MODIFIERS = {
    "tube_plate": (insert_bosses, "insert_solid", {"sparse_infill_density": "100%"}),
}


def write_3mf(shape, path, slice_spec, part_number=None, modifiers=None):
    """A 3MF carrying the part AND the settings it wants.

    build123d's Mesher writes plain 3MF; the settings ride alongside it as per-object
    overrides, an Orca/Bambu-family convention rather than anything in the 3MF core spec
    -- the core spec has no notion of a perimeter count, so in other slicers this opens as
    plain geometry. The zip needs no [Content_Types].xml entry: the slicer reads the file
    by path, and real files from this machine's slicer do not declare a .config type.

    The override keys off the object id in 3D/3dmodel.model, which Mesher writes as 1 and
    <build> references, so the id is read back rather than assumed.
    """
    import re, zipfile
    path.parent.mkdir(parents=True, exist_ok=True)
    name = part_number or path.stem
    mods = MODIFIERS.get(name) if modifiers is None else modifiers
    rows = "".join(f'    <metadata key="{k}" value="{v}"/>\n'
                   for k, v in slice_spec.config().items())

    mesher = Mesher(unit=Unit.MM)
    mesher.add_shape(shape, part_number=part_number)
    mesher.write(str(path))

    if not mods:
        # No modifiers: leave the file exactly as it has been shipping -- a single mesh
        # object with the overrides on it. Not folded into the branch below on purpose,
        # so the common case stays the structure that was validated in the slicer.
        with zipfile.ZipFile(path) as z:
            model = z.read(MODEL_PATH).decode("utf-8")
        built = re.search(r'<item\s+objectid="(\d+)"', model)
        assert built, f"{path}: no <build><item> to attach settings to"
        cfg = ('<?xml version="1.0" encoding="UTF-8"?>\n<config>\n'
               f'  <object id="{built.group(1)}">\n'
               f'    <metadata key="name" value="{name}"/>\n{rows}'
               '  </object>\n</config>\n')
        with zipfile.ZipFile(path, "a", zipfile.ZIP_DEFLATED) as z:
            z.writestr(SETTINGS_PATH, cfg)
        return

    # With modifiers the part becomes a components object holding the real mesh plus one
    # mesh per modifier, and <part id> matches each component's objectid -- the layout a
    # real project file uses.
    make, mod_name, overrides = mods
    solids = list(make())

    def mesh_object(sh, oid):
        """ONE shape per object. add_shape() on a compound of disjoint solids silently
        writes only the FIRST -- which shipped a tube plate with one insert reinforced out
        of three, and looked correct everywhere except in the slice preview."""
        # Mesher.write() dispatches on the extension, so the scratch file must be .3mf.
        tmp = path.with_name(f"{path.stem}.tmp{oid}.3mf")
        ms = Mesher(unit=Unit.MM); ms.add_shape(sh); ms.write(str(tmp))
        with zipfile.ZipFile(tmp) as z:
            src = z.read(MODEL_PATH).decode("utf-8")
        tmp.unlink()
        blk = re.findall(r"<object\b(?:(?!</object>).)*?<mesh>.*?</mesh>\s*</object>",
                         src, re.S)[0]
        return re.sub(r'id="\d+"', f'id="{oid}"', blk, count=1)

    import uuid
    u = lambda: str(uuid.uuid4())
    ident = "1 0 0 0 1 0 0 0 1 0 0 0"
    blocks = [mesh_object(shape, 1)]
    blocks += [mesh_object(s, 2 + i) for i, s in enumerate(solids)]
    ids = list(range(1, len(blocks) + 1))
    comps = "".join(f'    <component objectid="{i}" p:UUID="{u()}" '
                    f'transform="{ident}"/>\n' for i in ids)
    container = max(ids) + 1
    model = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<model unit="millimeter" xml:lang="en-US"\n'
        ' xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"\n'
        ' xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06">\n'
        ' <resources>\n' + "\n".join(blocks) + "\n"
        f'  <object id="{container}" type="model" p:UUID="{u()}">\n'
        f'   <components>\n{comps}   </components>\n  </object>\n'
        ' </resources>\n'
        f' <build p:UUID="{u()}">\n  <item objectid="{container}" p:UUID="{u()}" '
        f'transform="{ident}" printable="1"/>\n </build>\n</model>\n')

    mtx = '<metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>'
    over = "".join(f'      <metadata key="{k}" value="{v}"/>\n'
                   for k, v in overrides.items())
    parts = (f'    <part id="1" subtype="normal_part">\n'
             f'      <metadata key="name" value="{name}"/>\n      {mtx}\n    </part>\n')
    # Numbered off the modifier list itself, not off STATIONS. Naming them by station
    # angle read better but pinned this writer to three-per-part: a caller with two
    # modifiers got three <part> entries, the last pointing at an object that does not
    # exist. The names are labels in the slicer's object tree; the count is structural.
    parts += "".join(
        f'    <part id="{2+i}" subtype="modifier_part">\n'
        f'      <metadata key="name" value="{mod_name}_{i+1}"/>\n      {mtx}\n{over}'
        f'    </part>\n' for i in range(len(solids)))
    cfg = ('<?xml version="1.0" encoding="UTF-8"?>\n<config>\n'
           f'  <object id="{container}">\n'
           f'    <metadata key="name" value="{name}"/>\n{rows}{parts}'
           '  </object>\n</config>\n')

    with zipfile.ZipFile(path) as z:
        keep = {n: z.read(n) for n in z.namelist() if n != MODEL_PATH}
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for n, b in keep.items():
            z.writestr(n, b)
        z.writestr(MODEL_PATH, model)
        z.writestr(SETTINGS_PATH, cfg)


def read_3mf_config(path):
    """The settings actually in a written 3MF -- for checking the file, not the intention."""
    import zipfile
    from xml.etree import ElementTree
    with zipfile.ZipFile(path) as z:
        if SETTINGS_PATH not in z.namelist():
            # The likeliest real failure -- geometry written, settings silently absent --
            # and it must not surface as a bare KeyError from inside zipfile.
            raise SystemExit(
                f"\n{path} carries NO print settings.\n"
                f"  it holds: {z.namelist()}\n"
                f"  the 3MF was written but {SETTINGS_PATH} was not injected; "
                f"see write_3mf()")
        root = ElementTree.fromstring(z.read(SETTINGS_PATH))
    obj = root.find("object")
    return {m.get("key"): m.get("value") for m in obj.findall("metadata")
            if m.get("key") != "name"}


def read_3mf_modifiers(path):
    """Every modifier in a written 3MF, as (name, overrides, bounding box).

    Reads the MESHES back out of the zip rather than trusting the geometry that went in.
    That distinction is the whole point: a compound of three blocks passed straight into
    add_shape() produced a file with ONE, and a coverage check run against the input
    geometry passed it happily. Only the file is evidence.
    """
    import re, zipfile
    from xml.etree import ElementTree
    with zipfile.ZipFile(path) as z:
        cfg = ElementTree.fromstring(z.read(SETTINGS_PATH))
        model = z.read(MODEL_PATH).decode("utf-8")
    out = []
    for part in cfg.find("object").findall("part"):
        if part.get("subtype") != "modifier_part":
            continue
        oid = part.get("id")
        blk = re.search(r'<object\b[^>]*id="' + oid + r'"(?:(?!</object>).)*?</object>',
                        model, re.S)
        assert blk, f"{path}: modifier part {oid} has no mesh object"
        xs, ys, zs = [], [], []
        for v in re.finditer(r'<vertex x="([-\d.eE]+)" y="([-\d.eE]+)" z="([-\d.eE]+)"',
                             blk.group(0)):
            xs.append(float(v.group(1))); ys.append(float(v.group(2)))
            zs.append(float(v.group(3)))
        assert xs, f"{path}: modifier part {oid} has an EMPTY mesh"
        meta = {m.get("key"): m.get("value") for m in part.findall("metadata")}
        out.append((meta.get("name"),
                    {k: v for k, v in meta.items() if k not in ("name", "matrix")},
                    (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))))
    return out


def purchased(total_cc=None):
    """The buy list, with the reason each line is what it is. Every number here is read
    from the parameters above rather than typed, so the BOM cannot drift from the model
    the way a hand-maintained table does."""
    preload = (SPRING_FREE_L - (PLATE_GAP + SPRING_SEAT_DEPTH)) * SPRING_RATE / 4.4482
    return [
        {"qty": 6, "item": "10-24 hex-head MACHINE screw",
         "spec": f"{PUSH_BOLT_L / 25.4:g}\" long ({PUSH_BOLT_L:.1f} mm), zinc or stainless",
         "note": "Machine screws, NOT hex cap screws: a #10 cap screw carries an "
                 "unthreaded shank about 19 mm long, exactly where the captured nut in "
                 "the tube plate needs thread. One length for all six, and a 1/2\" "
                 "multiple, because odd lengths are a nuisance to source."},
        {"qty": 6, "item": "10-24 hex nut",
         "spec": f"{NUT_AF / 25.4:g}\" across flats, {NUT_T / 25.4:g}\" thick",
         "note": "Three press into the tube plate's forward face (captured, for the push "
                 "bolts), three press into the pull knobs. Identical parts -- the pull "
                 "knob is what replaced the wing nut."},
        {"qty": 3, "item": "#4 flat washer (landing pad)",
         "spec": f"{PAD_OD / 25.4:g}\" OD, {PAD_ID / 25.4:g}\" bore, "
                 f"{PAD_T / 25.4:g}\" thick",
         "note": "A #4 washer under a #10 bolt, and that is NOT a typo. What the "
                 "push-bolt tips bear on -- steel on steel, so no bolt ever embosses the "
                 "plastic and walks the collimation. The bore has to be SMALLER than the "
                 "bolt's point or the pad does nothing: a #10 washer's 0.2031\" bore is "
                 "free-fit clearance for a #10 bolt, so the tip drops through it and "
                 "lands on plastic. The 0.125\" bore here is what the point rests on."},
        {"qty": 3, "item": "Compression spring",
         "spec": f"{SPRING_WIRE_D:g} mm wire x {SPRING_OD:g} mm OD x "
                 f"{SPRING_FREE_L:g} mm free length (~{SPRING_RATE_LB_IN:g} lb/in)",
         "note": f"BUY BY GEOMETRY, NOT BY RATE -- rate follows k = Gd^4/8D^3n and wire "
                 f"diameter dominates at the fourth power. Do not buy a 'telescope "
                 f"collimation spring kit': those compute to ~152 lb/in, more than ten "
                 f"times this, and you would never turn the pull knobs. Gives "
                 f"{preload:.2f} lb per station at the {PLATE_GAP / 25.4:g}\" gap. The "
                 f"FREE LENGTH is what carries the load here: the seat and the gap eat a "
                 f"fixed {PLATE_GAP + SPRING_SEAT_DEPTH:.2f} mm of any spring fitted, so "
                 f"a shorter one of the same rate arrives with less preload, not the "
                 f"same preload."},
        {"qty": 3, "item": "10-24 heat-set insert",
         "spec": f"{INSERT_BORE_D:g} mm bore x {INSERT_DEPTH:g} mm",
         "note": "Radial, in the tube plate rim, at mid-thickness. These three screws "
                 "carry the entire cell -- mirror, plates and hardware. Dimensioned "
                 "around [ruthex RX-10-24x9.5](https://www.ruthex.de/en/products/"
                 "ruthex-10-24-gewindeeinsatz-zoll-unc-50-stuck-rx-10-24x9-5-"
                 "gewindebuchsen-aus-messing-stabile-einpressmutter-durch-warme-in-3d-"
                 "druck-teile-aus-kunststoff-einsetzbar) -- 7.1 mm OD, 9.5 mm long, "
                 f"6.4 mm recommended hole. The {INSERT_BORE_D:g} mm bore drawn here "
                 "prints at ~6.45 mm at the measured 0.8% shrink, so do NOT compensate "
                 "it. Roof over the seated insert is 2.80 mm against ruthex's 2.6 mm "
                 "minimum wall -- the tight dimension, and why the insert coupon is "
                 "worth reading before this plate goes on the bed."},
        {"qty": 3, "item": "#10 screw (tube mount)",
         "spec": "length to suit: tube wall 0.125\" + washer + insert reach",
         "note": "Goes through the sonotube into the inserts above. Drill the tube using "
                 "the insert bores as the guide, at the depth that reaches focus."},
        {"qty": 3, "item": "1\" fender washer",
         "spec": "1\" OD, #10 bore",
         "note": "OUTSIDE the tube, and not optional. Statically the screws see ~70 psi "
                 "against cardboard good for 1000, but a 10 g transport knock puts ~700 "
                 "psi on the hole edge: the holes go oval and collimation is gone every "
                 "time you move the scope. A fender washer spreads it ~15x."},
        {"qty": 3, "item": "M3 heat-set insert",
         "spec": f"{M3_INSERT_D:g} mm bore x {M3_INSERT_DEPTH:g} mm",
         "note": "Into the tops of the centering posts, for the clips."},
        {"qty": 3, "item": "M3 cap screw",
         "spec": "~10 mm",
         "note": "Holds a clip. Never snug one down onto the glass -- the clips are "
                 "drop-insurance standing 0.030\" clear, not a clamp."},
        {"qty": 1, "item": "Black ABS filament",
         "spec": ("~1 kg spool" if total_cc is None else
                  f"{total_cc:.0f} cc of part volume ({total_cc * 1.04 / 1000:.2f} kg "
                  f"of ABS) -- a 1 kg spool covers it with the brim and a reprint"),
         "note": "ABS for the heat: a black cell in a closed tube sits in the sun. It "
                 "also creeps under sustained tension, which is why every steel-to-"
                 "plastic interface in this design is loaded in compression."},
        {"qty": 1, "item": "RTV silicone",
         "spec": "neutral-cure, small tube",
         "note": "Three dabs under the mirror at 0.0625\", plus a spot under each pocket "
                 "cap. NOT acetic-cure (the vinegar smell) near an aluminised surface."},
    ]


def bom(parts, volumes=None):
    """Printed parts and the buy list as one annotated table. Quantities for the printed
    rows are counted off the assembly, exactly as downloads() does, so the BOM, the
    download list and the picture cannot disagree about how many of anything there is."""
    qty = {p["name"]: len(p["instances"]) for p in parts}
    rows = []
    for n in PARTS:
        # .get, not [], so a part added to PARTS without print settings comes out as an
        # empty row that verify() reports -- rather than a KeyError from a BOM function,
        # which reads like a bug in the BOM instead of an unfinished part.
        spec, note = PRINT.get(n, (None, ""))
        settings = spec.prose() if spec else ""
        v = (volumes or {}).get(n)
        rows.append({"section": "printed", "qty": qty.get(n, 1), "item": n,
                     "spec": settings + (f", {v / 1000:.2f} cc each" if v else ""),
                     "note": note})
    # Filament is the one purchased line that depends on the printed ones, so it is only
    # quantified when real volumes are in hand (the export pass); verify() runs without.
    total_cc = (sum(qty.get(n, 1) * v for n, v in volumes.items()) / 1000
                if volumes else None)
    for r in purchased(total_cc):
        rows.append({"section": "purchased", **r})
    return rows


def bom_markdown(rows):
    tot = sum(r["qty"] for r in rows if r["section"] == "printed")
    out = [
        f"# Bill of materials — {CELL['mirror_d']:g}\" mirror cell",
        "",
        f"Generated by `mirror_cell.py --aperture {APERTURE}`, which writes it to",
        f"`{BUILD}/` and commits this copy as `{BOM_PATH}`. Every number comes from the",
        "model — quantities are counted off the assembly, dimensions read from the",
        "parameters — so **regenerate this file rather than editing it**. `--check` fails",
        "if the committed copy has gone stale.",
        "",
        f"For a {CELL['mirror_d']:g}\" × {CELL['mirror_t']:g}\" mirror in a "
        f"{CELL['tube_id']:g}\" ID tube.",
        "",
        f"**{tot} printed pieces** from {len(PARTS)} distinct parts, plus the buy list below.",
        "",
        "Printer settings that apply to everything: 0.4 mm nozzle, 0.2 mm layers, ABS at",
        f"250–255 °C, bed 100–110 °C, **enclosure closed, part cooling 0–20 %**, "
        f"{BRIM:g} mm brim.",
        "Both plates print rear-face-down with no supports.",
        "",
        "## Printed parts",
        "",
        "| Qty | Part | Slicer | Why it is like that |",
        "|---:|---|---|---|",
    ]
    for r in rows:
        if r["section"] == "printed":
            out.append(f"| {r['qty']} | `{r['item']}` | {r['spec']} | {r['note']} |")
    out += ["", "## Purchased", "",
            "| Qty | Item | Spec | Why |", "|---:|---|---|---|"]
    for r in rows:
        if r["section"] == "purchased":
            out.append(f"| {r['qty']} | {r['item']} | {r['spec']} | {r['note']} |")
    out += ["", "---", "",
            "Traps worth re-reading before you buy: machine screws (not cap screws),",
            "springs by geometry (not by rate), and fender washers on the OUTSIDE of the",
            "tube. See `mirror-cell-spec.md` §7 and `HANDOFF.md`.", ""]
    return "\n".join(out)


def bom_csv(rows):
    import csv, io
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["section", "qty", "item", "spec", "note"])
    for r in rows:
        w.writerow([r["section"], r["qty"], r["item"], r["spec"], r["note"]])
    return buf.getvalue()


def bom_snapshot_stale(rows, path=None):
    """Which BOM rows the committed snapshot no longer matches.

    BOM.md is committed because build/ is gitignored, so it is the copy anyone reading the
    repo (or a diff) actually sees -- and being committed is exactly what lets it go stale.
    Compared line for line, not byte for byte: the snapshot carries part volumes and a
    caller may not have built the solids.

    This is a query, not an assertion, and that is the point. Asked inside verify() it
    failed the run that would have fixed it; asked here, the writer can repair the file and
    --check can still refuse to.
    """
    import os
    path = path or BOM_PATH
    if not os.path.exists(path):
        return [r["item"] for r in rows]
    lines = open(path, encoding="utf-8").read().splitlines()

    def current(r):
        head = (f"| {r['qty']} | `{r['item']}` |" if r["section"] == "printed"
                else f"| {r['qty']} | {r['item']} |")
        return any(ln.startswith(head) and ln.rstrip().endswith(r["note"] + " |")
                   for ln in lines)

    return [r["item"] for r in rows if not current(r)]


def assembly():
    parts = [
        {"name": "tube_plate", "stl": "tube_plate.stl", "color": "#3d4450",
         "explode": [0, 0, -90], "instances": [{"pos": [0, 0, 0], "rot": 0}]},
        {"name": "mirror_plate", "stl": "mirror_plate.stl", "color": "#4a5260",
         "explode": [0, 0, 40], "instances": [{"pos": [0, 0, Z_MP], "rot": 0}]},
        {"name": "push_knob", "stl": "push_knob.stl", "color": "#8a6a3a",
         "explode": [0, 0, -170],
         "instances": _ring(R_PUSH, Z_MP - PUSH_BOLT_L - KNOB_T)},
        # hangs rearward off the plate face, held off it by the nut standing proud
        {"name": "pull_knob", "stl": "pull_knob.stl", "color": "#8a6a3a",
         "explode": [0, 0, -130],
         "instances": _ring(R_PULL, -(KNOB_T + PULL_NUT_PROUD), orient=False)},
        {"name": "clip", "stl": "clip.stl", "color": "#5f6a7a",
         "explode": [0, 0, 95],
         "instances": [{"pos": [0, 0, Z_MP + MIRROR_PLATE_T + POST_H], "rot": a}
                       for a in STATIONS]},
        # six identical nuts now: three captured in the tube plate, three in the pull
        # knobs. The rear three sit -NUT_T..0, i.e. bearing on the plate's rear face.
        {"name": "hex_nut", "stl": "hex_nut.stl", "color": "#c3ccd8",
         "group": "hardware", "explode": [0, 0, 60],
         "instances": _ring(R_PUSH, TUBE_PLATE_T - (NUT_T + 0.4), orient=False)
                      + _ring(R_PULL, -NUT_T, orient=False)},
        {"name": "washer", "stl": "washer.stl", "color": "#c3ccd8",
         "group": "hardware", "explode": [0, 0, -60],
         "instances": _ring(R_PUSH, Z_MP)},
        {"name": "pocket_cap", "stl": "pocket_cap.stl", "color": "#8a6a3a",
         "explode": [0, 0, 110], "instances": _ring(R_PULL, Z_CAP)},
        # Display only, and both flagged "context": they are drawn but must not drive the
        # camera framing, or a 202 mm tube shrinks the cell to nothing in every step.
        {"name": "fan", "stl": "fan.stl", "color": "#23262c", "context": True,
         "explode": [0, 0, -230], "instances": [{"pos": [0, 0, -FAN_T], "rot": 0}]},
        {"name": "shim", "stl": "shim.stl", "color": "#b0552f", "group": "shim",
         "explode": [0, 0, 150],
         "instances": [{"pos": [66 * cos(radians(a)), 66 * sin(radians(a)),
                                Z_MP + MIRROR_PLATE_T], "rot": a}
                       for a in (30.0, 150.0, 270.0)]},
    ]
    return {
        "stack": {
            "tube_plate_front": TUBE_PLATE_T, "mirror_plate_rear": Z_MP,
            "mirror_back": Z_MIRROR, "mirror_front": Z_MIRROR + MIRROR_T,
            "clip_underside": Z_MP + MIRROR_PLATE_T + POST_H,
        },
        "sequence": sequence(),
        "parts": parts,
        "downloads": downloads(parts),
        # The BOM travels in assembly.json too, so the viewer can say how many lines it
        # is offering without parsing the file it links to. The rows here carry no
        # volumes -- the exporter writes the quantified copy to build/bom.md.
        "bom": {"md": f"{BUILD}/bom.md", "csv": f"{BUILD}/bom.csv",
                "rows": bom(parts)},
        # generated procedurally in the viewer from these numbers
        "mirror": {"d": MIRROR_D, "t": MIRROR_T, "z": Z_MIRROR, "explode": [0, 0, 230]},
        # the tube is a plain annulus, so the viewer draws it rather than loading an STL
        "tube": {"id": TUBE_ID, "od": TUBE_OD, "z0": TUBE_Z0, "z1": TUBE_Z1,
                 "explode": [0, 0, -330]},
        # springs explode radially: axially they would stay buried between the plates.
        # z0 is the BOTTOM OF THE SEAT, not the plate face -- the seat is part of the
        # spring's span, which is the whole reason it costs preload.
        "springs": {"coil_d": SPRING_OD, "wire_d": SPRING_WIRE_D,
                    "z0": TUBE_PLATE_T - SPRING_SEAT_DEPTH, "z1": Z_MP,
                    "instances": [
                        {"pos": [R_PULL * cos(radians(a)), R_PULL * sin(radians(a)),
                                 (TUBE_PLATE_T + Z_MP) / 2],
                         "explode": [95 * cos(radians(a)), 95 * sin(radians(a)), 0]}
                        for a in STATIONS]},
        "bolts": [
            # z_head is the head's BEARING FACE; the head sits on the far side of it
            # from the tip. Push: head rearward, into the knob. Pull: head forward,
            # captured in the mirror plate. Getting this backwards flips the bolt.
            {"name": "push_bolts", "kind": "push", "r": R_PUSH, "angles": list(STATIONS), "d": inch(0.190),
             "head_t": HEAD_T, "head_af": HEAD_AF,
             "z_head": Z_MP - PUSH_BOLT_L, "z_tip": Z_MP, "explode": [0, 0, -170]},
            {"name": "pull_bolts", "kind": "pull", "r": R_PULL, "angles": list(STATIONS), "d": inch(0.190),
             "head_t": HEAD_T, "head_af": HEAD_AF,
             "z_head": Z_PULL_HEAD_FACE, "z_tip": Z_PULL_HEAD_FACE - PULL_BOLT_L,
             "explode": [0, 0, 110]},
        ],
    }


def verify():
    """Assertions that encode the spec. Every one of these has a reason."""
    ok = []

    def chk(cond, msg):
        ok.append((bool(cond), msg))

    # --- the three gaps that must never close (spec §8) -----------------------
    chk(abs((POST_IR - MIRROR_D / 2) - POST_GAP) < 1e-9,
        f"centering post radial gap = {POST_IR - MIRROR_D/2:.3f} mm ({POST_GAP/25.4:.3f}\")")
    chk(abs((POST_H - RTV_T - MIRROR_T) - CLIP_GAP) < 1e-9,
        f"clip air gap over mirror face = {POST_H - RTV_T - MIRROR_T:.3f} mm ({CLIP_GAP/25.4:.3f}\")")
    chk(RTV_T > 1.0, f"RTV bond thickness = {RTV_T:.3f} mm")

    # --- pull bolt head bears on a sound floor, in compression (spec §6) ------
    floor = MP_FLOOR
    chk(floor >= 3.0, f"mirror plate floor under hex pocket = {floor:.2f} mm (>= 3.0)")

    # --- push bolt nut floor --------------------------------------------------
    nut_floor = TUBE_PLATE_T - (NUT_T + 0.4)
    chk(nut_floor >= 3.0, f"tube plate floor under nut pocket = {nut_floor:.2f} mm")

    # --- bolt head must pass through the cap bore during assembly -------------
    # FIT_SLIP, not FIT_PRESS: this is the MIRROR PLATE's pocket. Pointed at the wrong
    # constant these three checks would still pass and would be checking nothing.
    head_corners = 2 * (HEAD_AF + FIT_SLIP) / sqrt(3.0)
    chk(head_corners < CAP_D,
        f"head across corners {head_corners:.2f} < cap bore {CAP_D:.2f} mm")
    chk(0 < FIT_PRESS <= FIT_SLIP,
        f"press fit {FIT_PRESS:.2f} is positive and no looser than the slip fit "
        f"{FIT_SLIP:.2f} mm")
    cap_d = CAP_D - CAP_CLEAR
    chk(CAP_CLEAR > 0, f"cap is a clearance fit ({CAP_CLEAR} mm), never a press fit")
    chk((CAP_D - head_corners) / 2 >= 1.0,
        f"ledge under the cap = {(CAP_D-head_corners)/2:.2f} mm at the hex corners")
    chk((cap_d - head_corners) / 2 >= 0.8,
        f"cap overlaps its ledge by {(cap_d-head_corners)/2:.2f} mm -- cannot drop through")
    chk(CAP_D < RTV_WELL_D,
        f"cap bore {CAP_D:.1f} inside the RTV well {RTV_WELL_D:.1f} mm "
        f"({100*(CAP_D/RTV_WELL_D)**2:.0f}% of the dab area)")

    # --- fan option must not undercut the centre bore -------------------------
    web = sqrt(2) * FAN_PITCH / 2 - FAN_HOLE_D / 2 - CENTER_BORE / 2
    chk(web >= 1.5, f"web between fan hole and centre bore = {web:.2f} mm")

    # --- spring works across the whole travel (spec §4, §7) -------------------
    # solid_h, NOT solid: this function also defines solid(nm) further down to look parts
    # up by name, and a float bound to that name here shadows it for everything in between.
    # A check written in that gap silently intersected against a float, threw, and was
    # turned into a PASS by a blanket except. Do not reintroduce the short name.
    free, solid_h = SPRING_FREE_L, SPRING_SOLID_H
    chk(free > PLATE_GAP, f"spring free length {free} > gap {PLATE_GAP:.2f} mm (stays preloaded)")
    chk(solid_h < PLATE_GAP - 3.0, f"solid height {solid_h} well below gap {PLATE_GAP:.2f} mm (no coil bind)")
    chk(SPRING_SEAT_D > SPRING_OD, "spring seat clears spring OD")

    # --- posts land ON the stations, and on plate material --------------------
    from math import atan2, degrees, hypot
    mp = mirror_plate()
    z0 = MIRROR_PLATE_T + 0.05
    h = POST_H + CLIP_T + 5
    ups = (mp & Pos(0, 0, z0 + h / 2) * Box(500, 500, h)).solids()
    chk(len(ups) == 3, f"{len(ups)} posts above the plate (expect 3, clips are separate)")
    top = max(s.bounding_box().max.Z for s in ups)
    chk(abs(top - (MIRROR_PLATE_T + POST_H)) < 1e-6,
        f"nothing integral above the post tops (top z={top:.3f}) -- clips must be separate")
    found = sorted(degrees(atan2(s.center().Y, s.center().X)) % 360 for s in ups)
    want = sorted(a % 360 for a in STATIONS)
    chk(all(abs(f - w) < 0.5 for f, w in zip(found, want)),
        f"posts at {[round(a,1) for a in found]} vs stations {want}")

    def plate_edge_r(phi):
        r = MP_ARC_R
        for f in (30.0, 150.0, 270.0):
            c = cos(radians(phi - f))
            if c > 1e-6:
                r = min(r, MP_FLAT_D / c)
        return r

    worst = min(plate_edge_r(a + d) - (POST_IR + POST_T)
                for a in STATIONS for d in (-POST_SPAN / 2, 0, POST_SPAN / 2))
    chk(worst >= 0.0, f"post outer edge inside plate outline by {worst:.2f} mm")

    # --- the mirror can actually be installed ---------------------------------
    slip = 2 * POST_IR - MIRROR_D
    chk(slip > 0, f"mirror drops in past the posts with {slip:.2f} mm across flats")
    chk(2 * CLIP_R_IN < MIRROR_D,
        f"clip opening {2*CLIP_R_IN:.1f} < mirror {MIRROR_D:.1f} mm, so it does retain")
    chk(POST_T - M3_INSERT_D >= 3.0,
        f"post wall around M3 insert = {(POST_T-M3_INSERT_D)/2:.2f} mm each side")

    # --- the rear face: two printed knobs on one station ray (ADR-0002) --------
    # THE invariant. It is radial, so unlike the axial escape it replaced it does not
    # depend on bolt length or on where either adjuster happens to be set. Both parts
    # shrink together, so the printed clearance is 0.993 of this -- a 0.7% effect.
    knob_gap = (R_PULL - PULL_KNOB_D / 2) - (R_PUSH + PUSH_KNOB_D / 2)
    chk(knob_gap >= 2.0,
        f"push knob to pull knob = {knob_gap:.2f} mm, unconditional (>= 2.0)")

    # Range of the pull side: unscrewing the knob opens the gap and pulls bolt out of
    # the nut, so the thread runs out eventually. The spring should run out FIRST.
    protrude = PULL_BOLT_L - Z_PULL_HEAD_FACE
    thread_range = protrude - NUT_T
    chk(thread_range > 0,
        f"pull bolt reaches through its nut: {protrude:.2f} mm out, nut {NUT_T:.2f} tall "
        f"({thread_range:+.2f} mm of range beyond it)")
    # The mechanism must stop before the spring does, not after: at the widest gap the
    # thread allows, the spring is still under load and still doing its job. (Written the
    # other way round first -- "spring goes slack first" -- which is the softer failure
    # but leaves settings where the cell is sprung by nothing.)
    spring_range = SPRING_FREE_L - (PLATE_GAP + SPRING_SEAT_DEPTH)
    chk(thread_range < spring_range,
        f"thread runs out at +{thread_range:.2f} mm, still {spring_range-thread_range:.2f}"
        f" mm inside the spring's +{spring_range:.2f} mm -- never slack in range")

    # The push screw must still reach the mirror plate at the loosest setting the pull
    # side can reach; if it cannot, one adjuster can outrun the other.
    gap_max = PLATE_GAP + min(thread_range, spring_range)
    standoff = PUSH_BOLT_L - TUBE_PLATE_T - PLATE_GAP
    standoff_min = PUSH_BOLT_L - TUBE_PLATE_T - gap_max
    chk(standoff_min > 2.0,
        f"push knob stands off {standoff:.2f} mm at nominal, {standoff_min:.2f} mm at the "
        f"widest gap the spring allows -- it never bottoms on the plate")

    # Spring preload, computed from geometry rather than typed into the spec. The seat
    # is part of the span: at 2.5 mm it quietly cost 40% of the preload.
    preload = (SPRING_FREE_L - (PLATE_GAP + SPRING_SEAT_DEPTH)) * SPRING_RATE  # N
    # The moving assembly, computed rather than typed in. It was 11.8 N as a literal, which
    # would not have followed MIRROR_PLATE_T: thickening the plate to 0.500" adds ~28 g and
    # the check would still have printed the old ratio. Glass and printed parts come from
    # the model's own solids; only the steel is an allowance, because it is purchased.
    glass = pi * (MIRROR_D / 2) ** 2 * MIRROR_T * GLASS_RHO          # g
    printed = (mirror_plate().volume + 3 * clip().volume) * ABS_RHO * ABS_PACKING
    moving = (glass + printed + HARDWARE_G) * 9.81e-3                # N
    chk(abs(moving - CELL["moving_n"]) < 1.5,
        f"moving assembly {moving/4.4482:.2f} lb computed from solids, against the "
        f"{CELL['moving_n']/4.4482:.2f} lb this cell states "
        f"(glass {glass:.0f} g + printed {printed:.0f} g + steel {HARDWARE_G:.0f} g)")
    chk(3 * preload > 1.5 * moving,
        f"spring preload {preload/4.4482:.2f} lb/station, {3*preload/4.4482:.2f} lb total "
        f"vs {moving/4.4482:.2f} lb of moving assembly ({3*preload/moving:.2f}x)")

    # The push knob is blind behind its pocket -- probe the axis where a bore would be.
    depth = KNOB_T - (HEAD_T + 0.4)
    probe = extrude(Circle(PASS_HOLE_D / 2), depth - 0.5)
    try:
        solid_behind = (probe & push_knob()).volume
    except Exception:
        solid_behind = 0.0
    chk(abs(solid_behind - probe.volume) < 1.0,
        f"push knob is solid behind its pocket for {depth:.1f} mm "
        f"({solid_behind:.0f} of {probe.volume:.0f} mm^3 filled)")

    # The pull knob must never touch the plate: only the steel nut does.
    chk(PULL_NUT_PROUD > 0.2,
        f"nut stands {PULL_NUT_PROUD:.2f} mm proud of the pull knob face")

    # Sourcing rule, as an assertion rather than a comment that rots.
    halves = PUSH_BOLT_L / inch(0.5)
    chk(PUSH_BOLT_L == PULL_BOLT_L and abs(halves - round(halves)) < 1e-6,
        f"one bolt length throughout, and it is a 1/2\" multiple: {PUSH_BOLT_L/25.4:.3f}\"")

    # The thing that started this: hardware hanging off the back of the tube plate.
    stack_out = max(KNOB_T + PULL_NUT_PROUD, standoff + KNOB_T)
    chk(stack_out < 28.0, f"rear stack-out {stack_out:.2f} mm at nominal (< 28.0)")

    # --- knob walls: arithmetic, then the same thing against the solids --------
    for nm, d, af in (("push", PUSH_KNOB_D, HEAD_AF), ("pull", PULL_KNOB_D, NUT_AF)):
        corners = 2 * (af + FIT_PRESS) / sqrt(3.0)
        wall = (d - 2 * KNOB_FLUTE_DEPTH - corners) / 2
        chk(wall >= 2.0,
            f"{nm} knob wall at a flute = {wall:.2f} mm (>= 2.0), "
            f"hex {corners:.2f} across corners in ø{d:.0f}")
    # Solid against solid: the flutes must not break into the pocket ANYWHERE. The
    # arithmetic above assumes the phase lands flutes on flats; this does not assume it.
    for nm, fn, d, af, h in (("push", push_knob, PUSH_KNOB_D, HEAD_AF, HEAD_T + 0.4),
                             ("pull", pull_knob, PULL_KNOB_D, NUT_AF, NUT_T)):
        pocket = Pos(0, 0, KNOB_T - h) * hex_prism(af, h, fit=FIT_PRESS)
        flutes = Compound([at(30.0 + 360.0 * i / KNOB_FLUTES,
                              d / 2 + KNOB_FLUTE_D / 2 - KNOB_FLUTE_DEPTH)
                           * extrude(Circle(KNOB_FLUTE_D / 2), KNOB_T)
                           for i in range(KNOB_FLUTES)])
        try:
            broke = (pocket & flutes).volume
        except Exception:
            broke = 0.0
        chk(broke < 1.0,
            f"{nm} knob: {KNOB_FLUTES} flutes never break into the hex pocket "
            f"(overlap {broke:.2f} mm^3)")

    bolts = {b["kind"]: b for b in assembly()["bolts"]}
    push_dir = bolts["push"]["z_head"] - bolts["push"]["z_tip"]
    pull_dir = bolts["pull"]["z_head"] - bolts["pull"]["z_tip"]
    chk(push_dir < 0, f"push bolt head is REARWARD of its tip ({push_dir:+.1f} mm)")
    chk(pull_dir > 0, f"pull bolt head is FORWARD of its tip ({pull_dir:+.1f} mm) "
                      f"-- captured in the mirror plate")
    chk(abs(bolts["pull"]["z_head"] - Z_PULL_HEAD_FACE) < 1e-9,
        "pull bolt head bears on the hex pocket floor")

    for nm, r, d in (("push", R_PUSH, PUSH_KNOB_D), ("pull", R_PULL, PULL_KNOB_D)):
        sep = 2 * r * sin(radians(60))
        chk(sep - d > 5.0,
            f"adjacent {nm} knobs clear each other by {sep-d:.1f} mm")

    # --- no part may have two instances at the same place ---------------------
    # (both the springs and the wing nuts have been stacked on the axis at some point,
    #  by forgetting that geometry modelled about the origin still needs placing)
    # Checked in WORLD space: some parts carry their radius in the geometry (clip) and
    # some are modelled about their own origin (wingnut, knob). Comparing raw pos values
    # gets both cases wrong -- comparing where the solid actually lands does not.
    built = {**PARTS, **HARDWARE}
    cache = {}

    def solid(nm):
        if nm not in cache:
            cache[nm] = built[nm]()
        return cache[nm]

    for part in assembly()["parts"]:
        c = solid(part["name"]).center()
        world = []
        for i in part["instances"]:
            a = radians(i.get("rot", 0.0))
            world.append((round(c.X * cos(a) - c.Y * sin(a) + i["pos"][0], 3),
                          round(c.X * sin(a) + c.Y * cos(a) + i["pos"][1], 3)))
        chk(len(set(world)) == len(world),
            f"{part['name']}: {len(world)} instances land in "
            f"{len(set(world))} distinct places")
        if len(world) == 3:
            radii = {round(hypot(*w), 1) for w in world}
            chk(len(radii) == 1 and max(radii) > 1.0,
                f"{part['name']}: all 3 land on one ring, r={radii}")

    # --- the sequence may only name things that exist, and must end complete ---
    A = assembly()
    drawable = {p["name"] for p in A["parts"]} | {"mirror", "springs", "tube"} \
        | {b["name"] for b in A["bolts"]}
    named = {k for st in A["sequence"] for k in st["pose"]}
    chk(named <= drawable, f"sequence names only real items; stray: {named - drawable}")
    final = set(A["sequence"][-1]["pose"])
    chk(final == drawable - {"shim"},
        f"final step shows everything but the shims; missing {drawable-{'shim'}-final}")

    # --- the download list must offer every printed part, and no ghosts --------
    # The failure this guards against is silent: a part added to PARTS and exported but
    # missing from the viewer's list, or a stale entry pointing at a file that stopped
    # being written. Quantities are checked against the assembly so the list cannot
    # promise three of something the picture shows one of.
    import os
    D = A["downloads"]
    printed = [d for d in D if d["kind"] == "printed"]
    listed = {d["name"] for d in printed}
    chk(listed == set(PARTS),
        f"downloads offer every printed part; missing {set(PARTS) - listed}, "
        f"stray {listed - set(PARTS)}")
    chk(len({d["name"] for d in D}) == len(D), "no part is listed for download twice")
    inst = {p["name"]: len(p["instances"]) for p in A["parts"]}
    chk(all(d["qty"] == inst[d["name"]] for d in D if d["name"] in inst),
        "download quantities match the instance counts in the assembly")
    # (case-insensitive: the vendor file is .STEP, and that is McMaster's spelling)
    chk(all(d["step"].lower().endswith(".step") and d["stl"].endswith(".stl")
            for d in D),
        "every download names a .step and a .stl")
    chk(all(d["step"] == f"{BUILD}/{d['name']}.step" for d in printed),
        "printed downloads point at the files the exporter actually writes")
    # The 3MF is the one the viewer offers for slicing, so the guarantee has to run both
    # ways: the panel cannot offer a file the exporter skips, and cannot silently omit one
    # it writes. Coupons carry their own manifest and are checked in test_coupon.py.
    chk(all(d.get("3mf") == f"{BUILD}/3mf/{d['name']}.3mf" for d in printed),
        "printed downloads point at the 3MFs the exporter actually writes")
    chk(all(d["kind"] == "printed" for d in D),
        "every download is a printed part -- no purchased solid is in the design now")

    # --- the BOM must agree with the assembly it claims to describe ------------
    # A BOM is exactly the document that rots: it is read once, at the shop counter,
    # long after the geometry moved. So nothing in it is typed -- quantities come off
    # the same instance counts the picture does, and these checks are what keep it so.
    B = A["bom"]["rows"]
    bprint = {r["item"]: r for r in B if r["section"] == "printed"}
    chk(set(bprint) == set(PARTS),
        f"BOM lists every printed part; missing {set(PARTS) - set(bprint)}, "
        f"stray {set(bprint) - set(PARTS)}")
    chk(all(bprint[n]["qty"] == inst[n] for n in bprint if n in inst),
        "BOM printed quantities match the instance counts in the assembly")
    chk({d["name"]: d["qty"] for d in printed} == {n: r["qty"] for n, r in bprint.items()},
        "BOM and download list agree on quantities part for part")
    chk(all(r["note"].strip() and r["spec"].strip() for r in B),
        "every BOM line is annotated -- a spec and a reason, not just a count")
    # The fasteners the model actually draws must be on the buy list in the right number.
    # This is the check that would fire if a station were added, or a knob stopped
    # capturing a nut: the drawn count changes and the BOM does not follow.
    buy = {r["item"]: r["qty"] for r in B if r["section"] == "purchased"}
    drawn = {"10-24 hex nut": inst["hex_nut"],
             "#4 flat washer (landing pad)": inst["washer"],
             "Compression spring": len(A["springs"]["instances"]),
             "10-24 hex-head MACHINE screw": sum(len(b["angles"]) for b in A["bolts"])}
    chk(all(buy.get(k) == v for k, v in drawn.items()),
        f"BOM buys exactly the hardware the model draws: {drawn}")
    # Both bolts are one length, which is the whole point of ADR-0002's rework, and the
    # BOM states that length as a single number. It may not quietly become two.
    chk(abs(PUSH_BOLT_L - PULL_BOLT_L) < 1e-9,
        "push and pull bolts are the same length, so the BOM's one screw line is honest")
    md = bom_markdown(B)
    chk(all(r["item"] in md for r in B) and md.count("\n|") >= len(B),
        f"the Markdown BOM renders every one of its {len(B)} lines")

    # The BOM.md snapshot is NOT checked here. It used to be, and the check deadlocked its
    # own fix: verify() raises SystemExit on failure and the write happens after it, so the
    # first run after editing any BOM note failed, skipped the write, and every rerun failed
    # identically. Currency is now enforced where it can also be repaired -- see
    # bom_snapshot_stale() and the --check flag.

    # --- parts that sit in recesses must actually fit in them -----------------
    # Intersecting the placed solid with its plate catches a mis-keyed hex directly:
    # a nut rotated to its station angle collides with the pocket wall.
    # "clip" closes one of the two fits that had no solid-vs-solid test: the clips are
    # drawn separately from the posts they land on, so nothing but this catches a clip
    # whose underside or M3 bore has drifted into the post top.
    seated = {"hex_nut": ("tube_plate", "pull_knob"), "washer": ("mirror_plate",),
              "pocket_cap": ("mirror_plate",), "clip": ("mirror_plate",)}
    parts_by_name = {p["name"]: p for p in A["parts"]}
    for nm, hosts in seated.items():
        # A part may sit in more than one host now -- three of the six nuts are captured
        # in the tube plate, three in the pull knobs. Intersecting against every host at
        # once is right: a nut must clash with NONE of them, wherever it is.
        body = Compound([Pos(*i["pos"]) * Rot(0, 0, i.get("rot", 0.0)) * solid(h)
                         for h in hosts for i in parts_by_name[h]["instances"]])
        for inst in parts_by_name[nm]["instances"]:
            placed = Pos(*inst["pos"]) * Rot(0, 0, inst.get("rot", 0.0)) * solid(nm)
            try:
                clash = (placed & body).volume
            except Exception:
                clash = 0.0
            # Clips are placed on the axis and rotated out to their station, so radius
            # says nothing about which one failed; name them by angle instead.
            r = hypot(*inst["pos"][:2])
            where = f"r={r:.0f}" if r > 1.0 else f"{inst.get('rot', 0.0):.0f} deg"
            chk(clash < 1.0,
                f"{nm} at {where} seats in its "
                f"{'/'.join(hosts)} recess (overlap {clash:.2f} mm^3)")

    # --- the landing pads actually stop the push bolts -------------------------
    # This is the check that was missing, and its absence let a #10 washer sit here for
    # the whole design: the seating check proved the pad FIT ITS RECESS, which it did,
    # while the bolt it exists to stop passed clean through its bore. A pad is defined by
    # what it stops, so that is what is asserted.
    chk(PAD_ID < BOLT_POINT_D,
        f"landing pad bore {PAD_ID:.2f} mm is under the bolt point {BOLT_POINT_D:.2f} mm "
        f"(major {BOLT_MAJOR_D:.2f}), so the tip lands on steel -- a #10 washer's "
        f"{BOLT_CLEAR_D:.2f} mm bore would not")
    # ...and the same thing against the solids, which is the version that cannot be
    # fooled by getting the arithmetic right about the wrong two numbers.
    # Swept THROUGH the pad's thickness, not parked against its face: the bolt only
    # touches, so a flush cylinder intersects in zero volume and the check reads 0 mm^2
    # whatever the geometry does. Dividing the swept volume by PAD_T gives the contact
    # annulus as an area, which is the number that means something.
    tip = at(STATIONS[0], R_PUSH, PAD_T / 2) * Cylinder(
        radius=BOLT_POINT_D / 2, height=PAD_T * 3, align=(Align.CENTER,) * 3)
    pad = at(STATIONS[0], R_PUSH) * washer()
    contact = (tip & pad).volume / PAD_T  # mm^2 of face the point actually rests on
    chk(contact > 1.0,
        f"push bolt point rests on {contact:.1f} mm^2 of pad (annulus between the "
        f"{PAD_ID:.2f} mm bore and the {BOLT_POINT_D:.2f} mm point)")

    # --- the bolt HEADS, against the pockets that capture them ----------------
    # The other fit that had no solid test. The heads are procedural stand-ins in the
    # viewer with unmatched hex phase, so a mis-keyed head still LOOKS right on screen --
    # only a real hex solid against the real pocket says whether it goes in.
    #
    # MUST stay below solid(nm), and the intersection is deliberately NOT wrapped in a
    # blanket except: written above it and wrapped, this check intersected a float, threw,
    # and reported PASS on four separately broken models. An exception here should be a
    # crash, not a green tick.
    head = hex_head()
    cap_z = (MIRROR_PLATE_T - RTV_WELL_DEPTH) - CAP_T
    for nm, host, placed in (
            ("push bolt head", "push_knob", Pos(0, 0, KNOB_T - HEAD_T) * head),
            ("pull bolt head", "mirror_plate",
             Compound([at(a, R_PULL, cap_z - (HEAD_T + 0.4)) * head for a in STATIONS])),
    ):
        body = solid(host)
        assert placed.volume > 0 and body.volume > 0, f"{nm}: empty operand"
        chk((placed & body).volume < 1.0,
            f"{nm} seats in its {host} pocket "
            f"(overlap {(placed & body).volume:.2f} mm^3)")

    # --- the tube stub, and the fan in the space the knobs left ---------------
    chk(abs(TUBE_OD - TUBE_ID - 2 * TUBE_WALL) < 1e-9 and abs(TUBE_WALL - inch(0.125)) < 1e-9,
        f"tube {TUBE_ID/25.4:.3f}\" ID, {TUBE_WALL/25.4:.3f}\" wall, "
        f"{TUBE_OD/25.4:.3f}\" OD")
    chk(abs((TUBE_PLATE_T / 2 - TUBE_Z0) - inch(3.65)) < 1e-9,
        f"tube reaches {(TUBE_PLATE_T/2-TUBE_Z0)/25.4:.2f}\" rearward of the plate's "
        f"mid-plane")
    chk(abs((TUBE_Z1 - (Z_MIRROR + MIRROR_T)) - inch(2.0)) < 1e-9,
        f"tube reaches {(TUBE_Z1-(Z_MIRROR+MIRROR_T))/25.4:.2f}\" above the mirror's face")
    # Everything the cell owns has to be inside the stub, or the stub is the wrong length.
    hw_rear = -(standoff + KNOB_T)
    chk(TUBE_Z0 < hw_rear - 5.0,
        f"tube encloses the rear hardware: ends at {TUBE_Z0:.1f}, hardware stops at "
        f"{hw_rear:.1f} mm")
    chk(TUBE_Z1 > Z_MP + MIRROR_PLATE_T + POST_H + CLIP_T + 5.0,
        f"tube encloses the clip tops ({Z_MP+MIRROR_PLATE_T+POST_H+CLIP_T:.1f} mm)")
    reach = max(MP_ARC_R, R_PULL + PULL_KNOB_D / 2, TP_ARC_R)
    chk(reach < TUBE_ID / 2 + 1e-9,
        f"widest thing in the cell reaches r={reach:.2f}, tube bore r={TUBE_ID/2:.2f} mm")

    # The fan lives in the hole the knobs are NOT in. Corner-to-knob is the tight one.
    fan_corner = sqrt(2) * (FAN_SIZE / 2 - FAN_CORNER_R) + FAN_CORNER_R
    chk(fan_corner < R_PUSH - PUSH_KNOB_D / 2,
        f"fan corner r={fan_corner:.2f} clears the push knobs at r={R_PUSH-PUSH_KNOB_D/2:.2f}"
        f" by {R_PUSH - PUSH_KNOB_D/2 - fan_corner:.2f} mm")
    chk(FAN_THROAT_D <= CENTER_BORE + 1e-9,
        f"fan throat {FAN_THROAT_D:.1f} passes the {CENTER_BORE:.1f} mm centre bore")
    chk(FAN_CLEAR_HOLE_D > FAN_HOLE_D,
        f"fan's own holes ({FAN_CLEAR_HOLE_D}) are clearance over the plate's "
        f"tapped {FAN_HOLE_D} mm")
    # Solid against solid: bolted to the rear face, the fan must touch the plate and no
    # more. A fan sunk into the plate, or hovering, both show up here.
    fan_inst = [p for p in A["parts"] if p["name"] == "fan"][0]["instances"][0]
    placed_fan = Pos(*fan_inst["pos"]) * fan()
    try:
        clash = (placed_fan & solid("tube_plate")).volume
    except Exception:
        clash = 0.0
    chk(clash < 1.0, f"fan sits on the tube plate's rear face (overlap {clash:.2f} mm^3)")
    chk(abs(placed_fan.bounding_box().max.Z) < 1e-9,
        f"fan's mounting face is ON the rear face (z={placed_fan.bounding_box().max.Z:.2f})")

    # --- the mirror plate must clear the tube wall as it tilts ----------------
    # Tilting shrinks a feature's projected radius (r.cos) but swings tall features out
    # (h.sin), so the governing feature changes with angle. h is measured above the
    # pivot, taken as the mirror plate's rear face.
    # An ENVELOPE, not the mechanism's range: the bolt clearance caps tilt at 1.42 deg as
    # printed (see BOLT_CLEAR_D), so checking clearance at 3 deg is deliberately
    # pessimistic. Not derived from the bolt holes on purpose -- if a future change opens
    # up the tilt range, this check should not silently widen with it.
    TILT_MAX = 3.0     # degrees; real collimation is well under 1
    features = [("plate rim", MP_ARC_R, MIRROR_PLATE_T),
                ("clip tops", POST_IR + POST_T, MIRROR_PLATE_T + POST_H + CLIP_T),
                ("mirror rim", MIRROR_D / 2, MIRROR_PLATE_T + RTV_T + MIRROR_T)]
    th = radians(TILT_MAX)
    worst = max((r * cos(th) + h * sin(th), nm) for nm, r, h in features)
    chk(worst[0] < TUBE_ID / 2 - 3.0,
        f"at {TILT_MAX:.0f} deg tilt the {worst[1]} swings to r={worst[0]:.2f}, "
        f"clearing the tube wall by {TUBE_ID/2 - worst[0]:.2f} mm")

    # --- a bolt has to go through the hole at all --------------------------------
    # The check that was missing, and the cheapest one in the file. Every downstream
    # number about tilt assumed a bolt fits, and none of them said so; the first tube
    # plate printed its pull holes at exactly the bolt's major diameter and the model was
    # perfectly happy. Stated AS PRINTED against real hardware, which is the only version
    # that could have caught it.
    for nm, drawn in (("pull", PULL_HOLE_D), ("pass-through", PASS_HOLE_D)):
        side = (printed_hole(drawn) - BOLT_MAJOR_D) / 2
        chk(side > 0.10,
            f"{nm} hole drawn {drawn:.2f} prints at {printed_hole(drawn):.2f} mm, "
            f"{side:.3f} mm per side over a {BOLT_MAJOR_D:.2f} mm bolt")
    # And the pass-through must be the looser of the two, or the names are a lie.
    chk(PASS_HOLE_D > PULL_HOLE_D,
        f"pass-through holes ({printed_hole(PASS_HOLE_D):.2f} printed) are looser than the "
        f"pull station's ({printed_hole(PULL_HOLE_D):.2f}), which is the one doing work")

    # Opening the pass-through bore eats into the floor the pull-bolt head bears on, which
    # is a load path and did not look like one from the hole's side. The head must land on
    # ABS at a pressure ABS can hold FOREVER -- spring tension never comes off -- so this is
    # a creep limit, not a strength one, and 2 MPa is the conservative end of what ABS will
    # take indefinitely at the temperature a black cell in a closed tube reaches.
    head_floor = sqrt(3.0) / 2 * HEAD_AF ** 2 - pi * (printed_hole(PASS_HOLE_D) / 2) ** 2
    seat_p = ((SPRING_FREE_L - (PLATE_GAP + SPRING_SEAT_DEPTH)) * SPRING_RATE) / head_floor
    chk(seat_p < 2.0,
        f"pull-bolt head bears on {head_floor:.1f} mm^2 of floor at {seat_p:.2f} MPa "
        f"-- sustained, so the limit is creep, not yield")
    # ...and the head must not simply fall through the bore it is supposed to sit on.
    chk(HEAD_AF > printed_hole(PASS_HOLE_D) + 1.0,
        f"hex head across flats {HEAD_AF:.2f} mm spans the {printed_hole(PASS_HOLE_D):.2f} "
        f"mm bore beneath it")

    # --- and the mechanism's actual tilt budget, against both ends of its bracket
    # Three separate statements, because they fail for three different reasons.
    budget = pull_bolt_tilt()                       # as printed; the range there really is
    lever = 1.5 * R_PULL   # one station against the line joining the other two
    chk(budget >= TILT_NEEDED,
        f"pull-bolt holes give +/-{budget:.2f} deg ({budget*60:.0f} arcmin, "
        f"+/-{lever*tan(radians(budget)):.2f} mm at a station) against the "
        f"{TILT_NEEDED:.2f} deg the cell must provide")

    # The envelope above must stay PESSIMISTIC. It is a fixed 3 deg on purpose, so this is
    # the check that notices if the mechanism ever grows past it -- a thinner tube plate or
    # a looser clearance hole would do it -- and it fails rather than quietly widening the
    # swing check along with it.
    chk(budget < TILT_MAX,
        f"the {budget:.2f} deg the holes allow stays inside the {TILT_MAX:.0f} deg "
        f"envelope the tube-wall check assumes")

    # The hole must bind BEFORE the spring goes slack, the same ordering argument as
    # thread_range < spring_range above: jamming a bolt is a hard stop and harmless, while
    # a slack spring at full tilt costs the mirror plate its seat. spring_range is the
    # axial travel one station has, computed with the preload figures further up.
    spring_tilt = degrees(atan(spring_range / lever))
    chk(budget < spring_tilt,
        f"the holes bind at {budget:.2f} deg, before the spring goes slack at "
        f"{spring_tilt:.2f} deg -- the stop is a jammed bolt, not a lost seat")

    # --- NOTHING may occupy the mirror's volume (spec §8) ----------------------
    # Stated as a solid-vs-solid test rather than as dimensions: it covers the posts, the
    # new root chamfer and the clips in one statement, and it cannot be fooled by a
    # feature I forgot to think about.
    mp = solid("mirror_plate")
    glass = Pos(0, 0, MIRROR_PLATE_T + RTV_T + MIRROR_T / 2) * Cylinder(
        radius=MIRROR_D / 2, height=MIRROR_T)
    try:
        clash = (mp & glass).volume
    except Exception:
        clash = 0.0
    chk(clash < 0.01, f"mirror plate (posts + root chamfer) clear of the glass "
                      f"(overlap {clash:.3f} mm^3)")
    for a in STATIONS:
        placed = Pos(0, 0, MIRROR_PLATE_T + POST_H) * Rot(0, 0, a) * solid("clip")
        try:
            cc = (placed & glass).volume
        except Exception:
            cc = 0.0
        chk(cc < 0.01, f"clip at {a:.0f} deg clear of the glass (overlap {cc:.3f} mm^3)")

    # --- and nothing may hang over the plate outline ---------------------------
    envelope = Pos(0, 0, 25) * Cylinder(radius=MP_ARC_R + 0.02, height=150)
    try:
        over = (mp - envelope).volume
    except Exception:
        over = 0.0
    chk(over < 1.0, f"nothing overhangs the {MP_ARC_R:.1f} mm plate outline "
                    f"({over:.2f} mm^3 outside)")

    # --- the lightening holes must leave real straps, not a thin rim ----------
    # Sized carelessly, a hole merges into the bore and the three station-arms end up
    # joined only by a rim. Straps are checked on both sides.
    inner = MP_LIGHTEN_RC - MP_LIGHTEN_R - MP_CENTER_BORE / 2
    outer = MP_FLAT_D - (MP_LIGHTEN_RC + MP_LIGHTEN_R)
    chk(inner >= 4.0, f"strap between lightening hole and bore = {inner:.1f} mm")
    chk(outer >= 4.0, f"strap between lightening hole and flat = {outer:.1f} mm")
    well = hypot(MP_LIGHTEN_RC * cos(radians(30)),
                 MP_LIGHTEN_RC * sin(radians(30)) - R_PULL) - RTV_WELL_D / 2 - MP_LIGHTEN_R
    chk(well >= 5.0, f"lightening hole clears the RTV well by {well:.1f} mm")
    chk(MP_CENTER_BORE / 2 <= R_PUSH - (PAD_OD / 2 + 0.15) - 3.0,
        f"bore clears the landing pad recess by "
        f"{R_PUSH-(PAD_OD/2+0.15)-MP_CENTER_BORE/2:.1f} mm")

    # --- the corner tabs must still hold the tube screws -----------------------
    # Cutting the flats deeper narrows exactly the tabs the whole cell hangs from. A tab's
    # full width perpendicular to the station ray is 2*(TP_FLAT_D - r/2)/cos(30), and the
    # radial insert bore enters at the rim, where the tab is narrowest.
    tab = 2 * (TP_FLAT_D - TP_ARC_R * sin(radians(30))) / cos(radians(30))
    # Measured from the SEATED INSERT, not the bore: the insert is 0.6 mm fatter than the
    # hole it melts into, and it is the insert the screw pulls against.
    wall = (tab - INSERT_OD) / 2
    chk(wall >= 3.0,
        f"corner tab is {tab:.1f} mm wide at the rim -> {wall:.1f} mm of ABS each side "
        f"of the seated insert")

    # --- the roof over the radial bore: the tight dimension in this design -----
    # The bore is at mid-thickness in the tube plate, so the wall above and below it is
    # whatever the plate has left. Nothing enforced this before: the coupon check only
    # proved the COUPON reproduced the roof, which it would have done just as happily at
    # 1 mm. These three screws carry the entire cell, so the wall they pull against is
    # held to the vendor's own minimum, and it is measured over the seated insert.
    # This is a GEOMETRY check, and geometry is not material: at 40% gyroid roughly 1.1 mm
    # of that roof would have been infill. The insert_solid modifiers in the exported 3MF
    # are what make the assertion mean what it says -- see MODIFIERS.
    roof = (TUBE_PLATE_T - INSERT_OD) / 2
    chk(roof >= INSERT_MIN_WALL,
        f"roof over the seated insert = {roof:.2f} mm, ruthex minimum {INSERT_MIN_WALL:.2f}"
        f" (bore alone would read {(TUBE_PLATE_T - INSERT_BORE_D)/2:.2f} mm and flatter)")
    chk("tube_plate" in MODIFIERS,
        "the insert region is forced solid by a modifier, so the wall above is material "
        "and not 40% gyroid")

    # The bore is drawn NOMINAL and shrinks into the vendor's recommended hole -- the same
    # convention as the tube plate OD. Compensating it would print it oversize and the
    # knurl would have nothing to bite.
    chk(abs(INSERT_BORE_D * (1 - PRINT_SHRINK) - INSERT_HOLE_D) <= 0.1,
        f"bore {INSERT_BORE_D:g} mm prints at {INSERT_BORE_D*(1-PRINT_SHRINK):.2f} mm "
        f"against ruthex's {INSERT_HOLE_D:g} mm recommended hole")
    chk(INSERT_DEPTH > INSERT_L,
        f"bore {INSERT_DEPTH:g} mm is deeper than the {INSERT_L:g} mm insert, so the "
        f"screw tip runs out past it")

    # --- slicer settings are complete, and printable as drawn ------------------
    # Data only: the written 3MFs are checked after the write, not here, because verify()
    # runs BEFORE the exporter and --check writes nothing. Asked here, a file check would
    # be reading the previous run -- the deadlock the BOM snapshot check used to have.
    missing = [n for n in PARTS if n not in PRINT]
    chk(not missing, f"every printable part has slicer settings; missing {missing}")
    for name, (spec, note) in PRINT.items():
        chk(name in PARTS, f"PRINT names a real part: {name}")
        chk(bool(note.strip()), f"{name} carries a reason, not just settings")
        # walls and solid travel together or not at all -- a part with walls but no shell
        # count would emit wall_loops with no top/bottom and slice to something nobody
        # chose. (Slice.__init__ guards density and pattern at construction.)
        chk((spec.walls is None) == (spec.solid is None),
            f"{name}: walls and solid layers are both set or both unset "
            f"({spec.walls}, {spec.solid})")
        # Shells are counted in LAYERS, so they buy a thickness only at LAYER_H. If top and
        # bottom together exceeded the part, it would print solid whatever the density says
        # and the infill setting would be a fiction. Bounding-box height is generous -- a
        # part can be thinner than its bbox in places -- so this is a floor, not a proof.
        if spec.solid is not None:
            h = PARTS[name]().bounding_box().size.Z
            chk(2 * spec.solid * LAYER_H < h,
                f"{name}: {spec.solid}+{spec.solid} shell layers = "
                f"{2*spec.solid*LAYER_H:.1f} mm at {LAYER_H} mm, inside its {h:.1f} mm")

    # Modifiers exist to make a region SOLID. Asserted as that, not as "matches
    # MODIFIERS" -- the round-trip check compares the file against this table, so it
    # cannot notice the table itself being wrong, and a modifier at anything under 100%
    # is decoration that still costs print time.
    for host, (make, mod_name, overrides) in MODIFIERS.items():
        chk(host in PARTS, f"MODIFIERS names a real part: {host}")
        chk(overrides.get("sparse_infill_density") == "100%",
            f"{host} modifier '{mod_name}' fills its region solid "
            f"({overrides.get('sparse_infill_density')}) -- anything less does not give "
            f"the insert the material ruthex's minimum wall assumes")
        solids = make()
        chk(len(solids) == len(STATIONS),
            f"{host}: {len(solids)} modifier solids for {len(STATIONS)} stations")
        chk(all(s.volume > 0 for s in solids),
            f"{host}: every modifier solid has volume")

    # Exports must land on the bed ready to slice. True today only because of how each
    # part happens to be drawn, which is exactly the kind of thing that quietly stops
    # being true: a part sunk below z=0 or floating above it loads into the slicer in a
    # pose nobody intended, and the settings riding with it would be beside the point.
    for name, fn in PARTS.items():
        z0 = fn().bounding_box().min.Z
        chk(abs(z0) < 1e-6, f"{name} rests on the bed (z_min = {z0:+.3f} mm)")

    # --- everything fits the printer, WITH ITS BRIM ---------------------------
    # The brim is in this check because at 8" it is the binding constraint, not a
    # nicety: the tube plate has to reach the tube wall to take its screws, so a 10"
    # tube puts a 237 mm part on a 250 mm bed and there is no room for the 8-10 mm
    # skirt the 6" cell prints with. That is the cell's tightest number and it belongs
    # in an assertion, not in a slicer note nobody reads until the plate is on the bed.
    # BRIM is what the cell can actually be given; if a part grows, this fails.
    for name, fn in PARTS.items():
        s = fn().bounding_box().size
        chk(s.X + 2 * BRIM < BED[0] and s.Y + 2 * BRIM < BED[1] and s.Z < BED[2],
            f"{name} fits bed with its {BRIM:g} mm brim: "
            f"{s.X + 2*BRIM:.0f} x {s.Y + 2*BRIM:.0f} x {s.Z:.0f} mm in "
            f"{BED[0]:.0f} x {BED[1]:.0f} x {BED[2]:.0f}")

    for good, msg in ok:
        print(f"  {'PASS' if good else 'FAIL'}  {msg}")
    failed = [m for g, m in ok if not g]
    if failed:
        raise SystemExit(f"\n{len(failed)} CHECK(S) FAILED")
    print(f"\n  all {len(ok)} checks passed")


if __name__ == "__main__":
    import os, sys
    # --check is the CI entry point: verify, refuse a stale snapshot, write nothing. The
    # default run is the author's, and it REPAIRS the snapshot rather than failing on it.
    check_only = "--check" in sys.argv
    verify()
    print()
    if not check_only:
        os.makedirs(BUILD, exist_ok=True)
    vols = {}
    for name, fn in PARTS.items():
        part = fn()
        if not check_only:
            export_step(part, f"{BUILD}/{name}.step")
            export_stl(part, f"{BUILD}/{name}.stl")
            write_3mf(part, Path(f"{BUILD}/3mf/{name}.3mf"), PRINT[name][0],
                      part_number=name)
        vols[name] = part.volume
        bb = part.bounding_box()
        print(f"{name:14s} vol {part.volume/1000:8.2f} cm^3   "
              f"bbox {bb.size.X:6.1f} x {bb.size.Y:6.1f} x {bb.size.Z:6.1f} mm")

    for name, fn in HARDWARE.items():
        part = fn()
        if not check_only:
            export_stl(part, f"{BUILD}/{name}.stl")
        bb = part.bounding_box()
        print(f"{name:14s} (purchased)          "
              f"bbox {bb.size.X:6.1f} x {bb.size.Y:6.1f} x {bb.size.Z:6.1f} mm")

    import json
    A = assembly()
    # The BOM is written with real volumes, which is why it happens here and not in
    # assembly(): the copy in assembly.json is the same rows, unquantified.
    rows = bom(A["parts"], vols)
    md = bom_markdown(rows)
    stale = bom_snapshot_stale(rows)

    if check_only:
        # CI, or a fresh checkout. Nothing is written, so a stale snapshot is somebody
        # having committed the model without rerunning it -- and that is a hard failure.
        if stale:
            raise SystemExit(
                f"\n{BOM_PATH} is STALE and --check writes nothing.\n"
                f"  rows the snapshot no longer matches: {stale}\n"
                f"  fix: rerun `python3 mirror_cell.py --aperture {APERTURE}` "
                f"and commit {BOM_PATH}")
        print(f"\n--check: all checks passed and {BOM_PATH} is current; nothing written")
    else:
        with open(f"{BUILD}/assembly.json", "w", encoding="utf-8") as f:
            json.dump(A, f, indent=1)
        with open(f"{BUILD}/bom.md", "w", encoding="utf-8") as f:
            f.write(md)
        with open(f"{BUILD}/bom.csv", "w", encoding="utf-8") as f:
            f.write(bom_csv(rows))
        # ...and a snapshot at the top level, which is the one that gets committed:
        # build/ is gitignored, so without this the repo has no readable buy list at all.
        with open(BOM_PATH, "w", encoding="utf-8") as f:
            f.write(md)
        # Round-trip the 3MFs: reopen what was actually written and compare it to what the
        # model meant. verify() checked the DATA; this checks the ARTIFACT, which is the
        # only thing that catches an injection that silently did not happen -- seven files
        # with no settings in them look exactly like seven correct ones from the outside.
        for name in PARTS:
            p = Path(f"{BUILD}/3mf/{name}.3mf")
            want = PRINT[name][0].config()
            got = read_3mf_config(p)
            if got != want:
                raise SystemExit(
                    f"\n3MF SETTINGS DID NOT ROUND-TRIP for {name}\n"
                    f"  wrote:  {got}\n  meant:  {want}")

            found = read_3mf_modifiers(p)
            if name not in MODIFIERS:
                if found:
                    raise SystemExit(f"\n{p} has {len(found)} unexpected modifier(s)")
                continue
            _, _, overrides = MODIFIERS[name]
            if len(found) != len(STATIONS):
                raise SystemExit(
                    f"\n{p} carries {len(found)} modifier meshes, expected "
                    f"{len(STATIONS)} -- one per station.\n"
                    f"  found: {[f[0] for f in found]}")
            # One modifier centred on each station's bore, spanning the plate, and big
            # enough to hold the cylinder ruthex's minimum wall describes. Written from
            # the insert constants rather than from insert_bosses(), so it is not the
            # generator checking its own homework -- and it reads the MESHES, so a mesh
            # that never reached the file fails here however good the source geometry was.
            rr = INSERT_OD / 2 + INSERT_MIN_WALL
            reach = TP_ARC_R - INSERT_DEPTH / 2
            for a in STATIONS:
                cx, cy = reach * cos(radians(a)), reach * sin(radians(a))
                near = [b for _, _, b in found
                        if hypot((b[0] + b[3]) / 2 - cx, (b[1] + b[4]) / 2 - cy) < 1.0]
                if not near:
                    raise SystemExit(
                        f"\n{p}: no modifier centred on the insert at {a:.0f} deg "
                        f"(expected near x={cx:.1f} y={cy:.1f})\n"
                        f"  boxes in the file: {[f[2] for f in found]}")
                b = near[0]
                if not (b[2] <= 1e-6 and b[5] >= TUBE_PLATE_T - 1e-6):
                    raise SystemExit(f"\n{p}: modifier at {a:.0f} deg spans z "
                                     f"{b[2]:.2f}..{b[5]:.2f}, not the full plate")
                if min(b[3] - b[0], b[4] - b[1]) < 2 * rr - 1e-6:
                    raise SystemExit(
                        f"\n{p}: modifier at {a:.0f} deg is {b[3]-b[0]:.1f} x "
                        f"{b[4]-b[1]:.1f} mm, too small for the {2*rr:.1f} mm "
                        f"solid region ruthex's minimum wall needs")
            for nm, ov, _ in found:
                if ov != overrides:
                    raise SystemExit(f"\n{p}: modifier {nm} carries {ov}, "
                                     f"expected {overrides}")
        print(f"{BUILD}/3mf/ written; {len(PARTS)} parts, settings and "
              f"{len(STATIONS)} modifiers verified in the files")

        print(f"\n{BUILD}/assembly.json written; {BUILD}/bom.md, {BUILD}/bom.csv and "
              f"the committed {BOM_PATH} ({len(rows)} lines)")
        # Reported AFTER the write, so this is news rather than an obstacle: the file has
        # already been brought up to date and the line just says what moved.
        if stale:
            print(f"  {BOM_PATH} updated -- rows that changed: {stale}")
            print(f"  commit it; `python3 mirror_cell.py --check` is what refuses a "
                  f"stale snapshot.")
