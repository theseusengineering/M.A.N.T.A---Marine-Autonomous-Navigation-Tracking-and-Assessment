import { CraftDynamics, ESTIMATED_CRAFT, clamp } from './physics.js';
import { CONTROLLER_DEFAULTS, WaypointController } from './controller.js';
import { CraftMesh } from './model.js';

const worldCanvas = document.querySelector('#worldCanvas');
const worldContext = worldCanvas.getContext('2d');
const plotCanvas = document.querySelector('#plotCanvas');
const plotContext = plotCanvas.getContext('2d');
const dynamics = new CraftDynamics();
const controller = new WaypointController();
const mesh = new CraftMesh();

const simulation = {
  running: false,
  route: [],
  trail: [],
  history: [],
  controls: { port: 0, starboard: 0, keelAngle: 0 },
  view: { x: 0, y: 2, width: 15 },
  gustRemaining: 0,
  historyClock: 0,
};

const ids = Object.fromEntries([...document.querySelectorAll('[id]')].map(element => [element.id, element]));

const bindings = {
  currentSpeed: { suffix: ' m/s', digits: 2 },
  currentDirection: { suffix: '°', digits: 0 },
  waveStrength: { suffix: ' N', digits: 0 },
  waveDirection: { suffix: '°', digits: 0 },
  wavePeriod: { suffix: ' s', digits: 1 },
  headingKp: { suffix: '', digits: 2 },
  headingKi: { suffix: '', digits: 2 },
  headingKd: { suffix: '', digits: 2 },
  lookahead: { suffix: ' m', digits: 1 },
  keelShare: { suffix: '%', digits: 0 },
  waypointRadius: { suffix: ' m', digits: 1 },
  mass: { suffix: ' kg', digits: 0 },
  motorThrust: { suffix: ' N', digits: 0 },
  cruiseSpeed: { suffix: ' m/s', digits: 1 },
  maxKeel: { suffix: '°', digits: 0 },
  forwardDrag: { suffix: ' N/(m/s)²', digits: 0 },
  lateralDrag: { suffix: ' N/(m/s)²', digits: 0 },
};

function number(id) {
  return Number(ids[id].value);
}

function updateBoundValue(id) {
  const binding = bindings[id];
  ids[`${id}Out`].textContent = number(id).toFixed(binding.digits) + binding.suffix;
}

for (const id of Object.keys(bindings)) {
  updateBoundValue(id);
  ids[id].addEventListener('input', () => {
    updateBoundValue(id);
    applyParameters();
  });
}

function applyParameters() {
  dynamics.setParameters({
    mass: number('mass'),
    motorThrust: number('motorThrust'),
    maxKeelDeg: number('maxKeel'),
    forwardDrag: number('forwardDrag'),
    lateralDrag: number('lateralDrag'),
  });
  controller.setParameters({
    headingKp: number('headingKp'),
    headingKi: number('headingKi'),
    headingKd: number('headingKd'),
    lookahead: number('lookahead'),
    keelShare: number('keelShare') / 100,
    waypointRadius: number('waypointRadius'),
    cruiseSpeed: number('cruiseSpeed'),
  });
}

function environment() {
  return {
    currentSpeed: number('currentSpeed'),
    currentDirection: number('currentDirection'),
    waveStrength: number('waveStrength'),
    waveDirection: number('waveDirection'),
    wavePeriod: number('wavePeriod'),
    gustRemaining: simulation.gustRemaining,
    gustStrength: 0.75,
  };
}

function resizeCanvas(canvas, context) {
  const ratio = Math.min(devicePixelRatio || 1, 2);
  const rect = canvas.getBoundingClientRect();
  const width = Math.max(1, Math.round(rect.width * ratio));
  const height = Math.max(1, Math.round(rect.height * ratio));
  if (canvas.width !== width || canvas.height !== height) {
    canvas.width = width;
    canvas.height = height;
  }
  context.setTransform(ratio, 0, 0, ratio, 0, 0);
  return { width: rect.width, height: rect.height, ratio };
}

