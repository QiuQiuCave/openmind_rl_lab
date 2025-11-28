"""Utilities to export R2 locomotion policies to ONNX with rich metadata."""

from __future__ import annotations

import os
from typing import Any, Iterable

import onnx
import torch

from isaaclab.envs import ManagerBasedRLEnv
from isaaclab_rl.rsl_rl.exporter import _OnnxPolicyExporter


def export_r2_locomotion_policy_as_onnx(
    env: ManagerBasedRLEnv,
    actor_critic: torch.nn.Module,
    path: str,
    *,
    filename: str = "policy.onnx",
    normalizer: torch.nn.Module | None = None,
    verbose: bool = False,
    obs_full: bool = False,
) -> None:
    """Export a locomotion policy (trained on R2) to ONNX format.

    Parameters
    ----------
    env:
        The fully constructed Isaac Lab environment that the policy was trained on.
    actor_critic:
        The policy network (usually coming from an RslRl OnPolicyRunner).
    path:
        Directory where the ONNX file should be written. It will be created if missing.
    filename:
        Name of the ONNX file. Defaults to ``policy.onnx``.
    normalizer:
        Optional observation normalizer module used during training.
    verbose:
        Whether to enable verbose output inside ``torch.onnx.export``.
    obs_full:
        When ``True`` every observation term becomes an individual ONNX input.
        When ``False`` the exporter expects a single concatenated observation vector.
    """

    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

    exporter = _OnnxR2LocomotionPolicyExporter(env, actor_critic, normalizer, verbose, obs_full)
    exporter.export(path, filename)


class _OnnxR2LocomotionPolicyExporter(_OnnxPolicyExporter):
    """Thin wrapper around ``_OnnxPolicyExporter`` with custom R2 handling."""

    def __init__(
        self,
        env: ManagerBasedRLEnv,
        actor_critic: torch.nn.Module,
        normalizer: torch.nn.Module | None = None,
        verbose: bool = False,
        obs_full: bool = False,
    ) -> None:
        super().__init__(actor_critic, normalizer, verbose)
        self.env = env
        self.obs_full = obs_full
        (
            self.observation_names,
            self.observation_dims,
            self.observation_history_lengths,
        ) = _collect_observation_specs(env)
        # Pre-compute the flattened observation dimension so we do not rely on
        # specific actor implementations exposing ``in_features``.
        self.concatenated_obs_dim = sum(self.observation_dims)

    def forward(self, *args: torch.Tensor) -> torch.Tensor:
        if self.obs_full:
            obs = torch.cat(args, dim=-1)
        else:
            if len(args) != 1:
                raise ValueError("Expected a single concatenated observation tensor when obs_full=False.")
            obs = args[0]
        return self.actor(self.normalizer(obs))

    def export(self, path: str, filename: str) -> None:
        self.to("cpu")
        onnx_path = os.path.join(path, filename)

        if self.obs_full:
            dummy_inputs = []
            input_names = []
            for name, dim in zip(self.observation_names, self.observation_dims):
                dummy_inputs.append(torch.zeros(1, dim))
                input_names.append(name)

            torch.onnx.export(
                self,
                tuple(dummy_inputs),
                onnx_path,
                export_params=True,
                opset_version=11,
                verbose=self.verbose,
                input_names=input_names,
                output_names=["actions"],
                dynamic_axes={},
            )
        else:
            obs = torch.zeros(1, self.concatenated_obs_dim)
            torch.onnx.export(
                self,
                (obs,),
                onnx_path,
                export_params=True,
                opset_version=11,
                verbose=self.verbose,
                input_names=["obs"],
                output_names=["actions"],
                dynamic_axes={},
            )


def attach_r2_locomotion_metadata(
    env: ManagerBasedRLEnv,
    run_path: str,
    path: str,
    *,
    filename: str = "policy.onnx",
    extra_metadata: dict[str, Any] | None = None,
) -> None:
    """Append deployment metadata to an exported ONNX policy."""

    onnx_path = os.path.join(path, filename)
    metadata = _collect_metadata(env, run_path)
    if extra_metadata:
        metadata.update(extra_metadata)

    model = onnx.load(onnx_path)
    # Drop duplicated keys so re-running does not grow the metadata list.
    preserved = [entry for entry in model.metadata_props if entry.key not in metadata]
    model.ClearField("metadata_props")
    model.metadata_props.extend(preserved)

    for key, value in metadata.items():
        entry = onnx.StringStringEntryProto()
        entry.key = key
        entry.value = (
            list_to_csv_str(value)
            if isinstance(value, (list, tuple))
            else str(value)
        )
        model.metadata_props.append(entry)

    onnx.save(model, onnx_path)


