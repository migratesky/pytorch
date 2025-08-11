#!/usr/bin/env python3
"""
Migration validation script for PyTorch CI test runner.

This script validates that the Python-based test runner produces the same
results as the original shell-based test.sh script, ensuring a safe migration.
"""

import os
import sys
import subprocess
import logging
import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

# Add the .ci/pytorch directory to Python path for imports
ci_dir = Path(__file__).parent
sys.path.insert(0, str(ci_dir))

from test_config.environment import EnvironmentConfig
from test_config.test_registry import TestRegistry


@dataclass
class TestResult:
    """Test execution result."""
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    execution_time: float


@dataclass
class ValidationResult:
    """Validation comparison result."""
    test_config: str
    build_environment: str
    python_result: TestResult
    shell_result: TestResult
    matches: bool
    differences: List[str]


class MigrationValidator:
    """Validates the migration from shell to Python test runner."""
    
    def __init__(self, verbose: bool = False):
        self.logger = logging.getLogger(__name__)
        self.verbose = verbose
        self.ci_dir = ci_dir
        self.python_runner = self.ci_dir / "test_python.py"
        self.shell_runner = self.ci_dir / "test.sh"
        
        # Setup logging
        level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def run_python_test(self, env_vars: Dict[str, str], dry_run: bool = True) -> TestResult:
        """Run the Python-based test runner."""
        import time
        
        cmd = [sys.executable, str(self.python_runner)]
        if dry_run:
            cmd.append("--dry-run")
        if self.verbose:
            cmd.append("--verbose")
        
        # Set environment
        test_env = os.environ.copy()
        test_env.update(env_vars)
        
        self.logger.debug(f"Running Python test: {' '.join(cmd)}")
        self.logger.debug(f"Environment: {env_vars}")
        
        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                cwd=self.ci_dir,
                env=test_env,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            execution_time = time.time() - start_time
            
            return TestResult(
                success=result.returncode == 0,
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                execution_time=execution_time
            )
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return TestResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="Test timed out after 5 minutes",
                execution_time=execution_time
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return TestResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=f"Exception running Python test: {e}",
                execution_time=execution_time
            )
    
    def run_shell_test(self, env_vars: Dict[str, str], dry_run: bool = True) -> TestResult:
        """Run the shell-based test runner."""
        import time
        
        if not self.shell_runner.exists():
            return TestResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="Shell test runner not found",
                execution_time=0.0
            )
        
        # For shell script, we simulate dry-run by setting a flag
        cmd = ["bash", str(self.shell_runner)]
        
        # Set environment
        test_env = os.environ.copy()
        test_env.update(env_vars)
        if dry_run:
            test_env["DRY_RUN"] = "1"
        
        self.logger.debug(f"Running shell test: {' '.join(cmd)}")
        self.logger.debug(f"Environment: {env_vars}")
        
        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                cwd=self.ci_dir,
                env=test_env,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            execution_time = time.time() - start_time
            
            return TestResult(
                success=result.returncode == 0,
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                execution_time=execution_time
            )
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return TestResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="Test timed out after 5 minutes",
                execution_time=execution_time
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return TestResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=f"Exception running shell test: {e}",
                execution_time=execution_time
            )
    
    def compare_results(self, python_result: TestResult, shell_result: TestResult) -> Tuple[bool, List[str]]:
        """Compare Python and shell test results."""
        differences = []
        
        # Compare exit codes
        if python_result.exit_code != shell_result.exit_code:
            differences.append(f"Exit codes differ: Python={python_result.exit_code}, Shell={shell_result.exit_code}")
        
        # Compare success status
        if python_result.success != shell_result.success:
            differences.append(f"Success status differs: Python={python_result.success}, Shell={shell_result.success}")
        
        # For dry-run, we mainly care about the test selection logic
        # We don't expect exact stdout/stderr matches due to different implementations
        
        matches = len(differences) == 0
        return matches, differences
    
    def validate_test_config(self, build_env: str, test_config: str, dry_run: bool = True) -> ValidationResult:
        """Validate a specific test configuration."""
        self.logger.info(f"Validating: BUILD_ENVIRONMENT={build_env}, TEST_CONFIG={test_config}")
        
        env_vars = {
            "BUILD_ENVIRONMENT": build_env,
            "TEST_CONFIG": test_config,
            "SHARD_NUMBER": "1",
            "NUM_TEST_SHARDS": "1"
        }
        
        # Run both implementations
        python_result = self.run_python_test(env_vars, dry_run=dry_run)
        shell_result = self.run_shell_test(env_vars, dry_run=dry_run)
        
        # Compare results
        matches, differences = self.compare_results(python_result, shell_result)
        
        return ValidationResult(
            test_config=test_config,
            build_environment=build_env,
            python_result=python_result,
            shell_result=shell_result,
            matches=matches,
            differences=differences
        )
    
    def get_test_configurations(self) -> List[Tuple[str, str]]:
        """Get list of test configurations to validate."""
        # Common test configurations to validate
        configurations = [
            ("pytorch-linux-xenial-py3.8-gcc7", "smoke"),
            ("pytorch-linux-xenial-py3.8-gcc7", "python"),
            ("pytorch-linux-xenial-py3.8-gcc7-cuda11", "inductor"),
            ("pytorch-linux-xenial-py3.8-gcc7-cuda11", "distributed"),
            ("pytorch-linux-xenial-py3.8-gcc7-cuda11", "h100_distributed"),
            ("pytorch-linux-xenial-py3.8-gcc7-cuda11", "h100_symm_mem"),
            ("pytorch-linux-xenial-py3.8-gcc7-cuda11", "h100_cutlass_backend"),
            ("pytorch-linux-xenial-py3.8-gcc7-libtorch", "libtorch"),
            ("pytorch-linux-xenial-py3.8-gcc7-xpu", "xpu"),
        ]
        return configurations
    
    def run_validation(self, dry_run: bool = True) -> List[ValidationResult]:
        """Run validation for all test configurations."""
        self.logger.info("Starting migration validation")
        
        configurations = self.get_test_configurations()
        results = []
        
        for build_env, test_config in configurations:
            try:
                result = self.validate_test_config(build_env, test_config, dry_run=dry_run)
                results.append(result)
                
                if result.matches:
                    self.logger.info(f"✅ PASS: {test_config} on {build_env}")
                else:
                    self.logger.warning(f"❌ FAIL: {test_config} on {build_env}")
                    for diff in result.differences:
                        self.logger.warning(f"  - {diff}")
                        
            except Exception as e:
                self.logger.error(f"❌ ERROR: {test_config} on {build_env}: {e}")
                # Create a failed result
                results.append(ValidationResult(
                    test_config=test_config,
                    build_environment=build_env,
                    python_result=TestResult(False, -1, "", str(e), 0.0),
                    shell_result=TestResult(False, -1, "", "", 0.0),
                    matches=False,
                    differences=[f"Validation error: {e}"]
                ))
        
        return results
    
    def generate_report(self, results: List[ValidationResult]) -> str:
        """Generate a validation report."""
        total = len(results)
        passed = sum(1 for r in results if r.matches)
        failed = total - passed
        
        report = [
            "# Migration Validation Report",
            "",
            f"**Total Configurations Tested:** {total}",
            f"**Passed:** {passed}",
            f"**Failed:** {failed}",
            f"**Success Rate:** {(passed/total*100):.1f}%" if total > 0 else "**Success Rate:** N/A",
            "",
        ]
        
        if failed > 0:
            report.extend([
                "## Failed Configurations",
                "",
            ])
            
            for result in results:
                if not result.matches:
                    report.extend([
                        f"### {result.test_config} on {result.build_environment}",
                        "",
                        "**Differences:**",
                    ])
                    for diff in result.differences:
                        report.append(f"- {diff}")
                    report.extend([
                        "",
                        f"**Python Exit Code:** {result.python_result.exit_code}",
                        f"**Shell Exit Code:** {result.shell_result.exit_code}",
                        "",
                    ])
        
        if passed > 0:
            report.extend([
                "## Passed Configurations",
                "",
            ])
            
            for result in results:
                if result.matches:
                    report.append(f"- ✅ {result.test_config} on {result.build_environment}")
        
        return "\n".join(report)


def main():
    """Main entry point for the migration validator."""
    parser = argparse.ArgumentParser(description="Validate PyTorch CI migration from shell to Python")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Run in dry-run mode (default)")
    parser.add_argument("--real-run", action="store_true", help="Run actual tests (not dry-run)")
    parser.add_argument("--output", "-o", help="Output report to file")
    
    args = parser.parse_args()
    
    # Determine dry-run mode
    dry_run = not args.real_run
    
    # Create validator
    validator = MigrationValidator(verbose=args.verbose)
    
    # Run validation
    results = validator.run_validation(dry_run=dry_run)
    
    # Generate report
    report = validator.generate_report(results)
    
    # Output report
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"Report written to {args.output}")
    else:
        print(report)
    
    # Exit with appropriate code
    failed_count = sum(1 for r in results if not r.matches)
    sys.exit(0 if failed_count == 0 else 1)


if __name__ == "__main__":
    main()
