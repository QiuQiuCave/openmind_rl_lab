# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Configuration for Openmind R2V2 robot.

This is a third-party humanoid robot configuration based on the R2V2 model
(with hand fixed).
"""

import isaaclab.sim as sim_utils
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.assets.articulation import ArticulationCfg

from unitree_rl_lab.assets.robots.unitree import UnitreeArticulationCfg


OPENMIND_MODEL_DIR = "/root/qzy_workspace/assetslib/third_party"

# All revolute joints in the USD (must match asset.data.joint_names exactly for export_deploy_cfg).
# In the "hand_fixed" variant, upper-body joints (arms, hands, fingers, head) are fixed;
# only the 14 leg + waist revolute joints remain.
OPENMIND_R2V2_JOINT_NAMES = [
    # 12 leg joints
    "left_hip_pitch_joint",
    "left_hip_roll_joint",
    "left_hip_yaw_joint",
    "left_knee_joint",
    "left_ankle_pitch_joint",
    "left_ankle_roll_joint",
    "right_hip_pitch_joint",
    "right_hip_roll_joint",
    "right_hip_yaw_joint",
    "right_knee_joint",
    "right_ankle_pitch_joint",
    "right_ankle_roll_joint",
    # 2 waist joints
    "waist_yaw_joint",
    "waist_pitch_joint",
]

OPENMIND_R2V2_INIT_JOINT_POS = {
    **{name: 0.0 for name in OPENMIND_R2V2_JOINT_NAMES},
    # slight crouch pose for stable standing
    "left_hip_pitch_joint": -0.1,
    "left_knee_joint": 0.3,
    "left_ankle_pitch_joint": -0.2,
    "right_hip_pitch_joint": -0.1,
    "right_knee_joint": 0.3,
    "right_ankle_pitch_joint": -0.2,
}

OPENMIND_R2V2_STIFFNESS = {
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
}

OPENMIND_R2V2_DAMPING = {
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
}

OPENMIND_R2V2_EFFORT = {
    "left_hip_pitch_joint": 150.0,
    "left_hip_roll_joint": 130.0,
    "left_hip_yaw_joint": 130.0,
    "left_knee_joint": 150.0,
    "left_ankle_pitch_joint": 75.0,
    "left_ankle_roll_joint": 75.0,
    "right_hip_pitch_joint": 150.0,
    "right_hip_roll_joint": 130.0,
    "right_hip_yaw_joint": 130.0,
    "right_knee_joint": 150.0,
    "right_ankle_pitch_joint": 75.0,
    "right_ankle_roll_joint": 75.0,
    "waist_yaw_joint": 130.0,
    "waist_pitch_joint": 130.0,
}

##
# Configuration
##

OPENMIND_R2V2_CFG = UnitreeArticulationCfg(
    spawn=sim_utils.UsdFileCfg(
        usd_path=f"{OPENMIND_MODEL_DIR}/r2_v2_with_hand_fixed/usd/r2_v2_with_hand_fixed.usd",
        activate_contact_sensors=True,
        rigid_props=sim_utils.RigidBodyPropertiesCfg(
            disable_gravity=False,
            retain_accelerations=False,
            linear_damping=0.0,
            angular_damping=0.0,
            max_linear_velocity=1000.0,
            max_angular_velocity=1000.0,
            max_depenetration_velocity=1.0,
        ),
        articulation_props=sim_utils.ArticulationRootPropertiesCfg(
            fix_root_link=False,
            enabled_self_collisions=False,
            solver_position_iteration_count=4,
            solver_velocity_iteration_count=4,
        ),
    ),
    init_state=ArticulationCfg.InitialStateCfg(
        pos=(0.0, 0.0, 0.665),
        joint_pos=OPENMIND_R2V2_INIT_JOINT_POS,
        joint_vel={".*": 0.0},
    ),
    soft_joint_pos_limit_factor=1.0,
    actuators={
        "r2v2_motors": ImplicitActuatorCfg(
            joint_names_expr=[".*"],
            effort_limit_sim=OPENMIND_R2V2_EFFORT,
            stiffness=OPENMIND_R2V2_STIFFNESS,
            damping=OPENMIND_R2V2_DAMPING,
            armature=0.01,
        ),
    },
    joint_sdk_names=OPENMIND_R2V2_JOINT_NAMES.copy(),
)

"""Configuration for the Openmind R2V2 Humanoid robot (with hand fixed)."""
