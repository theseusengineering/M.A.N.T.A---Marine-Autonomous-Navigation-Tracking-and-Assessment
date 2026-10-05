# MANTA control simulator

This browser-based simulator uses the POC v1 OBJ as a top-down 3D representation of the proposed full-size craft. It models planar motion for controller development: surge, sway, yaw, two fixed-direction motors, a centred steering keel, drag, current and horizontal wave disturbance.

The model parameters are initial estimates. Read `assumptions.html` before treating the output as physical evidence.

## Run locally

On macOS, double-click `Open MANTA Simulator.command`. Keep its Terminal window open while using the simulator.

Alternatively, from the project root:

```sh
python3 -m http.server 8000
```

Open <http://localhost:8000/Simulation/>.

The local server is required because browsers do not normally allow an HTML file opened with `file://` to fetch its OBJ asset.

## Basic workflow

1. Click the water to add waypoints, or select **Example route**.
2. Set current and wave conditions.
3. Select **Run**.
4. Watch the intended route, actual trail, short prediction and controller telemetry.
5. Adjust heading PID, lookahead and keel allocation.
6. Reset and repeat the same route and environment.
7. Export the run as CSV for comparison.

## Structure

- `index.html`: simulator and tuning interface.
- `assumptions.html`: equations, estimates, limitations and validation tests.
- `js/physics.js`: planar craft dynamics.
- `js/controller.js`: waypoint follower and actuator allocation.
- `js/model.js`: dependency-free OBJ loader and craft renderer.
- `js/app.js`: interface, plotting and simulation loop.
- `assets/poc_v1_simplified.obj`: lightweight derivative of the original POC mesh.
- `tools/simplify_obj.py`: regenerates the lightweight mesh from the original OBJ.
