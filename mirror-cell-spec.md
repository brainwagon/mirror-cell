# 6" Mirror Cell — Design Spec

*Derived from a grilling session, 2026-07-28. This is a **one-off** design for one specific
telescope: the 6" Newtonian originally built in the 1970s, being rebuilt with a 3D-printed
cell. It is deliberately **not** parametric across apertures — see §9.*

Terminology is defined in [CONTEXT.md](./CONTEXT.md) and used strictly here.

---

## 1. The telescope this is for

| | |
|---|---|
| Mirror | 6.000" dia × 1.000" thick, 44" focal length (**f/7.33**), **2.3 lb** |
| Tube | Sonotube, 7.750" OD / **7.500" ID** |
| Related | `~/dob` (mount designer), `~/dob-6-project` (this scope's DXFs), `~/blip` (the FEA that settled the support radius) |

The mount project `~/dob` explicitly scopes out the mirror cell — its part inventory has no
cell at all. This project fills that hole.

## 2. Scope

**In scope**, all five jobs of a cell: axial support, lateral support, retention,
collimation, and the tube interface.

**Out of scope:** optical design (settled — 44" f/7.33); the mount (that's `~/dob`); any
aperture other than 6". A 3-point cell is only valid to roughly 8–10"; larger mirrors need
6- or 9-point flotation, which is a different part family.

## 3. Architecture

Two plates and three Stations.

- **Tube plate** — fixed to the sonotube, carries the collimation hardware, never touches
  the mirror.
- **Mirror plate** — floats on the collimation hardware, carries the mirror.
- **Station** — one of three positions at 90°/210°/330°. Each carries a Push bolt, a Pull
  bolt, a Support point, a Centering post and a Side clip, **all on one ray from the axis.**

Collimation is **push-pull with springs on the pull bolts** — the springs give compliance
while adjusting, the push bolts lock. This follows
[Stellafane](https://stellafane.org/tm/dob/ota/cell2.html) and matches the existing cell.

## 4. Geometry

**Radii.** Push bolts at **r = 1.500"**. Pull bolts at **r = 2.250" (0.75R)**. The three
Support points are **coaxial with the pull bolts** — see [ADR-0001](./docs/adr/0001-support-points-coaxial-with-pull-bolts.md).

**Axial stack**, measured from the Tube plate's rear face:

```
0.0000  tube plate rear face   ← wing nuts and knobs live here
0.5000  tube plate front face
        ── 0.600" nominal spring gap ──
1.1000  mirror plate rear face  ← landing pads here
1.4750  mirror plate front face ← RTV wells here
1.5375  mirror back             (0.0625" bond)
2.5375  mirror front
2.5675  clip underside          (0.030" air gap)
```

The 0.600" gap is a **nominal, not a fixed dimension** — the wing nuts set the real value.
The spring must neither coil-bind at minimum gap nor go slack at maximum.

## 5. Parts

### Tube plate
7.500" OD triangle with three arc corners, flats at **60 mm** from the axis,
**0.500" thick**.

The flats are cut deep — 205 cm³ against 313 cm³ for a lightly-trimmed triangle, a **35%
saving on the largest part in the design**. That is safe because **the load path never
crosses a flat**: the collimation bolts sit on the station rays at r = 1.500" and 2.250",
and the tube screws are on those *same* rays at the arc corners, so the mirror's weight
travels radially outward along each arm. Material between stations carries torsion only,
and at ½" thick against ~2 lb per Station there is enormous margin. It also opens the back
of the cell further for mirror cooldown (§3) and leaves less large flat area to warp.

**The binding constraint is the corner tabs, not stiffness.** Those tabs carry the three
radial insert bores from which the entire cell hangs; a tab is
`2·(TP_FLAT_D − R/2)/cos 30°` wide at the rim, so cutting past ~53 mm eats into the bores.
At 60 mm the tab is 28.6 mm wide, leaving 11 mm of ABS each side.

- **Draw the OD at nominal 7.500"** and let ABS shrinkage supply the clearance. This is
  empirically confirmed by a test-fitted print, not calculated. **Do not pre-compensate
  any tube-referenced dimension** — mixing nominal and compensated conventions in one part
  is how this gets ruined.
- Center bore **1.500"** (changed from the prototype's 1.622" — see below), plus four M3
  holes on a 32 mm square: a **40 mm fan option, left unpopulated**. These cost nothing
  now and cannot be added later without pulling the mirror and reprinting.

  > **Changed from the prototype.** A 40 mm fan's screws sit on a 32 mm square, i.e. at
  > r = 22.63". Against a 1.622" bore that leaves a **0.43 mm web** — not a printable
  > feature. 1.500" restores a 1.98 mm web while still passing nearly the fan's full
  > 38 mm throat. Caught by the model's checks, not by inspection.
- Three **radial** 6.5 mm heat-set insert bores at mid-thickness, at the Stations.
- Push-bolt **hex nut pockets at r = 1.500", opening forward** (see §6).
- Pull-bolt clearance holes at r = 2.250", with spring seats on the front face.
- The prototype's six 0.5" edge scallops are **dropped**.

### Mirror plate
Triangle with three arc corners at **88.0 mm** radius, **0.375" thick**.

The outline is set by what it must contain, not by the tube. It has to hold the posts
(outer face at 84.96 mm) **plus the room their root chamfer needs outboard** — 3.04 mm of
margin. It was briefly trimmed to 86.0 to save material; that saved 1.7% and capped the
chamfer at 1.04 mm on the face that needs it most, so it went back to 88.0. Cheap plastic,
expensive stress riser.

Against a 95.25 mm tube-wall radius that is **6.9 mm of clearance at 3° of tilt**, and the
governing feature changes with angle: below ~5° the plate rim dominates, above it the clip
tops do, because tilt trades `r·cosθ` against `h·sinθ`.

- Pull-bolt **hex pockets at r = 2.250", opening forward, capped** (see below).
- **RTV wells** (22 mm dia) around each pocket to meter glue volume.
- **Landing-pad recesses** for #10 washers on the rear face at r = 1.500".
- Centre bore **56 mm** — its *own* parameter, not the tube plate's. The tube plate's bore
  is set by the 40 mm fan screw circle; this one is limited by the landing pads (recess
  inner edge at 31.6 mm) and wants to be as open as possible so fan air actually reaches
  the back of the glass. Coupling the two would tie together constraints that have nothing
  to do with each other.
- Three **lightening holes** (r = 12.5 mm) at the mid-angles, between Stations.
- Three **Centering posts**, inner face at r = 3.030", 8 mm thick, each with an **M3
  heat-set insert** in its top face for a clip.
- A **1.5 mm × 45° chamfer round each post root.** The post is a cantilever wall and its
  root is a stress riser; worse, printed flat the root's tension is carried across
  **layer interfaces**, the weak direction in FDM. The critical face is the **outer** one:
  an upward load on a clip tips the post inward, putting the root's outer fibres in
  tension.

  Size is capped on both sides — outboard by the plate edge (3.04 mm of room at
  `MP_ARC_R` = 88.0), inboard by the mirror's 1.588 mm bond gap. **Inboard now binds:**
  the chamfer rises `c − 0.762` mm at the mirror rim, so 1.5 mm leaves 0.85 mm of air
  under the glass. It is built as a **loft**, not a tapered extrude — OCC's tapered prism
  fails on this profile above about 1 mm.

**Lightening the mirror plate works differently.** The tube-plate trick — cutting the
flats deeper — does *not* transfer: the posts span ±16° and reach r = 86.5, so they
already occupy the angles the flats would bite into, leaving only 2.7 mm of room in the
outline. The free material is in the middle and at the mid-angles instead, and taking it
gives **13.8%** (192.7 → 166.0 cc).

This is safe for the same reason as the tube plate, only more so: [ADR-0001](./docs/adr/0001-support-points-coaxial-with-pull-bolts.md)
made each silicone dab **coaxial with its pull bolt**, so the mirror's weight goes straight
into the bolt with *zero span*, and the push bolts are on the same rays. Between Stations
the plate only has to keep the three coplanar.

**The trap is sizing the holes so they merge into the bore.** At r = 18 on a 42 mm circle
the hole meets a 56 mm bore, the plate is cut clear through at every mid-angle, and the
three arms end up joined only by a 5 mm rim. It computes as a 20.9% saving and is
structurally worthless. Straps are held at **6 mm on both sides** and checked.

### Side clips (×3, separate parts)
**The clips cannot be integral, and this is a correctness constraint, not a preference.**
A clip reaching in to r = 71.2 mm leaves a 142.4 mm opening; the mirror is 152.4 mm. With
clips printed onto the posts the mirror could never be installed at all — it is 10 mm too
big to pass, in every direction, with only 2.35 mm of vertical slack under the clips
against a 25.4 mm blank, so it cannot be tilted in either.

Being separate also fixes a printing problem: integral, a clip is a 5.76 mm horizontal
overhang 37 mm up in the air, and the surface that would droop or need support is its
**underside — the 0.030" air gap**, one of the three gaps that must never close. Printed
flat as its own part, that face is a clean bed-facing surface.

Each clip bolts to a post top with a single **M3 cap screw**. Fitted after the mirror is
glued and cured.

### Pocket caps (×3, separate parts)
The pull bolt goes in from the **front** face, so its hex pocket must open forward — into
the same face the silicone dab sits on, since the dab is coaxial with the bolt
([ADR-0001](./docs/adr/0001-support-points-coaxial-with-pull-bolts.md)). That leaves a
hole in the middle of the RTV well. Without a cap the dab is laid over open air: silicone
runs down into the hex, the bond loses volume, its thickness stops being what the shims
say, and the bolt head is bonded in.

The cap is an **11.5 mm × 1.5 mm printed disc** dropped into a 12 mm counterbore, flush
with the well floor. It carries ~30% of the dab area, about **0.16 lb** per Station.

**It is deliberately not a precision fit.** The disc is 0.5 mm under its bore so it always
drops in, it overlaps its ledge by 1.02 mm so it cannot fall through onto the bolt head,
and it is **bedded in a spot of the same RTV** used for the dabs — which is already in
hand at that point in the sequence. An earlier version used a 10 mm bore, which left only
**0.27 mm of ledge at the hex corners**; in a material that shrinks 0.6–0.8% that part
either jams or drops through. Nothing about this cap should need dialling in.

### Printed shims (×3, separate parts)
0.0625" thick. Set the RTV bond thickness during cure, then pulled out. Replaces the
toothpicks used previously — same thickness, now repeatable.

### Collimation knobs (×3)
Printed, capturing a hex bolt head in a **hex pocket** — a form fit, not friction, so the
knob cannot slip on the bolt.

## 6. Why the nut pockets open forward

Work out the load direction. A Push bolt threaded in the Tube plate shoves the Mirror
plate forward, so its reaction drives the nut **rearward** — the nut needs plastic behind
it, so its pocket opens *forward*, into the gap. The same is true of anything threaded
into the Mirror plate.

This is why the Pull bolt is **reversed**: a hex head captured in the Mirror plate, shank
rearward through the spring, **wing nut on the outside**. Tension then loads a flat pocket
floor in **pure compression** — the one loading ABS handles without creeping — and nothing
that can loosen is trapped under the mirror.

**Every steel-to-plastic interface in this design is in compression.** That is not
incidental; ABS creeps under sustained tension, and a cell that creeps loses collimation
slowly, invisibly, over weeks. The Landing pads exist for the same reason: a bolt tip
bearing directly on ABS would emboss a dimple and walk the collimation.

## 7. Hardware

| Qty | Item |
|---|---|
| 6 | 10-24 **hex-head** bolts, **all 2"** — one type *and* one length throughout |
| 3 | 10-24 wing nuts — **McMaster 90866A011**, zinc-plated steel, 0.875" span × 0.500" tall |
| 3 | 10-24 hex nuts (captured, push bolts) |
| 3 | #10 flat washers, 0.5" OD (Landing pads) |
| 3 | Compression springs — **0.9 mm wire × 9 mm OD × 20 mm free length, ≈ 13 lb/in** |
| 3 | #10 screws + **1" fender washers** (tube mount) |
| 3 | 10-24 heat-set inserts, 6.5 mm bore (tube mount) |
| 3 | **M3 heat-set inserts, 4.0 mm bore** (post tops, for the clips) |
| 3 | **M3 cap screws**, ~10 mm (clips) |
| — | Black ABS; RTV silicone |

**Springs — do not buy a "telescope collimation spring kit."** Those are sized for cells
with no push bolts, where springs alone hold collimation; a typical ScopeStuff-style
primary spring computes to **~152 lb/in**, over ten times what this wants, and you would
never turn the wing nuts. Buy by **geometry**, not by rate — listings publish wire
diameter and OD but rarely rate, and rate follows from `k = Gd⁴/8D³n`. Wire diameter
dominates (fourth power): a common assortment kit at 1.4 mm wire computes to ~57 lb/in,
still far too stiff.

At the 0.600" gap, 13 lb/in gives **1.9 lb preload per Station, 5.7 lb total** against
~2.6 lb of mirror and plate — seated in any tube orientation, still finger-turnable.

**Fender washers** matter. Statically the three tube screws see ~70 psi against cardboard
that's good for over 1000. The load case is **transport**: a 10 g knock puts ~700 psi on
the hole edge, cardboard crushes, holes go oval, and collimation is gone every time you
move the scope. A 1" fender washer spreads that ~15× and makes it a non-issue.

## 8. The three gaps that must never close

| Gap | Value | Guards against |
|---|---|---|
| Centering post → mirror edge | **0.030" radial** | Cold-night pinch |
| Clip → mirror front face | **0.030" axial** | Contact stress → astigmatism |
| RTV bond thickness | **0.0625"** | Mirror bottoming onto plastic |

ABS moves ~90 ppm/°C against glass at 3–9. Cooling from a 22 °C room to a −8 °C night
contracts the plate ~0.016" on diameter while the glass barely moves — **~0.007" of radial
squeeze**. Posts fitted snugly at room temperature would grip the mirror on exactly the
coldest, best-seeing nights.

The model states this as a **solid-vs-solid test**, not as dimensions: the mirror's
volume is intersected with the mirror plate and with each clip, and both must be empty.
That covers the posts, the root chamfer and the clips in one statement, and cannot be
fooled by a feature nobody thought to measure.

These gaps are printed, specified and non-adjustable. **Closing one is a defect, not a
tighter assembly.** The failure they prevent is invisible: a pinched or bottomed mirror
looks correct, passes daylight inspection, and only shows as astigmatism on nights good
enough to notice — by which point it is glued down.

Bond thickness was checked rather than assumed. Differential contraction shears the dab,
and force on the glass scales as 1/thickness: 1.5 lb per dab at 0.125", **3.0 lb at
0.0625"**, 6.2 lb at 0.030". RTV takes >100% shear strain elastically, so 9.4% is nowhere
near a limit, and the load is *in-plane* — the least harmful direction. Thinner is
simultaneously better for axial sag and collimation retention, which is why 0.0625" wins
over the 0.125" first proposed.

## 9. Assembly notes

- **Drill the tube in situ**, using the Tube plate's own insert bores as the drill guide,
  with the plate held at the depth that reaches focus. The Tube plate's axial position is
  what sets mirror-to-focuser distance; nothing else constrains it.
- Install the push-bolt nuts **before** the Mirror plate goes on. Once a bolt is threaded
  in, its nut is captive permanently.
- **Order matters at the mirror: posts, then glass, then clips.** Drop the mirror in past
  the Centering posts (1.52 mm of slip), shim it, let the RTV cure, pull the shims, and
  only then bolt the Side clips on. There is no way to fit the mirror with clips in place.
- Hex pocket clearances **must be dialled on an ABS test coupon** before printing either
  plate — ABS shrinks 0.6–0.8% and nominal dimensions will not fit.
- Collimate by backing off the push bolts, setting tilt with the wing nuts, then snugging
  the push bolts. The cell is deliberately *soft* while adjusting and stiff once locked.

## 10. Open items

- ~~Mirror plate thickness~~ — **resolved at 0.375"**. The model checks the stack: RTV
  well 1.0 + cap 1.5 + hex pocket 3.575 leaves a **3.45 mm floor** for the pull bolt head
  to bear on. This is also why there is **no spring seat on the mirror plate's rear face**
  — cutting one would have left 0.95 mm of ABS under that floor. The spring is located by
  its tube-plate seat and the bolt shank, and bears on the flat face.
- ~~Center bore~~ — **resolved at 1.500"**, see §5.
- **Hex pocket clearance (`FIT`, currently 0.25 mm) — still needs an ABS test coupon.**
  This is the one number the model cannot check for you.
- ~~Exact bolt lengths~~ — **resolved: all six are 1¾".** Push bolts were 1½", which put
  the Collimation knobs into the wing nuts: they overlap **5.45 mm radially** (knob reaches
  r=53.1, wing nut reaches r=47.6, and both sit on the same Station ray), so they must
  clear *axially* instead. Against the **measured** McMaster 90866A011 the radial overlap
  is 7.06 mm, and 2" bolts give **10.16 mm** of axial clearance while also letting the pull
  bolt reach fully through the wing nut (3.14 mm proud) — and every bolt in the cell is
  identical.

  The wing nut envelope is measured from the vendor STEP file (kept in the repo), not from
  catalogue figures; my first estimates, 19.0 × 11.0 mm, were both undersized. **A wing nut
  turns, so its wings can point anywhere** — clearance is checked in the worst case, wings
  radial.
- Knob and plate outline shapes — aesthetic, provisional.
- No fan is specified or bought; only the mounting holes exist.

## 11. Load-bearing decisions, and what would overturn them

- **All steel-to-plastic interfaces in compression** (§6). If a future revision introduces
  a fastener in sustained tension against ABS, the creep argument is broken and
  collimation stability is no longer predicted.
- **Support radius chosen mechanically, not optically** ([ADR-0001](./docs/adr/0001-support-points-coaxial-with-pull-bolts.md)).
  Valid only because the mirror is full-thickness. **Tripwire:** a thin or larger blank
  makes support placement matter again, and this design should not be reused for one.
- **Nominal-dimension convention against the tube** (§5), confirmed by a real test fit —
  not by calculation. Re-verify if the filament or printer changes.
