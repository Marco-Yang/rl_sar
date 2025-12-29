# Unitree Go2 强化学习观测空间文档

本文档详细说明了 Unitree Go2 机器人在粗糙地形速度跟踪任务中的观测空间构成和顺序。

## 📋 目录
- [观测空间总览](#观测空间总览)
- [详细观测空间](#详细观测空间)
- [观测空间维度](#观测空间维度)
- [噪声和裁剪](#噪声和裁剪)
- [配置文件](#配置文件)

---

## 观测空间总览

训练环境：`RobotLab-Isaac-Velocity-Rough-Unitree-Go2-v0`  
配置文件：`source/robot_lab/robot_lab/tasks/manager_based/locomotion/velocity/config/quadruped/unitree_go2/rough_env_cfg.py`

**总观测维度**: 48 维

**注意**: 在 Unitree Go2 配置中，以下观测项被禁用：
- ❌ `base_lin_vel` (基座线速度)
- ❌ `height_scan` (高度扫描)

---

## 详细观测空间

### 1. 基座角速度 (Base Angular Velocity)
- **维度**: 3
- **索引**: 0-2
- **内容**: `[ω_x, ω_y, ω_z]`
- **参考系**: 机器人基座坐标系
- **单位**: rad/s
- **缩放**: 0.25
- **噪声**: 均匀噪声 [-0.2, 0.2]
- **裁剪**: [-100.0, 100.0]
- **说明**: 机器人基座在三个轴上的角速度

### 2. 投影重力 (Projected Gravity)
- **维度**: 3
- **索引**: 3-5
- **内容**: `[g_x, g_y, g_z]`
- **参考系**: 机器人基座坐标系
- **单位**: 归一化重力向量
- **缩放**: 1.0
- **噪声**: 均匀噪声 [-0.05, 0.05]
- **裁剪**: [-100.0, 100.0]
- **说明**: 重力向量在机器人基座坐标系中的投影，用于感知姿态

### 3. 速度命令 (Velocity Commands)
- **维度**: 3
- **索引**: 6-8
- **内容**: `[v_x_cmd, v_y_cmd, ω_z_cmd]`
- **单位**: 
  - 线速度: m/s
  - 角速度: rad/s
- **缩放**: 1.0
- **噪声**: 无
- **裁剪**: [-100.0, 100.0]
- **范围**:
  - `v_x_cmd`: [-1.0, 1.0] m/s (前后速度)
  - `v_y_cmd`: [-1.0, 1.0] m/s (左右速度)
  - `ω_z_cmd`: [-1.0, 1.0] rad/s (转向角速度)
- **说明**: 期望的运动速度命令

### 4. 关节位置 (Joint Positions)
- **维度**: 12
- **索引**: 9-20
- **内容**: 相对于默认位置的关节角度偏差
- **单位**: rad
- **缩放**: 1.0
- **噪声**: 均匀噪声 [-0.01, 0.01]
- **裁剪**: [-100.0, 100.0]
- **顺序**:
  ```
  [9]  FR_hip_joint      (右前髋关节)
  [10] FR_thigh_joint    (右前大腿关节)
  [11] FR_calf_joint     (右前小腿关节)
  [12] FL_hip_joint      (左前髋关节)
  [13] FL_thigh_joint    (左前大腿关节)
  [14] FL_calf_joint     (左前小腿关节)
  [15] RR_hip_joint      (右后髋关节)
  [16] RR_thigh_joint    (右后大腿关节)
  [17] RR_calf_joint     (右后小腿关节)
  [18] RL_hip_joint      (左后髋关节)
  [19] RL_thigh_joint    (左后大腿关节)
  [20] RL_calf_joint     (左后小腿关节)
  ```

### 5. 关节速度 (Joint Velocities)
- **维度**: 12
- **索引**: 21-32
- **内容**: 关节角速度
- **单位**: rad/s
- **缩放**: 0.05
- **噪声**: 均匀噪声 [-1.5, 1.5]
- **裁剪**: [-100.0, 100.0]
- **顺序**: 与关节位置顺序相同

### 6. 上一步动作 (Last Action)
- **维度**: 12
- **索引**: 33-44
- **内容**: 上一时刻输出的关节位置目标
- **单位**: 归一化动作空间 (通常在 [-1, 1])
- **缩放**: 1.0
- **噪声**: 无
- **裁剪**: [-100.0, 100.0]
- **顺序**: 与关节位置顺序相同
- **说明**: 提供时间相关性信息，帮助策略平滑控制

### 7. 高度扫描基准 (Height Scan Base) - 仅 Critic 使用
- **维度**: 4 (在 Critic 观测中，但不在 Policy 中)
- **内容**: 基座周围小区域的高度测量
- **说明**: 此项仅在 Critic 网络中使用，不在 Policy 网络的观测中

---

## 观测空间维度

### Policy 观测空间 (Actor 网络输入)
```
总维度: 45

分组:
- 基座角速度:    3 维  [0:3]
- 投影重力:      3 维  [3:6]
- 速度命令:      3 维  [6:9]
- 关节位置:     12 维  [9:21]
- 关节速度:     12 维  [21:33]
- 上一步动作:   12 维  [33:45]
```

### Critic 观测空间 (Critic 网络输入)
```
总维度: 更多维度 (包含额外信息)

额外包含:
- 基座线速度:    3 维
- 高度扫描基准:  4 维
- ... (其他特权信息)
```

---

## 噪声和裁剪

### 观测噪声配置

在训练期间，为提高策略鲁棒性，对观测添加了随机噪声：

| 观测项 | 噪声类型 | 噪声范围 | 是否在 Play 模式启用 |
|--------|----------|----------|---------------------|
| 基座角速度 | 均匀噪声 | [-0.2, 0.2] | ❌ 否 |
| 投影重力 | 均匀噪声 | [-0.05, 0.05] | ❌ 否 |
| 速度命令 | 无 | - | - |
| 关节位置 | 均匀噪声 | [-0.01, 0.01] | ❌ 否 |
| 关节速度 | 均匀噪声 | [-1.5, 1.5] | ❌ 否 |
| 上一步动作 | 无 | - | - |

**注意**: 在 `play.py` 中，`enable_corruption = False`，因此推理时不添加噪声。

### 观测裁剪

所有观测项在添加噪声后都会被裁剪到 `[-100.0, 100.0]` 范围内，防止异常值。

---

## 动作空间

### 动作维度: 12

动作表示目标关节位置的偏移量（相对于默认姿态）：

```
动作缩放:
- 髋关节 (*_hip_joint):   0.125
- 其他关节 (腿部关节):    0.25
```

**动作裁剪**: [-100.0, 100.0]

**关节顺序**: 与观测空间中的关节顺序相同

---

## 配置文件

### 主要配置文件

1. **环境配置**: 
   ```
   source/robot_lab/robot_lab/tasks/manager_based/locomotion/velocity/config/quadruped/unitree_go2/rough_env_cfg.py
   ```

2. **基础配置**:
   ```
   source/robot_lab/robot_lab/tasks/manager_based/locomotion/velocity/velocity_env_cfg.py
   ```

3. **MDP 函数**:
   ```
   source/robot_lab/robot_lab/tasks/manager_based/locomotion/velocity/mdp/
   ```

### 关键配置代码片段

```python
# 禁用的观测项
self.observations.policy.base_lin_vel = None
self.observations.policy.height_scan = None

# 缩放配置
self.observations.policy.base_ang_vel.scale = 0.25
self.observations.policy.joint_pos.scale = 1.0
self.observations.policy.joint_vel.scale = 0.05
```

---

## 可视化观测空间

```
观测空间结构 (45维):

┌─────────────────────────────────────────────┐
│  基座角速度 (3)          [0:3]             │
├─────────────────────────────────────────────┤
│  投影重力 (3)            [3:6]             │
├─────────────────────────────────────────────┤
│  速度命令 (3)            [6:9]             │
├─────────────────────────────────────────────┤
│  关节位置 (12)           [9:21]            │
│    FR: hip, thigh, calf                     │
│    FL: hip, thigh, calf                     │
│    RR: hip, thigh, calf                     │
│    RL: hip, thigh, calf                     │
├─────────────────────────────────────────────┤
│  关节速度 (12)           [21:33]           │
│    (顺序同上)                               │
├─────────────────────────────────────────────┤
│  上一步动作 (12)         [33:45]           │
│    (顺序同上)                               │
└─────────────────────────────────────────────┘
```

---

## 使用示例

### Python 代码示例

```python
import torch

# 假设观测向量
obs = torch.randn(1, 45)  # (batch_size, obs_dim)

# 提取各部分观测
base_ang_vel = obs[:, 0:3]          # 基座角速度
proj_gravity = obs[:, 3:6]          # 投影重力
vel_commands = obs[:, 6:9]          # 速度命令
joint_pos = obs[:, 9:21]            # 关节位置
joint_vel = obs[:, 21:33]           # 关节速度
last_action = obs[:, 33:45]         # 上一步动作

# 单个关节访问
FR_hip_pos = obs[:, 9]              # 右前髋关节位置
FR_thigh_pos = obs[:, 10]           # 右前大腿关节位置
FR_calf_pos = obs[:, 11]            # 右前小腿关节位置
```

---

## 训练信息

### 检查点路径
```
logs/rsl_rl/unitree_go2_rough/2025-12-24_16-11-25/model_23599.pt
```

### 训练参数
- **算法**: PPO (Proximal Policy Optimization)
- **训练步数**: 23,599 iterations
- **环境数量**: 4096 (训练时)
- **步长**: 0.02s (50 Hz)

---

## 常见问题

### Q1: 为什么没有基座线速度观测？
**A**: 在 Unitree Go2 配置中，`base_lin_vel` 被设置为 `None`，这是一种设计选择，迫使策略通过其他观测（如关节速度、重力方向等）隐式推断机器人的运动状态。

### Q2: 高度扫描在哪里？
**A**: `height_scan` 也被禁用了（设为 `None`）。这简化了观测空间，机器人依赖本体感觉完成导航。

### Q3: 如何启用这些观测？
**A**: 在配置文件中注释掉或删除以下行：
```python
# self.observations.policy.base_lin_vel = None
# self.observations.policy.height_scan = None
```

### Q4: Critic 网络的观测空间是什么？
**A**: Critic 网络使用额外的特权信息，包括：
- 基座线速度 (3维)
- 高度扫描基准 (4维)
- 其他环境状态信息

---

## 版本信息

- **robot_lab 版本**: v2.3.0
- **Isaac Lab 版本**: v2.3.0
- **文档更新日期**: 2025-12-29

---

## 参考资料

1. [Isaac Lab 文档](https://isaac-sim.github.io/IsaacLab)
2. [RSL-RL 库](https://github.com/leggedrobotics/rsl_rl)
3. [Unitree Go2 机器人](https://www.unitree.com/go2)

---

**最后更新**: 2025-12-29  
**作者**: GitHub Copilot  
**项目**: robot_lab - Unitree Go2 RL Training
