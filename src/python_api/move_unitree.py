import argparse
import matplotlib.pyplot as plt
import numpy as np
import torch
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(
    description="Test script for Unitree H1 robot standing."
)
parser.add_argument("--num_envs", type=int, default=1, help="Number of environments to spawn.")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import isaaclab.sim as sim_utils
from isaaclab.assets import AssetBaseCfg, ArticulationCfg
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.scene import InteractiveScene, InteractiveSceneCfg
from isaaclab.utils.assets import ISAACLAB_NUCLEUS_DIR

# --- 1. 导入H1配置 ---
from isaaclab_assets import H1_CFG
# from isaaclab.source.isaaclab_assets.isaaclab_assets.robots.unitree import H1_CFG

# --- 2. 设计场景 ---
class H1StandSceneCfg(InteractiveSceneCfg):
    """一个包含地面、灯光和H1机器人的场景。"""
    ground = AssetBaseCfg(prim_path="/World/ground", spawn=sim_utils.GroundPlaneCfg())
    dome_light = AssetBaseCfg(
        prim_path="/World/light", spawn=sim_utils.DomeLightCfg(intensity=2000.0, color=(0.95, 0.95, 0.95))
    )
    h1_robot = H1_CFG.replace(prim_path="{ENV_REGEX_NS}/H1")


# --- 3. 仿真循环与控制逻辑 ---
def run_h1_standing_test(sim: sim_utils.SimulationContext, scene: InteractiveScene, app_launcher):
    """运行H1站立测试并记录数据"""
    sim_dt = sim.get_physics_dt()
    sim_time = 0.0
    count = 0
    
    # 仿真总时长 5 秒
    simulation_duration = 5.0
    total_steps = int(simulation_duration / sim_dt)

    robot = scene["h1_robot"]
    # 定义目标站立姿势
    target_joint_pos_dict = {
        ".*_hip_yaw": 0.0, ".*_hip_roll": 0.0, ".*_hip_pitch": -0.28,
        ".*_knee": 0.79, ".*_ankle": -0.52, "torso": 0.0,
        ".*_shoulder_pitch": 0.28, ".*_shoulder_roll": 0.0, ".*_shoulder_yaw": 0.0, ".*_elbow": 0.52,
    }
    # 将目标姿势字典转换为与机器人关节顺序匹配的张量
    target_pos_tensor = robot.data.default_joint_pos.clone()
    for pattern, value in target_joint_pos_dict.items():
        indices = robot.find_joints(pattern)[0]
        if len(indices) > 0:
            target_pos_tensor[:, indices] = value
    joint_pos_history = []
    time_history = []
    body_pos_history = [] 
    time_history = []
    
    print("开始H1站立控制测试...")

    # 仿真主循环
    while app_launcher.app.is_running() and count < total_steps:
        # --- 控制逻辑 ---
        # 直接将目标关节位置发送给机器人
        robot.set_joint_position_target(target_pos_tensor)

        # --- 数据记录 ---
        time_history.append(sim_time)
        joint_pos_history.append(robot.data.joint_pos.cpu().numpy().flatten()) # .flatten()去除多余维度
        body_pos_history.append(robot.data.body_pos_w[0, :, :].clone().cpu().numpy())

        # --- 仿真步进 ---
        scene.write_data_to_sim()
        sim.step()
        sim_time += sim_dt
        count += 1
        scene.update(sim_dt)

    print(f"仿真结束。总时长: {sim_time:.2f}s")
    return time_history, np.array(joint_pos_history), np.array(body_pos_history), robot.joint_names, robot.body_names

# --- 4. 主函数 ---
def main():
    # 初始化仿真上下文
    sim_cfg = sim_utils.SimulationCfg(dt=1/120.0, device=args_cli.device) # 提高物理仿真频率
    sim = sim_utils.SimulationContext(sim_cfg)

    # 设置相机视角
    sim.set_camera_view(eye=[2.5, 2.5, 2.5], target=[0.0, 0.0, 1.0])

    # 创建场景
    scene_cfg = H1StandSceneCfg(num_envs=1, env_spacing=2.0)
    scene = InteractiveScene(scene_cfg)
    
    # 重置仿真和场景
    sim.reset()
    scene.reset()
    print("[INFO]: 场景和仿真设置完成。")

    # 运行仿真测试
    time_data, pos_data, body_pos_data, joint_names, body_names = run_h1_standing_test(sim, scene, app_launcher)
    
    plt.figure(figsize=(15, 10))
    plt.title("H1 Robot Joint Angle Variation (Standing Task)")
    plt.xlabel("Time (s)")
    plt.ylabel("Joint Angle (rad)")

    print(joint_names, body_names)
    # 选择几个关键的腿部关节进行绘制
    joints_to_plot = ["torso", "left_hip_pitch", "left_ankle"]
    for joint_name in joints_to_plot:
        try:
            joint_idx = joint_names.index(joint_name)
            plt.plot(time_data, pos_data[:, joint_idx], label=joint_name)
        except ValueError:
            print(f"警告：在机器人关节列表中未找到关节 '{joint_name}'")
    
    plt.legend()
    plt.grid(True)
    plt.show()

    def plot_3d_trajectory(body_pos_data, body_names, title="3D Trajectory"):
        """
        绘制机器人身体各部位的3D空间轨迹。
        """
        from mpl_toolkits.mplot3d import Axes3D

        fig = plt.figure(figsize=(12, 12))
        ax = fig.add_subplot(111, projection='3d')
        
        bodies_to_plot = ["torso_link", "left_hip_pitch_link", "left_ankle_link"]
        
        for body_name in bodies_to_plot:
            try:
                body_idx = body_names.index(body_name)
                trajectory = body_pos_data[:, body_idx, :]
                x = trajectory[:, 0]
                y = trajectory[:, 1]
                z = trajectory[:, 2]
                
                ax.plot(x, y, z, label=f"{body_name} Trajectory")
                ax.scatter(x[0], y[0], z[0], marker='o', s=100, label=f"{body_name} Start")
                ax.scatter(x[-1], y[-1], z[-1], marker='x', s=100, label=f"{body_name} End")
                
            except ValueError:
                print(f"警告：在机器人身体部位列表中未找到 '{body_name}'")
        
        ax.set_title(title)
        ax.set_xlabel("X (m)")
        ax.set_ylabel("Y (m)")
        ax.set_zlabel("Z (m)")
        ax.legend()
        ax.grid(True)
        # 保持坐标轴比例一致，让运动看起来不失真
        ax.set_aspect('equal', adjustable='box')
        plt.show()

    plot_3d_trajectory(body_pos_data, body_names, title="H1 Robot Body Trajectory")

if __name__ == "__main__":
    main()