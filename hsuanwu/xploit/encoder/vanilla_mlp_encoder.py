import gymnasium as gym
import torch as th
from torch import nn

from hsuanwu.xploit.encoder.base import BaseEncoder, network_init


class VanillaMlpEncoder(BaseEncoder):
    """Multi layer perceptron (MLP) for processing state-based inputs.

    Args:
        observation_space (Space): Observation space of the environment.
        feature_dim (int): Number of features extracted.
        hidden_dim (int): Number of units per hidden layer.

    Returns:
        Mlp-based encoder instance.
    """

    def __init__(
        self, observation_space: gym.Space, feature_dim: int = 64, hidden_dim: int = 256
    ) -> None:
        super().__init__(observation_space, feature_dim)

        input_dim = observation_space.shape[0]
        self.trunk = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, feature_dim),
        )

        self.apply(network_init)

    def forward(self, obs: th.Tensor) -> th.Tensor:
        return self.trunk(obs)
