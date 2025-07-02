
## 运动控制测试

### Simple Locomotion
我们来参考一下这个 `isaaclab/source/isaaclab_tasks/isaaclab_tasks/direct/humanoid/humanoid_env.py` 来先尝试运行一下简单用例，并理解一个 RL 任务在 Isaac Lab 中是如何被组织和定义的。

humanoid_env解析：

---

- 首先我们可以在这个 `__init__.py` 的入口函数处找到我们这个任务的注册名和各种信息：
  ```py
  gym.register(
      id="Isaac-Humanoid-Direct-v0",
      entry_point=f"{__name__}.humanoid_env:HumanoidEnv",
      disable_env_checker=True,
      kwargs={
          "env_cfg_entry_point": f"{__name__}.humanoid_env:HumanoidEnvCfg",
          "rl_games_cfg_entry_point": f"{agents.__name__}:rl_games_ppo_cfg.yaml",
          "rsl_rl_cfg_entry_point": f"{agents.__name__}.rsl_rl_ppo_cfg:HumanoidPPORunnerCfg",
          "skrl_cfg_entry_point": f"{agents.__name__}:skrl_ppo_cfg.yaml",
      },
  )
  ```
  这里的 `Isaac-Direct-Humanoid-v0` 就是我们要用的任务名， 我们接下来会以这个任务名来启动我们的训练任务。
