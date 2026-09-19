# Context: Mirror Cell

A 3-point primary mirror cell for a 6" Newtonian, 3D printed, assembled with 10-24
hardware (the six collimation bolts can be 1/4-20 instead — see ADR-0004 — but the three
tube-mount inserts are 10-24 in every build). Lives in the telescope built by `~/dob` /
`~/dob-6-project` (7.75" OD sonotube).

This file is a glossary. It holds terms, not dimensions, decisions, or construction
details.

## Glossary

### Tube plate
The fixed plate. Attaches to the sonotube and does not move relative to it. Carries the
collimation hardware. Does not touch the mirror.

Not "back plate" — that name has been used for both plates and is banned here.

### Mirror plate
The floating plate. Carries the mirror on its front face and rides on the collimation
hardware. Its position and tilt relative to the Tube plate is what collimation adjusts.

### Support point
One of the three locations where the Mirror plate bears the weight of the mirror. Three
of them, 120° apart, all at the same radius from the optical axis. Distinct from the
collimation bolts, which are at a different (larger) radius — the two sets of three
points are not the same three points and must never be conflated.

### Silicone dab
The compliant bond at a Support point: a blob of RTV between the Mirror plate and the
back of the mirror. It is simultaneously the axial support, the lateral restraint, and
the primary retention. Its compliance is functional, not incidental — it decouples the
glass from the much larger thermal expansion of the printed plate.

### Push bolt
A collimation bolt bearing against the Mirror plate, pushing it away from the Tube plate.
Snugged after adjustment; this is what locks collimation.

### Pull bolt
A collimation bolt drawing the Mirror plate toward the Tube plate, with a spring in
compression between the plates. The spring provides the compliance that makes adjustment
continuous; the Pull bolt sets the working point.

### Side clip
A retainer overhanging the front edge of the mirror. Drop-insurance only — in normal
operation it carries no load, because the Silicone dabs do. Not to be described as
"lateral support".

### Station
One of the three angular positions, 120° apart, at which the cell does all of its work.
A single Station comprises a Push bolt and its Push knob, a Pull bolt and its Pull knob,
a Support point, a Centering post and a Side clip. Saying "the three stations" is preferred to enumerating the hardware,
because everything at a Station shares one ray from the optical axis.

### Centering post
An upstand at a Station that locates the mirror concentric with the Mirror plate during
glue-up. It is a locating feature, never a clamping one: it stands off the glass by a
deliberate clearance so that differential thermal contraction can never let it grip.
Carries the Side clip.

### Landing pad
The steel washer let into the Mirror plate where a Push bolt bears on it. Exists so that
no steel fastener ever contacts plastic at a point — the load is spread over a face, and
the contact is steel-on-steel.

### Push knob
The printed knob at the user-facing end of a Push bolt. Captures the bolt's hex head in a
hex pocket — a form fit, not friction — and carries torque only, never axial load.

### Pull knob
The printed knob at the user-facing end of a Pull bolt, which is also its nut: it captures
a plain hex nut in a hex pocket, and the nut stands slightly proud of the printed face so
that steel, never ABS, bears on the Tube plate. Replaced a wing nut.

Not "Collimation knob" — that name meant only the push-side knob and there are two knobs
now, so it is banned here alongside "back plate".

## Standing rule: clearance is a feature

Three separate places in this design deliberately do *not* touch the glass — the Side
clips, the Centering posts, and (via the Silicone dabs) the Mirror plate itself. In each
case the gap is specified, printed, and non-adjustable. A gap here is never slop to be
taken up during assembly; closing one is a defect, because a pinched mirror is an
astigmatic mirror. The printed part expands and contracts roughly ten times as much as
the glass does, so every gap must survive the coldest night you will ever observe on.
