#!/usr/bin/env python3
"""检查策略导出文件的完整性，用于Sim2Sim部署前的验证。"""

import argparse
import os
from pathlib import Path


def check_policy_export(policy_dir: str):
    """检查策略导出目录是否包含所有必需的文件。"""
    policy_path = Path(policy_dir).expanduser().resolve()
    
    if not policy_path.exists():
        print(f"❌ 错误: 策略目录不存在: {policy_path}")
        return False
    
    print(f"✓ 策略目录: {policy_path}")
    
    # 检查必需的文件
    required_files = {
        "exported/policy.onnx": "ONNX策略模型",
        "params/deploy.yaml": "部署配置文件",
    }
    
    all_exist = True
    for rel_path, description in required_files.items():
        file_path = policy_path / rel_path
        if file_path.exists():
            file_size = file_path.stat().st_size / (1024 * 1024)  # MB
            print(f"✓ {description}: {file_path} ({file_size:.2f} MB)")
        else:
            print(f"❌ 缺少文件: {file_path} ({description})")
            all_exist = False
    
    # 检查可选的文件
    optional_files = {
        "exported/policy.pt": "PyTorch JIT模型（可选）",
    }
    
    for rel_path, description in optional_files.items():
        file_path = policy_path / rel_path
        if file_path.exists():
            file_size = file_path.stat().st_size / (1024 * 1024)  # MB
            print(f"○ {description}: {file_path} ({file_size:.2f} MB)")
    
    # 检查deploy.yaml的内容
    deploy_yaml = policy_path / "params" / "deploy.yaml"
    if deploy_yaml.exists():
        try:
            import yaml
            with open(deploy_yaml, 'r') as f:
                cfg = yaml.safe_load(f)
            
            # 检查关键配置项
            required_keys = [
                "joint_ids_map",
                "step_dt",
                "stiffness",
                "damping",
                "actions",
                "observations",
            ]
            
            print("\n检查deploy.yaml配置项:")
            for key in required_keys:
                if key in cfg:
                    print(f"  ✓ {key}")
                else:
                    print(f"  ❌ 缺少配置项: {key}")
                    all_exist = False
            
            # 检查命令配置
            if "commands" in cfg and "base_velocity" in cfg["commands"]:
                print(f"  ✓ commands.base_velocity")
            else:
                print(f"  ⚠ commands.base_velocity (可选)")
            
        except Exception as e:
            print(f"⚠ 无法解析deploy.yaml: {e}")
    
    print("\n" + "="*60)
    if all_exist:
        print("✓ 所有必需文件都已就绪，可以用于Sim2Sim部署！")
        print(f"\n在config.yaml中设置:")
        print(f"  policy_dir: {policy_path}")
        print(f"  或相对路径（相对于deploy/robots/g1_29dof/config/）:")
        # 计算相对路径
        try:
            deploy_config_dir = Path(__file__).parent.parent / "deploy" / "robots" / "g1_29dof" / "config"
            if deploy_config_dir.exists():
                rel_path = os.path.relpath(policy_path, deploy_config_dir)
                print(f"  policy_dir: {rel_path}")
        except:
            pass
    else:
        print("❌ 缺少必需文件，请先导出策略！")
        print("\n运行以下命令导出策略:")
        print("  python scripts/rsl_rl/play.py --task Unitree-G1-29dof-Velocity --checkpoint <checkpoint_path>")
    
    return all_exist


def main():
    parser = argparse.ArgumentParser(description="检查策略导出文件")
    parser.add_argument(
        "policy_dir",
        type=str,
        help="策略目录路径（包含exported和params文件夹）",
    )
    
    args = parser.parse_args()
    check_policy_export(args.policy_dir)


if __name__ == "__main__":
    main()











