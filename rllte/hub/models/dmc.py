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


import torch as th
from huggingface_hub import hf_hub_download
from torch import nn


class DMControl:
    """Trained models of various RL algorithms on the full dmc benchmark.
    Environment link: https://github.com/google-deepmind/dm_control
    Number of environments: 24
    Number of training steps: 1,000,000
    Number of seeds: 10
    Added algorithms: [SAC, DrQ-v2]
    """

    def __init__(self) -> None:
        pass

    def load_models(
        self,
        agent: str,
        env_id: str,
        seed: int,
        device: str = "cpu",
        obs_type: str = "state"
    ) -> nn.Module:
        """Load the model from the hub.

        Args:
            agent (str): The agent to load.
            env_id (str): The environment id to load.
            seed (int): The seed to load.
            device (str): The device to load the model on.
            obs_type (str): A type from ['state', 'pixel'].

        Returns:
            The loaded model.
        """
        model_file = f"{agent.lower()}_dmc_{obs_type}_{env_id}_seed_{seed}.pth"
        subfolder = f"dmc/{agent}"
        file = hf_hub_download(repo_id="RLE-Foundation/rllte-hub", repo_type="model", filename=model_file, subfolder=subfolder)
        model = th.load(file, map_location=device)

        return model.eval()
