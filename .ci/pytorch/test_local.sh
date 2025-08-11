#!/bin/bash
"""
Local testing script for PyTorch CI Python test runner.

This script sets up the proper environment variables for local testing
and provides a convenient interface to test the Python runner locally.
"""

set -e

# Default values
BUILD_ENVIRONMENT="${BUILD_ENVIRONMENT:-linux-focal-py3.8-gcc7}"
TEST_CONFIG="${TEST_CONFIG:-smoke}"
SHARD_NUMBER="${SHARD_NUMBER:-1}"
NUM_TEST_SHARDS="${NUM_TEST_SHARDS:-1}"
USE_PYTHON_TEST_RUNNER="${USE_PYTHON_TEST_RUNNER:-1}"
NO_SHELL_FALLBACK="${NO_SHELL_FALLBACK:-1}"

# Parse command line arguments
DRY_RUN=""
VERBOSE=""
FORCE_PYTHON=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN="--dry-run"
            shift
            ;;
        --verbose)
            VERBOSE="--verbose"
            shift
            ;;
        --force-python)
            FORCE_PYTHON="--force-python"
            USE_PYTHON_TEST_RUNNER=1
            shift
            ;;
        --build-env)
            BUILD_ENVIRONMENT="$2"
            shift 2
            ;;
        --test-config)
            TEST_CONFIG="$2"
            shift 2
            ;;
        --shard)
            SHARD_NUMBER="$2"
            shift 2
            ;;
        --total-shards)
            NUM_TEST_SHARDS="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --dry-run              Show what would be run without executing"
            echo "  --verbose              Enable verbose output"
            echo "  --force-python         Force Python test runner"
            echo "  --build-env ENV        Set BUILD_ENVIRONMENT (default: linux-focal-py3.8-gcc7)"
            echo "  --test-config CONFIG   Set TEST_CONFIG (default: smoke)"
            echo "  --shard N              Set SHARD_NUMBER (default: 1)"
            echo "  --total-shards N       Set NUM_TEST_SHARDS (default: 1)"
            echo "  --help, -h             Show this help message"
            echo ""
            echo "Environment Variables:"
            echo "  BUILD_ENVIRONMENT      Build environment identifier"
            echo "  TEST_CONFIG           Test configuration to run"
            echo "  SHARD_NUMBER          Current shard number (1-based)"
            echo "  NUM_TEST_SHARDS       Total number of shards"
            echo "  USE_PYTHON_TEST_RUNNER Force Python test runner"
            echo "  NO_SHELL_FALLBACK     Disable shell script fallback"
            echo ""
            echo "Examples:"
            echo "  $0 --dry-run --verbose"
            echo "  $0 --test-config python --build-env linux-focal-py3.9-gcc7"
            echo "  $0 --test-config inductor --shard 2 --total-shards 4"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Export environment variables
export BUILD_ENVIRONMENT
export TEST_CONFIG
export SHARD_NUMBER
export NUM_TEST_SHARDS
export USE_PYTHON_TEST_RUNNER
export NO_SHELL_FALLBACK

# Print configuration
echo "=== PyTorch CI Local Test Configuration ==="
echo "BUILD_ENVIRONMENT: $BUILD_ENVIRONMENT"
echo "TEST_CONFIG: $TEST_CONFIG"
echo "SHARD_NUMBER: $SHARD_NUMBER"
echo "NUM_TEST_SHARDS: $NUM_TEST_SHARDS"
echo "USE_PYTHON_TEST_RUNNER: $USE_PYTHON_TEST_RUNNER"
echo "NO_SHELL_FALLBACK: $NO_SHELL_FALLBACK"
echo "============================================"
echo ""

# Change to the CI directory
cd "$(dirname "${BASH_SOURCE[0]}")"

# Run the Python test runner
echo "Running Python test runner..."
python3 test_python.py $DRY_RUN $VERBOSE $FORCE_PYTHON
