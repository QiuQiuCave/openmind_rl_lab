# G1策略Sim2Sim到MuJoCo验证指南

本指南将详细介绍如何将G1策略从Isaac Sim转移到MuJoCo进行验证。

## 前置条件

1. **已完成策略训练**：在Isaac Sim中训练好G1策略
2. **已安装Isaac Lab**：确保Isaac Lab环境已正确配置
3. **已安装unitree_mujoco**：MuJoCo仿真环境

## 步骤1: 导出策略模型

### 1.1 运行play.py导出ONNX模型

训练完成后，使用`play.py`脚本会自动导出策略为ONNX格式：

```bash
python scripts/rsl_rl/play.py --task Unitree-G1-29dof-Velocity --checkpoint <checkpoint_path>
```

或者指定完整路径：

```bash
python scripts/rsl_rl/play.py \
    --task Unitree-G1-29dof-Velocity \
    --checkpoint logs/rsl_rl/unitree_g1_29dof_velocity/<run_name>/model_<iteration>.pt
```

**注意**：运行`play.py`会自动：
- 导出ONNX模型到 `logs/rsl_rl/unitree_g1_29dof_velocity/<run_name>/exported/policy.onnx`
- 训练时也会自动生成`deploy.yaml`配置文件到 `logs/rsl_rl/unitree_g1_29dof_velocity/<run_name>/params/deploy.yaml`

### 1.2 验证导出文件

确保以下文件存在：
- `logs/rsl_rl/unitree_g1_29dof_velocity/<run_name>/exported/policy.onnx`
- `logs/rsl_rl/unitree_g1_29dof_velocity/<run_name>/params/deploy.yaml`

## 步骤2: 配置部署控制器

### 2.1 修改config.yaml

编辑 `deploy/robots/g1_29dof/config/config.yaml`，设置策略目录：

```yaml
FSM:
  Velocity:
    policy_dir: ../../../logs/rsl_rl/unitree_g1_29dof_velocity/<run_name>
```

**重要**：
- `policy_dir`可以是相对路径或绝对路径
- 如果使用相对路径，它是相对于`deploy/robots/g1_29dof/config/`目录
- 策略目录必须包含`exported/policy.onnx`和`params/deploy.yaml`

### 2.2 验证配置

确保配置文件指向正确的策略目录，部署控制器会自动查找：
1. 首先检查`policy_dir/exported/policy.onnx`是否存在
2. 如果不存在，会在`policy_dir`下查找最新的包含`exported`文件夹的子目录

## 步骤3: 安装依赖和编译

### 3.1 安装系统依赖

```bash
sudo apt install -y libyaml-cpp-dev libboost-all-dev libeigen3-dev libspdlog-dev libfmt-dev
```

### 3.2 安装unitree_sdk2

```bash
git clone git@github.com:unitreerobotics/unitree_sdk2.git
cd unitree_sdk2
mkdir build && cd build
cmake .. -DBUILD_EXAMPLES=OFF
sudo make install
```

### 3.3 编译部署控制器

```bash
cd unitree_rl_lab/deploy/robots/g1_29dof
mkdir -p build && cd build
cmake ..
make
```

编译完成后，会在`build`目录下生成`g1_ctrl`可执行文件。

## 步骤4: 配置MuJoCo仿真

### 4.1 安装unitree_mujoco

