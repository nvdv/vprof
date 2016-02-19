"""Main test module."""
import unittest

from vprof.tests import base_profile_test
from vprof.tests import code_heatmap_test
from vprof.tests import memory_profile_test
from vprof.tests import runtime_profile_test


if __name__ == '__main__':
    loader, runner = unittest.TestLoader(), unittest.TextTestRunner()
    runner.run(loader.loadTestsFromModule(base_profile_test))
    runner.run(loader.loadTestsFromModule(code_heatmap_test))
    runner.run(loader.loadTestsFromModule(memory_profile_test))
    runner.run(loader.loadTestsFromModule(runtime_profile_test))
