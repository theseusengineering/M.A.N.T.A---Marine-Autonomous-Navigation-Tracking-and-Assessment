# Engineering notes — Demo tracking casing

**Casing created:** 2026-09-22

## 2026-09-22 — Camera casing v1

### What I made and why

I started by importing a 3D model of the ESP32 board that I found online, then modelled the casing around it with a small hole for the USB port. The ESP32 board model in the project's reference assets is the [Seeed Studio XIAO ESP32S3 Sense STEP](../Reference%20Assets/Seeed%20Studio%20XIAO%20ESP32S3%20Sense%203D%20Model/Seeed%20Studio%20XIAO-ESP32-S3-Sense.step). The casing is shown in the [isometric view](camera%20casing%20v1/camera%20casing%20v1%20Iso.png) and [front view](camera%20casing%20v1/camera%20casing%20v1%20Front.png). It is about 25 × 29 × 26 mm.

### What I observed

It worked first try.

## Date not confirmed — Streamlined trailing edge (Camera House Test v3)

### What I made and why

This is the fluid dynamics version. I took the profile we've been using and added it to the trailing edge of the camera housing I had already modelled, so that water can flow over it better. The [top view](Camera%20House%20Test%20v3/Camera%20House%20Test%20v3%20Top.png) shows the casing at the front with the tapered profile behind it. The [front view](Camera%20House%20Test%20v3/Camera%20House%20Test%20v3%20Front.png) shows it from the front. With the profile added, the part is about 116 mm long.

### Assumptions and uncertainties

**Unverified:** I expect the profile to improve flow over the housing, but I haven't measured or tested that here.

## Date not confirmed — Telescoping stanchion and rope winder

### What I made and why

Next I modelled a retracting mechanism. It uses a telescoping section ([Telescope 2 v2](Telescope%202%20v2/Telescope%202%20v2%20Iso.png)) that lowers the camera, and a winder that winds the rope. The winder is made up of the [top winder housing](Top%20winder%20housing/Top%20winder%20housing%20Iso.png), the [pin winder](Pin%20winder/Pin%20winder%20Iso.png) and a [24-tooth spur gear](Spur%20Gear%2024%20teeth%20(1)/Spur%20Gear%2024%20teeth%20(1)%20Iso.png). The full assembly is [camera stantion v3](camera%20stantion%20v3/camera%20stantion%20v3%20Iso.png), with a [side view](camera%20stantion%20v3/camera%20stantion%20v3%20Side.png). These parts were exported on 2026-09-29, and the stanchion's `.3mf` on 2026-09-30.

I modelled the telescope sections straight, so I had to build in mechanical stops to limit how far they extend.

### What I observed

The telescoping mechanism for dropping the camera works very well.

The rope winder ended up being a non-starter. It works in one direction while there is tension on the rope. As soon as a current or some other force pushes upwards on the telescope, it collapses. That leaves me no way to control the camera height in that degree of freedom.

**Not specified:** the test conditions, such as whether this was tested in water, on the bench or in the CAD model.

### What I learned

The height mechanism needs to be incompressible, so that it can resist upward forces as well as hold the camera down under tension.

### Next steps

- Make the next version of the telescope tapered instead of straight. The contour itself should then limit the extension, so it won't need the mechanical stops I modelled into this version.
- Find an incompressible mechanism to control the camera height in place of the rope winder.
