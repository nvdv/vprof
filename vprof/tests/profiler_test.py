# pylint: disable=protected-access, missing-docstring
import unittest

from vprof import profiler

# For Python 2 and Python 3 compatibility.
try:
    import mock
except ImportError:
    from unittest import mock  # pylint: disable=ungrouped-imports


class ProfilerUnittest(unittest.TestCase):

    def setUp(self):
        self._profiler = object.__new__(profiler.Profiler)

    def testTransformStats(self):
        prof = mock.MagicMock()
        prof.total_tt = 0.075
        prof.stats = {
            ('fname1', 1, 'func1'): (5, 10, 0.001, 0.01, ()),
            ('fname1', 5, 'func2'): (10, 15, 0.002, 0.02, ()),
            ('fname2', 11, '<func3>'): (15, 20, 0.003, 0.045, ())
        }
        expected_results = [
            ('fname2', 11, '<func3>', 0.045, 60.0,
             20, 15, 0.003, 'fname2', 727188755),
            ('fname1', 5, 'func2', 0.02, 26.6667,
             15, 10, 0.002, 'fname1', 591398039),
            ('fname1', 1, 'func1', 0.01, 13.3333,
             10, 5, 0.001, 'fname1', 590742678),
        ]

        self.assertListEqual(
            self._profiler._transform_stats(prof), expected_results)

# pylint:  enable=protected-access, missing-docstring
