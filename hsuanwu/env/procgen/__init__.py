from typing import Dict, Tuple
import gymnasium as gym
import numpy as np
import torch as th
from gymnasium.spaces.box import Box
from gymnasium.wrappers import (
    NormalizeReward,
    RecordEpisodeStatistics,
    TransformObservation,
    TransformReward,
)
from procgen import ProcgenEnv

class TorchVecEnvWrapper(gym.Wrapper):
    """Build environments that output torch tensors.

    Args:
        env (Env): The environment.
        device (Device): Device (cpu, cuda, ...) on which the code should be run.

    Returns:
        Environment instance.
    """

    def __init__(self, env: gym.Env, device: th.device) -> None:
        super().__init__(env)
        self._device = th.device(device)
        self.observation_space = Box(
            low=env.single_observation_space.low[0, 0, 0],
            high=env.single_observation_space.high[0, 0, 0],
            shape=[3, 64, 64],
            dtype=env.single_observation_space.dtype,
        )
        self.action_space = env.single_action_space
        self.num_envs = env.num_envs

    def reset(self, **kwargs) -> Tuple[th.Tensor, Dict]:
        obs, info = self.env.reset(**kwargs)
        obs = th.as_tensor(obs.transpose(0, 3, 1, 2), device=self._device)
        return obs, info

    def step(self, action: th.Tensor) -> Tuple[th.Tensor, th.Tensor, th.Tensor, bool, Dict]:
        # Procgen games currently doesn't support Gymnasium.
        obs, reward, terminated, truncated, info = self.env.step(
            action.squeeze(1).cpu().numpy()
        )

        obs = th.as_tensor(obs.transpose(0, 3, 1, 2), device=self._device)
        reward = th.as_tensor(
            reward, dtype=th.float32, device=self._device
        ).unsqueeze(dim=1)
        terminated = th.as_tensor(
            [[1.0] if _ else [0.0] for _ in terminated],
            dtype=th.float32,
            device=self._device,
        )
        truncated = th.as_tensor(
            [[1.0] if _ else [0.0] for _ in truncated],
            dtype=th.float32,
            device=self._device,
        )

        return obs, reward, terminated, truncated, info


class AdapterEnv(gym.Wrapper):
    """Procgen games currently doesn't support Gymnasium.

    Args:
        env (Env): Environment to wrap.
        num_envs (int): Number of parallel environments.

    Returns:
        AdapterEnv instance.
    """

    def __init__(self, env: gym.Env, num_envs: int) -> None:
        super().__init__(env)
        self.num_envs = num_envs

    def step(self, action: int) -> Tuple[np.array, float, bool, bool, Dict]:
        obs, reward, done, info = self.env.step(action)
        return obs, reward, done, done, {}

    def reset(self, **kwargs) -> Tuple[np.array, Dict]:
        obs = self.env.reset()
        return obs, {}


def make_procgen_env(
    env_id: str = "bigfish",
    num_envs: int = 64,
    gamma: float = 0.99,
    num_levels: int = 0,
    start_level: int = 0,
    distribution_mode: str = "easy",
    device: th.device = "cpu",
) -> gym.Env:
    """Build Prcogen environments.

    Args:
        env_id (str): Name of environment.
        num_envs (int): Number of parallel environments.
        gamma (float): A discount factor.
        num_levels (int): The number of unique levels that can be generated. Set to 0 to use unlimited levels.
        start_level (int): The lowest seed that will be used to generated levels. 'start_level' and 'num_levels' fully specify the set of possible levels.
        distribution_mode (str): What variant of the levels to use, the options are "easy", "hard", "extreme", "memory", "exploration".
        device (Device): Device (cpu, cuda, ...) on which the code should be run.

    Returns:
        Environments instance.
    """
    envs = ProcgenEnv(
        num_envs=num_envs,
        env_name=env_id,
        num_levels=num_levels,
        start_level=start_level,
        distribution_mode=distribution_mode,
    )
    envs = AdapterEnv(envs, num_envs)
    envs = TransformObservation(envs, lambda obs: obs["rgb"])
    envs.single_action_space = envs.action_space
    envs.single_observation_space = envs.observation_space["rgb"]
    envs.is_vector_env = True
    envs = RecordEpisodeStatistics(envs)
    envs = NormalizeReward(envs, gamma=gamma)
    envs = TransformReward(envs, lambda reward: np.clip(reward, -10, 10))

    return TorchVecEnvWrapper(envs, device)
