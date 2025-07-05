## PPO 与 推箱子 HOI
Protomotion提出的工作以及相关文章：

- Maskmimic: https://arxiv.org/pdf/2409.14393v1
- ASE: https://arxiv.org/pdf/2205.01906
- AMP: https://arxiv.org/pdf/2104.02180
- DeepMimic: https://arxiv.org/pdf/1804.02717

我们现在先来实现一个比较简单的HOI任务，推箱子到指定地点，为此我们将基于官方给出的示例 `steering_mlp` 来进行修改。

首先观察一下官方的启动脚本:
```bash
PYTHON_PATH protomotions/train_agent.py +exp=steering_mlp +robot=h1 +simulator=<simulator> +experiment_name=h1_steering
```
which will train a steering agent using the Unitree H1 humanoid on the selected simulator. This does not use any reference data or discriminative rewards. It optimizes using pure task-rewards using PPO.

这个启动脚本使用了hydra来作为它的启动配置框架，它所有配置项的根目录应该位于 `protomotion\protomotions\config`，里面包含了所有可用的配置，然后它指定了exp文件夹中的steering作为实验任务，指定了robot目录下的H1机器人作为机器人配置， 最后指定了一个实验名。

### **Hydra 核心概念速览**

在解读前，我们先了解两个 Hydra 的核心概念：

1.  **组合 (`defaults` 列表)**:
    *   一个配置文件可以像搭积木一样，由多个其他配置文件“组合”而成。
    *   `defaults` 列表就是告诉 Hydra：“先加载这些默认的积木块，然后再用我这个文件里的设置去覆盖或添加它们。”
    *   例如 `- ppo_mlp` 就是加载一个名为 `ppo_mlp.yaml` 的默认配置。

2.  **变量插值 (`${...}` 语法)**:
    *   这允许你在一个地方引用另一个地方的配置值，就像编程语言里的变量一样。
    *   例如 `${env.config.steering_params.obs_size}` 的意思是：“去 `env` 配置块下的 `config` 子块，再找到 `steering_params`，取出 `obs_size` 的值，然后把它填到这里来。”
    *   这避免了在多个地方重复写同一个值，改一处即可全部生效。

### **配置文件逐行解读**
现在，我们来看这个 `steering.yaml` 文件。
```yaml
defaults:
  - ppo_mlp
  - /env/steering
```
*   **含义**: 这是配置的**基础**，它告诉 Hydra 去加载两个默认的配置文件作为模板：
    *   `- ppo_mlp`: 加载 `ppo_mlp.yaml` 文件。这个文件很可能定义了一个标准的 **PPO 算法** 和一个 **MLP (多层感知机)** 网络的默认配置（比如学习率、折扣因子、网络层数等）。
    *   `- /env/steering`: 加载 `env` 目录下的 `steering.yaml` 文件。这个文件定义了**仿真环境本身**的配置（比如机器人模型、物理参数、基础的观测和奖励等）。
*   **效果**: 在执行到这里时，Hydra 已经构建了一个包含 PPO 算法和仿真环境的完整配置对象。接下来的所有内容，都是对这个“基础模板”的**修改和补充**。

根据里面文件的递归定义调用，实际上steering_mlp.yaml展开后应该是这样的：
```yaml
- ppo_mlp
    defaults:
        - /agent/ppo/agent
            num_envs: 4096
            agent:
                _target_: protomotions.agents.ppo.agent.PPO
                    config:
                        ...
        - /env/base_env
            defaults:
            - /terrain/flat
            - /motion_manager/base_manager
            env:
                _target_: protomotions.envs.base_env.env.BaseEnv
                _recursive_: False
                config:
                    experiment_name: ${experiment_name}
                    num_envs: ${num_envs}
                    headless: ${headless}
                    simulator: ${simulator}
                    max_episode_length: 300
                    robot: ${robot}
                    ...

        - /agent/ppo/models/mlp_actor
            agent:
                config:
                    # Setup basic actor-critic structure
                    model:
                    config:
                        actor:
                        _target_: protomotions.agents.ppo.model.PPOActor
                        ...
        - /agent/ppo/models/mlp_critic
            agent:
                config:
                    # Setup basic actor-critic structure
                    model:
                    config:
                        critic:
                        _target_: protomotions.agents.common.mlp.MultiHeadedMLP
                        ...

- /env/steering
    defaults:
        - base_env

        # Env structure
        env:
        _target_: protomotions.envs.steering.env.Steering
        config:
            enable_height_termination: True
            steering_params:
                ...
```