- `humanoid_env.py` 中的配置参数解析： 
  -  一、通用环境（Env）参数
    
      这些参数定义了强化学习任务的基本框架。
       *   `episode_length_s = 15.0`:
           *   **含义**: 一个“回合”（episode）的最大持续时间，单位是秒。
           *   **作用**: 当仿真时间达到15秒后，如果机器人还没有因为摔倒等原因“死亡”，这一回合也会被强制结束并重置。这可以防止智能体在一个状态停留过久，鼓励它更快地学习。

       *   `decimation = 2`:
           *   **含义**: 抽取/降频数。
           *   **作用**: Isaac Sim 的物理引擎可能以很高的频率运行（例如120Hz），但我们不需要那么频繁地让 AI 做决策。这个参数表示，每进行 **2** 次物理仿真的步进，我们才执行 **1** 次控制循环（即获取观测、计算奖励、执行动作）。这被称为“控制频率”或“决策频率”。这里的控制频率是 120Hz / 2 = 60Hz。

       *   `action_scale = 1.0`:
           *   **含义**: 动作缩放比例。
           *   **作用**: 强化学习算法输出的动作值通常在 `[-1, 1]` 的范围内。这个参数会将网络输出的动作值乘以 `1.0` 再应用到机器人上。你可以用它来调整动作的整体强度。

       *   `action_space = 21`:
           *   **含义**: 动作空间的维度。
           *   **作用**: 告诉RL算法，它需要为多少个关节输出控制指令。这个数字通常等于机器人需要控制的关节数量。对于这个 Humanoid 机器人，有21个可动关节。

       *   `observation_space = 75`:
           *   **含义**: 观测空间的维度。
           *   **作用**: 告诉RL算法，它在做决策时会接收到一个包含多少个数值的向量。这个向量就是机器人的“感官输入”，比如关节角度、速度、身体姿态等。

       *   `state_space = 0`:
           *   **含义**: 状态空间的维度。
           *   **作用**: 在某些算法中，会区分“观测”（Observation，可能是不完整的）和“状态”（State，完整的真实状态）。在`DirectRLEnv`这个基础框架中，通常不作区分，观测就是状态，所以这里设为0或不使用。

  - 二、仿真（Simulation）和物理（Physics）参数

      这部分控制着物理世界的规则。

      *   `sim: SimulationCfg(...)`:
          *   **含义**: 定义整个仿真的核心参数。
          *   `dt=1 / 120`: 物理仿真的时间步长，即每一步仿真代表 `1/120` 秒。这决定了物理引擎的更新频率（120Hz）。
          *   `render_interval=decimation`: 每隔 `decimation` (即2) 次仿真步进，渲染一次画面。这是一种性能优化，因为渲染比物理计算更耗费资源。

      *   `terrain: TerrainImporterCfg(...)`:
          *   **含义**: 定义地面/地形的属性。
          *   `terrain_type="plane"`: 使用一个无限大的平坦地面。
          *   `static_friction=1.0`, `dynamic_friction=1.0`: 静摩擦和动摩擦系数。值越大，地面越“粗糙”，机器人越不容易打滑。
          *   `restitution=0.0`: 碰撞恢复系数（弹性）。0表示完全非弹性碰撞（像撞在一块粘土上），1表示完全弹性碰撞（像一个完美的弹球）。

  - 三、场景（Scene）参数

      这部分定义了如何组织多个并行的仿真环境。

      *   `scene: InteractiveSceneCfg(...)`:
          *   `num_envs=4096`: **关键性能参数**。同时运行 4096 个并行的仿真环境。这是 Isaac Lab 能实现高效训练的核心。
          *   `env_spacing=4.0`: 每个环境在世界坐标系中的间距是4米，防止不同环境里的机器人互相干扰。
          *   `replicate_physics=True`: **关键性能优化**。让GPU为每个环境独立且并行地计算物理，而不是在一个大场景里串行计算。

  - 四、机器人（Robot）和奖励（Reward）相关参数

      这部分是**算法和行为调优的核心**，也是我们后续做实验时最常修改的地方。

      *   `robot: ArticulationCfg = HUMANOID_CFG.replace(...)`:
          *   **含义**: 指定机器人模型。它使用了预定义的 `HUMANOID_CFG`，并通过 `.replace()` 方法修改了它的 `prim_path`，使其能匹配所有并行环境中的机器人（`env_.*` 是通配符）。

      *   `joint_gears: list = [...]`:
          *   **含义**: 每个关节的齿轮比列表。
          *   **作用**: 这在物理上影响着电机输出的力矩如何转化为关节的实际力矩。通常由机器人制造商提供，一般不需要修改。

      - **奖励与惩罚的权重（Weights & Scales）**

        这些参数是**奖励函数**的“旋钮”。通过调整它们，我们可以告诉机器人什么行为更重要。

        *   `heading_weight: float = 0.5`:
            *   **含义**: “朝向”奖励的权重。用于计算“朝向目标方向”的奖励。值越大，机器人越倾向于朝着指定的方向前进。
        *   `up_weight: float = 0.1`:
            *   **含义**: “身体垂直”奖励的权重。值越大，机器人越倾向于保持身体（通常是Z轴）竖直向上。

        *   `energy_cost_scale: float = 0.05`:
            *   **含义**: 能量消耗惩罚的缩放系数。这个惩罚项通常与力矩和速度的平方成正比，模拟真实的能量消耗。值越大，机器人越倾向于用“节能”的方式运动。
        *   `actions_cost_scale: float = 0.01`:
            *   **含义**: 动作惩罚的缩放系数。惩罚过大的动作指令（即力矩）。值越大，机器人动作越“温柔”。
        *   `alive_reward_scale: float = 2.0`:
            *   **含义**: “存活”奖励的缩放系数。只要机器人没有摔倒，在每个时间步都会获得一个固定的正奖励。值越大，机器人越有动力“活下去”。
        *   `dof_vel_scale: float = 0.1`:
            *   **含义**: 关节速度惩罚的缩放系数。惩罚过快的关节运动。值越大，机器人动作越平缓。

      - **终止与惩罚（Termination & Cost）**

        *   `death_cost: float = -1.0`:
            *   **含义**: “死亡”惩罚。当机器人摔倒时，会受到一个很大的负奖励。这给了它一个强烈的信号：“不要摔倒！”。
        *   `termination_height: float = 0.8`:
            *   **含义**: 终止高度。当机器人躯干的质心高度低于0.8米时，就判断为摔倒（死亡）。

      - **观测值缩放（Observation Scales）**

        这些参数用于将原始的物理观测值（可能范围很大）归一化到RL算法更喜欢的范围（如 `[-1, 1]`），有助于训练稳定。

        *   `angular_velocity_scale: float = 0.25`:
            *   **含义**: 角速度观测值的缩放系数。真实的角速度可能是很大的数值，乘以0.25把它缩小。
        *   `contact_force_scale: float = 0.01`:
            *   **含义**: 接触力观测值的缩放系数。脚底接触地面的力可能非常大，需要大幅缩小。

---

如何启动？

我们可以通过 `./isaaclab.bat` 脚本来查看我们当前环境下可用的所有训练任务， 它同时也包含了 `isaaclab_tasks` 下的所有训练场景和设置；
```ps1
./isaaclab.bat -p scripts/environments/list_envs.py
```
可以看到我们希望运行的环境在这里

![alt text](image-5.png)


同时我们可以指定使用哪个强化学习库来运行我们的环境，官方提供了以下几种不同的强化学习库

We provide wrappers to different reinforcement libraries. These wrappers convert the data from the environments into the respective libraries function argument and return types.
- RL-Games
- RSL-RL
- SKRL
- Stable-Baselines3

我们这里以大家最常用的 rlgames 作为示例：

```
./isaaclab.bat -p scripts/reinforcement_learning/rl_games/train.py --task Isaac-Humanoid-Direct-v0 --headless
```

成功运行环境：

![alt text](image-7.png)

80 epoch 示例：

<video controls src="Isaac Sim 4.5.0 2025-07-02 19-55-27.mp4" title="Title"></video>

### 训练 宇树 H1
教程：
https://docs.robotsfan.com/isaaclab/source/tutorials/03_envs/modify_direct_rl_env.html