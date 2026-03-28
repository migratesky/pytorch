"""
Basic test suites module that provides a centralized way to get all test suites.

This module serves as the main entry point for importing all test suite implementations
and provides a factory function to get all available test suites.
"""

from typing import List
from ..test_config.base import TestSuite

# Import all test suite implementations
from .python_tests import PythonTestSuite, PythonShardedTestSuite, SmokeTestSuite, Numpy2TestSuite
from .inductor_tests import (
    InductorTestSuite, InductorDistributedTestSuite, InductorCppWrapperTestSuite,
    InductorHalideTestSuite, InductorTritonCpuTestSuite, InductorMicrobenchmarkTestSuite,
    InductorAOTITestSuite
)
from .distributed_tests import DistributedTestSuite, DistributedRPCTestSuite, DistributedH100TestSuite
from .benchmark_tests import (
    OperatorBenchmarkTestSuite, TorchBenchTestSuite, DynamoBenchmarkTestSuite,
    CacheBenchTestSuite, VerifyCacheBenchTestSuite
)
from .coverage_tests import (
    CoveragePythonTestSuite, CoverageCppTestSuite, CoverageDockerTestSuite,
    CoverageDockerSingleTestSuite, CoverageDockerMultiTestSuite
)
from .mobile_tests import (
    MobileOptimizerTestSuite, LiteInterpreterTestSuite, MobileCodegenTestSuite,
    AndroidTestSuite, AndroidNDKTestSuite, IOSTestSuite, MobileCustomBuildTestSuite
)
from .specialized_tests import (
    BackwardTestSuite, XLATestSuite, ONNXTestSuite, JITLegacyTestSuite,
    Aarch64TestSuite, CrossCompileTestSuite, ROCmTestSuite, ASANTestSuite
)


def get_all_test_suites() -> List[TestSuite]:
    """
    Get all available test suites.
    
    Returns:
        List of all test suite instances
    """
    return [
        # Python test suites
        PythonTestSuite(),
        PythonShardedTestSuite(),
        SmokeTestSuite(),
        Numpy2TestSuite(),

        # Inductor test suites
        InductorTestSuite(),
        InductorDistributedTestSuite(),
        InductorCppWrapperTestSuite(),
        InductorHalideTestSuite(),
        InductorTritonCpuTestSuite(),
        InductorMicrobenchmarkTestSuite(),
        InductorAOTITestSuite(),

        # Distributed test suites
        DistributedTestSuite(),
        DistributedRPCTestSuite(),
        DistributedH100TestSuite(),

        # Benchmark test suites
        OperatorBenchmarkTestSuite(),
        TorchBenchTestSuite(),
        DynamoBenchmarkTestSuite(),
        CacheBenchTestSuite(),
        VerifyCacheBenchTestSuite(),

        # Coverage test suites
        CoveragePythonTestSuite(),
        CoverageCppTestSuite(),
        CoverageDockerTestSuite(),
        CoverageDockerSingleTestSuite(),
        CoverageDockerMultiTestSuite(),

        # Mobile test suites
        MobileOptimizerTestSuite(),
        LiteInterpreterTestSuite(),
        MobileCodegenTestSuite(),
        AndroidTestSuite(),
        AndroidNDKTestSuite(),
        IOSTestSuite(),
        MobileCustomBuildTestSuite(),

        # Specialized test suites
        BackwardTestSuite(),
        XLATestSuite(),
        ONNXTestSuite(),
        JITLegacyTestSuite(),
        Aarch64TestSuite(),
        CrossCompileTestSuite(),
        ROCmTestSuite(),
        ASANTestSuite(),
    ]


def get_test_suite_by_name(name: str) -> TestSuite:
    """
    Get a specific test suite by name.
    
    Args:
        name: Name of the test suite
        
    Returns:
        Test suite instance
        
    Raises:
        ValueError: If test suite name is not found
    """
    all_suites = get_all_test_suites()
    for suite in all_suites:
        if suite.name == name:
            return suite
    
    available_names = [suite.name for suite in all_suites]
    raise ValueError(f"Test suite '{name}' not found. Available suites: {available_names}")
