
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