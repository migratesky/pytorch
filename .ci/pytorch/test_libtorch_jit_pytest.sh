#!/bin/bash
# LibTorch JIT Test Runner - Shell wrapper for pytest implementation
# This replaces the test_libtorch_jit function in test.sh

set -ex -o pipefail

echo "🚀 LibTorch JIT Tests - Modern pytest implementation"
echo "Environment: BUILD_ENVIRONMENT=${BUILD_ENVIRONMENT}"
echo "Test Config: TEST_CONFIG=${TEST_CONFIG}"

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Change to repo root
cd "${REPO_ROOT}"

# Install pytest dependencies if needed
if ! python -c "import pytest" 2>/dev/null; then
    echo "📦 Installing pytest dependencies..."
    pip install -r .ci/pytorch/requirements-pytest.txt
fi

# Run the pytest-based LibTorch JIT tests
echo "🎯 Executing LibTorch JIT tests via pytest..."
python .ci/pytorch/run_libtorch_jit_tests.py

echo "✅ LibTorch JIT tests completed"
