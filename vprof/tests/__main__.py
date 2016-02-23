"""Main test module."""
import multiprocessing
import unittest

from vprof.tests import base_profile_test
from vprof.tests import code_heatmap_test
from vprof.tests import memory_profile_test
from vprof.tests import runtime_profile_test

from vprof.tests import code_heatmap_e2e_test
from vprof.tests import memory_profile_e2e_test

_UNITTESTS = (
    base_profile_test,
    code_heatmap_test,
    memory_profile_test,
    runtime_profile_test,
)

_END_TO_END_TESTS = (
    code_heatmap_e2e_test,
    memory_profile_e2e_test,
)


def launch_test_module(module):
    """Loads tests from module and runs them."""
    curr_runner, curr_loader = unittest.TextTestRunner(), unittest.TestLoader()
    curr_runner.run(curr_loader.loadTestsFromModule(module))


if __name__ == '__main__':
    loader, runner = unittest.TestLoader(), unittest.TextTestRunner()
    all_unittests = unittest.TestSuite(
        loader.loadTestsFromModule(test) for test in _UNITTESTS)
    runner.run(all_unittests)

    # Run end to end tests in parallel.
    for test in _END_TO_END_TESTS:
        process = multiprocessing.Process(
            target=launch_test_module, args=(test,))
        process.start()
