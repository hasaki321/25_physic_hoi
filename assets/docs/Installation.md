
## Basic Task:Install and Get Started with Your Simulator

### Install and Launch Your Simulator
ref: 
- https://isaac-sim.github.io/IsaacLab/main/index.html
- https://docs.robotsfan.com/isaaclab/source/setup/installation/pip_installation.html
- isaac WebRTC 流式转发： https://docs.isaacsim.omniverse.nvidia.com/4.5.0/installation/manual_livestream_clients.html


IsaacSim是NVIDIAOmniverse平台的一部分，专门用于模拟和开发机器人应用。它结合了NVIDIA的硬件加速和先进的仿真功能，为开发者提供了一个强大的工具集，尤其在工业场景中如仓储、制造业等具有极大潜力。以下是Isaac Sim官方的学习资料与相关资源总结:

- NVIDIA Omniverse全站文档:https://docs.omniverse.nvidia.com/
- Isaac Sim开发者文档:https://developer.nvidia.com/isaac/sim
- Omniverse开发者文档:https://docs.omniverse.nvidia.com/dev-guide/latest/index.html
- Isaac Lab文档: https://isaac-sim.github.io/IsaacLab/
- Isaac Sim API 参考文档: https://docs.omniverse.nvidia.com/py/isaacsim/index.html
- ROS/ROS2 教程:https://docs.omniverse.nvidia.com/isaacsim/latest/ros_ros2_tutorials.html



#### Prev 官方pip源不可用
环境：
- 本地服务器
- Ubuntu 22.04
- Ryzon R5 5500
- 16 GB RAM
- Nvidia Tesla P100 16GB VRAM

Examples 
```bash
git submodule add https://github.com/isaac-sim/isaacsim-app-template.git
```

Isaac Sim
```bash
conda create -p ./env_isaaclab python=3.10
conda activate ./env_isaaclab

pip install torch==2.5.1 torchvision==0.20.1
pip install --upgrade pip
```

```bash
pip install --proxy http://127.0.0.1:7890 'isaacsim[all,extscache]==4.5.0' --extra-index-url https://pypi.nvidia.com
```
pip 源失效： https://pypi.nvidia.com/isaacsim/

Isaacsim 已经释放了开源git仓库： https://github.com/isaac-sim/IsaacSim；直接从git编译
```bash
conda activate ./env_isaaclab
git clone https://github.com/isaac-sim/IsaacSim.git isaacsim
cd isaacsim
git lfs install
git lfs pull

./build.sh
```

Isaac Lab
https://github.com/isaac-sim/IsaacLab/tree/feature/isaacsim_5_0
```bash
git clone -b feature/isaacsim_5_0 https://github.com/isaac-sim/IsaacLab.git isaaclab
cd isaaclab

ln -s ../isaacsim/_build/linux-x86_64/release _isaac_sim

./isaaclab.sh -i
```

```
./isaaclab.sh -p scripts/reinforcement_learning/skrl/train.py --task Isaac-Ant-v0 --headless
```
![alt text](./assets/images/sim_fail_0.png)


#### 7.2 IsaacSim 官方pip源可用
Isaac Sim
```bash
conda create -p ./env_isaaclab python=3.10 -y
conda activate ./env_isaaclab

pip install torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cu118
pip install --upgrade pip
pip install 'isaacsim[all,extscache]==4.5.0' --extra-index-url https://pypi.nvidia.com
```

Isaac Lab
https://github.com/isaac-sim/IsaacLab/tree/feature/isaacsim_5_0
```bash
git clone -b feature/isaacsim_5_0 https://github.com/isaac-sim/IsaacLab.git isaaclab
cd isaaclab

ln -s ../isaacsim/_build/linux-x86_64/release _isaac_sim

./isaaclab.sh -i
```
![alt text](./assets/images/sim_fail.png)


#### 使用云平台
资源来自兰州大学超算中心云平台

按照上述pip步骤安装，云平台不公开端口，我们将使用frp将端口流量转发到我们的公网服务器。
FRP: https://github.com/fatedier/frp

我们在循环处插入一个语句，看起来成功运行了
![alt text](./assets/images/turtor_0.png)

#### Windows
同上pip步骤安装
Enable long paths： https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation?tabs=registry#enable-long-paths-in-windows-10-version-1607-and-later

```ps1
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```

看起来是成功加载好了
![alt text](./assets/images/windows_sim.png)

