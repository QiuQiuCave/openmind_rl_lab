"""
Script to export R2 locomotion policy to ONNX with metadata.
Usage: python scripts/export_r2_policy_manual.py --headless
"""

import argparse
import os
import pickle
import sys

# 1. Launch Isaac Sim first
from isaaclab.app import AppLauncher

# Create the parser and handle arguments
parser = argparse.ArgumentParser(description="Export R2 Policy to ONNX")
# Add standard Isaac Lab args (like --headless)
AppLauncher.add_app_launcher_args(parser)
# Parse arguments
args_cli = parser.parse_args()

# Launch the app
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

# 2. Imports after app launch (Standard Isaac Lab pattern)
import gymnasium as gym
import torch

from rsl_rl.runners import OnPolicyRunner
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
import unitree_rl_lab.tasks  # Register tasks
from unitree_rl_lab.utils.r2_loco_onnx_exporter import (
    export_r2_locomotion_policy_as_onnx,
    attach_r2_locomotion_metadata
)

def main():
    # --- Configuration ---
    run_dir = os.path.abspath("logs/rsl_rl/unitree_r2_velocity/2025-11-07_14-33-25")
    checkpoint_file = "model_20000.pt"
    checkpoint_path = os.path.join(run_dir, checkpoint_file)
    export_folder = "exported_onnx"
    task_name = "Openmind-R2-Velocity" # Default task name for R2 velocity

    print(f"[INFO] Run Directory: {run_dir}")
    print(f"[INFO] Checkpoint: {checkpoint_path}")

    if not os.path.exists(checkpoint_path):
        print(f"[ERROR] Checkpoint not found at {checkpoint_path}")
        return

    # --- Load Configuration ---
    # We load the env config used during training to ensure consistency
    env_cfg_path = os.path.join(run_dir, "params", "env.pkl")
    agent_cfg_path = os.path.join(run_dir, "params", "agent.pkl")

    if not os.path.exists(env_cfg_path):
        print(f"[ERROR] Env config not found at {env_cfg_path}")
        return

    print(f"[INFO] Loading env config from: {env_cfg_path}")
    with open(env_cfg_path, "rb") as f:
        env_cfg = pickle.load(f)

    print(f"[INFO] Loading agent config from: {agent_cfg_path}")
    with open(agent_cfg_path, "rb") as f:
        agent_cfg = pickle.load(f)

    # --- Setup Environment ---
    # Set num_envs to 1 for export (we only need the structure)
    env_cfg.scene.num_envs = 1
    print(f"[INFO] Creating environment: {task_name}")
    # Render mode None for speed/headless
    env = gym.make(task_name, cfg=env_cfg, render_mode=None)
    
    # Wrap for RSL-RL (normalization, clipping, etc.)
    env = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)

    # --- Load Policy ---
    print(f"[INFO] Loading RSL-RL runner...")
    # Initialize runner
    runner = OnPolicyRunner(env, agent_cfg.to_dict(), log_dir=None, device=agent_cfg.device)
    
    # Load weights
    print(f"[INFO] Loading weights from {checkpoint_path}")
    runner.load(checkpoint_path)

    # Extract Policy Network
    # Handle different RSL-RL versions
    if hasattr(runner.alg, "policy"):
        policy_nn = runner.alg.policy
    else:
        policy_nn = runner.alg.actor_critic
    
    policy_nn.eval()
    
    # --- Export to ONNX ---
    export_path = os.path.join(run_dir, export_folder)
    onnx_filename = "policy.onnx"
    
    print(f"[INFO] Exporting to directory: {export_path}")
    
    # We need the unwrapped ManagerBasedRLEnv for metadata extraction
    base_env = env.unwrapped
    
    # 1. Export the model
    export_r2_locomotion_policy_as_onnx(
        env=base_env,
        actor_critic=policy_nn,
        path=export_path,
        filename=onnx_filename,
        normalizer=runner.obs_normalizer,
        verbose=True,
        obs_full=False, # Standard concatenated observation
    )

    # 2. Attach Metadata (Crucial for Sim2Real)
    print(f"[INFO] Attaching metadata to ONNX...")
    attach_r2_locomotion_metadata(
        env=base_env,
        run_path=run_dir,
        path=export_path,
        filename=onnx_filename
    )

    print(f"[SUCCESS] Export complete!")
    print(f"File saved at: {os.path.join(export_path, onnx_filename)}")

    # Cleanup
    env.close()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERROR] Exception occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        simulation_app.close()
