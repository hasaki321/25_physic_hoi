import torch
import numpy as np
import matplotlib.pyplot as plt

# Isaac Lab 核心库
import omni.isaac.lab.app as app_utils
from omni.isaac.lab.envs import ManagerBasedEnv
from omni.isaac.lab.scene import InteractiveScene, InteractiveSceneCfg
from omni.isaac.lab.assets import ArticulationCfg
from omni.isaac.lab_assets.robots import UNITREE_H1_CFG
import omni.isaac.lab.sim as sim_utils

# --- 1. 配置和启动仿真 ---
# headless=False 让我们能看到 GUI 窗口
app_utils.launch_standalone(headless=False)
# 获取仿真上下文，用于控制仿真循环
sim = sim_utils.SimulationContext(sim_utils.SimulationCfg(dt=1/60))

# --- 2. 搭建场景 ---
scene_cfg = InteractiveSceneCfg(num_envs=1, env_spacing=1.0)
scene = InteractiveScene(scene_cfg)
# 添加地面
scene.add_ground_plane()
# 添加H1机器人，并设置它的初始姿态（稍微弯曲膝盖，更稳定）
robot_cfg = UNITREE_H1_CFG
robot_cfg.init_state.pos = (0.0, 0.0, 1.05)
robot = scene.add(robot_cfg)

# 重置场景，确保所有物体都已加载
scene.reset()

# --- 3. 定义控制目标和参数 ---
# 定义一个目标站立姿势 (单位: 弧度)
# 你可以微调这些值来找到一个完美的站立姿势
target_joint_pos = {
    "left_hip_yaw": 0.0, "left_hip_roll": 0.0, "left_hip_pitch": -0.2,
    "left_knee": 0.5, "left_ankle": -0.3,
    "right_hip_yaw": 0.0, "right_hip_roll": 0.0, "right_hip_pitch": -0.2,
    "right_knee": 0.5, "right_ankle": -0.3,
    "torso": 0.0,
    "left_shoulder_pitch": 0.0, "left_shoulder_roll": 0.0, "left_shoulder_yaw": 0.0, "left_elbow": 0.0,
    "right_shoulder_pitch": 0.0, "right_shoulder_roll": 0.0, "right_shoulder_yaw": 0.0, "right_elbow": 0.0
}

# 获取机器人关节名称的顺序，这非常重要！
joint_names = robot.joint_names
# 将我们的目标姿势字典转换为一个与机器人关节顺序匹配的 torch 张量
# .get(name, 0.0) 表示如果字典里没这个关节，就用0.0作为默认值
target_pos_tensor = torch.tensor([target_joint_pos.get(name, 0.0) for name in joint_names], device=sim.device)

# 定义 PD 控制器的增益 (Stiffness and Damping)
# Kp (Stiffness) 刚度：决定了关节回到目标位置的“力量”有多大
# Kd (Damping) 阻尼：决定了抑制震荡的“力量”有多大
kp = 50.0 
kd = 1.0

# --- 4. 仿真循环与数据记录 ---
# 仿真总时长 5 秒
simulation_duration = 5.0 
# 计算总步数
total_steps = int(simulation_duration / sim.cfg.dt)

# 用于存储历史数据的列表
joint_pos_history = []
time_history = []

print("开始运动控制测试...")

for i in range(total_steps):
    # --- 控制逻辑 ---
    # 获取当前关节位置和速度
    current_pos = robot.data.joint_pos[0, :] # [0,:] 是因为数据有环境维度，我们只有一个环境
    current_vel = robot.data.joint_vel[0, :]

    # PD 控制律: effort = Kp * (target_pos - current_pos) - Kd * current_vel
    # 这就是控制的核心！
    position_error = target_pos_tensor - current_pos
    velocity_error = -current_vel
    effort = kp * position_error + kd * velocity_error

    # 将计算出的力矩指令发送给机器人
    # 注意要扩展维度以匹配API要求 (num_envs, num_actions)
    robot.set_joint_effort_target(effort.unsqueeze(0))

    # --- 数据记录 ---
    # 记录当前时间和关节位置
    time_history.append(i * sim.cfg.dt)
    # 我们只记录部分关键关节以方便绘图，例如左腿
    # .cpu().numpy() 将 GPU tensor 转换为 CPU numpy 数组
    joint_pos_history.append(current_pos.cpu().numpy())
    
    # --- 仿真步进 ---
    scene.write_data_to_sim() # 写入指令
    sim.step()              # 物理步进
    scene.update(sim.cfg.dt)# 更新场景状态

# 仿真结束后，可以稍微暂停一下，让你能看清最后的姿态
sim.step(render=True)
import time
time.sleep(2)

print("仿真结束。")

# --- 5. 绘制曲线图 ---
# 将记录的数据转换为 numpy 数组
joint_pos_history = np.array(joint_pos_history)

# 创建一个图表
plt.figure(figsize=(12, 8))
plt.title("H1 Robot Joint Angle Variation (Standing Task)")
plt.xlabel("Time (s)")
plt.ylabel("Joint Angle (rad)")

# 绘制我们感兴趣的几个关节
# 找到左腿膝关节 (left_knee) 和左髋关节 (left_hip_pitch) 的索引
left_knee_idx = joint_names.index("left_knee")
left_hip_pitch_idx = joint_names.index("left_hip_pitch")

plt.plot(time_history, joint_pos_history[:, left_knee_idx], label="Left Knee")
plt.plot(time_history, joint_pos_history[:, left_hip_pitch_idx], label="Left Hip Pitch")

# 也可以绘制目标位置作为参考线
plt.axhline(y=target_joint_pos["left_knee"], color='r', linestyle='--', label="Target Left Knee")
plt.axhline(y=target_joint_pos["left_hip_pitch"], color='g', linestyle='--', label="Target Left Hip Pitch")

plt.legend()
plt.grid(True)
plt.show()

# --- 6. 关闭仿真 ---
app_utils.close()