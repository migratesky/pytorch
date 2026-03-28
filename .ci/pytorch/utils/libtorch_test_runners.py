"""
LibTorch PyTorch test runners.

This module contains Python implementations for LibTorch-related PyTorch test functions,
replacing shell-based implementations with native Python logic.
"""

import os
import logging
import subprocess
from typing import List, Optional

from .test_execution import PyTorchTestRunner
from .shell_utils import run_command_with_output


class LibTorchTestRunner(PyTorchTestRunner):
    """Runner for LibTorch tests."""
    
    def run_libtorch_tests(self) -> bool:
        """
        Run LibTorch tests.
        
        This replaces the test_libtorch shell function.
        """
        self.logger.info("Running LibTorch tests")
        
        # Get extra options from environment
        extra_options = os.environ.get("PYTHON_TEST_EXTRA_OPTION", "")
        
        # LibTorch test files
        test_files = [
            "cpp/test_cpp_api.py"
        ]
        
        # Run LibTorch tests
        success = self.run_test_suite(
            test_files=test_files,
            extra_options=extra_options,
            upload_artifacts=True
        )
        
        # Check git status
        if success:
            success = self.assert_git_not_dirty()
            
        return success
    
    def run_libtorch_jit_tests(self) -> bool:
        """
        Run LibTorch JIT tests.
        
        This replaces the test_libtorch_jit shell function.
        Runs C++ JIT and lazy tensor tests with proper setup/teardown.
        """
        self.logger.info("Running LibTorch JIT tests")
        
        try:
            # Step 1: Setup - Prepare the model used by test_jit
            self.logger.info("Setting up JIT test models")
            setup_cmd = "python cpp/jit/tests_setup.py setup"
            success = run_command_with_output(setup_cmd, cwd="test")[0]
            if not success:
                self.logger.error("Failed to setup JIT test models")
                return False
            
            # Step 2: Run C++ JIT and lazy tensor tests
            self.logger.info("Running C++ JIT and lazy tensor tests")
            test_cmd = "python test/run_test.py --cpp --verbose -i cpp/test_jit cpp/test_lazy"
            
            # Add CUDA-specific configuration
            if hasattr(self, 'build_env') and self.build_env and "cuda" in self.build_env.lower() and getattr(self, 'test_config', '') != "nogpu":
                # Enable CUDA for lazy tensor tests
                env_vars = {"LTC_TS_CUDA": "1"}
                success = run_command_with_output(test_cmd, env=env_vars)[0]
            else:
                # Skip CUDA tests when CUDA is not available
                test_cmd += ' -k "not CUDA"'
                success = run_command_with_output(test_cmd)[0]
            
            if not success:
                self.logger.error("LibTorch JIT tests failed")
                return False
                
        finally:
            # Step 3: Cleanup - Always run teardown even if tests failed
            self.logger.info("Cleaning up JIT test artifacts")
            cleanup_cmd = "python cpp/jit/tests_setup.py shutdown"
            cleanup_success = run_command_with_output(cleanup_cmd, cwd="test")[0]
            if not cleanup_success:
                self.logger.warning("Failed to cleanup JIT test artifacts")
        
        # Check git status
        if success:
            success = self.assert_git_not_dirty()
            
        return success
    
    def run_libtorch_api_tests(self) -> bool:
        """
        Run LibTorch API tests.
        
        This replaces the test_libtorch_api shell function.
        """
        self.logger.info("Running LibTorch API tests")
        
        # Get extra options from environment
        extra_options = os.environ.get("PYTHON_TEST_EXTRA_OPTION", "")
        
        # LibTorch API test files
        test_files = [
            "cpp/api/test_api.py"
        ]
        
        # Run LibTorch API tests
        success = self.run_test_suite(
            test_files=test_files,
            extra_options=extra_options,
            upload_artifacts=True
        )
        
        # Check git status
        if success:
            success = self.assert_git_not_dirty()
            
        return success


class AOTCompilationTestRunner(PyTorchTestRunner):
    """Runner for AOT compilation tests."""
    
    def run_aot_compilation_tests(self) -> bool:
        """
        Run AOT compilation tests.
        
        This replaces the test_aot_compilation shell function.
        """
        self.logger.info("Running AOT compilation tests")
        
        # Get extra options from environment
        extra_options = os.environ.get("PYTHON_TEST_EXTRA_OPTION", "")
        
        # AOT compilation test files
        test_files = [
            "test_aot_autograd.py"
        ]
        
        # Run AOT compilation tests
        success = self.run_test_suite(
            test_files=test_files,
            extra_options=extra_options,
            upload_artifacts=True
        )
        
        # Check git status
        if success:
            success = self.assert_git_not_dirty()
            
        return success


class VulkanTestRunner(PyTorchTestRunner):
    """Runner for Vulkan tests."""
    
    def run_vulkan_tests(self) -> bool:
        """
        Run Vulkan tests.
        
        This replaces the test_vulkan shell function.
        """
        self.logger.info("Running Vulkan tests")
        
        # Get extra options from environment
        extra_options = os.environ.get("PYTHON_TEST_EXTRA_OPTION", "")
        
        # Vulkan test files
        test_files = [
            "test_vulkan.py"
        ]
        
        # Run Vulkan tests
        success = self.run_test_suite(
            test_files=test_files,
            extra_options=extra_options,
            upload_artifacts=True
        )
        
        # Check git status
        if success:
            success = self.assert_git_not_dirty()
            
        return success


class JitHooksTestRunner(PyTorchTestRunner):
    """Runner for JIT hooks tests."""
    
    def run_jit_hooks_tests(self) -> bool:
        """
        Run JIT hooks tests.
        
        This replaces the test_jit_hooks shell function.
        """
        self.logger.info("Running JIT hooks tests")
        
        # Get extra options from environment
        extra_options = os.environ.get("PYTHON_TEST_EXTRA_OPTION", "")
        
        # JIT hooks test files
        test_files = [
            "test_jit_hooks.py"
        ]
        
        # Run JIT hooks tests
        success = self.run_test_suite(
            test_files=test_files,
            extra_options=extra_options,
            upload_artifacts=True
        )
        
        # Check git status
        if success:
            success = self.assert_git_not_dirty()
            
        return success


class CppExtensionsTestRunner(PyTorchTestRunner):
    """Runner for C++ extensions tests."""
    
    def run_cpp_extensions_tests(self) -> bool:
        """
        Run C++ extensions tests.
        
        This replaces the test_cpp_extensions shell function.
        """
        self.logger.info("Running C++ extensions tests")
        
        # Get extra options from environment
        extra_options = os.environ.get("PYTHON_TEST_EXTRA_OPTION", "")
        
        # C++ extensions test files
        test_files = [
            "test_cpp_extensions_aot_no_ninja.py",
            "test_cpp_extensions_aot_ninja.py",
            "test_cpp_extensions_jit.py"
        ]
        
        # Run C++ extensions tests
        success = self.run_test_suite(
            test_files=test_files,
            extra_options=extra_options,
            upload_artifacts=True
        )
        
        # Check git status
        if success:
            success = self.assert_git_not_dirty()
            
        return success
