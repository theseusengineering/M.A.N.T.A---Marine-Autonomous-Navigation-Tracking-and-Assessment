# Engineering notes — Bike chain retraction (concept)

**Concept recorded:** 2026-10-06 (10:43, first project lesson of the week; nothing modelled or built yet)

## 2026-10-06 — Bike chain as the incompressible retraction member

### The idea and why

We just came up with an idea for an improved version of the incompressible retraction system. We're going to use a bike chain, because that's already modelled and we can just use a sprocket.

The issue with a bike chain on its own: if it were freestanding inside the telescoping keel system that houses the camera, it has a degree of freedom in the lateral direction — into the boat, down the aft side. But if we run it inside a central tube within the telescoping system, which can itself telescope on the inside, then it's limited in that direction too. It is then effectively incompressible.

### Why this beats the hinged gear for retraction length

The payoff is on the storage side. Once the chain is out of that limiting inner tube, we actually *want* it to bend in multiple directions. With the original [Django gear design](../Rigid%20Retractable%20Chainstay%20(Djangear)/engineering_notes.md), each hinge bends in one direction only, so it can only loop around once — that gives around 2 m of retraction length (**unverified estimate**). A bike chain can bend both ways, so we can loop it over and over. It's incredibly small, machined precisely, and all the tolerance is already built in. We could probably get around 15–20 m (**unverified estimate**).

This matters because the earlier [rope winder](../Demo%20tracking%20Casing/engineering_notes.md) collapsed under upward force — the retraction member has to be incompressible regardless of which design we pick.

### Assumptions and uncertainties

- **Main open question — wall thickness of the inner telescoping stanchions.** Because the chain keeps its lateral degree of freedom, the inner tube is what constrains it. The telescoping sections need a significant taper angle to limit movement, and I wonder whether, by the 15 m mark, the taper leaves enough wiggle room for sufficient wall thickness and stability in the sub-inner telescoping mechanism.
- **Not yet verified:** the ~2 m single-loop figure for the Django system and the 15–20 m figure for looped chain are both estimates, not measured or modelled.

### Fallback

If we can't make the inner telescoping tube work, there is a way to loop the Django system turning in only one direction. That would probably take up more space, but if the inner telescope isn't possible I don't know of any other option, since incompressibility is required regardless.

## 2026-10-06 — Follow-up: spiral wind, so the Djangear after all

### The decision

The multi-loop storage is possible with the [Djangear](../Rigid%20Retractable%20Chainstay%20(Djangear)/engineering_notes.md) by doing the top starting wind: if we wind in a spiral rather than a snaking wind, it only needs to bend in one direction, which is exactly what the hinges allow.

And we have to use the Djangear, because the inner telescoping mount is too much at 15 metres of taper to actually limit the movement of the bike chain. That answers the main open question from this morning's entry: the taper doesn't leave enough to constrain the chain, so the plain bike chain route is out.

### For the final product

I wonder whether we could instead use a modified bike chain that limits bend to one direction — the chain's small size and machined precision with the Djangear's one-way hinge behaviour. **Idea only; no modification designed or tested.**
