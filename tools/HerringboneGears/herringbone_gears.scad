// Herringbone gear + rack, built with BOSL2's gears.scad
// https://github.com/BelfrySCAD/BOSL2/wiki/gears.scad
//
// Open in OpenSCAD and edit values in the Customizer panel
// (Window > Customizer), or edit the numbers below. F5 previews,
// F6 renders, F7 exports an STL of whatever is ticked on.
//
// Meshing: the rack lies along X with its pitch line at Y=0; the gear's
// axis goes at Y = pitch radius (echoed to the console on every render).
// Both parts use the same helix angle; flip the sign on ONE part if the
// V directions clash.

include <BOSL2/std.scad>
include <BOSL2/gears.scad>

/* [Build] */
build_gear = true;
build_rack = true;
// Show the parts meshed for checking; untick to space them apart for export
show_meshed = true;

/* [Shared - must match to mesh] */
// Normal module (tooth size)
module_mm = 4;      // .1
// Helix angle of each herringbone half
helix_angle = 25;   // 1
pressure_angle = 20; // 1
// Total face width (both halves)
face_width = 30;    // .5
// Total clearance, applied as rack tooth thinning
backlash = 0.3;     // .05

/* [Gear] */
gear_teeth = 16;
// Bore for the pin; 0 = solid
bore_diameter = 6;  // .5

/* [Rack] */
rack_teeth = 8;
// Solid material below the tooth roots
rack_backing = 6;   // .5

pr = pitch_radius(mod=module_mm, teeth=gear_teeth, helical=helix_angle);
echo(str("Mesh centre distance (gear axis above rack pitch line): ", pr, " mm"));
echo(str("Gear pitch diameter: ", 2*pr, " mm; tip diameter approx: ", 2*pr + 2*module_mm, " mm"));
echo(str("Transverse pitch along the rack: ", PI*module_mm/cos(helix_angle), " mm"));

if (build_rack)
    rack(mod=module_mm, teeth=rack_teeth, thickness=face_width,
         backing=rack_backing, helical=helix_angle, herringbone=true,
         pressure_angle=pressure_angle, backlash=backlash, profile_shift=0);

if (build_gear)
    translate(show_meshed ? [0, pr, 0] : [0, build_rack ? pr + 40 : 0, 0])
        spur_gear(mod=module_mm, teeth=gear_teeth, thickness=face_width,
                  helical=helix_angle, herringbone=true,
                  pressure_angle=pressure_angle, profile_shift=0,
                  shaft_diam=bore_diameter);
