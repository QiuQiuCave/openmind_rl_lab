## 概述

`test_vel_r2_his_standalone.py` 是一个独立运行脚本，用于加载并测试 Unitree R2 人形机器人在 Sim2Sim 工作流中的速度策略。脚本将原本分散在工程各处的运行配置集中到单一文件中，方便在其他项目或实验环境中复用，只需通过命令行参数即可覆盖关键运行参数。

脚本基于 `sim2simlib` 提供的 `Sim2SimBaseModel`，内置 PID 电机模型、观测配置、动作缩放、默认命令等信息，可直接连接预训练策略权重（`policy.pt`），并选择是否打开 MuJoCo Viewer 进行可视化。

---

## 运行准备

- Python 3.8+（脚本使用 `__future__.annotations` 与类型标注）
- 安装 `sim2simlib` 及其依赖（MuJoCo、PyYAML 可选）
- 可访问的策略检查点目录，结构需包含 `exported/policy.pt`
- 有效的 R2 MuJoCo XML 模型，默认路径：`SIM2SIMLIB_ASSETS_DIR/third_party/r2_wholebody/mjcf/r2_wb.xml`

若需要从 `env.yaml` 读取环境参数，还需确保 `sim2simlib.utils.config.load_from_yaml` 可用（通常意味着已安装 PyYAML）。

---

## 主要功能

1. **策略与模型路径解析**
   - `--policy`：显式指定策略文件路径。
   - `--ckpt-dir`：指定训练日志目录，脚本自动查找 `exported/policy.pt`。
   - `--xml-path`：指定 MuJoCo 模型 XML。
   - 若路径无效会立即报错，避免运行时失败。

2. **环境参数注入**
   - 默认参数：`simulation_dt=0.005`、`control_decimation=4`、`action_scale=0.25`、`obs_history_length=5`。
   - 可通过命令行或 `--env-yaml` 覆盖：脚本在 YAML 中读取 `sim.dt`、`decimation`、`actions.JointPositionAction.scale`、`observations.policy.history_length`。

3. **传感器与动作配置**
   - 观测项：`base_ang_vel`、`gravity_orientation`、`cmd`、`joint_pos`、`joint_vel`、`last_action`，并可基于历史窗口堆叠。
   - 动作：关节位置控制，范围裁剪在 `[-100, 100]`，统一缩放。
   - 电机：配置了 20+ 个关节的力矩上限、刚度、阻尼，使用 PIDMotor。

4. **运行模式**
   - `--headless`：关闭 Viewer，直接执行仿真。
   - 默认启动 Viewer，可配合 `--camera-tracking` 与 `--camera-body` 开启跟随视角。
   - `--slowdown` 控制 Viewer 渲染倍率，便于观察。

5. **命令输入**
   - 默认线速度命令 `(0.8, 0.0, 0.0)`。
   - 通过 `--cmd VX VY YAW` 指定平移/旋转速度。

---

## 常用命令示例

### 1. 使用默认配置启动 Viewer

```bash
python3 scripts/sim2sim/test_vel_r2_his_standalone.py
```

### 2. 指定策略与 XML，并在无界面模式下运行

```bash
python3 scripts/sim2sim/test_vel_r2_his_standalone.py \
  --policy /path/to/policy.pt \
  --xml-path /path/to/r2_wb.xml \
  --headless
```

### 3. 从 env.yaml 读取时间步与缩放，同时修改目标速度

```bash
python3 scripts/sim2sim/test_vel_r2_his_standalone.py \
  --env-yaml /path/to/env.yaml \
  --cmd 1.0 0.2 0.3
```

### 4. 调整控制分辨率与动作缩放，并开启相机跟随

```bash
python3 scripts/sim2sim/test_vel_r2_his_standalone.py \
  --decimation 2 \
  --action-scale 0.35 \
  --camera-tracking \
  --camera-body torso
```

---

## 重要参数说明

- `--slowdown`：模拟渲染倍率。值越大，视觉播放越慢，更容易观察动作。
- `--debug`：启用后会在模型内部打印更多状态信息，便于调试。
- `--obs-history-length`：观测历史长度，会影响 `Observations_Config` 中的 `base_obs_his_length` 并改变状态堆叠维度。
- `DEFAULT_ANGLES` 支持通过正则匹配批量设定初始关节角度，例如 `".*_knee_joint": 0.3`。
- `POLICY_JOINT_NAMES` 列表决定策略输出与环境关节的映射顺序。

---

## 运行流程概述

1. 解析命令行参数。
2. 解析策略路径与 XML，读取必要配置。
3. 根据默认值 + YAML + 命令行合成最终环境参数。
4. 构建 `Sim2Sim_Config`，包含关节、观测、动作、电机等完整配置。
5. 实例化 `Sim2SimBaseModel`。
6. 根据 `--headless` 选择 `headless_run()` 或 `view_run()`。

---

## 故障排查

- **找不到策略/模型文件**：确保 `--policy` 或 `--ckpt-dir`、`--xml-path` 指向真实文件；路径支持 `~`，脚本会自动展开。
- **YAML 解析失败**：确认安装 PyYAML 且 `env.yaml` 结构包含脚本期望的字段。
- **Viewer 卡顿**：尝试调小 `--slowdown` 或使用 `--headless`；若需要观察细节，也可提高 `--slowdown` 值。
- **命令无效**：`--cmd` 需要提供三个浮点值（`VX VY YAW`），单位与训练配置保持一致（米/秒和弧度/秒）。
- **策略动作幅度不对**：检查 `--action-scale` 是否与训练时一致，或通过 `--env-yaml` 保持训练配置。

---

## 建议工作流

1. 使用默认配置确认脚本可运行。
2. 将训练时记录的 `env.yaml` 和策略权重复制到同一目录，利用 `--env-yaml` 和 `--ckpt-dir` 保持一致性。
3. 根据实验需求逐步调整命令、时间步、控制频率等参数，每次修改都记录日志，便于复现。
4. 在需要可视化调试时启用 Viewer 与相机跟随；在批量评估或集群环境下使用 `--headless`。

---

## 参考

- 策略默认目录：`/home/qiuziyu/code/unitree_rl_lab/logs/rsl_rl/unitree_r2_velocity/2025-11-07_14-33-25`
- 机器人 XML：`SIM2SIMLIB_ASSETS_DIR/third_party/r2_wholebody/mjcf/r2_wb.xml`
- 相关脚本：`scripts/sim2sim/test_vel_r2_his.py`（原始多文件配置版本）

如需进一步定制，可直接修改脚本中的默认常量（例如 `MOTOR_STIFFNESS`、`BASE_OBS_TERMS`）或扩展命令行参数，保持文档同步更新即可。

