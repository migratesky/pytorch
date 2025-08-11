#!/usr/bin/env python3
"""
CI-compatible Python test runner for PyTorch.

This script serves as a drop-in replacement for test.sh in CI environments.
It reads the same environment variables and provides the same interface,
but uses the modern Python-based test infrastructure.

Environment Variables:
    BUILD_ENVIRONMENT: Top-level label for what's being built/tested
    TEST_CONFIG: Specific test configuration to run
    SHARD_NUMBER: Current shard number (1-based)
    NUM_TEST_SHARDS: Total number of shards
    CONTINUE_THROUGH_ERROR: Whether to continue on test failures
    VERBOSE_TEST_LOGS: Enable verbose logging
    NO_TEST_TIMEOUT: Disable test timeouts
    PYTORCH_TEST_CUDA_MEM_LEAK_CHECK: Enable CUDA memory leak checking
    PYTORCH_TEST_RERUN_DISABLED_TESTS: Rerun disabled tests
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Add the .ci/pytorch directory to Python path for imports
ci_dir = Path(__file__).parent
sys.path.insert(0, str(ci_dir))
# Also add parent directory to help with imports
sys.path.insert(0, str(ci_dir.parent))

# Import required modules
import subprocess

def run_python_tests_via_registry(dry_run=False, verbose=False):
    """Run tests using the test registry system."""
    try:
        from test_config.environment import EnvironmentConfig
        from test_config.test_registry import TestRegistry
        
        # Create environment configuration
        env_config = EnvironmentConfig()
        
        # Create test registry and select appropriate test suite
        registry = TestRegistry()
        test_suite = registry.get_test_suite(env_config)
        
        if test_suite is None:
            logging.warning("No test suite selected from registry, using simple runner")
            return run_python_tests_via_simple_runner(dry_run, verbose)
        
        logging.info(f"Selected test suite: {test_suite.name}")
        
        # Run the selected test suite
        result = test_suite.run(env_config, dry_run=dry_run)
        if result:
            logging.info("Test registry execution completed successfully")
        return result
        
    except ImportError as e:
        logging.warning(f"Could not import test registry modules: {e}")
        logging.info("Falling back to simple test runner")
        return run_python_tests_via_simple_runner(dry_run, verbose)
    except Exception as e:
        logging.warning(f"Test registry execution failed: {e}")
        logging.info("Falling back to simple test runner")
        return run_python_tests_via_simple_runner(dry_run, verbose)

def run_python_tests_via_simple_runner(dry_run=False, verbose=False):
    """Run tests by delegating to simple_test_runner.py as fallback."""
    try:
        # Import and run the simple test runner
        from simple_test_runner import main as simple_main
        
        # Set up arguments for the simple runner
        import sys
        original_argv = sys.argv.copy()
        sys.argv = ['simple_test_runner.py']
        if dry_run:
            sys.argv.append('--dry-run')
        if verbose:
            sys.argv.append('--verbose')
        
        logging.info("Running tests via simple_test_runner.py")
        
        # Run the simple test runner
        result = simple_main()
        
        # Restore original argv
        sys.argv = original_argv
        
        if result == 0:
            logging.info("Simple test runner completed successfully")
            return True
        else:
            logging.error(f"Simple test runner failed with exit code: {result}")
            return False
    except Exception as e:
        logging.error(f"Simple test runner failed: {e}")
        import traceback
        logging.debug(traceback.format_exc())
        return False


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='PyTorch CI Python Test Runner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Environment Variables:
    BUILD_ENVIRONMENT       Build environment identifier
    TEST_CONFIG            Test configuration to run
    SHARD_NUMBER           Current shard number (1-based)
    NUM_TEST_SHARDS        Total number of shards
    USE_PYTHON_TEST_RUNNER Force Python test runner (disable shell fallback)
    NO_SHELL_FALLBACK      Disable shell script fallback
    CONTINUE_THROUGH_ERROR Continue on test failures
    VERBOSE_TEST_LOGS      Enable verbose logging
    NO_TEST_TIMEOUT        Disable test timeouts
        """
    )
    
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be run without executing')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('--fallback-on-error', action='store_true', default=False,
                       help='Fallback to shell script on Python runner errors')
    parser.add_argument('--no-fallback', dest='fallback_on_error', action='store_false',
                       help='Do not fallback to shell script on errors')
    parser.add_argument('--force-python', action='store_true',
                       help='Force Python test runner (same as USE_PYTHON_TEST_RUNNER=1)')
    
    return parser.parse_args()


