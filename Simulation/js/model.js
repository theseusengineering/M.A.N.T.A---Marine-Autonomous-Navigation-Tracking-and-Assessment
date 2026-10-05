import { bodyToWorld } from './physics.js';

function normalBrightness(a, b, c) {
  const ab = [b[0] - a[0], b[1] - a[1], b[2] - a[2]];
  const ac = [c[0] - a[0], c[1] - a[1], c[2] - a[2]];
  const normal = [
    ab[1] * ac[2] - ab[2] * ac[1],
    ab[2] * ac[0] - ab[0] * ac[2],
    ab[0] * ac[1] - ab[1] * ac[0],
  ];
  const length = Math.hypot(...normal) || 1;
  return 0.32 + 0.56 * Math.abs(normal[2] / length);
}

export class CraftMesh {
  constructor() {
    this.vertices = [];
    this.faces = [];
    this.loaded = false;
  }

  async load(url) {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`Model request failed: ${response.status}`);
    const vertices = [];
    const rawFaces = [];
    for (const line of (await response.text()).split(/\r?\n/)) {
      const fields = line.trim().split(/\s+/);
      if (fields[0] === 'v') vertices.push(fields.slice(1, 4).map(Number));
      if (fields[0] === 'f') rawFaces.push(fields.slice(1).map(value => Number(value.split('/')[0]) - 1));
    }
    const xs = vertices.map(vertex => vertex[0]);
    const ys = vertices.map(vertex => vertex[1]);
    const zs = vertices.map(vertex => vertex[2]);
    const centreX = (Math.min(...xs) + Math.max(...xs)) / 2;
    const centreY = (Math.min(...ys) + Math.max(...ys)) / 2;
    const minimumZ = Math.min(...zs);
    // The source is a 25% model in millimetres. Source -Y is the pointed bow.
    this.vertices = vertices.map(vertex => [
      (vertex[0] - centreX) * 0.004,
      -(vertex[1] - centreY) * 0.004,
      (vertex[2] - minimumZ) * 0.004,
    ]);
    this.faces = rawFaces.map(indices => ({
      indices,
      z: indices.reduce((sum, index) => sum + this.vertices[index][2], 0) / indices.length,
      shade: normalBrightness(...indices.slice(0, 3).map(index => this.vertices[index])),
    })).sort((a, b) => a.z - b.z);
    this.loaded = true;
  }

  draw(ctx, state, controls, worldToScreen, pixelsPerMetre) {
    if (!this.loaded) {
      this.drawFallback(ctx, state, controls, worldToScreen, pixelsPerMetre);
      return;
    }
    const projected = this.vertices.map(vertex => {
      const position = bodyToWorld(vertex[1], vertex[0], state.heading);
      // A slight elevation offset keeps the geometry visibly three-dimensional
      // while preserving a predominantly plan-view map.
      return worldToScreen(
        state.x + position.x + vertex[2] * 0.10,
        state.y + position.y + vertex[2] * 0.16,
      );
    });
    ctx.save();
    ctx.lineWidth = Math.max(0.35, pixelsPerMetre / 150);
    for (const face of this.faces) {
      const points = face.indices.map(index => projected[index]);
      ctx.beginPath();
      ctx.moveTo(points[0].x, points[0].y);
      for (let i = 1; i < points.length; i += 1) ctx.lineTo(points[i].x, points[i].y);
      ctx.closePath();
      const light = Math.round(52 + face.shade * 82);
      ctx.fillStyle = `rgb(${light - 8},${light + 8},${light + 8})`;
      ctx.fill();
      ctx.strokeStyle = 'rgba(5,15,17,.42)';
      ctx.stroke();
    }
    ctx.restore();
    this.drawActuators(ctx, state, controls, worldToScreen, pixelsPerMetre);
  }

  drawFallback(ctx, state, controls, worldToScreen, pixelsPerMetre) {
    ctx.save();
    const centre = worldToScreen(state.x, state.y);
    ctx.translate(centre.x, centre.y);
    ctx.rotate(state.heading);
    ctx.fillStyle = '#88999b';
    ctx.fillRect(-0.72 * pixelsPerMetre, -0.8 * pixelsPerMetre, 0.32 * pixelsPerMetre, 1.6 * pixelsPerMetre);
    ctx.fillRect(0.4 * pixelsPerMetre, -0.8 * pixelsPerMetre, 0.32 * pixelsPerMetre, 1.6 * pixelsPerMetre);
    ctx.fillRect(-0.55 * pixelsPerMetre, -0.15 * pixelsPerMetre, 1.1 * pixelsPerMetre, 0.3 * pixelsPerMetre);
    ctx.restore();
    this.drawActuators(ctx, state, controls, worldToScreen, pixelsPerMetre);
  }

  drawActuators(ctx, state, controls, worldToScreen, pixelsPerMetre) {
    const place = (forward, lateral) => {
      const offset = bodyToWorld(forward, lateral, state.heading);
      return worldToScreen(state.x + offset.x, state.y + offset.y);
    };
    ctx.save();
    for (const [lateral, throttle] of [[-0.55, controls.port], [0.55, controls.starboard]]) {
      const motor = place(-0.58, lateral);
      ctx.fillStyle = '#172125';
      ctx.beginPath();ctx.arc(motor.x, motor.y, Math.max(3, pixelsPerMetre * 0.07), 0, Math.PI * 2);ctx.fill();
      const direction = bodyToWorld(0.25 * throttle, 0, state.heading);
      const end = worldToScreen(state.x + direction.x + bodyToWorld(-0.75, lateral, state.heading).x,
        state.y + direction.y + bodyToWorld(-0.75, lateral, state.heading).y);
      ctx.strokeStyle = throttle >= 0 ? '#2bd9c2' : '#ffab45';ctx.lineWidth = 3;
      ctx.beginPath();ctx.moveTo(motor.x, motor.y);ctx.lineTo(end.x, end.y);ctx.stroke();
    }
    const pivot = place(-0.94, 0);
    const keelHeading = state.heading + controls.keelAngle * Math.PI / 180;
    const keelVector = bodyToWorld(-0.28, 0, keelHeading);
    const keelEnd = worldToScreen(state.x + bodyToWorld(-0.94, 0, state.heading).x + keelVector.x,
      state.y + bodyToWorld(-0.94, 0, state.heading).y + keelVector.y);
    ctx.strokeStyle = '#ffcf69';ctx.lineWidth = Math.max(3, pixelsPerMetre * 0.045);
    ctx.beginPath();ctx.moveTo(pivot.x, pivot.y);ctx.lineTo(keelEnd.x, keelEnd.y);ctx.stroke();
    ctx.restore();
  }
}