function viewTransform() {
  const rect = worldCanvas.getBoundingClientRect();
  const pixelsPerMetre = rect.width / simulation.view.width;
  return {
    width: rect.width,
    height: rect.height,
    pixelsPerMetre,
    worldToScreen(x, y) {
      return {
        x: rect.width / 2 + (x - simulation.view.x) * pixelsPerMetre,
        y: rect.height / 2 - (y - simulation.view.y) * pixelsPerMetre,
      };
    },
    screenToWorld(x, y) {
      return {
        x: simulation.view.x + (x - rect.width / 2) / pixelsPerMetre,
        y: simulation.view.y - (y - rect.height / 2) / pixelsPerMetre,
      };
    },
  };
}

function status(mode, text) {
  ids.modeBadge.className = `badge ${mode}`;
  ids.modeBadge.textContent = text;
}

function resetCraft() {
  simulation.running = false;
  dynamics.reset();
  controller.setRoute(simulation.route, { x: 0, y: 0 });
  simulation.controls = { port: 0, starboard: 0, keelAngle: 0 };
  simulation.trail = [{ x: 0, y: 0 }];
  simulation.history = [];
  simulation.historyClock = 0;
  simulation.gustRemaining = 0;
  simulation.view.x = 0;
  simulation.view.y = 2;
  ids.runButton.disabled = false;
  ids.pauseButton.disabled = true;
  status('idle', simulation.route.length ? 'READY' : 'ROUTE NEEDED');
  updateTelemetry();
}

function run() {
  if (!simulation.route.length) {
    status('idle', 'ADD WAYPOINTS');
    return;
  }
  if (controller.complete) {
    dynamics.reset();
    controller.setRoute(simulation.route, { x: 0, y: 0 });
    simulation.controls = { port: 0, starboard: 0, keelAngle: 0 };
    simulation.trail = [{ x: 0, y: 0 }];
    simulation.history = [];
  }
  simulation.running = true;
  ids.runButton.disabled = true;
  ids.pauseButton.disabled = false;
  status('running', 'RUNNING');
}

function pause() {
  simulation.running = false;
  ids.runButton.disabled = false;
  ids.pauseButton.disabled = true;
  status('paused', 'PAUSED');
}

function clearRoute() {
  simulation.route.length = 0;
  resetCraft();
}

function exampleRoute() {
  simulation.route = [
    { x: 0, y: 5 },
    { x: 4.2, y: 8.2 },
    { x: 5.2, y: 13.1 },
    { x: 0.8, y: 16.2 },
    { x: -3.8, y: 13.1 },
  ];
  resetCraft();
}

function addWaypoint(event) {
  if (event.button !== 0) return;
  const rect = worldCanvas.getBoundingClientRect();
  const transform = viewTransform();
  const waypoint = transform.screenToWorld(event.clientX - rect.left, event.clientY - rect.top);
  simulation.route.push(waypoint);
  controller.setRoute(simulation.route, { x: dynamics.state.x, y: dynamics.state.y });
  ids.canvasHint.style.display = 'none';
  status('idle', 'READY');
}

function restoreController() {
  for (const [id, value] of Object.entries({
    headingKp: CONTROLLER_DEFAULTS.headingKp,
    headingKi: CONTROLLER_DEFAULTS.headingKi,
    headingKd: CONTROLLER_DEFAULTS.headingKd,
    lookahead: CONTROLLER_DEFAULTS.lookahead,
    keelShare: CONTROLLER_DEFAULTS.keelShare * 100,
    waypointRadius: CONTROLLER_DEFAULTS.waypointRadius,
  })) {
    ids[id].value = value;
    updateBoundValue(id);
  }
  applyParameters();
}