def check_environment():
    """Check and validate the CI environment."""
    try:
        # Log environment variables directly since we delegate to simple_test_runner.py
        build_env = os.environ.get('BUILD_ENVIRONMENT', '')
        test_config = os.environ.get('TEST_CONFIG', '')
        shard_number = os.environ.get('SHARD_NUMBER', '1')
        num_shards = os.environ.get('NUM_TEST_SHARDS', '1')
        
        logging.info(f"Build Environment: {build_env}")
        logging.info(f"Test Config: {test_config}")
        logging.info(f"Shard: {shard_number}/{num_shards}")
        
        return {
            'build_environment': build_env,
            'test_config': test_config,
            'shard_number': int(shard_number),
            'num_test_shards': int(num_shards)
        }
    except Exception as e:
        logging.error(f"Failed to check environment: {e}")
        raise


def run_python_tests(dry_run: bool = False, verbose: bool = False) -> bool:
    """Run tests using the Python test infrastructure."""
    try:
        # Try the registry-based approach first
        return run_python_tests_via_registry(dry_run=dry_run, verbose=verbose)
    except Exception as e:
        logging.error(f"Failed to run Python tests: {e}")
        return False


def fallback_to_shell(args: list) -> int:
    """Fallback to the original shell-based test.sh script."""
    logging.info("Falling back to shell-based test.sh")
    
    shell_script = Path(__file__).parent / "test.sh"
    
    if not shell_script.exists():
        logging.error(f"Shell script not found: {shell_script}")
        return 1
    
    # Execute the shell script with the same arguments
    try:
        result = subprocess.run(["bash", str(shell_script)] + args, cwd=ci_dir)
        return result.returncode
    except Exception as e:
        logging.error(f"Failed to execute shell script: {e}")
        return 1


def main() -> int:
    """Main entry point for the CI test runner."""
    args = parse_args()
    
    # Setup logging based on environment and arguments
    verbose = args.verbose or os.environ.get('VERBOSE_TEST_LOGS', '').lower() in ('1', 'true')
    setup_logging(verbose)
    
    logging.info("PyTorch CI Python Test Runner")
    logging.info("=" * 50)
    
    # Force Python runner if USE_PYTHON_TEST_RUNNER is set
    force_python = os.environ.get('USE_PYTHON_TEST_RUNNER', '').lower() in ('1', 'true')
    
    # Check if we should skip shell fallback entirely
    no_shell_fallback = force_python or args.dry_run or os.environ.get('NO_SHELL_FALLBACK', '').lower() in ('1', 'true')
    
    if force_python:
        logging.info("USE_PYTHON_TEST_RUNNER=1: Forcing Python test runner")
    
    try:
        # Check environment configuration (for logging purposes)
        try:
            check_environment()
        except Exception as e:
            logging.info(f"Environment check had issues: {e}, continuing with Python runner")
        
        # Run Python-based tests
        success = run_python_tests(dry_run=args.dry_run, verbose=args.verbose)
        
        if success:
            logging.info("All tests completed successfully")
            return 0
        else:
            logging.error("Python test runner reported failure")
            
            # Only fallback to shell if explicitly allowed and not in dry-run
            if args.fallback_on_error and not no_shell_fallback:
                logging.info("Attempting fallback to shell script")
                return fallback_to_shell(sys.argv[1:])
            else:
                if no_shell_fallback:
                    logging.info("Shell fallback disabled, returning Python runner result")
                return 1
            
    except Exception as e:
        logging.error(f"Python test runner failed: {e}")
        import traceback
        logging.debug(traceback.format_exc())
        
        # Only fallback to shell if explicitly allowed and not in dry-run
        if args.fallback_on_error and not no_shell_fallback:
            logging.info("Attempting fallback to shell script due to error")
            return fallback_to_shell(sys.argv[1:])
        else:
            if no_shell_fallback:
                logging.info("Shell fallback disabled, returning error")
            return 1


if __name__ == "__main__":
    sys.exit(main())
