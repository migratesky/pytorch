#!/usr/bin/env python3
"""
Error Injection Testing Framework

This script validates that the Python test runner behaves identically to the shell script
when encountering various types of errors. It injects intentional errors and compares
the error detection and reporting between both test runners.
"""

import os
import sys
import subprocess
import tempfile
import shutil
import logging
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Types of errors to inject for testing."""
    IMPORT_ERROR = "import_error"
    SYNTAX_ERROR = "syntax_error"
    RUNTIME_ERROR = "runtime_error"
    MISSING_DEPENDENCY = "missing_dependency"
    ENVIRONMENT_ERROR = "environment_error"
    TEST_FAILURE = "test_failure"
    TIMEOUT_ERROR = "timeout_error"


@dataclass
class TestResult:
    """Result of running a test with error injection."""
    runner_type: str  # "shell" or "python"
    error_type: ErrorType
    exit_code: int
    stdout: str
    stderr: str
    execution_time: float
    error_detected: bool
    error_message: str


@dataclass
class ErrorInjectionTest:
    """Definition of an error injection test."""
    name: str
    error_type: ErrorType
    description: str
    injection_method: str
    expected_exit_code: int
    expected_error_pattern: str


class ErrorInjector:
    """Handles injection of various types of errors for testing."""
    
    def __init__(self, pytorch_root: str):
        self.pytorch_root = Path(pytorch_root)
        self.backup_dir = Path(tempfile.mkdtemp(prefix="pytorch_error_injection_"))
        self.injected_files = []
        logger.info(f"Error injection backup directory: {self.backup_dir}")
    
    def inject_import_error(self) -> str:
        """Inject an import error by temporarily breaking an import."""
        target_file = self.pytorch_root / "torch" / "__init__.py"
        if not target_file.exists():
            # Fallback to a test file
            target_file = self.pytorch_root / "test" / "test_torch.py"
            if not target_file.exists():
                return "Could not find suitable file for import error injection"
        
        # Backup original file
        backup_file = self.backup_dir / target_file.name
        shutil.copy2(target_file, backup_file)
        self.injected_files.append((target_file, backup_file))
        
        # Inject import error
        with open(target_file, 'r') as f:
            content = f.read()
        
        # Add a bad import at the top
        bad_import = "import nonexistent_module_that_does_not_exist\n"
        with open(target_file, 'w') as f:
            f.write(bad_import + content)
        
        return f"Injected import error in {target_file}"
    
    def inject_syntax_error(self) -> str:
        """Inject a syntax error by breaking Python syntax."""
        # Create a temporary test file with syntax error
        test_file = self.pytorch_root / "test" / "test_syntax_error_injection.py"
        
        syntax_error_content = '''
# Intentional syntax error for testing
def test_function():
    print("This will cause a syntax error"
    # Missing closing parenthesis above
    return True

if __name__ == "__main__":
    test_function()
'''
        
        with open(test_file, 'w') as f:
            f.write(syntax_error_content)
        
        self.injected_files.append((test_file, None))  # No backup needed for new file
        return f"Created file with syntax error: {test_file}"
    
    def inject_runtime_error(self) -> str:
        """Inject a runtime error that will fail during execution."""
        # Create a temporary test file with runtime error
        test_file = self.pytorch_root / "test" / "test_runtime_error_injection.py"
        
        runtime_error_content = '''
# Intentional runtime error for testing
def test_function():
    # This will cause a ZeroDivisionError
    result = 1 / 0
    return result

if __name__ == "__main__":
    test_function()
'''
        
        with open(test_file, 'w') as f:
            f.write(runtime_error_content)
        
        self.injected_files.append((test_file, None))
        return f"Created file with runtime error: {test_file}"
    
    def inject_missing_dependency(self) -> str:
        """Inject a missing dependency error."""
        # Create a test file that imports a non-existent package
        test_file = self.pytorch_root / "test" / "test_missing_dependency.py"
        
        missing_dep_content = '''
# Intentional missing dependency for testing
import super_rare_nonexistent_package_xyz123

def test_function():
    return super_rare_nonexistent_package_xyz123.some_function()

if __name__ == "__main__":
    test_function()
'''
        
        with open(test_file, 'w') as f:
            f.write(missing_dep_content)
        
        self.injected_files.append((test_file, None))
        return f"Created file with missing dependency: {test_file}"
    
    def inject_environment_error(self) -> str:
        """Inject an environment variable dependency error."""
        # Create a test that requires a missing environment variable
        test_file = self.pytorch_root / "test" / "test_env_error_injection.py"
        
        env_error_content = '''
# Intentional environment error for testing
import os

def test_function():
    required_var = os.environ["REQUIRED_NONEXISTENT_VAR_XYZ123"]
    print(f"Required variable: {required_var}")
    return True

if __name__ == "__main__":
    test_function()
'''
        
        with open(test_file, 'w') as f:
            f.write(env_error_content)
        
        self.injected_files.append((test_file, None))
        return f"Created file with environment error: {test_file}"
    
    def inject_test_failure(self) -> str:
        """Inject a test that will fail assertion."""
        test_file = self.pytorch_root / "test" / "test_assertion_failure.py"
        
        test_failure_content = '''
# Intentional test failure for testing
import unittest

class TestFailure(unittest.TestCase):
    def test_intentional_failure(self):
        """This test is designed to fail."""
        self.assertTrue(False, "Intentional test failure for error injection testing")
    
    def test_assertion_error(self):
        """This test will also fail."""
        assert 1 == 2, "Intentional assertion failure"

if __name__ == "__main__":
    unittest.main()
'''
        
        with open(test_file, 'w') as f:
            f.write(test_failure_content)
        
        self.injected_files.append((test_file, None))
        return f"Created file with test failure: {test_file}"
    
    def cleanup(self):
        """Restore all modified files and clean up."""
        logger.info("Cleaning up error injections...")
        
        for target_file, backup_file in self.injected_files:
            try:
                if backup_file and backup_file.exists():
                    # Restore from backup
                    shutil.copy2(backup_file, target_file)
                    logger.info(f"Restored {target_file}")
                elif target_file.exists() and backup_file is None:
                    # Remove created file
                    target_file.unlink()
                    logger.info(f"Removed {target_file}")
            except Exception as e:
                logger.error(f"Failed to cleanup {target_file}: {e}")
        
        # Remove backup directory
        try:
            shutil.rmtree(self.backup_dir)
            logger.info(f"Removed backup directory: {self.backup_dir}")
        except Exception as e:
            logger.error(f"Failed to remove backup directory: {e}")


class ErrorInjectionTester:
    """Main class for running error injection tests."""
    
    def __init__(self, pytorch_root: str):
        self.pytorch_root = Path(pytorch_root)
        self.injector = ErrorInjector(pytorch_root)
        self.test_results: List[TestResult] = []
        
        # Define test cases
        self.test_cases = [
            ErrorInjectionTest(
                name="Import Error Test",
                error_type=ErrorType.IMPORT_ERROR,
                description="Test detection of import errors",
                injection_method="inject_import_error",
                expected_exit_code=1,
                expected_error_pattern="ImportError|ModuleNotFoundError"
            ),
            ErrorInjectionTest(
                name="Syntax Error Test", 
                error_type=ErrorType.SYNTAX_ERROR,
                description="Test detection of Python syntax errors",
                injection_method="inject_syntax_error",
                expected_exit_code=1,
                expected_error_pattern="SyntaxError"
            ),
            ErrorInjectionTest(
                name="Runtime Error Test",
                error_type=ErrorType.RUNTIME_ERROR,
                description="Test detection of runtime errors",
                injection_method="inject_runtime_error",
                expected_exit_code=1,
                expected_error_pattern="ZeroDivisionError"
            ),
            ErrorInjectionTest(
                name="Missing Dependency Test",
                error_type=ErrorType.MISSING_DEPENDENCY,
                description="Test detection of missing dependencies",
                injection_method="inject_missing_dependency",
                expected_exit_code=1,
                expected_error_pattern="ModuleNotFoundError"
            ),
            ErrorInjectionTest(
                name="Environment Error Test",
                error_type=ErrorType.ENVIRONMENT_ERROR,
                description="Test detection of missing environment variables",
                injection_method="inject_environment_error",
                expected_exit_code=1,
                expected_error_pattern="KeyError"
            ),
            ErrorInjectionTest(
                name="Test Failure Test",
                error_type=ErrorType.TEST_FAILURE,
                description="Test detection of test assertion failures",
                injection_method="inject_test_failure",
                expected_exit_code=1,
                expected_error_pattern="AssertionError|FAILED"
            )
        ]
    
    def run_shell_test(self, test_config: str = "smoke") -> TestResult:
        """Run the shell script test runner."""
        logger.info(f"Running shell script test with config: {test_config}")
        
        env = os.environ.copy()
        env.update({
            'BUILD_ENVIRONMENT': 'linux-focal-py3.8-gcc7',
            'TEST_CONFIG': test_config,
            'USE_PYTHON_TEST_RUNNER': '0'  # Force shell script
        })
        
        start_time = time.time()
        try:
            result = subprocess.run(
                [str(self.pytorch_root / '.ci' / 'pytorch' / 'test.sh')],
                cwd=self.pytorch_root,
                env=env,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            execution_time = time.time() - start_time
            
            return TestResult(
                runner_type="shell",
                error_type=ErrorType.TEST_FAILURE,  # Will be updated by caller
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                execution_time=execution_time,
                error_detected=result.returncode != 0,
                error_message=result.stderr if result.returncode != 0 else ""
            )
        
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return TestResult(
                runner_type="shell",
                error_type=ErrorType.TIMEOUT_ERROR,
                exit_code=124,  # Timeout exit code
                stdout="",
                stderr="Test timed out after 300 seconds",
                execution_time=execution_time,
                error_detected=True,
                error_message="Timeout error"
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return TestResult(
                runner_type="shell",
                error_type=ErrorType.RUNTIME_ERROR,
                exit_code=1,
                stdout="",
                stderr=str(e),
                execution_time=execution_time,
                error_detected=True,
                error_message=str(e)
            )
    
    def run_python_test(self, test_config: str = "smoke") -> TestResult:
        """Run the Python test runner."""
        logger.info(f"Running Python test runner with config: {test_config}")
        
        env = os.environ.copy()
        env.update({
            'BUILD_ENVIRONMENT': 'linux-focal-py3.8-gcc7',
            'TEST_CONFIG': test_config,
            'USE_PYTHON_TEST_RUNNER': '1'  # Force Python runner
        })
        
        start_time = time.time()
        try:
            result = subprocess.run(
                ['python3', str(self.pytorch_root / '.ci' / 'pytorch' / 'test_python_ci.py')],
                cwd=self.pytorch_root,
                env=env,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            execution_time = time.time() - start_time
            
            return TestResult(
                runner_type="python",
                error_type=ErrorType.TEST_FAILURE,  # Will be updated by caller
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                execution_time=execution_time,
                error_detected=result.returncode != 0,
                error_message=result.stderr if result.returncode != 0 else ""
            )
        
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return TestResult(
                runner_type="python",
                error_type=ErrorType.TIMEOUT_ERROR,
                exit_code=124,  # Timeout exit code
                stdout="",
                stderr="Test timed out after 300 seconds",
                execution_time=execution_time,
                error_detected=True,
                error_message="Timeout error"
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return TestResult(
                runner_type="python",
                error_type=ErrorType.RUNTIME_ERROR,
                exit_code=1,
                stdout="",
                stderr=str(e),
                execution_time=execution_time,
                error_detected=True,
                error_message=str(e)
            )
    
    def run_error_injection_test(self, test_case: ErrorInjectionTest) -> Tuple[TestResult, TestResult]:
        """Run a single error injection test comparing shell vs Python."""
        logger.info(f"Running error injection test: {test_case.name}")
        
        try:
            # Inject the error
            injection_method = getattr(self.injector, test_case.injection_method)
            injection_result = injection_method()
            logger.info(f"Error injection: {injection_result}")
            
            # Run shell script test
            shell_result = self.run_shell_test("smoke")
            shell_result.error_type = test_case.error_type
            
            # Run Python test
            python_result = self.run_python_test("smoke")
            python_result.error_type = test_case.error_type
            
            return shell_result, python_result
            
        except Exception as e:
            logger.error(f"Failed to run error injection test {test_case.name}: {e}")
            # Return error results
            error_result = TestResult(
                runner_type="error",
                error_type=test_case.error_type,
                exit_code=1,
                stdout="",
                stderr=str(e),
                execution_time=0.0,
                error_detected=True,
                error_message=str(e)
            )
            return error_result, error_result
    
    def run_all_tests(self) -> Dict[str, List[TestResult]]:
        """Run all error injection tests."""
        logger.info("Starting comprehensive error injection testing...")
        
        results = {}
        
        try:
            for test_case in self.test_cases:
                logger.info(f"\n{'='*60}")
                logger.info(f"Running test: {test_case.name}")
                logger.info(f"Description: {test_case.description}")
                logger.info(f"{'='*60}")
                
                shell_result, python_result = self.run_error_injection_test(test_case)
                
                results[test_case.name] = [shell_result, python_result]
                self.test_results.extend([shell_result, python_result])
                
                # Clean up after each test
                self.injector.cleanup()
                
                # Brief pause between tests
                time.sleep(1)
        
        finally:
            # Final cleanup
            self.injector.cleanup()
        
        return results
    
    def compare_results(self, shell_result: TestResult, python_result: TestResult) -> Dict:
        """Compare results between shell and Python runners."""
        return {
            'exit_code_match': shell_result.exit_code == python_result.exit_code,
            'both_detected_error': shell_result.error_detected and python_result.error_detected,
            'execution_time_ratio': python_result.execution_time / shell_result.execution_time if shell_result.execution_time > 0 else 0,
            'shell_exit_code': shell_result.exit_code,
            'python_exit_code': python_result.exit_code,
            'shell_error_message': shell_result.error_message[:200] + "..." if len(shell_result.error_message) > 200 else shell_result.error_message,
            'python_error_message': python_result.error_message[:200] + "..." if len(python_result.error_message) > 200 else python_result.error_message
        }
    
    def print_summary(self, results: Dict[str, List[TestResult]]):
        """Print a comprehensive summary of test results."""
        logger.info("\n" + "="*80)
        logger.info("ERROR INJECTION TESTING SUMMARY")
        logger.info("="*80)
        
        total_tests = len(results)
        matching_results = 0
        both_detected_errors = 0
        
        for test_name, test_results in results.items():
            if len(test_results) >= 2:
                shell_result = test_results[0]
                python_result = test_results[1]
                comparison = self.compare_results(shell_result, python_result)
                
                logger.info(f"\nTest: {test_name}")
                logger.info(f"  Shell Exit Code: {comparison['shell_exit_code']}")
                logger.info(f"  Python Exit Code: {comparison['python_exit_code']}")
                logger.info(f"  Exit Codes Match: {'✅' if comparison['exit_code_match'] else '❌'}")
                logger.info(f"  Both Detected Error: {'✅' if comparison['both_detected_error'] else '❌'}")
                
                if comparison['execution_time_ratio'] > 0:
                    logger.info(f"  Execution Time Ratio (Python/Shell): {comparison['execution_time_ratio']:.2f}")
                
                if comparison['shell_error_message']:
                    logger.info(f"  Shell Error: {comparison['shell_error_message']}")
                if comparison['python_error_message']:
                    logger.info(f"  Python Error: {comparison['python_error_message']}")
                
                if comparison['exit_code_match']:
                    matching_results += 1
                if comparison['both_detected_error']:
                    both_detected_errors += 1
        
        logger.info(f"\n{'='*80}")
        logger.info(f"OVERALL RESULTS:")
        logger.info(f"  Total Tests: {total_tests}")
        logger.info(f"  Matching Exit Codes: {matching_results}/{total_tests} ({matching_results/total_tests*100:.1f}%)")
        logger.info(f"  Both Detected Errors: {both_detected_errors}/{total_tests} ({both_detected_errors/total_tests*100:.1f}%)")
        
        if matching_results == total_tests and both_detected_errors == total_tests:
            logger.info(f"  🎉 SUCCESS: Python runner shows identical error detection to shell script!")
        else:
            logger.info(f"  ⚠️  ATTENTION: Some discrepancies found between runners")
        
        logger.info("="*80)


def main():
    """Main entry point for error injection testing."""
    if len(sys.argv) > 1:
        pytorch_root = sys.argv[1]
    else:
        pytorch_root = os.getcwd()
    
    if not Path(pytorch_root).exists():
        logger.error(f"PyTorch root directory does not exist: {pytorch_root}")
        sys.exit(1)
    
    logger.info(f"Starting error injection testing in: {pytorch_root}")
    
    tester = ErrorInjectionTester(pytorch_root)
    
    try:
        results = tester.run_all_tests()
        tester.print_summary(results)
    except KeyboardInterrupt:
        logger.info("\nTesting interrupted by user")
        tester.injector.cleanup()
    except Exception as e:
        logger.error(f"Testing failed with error: {e}")
        tester.injector.cleanup()
        sys.exit(1)


if __name__ == "__main__":
    main()
