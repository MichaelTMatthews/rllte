from hsuanwu.common.logger import DEBUG, Logger
from hsuanwu.common.typing import DictConfig

MATCH_KEYS = {
    "DrQv2Learner": {
        "storage": ["NStepReplayStorage"],
        "distribution": [
            "OrnsteinUhlenbeckNoise",
            "TruncatedNormalNoise",
            "NormalNoise",
        ],
        "augmentation": [],
        "reward": [],
    },
    "PPGLearner": {
        "storage": ["VanillaRolloutStorage"],
        "distribution": ["Categorical"],
        "augmentation": [],
        "reward": [],
    },
    "PPOLearner": {
        "storage": ["VanillaRolloutStorage"],
        "distribution": ["Categorical"],
        "augmentation": [],
        "reward": [],
    },
    "SACLearner": {
        "storage": ["VanillaReplayStorage"],
        "distribution": ["SquashedNormal"],
        "augmentation": [],
        "reward": [],
    },
    "IMPALALearner": {
        "storage": ["DistributedStorage"],
        "distribution": ["None"],
        "augmentation": [],
        "reward": [],
    },
}


def cfgs_checker(logger: Logger, cfgs: DictConfig) -> None:
    """Check the compatibility of modules.

    Args:
        logge (Logger): Hsuanwu logger instance.
        cfgs (DictConfig): Dict Config.

    """
    logger.log(DEBUG, "Checking the Compatibility of Modules...")

    # xploit part
    logger.log(DEBUG, f"Selected Encoder: {cfgs.encoder._target_}")
    logger.log(DEBUG, f"Selected Learner: {cfgs.learner._target_}")
    # Check the compatibility
    assert (
        cfgs.storage._target_ in MATCH_KEYS[cfgs.learner._target_]["storage"]
    ), f"{cfgs.storage._target_} is incompatible with {cfgs.learner._target_}, See https://docs.hsuanwu.dev/."
    logger.log(DEBUG, f"Selected Storage: {cfgs.storage._target_}")

    assert (
        cfgs.distribution._target_ in MATCH_KEYS[cfgs.learner._target_]["distribution"]
    ), f"{cfgs.distribution._target_} is incompatible with {cfgs.learner._target_}, See https://docs.hsuanwu.dev/."
    logger.log(DEBUG, f"Selected Distribution: {cfgs.distribution._target_}")

    if cfgs.use_aug:
        logger.log(
            DEBUG, f"Use Augmentation: {cfgs.use_aug}, {cfgs.augmentation._target_}"
        )
    else:
        logger.log(DEBUG, f"Use Augmentation: {cfgs.use_aug}")
    if cfgs.use_irs:
        logger.log(
            DEBUG, f"Use Intrinsic Reward: {cfgs.use_irs}, {cfgs.reward._target_}"
        )
    else:
        logger.log(DEBUG, f"Use Intrinsic Reward: {cfgs.use_irs}")
