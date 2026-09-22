# Engineering notes — ChainStay v1

**Model created:** 2026-09-18

## 2026-09-18 — Single-finned chain link and motion study

### What I made and why

I modelled a chain stay so we could lower the camera closer to the reef and take colour measurements at different depths. The idea is to relate those measurements to depth and extrapolate to the depth of the coral. At the same time, I want to limit twisting and unwanted bending or angle changes, because a camera trailing behind the craft at depth could skew its position relative to the craft's GPS reading.

I based the link on the familiar cable-chain protector design. That design is already used to protect cables and constrain where they can move; I am not claiming the basic chain concept as novel. For this version, I wanted it to bend in only one direction so it can be coiled without folding back and trailing behind the craft. This was a more deliberate design than the initial hull and centre-connector model.

### Geometry and motion

The [isometric front view](v1%20Assets/Iso%20Front.png) and [side view](v1%20Assets/Side.png) show the raised fin, side hinge plates and the open space through the link. Adjacent links join with printed snap features: the tapered geometry lets a link slide gradually over the pin and then lock once it has passed it. I added small limiting nubs so the chain cannot bend past straight in the unwanted direction. The nubs are the features that actually make contact at the straight limit.

I added a fin to the top of each link with the aim of reducing drag in water. I also intended it as a backup limit on extension, although the nubs are the primary straight stop. The [front view](v1%20Assets/Front.png) shows the fin's peaked profile. The structures below the link in the [isometric back view](v1%20Assets/Iso%20back.png) are custom printing supports, modelled to use less material and be easier to remove.

### Assumptions and uncertainties

The fin's effect on drag, the ability of the chain to keep the camera aligned under water, and the usefulness of colour measurements at different depths have not yet been tested. The CAD model shows the intended one-direction motion, but physical snap fit, strength, support removal and motion remain unverified while the first print is underway.

### What I observed

I have only done a CAD motion study so far. The [minimum-bend view](v1%20Assets/Minimum%20Bend%20from%20Motion%20Study.png) shows the straight limit at 0°, where the nubs make contact. I wanted the chain to bend more than 30° per joint, with 30° as the minimum acceptable range. The [maximum-bend view](v1%20Assets/Maximum%20Bend%20from%20Motion%20Study.png) shows an observed CAD limit of 39°. As of 2026-09-18, the first print is in progress and there are no physical test observations yet.

### Next tests

Suggested checks once the print finishes: whether the custom supports remove cleanly, the snap features assemble and hold, and the physical joint reaches the intended one-way motion and bend range. Later water testing could check the drag and camera-positioning assumptions.
