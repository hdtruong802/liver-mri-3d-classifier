"""set_seed phải làm random module tái lập được (T1.1 DoD)."""

import random

from src.utils.seed import set_seed


def test_set_seed_makes_random_reproducible():
    set_seed(42)
    a = [random.random() for _ in range(5)]
    set_seed(42)
    b = [random.random() for _ in range(5)]
    assert a == b


def test_set_seed_different_seeds_differ():
    set_seed(1)
    a = random.random()
    set_seed(2)
    b = random.random()
    assert a != b