def _collect_observation_specs(env: ManagerBasedRLEnv) -> tuple[list[str], list[int], list[int]]:
    obs_names = list(env.observation_manager.active_terms["policy"])
    group_obs_term_dim = env.observation_manager._group_obs_term_dim["policy"]
    obs_dims = [dims[-1] for dims in group_obs_term_dim]

    history_lengths: list[int] = []
    policy_cfg = env.observation_manager.cfg.policy
    if getattr(policy_cfg, "history_length", None) is not None:
        history_lengths = [policy_cfg.history_length] * len(obs_names)
    else:
        cfg_dict = policy_cfg.to_dict()
        for name in obs_names:
            length = cfg_dict[name]["history_length"]
            history_lengths.append(1 if length == 0 else length)

    return obs_names, obs_dims, history_lengths


def _collect_metadata(env: ManagerBasedRLEnv, run_path: str) -> dict[str, Any]:
    robot = env.scene["robot"].data
    obs_names, obs_dims, obs_history = _collect_observation_specs(env)
    action_term_name, action_term = _resolve_action_term(env)

    metadata = {
        "run_path": run_path,
        "task_cfg": env.cfg.__class__.__name__,
        "sim_dt": env.cfg.sim.dt,
        "decimation": env.cfg.decimation,
        "control_dt": env.cfg.sim.dt * env.cfg.decimation,
        "joint_names": list(robot.joint_names),
        "body_names": list(robot.body_names),
        "joint_stiffness": robot.default_joint_stiffness[0].detach().cpu().tolist(),
        "joint_damping": robot.default_joint_damping[0].detach().cpu().tolist(),
        "default_joint_pos": robot.default_joint_pos[0].detach().cpu().tolist(),
        "command_terms": _resolve_command_terms(env),
        "observation_names": obs_names,
        "observation_dims": obs_dims,
        "observation_history_lengths": obs_history,
        "action_term": action_term_name,
    }

    if hasattr(action_term, "_scale"):
        metadata["action_scale"] = _metadata_array(action_term._scale)
    if hasattr(action_term, "_offset"):
        metadata["action_offset"] = _metadata_array(action_term._offset)
    if hasattr(action_term, "_clip") and action_term._clip is not None:
        metadata["action_clip"] = _metadata_array(action_term._clip)

    return metadata


def _resolve_action_term(env: ManagerBasedRLEnv) -> tuple[str, Any]:
    preferred = ("JointPositionAction", "JointVelocityAction")
    for name in preferred:
        if name in env.action_manager._terms:  # type: ignore[attr-defined]
            return name, env.action_manager.get_term(name)

    for name in env.action_manager.active_terms:
        return name, env.action_manager.get_term(name)

    raise RuntimeError("No action terms registered in the action manager.")


def _resolve_command_terms(env: ManagerBasedRLEnv) -> list[str]:
    terms = getattr(env.command_manager, "active_terms", None)
    if terms is not None:
        if isinstance(terms, dict):
            return list(terms.keys())
        try:
            return list(terms)
        except TypeError:
            return [str(terms)]

    commands_cfg = getattr(env.cfg, "commands", None)
    if commands_cfg is None:
        return []
    try:
        attrs = vars(commands_cfg).keys()
    except TypeError:
        attrs = [name for name in dir(commands_cfg) if not name.startswith("_")]
        return list(attrs)

    return [name for name in attrs if not name.startswith("_")]


def list_to_csv_str(arr: Iterable[Any], *, decimals: int = 6, delimiter: str = ",") -> str:
    fmt = f"{{:.{decimals}f}}"
    serialized = []
    for item in arr:
        if isinstance(item, (int, float)):
            serialized.append(fmt.format(item))
        else:
            serialized.append(str(item))
    return delimiter.join(serialized)


def _metadata_array(value: Any) -> list[Any]:
    """Convert tensors / arrays / scalars into metadata-friendly lists."""
    if isinstance(value, torch.Tensor):
        tensor = value.detach().cpu()
        if tensor.ndim > 1:
            tensor = tensor[0]
        return tensor.tolist()
    if hasattr(value, "tolist"):
        data = value.tolist()
        if isinstance(data, list):
            if data and isinstance(data[0], list):
                return data[0]
            return data
        return [data]
    if isinstance(value, (list, tuple)):
        if value and isinstance(value[0], (list, tuple)):
            return list(value[0])
        return list(value)
    return [value]


__all__ = [
    "attach_r2_locomotion_metadata",
    "export_r2_locomotion_policy_as_onnx",
]
