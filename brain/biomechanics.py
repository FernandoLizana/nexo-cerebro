"""
Física + biomecánica corporal — cuerpo ↔ entorno ↔ cerebro.

Integra gravedad, inercia, fricción, colisiones con impulso, equilibrio, músculos,
articulaciones, respiración, ritmo cardíaco y fatiga física. El movimiento del mundo
pasa por fuerzas; el estado se proyecta a interocepción y nocicepción.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .ragdoll_skeleton import ArticulatedSkeleton

# Escala: ~1 px ≈ 1 cm en la simulación doméstica
PX_TO_M = 0.01
G = 9.81  # m/s²
DT = 0.33  # s por tick (~3 Hz mundo)
RHO_WATER = 1000.0  # kg/m³
RHO_BODY = 985.0
BODY_VOLUME_M3 = 0.068  # ~68 L


@dataclass
class BiomechanicalBody:
    """Cuerpo físico-biológico simplificado (humanoid 2.5D)."""

    mass: float = 68.0  # kg
    vx: float = 0.0  # px/s
    vy: float = 0.0
    vz: float = 0.0  # m/s vertical
    height: float = 0.0  # m sobre suelo
    ax: float = 0.0  # px/s²
    ay: float = 0.0
    body_angle: float = 0.0  # rad
    angular_velocity: float = 0.0

    on_ground: bool = True
    in_water: bool = False
    water_depth: float = 0.0  # 0–1 fracción sumergida
    buoyancy_n: float = 0.0
    gait: str = "idle"
    gait_phase: float = 0.0
    ragdoll_active: bool = False
    ragdoll_ticks: int = 0
    skeleton_art: ArticulatedSkeleton = field(default_factory=ArticulatedSkeleton)

    equilibrium: float = 1.0
    com_x: float = 0.0  # offset cm del COM respecto a pies
    com_y: float = 0.0

    heart_rate: float = 72.0
    breath_rate: float = 14.0
    blood_flow: float = 0.55
    physical_fatigue: float = 0.0
    muscle_activation: dict[str, float] = field(default_factory=lambda: {
        "quads": 0.0, "hamstrings": 0.0, "calves": 0.0,
        "glutes": 0.0, "core": 0.0, "arms": 0.0,
    })
    joint_stress: dict[str, float] = field(default_factory=lambda: {
        "spine": 0.0, "hip_l": 0.0, "hip_r": 0.0,
        "knee_l": 0.0, "knee_r": 0.0, "ankle_l": 0.0, "ankle_r": 0.0,
        "shoulder_l": 0.0, "shoulder_r": 0.0,
    })
    tendon_load: dict[str, float] = field(default_factory=lambda: {
        "achilles_l": 0.0, "achilles_r": 0.0, "patellar_l": 0.0, "patellar_r": 0.0,
    })
    skeleton: dict[str, float] = field(default_factory=lambda: {
        "pelvis_tilt": 0.0, "spine_flex": 0.0, "head_pitch": 0.0,
    })

    last_impact: float = 0.0
    last_forces: dict[str, float] = field(default_factory=dict)
    linear_momentum: float = 0.0
    angular_momentum: float = 0.0
    _jump_cooldown: int = 0

    WALK_FORCE = 420.0  # N → px/s² via F/m*scale
    RUN_FORCE = 680.0
    MU_GROUND = 0.62
    MU_WATER = 0.15
    CD_AIR = 0.08
    CD_WATER = 0.55

    def sync_pose(self, agent_x: float, agent_y: float) -> None:
        self.com_x = agent_x
        self.com_y = agent_y

    def _detect_environment(self, world) -> None:
        room = world.current_room()
        near_bath = room == "bano" or world._near_furniture("bath", 52)
        self.in_water = near_bath
        if near_bath:
            bath = world._furniture("bath")
            if bath:
                ax, ay = world.agent_x, world.agent_y
                cx = bath.x + bath.w / 2
                cy = bath.y + bath.h / 2
                in_tub = (
                    bath.x + 8 <= ax <= bath.x + bath.w - 8
                    and bath.y + 8 <= ay <= bath.y + bath.h - 8
                )
                if in_tub:
                    rel_y = float(np.clip((ay - bath.y) / max(bath.h, 1), 0, 1))
                    self.water_depth = float(np.clip(0.55 + (1.0 - rel_y) * 0.45, 0.4, 1.0))
                else:
                    self.water_depth = 0.25 if world._near_furniture("bath", 52) else 0.0
            else:
                self.water_depth = 0.5
            self.on_ground = self.height < 0.08 and self.water_depth < 0.35
        else:
            self.water_depth = 0.0
            self.buoyancy_n = 0.0

    def _apply_water_physics(self, weight_n: float) -> tuple[float, float, float]:
        """Flotabilidad de Arquímedes + arrastre hidrodinámico."""
        if not self.in_water or self.water_depth < 0.05:
            self.buoyancy_n = 0.0
            return 0.0, 0.0, 0.0

        submerged_vol = BODY_VOLUME_M3 * self.water_depth
        self.buoyancy_n = float(RHO_WATER * G * submerged_vol)
        net_up = self.buoyancy_n - weight_n * self.water_depth * 0.92

        fz = net_up / self.mass
        self.vz += fz * DT * 0.045
        self.vz *= 1.0 - self.CD_WATER * self.water_depth * DT * 0.35
        self.height += self.vz * DT
        self.height = float(np.clip(self.height, -0.15, 0.35))

        if self.height <= 0.0 and self.vz < 0:
            self.height = 0.0
            self.vz *= -0.15
            if abs(self.vz) > 0.8:
                self._apply_landing(abs(self.vz) * 2.5)

        drag_scale = 1.0 + self.CD_WATER * self.water_depth * 3.5
        return 0.0, 0.0, drag_scale

    def _motor_forces(
        self,
        motor: list[int],
        walk_goal: tuple[float, float] | None,
        agent_x: float,
        agent_y: float,
    ) -> tuple[float, float, float]:
        if self.ragdoll_active:
            return 0.0, 0.0, 0.0

        fx = fy = 0.0
        muscle = 0.0
        force = self.RUN_FORCE if self.gait == "run" else self.WALK_FORCE

        if walk_goal:
            gx, gy = walk_goal
            dx, dy = gx - agent_x, gy - agent_y
            dist = float(np.hypot(dx, dy))
            if dist > 6.0:
                fx += (dx / dist) * force
                fy += (dy / dist) * force
                muscle = max(muscle, 0.52)

        moves = {0: (-1.0, 0.0), 1: (1.0, 0.0), 2: (0.0, -1.0), 3: (0.0, 1.0)}
        for m in motor:
            if m in moves:
                ux, uy = moves[m]
                fx += ux * force
                fy += uy * force
                muscle = max(muscle, 0.48)

        return fx, fy, muscle

    def integrate(
        self,
        world,
        motor: list[int],
        *,
        walk_goal: tuple[float, float] | None = None,
    ) -> tuple[float, float, dict[str, Any]]:
        """Un paso físico: fuerzas → aceleración → velocidad → desplazamiento."""
        self.last_impact = 0.0
        self._detect_environment(world)
        agent_x, agent_y = world.agent_x, world.agent_y

        fx, fy, muscle = self._motor_forces(motor, walk_goal, agent_x, agent_y)

        weight_n = self.mass * G
        if self.in_water and self.water_depth > 0.05:
            _, _, drag_scale = self._apply_water_physics(weight_n)
            self.on_ground = self.height <= 0.02 and self.water_depth < 0.4
        else:
            drag_scale = 1.0
            if not self.on_ground:
                self.vz -= G * DT
                self.height += self.vz * DT
                if self.height <= 0.0:
                    impact_v = abs(self.vz)
                    self.height = 0.0
                    self.on_ground = True
                    self.vz = 0.0
                    if impact_v > 1.2:
                        self.last_impact = float(np.clip(impact_v / 6.0, 0, 1))
                        self._apply_landing(impact_v)
            elif muscle > 0.35 and self.physical_fatigue < 0.85 and not self.in_water:
                self._jump_cooldown = max(0, self._jump_cooldown - 1)
                if self.gait == "run" and muscle > 0.5 and self._jump_cooldown <= 0 and self.on_ground:
                    self.vz = 2.1
                    self.on_ground = False
                    self.height = 0.02
                    self._jump_cooldown = 36

        speed_px = float(np.hypot(self.vx, self.vy))
        speed_m = speed_px * PX_TO_M

        mu = self.MU_WATER if self.in_water else self.MU_GROUND
        if self.on_ground and speed_px > 0.5 and not (self.in_water and self.water_depth > 0.5):
            ff = mu * weight_n * (0.35 if self.in_water else 1.0)
            fx -= ff * (self.vx / speed_px)
            fy -= ff * (self.vy / speed_px)

        cd = self.CD_WATER if self.in_water else self.CD_AIR
        if speed_px > 0.5:
            drag = cd * speed_m * weight_n * 0.015 * drag_scale
            fx -= drag * (self.vx / speed_px)
            fy -= drag * (self.vy / speed_px)

        gain = 0.028 * (0.45 if self.in_water and self.water_depth > 0.5 else 1.0)
        # Walk-goal usable: prior físico más fuerte sin apagar biomecánica.
        if walk_goal is not None and muscle > 0.35:
            gain = max(gain, 0.12)
        self.ax = fx / self.mass * gain
        self.ay = fy / self.mass * gain

        self.vx += self.ax * DT
        self.vy += self.ay * DT

        # Gait from speed
        cap_walk = 9.5
        cap_run = 14.0
        sp = float(np.hypot(self.vx, self.vy))
        if not self.on_ground:
            self.gait = "fall" if self.vz < -0.5 else "jump"
        elif self.in_water and self.water_depth > 0.55:
            self.gait = "swim" if speed_px > 1.5 else "float"
        elif self.ragdoll_active:
            self.gait = "ragdoll"
        elif sp < 0.8:
            self.gait = "idle"
        elif sp < cap_walk:
            self.gait = "walk"
        else:
            self.gait = "run"
            if sp > cap_run:
                self.vx *= cap_run / sp
                self.vy *= cap_run / sp

        dx = self.vx * DT
        dy = self.vy * DT

        self.linear_momentum = self.mass * sp * PX_TO_M
        self.gait_phase = (self.gait_phase + 0.42 * (1.2 if self.gait == "run" else 1.0)) % 1.0
        self._update_skeleton(muscle, sp)
        self._update_biomechanics(muscle, sp)
        self._update_cardio(muscle, sp)

        meta = {
            "speed": round(sp, 2),
            "gait": self.gait,
            "impact": round(self.last_impact, 3),
            "forces": {k: round(v, 1) for k, v in self.last_forces.items()},
            "water_depth": round(self.water_depth, 3),
            "buoyancy_N": round(self.buoyancy_n, 1),
        }
        return dx, dy, meta

    def _update_skeleton(self, muscle: float, speed: float) -> None:
        art = self.skeleton_art
        if self.ragdoll_active:
            art.ragdoll_step(body_angle=self.body_angle, in_water=self.in_water)
        else:
            art.ragdoll_mode = False
            art.integrate_joints(self.gait, self.gait_phase, muscle)
        art.propagate_spine()
        sk_stress = art.joint_stress_map()
        for k, v in sk_stress.items():
            if k in self.joint_stress:
                self.joint_stress[k] = float(np.clip(max(self.joint_stress[k], v), 0, 1))
            elif k == "spine":
                self.joint_stress["spine"] = float(np.clip(v, 0, 1))
        self.skeleton["pelvis_tilt"] = art.pelvis_pitch
        self.skeleton["spine_flex"] = sum(art.spine_angles.values()) / max(len(art.spine_angles), 1)
        self.skeleton["head_pitch"] = float(art.spine_angles.get("cervical", 0))

    def _update_biomechanics(self, muscle: float, speed: float) -> None:
        act = float(np.clip(muscle + speed / 18.0, 0, 1))
        self.muscle_activation["quads"] = float(np.clip(act * 0.85, 0, 1))
        self.muscle_activation["hamstrings"] = float(np.clip(act * 0.65, 0, 1))
        self.muscle_activation["calves"] = float(np.clip(act * 0.55 + speed / 25.0, 0, 1))
        self.muscle_activation["glutes"] = float(np.clip(act * 0.7, 0, 1))
        self.muscle_activation["core"] = float(np.clip(0.25 + act * 0.45, 0, 1))
        self.muscle_activation["arms"] = float(np.clip(act * 0.35, 0, 1))

        stress = float(np.clip(speed / 16.0 + muscle * 0.4, 0, 1))
        for j in ("knee_l", "knee_r", "ankle_l", "ankle_r"):
            self.joint_stress[j] = float(np.clip(stress * 0.75, 0, 1))
        for j in ("hip_l", "hip_r"):
            self.joint_stress[j] = float(np.clip(stress * 0.55, 0, 1))
        self.joint_stress["spine"] = float(np.clip(stress * 0.35 + abs(self.angular_velocity) * 0.2, 0, 1))
        self.joint_stress["shoulder_l"] = self.joint_stress["shoulder_r"] = float(np.clip(act * 0.25, 0, 1))

        self.tendon_load["achilles_l"] = self.tendon_load["achilles_r"] = float(np.clip(stress * 0.6, 0, 1))
        self.tendon_load["patellar_l"] = self.tendon_load["patellar_r"] = float(np.clip(stress * 0.55, 0, 1))

        self.skeleton["pelvis_tilt"] = float(np.clip(act * 0.12, -0.3, 0.3))
        self.skeleton["spine_flex"] = float(np.clip(0.05 + stress * 0.15, 0, 0.4))
        self.skeleton["head_pitch"] = float(np.clip(self.ax * 0.002, -0.2, 0.2))

        # Equilibrio / centro de masa
        sway = abs(self.angular_velocity) + stress * 0.15
        self.equilibrium = float(np.clip(1.0 - sway - (0.4 if self.ragdoll_active else 0), 0, 1))
        self.angular_velocity *= 0.82
        self.angular_velocity += (self.ax - self.ay) * 0.0008
        self.body_angle = float(np.clip(self.body_angle + self.angular_velocity * DT, -0.6, 0.6))

        exertion = act * (1.2 if self.gait == "run" else 0.85)
        self.physical_fatigue = float(np.clip(self.physical_fatigue + exertion * 0.012 - 0.004, 0, 1))

        self.last_forces = {
            "weight_N": round(self.mass * G, 1),
            "muscle": round(act, 3),
            "momentum": round(self.linear_momentum, 2),
        }

    def _update_cardio(self, muscle: float, speed: float) -> None:
        load = float(np.clip(muscle + speed / 20.0 + self.physical_fatigue * 0.3, 0, 1))
        target_hr = 68.0 + load * 95.0 + (18.0 if self.gait == "run" else 0.0)
        self.heart_rate += (target_hr - self.heart_rate) * 0.18
        target_br = 12.0 + load * 22.0
        self.breath_rate += (target_br - self.breath_rate) * 0.15
        perf = 1.0 - self.physical_fatigue * 0.45
        self.blood_flow = float(np.clip(0.35 + (self.heart_rate / 180.0) * perf, 0.15, 1))

    def _apply_landing(self, impact_v: float) -> None:
        self.equilibrium = float(np.clip(self.equilibrium - impact_v * 0.08, 0, 1))
        entry = 0 if impact_v < 4 else 1
        self.skeleton_art.inject_spinal_shock(float(np.clip(impact_v / 5.0, 0.05, 0.9)), entry=entry)
        if impact_v > 3.5:
            self.ragdoll_active = True
            self.ragdoll_ticks = 10
            self.skeleton_art.ragdoll_mode = True
        for j in ("ankle_l", "ankle_r", "knee_l", "knee_r"):
            self.joint_stress[j] = float(np.clip(self.joint_stress.get(j, 0) + impact_v * 0.06, 0, 1))

    def collision_impulse(
        self,
        *,
        speed_before: float,
        region: str = "limbs",
        label: str = "",
    ) -> float:
        """Colisión → impulso, rebote, estrés articular, malestar."""
        impulse = float(np.clip(speed_before * 0.08, 0.02, 0.55))
        self.last_impact = impulse
        damp = 0.35 if self.ragdoll_active else 0.55
        self.vx *= -damp
        self.vy *= -damp
        self.angular_velocity += impulse * 0.4 * (1 if region == "head" else 0.6)
        self.equilibrium = float(np.clip(self.equilibrium - impulse * 0.5, 0, 1))
        if impulse > 0.25:
            self.ragdoll_active = True
            self.ragdoll_ticks = max(self.ragdoll_ticks, 6)
            self.skeleton_art.ragdoll_mode = True
        entry = 3 if region == "head" else (1 if region == "torso" else 0)
        self.skeleton_art.inject_spinal_shock(impulse * 0.85, entry=entry)
        reg = region if region in ("head", "torso", "limbs") else "limbs"
        if reg == "head":
            self.joint_stress["spine"] = float(np.clip(self.joint_stress["spine"] + impulse, 0, 1))
        else:
            for j in ("knee_l", "knee_r"):
                self.joint_stress[j] = float(np.clip(self.joint_stress[j] + impulse * 0.7, 0, 1))
        return impulse

    def tick_decay(self) -> None:
        if self.ragdoll_active:
            self.ragdoll_ticks -= 1
            if self.ragdoll_ticks <= 0:
                self.ragdoll_active = False
                self.skeleton_art.settle_ragdoll()
                self.equilibrium = float(np.clip(self.equilibrium + 0.15, 0, 1))
        if self.gait == "idle" and not self.in_water:
            self.vx *= 0.72
            self.vy *= 0.72

    def activity_strain(self) -> tuple[float, float]:
        sp = float(np.hypot(self.vx, self.vy))
        activity = float(np.clip(0.08 + sp / 22.0 + self.physical_fatigue * 0.25, 0.05, 1))
        strain = float(np.clip(1.0 + self.physical_fatigue * 0.35 + sum(self.joint_stress.values()) * 0.08, 0.8, 1.6))
        return activity, strain

    def apply_to_interoception(self, body, nociceptor) -> None:
        body.fatigue = float(np.clip(body.fatigue + self.physical_fatigue * 0.018 - 0.003, 0, 1))
        if self.gait == "run":
            body.body_temp = float(np.clip(body.body_temp + 0.004, 0, 1))
        if self.in_water:
            body.body_temp = float(np.clip(body.body_temp - 0.008, 0, 1))
            body.comfort = float(np.clip(body.comfort + 0.012 * self.water_depth, 0, 1))

        spine_wave = max(self.skeleton_art.spine_shock) if self.skeleton_art.spine_shock else 0
        if spine_wave > 0.25:
            nociceptor.transduce(
                region="torso",
                modality="mechanical",
                intensity=spine_wave * 0.55,
                label="onda de choque espinal",
            )

        max_stress = max(self.joint_stress.values()) if self.joint_stress else 0
        if max_stress > 0.35:
            nociceptor.transduce(
                region="limbs",
                modality="mechanical",
                intensity=max_stress * 0.45,
                label="estrés articular",
            )
        if self.last_impact > 0.01:
            nociceptor.apply_collision("limbs", self.last_impact, label="impacto")

        spine = self.joint_stress.get("spine", 0)
        if spine > 0.4:
            nociceptor.transduce(region="torso", modality="mechanical", intensity=spine * 0.35, label="columna")

        nociceptor._project_to_body(body)

    def encode(self, n: int) -> np.ndarray:
        vec = np.zeros(min(n, 14), dtype=np.float32)
        slots = [
            self.equilibrium,
            self.physical_fatigue,
            min(1.0, self.heart_rate / 180.0),
            min(1.0, self.breath_rate / 40.0),
            self.blood_flow,
            float(np.hypot(self.vx, self.vy) / 16.0),
            self.height * 2.0,
            1.0 if self.ragdoll_active else 0.0,
            max(self.joint_stress.values()) if self.joint_stress else 0,
            max(self.muscle_activation.values()) if self.muscle_activation else 0,
        ]
        for i, v in enumerate(slots):
            if i < vec.size:
                vec[i] = float(np.clip(v, 0, 1))
        m = float(vec.max())
        if m > 1e-6:
            vec /= m
        return vec

    def to_dict(self) -> dict[str, Any]:
        sp = float(np.hypot(self.vx, self.vy))
        return {
            "mass_kg": self.mass,
            "velocity": {"x": round(self.vx, 2), "y": round(self.vy, 2), "z": round(self.vz, 3)},
            "acceleration": {"x": round(self.ax, 2), "y": round(self.ay, 2)},
            "height_m": round(self.height, 3),
            "on_ground": self.on_ground,
            "in_water": self.in_water,
            "water_depth": round(self.water_depth, 3),
            "buoyancy_N": round(self.buoyancy_n, 1),
            "gait": self.gait,
            "gait_phase": round(self.gait_phase, 3),
            "equilibrium": round(self.equilibrium, 3),
            "center_of_mass": {"x": round(self.com_x, 1), "y": round(self.com_y, 1)},
            "linear_momentum": round(self.linear_momentum, 3),
            "angular_momentum": round(self.angular_momentum, 4),
            "body_angle": round(self.body_angle, 3),
            "speed": round(sp, 2),
            "ragdoll": self.ragdoll_active,
            "bones": self.skeleton_art.export_bones(),
            "spine_shock": [round(v, 3) for v in self.skeleton_art.spine_shock],
            "heart_rate_bpm": round(self.heart_rate, 1),
            "breath_rate": round(self.breath_rate, 1),
            "blood_flow": round(self.blood_flow, 3),
            "physical_fatigue": round(self.physical_fatigue, 3),
            "muscles": {k: round(v, 3) for k, v in self.muscle_activation.items()},
            "joints": {k: round(v, 3) for k, v in self.joint_stress.items()},
            "tendons": {k: round(v, 3) for k, v in self.tendon_load.items()},
            "skeleton": {k: round(v, 3) for k, v in self.skeleton.items()},
            "forces": dict(self.last_forces),
        }

    def load_dict(self, d: dict | None) -> None:
        if not d:
            return
        v = d.get("velocity") or {}
        self.vx = float(v.get("x", self.vx))
        self.vy = float(v.get("y", self.vy))
        self.vz = float(v.get("z", self.vz))
        self.height = float(d.get("height_m", self.height))
        self.gait = str(d.get("gait", self.gait))
        self.equilibrium = float(d.get("equilibrium", self.equilibrium))
        self.heart_rate = float(d.get("heart_rate_bpm", self.heart_rate))
        self.breath_rate = float(d.get("breath_rate", self.breath_rate))
        self.blood_flow = float(d.get("blood_flow", self.blood_flow))
        self.physical_fatigue = float(d.get("physical_fatigue", self.physical_fatigue))
        self.ragdoll_active = bool(d.get("ragdoll", self.ragdoll_active))
        self.water_depth = float(d.get("water_depth", self.water_depth))
        self.gait_phase = float(d.get("gait_phase", self.gait_phase))
        bones = d.get("bones")
        if isinstance(bones, dict):
            self.skeleton_art.load_bones(bones)
        shock = d.get("spine_shock")
        if isinstance(shock, list):
            self.skeleton_art.spine_shock = [float(x) for x in shock[:4]]
        for key, sub in (("muscles", self.muscle_activation), ("joints", self.joint_stress),
                         ("tendons", self.tendon_load), ("skeleton", self.skeleton)):
            block = d.get(key)
            if isinstance(block, dict):
                for k, val in block.items():
                    if k in sub:
                        sub[k] = float(val)
