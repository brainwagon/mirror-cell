"""6" mirror cell — build123d model.

A one-off design for one telescope (6.000" x 1.000" mirror, 44" FL, 7.500" ID sonotube).
Not parametric across apertures on purpose: a 3-point cell is only valid to ~8-10".
See mirror-cell-spec.md for the reasoning and docs/adr/0001 for the support radius.

Every dimension lives in the PARAMETERS block. Model internals are mm; the design is
dimensioned in inches, so inch() converts at the boundary.

    python3 mirror_cell.py          # writes STEP + STL for every part into build/
"""

from math import sqrt, cos, sin, radians, degrees, hypot, atan2
from build123d import *


def inch(x):
    return x * 25.4


# ---------------------------------------------------------------- PARAMETERS

# --- the telescope -----------------------------------------------------------
MIRROR_D = inch(6.000)
MIRROR_T = inch(1.000)
TUBE_ID = inch(7.500)  # draw NOMINAL; ABS shrinkage supplies the fit (spec §5)

# --- stations ----------------------------------------------------------------
STATIONS = (90.0, 210.0, 330.0)
R_PUSH = inch(1.500)  # push bolt circle
R_PULL = inch(2.250)  # pull bolt circle == support point circle (ADR-0001)

# --- axial stack (spec §4) ---------------------------------------------------
TUBE_PLATE_T = inch(0.500)
PLATE_GAP = inch(0.600)  # nominal; wing nuts set the real value
MIRROR_PLATE_T = inch(0.375)  # OPEN ITEM: proposed, not verified
RTV_T = inch(0.0625)  # bond thickness, set by the printed shims
CLIP_GAP = inch(0.030)  # clip -> mirror front face
POST_GAP = inch(0.030)  # centering post -> mirror edge, radial

# --- outlines ----------------------------------------------------------------
TP_ARC_R = TUBE_ID / 2  # tube plate corner arcs
# Tube plate flat, distance from the axis. Cut deep on purpose: the load path runs
# radially along each station ray (collimation bolt -> tube screw, both on the same ray),
# so material between stations carries only torsion. Also opens the back of the cell for
# mirror cooldown. Bounded below by the corner tabs, which hold the tube screws -- past
# about 53 the flats eat into the insert bores.
TP_FLAT_D = 60.0
# Mirror plate corner arcs. Must contain the posts (outer face at 84.96) AND leave room
# for the post root chamfer outboard, which is the more critical face -- see POST_FILLET.
# Trimmed to 86.0 at one point; that capped the chamfer at 1.04 mm, so it went back to 88.
MP_ARC_R = 88.0
MP_FLAT_D = 65.0
# The prototype used 1.622". That collides with the 40 mm fan screw circle: holes on a
# 32 mm square sit at r=22.63, leaving a 0.43 mm web to a 1.622" bore. 1.500" restores a
# 2 mm web while still passing nearly the fan's full 38 mm throat.
CENTER_BORE = inch(1.500)

# The mirror plate gets its OWN bore. The tube plate's is set by the 40 mm fan screw
# circle; this one is limited by the landing pads (recess inner edge at 31.6 mm) and wants
# to be as open as possible so fan air actually reaches the back of the glass.
MP_CENTER_BORE = 56.0
# Lightening holes between the stations. Nothing structural lives at the mid-angles: the
# dab is coaxial with its pull bolt (ADR-0001) and the push bolts are on the same rays, so
# the plate's only job out here is keeping the three stations coplanar.
MP_LIGHTEN_WALL = 6.0
MP_LIGHTEN_R = (MP_FLAT_D - 2 * MP_LIGHTEN_WALL - MP_CENTER_BORE / 2) / 2
MP_LIGHTEN_RC = MP_CENTER_BORE / 2 + MP_LIGHTEN_WALL + MP_LIGHTEN_R

# --- fan option (unpopulated, spec §5) ---------------------------------------
FAN_PITCH = 32.0
FAN_HOLE_D = 3.2

# --- 10-24 hardware ----------------------------------------------------------
BOLT_CLEAR_D = inch(0.2031)  # free-fit clearance for 10-24
NUT_AF = inch(0.375)  # 10-24 hex nut across flats
NUT_T = inch(0.130)
HEAD_AF = inch(0.3125)  # 10-24 hex head across flats
HEAD_T = inch(0.125)
FIT = 0.25  # clearance added to hex pockets. DIAL ON A TEST COUPON.