```ps1
cd isaaclab
.\isaaclab.bat -i
```

### IsaacGym
https://developer.nvidia.com/isaac-gym/download

Install IsaacGym
```bash
wget https://developer.nvidia.com/isaac-gym-preview-4
tar -xvzf isaac-gym-preview-4
pip install -e isaacgym/python
```


#### **Isaac Gym (前辈)**

*   **核心定位**: 一个**轻量级的、纯粹为并行强化学习（RL）设计**的物理仿真库。
*   **诞生背景**: 在 Isaac Gym 出现之前，用仿真进行强化学习训练的一大瓶颈是速度。传统的仿真器（如PyBullet, Gazebo）主要在CPU上运行，难以大规模并行。Isaac Gym 的革命性之处在于，它**完全在GPU上进行物理计算**，可以同时并行运行成千上万个独立的仿真环境，极大地提升了RL的采样效率。
*   **工作方式**:
    *   **无头（Headless）优先**: 它主要设计为在没有图形界面的服务器上运行。虽然也提供一个基础的查看器（viewer），但其主要目的是后台训练。
    *   **纯代码驱动**: 你无法像游戏引擎那样手动搭建场景。所有环境的定义、机器人的加载、物理的设置都必须通过Python代码完成。
    *   **API 相对底层**: API 设计紧凑，专注于RL流程，对于其他功能（如传感器仿真、场景创建）的支持有限。
*   **优点**:
    *   **极快的速度**: 在当时是并行物理仿真的速度之王，是许多RL研究论文的首选工具。
    *   **轻量级**: 安装和依赖相对简单。
*   **缺点**:
    *   **功能有限**:
        *   **渲染能力弱**: 它的可视化非常基础，无法生成用于训练视觉模型的高保真（photorealistic）图像。
        *   **传感器支持不佳**: 几乎没有对RGB-D相机、LiDAR等复杂传感器的官方支持。
        *   **生态系统封闭**: 难以与机器人操作系统（ROS）或其他3D内容创作工具（如Blender）集成。
    *   **已停止主要更新**: NVIDIA的开发重心已经全面转向Isaac Sim。

---

#### **Isaac Sim (当前与未来)**

*   **核心定位**: 一个**功能全面的、基于NVIDIA Omniverse平台**的机器人仿真器和合成数据生成工具。
*   **诞生背景**: 随着机器人技术的发展，需求不再仅仅是快速的RL训练。高逼真度的渲染（用于训练视觉感知模型）、精确的传感器仿真、与ROS等工业标准的无缝对接变得越来越重要。Isaac Sim 正是为满足这些综合性需求而生。
*   **工作方式**:
    *   **可视化与代码并重**:
        *   拥有一个强大的**图形用户界面（GUI）**，你可以像使用Unity或Unreal引擎一样，拖拽资产、搭建场景、设置光照和材质。
        *   同时提供丰富的**Python API**，允许你用代码程序化地控制一切，实现自动化和大规模实验。
    *   **基于Omniverse**: Omniverse是一个协作和模拟平台，这意味着Isaac Sim天生具备多用户协作、连接多种3D内容创作工具、使用USD（通用场景描述）标准格式等先进特性。
*   **优点**:
    *   **物理与渲染双强**:
        *   **高保真渲染**: 基于RTX光线追踪技术，可以生成电影级别的逼真图像，是生成合成数据的利器。
        *   **精确的物理仿真**: 集成了先进的PhysX 5物理引擎，支持刚体、软体、流体等多种仿真。
    *   **全面的传感器仿真**: 内置对RGB-D相机、LiDAR、IMU、接触传感器等的精确仿真。
    *   **生态开放**: 与ROS/ROS2深度集成，方便进行Sim-to-Real的算法验证和迁移。支持从各种CAD软件导入模型。
    *   **集成了并行仿真能力**: Isaac Sim 本身虽然是一个综合平台，但通过 **Isaac Lab** 这个框架，它**继承并超越了Isaac Gym的并行仿真能力**。你现在可以在Isaac Sim的高保真环境中，同样实现数千个环境的GPU并行训练。

*   **缺点**:
    *   **重量级**: 安装包较大，对硬件（特别是NVIDIA RTX显卡）要求较高。
    *   **学习曲线更陡**: 功能全面也意味着需要学习的概念和工具更多（如Omniverse、USD、Kit）。
