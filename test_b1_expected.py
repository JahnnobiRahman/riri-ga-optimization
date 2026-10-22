#!/usr/bin/env python3
"""
Test what B1 SHOULD be vs what it IS.
"""

from src.ga.genome import Genome

print("="*60)
print("B1 GENOME: EXPECTED vs ACTUAL")
print("="*60)

print("\n1. EXPECTED B1 (from user comment):")
print("   w_e=0.10, w_s=0.80, w_c=0.10 (sum=1.00)")
g_expected = Genome(
    p_id=0,
    w_s=0.80,
    w_e=0.10,
    w_c=0.10,
    memory_window=256,
    theta_mid=0.70,
    theta_high=0.95,
    gamma=0.0,
)
print(f"   BEFORE normalize(): w_e={g_expected.w_e:.2f}, w_s={g_expected.w_s:.2f}, w_c={g_expected.w_c:.2f}, sum={sum([g_expected.w_e, g_expected.w_s, g_expected.w_c]):.2f}")

g_expected.normalize()
print(f"   AFTER normalize():  w_e={g_expected.w_e:.2f}, w_s={g_expected.w_s:.2f}, w_c={g_expected.w_c:.2f}, sum={sum([g_expected.w_e, g_expected.w_s, g_expected.w_c]):.2f}")
print(f"   ✓ Weights unchanged by normalize() (already sum to 1.0)")

print("\n2. ACTUAL B1 (current baseline_comparison.py):")
print("   w_e=0.10, w_s=0.10, w_c=0.10 (sum=0.30)")
g_actual = Genome(
    p_id=0,
    w_s=0.10,
    w_e=0.10,
    w_c=0.10,
    memory_window=256,
    theta_mid=0.70,
    theta_high=0.95,
    gamma=0.0,
)
print(f"   BEFORE normalize(): w_e={g_actual.w_e:.2f}, w_s={g_actual.w_s:.2f}, w_c={g_actual.w_c:.2f}, sum={sum([g_actual.w_e, g_actual.w_s, g_actual.w_c]):.2f}")

g_actual.normalize()
print(f"   AFTER normalize():  w_e={g_actual.w_e:.2f}, w_s={g_actual.w_s:.2f}, w_c={g_actual.w_c:.2f}, sum={sum([g_actual.w_e, g_actual.w_s, g_actual.w_c]):.2f}")
print(f"   ✗ Weights changed - all become equal (0.33 each)")

print("\n3. COMPARISON:")
print(f"   Expected B1: High safety (0.80), low structure (0.10)")
print(f"   Actual B1:   Balanced (0.33 each) - NOT a zero-shot baseline")

print("\n" + "="*60)