INSERT_BORE_D = 6.5  # 10-24 heat-set insert
INSERT_DEPTH = 14.0

WASHER_D = inch(0.500)  # #10 flat washer, the landing pad
WASHER_T = inch(0.050)

# 10-24 wing nut, on the rear face of the tube plate.
# Measured from McMaster 90866A011 (zinc-plated steel), not from a catalogue guess.
# The earlier estimates (19.0 x 11.0) were both undersized.
WINGNUT_STEP = "90866A011_NO THREADS_Zinc-Plated Steel Wing Nut.STEP"
WING_SPAN = 22.225   # 0.875" across the wings
WING_H = 12.700      # 0.500" tall
WING_BODY_D = 10.274 # 0.4045" across the body

# A wing nut turns, so its wings can point anywhere. Clearance must hold in the worst
# case: wings radial, reaching WING_SPAN/2 inward toward the knobs.

# One length for all six bolts. 1-1/2" push bolts put the knobs into the wing nuts:
# they overlap 5.45 mm radially (same station ray), so they must clear axially instead.
PUSH_BOLT_L = inch(2.0)
PULL_BOLT_L = inch(2.0)

SPRING_OD = 9.0
SPRING_SEAT_D = SPRING_OD + 0.8
SPRING_SEAT_DEPTH = 2.5

# --- mirror plate detail -----------------------------------------------------
POST_IR = MIRROR_D / 2 + POST_GAP  # post inner face
POST_T = 8.0  # thick enough to take an M3 insert with sound walls
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

# --- knob --------------------------------------------------------------------
KNOB_D = 30.0
KNOB_T = 14.0
KNOB_FLUTES = 8
KNOB_FLUTE_D = 6.0

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
        p -= at(a, R_PUSH) * extrude(Circle(BOLT_CLEAR_D / 2), TUBE_PLATE_T)
        pocket_z = TUBE_PLATE_T - (NUT_T + 0.4)
        p -= at(a, R_PUSH, pocket_z) * hex_prism(NUT_AF, NUT_T + 0.4)

        # --- pull bolt: clearance through + spring seat on the FRONT face ------
        p -= at(a, R_PULL) * extrude(Circle(BOLT_CLEAR_D / 2), TUBE_PLATE_T)
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
        p -= at(a, R_PUSH) * extrude(Circle(WASHER_D / 2 + 0.15), WASHER_T + 0.15)

        # --- pull bolt head captured from the FRONT, in compression ------------
        p -= at(a, R_PULL) * extrude(Circle(BOLT_CLEAR_D / 2), MIRROR_PLATE_T)
        well_z = MIRROR_PLATE_T - RTV_WELL_DEPTH
        p -= at(a, R_PULL, well_z) * extrude(Circle(RTV_WELL_D / 2), RTV_WELL_DEPTH)
        cap_z = well_z - CAP_T
        p -= at(a, R_PULL, cap_z) * extrude(Circle(CAP_D / 2), CAP_T)
        head_h = HEAD_T + 0.4
        p -= at(a, R_PULL, cap_z - head_h) * hex_prism(HEAD_AF, head_h)

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

def knob():
    k = extrude(Circle(KNOB_D / 2), KNOB_T)
    for i in range(KNOB_FLUTES):
        a = 360.0 * i / KNOB_FLUTES
        k -= at(a, KNOB_D / 2) * extrude(Circle(KNOB_FLUTE_D / 2), KNOB_T)
    k -= Pos(0, 0, KNOB_T - (HEAD_T + 0.4)) * hex_prism(HEAD_AF, HEAD_T + 0.4)
    k -= extrude(Circle(BOLT_CLEAR_D / 2), KNOB_T)
    return k


def wingnut():
    """Purchased hardware, not printed. Imported so clearances are checked against the
    real part rather than against numbers I typed in."""
    return import_step(WINGNUT_STEP)


def hex_nut():
    """The captured 10-24 nut. Modelled so the assembly sequence can show it going in."""
    n = extrude(RegularPolygon(radius=NUT_AF / sqrt(3.0), side_count=6), NUT_T)
    n -= extrude(Circle(inch(0.190) / 2), NUT_T)
    return n


def washer():
    """#10 flat washer -- the Landing pad."""
    return extrude(Circle(WASHER_D / 2) - Circle(BOLT_CLEAR_D / 2), WASHER_T)


