#!/usr/bin/env python3
"""
Script to run LibTorchTestRunner tests.
"""

import sys
import os

# Add the CI utils directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.ci', 'pytorch', 'utils'))

from libtorch_test_runners import LibTorchTestRunner

def main():
    """Run LibTorchTestRunner tests."""
    print("Initializing LibTorchTestRunner...")
    
    # Initialize the test runner
    runner = LibTorchTestRunner()
    
    print("\n" + "="*60)
    print("Running LibTorch Tests")
    print("="*60)
    
    # Run basic LibTorch tests
    print("\n1. Running basic LibTorch tests...")
    success1 = runner.run_libtorch_tests()
    print(f"LibTorch tests: {'PASSED' if success1 else 'FAILED'}")
    
    # Run LibTorch JIT tests
    print("\n2. Running LibTorch JIT tests...")
    success2 = runner.run_libtorch_jit_tests()
    print(f"LibTorch JIT tests: {'PASSED' if success2 else 'FAILED'}")
    
    # Run LibTorch API tests
    print("\n3. Running LibTorch API tests...")
    success3 = runner.run_libtorch_api_tests()
    print(f"LibTorch API tests: {'PASSED' if success3 else 'FAILED'}")
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print(f"LibTorch tests:     {'PASSED' if success1 else 'FAILED'}")
    print(f"LibTorch JIT tests: {'PASSED' if success2 else 'FAILED'}")
    print(f"LibTorch API tests: {'PASSED' if success3 else 'FAILED'}")
    
    overall_success = success1 and success2 and success3
    print(f"\nOverall result: {'ALL TESTS PASSED' if overall_success else 'SOME TESTS FAILED'}")
    
    return 0 if overall_success else 1

if __name__ == "__main__":
    sys.exit(main())
