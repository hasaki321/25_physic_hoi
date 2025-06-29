# Physic HOI ShanghaiTech

## Basic Task:Install and Get Started with Your Simulator

### Install and Launch Your Simulator
ref: 
- https://isaac-sim.github.io/IsaacLab/main/index.html
- https://docs.robotsfan.com/isaaclab/source/setup/installation/pip_installation.html

Examples 
```bash
git clone https://github.com/isaac-sim/isaacsim-app-template.git
```

Isaac Sim
```bash
conda create -p ./env_isaaclab python=3.10
conda activate ./env_isaaclab

pip install torch==2.5.1 torchvision==0.20.1
pip install --upgrade pip
pip install --proxy http://127.0.0.1:7890 'isaacsim[all,extscache]==4.5.0' --extra-index-url https://pypi.nvidia.com
```

Isaac Lab



### Use Isaac Lab Framework for Simple Locomotion

## Git push token
token: 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