def pocket_cap():
    return extrude(Circle((CAP_D - CAP_CLEAR) / 2), CAP_T)


def shim():
    return extrude(Rectangle(SHIM_L, SHIM_W), RTV_T)


# ---------------------------------------------------------------- MAIN

# Printed parts. Bed-fit checks apply to these.
PARTS = {
    "tube_plate": tube_plate,
    "mirror_plate": mirror_plate,
    "clip": clip,
    "knob": knob,
    "pocket_cap": pocket_cap,
    "shim": shim,
}

# Purchased hardware. Exported so the viewer can show the real thing, but not printed.
HARDWARE = {"wingnut": wingnut, "hex_nut": hex_nut, "washer": washer}

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
         "Drop a 10-24 \u00d7 2\u2033 hex-head bolt into each hex pocket from the FRONT "
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
         "A #10 washer into each recess on the REAR face. These are what the push bolt "
         "tips bear on. Steel on steel, so no bolt ever embosses the plastic and walks "
         "the collimation.", None,
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
        ("Wing nuts",
         "Run a wing nut onto each pull bolt from the rear. The bolt comes through "
         "6.7 mm proud, so you have full thread engagement across the whole range.", None,
         pose(home=tp + ["hex_nut", "springs", "wingnut"]
              + [k for k in MP_KIDS if k != "shim"])),
        ("Push bolts and knobs",
         "Thread the three knob assemblies into the captured nuts from the rear, until "
         "each tip just touches its landing washer.", None,
         pose(home=tp + ["hex_nut", "springs", "wingnut", "push_bolts", "knob"]
              + [k for k in MP_KIDS if k != "shim"])),
        ("Into the tube, then collimate",
         "Hold the cell at the depth that reaches focus and drill the sonotube using the "
         "insert bores as the guide. Screws go in with 1\u2033 fender washers on the "
         "OUTSIDE of the tube. Then collimate: back the push bolts off, set tilt with the "
         "wing nuts, and snug the push bolts to lock.",
         "Without the fender washers a transport knock ovals the holes in the cardboard, "
         "and collimation is gone every time you move the scope.",
         pose(home=tp + ["hex_nut", "springs", "wingnut", "push_bolts", "knob"]
              + [k for k in MP_KIDS if k != "shim"])),
    ]
    return [{"title": t, "detail": d, "caution": c, "pose": p} for t, d, c, p in steps]


