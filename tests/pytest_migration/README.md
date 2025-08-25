# Pytest Migration POC

This directory contains pytest-native tests and configuration used to prototype migrating PyTorch's test orchestration away from bespoke bash/run_test.py flows.

What this POC demonstrates:

- Platform/backend policy mapping via markers
  - windows_skip, rocm_skip, s390x_skip, xpu_skip, serial, flaky, cuda, slow
- Best-effort defaults (only applied if plugin is installed)
  - pytest-timeout: PYTEST_DEFAULT_TIMEOUT (default 300s)
  - pytest-rerunfailures: PYTEST_RERUNS (default 1), PYTEST_RERUNS_DELAY (default 1)
- CUDA gating via fixtures and automatic skipping

Run examples:

```bash
# Run all POC tests
pytest -q tests/pytest_migration

# Only CUDA tests
pytest -q tests/pytest_migration -m cuda

# Exclude slow
pytest -q tests/pytest_migration -m "not slow"

# Parallel, serialize tests marked with `@pytest.mark.serial` (requires xdist)
pytest -q tests/pytest_migration -n auto

# Configure defaults via env
export PYTEST_DEFAULT_TIMEOUT=300
export PYTEST_RERUNS=1
export PYTEST_RERUNS_DELAY=1
pytest -q tests/pytest_migration
```

Notes:
- Sharding/balancing, distributed matrix setup, C++ build/test, coverage/metrics are out-of-scope for this POC and remain under run_test.py/CI.
- This POC is designed to coexist with the current infrastructure.
