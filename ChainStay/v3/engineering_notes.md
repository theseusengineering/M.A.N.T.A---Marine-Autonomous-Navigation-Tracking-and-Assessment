# Engineering notes — ChainStay v3.1

**Model created:** 2026-09-19

## 2026-09-19 — Solid link with mechanical back plate

### What I made and why

Compared with v2, I removed the small motion-limiting knobs and replaced them with a full mechanical back plate. I also made the centre of the link solid instead of leaving a hollow route for a cable. I originally used a cable-chain design because it is an established way to limit movement and protect cables, but I do not actually need to route a data cable through this chain. Keeping the outer chain mechanism while making the link solid should make it stronger and easier to print. This is still a prototype.

The [single-link isometric views](Assets/Single%20Link%20Iso.png) and [side view](Assets/Single%20Link%20Side.png) show the solid centre and the broad plate around the hinge area. The [two-link view](Assets/Duallink%20Iso.png) shows how neighbouring links fit together. This version needs neither the custom supports from earlier links nor regular printing supports.

### Assumptions and uncertainties

After a few movements, the rounded knobs on the earlier printed links developed play. The straight limit could then move about 1–2° past the intended 0°. I think the rounded shape contributed to that wear. The new flat back plate gives a broader mechanical stop, which I expect to leave less room for wear and make the straight limit more repeatable. That still needs testing over repeated cycles. A shifting stop would make it harder to know where the camera is in 3D space and link its images to position accurately.

I may use a more rigid material later. I also think the solid link might make water-flow modelling more predictable, but I have not modelled or tested its flow behaviour yet.

### What I observed

I used the same kind of CAD motion study as for v2. The [motion-study views](Assets/Motionstudy%20Top.png) and [second angle](Assets/Motionstudy%20Bottom.png) show the movement limited by the new plate, with a maximum bend of about 36°. The first batch has finished printing and worked as expected. It has been easier to print without supports, but I still have many batches to make for a full chain. **Not yet verified:** the long-term wear and repeatability of the 0° stop on the printed v3.1 links.

### Next tests and build quantity

I am aiming for about 1.2 m of chain to be housed in each hull. Each link contributes roughly 1 cm of chain length, suggesting about 120 links per hull (120 cm ÷ 1 cm per link), before allowing for the actual assembled pitch and end connections. I had roughly suggested 200 links earlier, but the required count still needs to be checked against the assembled chain and hull stowage space. I also need to test how well the back plate holds its limit after repeated movement and assess the water-flow behaviour before treating either improvement as confirmed.
