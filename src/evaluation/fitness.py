"""Shared per-example fitness used by GA (B1–B5) and LLM baselines (B6–B8)."""

from evaluation.scoring import compute_per_example_fitness

__all__ = ["compute_per_example_fitness"]
