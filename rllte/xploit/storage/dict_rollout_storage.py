# =============================================================================
# MIT License

# Copyright (c) 2023 Reinforcement Learning Evolution Foundation

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# =============================================================================


from typing import Generator, Dict

import gymnasium as gym
import torch as th
from torch.utils.data.sampler import BatchSampler, SubsetRandomSampler

from rllte.common.base_storage import VanillaRolloutBatch
from rllte.xploit.storage.vanilla_rollout_storage import VanillaRolloutStorage

class DictRolloutStorage(VanillaRolloutStorage):
    """Dict Rollout storage for on-policy algorithms and dictionary observations.

    Args:
        observation_space (gym.Space): The observation space of environment.
        action_space (gym.Space): The action space of environment.
        device (str): Device (cpu, cuda, ...) on which the code should be run.
        num_steps (int): The sample length of per rollout.
        num_envs (int): The number of parallel environments.
        batch_size (int): Batch size of samples.
        discount (float): discount factor.
        gae_lambda (float): Weighting coefficient for generalized advantage estimation (GAE).

    Returns:
        Dict rollout storage.
    """

    def __init__(
        self,
        observation_space: gym.Space,
        action_space: gym.Space,
        device: str = "cpu",
        num_steps: int = 256,
        num_envs: int = 8,
        batch_size: int = 64,
        discount: float = 0.999,
        gae_lambda: float = 0.95,
    ) -> None:
        super().__init__(observation_space, action_space, device, num_steps, num_envs, batch_size, discount, gae_lambda)

        assert isinstance(self.obs_shape, dict), "DictRolloutStorage only support Dict observation space."

        # data containers
        ###########################################################################################################
        self.observations = dict()
        for key, shape in self.obs_shape.items():
            self.observations[key] = th.empty(
                size=(num_steps + 1, num_envs, *shape),
                dtype=th.float32,
                device=self.device,
            )
        ###########################################################################################################

    def add(
        self,
        observations: th.Tensor,
        actions: th.Tensor,
        rewards: th.Tensor,
        terminateds: th.Tensor,
        truncateds: th.Tensor,
        info: Dict,
        next_observations: th.Tensor,
        log_probs: th.Tensor,
        values: th.Tensor
    ) -> None:
        """Add sampled transitions into storage.

        Args:
            observations (th.Tensor): Observations.
            actions (th.Tensor): Actions.
            rewards (th.Tensor): Rewards.
            terminateds (th.Tensor): Termination signals.
            truncateds (th.Tensor): Truncation signals.
            info (Dict): Extra information.
            next_observations (th.Tensor): Next observations.
            log_probs (th.Tensor): Log of the probability evaluated at `actions`.
            values (th.Tensor): Estimated values.

        Returns:
            None.
        """
        for key in self.observations.keys():
            if isinstance(self.observation_space.spaces[key], gym.spaces.Discrete):
                obs_ = observations[key].reshape((self.num_envs,) + self.obs_shape[key])
                next_obs_ = next_observations[key].reshape((self.num_envs,) + self.obs_shape[key])
            else:
                obs_ = observations[key]
                next_obs_ = next_observations[key]

            self.observations[key][self.step].copy_(obs_)
            self.observations[key][self.step + 1].copy_(next_obs_)

        self.actions[self.step].copy_(actions)
        self.rewards[self.step].copy_(rewards)
        self.terminateds[self.step + 1].copy_(terminateds)
        self.truncateds[self.step + 1].copy_(truncateds)
        self.log_probs[self.step].copy_(log_probs)
        self.values[self.step].copy_(values.flatten())

        self.step = (self.step + 1) % self.num_steps

    def sample(self) -> Generator:
        """Sample data from storage."""
        sampler = BatchSampler(SubsetRandomSampler(range(self.num_envs * self.num_steps)), self.batch_size, drop_last=True)

        for indices in sampler:
            batch_obs = {key: item[:-1].view(-1, *self.obs_shape[key])[indices] for (key, item) in self.observations.items()}
            batch_actions = self.actions.view(-1, *self.action_shape)[indices]
            batch_values = self.values.view(-1)[indices]
            batch_returns = self.returns.view(-1)[indices]
            batch_terminateds = self.terminateds[:-1].view(-1)[indices]
            batch_truncateds = self.truncateds[:-1].view(-1)[indices]
            batch_old_log_probs = self.log_probs.view(-1)[indices]
            adv_targ = self.advantages.view(-1)[indices]

            yield VanillaRolloutBatch(
                observations=batch_obs,
                actions=batch_actions,
                values=batch_values,
                returns=batch_returns,
                terminateds=batch_terminateds,
                truncateds=batch_truncateds,
                old_log_probs=batch_old_log_probs,
                adv_targ=adv_targ
            )