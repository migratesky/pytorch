# CI Integration Strategy for Python Test Runner

## Overview

This document outlines the strategy for integrating the Python-based test runner into PyTorch's CI pipeline as a replacement for the existing shell-based `test.sh` script.

## Current CI Architecture

The current CI system (`.github/workflows/_linux-test.yml`) executes tests using:

```bash
docker exec -t "${container_name}" sh -c "python3 -m pip install $(echo dist/*.whl)[opt-einsum] && ${TEST_COMMAND}"
```

Where `TEST_COMMAND` is typically `.ci/pytorch/test.sh`.

## Integration Approach

### Phase 1: Parallel Testing (Current)
- ✅ Python test infrastructure implemented
- ✅ Import and packaging issues resolved
- ✅ Validation script confirms all test suites load successfully
- ✅ CI-compatible Python test runner (`test_python.py`) created

### Phase 2: Gradual Rollout (Next Steps)

#### Step 1: Create Feature Flag
Add environment variable `USE_PYTHON_TEST_RUNNER` to enable Python-based testing:

```yaml
# In _linux-test.yml
env:
  USE_PYTHON_TEST_RUNNER: ${{ inputs.use-python-test-runner || 'false' }}
```

#### Step 2: Modify Test Command Selection
Update the test command selection logic:

```bash
if [[ $TEST_CONFIG == 'multigpu' ]]; then
  TEST_COMMAND=.ci/pytorch/multigpu-test.sh
elif [[ $BUILD_ENVIRONMENT == *onnx* ]]; then
  TEST_COMMAND=.ci/onnx/test.sh
elif [[ $USE_PYTHON_TEST_RUNNER == 'true' ]]; then
  TEST_COMMAND="python3 .ci/pytorch/test_python.py"
else
  TEST_COMMAND=.ci/pytorch/test.sh
fi
```

#### Step 3: Selective Testing
Start with low-risk test configurations:
- `smoke` tests
- `docs_test` 
- Single-shard configurations
- Non-CUDA builds

#### Step 4: Gradual Expansion
Progressively enable Python test runner for:
- Multi-shard configurations
- CUDA builds
- Distributed tests
- Performance benchmarks

### Phase 3: Full Migration

#### Step 1: Default to Python Runner
Change default behavior to use Python runner with shell fallback:

```bash
if [[ $USE_SHELL_TEST_RUNNER == 'true' ]]; then
  TEST_COMMAND=.ci/pytorch/test.sh
else
  TEST_COMMAND="python3 .ci/pytorch/test_python.py --fallback-on-error"
fi
```

#### Step 2: Remove Shell Script
After validation period, remove `test.sh` and related shell infrastructure.

## Safety Mechanisms

### 1. Automatic Fallback
The Python test runner includes automatic fallback to shell script:
- On import failures
- On Python infrastructure errors
- When `--fallback-on-error` flag is used

### 2. Environment Validation
- Validates all required environment variables
- Checks for missing dependencies
- Provides detailed error messages

### 3. Dry-Run Mode
- Test configuration without execution
- Validate test suite selection
- Debug environment issues

## Testing Strategy

### 1. Local Testing
```bash
# Test current environment
cd /Users/krishna.pinnaka/pytorch/.ci/pytorch
python3 test_python.py --dry-run --verbose

# Test specific configurations
BUILD_ENVIRONMENT=linux-focal-cuda12.1-py3.8-gcc9 \
TEST_CONFIG=distributed \
SHARD_NUMBER=1 \
NUM_TEST_SHARDS=2 \
python3 test_python.py --dry-run
```

### 2. CI Testing Workflow

#### Create Test Workflow
Create `.github/workflows/test-python-runner.yml`:

```yaml
name: Test Python Runner

on:
  pull_request:
    paths:
      - '.ci/pytorch/test_python.py'
      - '.ci/pytorch/test_suites/**'
      - '.ci/pytorch/test_config/**'
      - '.ci/pytorch/utils/**'

jobs:
  test-python-runner:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        test-config: [smoke, docs_test, python]
        build-env: [linux-focal-py3.8-gcc7, linux-focal-cuda11.8-py3.8-gcc9]
    
    steps:
      - uses: actions/checkout@v4
      - name: Test Python Runner
        env:
          BUILD_ENVIRONMENT: ${{ matrix.build-env }}
          TEST_CONFIG: ${{ matrix.test-config }}
          USE_PYTHON_TEST_RUNNER: true
        run: |
          cd .ci/pytorch
          python3 test_python.py --dry-run --verbose
```

### 3. Validation Checklist

Before enabling in production CI:
- [ ] All test suites import successfully
- [ ] Environment detection works correctly
- [ ] Shell function delegation operates properly
- [ ] Fallback mechanism functions as expected
- [ ] Performance is comparable to shell script
- [ ] All environment variables are handled
- [ ] Error handling is robust

## Rollback Plan

### Immediate Rollback
If issues are detected:
1. Set `USE_PYTHON_TEST_RUNNER=false` in workflow
2. Revert to shell-based testing immediately
3. Investigate and fix issues

### Gradual Rollback
For partial issues:
1. Disable Python runner for specific configurations
2. Maintain shell fallback for affected tests
3. Fix issues incrementally

## Monitoring and Metrics

### Success Metrics
- Test execution time comparison
- Test failure rate comparison
- CI pipeline reliability
- Error rate and types

### Monitoring Points
- Test suite selection accuracy
- Shell function execution success
- Import and dependency resolution
- Resource utilization

## Benefits of Migration

### Maintainability
- Modular, object-oriented test structure
- Clear separation of concerns
- Easier to add new test configurations
- Better error handling and logging

### Flexibility
- Dynamic test suite selection
- Conditional test execution
- Environment-specific optimizations
- Better integration with Python tooling

### Reliability
- Robust error handling
- Automatic fallback mechanisms
- Comprehensive validation
- Better debugging capabilities

## Timeline

### Week 1-2: Preparation
- Create feature flag infrastructure
- Implement CI workflow modifications
- Set up monitoring and validation

### Week 3-4: Limited Rollout
- Enable for smoke tests and docs
- Monitor performance and reliability
- Fix any discovered issues

### Week 5-8: Gradual Expansion
- Enable for more test configurations
- Expand to CUDA and distributed tests
- Collect performance metrics

### Week 9-12: Full Migration
- Default to Python runner
- Remove shell script dependencies
- Complete documentation updates

This strategy ensures a safe, gradual migration with multiple safety nets and rollback options.
