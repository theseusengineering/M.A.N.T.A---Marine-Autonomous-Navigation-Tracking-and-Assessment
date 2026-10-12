"""Parametric herringbone gear + rack generator for Fusion 360 (Mac/Windows).

Running the script opens a dialog where every value can be edited, with two
checkboxes choosing what to build: the circular gear, the straight rack, or
both. Values are remembered between runs in User Parameters (Modify ->
Change Parameters, the HB_* group), so either place can be used to edit them.

Rebuilding: each run deletes the previously generated "Herringbone Gear" /
"Herringbone Rack" component (only the ones whose checkbox is ticked) and
rebuilds it with the new values. Unticked ones are left alone.

Geometry
    transverse module   mt = mn / cos(beta)
    pitch               p  = pi * mt
    transverse angle    at = atan(tan(alpha) / cos(beta))
    rack half-skew      s  = (b/2) * tan(beta)
    gear half-twist     psi = s / pitch radius

The rack runs along +X with its pitch line at Y=0; the gear's axis is +Z
through its component origin, pitch radius mt*z/2. Backlash is applied
entirely on the rack (tooth thinning); the gear is cut to theory. With the
gear ABOVE the rack, the same helix-angle sign meshes; if the Vs clash,
flip the sign of the helix angle for one part and re-run.
"""

import math
import traceback

import adsk.core
import adsk.fusion

CMD_ID = "HerringboneGearRack"
GEAR_NAME = "Herringbone Gear"
RACK_NAME = "Herringbone Rack"
FLANK_POINTS = 12  # points per involute flank spline

# name, unit, default expression, comment
USER_PARAMS = [
    ("HB_mn", "mm", "4", "Herringbone: normal module (same for gear and rack)"),
    ("HB_beta", "deg", "25", "Herringbone: helix angle (sign flips the V direction)"),
    ("HB_alpha", "deg", "20", "Herringbone: normal pressure angle"),
    ("HB_width", "mm", "30", "Herringbone: total face width"),
    ("HB_backlash", "mm", "0.3", "Herringbone: total clearance, applied as rack tooth thinning"),
    ("HB_teeth", "", "8", "Herringbone rack: number of teeth"),
    ("HB_base", "mm", "6", "Herringbone rack: base thickness below tooth roots"),
    ("HB_gear_teeth", "", "16", "Herringbone gear: number of teeth"),
    ("HB_bore", "mm", "6", "Herringbone gear: bore diameter (0 = solid)"),
]

_app = None
_ui = None
_handlers = []  # keep handler objects alive for the lifetime of the dialog


# ---------------------------------------------------------------- parameters

def ensure_user_params(design):
    """Create missing HB_* user parameters; return {name: value} in database
    units (cm for lengths, radians for angles)."""
    values = {}
    params = design.userParameters
    for name, unit, default, comment in USER_PARAMS:
        param = params.itemByName(name)
        if param is None:
            param = params.add(name, adsk.core.ValueInput.createByString(default), unit, comment)
        values[name] = param.value
    return values


def save_user_params(design, cm_or_rad):
    """Write dialog values back to the HB_* user parameters."""
    for name, unit, _default, _comment in USER_PARAMS:
        value = cm_or_rad[name]
        if unit == "mm":
            expr = "{:.6g} mm".format(value * 10.0)
        elif unit == "deg":
            expr = "{:.6g} deg".format(math.degrees(value))
        else:
            expr = "{:.6g}".format(value)
        design.userParameters.itemByName(name).expression = expr


# ------------------------------------------------------------------ helpers

def delete_component(root, name):
    for occ in list(root.occurrences):
        if occ.component.name == name:
            occ.deleteMe()


def new_component(root, name):
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    occ.component.name = name
    return occ.component


def add_polygon(sketch, model_points):
    """Closed polygon from model-space (x, y, z) tuples, in cm."""
    lines = sketch.sketchCurves.sketchLines
    pts = [sketch.modelToSketchSpace(adsk.core.Point3D.create(*p)) for p in model_points]
    for i in range(len(pts)):
        lines.addByTwoPoints(pts[i], pts[(i + 1) % len(pts)])


def mid_plane_at(comp, offset):
    plane_input = comp.constructionPlanes.createInput()
    plane_input.setByOffset(comp.xYConstructionPlane, adsk.core.ValueInput.createByReal(offset))
    return comp.constructionPlanes.add(plane_input)


