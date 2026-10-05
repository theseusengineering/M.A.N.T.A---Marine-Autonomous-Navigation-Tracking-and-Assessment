# Engineering notes — Rigid retractable chainstay (Djangear) v1

**Model created:** 2026-10-05 (v1 printing at 70% scale)

## 2026-10-05 — Hinged rack and pinion, first print

### What I made and why

We needed a way to control the height of the retractable camera housing, similar to the rope on the [demo tracking casing](../Demo%20tracking%20Casing/engineering_notes.md), but incompressible. That is a difficult engineering challenge because rope is compressible. Something that is rigid in the vertical direction, which is what we want, is hard to make flexible laterally or rotationally, and we need it to bend so we can store it.

Django came up with the conceptual idea: take a straight gear and add hinges on the back of it. I then designed and CAD-modelled everything. It works as a rack and pinion system: a regular spur gear drives a straight spur gear (the rack). Segmenting the rack lets us add a hinge on each segment, so the straight gear can bend once it is past the driving gear. The [assembly view](Django%20Hinged%20Gear%20System%20v1/Django%20Hinged%20Gear%20System%20v1%20Iso.png) shows the segmented rack, the spur gear on its pin, and the [guide](guide%20v2/guide%20v2%20Iso.png).

The parts:

- **Hinge** ([hinge iso v1](hinge%20iso%20v1/hinge%20iso%20v1%20Iso.png)): this is a very complicated design that prints in place without supports. It took several tries in Fusion, trying out collision systems, simulating joints, and so on. The exported model is a combined body, so its renders only show the outside of the three hinge segments. A single segment exported on its own ([isometric view](hinge%20half%20iso%20v1%20(for%20photos)/hinge%20half%20iso%20v1%20(for%20photos)%20Iso.png), [back view](hinge%20half%20iso%20v1%20(for%20photos)/hinge%20half%20iso%20v1%20(for%20photos)%20Iso%20Back.png), [side view](hinge%20half%20iso%20v1%20(for%20photos)/hinge%20half%20iso%20v1%20(for%20photos)%20Side.png)) shows more of the mechanism. One end has a pair of knuckles with cone-shaped pins pointing into the gap between them, and the other end has a single knuckle with a hole through it. Each segment is about 10 × 76 × 30 mm.
- **Lengthwise split:** to print everything without supports, I split each segment lengthwise to isolate the hinge from the gear side, so that both have a flat face. The [gear flats](individual%203%20piece%20gear%20flats%20v1/individual%203%20piece%20gear%20flats%20v1%20Iso.png) are about 36.3 mm wide and the hinge about 10.0 mm, which together make up the 46.3 mm width of the [rack master](rack%20master%20v1/rack%20master%20v1%20Iso.png).
- **Aligner** ([aligner v1](aligner%20v1/aligner%20v1%20Iso.png)): aligns the two halves.
- **Pin** ([pin v1](pin%20v1/pin%20v1%20Iso.png)): holds the gear.
- **Guide v2** ([guide v2](guide%20v2/guide%20v2%20Iso.png)): changed so it prints without supports. The pin was originally fixed to the back of the guide; I made them two separate parts that snap into place.

Everything was modelled with about 0.3 mm of tolerance.

### Designing for CNC

I made most minimum radii and holes about 4–5 mm, because I plan to manufacture the hinges and gears out of metal on the CNC machine, and the smallest bit is 3.175 mm. The cutter needs to be able to get into those radii.

Assuming 3.175 mm is the bit diameter, the smallest internal corner radius it can cut is 3.175 ÷ 2 ≈ 1.59 mm, and the smallest hole it can cut is 3.175 mm across. The 4–5 mm minimums are above both.

I think the hinges themselves are too small to make on the CNC machine. The gear side is definitely fine to CNC because of the large radii, and that is the part that will see the most wear.

### Assumptions and uncertainties

- **Untested:** whether the print-in-place hinge works. That is what the 70% print is checking.
- **Scaled tolerance:** if the 70% scale is applied to the whole model in the slicer, the 0.3 mm clearance shrinks to about 0.21 mm (0.3 × 0.7). That could affect whether the hinge frees up, and it differs from the clearance in a full-size print.
- **Not specified:** how the hinge parts would be made if they are too small to CNC.

### Next tests

- Check whether the print-in-place hinge works on the 70% print.
