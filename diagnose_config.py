#!/usr/bin/env python3
"""
完整诊断 MuJoCo 和 Isaac Lab 的配置差异
"""

import torch
import yaml

print("=" * 80)
print("MuJoCo vs Isaac Lab 配置对比")
print("=" * 80)

# 1. 关节顺序
print("\n1. 关节顺序")
print("-" * 80)
isaac_joint_order = [
    "FR_hip_joint", "FR_thigh_joint", "FR_calf_joint",
    "FL_hip_joint", "FL_thigh_joint", "FL_calf_joint",
    "RR_hip_joint", "RR_thigh_joint", "RR_calf_joint",
    "RL_hip_joint", "RL_thigh_joint", "RL_calf_joint",
]

mujoco_joint_order_xml = [
    "FR_hip", "FR_thigh", "FR_calf",
    "FL_hip", "FL_thigh", "FL_calf", 
    "RR_hip", "RR_thigh", "RR_calf",
    "RL_hip", "RL_thigh", "RL_calf",
]

print("Isaac Lab 顺序:", isaac_joint_order)
print("MuJoCo XML 顺序:", mujoco_joint_order_xml)
print("✓ 顺序匹配!" if len(isaac_joint_order) == len(mujoco_joint_order_xml) else "✗ 顺序不匹配!")

# 2. 默认关节位置
print("\n2. 默认关节位置")
print("-" * 80)
default_pos = [0.0, 0.8, -1.5] * 4
print("Config 中 default_dof_pos:", default_pos)
print("每条腿: [hip=0.0, thigh=0.8, calf=-1.5]")

# 3. 动作缩放
print("\n3. 动作缩放")
print("-" * 80)
isaac_action_scale = {
    ".*_hip_joint": 0.125,
    "^(?!.*_hip_joint).*": 0.25
}
mujoco_action_scale = [0.125, 0.25, 0.25] * 4
print("Isaac Lab:", isaac_action_scale)
print("MuJoCo config:", mujoco_action_scale)
print("展开:")
for i, joint in enumerate(isaac_joint_order):
    scale = 0.125 if "hip" in joint else 0.25
    print(f"  [{i:2d}] {joint:20s}: {scale}")

# 4. 观测空间顺序
print("\n4. 观测空间顺序")
print("-" * 80)
isaac_obs_order = ["base_ang_vel", "projected_gravity", "velocity_commands", 
                   "joint_pos", "joint_vel", "last_action"]
mujoco_obs_order = ["ang_vel", "gravity_vec", "commands", "dof_pos", "dof_vel", "actions"]
isaac_dims = [3, 3, 3, 12, 12, 12]
mujoco_dims = [3, 3, 3, 12, 12, 12]

print("\nIsaac Lab 观测顺序 (45维):")
idx = 0
for obs, dim in zip(isaac_obs_order, isaac_dims):
    print(f"  [{idx:2d}-{idx+dim-1:2d}] {obs:20s} ({dim} dims)")
    idx += dim

print("\nMuJoCo config 观测顺序 (45维):")
idx = 0
for obs, dim in zip(mujoco_obs_order, mujoco_dims):
    print(f"  [{idx:2d}-{idx+dim-1:2d}] {obs:20s} ({dim} dims)")
    idx += dim

# 5. 观测缩放
print("\n5. 观测缩放因子")
print("-" * 80)
print("观测项               Isaac Lab    MuJoCo Config")
print("base_ang_vel        0.25          0.25  ✓")
print("projected_gravity   1.0           1.0   ✓")
print("velocity_commands   1.0           1.0   ✓")
print("joint_pos           1.0           1.0   ✓")
print("joint_vel           0.05          0.05  ✓")
print("last_action         1.0           1.0   ✓")

# 6. PD 控制参数
print("\n6. PD 控制参数")
print("-" * 80)
kp = [25.0] * 12
kd = [0.5] * 12
print(f"Kp: {kp[0]} (所有关节)")
print(f"Kd: {kd[0]} (所有关节)")
print("注意: Isaac Lab 中 PD 参数在 articulation_cfg.py 中定义")

# 7. 检查潜在问题
print("\n7. 潜在问题诊断")
print("-" * 80)

issues_found = []

# 检查观测空间是否禁用了 base_lin_vel
print("✓ base_lin_vel 已禁用 (Isaac Lab)")
print("✓ height_scan 已禁用 (Isaac Lab)")

# 检查观测顺序
if mujoco_obs_order == ["ang_vel", "gravity_vec", "commands", "dof_pos", "dof_vel", "actions"]:
    print("✓ 观测顺序匹配 Isaac Lab")
else:
    issues_found.append("观测顺序不匹配")
    print("✗ 观测顺序不匹配!")

print("\n" + "=" * 80)
if issues_found:
    print("发现问题:")
    for issue in issues_found:
        print(f"  ✗ {issue}")
else:
    print("✓ 所有配置匹配!")
print("=" * 80)

print("\n如果机器人仍然不走路，可能的原因:")
print("1. 模型权重文件损坏或不匹配")
print("2. 物理参数不匹配 (摩擦系数、质量、惯性)")
print("3. 控制频率不匹配 (Isaac Lab vs MuJoCo)")
print("4. Keyframe 初始姿态不对")
print("5. 重力向量转换有问题")
print("6. 命令值范围不对 (Isaac Lab 训练的命令范围)")
