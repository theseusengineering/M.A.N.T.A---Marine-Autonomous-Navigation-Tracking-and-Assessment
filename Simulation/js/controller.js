import { bearing, clamp, wrapAngle } from './physics.js';

export const CONTROLLER_DEFAULTS = Object.freeze({
  headingKp: 1.8,
  headingKi: 0.04,
  headingKd: 0.6,
  lookahead: 2,
  keelShare: 0.65,
  waypointRadius: 0.65,
  cruiseSpeed: 1.1,
});

export class WaypointController {
  constructor(parameters = {}) {
    this.parameters = { ...CONTROLLER_DEFAULTS, ...parameters };
    this.route = [];
    this.reset();
  }

  reset(start = { x: 0, y: 0 }) {
    this.start = { ...start };
    this.index = 0;
    this.integral = 0;
    this.previousError = 0;
    this.complete = false;
    this.telemetry = {
      crossTrack: 0,
      headingError: 0,
      desiredHeading: 0,
      targetSpeed: 0,
      targetPoint: { ...start },
    };
  }

  setRoute(route, start = this.start) {
    this.route = route;
    this.reset(start);
  }

  setParameters(parameters) {
    Object.assign(this.parameters, parameters);
  }

  segmentStart() {
    return this.index === 0 ? this.start : this.route[this.index - 1];
  }

  update(state, dt, craftParameters) {
    if (!this.route.length || this.complete) {
      return { port: 0, starboard: 0, keelAngle: 0 };
    }

    let target = this.route[this.index];
    let distance = Math.hypot(target.x - state.x, target.y - state.y);
    if (distance <= this.parameters.waypointRadius) {
      if (this.index < this.route.length - 1) {
        this.index += 1;
        this.integral = 0;
        target = this.route[this.index];
        distance = Math.hypot(target.x - state.x, target.y - state.y);
      } else {
        this.complete = true;
        return { port: 0, starboard: 0, keelAngle: 0 };
      }
    }

    const start = this.segmentStart();
    const segmentX = target.x - start.x;
    const segmentY = target.y - start.y;
    const segmentLength = Math.max(0.001, Math.hypot(segmentX, segmentY));
    const tangentX = segmentX / segmentLength;
    const tangentY = segmentY / segmentLength;
    const relativeX = state.x - start.x;
    const relativeY = state.y - start.y;
    const along = clamp(relativeX * tangentX + relativeY * tangentY, 0, segmentLength);
    const nearest = { x: start.x + tangentX * along, y: start.y + tangentY * along };
    const crossTrack = tangentX * (state.y - nearest.y) - tangentY * (state.x - nearest.x);
    const aimDistance = Math.min(segmentLength, along + this.parameters.lookahead);
    const aim = { x: start.x + tangentX * aimDistance, y: start.y + tangentY * aimDistance };
    const desiredHeading = bearing(state, aim);
    const headingError = wrapAngle(desiredHeading - state.heading);

    this.integral = clamp(this.integral + headingError * dt, -1.5, 1.5);
    const derivative = dt > 0 ? (headingError - this.previousError) / dt : 0;
    this.previousError = headingError;
    const steering = clamp(
      this.parameters.headingKp * headingError +
      this.parameters.headingKi * this.integral +
      this.parameters.headingKd * derivative,
      -1,
      1,
    );

    const finalWaypoint = this.index === this.route.length - 1;
    const slowdownDistance = Math.max(2.5, this.parameters.waypointRadius * 3.5);
    const speedFactor = finalWaypoint ? clamp(distance / slowdownDistance, 0.12, 1) : 1;
    const targetSpeed = this.parameters.cruiseSpeed * speedFactor;
    const speedError = targetSpeed - state.u;
    const baseThrottle = clamp(0.28 + speedError * 0.72, -0.4, 1);

    // A keel has little authority close to zero water speed, so differential
    // thrust automatically takes a larger share during launch and recovery.
    const keelAuthority = clamp(Math.abs(state.u) / 0.7, 0, 1);
    const effectiveKeelShare = this.parameters.keelShare * keelAuthority;
    const differential = steering * (1 - effectiveKeelShare) * 0.9;
    const keelAngle = steering * effectiveKeelShare * craftParameters.maxKeelDeg;

    this.telemetry = { crossTrack, headingError, desiredHeading, targetSpeed, targetPoint: aim };
    return {
      port: clamp(baseThrottle + differential, -1, 1),
      starboard: clamp(baseThrottle - differential, -1, 1),
      keelAngle,
    };
  }
}