```yaml
agent:
  config:
    task_reward_w: 1.0
```
*   **含义**: 我们现在要修改 `/agent/ppo/agent` 这个配置块。
*   **操作**: 在 `agent.config` 下，覆盖一个名为 `task_reward_w` 的参数，值为 `1.0`。
*   **推测**: 这个参数很可能是“任务奖励的权重”。对于 `steering`（导航/转向）任务，这个奖励可能与“机器人朝向目标方向的程度”有关。

```yaml
    modules:
      steering:
        _target_: protomotions.agents.common.common.Flatten
        num_in: ${env.config.steering_params.obs_size}
        num_out: ${.num_in}
        config:
          obs_key: steering
          normalize_obs: true
          norm_clamp_value: 5
```
*   **含义**: 这是**最关键的部分**，它定义了一个新的“模块”（module）。
*   **`modules`**: 这是一个自定义的配置块，用于存放可复用的组件，比如特征提取器。
*   **`steering`**: 这个新模块的名字叫做 `steering`。
*   **`_target_`**: 这是 Hydra 的一个**魔法字段**，用于**实例化对象**。它告诉 Hydra：“当需要创建这个模块时，请调用 `protomotions.agents.common.common.Flatten` 这个类的构造函数。”
*   **`num_in: ${env.config.steering_params.obs_size}`**: 这是给 `Flatten` 类的构造函数传参。`num_in` (输入维度) 的值，来自于我们刚刚加载的 `env/steering.yaml` 文件中定义的**转向观测 (`steering`) 的大小**。
*   **`num_out: ${.num_in}`**: `.` 表示“当前节点”。所以 `${.num_in}` 的意思是“`num_out` 的值等于当前节点下 `num_in` 的值”。这是一个非常方便的自引用。
*   **`config`**: 这是一个嵌套的配置，会作为参数传递给 `Flatten` 类。
    *   `obs_key: steering`: 告诉这个模块，它应该从整个观测数据中，只处理 `key` 为 `steering` 的那一部分数据。
    *   `normalize_obs: true`: 对这部分观测数据进行归一化。
    *   `norm_clamp_value: 5`: 归一化后，将值的范围限制在 `[-5, 5]` 之内。
*   **总结这部分**: 我们定义了一个名为 `steering` 的神经网络层（或模块），它的作用是：接收 `steering` 观测，将其归一化，然后输出。

```yaml
    # Append the direction obs to the actor and critic inputs
    model:
      config: 
        actor:
          config:
            mu_model:
              config:
                input_models:
                  steering: ${agent.config.modules.steering}
        critic:
          config:
            input_models:
              steering: ${agent.config.modules.steering}
```
*   **含义**: 我们现在要修改**模型（`model`）**的结构，把刚刚定义的 `steering` 模块**“插入”**到 Actor 和 Critic 网络中。
*   **`actor.config.mu_model.config.input_models`**: 这是一层层深入到 Actor 网络的输入部分。
*   **`steering: ${agent.config.modules.steering}`**: 在 Actor 的输入模型字典中，增加一个 `key` 为 `steering` 的项，它的 `value` 就是我们刚刚实例化的那个 `steering` 模块 (`protomotions.agents.common.common.Flatten` 对象)。
*   **对 `critic` 的操作同理**。
*   **效果**: 这段配置巧妙地告诉模型：“除了你默认的输入（比如本体感受信息），现在还要额外接收一个名为 `steering` 的输入。处理这个输入的具体方式，就是我们上面定义的那个 `steering` 模块。”

```yaml
    extra_inputs:
      steering: true
```
*   **含义**: 这是一个标志位，明确地告诉 `agent` 的其他部分（可能是数据处理或损失计算部分），我们的网络现在有一个额外的输入源，名为 `steering`。


通过上面的解析，我们接下来如果需要进行我们新的修改的话，我们很可能需要修改或者增加以下文件：

1. [x] 在 config/exp 中新增一个我们自己的实验配置名为 box_mlp.yaml
2. [-] 在 config/env 中新增一个我们自己的实验环境名为 box.yaml, 并且从 box_mlp.yaml 中设置为默认模板
3. [-] 完善实验配置，在 protomotions/envs/ 下新增一个目录名为 box 并在该目录下创建一个名为 env.py 的脚本以实现我们的逻辑
4. [] 修改 agent 模块新增我们自己的观察模块，并在actor和critic中把这个模块注入进去以实现拓展的观察空间 

### 环境脚本解读

通过对比`BaseEnv`和`Steering`，我们能非常清晰地看到一个优秀的强化学习框架是如何通过**继承和重载 (Inheritance and Overriding)** 来实现代码复用和功能扩展的。这正是面向对象编程思想在RL项目中的完美体现。

我将带您像剥洋葱一样，一层一层地解析这个过程。

---

#### **第一层：`BaseEnv` - "骨架"与"通用器官"**

