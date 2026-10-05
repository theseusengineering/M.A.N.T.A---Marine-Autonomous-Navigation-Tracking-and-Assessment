"""Create the lightweight browser mesh from the original POC OBJ.

This is a vertex-clustering simplifier. It is intentionally dependency free so
the displayed model can be regenerated without installing CAD or mesh tools.
"""

from pathlib import Path


SOURCE = Path(__file__).parents[2] / "P.O.C. Quick Draft v1" / "v1.obj"
OUTPUT = Path(__file__).parents[1] / "assets" / "poc_v1_simplified.obj"
GRID_MM = 15.0


def load_obj(path: Path):
    vertices = []
    triangles = []
    for line in path.read_text(errors="ignore").splitlines():
        fields = line.split()
        if not fields:
            continue
        if fields[0] == "v":
            vertices.append(tuple(map(float, fields[1:4])))
        elif fields[0] == "f":
            face = [int(item.split("/")[0]) - 1 for item in fields[1:]]
            for index in range(1, len(face) - 1):
                triangles.append((face[0], face[index], face[index + 1]))
    return vertices, triangles


def simplify(vertices, triangles):
    buckets = {}
    sums = []
    remap = []
    for vertex in vertices:
        key = tuple(round(value / GRID_MM) for value in vertex)
        if key not in buckets:
            buckets[key] = len(sums)
            sums.append([0.0, 0.0, 0.0, 0])
        target = buckets[key]
        remap.append(target)
        for axis in range(3):
            sums[target][axis] += vertex[axis]
        sums[target][3] += 1

    new_vertices = [tuple(values[axis] / values[3] for axis in range(3)) for values in sums]
    new_triangles = []
    seen = set()
    for triangle in triangles:
        mapped = tuple(remap[index] for index in triangle)
        if len(set(mapped)) < 3 or mapped in seen:
            continue
        seen.add(mapped)
        new_triangles.append(mapped)
    return new_vertices, new_triangles


def main():
    vertices, triangles = load_obj(SOURCE)
    vertices, triangles = simplify(vertices, triangles)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w") as output:
        output.write("# Simplified from P.O.C. Quick Draft v1/v1.obj\n")
        output.write(f"# Vertex clustering grid: {GRID_MM:g} source-model mm\n")
        for vertex in vertices:
            output.write("v {:.5f} {:.5f} {:.5f}\n".format(*vertex))
        for triangle in triangles:
            output.write("f {} {} {}\n".format(*(index + 1 for index in triangle)))
    print(f"Wrote {len(vertices)} vertices and {len(triangles)} triangles to {OUTPUT}")


if __name__ == "__main__":
    main()
