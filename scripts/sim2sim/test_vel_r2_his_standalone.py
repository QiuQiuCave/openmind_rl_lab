#!/usr/bin/env python3
"""Standalone runner for the Unitree R2 sim2sim velocity policy.

This script mirrors the configuration from ``test_vel_r2_his.py`` but keeps all
runtime parameters in a single file so it can be copied into other projects.
Override values with command-line arguments when integrating elsewhere.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

import numpy as np

from sim2simlib import SIM2SIMLIB_ASSETS_DIR
from sim2simlib.model.actuator_motor import PIDMotor
from sim2simlib.model.config import (
    Actions_Config,
    Motor_Config,
    Observations_Config,
    Sim2Sim_Config,
)
from sim2simlib.model.sim2sim_base import Sim2SimBaseModel

try:
    from sim2simlib.utils.config import load_from_yaml as _load_from_yaml
except ImportError:  # pragma: no cover - optional dependency
    _load_from_yaml = None


DEFAULT_CKPT_DIR = Path(
    "/home/qiuziyu/code/unitree_rl_lab/logs/rsl_rl/unitree_r2_velocity"
) / "2025-11-07_14-33-25"

DEFAULT_XML_PATH = Path(SIM2SIMLIB_ASSETS_DIR) / "third_party/r2_wholebody/mjcf/r2_wb.xml"

POLICY_JOINT_NAMES = [
    "left_hip_pitch_joint",
    "right_hip_pitch_joint",
    "waist_yaw_joint",
    "left_hip_roll_joint",
    "right_hip_roll_joint",
    "waist_pitch_joint",
    "left_hip_yaw_joint",
    "right_hip_yaw_joint",
    "left_shoulder_pitch_joint",
    "right_shoulder_pitch_joint",
    "left_knee_joint",
    "right_knee_joint",
    "left_shoulder_roll_joint",
    "right_shoulder_roll_joint",
    "left_ankle_pitch_joint",
    "right_ankle_pitch_joint",
    "left_shoulder_yaw_joint",
    "right_shoulder_yaw_joint",
    "left_ankle_roll_joint",
    "right_ankle_roll_joint",
    "left_arm_pitch_joint",
    "right_arm_pitch_joint",
]

DEFAULT_CMD = (0.8, 0.0, 0.0)

DEFAULT_ENV_PARAMS = {
    "simulation_dt": 0.005,
    "control_decimation": 4,
    "action_scale": 0.25,
    "obs_history_length": 5,
}

DEFAULT_BASE_POSITION = np.array([0.0, 0.0, 0.665], dtype=np.float32)
DEFAULT_ANGLES = {
    "left_hip_pitch_joint": -0.1,
    "right_hip_pitch_joint": -0.1,
    ".*_knee_joint": 0.3,
    ".*_ankle_pitch_joint": -0.2,
}

MOTOR_EFFORT_LIMIT = {
    "left_hip_pitch_joint": 130.0,
    "left_hip_roll_joint": 130.0,
    "left_hip_yaw_joint": 90.0,
    "left_knee_joint": 150.0,
    "left_ankle_pitch_joint": 75.0,
    "left_ankle_roll_joint": 75.0,
    "right_hip_pitch_joint": 130.0,
    "right_hip_roll_joint": 130.0,
    "right_hip_yaw_joint": 90.0,
    "right_knee_joint": 150.0,
    "right_ankle_pitch_joint": 75.0,
    "right_ankle_roll_joint": 75.0,
    "waist_yaw_joint": 90.0,
    "waist_pitch_joint": 90.0,
    "left_shoulder_pitch_joint": 36.0,
    "left_shoulder_roll_joint": 36.0,
    "left_shoulder_yaw_joint": 36.0,
    "left_arm_pitch_joint": 36.0,
    "right_shoulder_pitch_joint": 36.0,
    "right_shoulder_roll_joint": 36.0,
    "right_shoulder_yaw_joint": 36.0,
    "right_arm_pitch_joint": 36.0,
}

MOTOR_STIFFNESS = {
    "left_hip_pitch_joint": 100.0,
    "left_hip_roll_joint": 100.0,
    "left_hip_yaw_joint": 100.0,
    "left_knee_joint": 150.0,
    "left_ankle_pitch_joint": 30.0,
    "left_ankle_roll_joint": 30.0,
    "right_hip_pitch_joint": 100.0,
    "right_hip_roll_joint": 100.0,
    "right_hip_yaw_joint": 100.0,
    "right_knee_joint": 150.0,
    "right_ankle_pitch_joint": 30.0,
    "right_ankle_roll_joint": 30.0,
    "waist_yaw_joint": 300.0,
    "waist_pitch_joint": 300.0,
    "left_shoulder_pitch_joint": 100.0,
    "left_shoulder_roll_joint": 100.0,
    "left_shoulder_yaw_joint": 50.0,
    "left_arm_pitch_joint": 50.0,
    "right_shoulder_pitch_joint": 100.0,
    "right_shoulder_roll_joint": 100.0,
    "right_shoulder_yaw_joint": 50.0,
    "right_arm_pitch_joint": 50.0,
}

MOTOR_DAMPING = {
    "left_hip_pitch_joint": 5.0,
    "left_hip_roll_joint": 5.0,
    "left_hip_yaw_joint": 5.0,
    "left_knee_joint": 7.0,
    "left_ankle_pitch_joint": 3.0,
    "left_ankle_roll_joint": 3.0,
    "right_hip_pitch_joint": 5.0,
    "right_hip_roll_joint": 5.0,
    "right_hip_yaw_joint": 5.0,
    "right_knee_joint": 7.0,
    "right_ankle_pitch_joint": 3.0,
    "right_ankle_roll_joint": 3.0,
    "waist_yaw_joint": 3.0,
    "waist_pitch_joint": 3.0,
    "left_shoulder_pitch_joint": 2.0,
    "left_shoulder_roll_joint": 2.0,
    "left_shoulder_yaw_joint": 2.0,
    "left_arm_pitch_joint": 2.0,
    "right_shoulder_pitch_joint": 2.0,
    "right_shoulder_roll_joint": 2.0,
    "right_shoulder_yaw_joint": 2.0,
    "right_arm_pitch_joint": 2.0,
}

ACTION_CLIP = (-100.0, 100.0)

BASE_OBS_TERMS = [
    "base_ang_vel",
    "gravity_orientation",
    "cmd",
    "joint_pos",
    "joint_vel",
    "last_action",
]

BASE_OBS_SCALES = {
    "base_ang_vel": 0.2,
    "cmd": 1.0,
    "gravity_orientation": 1.0,
    "joint_pos": 1.0,
    "joint_vel": 0.05,
    "last_action": 1.0,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Unitree R2 sim2sim policy with inline configuration.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--ckpt-dir",
        type=Path,
        default=DEFAULT_CKPT_DIR,
        help="Directory that contains exported/policy.pt (used if --policy is not given).",
    )
    parser.add_argument(
        "--policy",
        type=Path,
        default=None,
        help="Explicit path to the scripted policy file (overrides --ckpt-dir).",
    )
    parser.add_argument(
        "--xml-path",
        type=Path,
        default=DEFAULT_XML_PATH,
        help="Path to the MuJoCo XML describing the R2 robot.",
    )
    parser.add_argument(
        "--env-yaml",
        type=Path,
        default=None,
        help="Optional env.yaml path to pull dt/decimation/action-scale/history values.",
    )
    parser.add_argument(
        "--sim-dt",
        type=float,
        default=None,
        help="Override the physics simulation timestep.",
    )
    parser.add_argument(
        "--decimation",
        type=int,
        default=None,
        help="Override the control decimation applied to the policy.",
    )
    parser.add_argument(
        "--action-scale",
        type=float,
        default=None,
        help="Override the JointPositionAction scale.",
    )
    parser.add_argument(
        "--obs-history-length",
        type=int,
        default=None,
        help="Number of history frames to keep for observations.",
    )
    parser.add_argument(
        "--cmd",
        type=float,
        nargs=3,
        metavar=("VX", "VY", "YAW"),
        default=None,
        help="Base velocity command fed into the policy.",
    )
    parser.add_argument(
        "--slowdown",
        type=float,
        default=1.0,
        help="Slowdown factor applied when rendering with the viewer.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run without launching the MuJoCo viewer.",
    )
    parser.add_argument(
        "--camera-tracking",
        action="store_true",
        help="Enable camera tracking when the viewer is running.",
    )
    parser.add_argument(
        "--camera-body",
        type=str,
        default="torso",
        help="Body name to follow when camera tracking is enabled.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging inside the sim2sim model.",
    )
    return parser.parse_args()


def _resolve_policy_path(ckpt_dir: Path | None, policy_path: Path | None) -> Path:
    if policy_path is not None:
        candidate = policy_path.expanduser()
    else:
        if ckpt_dir is None:
            raise ValueError("Either --policy or --ckpt-dir must be provided.")
        candidate = ckpt_dir.expanduser() / "exported" / "policy.pt"
    if not candidate.is_file():
        raise FileNotFoundError(f"Policy file not found at: {candidate}")
    return candidate


def _resolve_xml_path(xml_path: Path) -> Path:
    candidate = xml_path.expanduser()
    if not candidate.is_file():
        raise FileNotFoundError(f"MuJoCo XML not found at: {candidate}")
    return candidate


def _load_env_scalars_from_yaml(yaml_path: Path) -> dict[str, float]:
    if _load_from_yaml is None:
        raise RuntimeError(
            "--env-yaml was provided but PyYAML/sim2simlib loader is unavailable."
        )
    candidate = yaml_path.expanduser()
    if not candidate.is_file():
        raise FileNotFoundError(f"env.yaml not found at: {candidate}")
    env_cfg = _load_from_yaml(str(candidate))
    try:
        return {
            "simulation_dt": env_cfg["sim"]["dt"],
            "control_decimation": env_cfg["decimation"],
            "action_scale": env_cfg["actions"]["JointPositionAction"]["scale"],
            "obs_history_length": env_cfg["observations"]["policy"]["history_length"],
        }
    except KeyError as exc:
        raise KeyError(f"Missing key {exc} in {candidate}") from exc


def _resolve_env_params(args: argparse.Namespace) -> dict[str, float]:
    params = DEFAULT_ENV_PARAMS.copy()
    if args.env_yaml is not None:
        params.update(_load_env_scalars_from_yaml(args.env_yaml))
    if args.sim_dt is not None:
        params["simulation_dt"] = args.sim_dt
    if args.decimation is not None:
        params["control_decimation"] = args.decimation
    if args.action_scale is not None:
        params["action_scale"] = args.action_scale
    if args.obs_history_length is not None:
        params["obs_history_length"] = args.obs_history_length
    return params


def _resolve_cmd(cmd: Sequence[float] | None) -> list[float]:
    return list(cmd) if cmd is not None else list(DEFAULT_CMD)


def build_sim2sim_config(
    args: argparse.Namespace, policy_path: Path, xml_path: Path
) -> Sim2Sim_Config:
    env_params = _resolve_env_params(args)
    observation_cfg = Observations_Config(
        base_observations_terms=list(BASE_OBS_TERMS),
        scale=BASE_OBS_SCALES.copy(),
        using_base_obs_history=True,
        base_obs_his_length=env_params["obs_history_length"],
    )
    motor_cfg = Motor_Config(
        motor_type=PIDMotor,
        effort_limit=MOTOR_EFFORT_LIMIT.copy(),
        stiffness=MOTOR_STIFFNESS.copy(),
        damping=MOTOR_DAMPING.copy(),
    )
    action_cfg = Actions_Config(
        scale=env_params["action_scale"],
        action_clip=ACTION_CLIP,
    )
    cmd = _resolve_cmd(args.cmd)
    return Sim2Sim_Config(
        robot_name="r2_wholebody",
        simulation_dt=env_params["simulation_dt"],
        control_decimation=env_params["control_decimation"],
        slowdown_factor=args.slowdown,
        xml_path=str(xml_path),
        policy_path=str(policy_path),
        policy_joint_names=list(POLICY_JOINT_NAMES),
        observation_cfg=observation_cfg,
        cmd=cmd,
        action_cfg=action_cfg,
        motor_cfg=motor_cfg,
        default_pos=DEFAULT_BASE_POSITION.copy(),
        default_angles=DEFAULT_ANGLES.copy(),
        debug=args.debug,
        camera_tracking=args.camera_tracking and not args.headless,
        camera_tracking_body=args.camera_body,
    )


def main() -> None:
    args = parse_args()
    ckpt_dir = args.ckpt_dir.expanduser() if args.ckpt_dir is not None else None
    policy_path = _resolve_policy_path(ckpt_dir, args.policy)
    xml_path = _resolve_xml_path(args.xml_path)
    config = build_sim2sim_config(args, policy_path, xml_path)
    mujoco_model = Sim2SimBaseModel(config)
    if args.headless:
        mujoco_model.headless_run()
    else:
        mujoco_model.view_run()


if __name__ == "__main__":
    main()

