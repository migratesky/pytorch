#!/usr/bin/env python3
"""
Test script for CUDAGraph Tree heuristics fix #160281
Tests both the original issue and the workaround solutions
"""

import torch
import torch.compiler


def test_original_issue():
    """Test the original issue that causes tensor overwrite"""
    print("=== Testing Original Issue ===")
    
    def f(x):
        return x + 1

    def g(x):
        return x + 1

    # Compile both functions with reduce-overhead mode
    f = torch.compile(f, mode="reduce-overhead")
    g = torch.compile(g, mode="reduce-overhead")

    print("Running: g(f(torch.randn(2, device='cuda')))")
    
    try:
        result = g(f(torch.randn(2, device="cuda")))
        print(f"✓ Success! Result: {result}")
        return True
    except RuntimeError as e:
        print(f"✗ Error occurred: {e}")
        return False


def test_workaround_clone():
    """Test workaround using tensor cloning"""
    print("\n=== Testing Workaround: Tensor Cloning ===")
    
    def f(x):
        return x + 1

    def g(x):
        return x + 1

    f = torch.compile(f, mode="reduce-overhead")
    g = torch.compile(g, mode="reduce-overhead")

    print("Running: g(f(torch.randn(2, device='cuda')).clone())")
    
    try:
        x = torch.randn(2, device="cuda")
        intermediate = f(x)
        result = g(intermediate.clone())  # Clone to prevent overwrite
        print(f"✓ Success! Result: {result}")
        return True
    except RuntimeError as e:
        print(f"✗ Error occurred: {e}")
        return False


def test_workaround_mark_step():
    """Test workaround using mark_step_begin"""
    print("\n=== Testing Workaround: Mark Step Begin ===")
    
    def f(x):
        return x + 1

    def g(x):
        return x + 1

    f = torch.compile(f, mode="reduce-overhead")
    g = torch.compile(g, mode="reduce-overhead")

    print("Running with torch.compiler.cudagraph_mark_step_begin()")
    
    try:
        x = torch.randn(2, device="cuda")
        torch.compiler.cudagraph_mark_step_begin()
        intermediate = f(x)
        torch.compiler.cudagraph_mark_step_begin()
        result = g(intermediate)
        print(f"✓ Success! Result: {result}")
        return True
    except RuntimeError as e:
        print(f"✗ Error occurred: {e}")
        return False


def test_no_grad_workaround():
    """Test workaround using torch.no_grad"""
    print("\n=== Testing Workaround: torch.no_grad ===")
    
    def f(x):
        return x + 1

    def g(x):
        return x + 1

    f = torch.compile(f, mode="reduce-overhead")
    g = torch.compile(g, mode="reduce-overhead")

    print("Running with torch.no_grad()")
    
    try:
        with torch.no_grad():
            x = torch.randn(2, device="cuda")
            result = g(f(x))
        print(f"✓ Success! Result: {result}")
        return True
    except RuntimeError as e:
        print(f"✗ Error occurred: {e}")
        return False


def main():
    if not torch.cuda.is_available():
        print("CUDA not available, skipping tests")
        return
    
    print("Testing CUDAGraph Tree heuristics fix for issue #160281")
    print("=" * 60)
    
    results = []
    results.append(("Original Issue", test_original_issue()))
    results.append(("Clone Workaround", test_workaround_clone()))
    results.append(("Mark Step Workaround", test_workaround_mark_step()))
    results.append(("No Grad Workaround", test_no_grad_workaround()))
    
    print("\n" + "=" * 60)
    print("SUMMARY:")
    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"  {test_name}: {status}")
    
    if results[0][1]:  # Original issue test passed
        print("\n✓ The CUDAGraph Tree heuristics fix appears to be working!")
    else:
        print("\n✗ The original issue still exists. Workarounds are available.")


if __name__ == "__main__":
    main()
