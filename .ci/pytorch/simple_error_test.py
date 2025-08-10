#!/usr/bin/env python3
"""
Simple Error Injection Test

This script creates a simple test to validate that both the shell script and Python test runner
detect and handle errors identically by injecting an intentional error.
"""

import os
import sys
import subprocess
import tempfile
import time
from pathlib import Path

def create_failing_test():
    """Create a simple Python test file that will fail."""
    test_content = '''#!/usr/bin/env python3
"""
Intentional failing test for error injection validation.
"""
import sys

def test_intentional_failure():
    """This test is designed to fail."""
    print("Running intentional failure test...")
    print("This test will fail with exit code 1")
    sys.exit(1)

if __name__ == "__main__":
    test_intentional_failure()
'''
    
    # Create the failing test in the test directory
    test_file = Path("/Users/krishna.pinnaka/pytorch/test/test_intentional_failure.py")
    with open(test_file, 'w') as f:
        f.write(test_content)
    
    # Make it executable
    os.chmod(test_file, 0o755)
    
    return test_file

def run_shell_test():
    """Run the shell script test runner."""
    print("🔧 Running shell script test runner...")
    
    env = os.environ.copy()
    env.update({
        'BUILD_ENVIRONMENT': 'linux-focal-py3.8-gcc7',
        'TEST_CONFIG': 'smoke',
        'USE_PYTHON_TEST_RUNNER': '0'  # Force shell script
    })
    
    start_time = time.time()
    try:
        result = subprocess.run(
            ['bash', '.ci/pytorch/test.sh'],
            cwd='/Users/krishna.pinnaka/pytorch',
            env=env,
            capture_output=True,
            text=True,
            timeout=60  # 1 minute timeout for quick test
        )
        execution_time = time.time() - start_time
        
        print(f"Shell script completed in {execution_time:.2f}s")
        print(f"Exit code: {result.returncode}")
        if result.stdout:
            print(f"STDOUT (first 500 chars): {result.stdout[:500]}...")
        if result.stderr:
            print(f"STDERR (first 500 chars): {result.stderr[:500]}...")
        
        return {
            'exit_code': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'execution_time': execution_time
        }
    
    except subprocess.TimeoutExpired:
        print("❌ Shell script timed out")
        return {
            'exit_code': 124,
            'stdout': '',
            'stderr': 'Timeout after 60 seconds',
            'execution_time': 60.0
        }
    except Exception as e:
        print(f"❌ Shell script failed with exception: {e}")
        return {
            'exit_code': 1,
            'stdout': '',
            'stderr': str(e),
            'execution_time': 0.0
        }

def run_python_test():
    """Run the Python test runner."""
    print("🐍 Running Python test runner...")
    
    env = os.environ.copy()
    env.update({
        'BUILD_ENVIRONMENT': 'linux-focal-py3.8-gcc7',
        'TEST_CONFIG': 'smoke',
        'USE_PYTHON_TEST_RUNNER': '1'  # Force Python runner
    })
    
    start_time = time.time()
    try:
        result = subprocess.run(
            ['python3', '.ci/pytorch/test_python_ci.py'],
            cwd='/Users/krishna.pinnaka/pytorch',
            env=env,
            capture_output=True,
            text=True,
            timeout=60  # 1 minute timeout for quick test
        )
        execution_time = time.time() - start_time
        
        print(f"Python runner completed in {execution_time:.2f}s")
        print(f"Exit code: {result.returncode}")
        if result.stdout:
            print(f"STDOUT (first 500 chars): {result.stdout[:500]}...")
        if result.stderr:
            print(f"STDERR (first 500 chars): {result.stderr[:500]}...")
        
        return {
            'exit_code': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'execution_time': execution_time
        }
    
    except subprocess.TimeoutExpired:
        print("❌ Python runner timed out")
        return {
            'exit_code': 124,
            'stdout': '',
            'stderr': 'Timeout after 60 seconds',
            'execution_time': 60.0
        }
    except Exception as e:
        print(f"❌ Python runner failed with exception: {e}")
        return {
            'exit_code': 1,
            'stdout': '',
            'stderr': str(e),
            'execution_time': 0.0
        }

def compare_results(shell_result, python_result):
    """Compare the results from both test runners."""
    print("\n" + "="*60)
    print("COMPARISON RESULTS")
    print("="*60)
    
    print(f"Shell Exit Code:  {shell_result['exit_code']}")
    print(f"Python Exit Code: {python_result['exit_code']}")
    print(f"Exit Codes Match: {'✅ YES' if shell_result['exit_code'] == python_result['exit_code'] else '❌ NO'}")
    
    print(f"\nShell Execution Time:  {shell_result['execution_time']:.2f}s")
    print(f"Python Execution Time: {python_result['execution_time']:.2f}s")
    
    if python_result['execution_time'] > 0 and shell_result['execution_time'] > 0:
        ratio = python_result['execution_time'] / shell_result['execution_time']
        print(f"Time Ratio (Python/Shell): {ratio:.2f}")
    
    # Check if both detected errors (non-zero exit codes)
    shell_error = shell_result['exit_code'] != 0
    python_error = python_result['exit_code'] != 0
    
    print(f"\nShell Detected Error:  {'✅ YES' if shell_error else '❌ NO'}")
    print(f"Python Detected Error: {'✅ YES' if python_error else '❌ NO'}")
    print(f"Both Detected Error:   {'✅ YES' if shell_error and python_error else '❌ NO'}")
    
    # Overall assessment
    print(f"\n{'='*60}")
    if shell_result['exit_code'] == python_result['exit_code'] and shell_error and python_error:
        print("🎉 SUCCESS: Both runners detected the error identically!")
    elif shell_result['exit_code'] == python_result['exit_code']:
        print("✅ GOOD: Exit codes match")
    else:
        print("⚠️  ATTENTION: Exit codes differ - investigate further")
    print("="*60)

def main():
    """Main test execution."""
    print("🧪 Simple Error Injection Test")
    print("Testing error handling parity between shell script and Python test runner")
    print("="*80)
    
    # First, let's test without any error injection to establish baseline
    print("\n📋 BASELINE TEST (No Error Injection)")
    print("-" * 50)
    
    print("Running baseline shell test...")
    shell_baseline = run_shell_test()
    
    print("\nRunning baseline Python test...")
    python_baseline = run_python_test()
    
    print("\n📊 Baseline Comparison:")
    compare_results(shell_baseline, python_baseline)
    
    # Now let's create a failing test and see how both runners handle it
    print(f"\n🔥 ERROR INJECTION TEST")
    print("-" * 50)
    
    try:
        # Create a failing test
        failing_test = create_failing_test()
        print(f"Created failing test: {failing_test}")
        
        print("\nRunning shell test with failing test...")
        shell_error = run_shell_test()
        
        print("\nRunning Python test with failing test...")
        python_error = run_python_test()
        
        print("\n📊 Error Injection Comparison:")
        compare_results(shell_error, python_error)
        
    finally:
        # Clean up the failing test
        try:
            failing_test.unlink()
            print(f"\nCleaned up: {failing_test}")
        except:
            pass
    
    print("\n✅ Error injection testing complete!")

if __name__ == "__main__":
    main()
