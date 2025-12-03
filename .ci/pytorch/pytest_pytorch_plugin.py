#!/usr/bin/env python3
"""
PyTorch-specific pytest plugin for CI testing.
Replaces the bloated run_test.py with clean, standard pytest functionality.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

import pytest


class PytorchTestEnvironment:
    """Manages PyTorch-specific test environment setup"""
    
    @staticmethod
    def is_cuda_build() -> bool:
        """Check if this is a CUDA build environment"""
        build_env = os.environ.get("BUILD_ENVIRONMENT", "")
        return "cuda" in build_env
    
    @staticmethod
    def is_nogpu_test() -> bool:
        """Check if GPU tests should be skipped"""
        test_config = os.environ.get("TEST_CONFIG", "")
        return "nogpu" in test_config
    
    @staticmethod
    def setup_cuda_environment():
        """Set up CUDA-specific environment variables"""
        if PytorchTestEnvironment.is_cuda_build() and not PytorchTestEnvironment.is_nogpu_test():
            os.environ["LTC_TS_CUDA"] = "1"
            print("🔧 CUDA environment configured")
    
    @staticmethod
    def get_test_directory() -> Path:
        """Get the PyTorch test directory"""
        # Assume we're running from the repo root
        return Path.cwd() / "test"


class LibtorchJitTestManager:
    """Manages LibTorch JIT test lifecycle (setup/cleanup)"""
    
    def __init__(self):
        self.test_dir = PytorchTestEnvironment.get_test_directory()
        self.setup_script = self.test_dir / "cpp" / "jit" / "tests_setup.py"
    
    def setup(self) -> bool:
        """Run JIT test setup"""
        print("🚀 Setting up LibTorch JIT tests...")
        try:
            result = subprocess.run(
                [sys.executable, str(self.setup_script), "setup"],
                cwd=str(self.test_dir),
                check=True,
                capture_output=True,
                text=True
            )
            print("✅ LibTorch JIT setup completed")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ LibTorch JIT setup failed: {e}")
            print(f"stdout: {e.stdout}")
            print(f"stderr: {e.stderr}")
            return False
    
    def cleanup(self) -> bool:
        """Run JIT test cleanup"""
        print("🧹 Cleaning up LibTorch JIT tests...")
        try:
            result = subprocess.run(
                [sys.executable, str(self.setup_script), "shutdown"],
                cwd=str(self.test_dir),
                check=True,
                capture_output=True,
                text=True
            )
            print("✅ LibTorch JIT cleanup completed")
            return True
        except subprocess.CalledProcessError as e:
            print(f"⚠️  LibTorch JIT cleanup failed: {e}")
            print(f"stdout: {e.stdout}")
            print(f"stderr: {e.stderr}")
            return False


# Global test manager instance
_jit_manager = None


def pytest_configure(config):
    """Configure PyTorch-specific test environment"""
    print("🔧 Configuring PyTorch test environment...")
    
    # Set up environment variables
    PytorchTestEnvironment.setup_cuda_environment()
    
    # Add custom markers
    config.addinivalue_line(
        "markers", "libtorch_jit: marks tests as LibTorch JIT tests"
    )
    config.addinivalue_line(
        "markers", "cuda_required: marks tests that require CUDA"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection based on environment"""
    if PytorchTestEnvironment.is_nogpu_test():
        # Skip CUDA tests when nogpu is specified
        skip_cuda = pytest.mark.skip(reason="CUDA tests disabled (nogpu)")
        for item in items:
            if "cuda" in item.nodeid.lower() or item.get_closest_marker("cuda_required"):
                item.add_marker(skip_cuda)


def pytest_sessionstart(session):
    """Set up test session - run setup for LibTorch JIT tests if needed"""
    global _jit_manager
    
    # Check if we're running LibTorch JIT tests
    test_files = [item.fspath.basename for item in session.items]
    if any("test_jit" in f or "test_lazy" in f for f in test_files):
        print("🎯 LibTorch JIT tests detected, running setup...")
        _jit_manager = LibtorchJitTestManager()
        if not _jit_manager.setup():
            pytest.exit("LibTorch JIT setup failed", returncode=1)


def pytest_sessionfinish(session, exitstatus):
    """Clean up test session"""
    global _jit_manager
    
    if _jit_manager:
        print("🧹 Running LibTorch JIT cleanup...")
        _jit_manager.cleanup()


def pytest_runtest_setup(item):
    """Set up individual test runs"""
    # Add any per-test setup here if needed
    pass


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Provide custom terminal summary"""
    if exitstatus == 0:
        terminalreporter.write_line("🎉 All PyTorch tests passed!", green=True)
    else:
        terminalreporter.write_line("❌ Some PyTorch tests failed", red=True)


# Pytest plugin registration
def pytest_plugins():
    """Register this as a pytest plugin"""
    return ["pytest_pytorch_plugin"]
