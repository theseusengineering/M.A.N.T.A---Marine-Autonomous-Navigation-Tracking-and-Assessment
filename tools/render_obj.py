"""Render PNG views of OBJ models for engineering notes.

Each body (`g` group in the OBJ) gets its own colour so assemblies stay legible.
Uses VTK off-screen, so no window opens.

    python3 tools/render_obj.py "Demo tracking Casing/camera casing v1/camera casing v1.obj"
    python3 tools/render_obj.py "Demo tracking Casing"/*/*.obj
    python3 tools/render_obj.py model.obj --views iso top --up y

Images are written as "<model name> <View>.png" next to the model, or into --out.
"""

import argparse
from pathlib import Path

import vtk

BODY_COLOURS = [
    (0.55, 0.66, 0.78),
    (0.85, 0.62, 0.42),
    (0.56, 0.74, 0.55),
    (0.80, 0.55, 0.62),
    (0.70, 0.64, 0.82),
    (0.84, 0.78, 0.48),
    (0.50, 0.75, 0.76),
    (0.72, 0.60, 0.52),
]

# Camera direction (from the model towards the camera) and view-up, for Z-up models.
VIEWS = {
    "iso": ((1, -1, 0.8), (0, 0, 1)),
    "iso back": ((-1, 1, 0.8), (0, 0, 1)),
    "front": ((0, -1, 0), (0, 0, 1)),
    "side": ((1, 0, 0), (0, 0, 1)),
    "top": ((0, 0, 1), (0, 1, 0)),
    "bottom": ((0, 0, -1), (0, 1, 0)),
}


def load_bodies(path):
    """Return [(name, vertices, faces)] with one entry per OBJ group."""
    vertices = []
    bodies = []
    name, faces = path.stem, []
    for line in path.read_text(errors="ignore").splitlines():
        fields = line.split()
        if not fields:
            continue
        if fields[0] == "v":
            vertices.append(tuple(map(float, fields[1:4])))
        elif fields[0] in ("g", "o"):
            if faces:
                bodies.append((name, faces))
            name, faces = " ".join(fields[1:]) or path.stem, []
        elif fields[0] == "f":
            face = []
            for item in fields[1:]:
                index = int(item.split("/")[0])
                face.append(index - 1 if index > 0 else len(vertices) + index)
            faces.append(face)
    if faces:
        bodies.append((name, faces))
    return vertices, bodies


def body_actor(vertices, faces, colour, up_axis):
    points = vtk.vtkPoints()
    for x, y, z in vertices:
        points.InsertNextPoint((x, -z, y) if up_axis == "y" else (x, y, z))
    polys = vtk.vtkCellArray()
    for face in faces:
        polys.InsertNextCell(len(face), face)
    mesh = vtk.vtkPolyData()
    mesh.SetPoints(points)
    mesh.SetPolys(polys)

    clean = vtk.vtkCleanPolyData()
    clean.SetInputData(mesh)
    normals = vtk.vtkPolyDataNormals()
    normals.SetInputConnection(clean.GetOutputPort())
    normals.SetFeatureAngle(35)
    normals.SplittingOn()

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(normals.GetOutputPort())
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    prop = actor.GetProperty()
    prop.SetColor(colour)
    prop.SetSpecular(0.25)
    prop.SetSpecularPower(30)
    return actor


def render(path, out_dir, views, size, up_axis):
    vertices, bodies = load_bodies(path)
    renderer = vtk.vtkRenderer()
    renderer.SetBackground(1, 1, 1)
    vtk.vtkLightKit().AddLightsToRenderer(renderer)
    for index, (_, faces) in enumerate(bodies):
        colour = BODY_COLOURS[index % len(BODY_COLOURS)]
        renderer.AddActor(body_actor(vertices, faces, colour, up_axis))

    window = vtk.vtkRenderWindow()
    window.SetOffScreenRendering(1)
    window.SetSize(size, size)
    window.SetMultiSamples(8)
    window.AddRenderer(renderer)

    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for view in views:
        direction, view_up = VIEWS[view]
        camera = renderer.GetActiveCamera()
        camera.SetFocalPoint(0, 0, 0)
        camera.SetPosition(*direction)
        camera.SetViewUp(*view_up)
        camera.ParallelProjectionOn()
        renderer.ResetCamera()
        renderer.ResetCameraClippingRange()
        camera.Zoom(0.95)
        window.Render()

        grab = vtk.vtkWindowToImageFilter()
        grab.SetInput(window)
        grab.Update()
        writer = vtk.vtkPNGWriter()
        target = out_dir / f"{path.stem} {view.title()}.png"
        writer.SetFileName(str(target))
        writer.SetInputConnection(grab.GetOutputPort())
        writer.Write()
        written.append(target)
    return written


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("models", nargs="+", type=Path)
    parser.add_argument("--out", type=Path, help="output folder (default: next to each model)")
    parser.add_argument("--views", nargs="+", choices=VIEWS, default=["iso", "front", "side", "top"])
    parser.add_argument("--size", type=int, default=1200)
    parser.add_argument("--up", choices=["z", "y"], default="z", help="model up axis (Fusion exports are Z up)")
    args = parser.parse_args()

    for model in args.models:
        for target in render(model, args.out or model.parent, args.views, args.size, args.up):
            print(target)


if __name__ == "__main__":
    main()