function restoreCraft() {
  for (const [id, value] of Object.entries({
    mass: ESTIMATED_CRAFT.mass,
    motorThrust: ESTIMATED_CRAFT.motorThrust,
    cruiseSpeed: CONTROLLER_DEFAULTS.cruiseSpeed,
    maxKeel: ESTIMATED_CRAFT.maxKeelDeg,
    forwardDrag: ESTIMATED_CRAFT.forwardDrag,
    lateralDrag: ESTIMATED_CRAFT.lateralDrag,
  })) {
    ids[id].value = value;
    updateBoundValue(id);
  }
  applyParameters();
}

function simulationStep(dt) {
  applyParameters();
  simulation.controls = controller.update(dynamics.state, dt, dynamics.parameters);
  dynamics.step(dt, simulation.controls, environment());
  simulation.gustRemaining = Math.max(0, simulation.gustRemaining - dt);

  const state = dynamics.state;
  const previous = simulation.trail.at(-1);
  if (!previous || Math.hypot(state.x - previous.x, state.y - previous.y) > 0.035) {
    simulation.trail.push({ x: state.x, y: state.y });
    if (simulation.trail.length > 9000) simulation.trail.shift();
  }
  simulation.historyClock += dt;
  if (simulation.historyClock >= 0.1) {
    simulation.historyClock = 0;
    simulation.history.push({
      time: state.time,
      x: state.x,
      y: state.y,
      speed: state.u,
      heading: state.heading * 180 / Math.PI,
      crossTrack: controller.telemetry.crossTrack,
      headingError: controller.telemetry.headingError * 180 / Math.PI,
      keel: simulation.controls.keelAngle,
      port: simulation.controls.port,
      starboard: simulation.controls.starboard,
    });
    if (simulation.history.length > 1800) simulation.history.shift();
  }
  if (controller.complete) {
    pause();
    status('complete', 'ROUTE COMPLETE');
  }
}

function drawGrid(transform) {
  const { width, height, pixelsPerMetre, worldToScreen } = transform;
  worldContext.fillStyle = '#06171a';
  worldContext.fillRect(0, 0, width, height);
  const metresAcross = width / pixelsPerMetre;
  const spacing = metresAcross > 22 ? 2 : 1;
  const left = simulation.view.x - width / pixelsPerMetre / 2;
  const right = simulation.view.x + width / pixelsPerMetre / 2;
  const bottom = simulation.view.y - height / pixelsPerMetre / 2;
  const top = simulation.view.y + height / pixelsPerMetre / 2;
  worldContext.lineWidth = 1;
  for (let x = Math.floor(left / spacing) * spacing; x <= right; x += spacing) {
    const screen = worldToScreen(x, 0);
    worldContext.strokeStyle = Math.abs(x) < 0.001 ? '#315158' : '#183036';
    worldContext.beginPath();worldContext.moveTo(screen.x, 0);worldContext.lineTo(screen.x, height);worldContext.stroke();
  }
  for (let y = Math.floor(bottom / spacing) * spacing; y <= top; y += spacing) {
    const screen = worldToScreen(0, y);
    worldContext.strokeStyle = Math.abs(y) < 0.001 ? '#315158' : '#183036';
    worldContext.beginPath();worldContext.moveTo(0, screen.y);worldContext.lineTo(width, screen.y);worldContext.stroke();
  }
  worldContext.fillStyle = '#759397';worldContext.font = '11px system-ui';
  worldContext.fillText(`${spacing} m grid`, 12, height - 14);
}

function drawEnvironment(transform) {
  const env = environment();
  const direction = env.currentDirection * Math.PI / 180;
  const origin = { x: transform.width - 62, y: 58 };
  const length = 18 + env.currentSpeed * 25;
  worldContext.save();
  worldContext.strokeStyle = '#55aaff';worldContext.fillStyle = '#55aaff';worldContext.lineWidth = 2;
  worldContext.beginPath();worldContext.moveTo(origin.x, origin.y);
  worldContext.lineTo(origin.x + Math.sin(direction) * length, origin.y - Math.cos(direction) * length);worldContext.stroke();
  worldContext.fillText('CURRENT', origin.x - 30, origin.y - 12);
  if (simulation.gustRemaining > 0) {
    worldContext.fillStyle = '#ffab45';worldContext.fillText(`GUST ${simulation.gustRemaining.toFixed(1)} s`, origin.x - 30, origin.y + 20);
  }
  worldContext.restore();
}