`BaseEnv` 的作用是定义一个强化学习环境所**必须拥有**的所有基础组件和工作流程。它就像一个机器人的通用骨架和内脏，不管这个机器人将来是要走路、推箱子还是跳舞，这些基础部分都是不可或缺的。

**`BaseEnv` 的核心职责 (`__init__` 函数里做了什么):**

1.  **启动仿真器 (`self.simulator`)**:
    *   根据配置文件 (`self.config.simulator`)，实例化一个 `Simulator` 对象。这是整个仿真世界的核心，负责物理计算、加载机器人和场景。
    *   **关键点**: `BaseEnv` 不关心你用的是 Isaac Sim 还是其他什么仿真器，它只通过一个标准的 `Simulator` 接口来交互。这就是“解耦”。

2.  **创建地形 (`self.terrain`)**:
    *   根据配置实例化一个 `Terrain` 对象。它可以是平地，也可以是随机山坡。

3.  **处理运动数据 (`self.motion_lib`, `self.motion_manager`)**:
    *   如果配置了运动文件（用于模仿学习），就加载 `MotionLib` (运动库)，并创建 `MotionManager` (运动管理器) 来管理每个环境应该播放哪个动作。

4.  **建立观测回调 (`self.self_obs_cb`, `self.terrain_obs_cb`)**:
    *   创建 `HumanoidObs` 和 `TerrainObs` 对象。这两个对象是专门负责计算“本体观测”（关节角度、速度等）和“地形观测”（机器人脚下的地形高度）的。
    *   **关键点**: `BaseEnv` 把不同类型的观测计算逻辑封装在不同的类里，而不是混在一起，使得代码清晰、可扩展。

5.  **初始化缓冲区 (`self.rew_buf`, `self.reset_buf`, ...)**:
    *   创建用于存放奖励、重置信号、进度等信息的 `torch.Tensor`。这些是RL算法运行时必不可少的数据容器。

**`BaseEnv` 的工作流程 (`step` 函数):**

`step` 函数定义了一个标准的“仿真-学习”循环，这是一个所有RL环境都遵循的通用流程：

1.  `pre_physics_step(actions)`: 在物理步进前对动作进行预处理。
2.  `self.simulator.step(actions, ...)`: **将动作发送给仿真器**，驱动物理世界前进一小步。
3.  `post_physics_step()`: 物理步进后，进行一系列计算和检查。
    *   `compute_observations()`: 调用 `self_obs_cb` 和 `terrain_obs_cb` 来**更新所有观测数据**。
    *   `compute_reward()`: **计算奖励**。
    *   `compute_reset()`: **检查是否需要重置环境**（比如机器人摔倒了）。
4.  返回 `(obs, reward, reset, extras)`: 将计算好的数据打包，返回给RL算法。

**`BaseEnv` 留下的“接口” (可被子类重载的方法):**

`BaseEnv` 在很多地方故意只做了最基础的实现，把具体逻辑留给子类去完成。这些就是它的“扩展接口”：

*   `compute_observations()`: 它只调用了基础的观测模块，子类可以重载它，加入更多自定义的观测。
*   `compute_reward()`: **最重要**的接口。`BaseEnv` 里的实现极其简单 (`self.rew_buf[:] = 1.0`)，只是给了一个“存活奖励”。它**期望**子类必须重载这个方法来定义有意义的任务奖励。
*   `compute_reset()`: 提供了基于摔倒的通用重置逻辑，子类可以重载它来增加新的重置条件。
*   `create_visualization_markers()`: 允许子类添加自定义的可视化标记。

---

#### **第二层：`Steering` - 添加"血肉"与"特定任务大脑"**

`Steering` 类继承自 `BaseEnv`。它的目标是实现一个特定的“导航/转向”任务。它通过**重载 (override)** 和**扩展 (extend)** `BaseEnv` 的方法来添加自己的专属逻辑。

**`Steering` 如何利用和扩展 `BaseEnv` (`__init__` 函数):**

1.  **调用父类构造函数 (`super().__init__(...)`)**:
    *   这是第一步，也是最重要的一步。它执行了 `BaseEnv` 的所有初始化代码，意味着 `Steering` 环境一出生就自动拥有了仿真器、地形、基础观测模块和所有缓冲区。**它不需要重复造轮子。**

2.  **定义任务专属变量**:
    *   它从自己的配置文件 (`self.config.steering_params`) 中读取任务参数，如 `_tar_speed_min`, `_heading_change_steps_min` 等。
    *   创建 `self.steering_obs`, `self._tar_dir`, `self._tar_speed` 等**任务专属的缓冲区**，用来存放“目标方向”、“目标速度”等信息。

**`Steering` 如何重载 "接口" 来实现自己的逻辑:**

