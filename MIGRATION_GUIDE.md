# PyTorch test.sh Migration Guide

## Overview
This guide helps you understand and run the `.ci/pytorch/test.sh` script locally for migration to Python.

## Key Findings from Local Testing

### ✅ What Works Locally
1. **Environment Setup**: The script correctly detects local environment
2. **Configuration Checks**: PyTorch config detection works
3. **Debug Assertions**: Core PyTorch functionality tests pass
4. **Script Structure Analysis**: We can analyze the 157 conditional blocks and 155 Python commands

### ⚠️ What Requires Workarounds
1. **Dependency Conflicts**: CI-specific packages may conflict with local PyTorch
2. **Version Mismatches**: Source code tests vs installed PyTorch versions
3. **CUDA Dependencies**: Many CI dependencies expect CUDA on Linux

## How to Run test.sh Locally

### Method 1: Direct Execution (Partial Success)
```bash
cd /Users/krishna.pinnaka/pytorch
BUILD_ENVIRONMENT=local TEST_CONFIG=smoke bash .ci/pytorch/test.sh
```

**Expected Behavior:**
- ✅ Environment setup works
- ✅ PyTorch configuration detection works  
- ✅ Debug assertion tests pass
- ❌ Full test suite may fail on dependency issues

### Method 2: Targeted Function Execution
Run specific parts of the script by extracting key functions:

```bash
# Run debug assertion (from line 283)
cd test && python -c "import torch; torch._C._crash_if_debug_asserts_fail(424242)"

# Show PyTorch config (from script)
cd test && python -c "import torch; print(torch.__config__.show())"

# Run basic tests (equivalent to test_python_smoke)
python test/run_test.py --include test_matmul_cuda --verbose
```

## Shell Script Structure Analysis

### Core Functions Identified:
1. `test_python_smoke()` - Line 325-329
2. `test_python()` - Line 319-323  
3. `test_python_shard()` - Line 303-317
4. `test_h100_distributed()` - Line 331-337
5. `test_h100_symm_mem()` - Line 339-346

### Key Patterns for Migration:

#### 1. Environment Variable Checks
```bash
# Shell script pattern:
if [[ "$TEST_CONFIG" == "smoke" ]]; then
    test_python_smoke
fi
```

```python
# Python equivalent:
if os.environ.get('TEST_CONFIG') == 'smoke':
    run_python_smoke_tests()
```

#### 2. Test Execution Pattern
```bash
# Shell script:
time python test/run_test.py --include test_matmul_cuda inductor/test_fp8 --verbose
```

```python
# Python equivalent:
import subprocess
import time

start_time = time.time()
result = subprocess.run([
    'python', 'test/run_test.py',
    '--include', 'test_matmul_cuda', 'inductor/test_fp8',
    '--verbose'
], timeout=300)
execution_time = time.time() - start_time
```

#### 3. Conditional Logic Migration
The script has 157 conditional blocks like:
```bash
[[ "$BUILD_ENVIRONMENT" == *cuda* ]]
[[ "$TEST_CONFIG" == *distributed* ]]
[[ "$SHARD_NUMBER" -gt 1 ]]
```

Python equivalents:
```python
build_env = os.environ.get('BUILD_ENVIRONMENT', '')
test_config = os.environ.get('TEST_CONFIG', '')
shard_number = int(os.environ.get('SHARD_NUMBER', '1'))

if 'cuda' in build_env:
    # CUDA-specific logic
if 'distributed' in test_config:
    # Distributed test logic
if shard_number > 1:
    # Sharding logic
```

## Migration Strategy

### Phase 1: Core Structure
1. **Environment Setup**: Migrate environment variable handling
2. **Configuration Detection**: Port PyTorch config checks
3. **Test Selection Logic**: Convert conditional test selection

### Phase 2: Test Execution
1. **Test Runner Integration**: Replace subprocess calls with direct test runner usage
2. **Timeout Handling**: Implement proper timeout and error handling
3. **Parallel Execution**: Port shard-based parallel testing

### Phase 3: CI Integration
1. **Artifact Handling**: Port `--upload-artifacts-while-running` logic
2. **Git Cleanliness**: Port `assert_git_not_dirty` checks
3. **Error Reporting**: Implement proper error reporting and exit codes

## Recommended Python Test Structure

```python
class PyTorchCITest:
    def __init__(self):
        self.build_env = os.environ.get('BUILD_ENVIRONMENT', '')
        self.test_config = os.environ.get('TEST_CONFIG', 'default')
        self.shard_number = int(os.environ.get('SHARD_NUMBER', '1'))
        self.num_shards = int(os.environ.get('NUM_TEST_SHARDS', '1'))
    
    def run_smoke_tests(self):
        """Equivalent to test_python_smoke()"""
        return self._run_test_suite([
            'test_matmul_cuda',
            'inductor/test_fp8', 
            'inductor/test_max_autotune'
        ])
    
    def run_full_tests(self):
        """Equivalent to test_python()"""
        return self._run_test_suite(
            exclude=['--exclude-jit-executor', '--exclude-distributed-tests']
        )
    
    def _run_test_suite(self, include=None, exclude=None, timeout=300):
        """Core test execution logic"""
        cmd = ['python', 'test/run_test.py']
        
        if include:
            cmd.extend(['--include'] + include)
        if exclude:
            cmd.extend(exclude)
        
        cmd.extend(['--verbose', '--upload-artifacts-while-running'])
        
        start_time = time.time()
        result = subprocess.run(cmd, timeout=timeout)
        execution_time = time.time() - start_time
        
        return {
            'success': result.returncode == 0,
            'execution_time': execution_time,
            'exit_code': result.returncode
        }
```

## Next Steps for Migration

1. **Study the working parts**: Use the targeted test runner to understand core logic
2. **Map shell conditionals**: Create a mapping of all 157 conditional blocks
3. **Port test functions**: Convert each test_* function to Python
4. **Handle edge cases**: Address platform-specific and CI-specific logic
5. **Test incrementally**: Validate each migrated component

## Files Created for Your Migration
- `run_test_local.py` - Full script runner with analysis
- `run_specific_tests.py` - Targeted test execution
- `MIGRATION_GUIDE.md` - This comprehensive guide

You now have a solid foundation to understand the shell script behavior and begin the Python migration!
