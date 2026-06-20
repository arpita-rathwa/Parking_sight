"""Severity-ordered state vocabulary. States are relabeled after training so that
index 0 is always the calmest regime and index N-1 the most severe — this is what
makes the model's output interpretable to a non-ML judge."""

from __future__ import annotations

import numpy as np

_NAMES = {
    4: ["calm", "building", "congested", "critical"],
    3: ["calm", "building", "congested"],
    2: ["calm", "congested"],
}


def state_names(n: int) -> list[str]:
    return _NAMES.get(n, [f"state_{i}" for i in range(n)])


def severity_weights(n: int) -> np.ndarray:
    """Linear 0..1 severity weight per state (calm=0, most-severe=1)."""
    return np.linspace(0.0, 1.0, n)


def hot_state_indices(n: int) -> list[int]:
    """The 'hotspot' states = the top half of the severity ladder."""
    start = (n + 1) // 2
    return list(range(start, n))
