# pylint: disable=protected-access, missing-docstring
import unittest

from vprof import profiler

# For Python 2 and Python 3 compatibility.
try:
    import mock
except ImportError:
    from unittest import mock  # pylint: disable=ungrouped-imports


class ProrilerUnittest(unittest.TestCase):

    def setUp(self):
        self._profiler = object.__new__(profiler.Profiler)

    def testTransformStats(self):
        prof = mock.MagicMock()
        prof.total_tt = 0.075
        prof.stats = {
            ('filename1', 1, 'func1'): (5, 10, 0.001, 0.01, ()),
            ('filename1', 5, 'func2'): (10, 15, 0.002, 0.02, ()),
            ('filename2', 11, '<func3>'): (15, 20, 0.003, 0.045, ())
        }
        expected_results = [
            ('filename2', 11, '[func3]', 0.045, 60.0, 20, 15, 0.003, 'filename2'),
            ('filename1', 5, 'func2', 0.02, 26.6667, 15, 10, 0.002, 'filename1'),
            ('filename1', 1, 'func1', 0.01, 13.3333, 10, 5, 0.001, 'filename1'),
        ]

        self.assertListEqual(
            self._profiler._transform_stats(prof), expected_results)

# pylint:  enable=protected-access, missing-docstring
