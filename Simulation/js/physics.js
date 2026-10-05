export const ESTIMATED_CRAFT = Object.freeze({
  mass: 30,
  length: 1.6,
  beam: 1.48,
  yawInertia: 11.9,
  motorThrust: 25,
  motorArm: 0.55,
  keelArm: 0.88,
  maxKeelDeg: 30,
  keelCoefficient: 48,
  forwardDrag: 22,
  lateralDrag: 85,
  yawDrag: 16,
});

export function clamp(value, low, high) {
  return Math.max(low, Math.min(high, value));
}

export function wrapAngle(angle) {
  while (angle > Math.PI) angle -= Math.PI * 2;
  while (angle < -Math.PI) angle += Math.PI * 2;
  return angle;
}

export function bearing(from, to) {
  return Math.atan2(to.x - from.x, to.y - from.y);
}

export function bodyToWorld(u, v, heading) {
  return {
    x: u * Math.sin(heading) + v * Math.cos(heading),
    y: u * Math.cos(heading) - v * Math.sin(heading),
  };
}

export function worldToBody(x, y, heading) {
  return {
    u: x * Math.sin(heading) + y * Math.cos(heading),
    v: x * Math.cos(heading) - y * Math.sin(heading),
  };
}

export class CraftDynamics {
  constructor(parameters = {}) {
    this.parameters = { ...ESTIMATED_CRAFT, ...parameters };
    this.reset();
  }

  reset(initial = {}) {
    this.state = {
      x: initial.x ?? 0,
      y: initial.y ?? 0,
      heading: initial.heading ?? 0,
      u: initial.u ?? 0,
      v: initial.v ?? 0,
      yawRate: initial.yawRate ?? 0,
      time: 0,
    };
    this.lastForces = { surge: 0, sway: 0, yaw: 0 };
  }

  setParameters(parameters) {
    Object.assign(this.parameters, parameters);
    this.parameters.yawInertia = this.parameters.mass *
      (this.parameters.length ** 2 + this.parameters.beam ** 2) / 12;
  }

  step(dt, controls, environment) {
    const p = this.parameters;
    const s = this.state;
    const direction = environment.currentDirection * Math.PI / 180;
    const gust = environment.gustRemaining > 0 ? environment.gustStrength : 0;
    const currentSpeed = environment.currentSpeed + gust;
    const currentWorld = {
      x: currentSpeed * Math.sin(direction),
      y: currentSpeed * Math.cos(direction),
    };
    const currentBody = worldToBody(currentWorld.x, currentWorld.y, s.heading);
    const waterU = s.u - currentBody.u;
    const waterV = s.v - currentBody.v;

    const port = clamp(controls.port, -1, 1) * p.motorThrust;
    const starboard = clamp(controls.starboard, -1, 1) * p.motorThrust;
    let surgeForce = port + starboard;
    let swayForce = 0;
    let yawMoment = p.motorArm * (port - starboard);

    surgeForce -= 0.55 * p.forwardDrag * waterU;
    surgeForce -= p.forwardDrag * Math.abs(waterU) * waterU;
    swayForce -= 0.7 * p.lateralDrag * waterV;
    swayForce -= p.lateralDrag * Math.abs(waterV) * waterV;
    yawMoment -= p.yawDrag * s.yawRate;
    yawMoment -= 5 * Math.abs(s.yawRate) * s.yawRate;

    const keelAngle = clamp(controls.keelAngle, -p.maxKeelDeg, p.maxKeelDeg) * Math.PI / 180;
    const keelLoad = p.keelCoefficient * waterU * Math.abs(waterU) * Math.sin(keelAngle);
    swayForce -= keelLoad;
    yawMoment += p.keelArm * keelLoad;

    if (environment.waveStrength > 0) {
      const phase = (Math.PI * 2 * s.time / environment.wavePeriod);
      const waveDirection = environment.waveDirection * Math.PI / 180;
      const pulse = Math.sin(phase) + 0.35 * Math.sin(phase * 1.73 + 1.1);
      const waveWorld = {
        x: environment.waveStrength * pulse * Math.sin(waveDirection),
        y: environment.waveStrength * pulse * Math.cos(waveDirection),
      };
      const waveBody = worldToBody(waveWorld.x, waveWorld.y, s.heading);
      surgeForce += waveBody.u;
      swayForce += waveBody.v;
      yawMoment += environment.waveStrength * 0.22 * Math.sin(phase * 1.31 + 0.7);
    }

    const uDot = surgeForce / p.mass + s.yawRate * s.v;
    const vDot = swayForce / p.mass - s.yawRate * s.u;
    const yawDot = yawMoment / p.yawInertia;
    s.u = clamp(s.u + uDot * dt, -3.5, 3.5);
    s.v = clamp(s.v + vDot * dt, -2.5, 2.5);
    s.yawRate = clamp(s.yawRate + yawDot * dt, -2.2, 2.2);

    const velocity = bodyToWorld(s.u, s.v, s.heading);
    s.x += velocity.x * dt;
    s.y += velocity.y * dt;
    s.heading = wrapAngle(s.heading + s.yawRate * dt);
    s.time += dt;
    this.lastForces = { surge: surgeForce, sway: swayForce, yaw: yawMoment };
    return s;
  }
}