参考 [unitree_mujoco](https://github.com/unitreerobotics/unitree_mujoco) 的安装指南。

### 4.2 配置unitree_mujoco

编辑 `unitree_mujoco/simulate/config.yaml`：

```yaml
robot: g1                    # 设置为g1
domain_id: 0                 # 设置为0
enable_elastic_hand: 1       # 设置为1
use_joystick: 1              # 设置为1（如果使用手柄）
```

### 4.3 启动MuJoCo仿真

```bash
cd unitree_mujoco/simulate/build
./unitree_mujoco
```

或者使用命令行参数：

```bash
./unitree_mujoco -i 0 -n eth0 -r g1 -s scene_29dof.xml
```

参数说明：
- `-i 0`: domain_id
- `-n eth0`: 网络接口（sim2sim可以忽略）
- `-r g1`: 机器人类型
- `-s scene_29dof.xml`: 场景文件

## 步骤5: 运行Sim2Sim验证

### 5.1 启动部署控制器

在另一个终端中：

```bash
cd unitree_rl_lab/deploy/robots/g1_29dof/build
./g1_ctrl
```

### 5.2 操作步骤

按照以下顺序操作：

1. **让机器人站起来**：
   - 按下 `[L2 + Up]` 键，使机器人进入站立状态

2. **调整机器人位置**：
   - 点击MuJoCo窗口使其获得焦点
   - 按下 `8` 键，使机器人脚部接触地面

3. **运行策略**：
   - 按下 `[R1 + X]` 键，启动RL策略

4. **禁用弹性带**（可选）：
   - 点击MuJoCo窗口
   - 按下 `9` 键，禁用弹性带（如果启用）

### 5.3 控制命令

如果使用键盘控制速度命令，可以在`deploy.yaml`中将观察项改为：

```yaml
observations:
  keyboard_velocity_commands:  # 改为这个而不是velocity_commands
    params: {command_name: base_velocity}
```

键盘映射：
- `w`: 前进
- `s`: 后退
- `a`: 左移
- `d`: 右移
- `q`: 左转
- `e`: 右转

## 步骤6: 故障排查

### 6.1 策略文件未找到

**错误**：`Policy directory: ...` 或 `Failed to load policy.onnx`

**解决方案**：
- 检查`config.yaml`中的`policy_dir`路径是否正确
- 确保`exported/policy.onnx`文件存在
- 检查文件权限

### 6.2 配置文件错误

**错误**：`Failed to load deploy.yaml`

**解决方案**：
- 确保`params/deploy.yaml`文件存在
- 检查YAML文件格式是否正确
- 查看部署控制器的日志输出

### 6.3 MuJoCo连接问题

**错误**：无法连接到MuJoCo仿真

**解决方案**：
- 确保MuJoCo仿真正在运行
- 检查`domain_id`是否匹配（都是0）
- 查看网络配置

### 6.4 观察维度不匹配

**错误**：观察维度与策略不匹配

**解决方案**：
- 确保`deploy.yaml`中的观察配置与训练时一致
- 检查观察项的scale和history_length设置
- 验证joint_ids_map是否正确

## 步骤7: 验证清单

完成以下检查项：

- [ ] 策略已导出为ONNX格式
- [ ] `deploy.yaml`配置文件已生成
- [ ] `config.yaml`中的`policy_dir`已正确设置
- [ ] 部署控制器已成功编译
- [ ] unitree_mujoco已安装并配置
- [ ] MuJoCo仿真已启动
- [ ] 部署控制器可以连接到MuJoCo
- [ ] 机器人可以正常站立
- [ ] 策略可以正常运行

## 附加说明

### 策略目录结构

正确的策略目录结构应该是：

```
logs/rsl_rl/unitree_g1_29dof_velocity/<run_name>/
├── exported/
│   └── policy.onnx          # ONNX策略模型
├── params/
│   └── deploy.yaml          # 部署配置文件
└── model_*.pt               # 原始checkpoint文件
```

### 使用不同版本的策略

如果需要测试不同训练迭代的策略：

1. 修改`config.yaml`中的`policy_dir`指向不同的run目录
2. 或者创建符号链接指向最新的策略目录
3. 重新启动部署控制器

### Sim2Real部署

Sim2Sim验证成功后，可以按照相同的方式部署到真实机器人：

```bash
./g1_ctrl --network eth0  # eth0是网络接口名称
```

确保：
- 机器人的板载控制程序已关闭
- 网络连接正常
- 安全措施已就位

## 参考资源

- [unitree_mujoco GitHub](https://github.com/unitreerobotics/unitree_mujoco)
- [unitree_sdk2 GitHub](https://github.com/unitreerobotics/unitree_sdk2)
- [Isaac Lab文档](https://isaac-sim.github.io/IsaacLab)

## 常见问题

**Q: 策略在Isaac Sim中表现很好，但在MuJoCo中不稳定？**

A: 这可能是由于两个仿真器之间的物理参数差异。可以尝试：
- 调整MuJoCo的物理参数使其更接近Isaac Sim
- 在训练时增加域随机化
- 检查action scaling是否正确

**Q: 如何切换不同的策略？**

A: 修改`config.yaml`中的`policy_dir`，然后重新启动部署控制器。

**Q: 可以在没有MuJoCo的情况下测试策略吗？**

A: 可以，使用`play.py`在Isaac Sim中测试策略，但这不能替代MuJoCo验证，因为MuJoCo更接近真实物理。











