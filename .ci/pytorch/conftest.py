#!/usr/bin/env python3
"""
PyTorch CI pytest configuration.
This file configures pytest for PyTorch-specific testing needs.
"""

import os
import sys
from pathlib import Path

# Add the plugin to pytest
pytest_plugins = ["pytest_pytorch_plugin"]

# Ensure we can import the plugin
sys.path.insert(0, str(Path(__file__).parent))

# PyTorch-specific pytest configuration
def pytest_addoption(parser):
    """Add PyTorch-specific command line options"""
    parser.addoption(
        "--libtorch-jit",
        action="store_true",
        default=False,
        help="Run LibTorch JIT tests specifically"
    )
    parser.addoption(
        "--cuda-only",
        action="store_true", 
        default=False,
        help="Run only CUDA tests"
    )
    parser.addoption(
        "--no-cuda",
        action="store_true",
        default=False,
        help="Skip CUDA tests"
    )


def pytest_configure(config):
    """Additional configuration for PyTorch tests"""
    # Set test reports directory
    test_reports_dir = Path.cwd() / "test" / "test-reports"
    test_reports_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure XML output if in CI
    if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
        if not config.getoption("--junit-xml"):
            xml_path = test_reports_dir / "pytest_results.xml"
            config.option.junit_xml = str(xml_path)


def pytest_collection_modifyitems(config, items):
    """Filter tests based on command line options"""
    if config.getoption("--libtorch-jit"):
        # Only run LibTorch JIT tests
        jit_items = []
        for item in items:
            if "test_jit" in str(item.fspath) or "test_lazy" in str(item.fspath):
                jit_items.append(item)
        items[:] = jit_items
    
    if config.getoption("--cuda-only"):
        # Only run CUDA tests
        cuda_items = []
        for item in items:
            if "cuda" in item.nodeid.lower() or item.get_closest_marker("cuda_required"):
                cuda_items.append(item)
        items[:] = cuda_items
    
    if config.getoption("--no-cuda"):
        # Skip CUDA tests
        import pytest
        skip_cuda = pytest.mark.skip(reason="CUDA tests disabled via --no-cuda")
        for item in items:
            if "cuda" in item.nodeid.lower() or item.get_closest_marker("cuda_required"):
                item.add_marker(skip_cuda)
