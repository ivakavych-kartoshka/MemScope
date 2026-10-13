"""Predeclared statistics from paper Section 11.8."""

from __future__ import annotations

import math
import random
import statistics
from collections.abc import Mapping, Sequence


def wilson_interval(successes: int, trials: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if trials <= 0 or successes < 0 or successes > trials:
        raise ValueError("require 0 <= successes <= trials and trials > 0")
    p = successes / trials
    denom = 1 + z * z / trials
    center = (p + z * z / (2 * trials)) / denom
    radius = z * math.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials)) / denom
    return max(0.0, center - radius), min(1.0, center + radius)


def bootstrap_median_ci(
    values: Sequence[float], confidence: float = 0.95, repetitions: int = 2000, seed: int = 0
) -> tuple[float, float]:
    if not values or repetitions < 1 or not 0 < confidence < 1:
        raise ValueError("nonempty values, positive repetitions, and 0 < confidence < 1 required")
    rng = random.Random(seed)
    medians = []
    for _ in range(repetitions):
        sample = [values[rng.randrange(len(values))] for _ in values]
        medians.append(float(statistics.median(sample)))
    medians.sort()
    alpha = (1 - confidence) / 2
    low = medians[max(0, int(alpha * repetitions))]
    high = medians[min(repetitions - 1, int((1 - alpha) * repetitions) - 1)]
    return low, high


def holm_adjust(p_values: Mapping[str, float]) -> dict[str, float]:
    if any(not 0 <= value <= 1 for value in p_values.values()):
        raise ValueError("p-values must lie in [0, 1]")
    ordered = sorted(p_values.items(), key=lambda pair: pair[1])
    adjusted: dict[str, float] = {}
    running = 0.0
    count = len(ordered)
    for index, (name, value) in enumerate(ordered):
        running = max(running, min(1.0, (count - index) * value))
        adjusted[name] = running
    return adjusted