1.  **`compute_observations(self, env_ids=None)`**:
    *   `super().compute_observations(env_ids)`: 首先，调用父类的方法，把基础的“本体观测”和“地形观测”先算好。
    *   `obs = compute_heading_observations(...)`: 然后，调用它自己定义的 `compute_heading_observations` 函数，计算**“转向观测”**（目标方向在机器人局部坐标系下的表示）。
    *   `self.steering_obs[env_ids] = obs`: 将计算出的新观测存入自己的专属缓冲区。

2.  **`get_obs(self)`**:
    *   `obs = super().get_obs()`: 先获取父类提供的所有基础观测（一个字典）。
    *   `obs.update({"steering": self.steering_obs})`: **关键一步！** 将自己计算的 `steering` 观测，作为一个新的 `key` 添加到总的观测字典中。这样，返回给RL智能体的总观测里，就包含了导航任务所需的信息。

3.  **`compute_reward(self)`**:
    *   **完全重载！** 它没有调用 `super().compute_reward()`，而是用自己的奖励函数 `compute_heading_reward` 来完全替代父类的实现。
    *   `self.rew_buf[:] = compute_heading_reward(...)`: 这个函数根据机器人当前的速度、之前的位置、目标方向和目标速度，计算出一个奖励值，这个奖励值**直接反映了机器人“跟上目标”的程度**。这就是该任务的核心驱动力。

4.  **`post_physics_step(self)` 和 `check_update_task(self)`**:
    *   扩展了 `post_physics_step`，在每次仿真步进后调用 `check_update_task`。
    *   `check_update_task` 会检查是否到了该改变目标方向的时间，如果是，就调用 `reset_heading_task` 来随机生成一个新的目标方向和速度。这使得任务具有动态性。

5.  **`reset(self, env_ids=None)`**:
    *   在调用父类的 `reset` 之前，先调用 `self.reset_heading_task(env_ids)` 来为需要重置的环境初始化一个新的导航目标。

---

#### **总结**

| `BaseEnv` (父类) | `Steering` (子类) |
| :--- | :--- |
| **提供骨架**: `__init__`, `step` 的完整流程。 | **直接继承**，无需重写。 |
| **提供通用器官**: 仿真器、地形、运动库。 | **直接使用** `self.simulator`, `self.terrain`。 |
| **提供基础观测**: `HumanoidObs`, `TerrainObs`。 | **调用** `super().compute_observations()` 来获取基础观测。 |
| **定义观测“篮子”**: `get_obs()` 返回一个观测字典。 | **扩展“篮子”**: `obs.update({"steering": ...})`，往里面放新东西。 |
| **定义奖励“占位符”**: `compute_reward()` 只给一个简单的存活奖励。 | **完全重写**: 用 `compute_heading_reward` 替换，实现任务专属的奖励逻辑。 |
| **提供通用重置**: 根据摔倒来重置。 | **扩展重置**: 在重置时，额外调用 `reset_heading_task` 来更新任务目标。 |

**简单来说，`BaseEnv` 说：“作为一个环境，你必须有手有脚，能跑起来，能看能感觉。” 而 `Steering` 说：“好的，谢谢你的手脚。现在，我要用我的大脑告诉你，我们今天的目标是朝那个方向跑，跑得越准，奖励越高！”**

### 设计奖励与修改脚本
基于steering任务，我们如果需要指定人物推动箱子到目标地点的话，我们需要：

1. 修改地形使其在每次重置的时候能随机一个box的新位置以及新目标位置（距离人物一定半径圆内，目标距离箱子一定半径圆内） -> 可能需要修改 self.terrain 和 reset 函数
2. 推箱子任务其实与steering任务类似，我们可以把任务划分为两个阶段，给予阶段性奖励 -> 需要修改 observation， reward, reset
   1. 在还没与箱子接触的时候（箱子周围一小个半径判定接触或者直接能计算接触），把箱子的方向设置为我们的目标移动方向，给予与steering一样的reward（scale factor 1），在第一次接触到箱子（设置flag）的时候设置微弱奖励，不再计算该阶段接近奖励
   2. 与箱子接触后，把箱子的目标方向设置为我们的目标移动方向，给予与steering一样的reward（scale factor 1），在推到终点的时候设置较大reward，重置任务
3. 动作空间应该是保持不变，观察空间在steering任务中是比动作空间多了3个(local_tar_dir[x,y]->(root_rot, tar_dir3d 做了某种运算),vel)，我们的观察空间可能需要分为两段（人与箱子的关系，箱子与目标点的关系）


### 实验
```
python protomotions/train_agent.py +exp=box_mlp +robot=smpl +simulator=isaaclab +experiment_name=smpl_box_pushing +fabric.strategy.process_group_backend="gloo" 
```