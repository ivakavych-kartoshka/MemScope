"""Deterministic seed control."""

import os
import random


def seed_everything(seed: int) -> random.Random:
    if seed < 0:
        raise ValueError("seed must be non-negative")
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    try:
        import numpy as np

        np.random.seed(seed)
    except ImportError:
        pass
    return random.Random(seed)
