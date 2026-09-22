# Engineering notes — P.O.C. Quick Draft v1

**Model created:** 2026-09-15

## 2026-09-15 — Initial proof of concept

### What I made and why

I made a simple first model to bring to the second project class and show the idea. It was a rough visual proof of concept, not yet a prototype. I used my previous knowledge of general boat hull shapes. There were no formal design calculations, the model was not parametric, and I had not considered materials for the final craft.

As shown in the [isometric view](v1%20Assets/Iso%20View.png) and [side view](v1%20Assets/Side%20View.png), I modelled the centre structure to sit slightly above the expected water level between the two hulls to reduce drag, then dip down in the middle to hold the camera mount. I used a sharp angle there so I could print it without supports. I designed the [camera mount](v1%20Assets/Camera%20Mount%20v1.png) around the general shape of a GoPro. I scaled the whole design to 25% so it would print faster and I would not have to bring a large model to class.

### Assumptions and uncertainties

I made a lot of assumptions about size and buoyancy. The intended full size load, the waterline, and the drag reduction from raising the centre structure had not been calculated or verified. The camera mount was based on the general GoPro shape; its fit has not been confirmed.

### What I observed

After printing the 25% model, I coated it in waterproof epoxy. I put it in a sheet pan of water and added weights to see when it sank. It sank after I added about 750 g of weight. **Not specified:** the model's own mass and how much of it was submerged before that point.

Using the cube rule for volume, I estimated that 750 g of added weight at 25% scale corresponds to about 48 kg of added load at full scale (0.75 kg × 4³). Even with a safety factor of four, I thought that was more than enough for this rough proof of concept. **Unverified estimate:** this extrapolation assumes the full size craft has the same proportions and comparable floating behaviour; the pan test does not establish its actual payload capacity.

### Next tests

Refine the design, then test it with CFD and physical fluid tests. Check the full size buoyancy and load capacity rather than relying on the small model estimate.
