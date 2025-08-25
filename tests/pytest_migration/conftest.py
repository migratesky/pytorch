"""
PyTest configuration for the new pytest-based test infrastructure.
This configuration is designed to work alongside PyTorch's existing test infrastructure.
"""
import os
import sys
import platform

import pytest

def pytest_configure(config):
    """Register markers and configure pytest."""
    # Common capability markers
    config.addinivalue_line("markers", "cuda: mark test as requiring CUDA")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "serial: mark test to run in a serialized group")
    config.addinivalue_line("markers", "flaky: mark test as flaky (will rerun if plugin present)")

    # Platform/backend skip markers (POC mapping of run_test.py blocklists)
    config.addinivalue_line("markers", "windows_skip: skip on Windows")
    config.addinivalue_line("markers", "rocm_skip: skip on ROCm builds")
    config.addinivalue_line("markers", "s390x_skip: skip on s390x arch")
    config.addinivalue_line("markers", "xpu_skip: skip on XPU builds")

    # Default timeout (requires pytest-timeout). Best-effort: only set if plugin is installed
    timeout = os.getenv("PYTEST_DEFAULT_TIMEOUT", "300")
    try:
        # Accessing option attributes only works after parsing, but config.option may exist here.
        # Guard with hasattr to avoid AttributeError when plugin is absent.
        if hasattr(config, "option") and hasattr(config.option, "timeout") and not config.option.timeout:
            config.option.timeout = int(timeout)
    except Exception:
        # No-op if plugin not installed
        pass

    # Default reruns for flaky tests (requires pytest-rerunfailures). Best-effort
    try:
        if hasattr(config, "option") and hasattr(config.option, "reruns") and config.option.reruns is None:
            config.option.reruns = int(os.getenv("PYTEST_RERUNS", "1"))
        if hasattr(config, "option") and hasattr(config.option, "reruns_delay") and config.option.reruns_delay is None:
            config.option.reruns_delay = int(os.getenv("PYTEST_RERUNS_DELAY", "1"))
    except Exception:
        pass

    # POC sharding via pytest-split (best-effort): set splits/group defaults from env
    try:
        if hasattr(config, "option") and hasattr(config.option, "splits") and not config.option.splits:
            env_splits = os.getenv("PYTEST_SPLITS") or os.getenv("NUM_TEST_SHARDS")
            if env_splits:
                config.option.splits = int(env_splits)
        if hasattr(config, "option") and hasattr(config.option, "group") and not config.option.group:
            env_group = os.getenv("PYTEST_GROUP") or os.getenv("SHARD_NUMBER")
            if env_group:
                config.option.group = int(env_group)
    except Exception:
        # If plugin is not present or options missing, ignore
        pass

@pytest.fixture(scope="session")
def cuda_available():
    """Check if CUDA is available."""
    try:
        import torch  # noqa: F401
        return torch.cuda.is_available()
    except Exception:
        # If torch is not importable or CUDA check fails, treat as not available
        return False

@pytest.fixture(autouse=True)
def skip_cuda(request, cuda_available):
    """Skip CUDA tests if CUDA is not available."""
    if request.node.get_closest_marker('cuda') and not cuda_available:
        pytest.skip('CUDA not available')

@pytest.fixture(scope="function")
def cuda_device(cuda_available):
    """Provide CUDA device if available."""
    if not cuda_available:
        pytest.skip('CUDA not available')
    import torch
    return torch.device('cuda')

@pytest.fixture(autouse=True)
def cuda_memory_cleanup():
    """Clean up CUDA memory before and after each test."""
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            yield
            torch.cuda.empty_cache()
            return
    except Exception:
        pass
    # Default when torch is not available
    yield


def _is_rocm_build() -> bool:
    try:
        import torch
        return bool(getattr(torch.version, "hip", None))
    except Exception:
        return False


def _is_xpu_build() -> bool:
    # Heuristic: BUILD_ENVIRONMENT contains xpu
    return "xpu" in os.getenv("BUILD_ENVIRONMENT", "")


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config, items: list[pytest.Item]):
    """Apply platform/backend blocklist skips and simple serial grouping.

    This is a lightweight POC replacement for portions of run_test.py policies.
    """
    is_windows = sys.platform.startswith("win")
    is_s390x = platform.machine() == "s390x"
    is_rocm = _is_rocm_build()
    is_xpu = _is_xpu_build()

    for item in items:
        # Platform/backend conditional skips via markers on tests or modules
        if item.get_closest_marker("windows_skip") and is_windows:
            item.add_marker(pytest.mark.skip(reason="Skipped on Windows (POC blocklist)"))
        if item.get_closest_marker("rocm_skip") and is_rocm:
            item.add_marker(pytest.mark.skip(reason="Skipped on ROCm (POC blocklist)"))
        if item.get_closest_marker("s390x_skip") and is_s390x:
            item.add_marker(pytest.mark.skip(reason="Skipped on s390x (POC blocklist)"))
        if item.get_closest_marker("xpu_skip") and is_xpu:
            item.add_marker(pytest.mark.skip(reason="Skipped on XPU (POC blocklist)"))

        # If test is marked flaky and rerun plugin is present, ensure at least 1 rerun
        if item.get_closest_marker("flaky") and hasattr(config.option, "reruns"):
            if not config.option.reruns:
                config.option.reruns = 1

    # Optional: group serial tests if pytest-xdist is used
    # If pytest-xdist's xdist_group plugin is available, mark serial items into same group
    try:
        import xdist  # noqa: F401
        # Some environments have pytest-xdist but not xdist-grouping; best-effort
        for item in items:
            if item.get_closest_marker("serial"):
                item.add_marker(pytest.mark.xdist_group("serial_group"))
    except Exception:
        # No xdist or grouping available; serial marker becomes documentation-only in this POC
        pass