function drawPolyline(points, transform, colour, width = 2, dash = []) {
  if (points.length < 2) return;
  worldContext.save();worldContext.strokeStyle = colour;worldContext.lineWidth = width;worldContext.setLineDash(dash);
  worldContext.beginPath();
  points.forEach((point, index) => {
    const screen = transform.worldToScreen(point.x, point.y);
    if (index === 0) worldContext.moveTo(screen.x, screen.y); else worldContext.lineTo(screen.x, screen.y);
  });
  worldContext.stroke();worldContext.restore();
}

function prediction() {
  const result = [];
  let x = dynamics.state.x;
  let y = dynamics.state.y;
  let heading = dynamics.state.heading;
  let speed = dynamics.state.u;
  const turnRate = dynamics.state.yawRate +
    (simulation.controls.port - simulation.controls.starboard) * 0.32 +
    simulation.controls.keelAngle * Math.PI / 180 * Math.max(0, speed) * 0.35;
  for (let index = 0; index < 20; index += 1) {
    const dt = 0.2;
    speed += (controller.telemetry.targetSpeed - speed) * 0.18;
    heading += turnRate * dt;
    x += Math.sin(heading) * speed * dt;
    y += Math.cos(heading) * speed * dt;
    result.push({ x, y });
  }
  return result;
}

function drawRoute(transform) {
  const origin = simulation.trail[0] ?? { x: dynamics.state.x, y: dynamics.state.y };
  drawPolyline([origin, ...simulation.route], transform, '#e9f4f2', 2);
  drawPolyline(simulation.trail, transform, '#2bd9c2', 2.5);
  if (simulation.running) drawPolyline([{ x: dynamics.state.x, y: dynamics.state.y }, ...prediction()], transform, '#ffab45', 1.5, [5, 4]);
  simulation.route.forEach((waypoint, index) => {
    const point = transform.worldToScreen(waypoint.x, waypoint.y);
    const active = index === controller.index && !controller.complete;
    worldContext.fillStyle = active ? '#ffcf69' : '#dbe9e8';
    worldContext.strokeStyle = '#06171a';worldContext.lineWidth = 2;
    worldContext.beginPath();worldContext.arc(point.x, point.y, active ? 7 : 5, 0, Math.PI * 2);worldContext.fill();worldContext.stroke();
    worldContext.fillStyle = '#06171a';worldContext.font = 'bold 9px system-ui';worldContext.textAlign = 'center';worldContext.textBaseline = 'middle';
    worldContext.fillText(String(index + 1), point.x, point.y + .5);
  });
  worldContext.textAlign = 'left';worldContext.textBaseline = 'alphabetic';
}

function drawWorld() {
  const size = resizeCanvas(worldCanvas, worldContext);
  if (ids.followCraft.checked && simulation.running) {
    simulation.view.x += (dynamics.state.x - simulation.view.x) * 0.05;
    simulation.view.y += (dynamics.state.y - simulation.view.y) * 0.05;
  }
  const transform = viewTransform();
  transform.width = size.width;transform.height = size.height;
  drawGrid(transform);
  drawEnvironment(transform);
  drawRoute(transform);
  mesh.draw(worldContext, dynamics.state, simulation.controls, transform.worldToScreen, transform.pixelsPerMetre);
}

