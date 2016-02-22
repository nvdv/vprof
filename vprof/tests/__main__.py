"""Main test module."""
import unittest

from vprof.tests import base_profile_test
from vprof.tests import code_heatmap_test
from vprof.tests import memory_profile_test
from vprof.tests import runtime_profile_test

from vprof.tests import code_heatmap_e2e_test

_UNITTESTS = (
    base_profile_test,
    code_heatmap_test,
    memory_profile_test,
    runtime_profile_test,
)

_END_TO_END_TESTS = (
    code_heatmap_e2e_test,
)

if __name__ == '__main__':
    loader, runner = unittest.TestLoader(), unittest.TextTestRunner()
    all_unittests = unittest.TestSuite(
        loader.loadTestsFromModule(test) for test in _UNITTESTS)
    e2e_tests = unittest.TestSuite(
        loader.loadTestsFromModule(test) for test in _END_TO_END_TESTS)
    runner.run(all_unittests)
    runner.run(e2e_tests)
