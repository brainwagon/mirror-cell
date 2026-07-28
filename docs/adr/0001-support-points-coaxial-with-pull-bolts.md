# Support points are coaxial with the pull bolts at 0.75R, not at the PLOP optimum

PLOP-style optimisation puts the three support points of a 3-point cell near **0.40R**,
and the classical Grubb/Stellafane result puts them at **0.707R**; we have placed them at
**0.75R**, directly over the pull bolts, and chose that on mechanical rather than optical
grounds. The justification is `~/blip`, our own FEA of this exact mirror, which found that
for a full-thickness 6" blank the difference between these placements is **under 1/40 wave
— supporting at the extreme edge is still only 1/30 wave**, i.e. optically undetectable at
the eyepiece. With optics thus indifferent, the load path decides: putting the support
points on the same ray *and the same radius* as the pull bolts means the mirror's weight
travels mirror → silicone dab → boss → bolt → tube plate with **no bending moment in the
mirror plate at all**, which matters enormously for a printed ABS part, where bending is
the weak direction and the place creep shows up.

## Consequences

- The mirror plate can be a light three-armed triangle instead of a stiff disk — less
  plastic, shorter print, better airflow behind the mirror for cooldown.
- 0.75R is close enough to the classical 0.707R that the cell will not look strange to
  another ATM.
- **This reasoning does not transfer.** It holds only because the blank is full-thickness
  and small. For a thin or larger mirror the deflection is no longer negligible, support
  placement matters again, and this cell should not be reused as a starting point — that
  is recorded as a tripwire in the spec.
- The decision is effectively irreversible: moving the support points means unglueing a
  mirror bonded with RTV.
