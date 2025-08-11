"""
Test registry for managing and selecting test suites.

This module provides the central registry that determines which test suite
to run based on the environment configuration.
"""

import logging
from typing import List, Optional

from .base import TestSuite, ConditionalTestSuite, DefaultTestSuite
from .environment import EnvironmentConfig

# Import test suite implementations with simplified fallback
try:
    # Try relative imports first (more likely to work in this structure)
    from ..test_suites import basic_test_suites
except ImportError:
    try:
        # Fallback to direct import
        from test_suites import basic_test_suites
    except ImportError:
        # If modules don't exist yet, we'll create basic suites inline
        basic_test_suites = None


class TestRegistry:
    """Registry for managing test suites and selecting the appropriate one."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.test_suites: List[TestSuite] = []
        self.default_suite = DefaultTestSuite()
        self._register_test_suites()
    
    def _register_test_suites(self) -> None:
        """Register all available test suites."""
        
        # If we have the basic_test_suites module, use it
        if basic_test_suites is not None:
            # Use imported test suites when available
            self.test_suites.extend(basic_test_suites.get_all_test_suites())
            return
        
        # Otherwise, create essential test suites inline
        # This is the fallback when modules aren't implemented yet
        self._register_essential_test_suites()
    
    def _register_essential_test_suites(self) -> None:
        """Register essential test suites when modules are not available."""
        
        # Core test suites that are most commonly used
        essential_suites = [
            # Python tests
            {
                "name": "python",
                "description": "Python tests",
                "test_config_patterns": ["python"],
                "functions": ["test_python", "test_aten", "test_vec256"]
            },
            # Smoke tests
            {
                "name": "smoke", 
                "description": "Smoke tests",
                "test_config_patterns": ["smoke"],
                "functions": ["test_python_smoke"]
            },
            # Inductor tests
            {
                "name": "inductor",
                "description": "Inductor compiler tests",
                "test_config_patterns": ["inductor"],
                "exclude_patterns": ["distributed", "cpp_wrapper"],
                "functions": ["test_inductor_shard"]
            },
            # Distributed tests
            {
                "name": "distributed",
                "description": "Distributed training tests",
                "test_config_patterns": ["distributed"],
                "functions": ["test_distributed", "test_rpc"]
            },
            # H100 specialized tests
            {
                "name": "h100_distributed",
                "description": "H100 distributed tests",
                "test_config_patterns": ["h100_distributed"],
                "functions": ["test_h100_distributed"]
            },
            {
                "name": "h100_symm_mem",
                "description": "H100 symmetric memory tests",
                "test_config_patterns": ["h100-symm-mem"],
                "functions": ["test_h100_symm_mem"]
            },
            {
                "name": "h100_cutlass_backend",
                "description": "H100 CUTLASS backend tests",
                "test_config_patterns": ["h100_cutlass_backend"],
                "functions": ["test_h100_cutlass_backend"]
            },
            # Build environment specific tests
            {
                "name": "libtorch",
                "description": "LibTorch C++ tests",
                "build_env_patterns": ["libtorch"],
                "functions": ["test_libtorch_cpp"]
            },
            {
                "name": "xpu",
                "description": "XPU backend tests",
                "build_env_patterns": ["xpu"],
                "functions": ["install_torchvision", "test_python", "test_aten", "test_xpu_bin"]
            }
        ]
        
        # Create and register test suites
        for suite_config in essential_suites:
            suite = ConditionalTestSuite(
                name=suite_config["name"],
                description=suite_config["description"],
                test_config_patterns=suite_config.get("test_config_patterns", []),
                build_env_patterns=suite_config.get("build_env_patterns", []),
                exclude_patterns=suite_config.get("exclude_patterns", [])
            )
            
            # Add test functions
            for func_name in suite_config["functions"]:
                suite.add_test_function(func_name)
            
            self.test_suites.append(suite)
    
    def get_test_suite(self, env_config: EnvironmentConfig) -> Optional[TestSuite]:
        """Get the appropriate test suite for the given environment configuration."""
        
        # Check each registered test suite in order
        for suite in self.test_suites:
            if suite.matches(env_config):
                self.logger.info(f"Selected test suite: {suite.name}")
                return suite
        
        # If no specific suite matches, return the default suite
        self.logger.info("No specific test suite matched, using default suite")
        return self.default_suite
    
    def list_test_suites(self) -> List[str]:
        """Get list of all registered test suite names."""
        return [suite.name for suite in self.test_suites] + [self.default_suite.name]