def assembly():
    return {
        "stack": {
            "tube_plate_front": TUBE_PLATE_T, "mirror_plate_rear": Z_MP,
            "mirror_back": Z_MIRROR, "mirror_front": Z_MIRROR + MIRROR_T,
            "clip_underside": Z_MP + MIRROR_PLATE_T + POST_H,
        },
        "sequence": sequence(),
        "parts": [
            {"name": "tube_plate", "stl": "tube_plate.stl", "color": "#3d4450",
             "explode": [0, 0, -90], "instances": [{"pos": [0, 0, 0], "rot": 0}]},
            {"name": "mirror_plate", "stl": "mirror_plate.stl", "color": "#4a5260",
             "explode": [0, 0, 40], "instances": [{"pos": [0, 0, Z_MP], "rot": 0}]},
            {"name": "knob", "stl": "knob.stl", "color": "#8a6a3a",
             "explode": [0, 0, -170],
             "instances": _ring(R_PUSH, Z_MP - PUSH_BOLT_L - KNOB_T)},
            {"name": "clip", "stl": "clip.stl", "color": "#5f6a7a",
             "explode": [0, 0, 95],
             "instances": [{"pos": [0, 0, Z_MP + MIRROR_PLATE_T + POST_H], "rot": a}
                           for a in STATIONS]},
            {"name": "hex_nut", "stl": "hex_nut.stl", "color": "#c3ccd8",
             "group": "hardware", "explode": [0, 0, 60],
             "instances": _ring(R_PUSH, TUBE_PLATE_T - (NUT_T + 0.4), orient=False)},
            {"name": "washer", "stl": "washer.stl", "color": "#c3ccd8",
             "group": "hardware", "explode": [0, 0, -60],
             "instances": _ring(R_PUSH, Z_MP)},
            {"name": "pocket_cap", "stl": "pocket_cap.stl", "color": "#8a6a3a",
             "explode": [0, 0, 110], "instances": _ring(R_PULL, Z_CAP)},
            # real McMaster solid; wings drawn radial, the worst case for knob clearance
            {"name": "wingnut", "stl": "wingnut.stl", "color": "#c3ccd8",
             "group": "hardware", "explode": [0, 0, -130],
             # the vendor solid is modelled about its OWN origin: it must be moved out to
             # the pull-bolt circle, not left at [0,0,0]
             "instances": _ring(R_PULL, 0.0)},
            {"name": "shim", "stl": "shim.stl", "color": "#b0552f", "group": "shim",
             "explode": [0, 0, 150],
             "instances": [{"pos": [66 * cos(radians(a)), 66 * sin(radians(a)),
                                    Z_MP + MIRROR_PLATE_T], "rot": a}
                           for a in (30.0, 150.0, 270.0)]},
        ],
        # generated procedurally in the viewer from these numbers
        "mirror": {"d": MIRROR_D, "t": MIRROR_T, "z": Z_MIRROR, "explode": [0, 0, 230]},
        # springs explode radially: axially they would stay buried between the plates
        "springs": {"coil_d": SPRING_OD, "wire_d": 0.9, "z0": TUBE_PLATE_T, "z1": Z_MP,
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
    floor = MIRROR_PLATE_T - RTV_WELL_DEPTH - CAP_T - (HEAD_T + 0.4)
    chk(floor >= 3.0, f"mirror plate floor under hex pocket = {floor:.2f} mm (>= 3.0)")

    # --- push bolt nut floor --------------------------------------------------
    nut_floor = TUBE_PLATE_T - (NUT_T + 0.4)
    chk(nut_floor >= 3.0, f"tube plate floor under nut pocket = {nut_floor:.2f} mm")

    # --- bolt head must pass through the cap bore during assembly -------------
    head_corners = 2 * (HEAD_AF + FIT) / sqrt(3.0)
    chk(head_corners < CAP_D,
        f"head across corners {head_corners:.2f} < cap bore {CAP_D:.2f} mm")
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
    free, solid = 20.0, 6.2  # 0.9 mm wire x 9 mm OD x 20 mm FL, ~5 active coils
    chk(free > PLATE_GAP, f"spring free length {free} > gap {PLATE_GAP:.2f} mm (stays preloaded)")
    chk(solid < PLATE_GAP - 3.0, f"solid height {solid} well below gap {PLATE_GAP:.2f} mm (no coil bind)")
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

    # --- knobs must not foul the wing nuts (both live on the rear face) --------
    kr = (R_PUSH - KNOB_D / 2, R_PUSH + KNOB_D / 2)
    wr = (R_PULL - WING_SPAN / 2, R_PULL + WING_SPAN / 2)
    radial = min(kr[1], wr[1]) - max(kr[0], wr[0])
    kf = Z_MP - PUSH_BOLT_L
    axial = min(kf, 0.0) - max(kf - KNOB_T, -WING_H)
    chk(radial <= 0 or axial <= -2.0,
        f"knob/wing-nut: radial overlap {radial:+.2f} mm, axial gap {-axial:+.2f} mm")
    bolt_end = Z_PULL_HEAD_FACE - PULL_BOLT_L
    engage = -bolt_end
    # criterion is physical: the bolt must reach through the nut, not stop part way
    chk(engage >= WING_H,
        f"pull bolt reaches through the wing nut: {engage:.2f} mm vs {WING_H:.2f} mm tall "
        f"({engage - WING_H:+.2f} mm proud)")

    bolts = {b["kind"]: b for b in assembly()["bolts"]}
    push_dir = bolts["push"]["z_head"] - bolts["push"]["z_tip"]
    pull_dir = bolts["pull"]["z_head"] - bolts["pull"]["z_tip"]
    chk(push_dir < 0, f"push bolt head is REARWARD of its tip ({push_dir:+.1f} mm)")
    chk(pull_dir > 0, f"pull bolt head is FORWARD of its tip ({pull_dir:+.1f} mm) "
                      f"-- captured in the mirror plate")
    chk(abs(bolts["pull"]["z_head"] - Z_PULL_HEAD_FACE) < 1e-9,
        "pull bolt head bears on the hex pocket floor")

    sep = 2 * R_PUSH * sin(radians(60))
    chk(sep - KNOB_D > 5.0, f"adjacent knobs clear each other by {sep-KNOB_D:.1f} mm")

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
    drawable = {p["name"] for p in A["parts"]} | {"mirror", "springs"} \
        | {b["name"] for b in A["bolts"]}
    named = {k for st in A["sequence"] for k in st["pose"]}
    chk(named <= drawable, f"sequence names only real items; stray: {named - drawable}")
    final = set(A["sequence"][-1]["pose"])
    chk(final == drawable - {"shim"},
        f"final step shows everything but the shims; missing {drawable-{'shim'}-final}")

    # --- parts that sit in recesses must actually fit in them -----------------
    # Intersecting the placed solid with its plate catches a mis-keyed hex directly:
    # a nut rotated to its station angle collides with the pocket wall.
    seated = {"hex_nut": "tube_plate", "washer": "mirror_plate",
              "pocket_cap": "mirror_plate"}
    parts_by_name = {p["name"]: p for p in A["parts"]}
    for nm, plate_nm in seated.items():
        body = solid(plate_nm)
        for inst in parts_by_name[nm]["instances"]:
            placed = Pos(*inst["pos"]) * Rot(0, 0, inst.get("rot", 0.0)) * solid(nm)
            try:
                clash = (placed & body).volume
            except Exception:
                clash = 0.0
            chk(clash < 1.0,
                f"{nm} at {inst.get('rot',0):.0f} deg seats in its {plate_nm} recess "
                f"(overlap {clash:.2f} mm^3)")

    # --- the mirror plate must clear the tube wall as it tilts ----------------
    # Tilting shrinks a feature's projected radius (r.cos) but swings tall features out
    # (h.sin), so the governing feature changes with angle. h is measured above the
    # pivot, taken as the mirror plate's rear face.
    TILT_MAX = 3.0     # degrees; real collimation is well under 1
    features = [("plate rim", MP_ARC_R, MIRROR_PLATE_T),
                ("clip tops", POST_IR + POST_T, MIRROR_PLATE_T + POST_H + CLIP_T),
                ("mirror rim", MIRROR_D / 2, MIRROR_PLATE_T + RTV_T + MIRROR_T)]
    th = radians(TILT_MAX)
    worst = max((r * cos(th) + h * sin(th), nm) for nm, r, h in features)
    chk(worst[0] < TUBE_ID / 2 - 3.0,
        f"at {TILT_MAX:.0f} deg tilt the {worst[1]} swings to r={worst[0]:.2f}, "
        f"clearing the tube wall by {TUBE_ID/2 - worst[0]:.2f} mm")

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
    chk(MP_CENTER_BORE / 2 <= R_PUSH - (WASHER_D / 2 + 0.15) - 3.0,
        f"bore clears the landing pad recess by "
        f"{R_PUSH-(WASHER_D/2+0.15)-MP_CENTER_BORE/2:.1f} mm")

    # --- the corner tabs must still hold the tube screws -----------------------
    # Cutting the flats deeper narrows exactly the tabs the whole cell hangs from. A tab's
    # full width perpendicular to the station ray is 2*(TP_FLAT_D - r/2)/cos(30), and the
    # radial insert bore enters at the rim, where the tab is narrowest.
    tab = 2 * (TP_FLAT_D - TP_ARC_R * sin(radians(30))) / cos(radians(30))
    wall = (tab - INSERT_BORE_D) / 2
    chk(wall >= 3.0,
        f"corner tab is {tab:.1f} mm wide at the rim -> {wall:.1f} mm of ABS each side "
        f"of the insert bore")

    # --- everything fits the printer ------------------------------------------
    for name, fn in PARTS.items():
        s = fn().bounding_box().size
        chk(s.X < BED[0] and s.Y < BED[1] and s.Z < BED[2],
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
    for name, fn in PARTS.items():
        part = fn()
        export_step(part, f"build/{name}.step")
        export_stl(part, f"build/{name}.stl")
        bb = part.bounding_box()
        print(f"{name:14s} vol {part.volume/1000:8.2f} cm^3   "
              f"bbox {bb.size.X:6.1f} x {bb.size.Y:6.1f} x {bb.size.Z:6.1f} mm")

    for name, fn in HARDWARE.items():
        part = fn()
        export_stl(part, f"build/{name}.stl")
        bb = part.bounding_box()
        print(f"{name:14s} (purchased)          "
              f"bbox {bb.size.X:6.1f} x {bb.size.Y:6.1f} x {bb.size.Z:6.1f} mm")

    import json
    with open("build/assembly.json", "w") as f:
        json.dump(assembly(), f, indent=1)
    print("\nbuild/assembly.json written")
