#!/usr/bin/env python3
"""
LibTorch JIT Test Runner - Simple Direct Implementation
Replaces the test_libtorch_jit function from test.sh with clean Python execution.
Handles setup/cleanup and C++ test execution without the bloated run_test.py.
"""

import os
import sys
import subprocess
from pathlib import Path


def run_command(cmd: list[str], cwd: str = None, env: dict = None) -> bool:
    """Run a command and return success status"""
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    
    print(f"🔧 Running: {' '.join(cmd)}")
    if cwd:
        print(f"   Working directory: {cwd}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            env=full_env,
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed with exit code {e.returncode}")
        return False


def setup_jit_tests() -> bool:
    """Run JIT test setup - equivalent to: pushd test; python cpp/jit/tests_setup.py setup; popd"""
    print("🚀 Setting up LibTorch JIT tests...")
    return run_command(
        [sys.executable, "cpp/jit/tests_setup.py", "setup"],
        cwd="test"
    )


def cleanup_jit_tests() -> bool:
    """Run JIT test cleanup - equivalent to: pushd test; python cpp/jit/tests_setup.py shutdown; popd"""
    print("🧹 Cleaning up LibTorch JIT tests...")
    return run_command(
        [sys.executable, "cpp/jit/tests_setup.py", "shutdown"],
        cwd="test"
    )


def run_cpp_tests() -> bool:
    """Run the actual C++ tests - equivalent to the original run_test.py call"""
    build_env = os.environ.get("BUILD_ENVIRONMENT", "")
    test_config = os.environ.get("TEST_CONFIG", "")
    
    # Build the command equivalent to the original shell logic
    cmd = [
        sys.executable, "test/run_test.py",
        "--cpp",
        "--verbose", 
        "-i", "cpp/test_jit", "cpp/test_lazy"
    ]
    
    # Environment-based conditional logic (replaces shell if/else)
    extra_env = {}
    if "cuda" in build_env and "nogpu" not in test_config:
        print("🔥 Running LibTorch JIT tests with CUDA support")
        extra_env["LTC_TS_CUDA"] = "1"
    else:
        print("💻 Running LibTorch JIT tests without CUDA")
        cmd.extend(["-k", "not CUDA"])
    
    return run_command(cmd, env=extra_env)


def main():
    """Main entry point - replaces the test_libtorch_jit shell function"""
    print("🚀 Starting LibTorch JIT tests (simplified Python implementation)")
    
    # Ensure we're in the repo root
    repo_root = Path(__file__).parent.parent.parent
    os.chdir(repo_root)
    
    success = True
    
    try:
        # Phase 1: Setup
        if not setup_jit_tests():
            print("❌ Setup failed")
            return 1
        
        # Phase 2: Run tests
        if not run_cpp_tests():
            print("❌ C++ tests failed")
            success = False
        
    finally:
        # Phase 3: Cleanup (always run)
        if not cleanup_jit_tests():
            print("⚠️  Cleanup failed")
    
    if success:
        print("✅ LibTorch JIT tests completed successfully!")
        return 0
    else:
        print("❌ LibTorch JIT tests failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