def loft_two_profiles(comp, prof_a, prof_b):
    loft_input = comp.features.loftFeatures.createInput(
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    loft_input.loftSections.add(prof_a)
    loft_input.loftSections.add(prof_b)
    return comp.features.loftFeatures.add(loft_input)


def mirror_bodies(comp, bodies, plane):
    entities = adsk.core.ObjectCollection.create()
    for body in bodies:
        entities.add(body)
    mirror_input = comp.features.mirrorFeatures.createInput(entities, plane)
    return comp.features.mirrorFeatures.add(mirror_input)


def combine_all(comp, target):
    tools = adsk.core.ObjectCollection.create()
    for body in comp.bRepBodies:
        if body != target:
            tools.add(body)
    if tools.count == 0:
        return
    combine_input = comp.features.combineFeatures.createInput(target, tools)
    combine_input.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
    comp.features.combineFeatures.add(combine_input)


# --------------------------------------------------------------- rack build

def build_rack(root, g):
    comp = new_component(root, RACK_NAME)
    pitch, b, z = g["pitch"], g["b"], g["rack_teeth"]
    ha, hf = g["ha"], g["hf"]

    tooth_poly = [
        (-g["w_root"], -hf),
        (-g["w_tip"], ha),
        (g["w_tip"], ha),
        (g["w_root"], -hf),
    ]

    sketch0 = comp.sketches.add(comp.xYConstructionPlane)
    add_polygon(sketch0, [(x, y, 0.0) for x, y in tooth_poly])

    mid_plane = mid_plane_at(comp, b / 2.0)
    sketch_mid = comp.sketches.add(mid_plane)
    add_polygon(sketch_mid, [(x + g["shift"], y, b / 2.0) for x, y in tooth_poly])

    loft = loft_two_profiles(comp, sketch0.profiles.item(0), sketch_mid.profiles.item(0))
    half_tooth = loft.bodies.item(0)
    mirror = mirror_bodies(comp, [half_tooth], mid_plane)
    tooth_bodies = [half_tooth] + [mirror.bodies.item(i) for i in range(mirror.bodies.count)]

    if z > 1:
        entities = adsk.core.ObjectCollection.create()
        for body in tooth_bodies:
            entities.add(body)
        pattern_input = comp.features.rectangularPatternFeatures.createInput(
            entities,
            comp.xConstructionAxis,
            adsk.core.ValueInput.createByReal(z),
            adsk.core.ValueInput.createByReal(pitch),
            adsk.fusion.PatternDistanceType.SpacingPatternDistanceType)
        comp.features.rectangularPatternFeatures.add(pattern_input)

    x_min, x_max = -pitch / 2.0, (z - 0.5) * pitch
    base_sketch = comp.sketches.add(comp.xYConstructionPlane)
    add_polygon(base_sketch, [
        (x_min, -hf, 0.0),
        (x_max, -hf, 0.0),
        (x_max, -hf - g["base_t"], 0.0),
        (x_min, -hf - g["base_t"], 0.0),
    ])
    base_body = comp.features.extrudeFeatures.addSimple(
        base_sketch.profiles.item(0),
        adsk.core.ValueInput.createByReal(b),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation).bodies.item(0)

    combine_all(comp, base_body)

    # Trim skewed tooth ends flush with the base ends (skips if nothing overhangs)
    margin = abs(g["shift"]) + pitch
    y_low, y_high = -hf - g["base_t"] - 0.1, ha + 0.1
    trim_sketch = comp.sketches.add(comp.xYConstructionPlane)
    add_polygon(trim_sketch, [
        (x_min - margin, y_low, 0.0), (x_min, y_low, 0.0),
        (x_min, y_high, 0.0), (x_min - margin, y_high, 0.0),
    ])
    add_polygon(trim_sketch, [
        (x_max, y_low, 0.0), (x_max + margin, y_low, 0.0),
        (x_max + margin, y_high, 0.0), (x_max, y_high, 0.0),
    ])
    try:
        profiles = adsk.core.ObjectCollection.create()
        for i in range(trim_sketch.profiles.count):
            profiles.add(trim_sketch.profiles.item(i))
        trim_input = comp.features.extrudeFeatures.createInput(
            profiles, adsk.fusion.FeatureOperations.CutFeatureOperation)
        trim_input.setDistanceExtent(False, adsk.core.ValueInput.createByReal(b))
        comp.features.extrudeFeatures.add(trim_input)
    except Exception:
        pass


# --------------------------------------------------------------- gear build

def gear_flank_points(g, side, rotation):
    """Involute flank of one tooth centered on +X, model (x, y) in cm.
    side=+1 for the counterclockwise flank, -1 for the other. Ordered from
    the root outwards to the tip."""
    r_b, r_tip, r_root = g["r_base"], g["r_tip"], g["r_root"]
    inv_a = math.tan(g["alpha_t"]) - g["alpha_t"]
    half_pitch_ang = math.pi / (2.0 * g["gear_teeth"])

    pts = []
    r_lo = max(r_b, r_root)
    for i in range(FLANK_POINTS + 1):
        r = r_lo + (r_tip - r_lo) * i / FLANK_POINTS
        angle_r = math.acos(min(1.0, r_b / r))
        inv_r = math.tan(angle_r) - angle_r
        theta = half_pitch_ang + inv_a - inv_r
        pts.append((r, theta))
    # Radial run-in below the involute, reaching slightly inside the root
    # circle so the tooth overlaps the core cylinder for a clean join
    pts.insert(0, (g["r_in"], pts[0][1]))
    return [(r * math.cos(rotation + side * th), r * math.sin(rotation + side * th))
            for r, th in pts]


def add_gear_tooth_profile(sketch, g, rotation, z_level):
    """One closed tooth profile: two involute splines, tip arc, inner arc."""
    to_sketch = lambda x, y: sketch.modelToSketchSpace(adsk.core.Point3D.create(x, y, z_level))

    left = gear_flank_points(g, +1, rotation)
    right = gear_flank_points(g, -1, rotation)

    splines = sketch.sketchCurves.sketchFittedSplines
    arcs = sketch.sketchCurves.sketchArcs
    center = to_sketch(0.0, 0.0)

    for pts in (left, right):
        collection = adsk.core.ObjectCollection.create()
        for x, y in pts:
            collection.add(to_sketch(x, y))
        splines.add(collection)

    th_tip = math.atan2(left[-1][1], left[-1][0]) - rotation
    arcs.addByCenterStartSweep(center, to_sketch(*left[-1]), -2.0 * th_tip)   # tip arc
    th_in = math.atan2(left[0][1], left[0][0]) - rotation
    arcs.addByCenterStartSweep(center, to_sketch(*right[0]), 2.0 * th_in)     # inner arc


def build_gear(root, g):
    comp = new_component(root, GEAR_NAME)
    b, z = g["b"], g["gear_teeth"]
    psi = g["shift"] / g["r_pitch"]  # half-face twist angle

    sketch0 = comp.sketches.add(comp.xYConstructionPlane)
    add_gear_tooth_profile(sketch0, g, 0.0, 0.0)

    mid_plane = mid_plane_at(comp, b / 2.0)
    sketch_mid = comp.sketches.add(mid_plane)
    add_gear_tooth_profile(sketch_mid, g, psi, b / 2.0)

    loft = loft_two_profiles(comp, sketch0.profiles.item(0), sketch_mid.profiles.item(0))
    half_tooth = loft.bodies.item(0)
    mirror = mirror_bodies(comp, [half_tooth], mid_plane)
    tooth_bodies = [half_tooth] + [mirror.bodies.item(i) for i in range(mirror.bodies.count)]

    entities = adsk.core.ObjectCollection.create()
    for body in tooth_bodies:
        entities.add(body)
    pattern_input = comp.features.circularPatternFeatures.createInput(
        entities, comp.zConstructionAxis)
    pattern_input.quantity = adsk.core.ValueInput.createByReal(z)
    pattern_input.totalAngle = adsk.core.ValueInput.createByString("360 deg")
    pattern_input.isSymmetric = False
    comp.features.circularPatternFeatures.add(pattern_input)

    core_sketch = comp.sketches.add(comp.xYConstructionPlane)
    core_sketch.sketchCurves.sketchCircles.addByCenterRadius(
        core_sketch.modelToSketchSpace(adsk.core.Point3D.create(0, 0, 0)), g["r_root"])
    core_body = comp.features.extrudeFeatures.addSimple(
        core_sketch.profiles.item(0),
        adsk.core.ValueInput.createByReal(b),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation).bodies.item(0)

    combine_all(comp, core_body)

    if g["bore"] > 1e-6:
        bore_sketch = comp.sketches.add(comp.xYConstructionPlane)
        bore_sketch.sketchCurves.sketchCircles.addByCenterRadius(
            bore_sketch.modelToSketchSpace(adsk.core.Point3D.create(0, 0, 0)), g["bore"] / 2.0)
        bore_input = comp.features.extrudeFeatures.createInput(
            bore_sketch.profiles.item(0), adsk.fusion.FeatureOperations.CutFeatureOperation)
        bore_input.setDistanceExtent(False, adsk.core.ValueInput.createByReal(b))
        comp.features.extrudeFeatures.add(bore_input)


# ------------------------------------------------------------ derived maths

def derive(v):
    """Compute all derived geometry from raw dialog values. Lengths in cm."""
    g = dict(v)
    mn, beta, alpha_n = v["mn"], v["beta"], v["alpha_n"]
    g["mt"] = mn / math.cos(beta)
    g["pitch"] = math.pi * g["mt"]
    g["alpha_t"] = math.atan(math.tan(alpha_n) / math.cos(beta))
    g["shift"] = (v["b"] / 2.0) * math.tan(beta)
    g["ha"] = mn
    g["hf"] = 1.25 * mn
    g["w_tip"] = g["pitch"] / 4.0 - g["ha"] * math.tan(g["alpha_t"]) - v["backlash"] / 2.0
    g["w_root"] = g["pitch"] / 4.0 + g["hf"] * math.tan(g["alpha_t"]) - v["backlash"] / 2.0
    g["root_gap"] = g["pitch"] - 2.0 * g["w_root"]
    g["r_pitch"] = g["mt"] * v["gear_teeth"] / 2.0
    g["r_base"] = g["r_pitch"] * math.cos(g["alpha_t"])
    g["r_tip"] = g["r_pitch"] + g["ha"]
    g["r_root"] = g["r_pitch"] - g["hf"]
    g["r_in"] = g["r_root"] - 0.3 * mn  # tooth overlap into the core cylinder
    return g


def validate(g, build_gear_flag, build_rack_flag):
    if build_rack_flag:
        if g["rack_teeth"] < 1:
            return "Rack teeth must be at least 1."
        if g["w_tip"] <= 0:
            return "Rack tooth tip width <= 0: reduce pressure angle, helix angle or backlash, or increase the module."
        if g["root_gap"] <= 0:
            return "Rack teeth merge at the root: check pressure and helix angles."
    if build_gear_flag:
        if g["gear_teeth"] < 4:
            return "Gear teeth must be at least 4."
        inv_a = math.tan(g["alpha_t"]) - g["alpha_t"]
        angle_tip = math.acos(min(1.0, g["r_base"] / g["r_tip"]))
        th_tip = math.pi / (2.0 * g["gear_teeth"]) + inv_a - (math.tan(angle_tip) - angle_tip)
        if th_tip <= 0:
            return "Gear tooth comes to a point before the tip: add teeth or reduce the helix/pressure angle."
        if g["bore"] / 2.0 >= g["r_in"]:
            return "Bore is larger than the gear root: reduce HB_bore or add teeth."
    return None


# ------------------------------------------------------------------ dialog

class ExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            design = adsk.fusion.Design.cast(_app.activeProduct)
            inputs = args.command.commandInputs

            raw = {
                "mn": inputs.itemById("mn").value,
                "beta": inputs.itemById("beta").value,
                "alpha_n": inputs.itemById("alpha").value,
                "b": inputs.itemById("width").value,
                "backlash": inputs.itemById("backlash").value,
                "rack_teeth": inputs.itemById("rack_teeth").value,
                "base_t": inputs.itemById("base").value,
                "gear_teeth": inputs.itemById("gear_teeth").value,
                "bore": inputs.itemById("bore").value,
            }
            do_gear = inputs.itemById("build_gear").value
            do_rack = inputs.itemById("build_rack").value
            if not (do_gear or do_rack):
                _ui.messageBox("Nothing to build: tick the gear, the rack, or both.")
                return

            g = derive(raw)
            problem = validate(g, do_gear, do_rack)
            if problem:
                _ui.messageBox(problem)
                return

            save_user_params(design, {
                "HB_mn": raw["mn"], "HB_beta": raw["beta"], "HB_alpha": raw["alpha_n"],
                "HB_width": raw["b"], "HB_backlash": raw["backlash"],
                "HB_teeth": raw["rack_teeth"], "HB_base": raw["base_t"],
                "HB_gear_teeth": raw["gear_teeth"], "HB_bore": raw["bore"],
            })

            root = design.rootComponent
            summary = ["Transverse module: {:.4f} mm".format(g["mt"] * 10),
                       "Pitch: {:.4f} mm".format(g["pitch"] * 10)]
            if do_gear:
                delete_component(root, GEAR_NAME)
                build_gear(root, g)
                summary.append("Gear pitch diameter: {:.3f} mm".format(g["r_pitch"] * 20))
            if do_rack:
                delete_component(root, RACK_NAME)
                build_rack(root, g)
                summary.append("Rack length: {:.2f} mm".format(g["rack_teeth"] * g["pitch"] * 10))
                summary.append("Rack root gap: {:.2f} mm (CNC bit needs >= 3.175 mm)".format(
                    g["root_gap"] * 10))
            summary.append("\nMesh: gear axis {:.3f} mm above the rack pitch line "
                           "(gear above rack = matching V direction).".format(g["r_pitch"] * 10))
            _ui.messageBox("\n".join(summary))
        except Exception:
            _ui.messageBox("Failed:\n{}".format(traceback.format_exc()))


class DestroyHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        adsk.terminate()


class CreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            design = adsk.fusion.Design.cast(_app.activeProduct)
            v = ensure_user_params(design)
            cmd = args.command
            cmd.setDialogInitialSize(380, 460)
            inputs = cmd.commandInputs
            real = adsk.core.ValueInput.createByReal

            shared = inputs.addGroupCommandInput("shared_group", "Shared (must match to mesh)")
            si = shared.children
            si.addValueInput("mn", "Normal module", "mm", real(v["HB_mn"]))
            si.addValueInput("beta", "Helix angle", "deg", real(v["HB_beta"]))
            si.addValueInput("alpha", "Pressure angle", "deg", real(v["HB_alpha"]))
            si.addValueInput("width", "Face width", "mm", real(v["HB_width"]))
            si.addValueInput("backlash", "Backlash (on rack)", "mm", real(v["HB_backlash"]))

            gear = inputs.addGroupCommandInput("gear_group", "Circular gear")
            gi = gear.children
            gi.addBoolValueInput("build_gear", "Build gear", True, "", True)
            gi.addIntegerSpinnerCommandInput("gear_teeth", "Teeth", 4, 200, 1,
                                             int(round(v["HB_gear_teeth"])))
            gi.addValueInput("bore", "Bore diameter (0 = solid)", "mm", real(v["HB_bore"]))

            rack = inputs.addGroupCommandInput("rack_group", "Rack")
            ri = rack.children
            ri.addBoolValueInput("build_rack", "Build rack", True, "", True)
            ri.addIntegerSpinnerCommandInput("rack_teeth", "Teeth", 1, 500, 1,
                                             int(round(v["HB_teeth"])))
            ri.addValueInput("base", "Base thickness", "mm", real(v["HB_base"]))

            on_execute = ExecuteHandler()
            cmd.execute.add(on_execute)
            _handlers.append(on_execute)
            on_destroy = DestroyHandler()
            cmd.destroy.add(on_destroy)
            _handlers.append(on_destroy)
        except Exception:
            _ui.messageBox("Failed:\n{}".format(traceback.format_exc()))


def run(context):
    global _app, _ui
    try:
        _app = adsk.core.Application.get()
        _ui = _app.userInterface
        design = adsk.fusion.Design.cast(_app.activeProduct)
        if design is None:
            _ui.messageBox("Open a Design document first.")
            return
        if design.designType != adsk.fusion.DesignTypes.ParametricDesignType:
            _ui.messageBox("Switch to parametric modelling (capture design history) first.")
            return

        cmd_def = _ui.commandDefinitions.itemById(CMD_ID)
        if cmd_def:
            cmd_def.deleteMe()
        cmd_def = _ui.commandDefinitions.addButtonDefinition(
            CMD_ID, "Herringbone Gear + Rack", "Builds a herringbone gear and/or rack.")
        on_created = CreatedHandler()
        cmd_def.commandCreated.add(on_created)
        _handlers.append(on_created)
        cmd_def.execute()
        adsk.autoTerminate(False)
    except Exception:
        if _ui:
            _ui.messageBox("Failed:\n{}".format(traceback.format_exc()))
