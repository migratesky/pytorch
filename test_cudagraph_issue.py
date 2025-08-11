#!/usr/bin/env python3
"""
Reproduction script for CUDAGraph Tree heuristics issue #160281
Error: accessing tensor output of CUDAGraphs that has been overwritten by a subsequent run
"""

import torch


def f(x):
    return x + 1


def g(x):
    return x + 1


# Compile both functions with reduce-overhead mode
f = torch.compile(f, mode="reduce-overhead")
g = torch.compile(g, mode="reduce-overhead")

print("Testing CUDAGraph composition issue...")
print("Running: g(f(torch.randn(2, device='cuda')))")

try:
    result = g(f(torch.randn(2, device="cuda")))
    print(f"Success! Result: {result}")
except RuntimeError as e:
    print(f"Error occurred: {e}")
    print("\nThis demonstrates the CUDAGraph tensor overwrite issue.")
