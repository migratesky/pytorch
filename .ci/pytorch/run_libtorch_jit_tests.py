#!/usr/bin/env python3
"""
LibTorch JIT Test Runner - Pure pytest implementation
Replaces the test_libtorch_jit function from test.sh with clean pytest execution.
"""

import os
import sys
import subprocess
from pathlib import Path


def get_pytest_command() -> list[str]:
    """Build the pytest command based on environment"""
    cmd = [
        sys.executable, "-m", "pytest",
        # Test paths - equivalent to cpp/test_jit cpp/test_lazy
        "test/cpp/test_jit",
        "test/cpp/test_lazy",
        # Verbose output
        "-v",
        # Short traceback format
        "--tb=short",
        # Configuration directory (will use conftest.py)
        "--confcutdir=.ci/pytorch",
        # Generate XML report for CI
        "--junit-xml=test/test-reports/libtorch_jit_results.xml",
        # Parallel execution for faster tests
        "-n", "auto",
        # Retry failed tests twice (like the original)
        "--reruns=2",
    ]
    
    # Environment-based conditional logic (replaces shell if/else)
    build_env = os.environ.get("BUILD_ENVIRONMENT", "")
    test_config = os.environ.get("TEST_CONFIG", "")
    
    if "cuda" in build_env and "nogpu" not in test_config:
        # CUDA build with GPU tests enabled
        print("🔥 Running LibTorch JIT tests with CUDA support")
        # The plugin will set LTC_TS_CUDA=1 automatically
    else:
        # Non-CUDA build or GPU tests disabled
        print("💻 Running LibTorch JIT tests without CUDA")
        cmd.extend(["-k", "not CUDA"])  # Skip CUDA tests
    
    return cmd


def main():
    """Main entry point - replaces the test_libtorch_jit shell function"""
    print("🚀 Starting LibTorch JIT tests (pytest implementation)")
    
    # Ensure we're in the right directory
    repo_root = Path(__file__).parent.parent.parent
    os.chdir(repo_root)
    
    # Add our CI directory to Python path for plugin imports
    ci_dir = repo_root / ".ci" / "pytorch"
    sys.path.insert(0, str(ci_dir))
    
    # Build pytest command
    pytest_cmd = get_pytest_command()
    
    print(f"📋 Running command: {' '.join(pytest_cmd)}")
    
    # Execute pytest
    try:
        result = subprocess.run(pytest_cmd, check=False)
        
        if result.returncode == 0:
            print("✅ LibTorch JIT tests completed successfully!")
        else:
            print(f"❌ LibTorch JIT tests failed with exit code {result.returncode}")
        
        return result.returncode
        
    except Exception as e:
        print(f"💥 Error running LibTorch JIT tests: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