function drawPlot() {
  const { width, height } = resizeCanvas(plotCanvas, plotContext);
  plotContext.clearRect(0, 0, width, height);
  plotContext.fillStyle = '#091416';plotContext.fillRect(0, 0, width, height);
  plotContext.strokeStyle = '#263d42';plotContext.lineWidth = 1;
  for (let row = 1; row < 4; row += 1) {
    const y = height * row / 4;plotContext.beginPath();plotContext.moveTo(0, y);plotContext.lineTo(width, y);plotContext.stroke();
  }
  const visible = simulation.history.slice(-600);
  if (visible.length < 2) return;
  const maxMagnitude = Math.max(1, ...visible.map(sample => Math.abs(sample.crossTrack)), ...visible.map(sample => Math.abs(sample.headingError / 30)));
  const drawSeries = (getter, colour) => {
    plotContext.strokeStyle = colour;plotContext.lineWidth = 2;plotContext.beginPath();
    visible.forEach((sample, index) => {
      const x = index / (visible.length - 1) * width;
      const y = height / 2 - getter(sample) / maxMagnitude * height * 0.42;
      if (index === 0) plotContext.moveTo(x, y); else plotContext.lineTo(x, y);
    });
    plotContext.stroke();
  };
  drawSeries(sample => sample.crossTrack, '#2bd9c2');
  drawSeries(sample => sample.headingError / 30, '#ffab45');
}

function updateTelemetry() {
  const telemetry = controller.telemetry;
  ids.speedValue.textContent = `${dynamics.state.u.toFixed(2)} m/s`;
  ids.crossTrackValue.textContent = `${telemetry.crossTrack.toFixed(2)} m`;
  ids.headingErrorValue.textContent = `${(telemetry.headingError * 180 / Math.PI).toFixed(1)}°`;
  ids.keelValue.textContent = `${simulation.controls.keelAngle.toFixed(1)}°`;
  ids.portValue.textContent = `${Math.round(simulation.controls.port * 100)}%`;
  ids.starboardValue.textContent = `${Math.round(simulation.controls.starboard * 100)}%`;
}

function exportCsv() {
  if (!simulation.history.length) return;
  const columns = ['time', 'x', 'y', 'speed', 'heading', 'crossTrack', 'headingError', 'keel', 'port', 'starboard'];
  const rows = [columns.join(','), ...simulation.history.map(sample => columns.map(column => sample[column].toFixed(4)).join(','))];
  const link = document.createElement('a');
  link.href = URL.createObjectURL(new Blob([rows.join('\n')], { type: 'text/csv' }));
  link.download = `manta-simulation-${new Date().toISOString().replace(/[:.]/g, '-')}.csv`;
  link.click();URL.revokeObjectURL(link.href);
}

ids.runButton.addEventListener('click', run);
ids.pauseButton.addEventListener('click', pause);
ids.resetButton.addEventListener('click', resetCraft);
ids.clearButton.addEventListener('click', clearRoute);
ids.demoButton.addEventListener('click', exampleRoute);
ids.gustButton.addEventListener('click', () => { simulation.gustRemaining = 4; });
ids.restoreController.addEventListener('click', restoreController);
ids.restoreCraft.addEventListener('click', restoreCraft);
ids.exportButton.addEventListener('click', exportCsv);
worldCanvas.addEventListener('pointerdown', addWaypoint);

for (const tab of document.querySelectorAll('.tab')) {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab,.tab-panel').forEach(element => element.classList.remove('active'));
    tab.classList.add('active');ids[tab.dataset.tab].classList.add('active');
  });
}

worldCanvas.addEventListener('wheel', event => {
  event.preventDefault();
  simulation.view.width = clamp(simulation.view.width * (event.deltaY > 0 ? 1.12 : 0.89), 6, 35);
}, { passive: false });

let previousTime = performance.now();
let accumulator = 0;
function frame(now) {
  const elapsed = Math.min(0.1, (now - previousTime) / 1000);
  previousTime = now;
  if (simulation.running) {
    accumulator += elapsed * number('timeScale');
    while (accumulator >= 1 / 60) {
      simulationStep(1 / 60);
      accumulator -= 1 / 60;
    }
  } else accumulator = 0;
  updateTelemetry();drawWorld();drawPlot();requestAnimationFrame(frame);
}

applyParameters();
resetCraft();
mesh.load('assets/poc_v1_simplified.obj').catch(error => {
  console.warn('Using fallback craft geometry:', error);
});
requestAnimationFrame(frame);
