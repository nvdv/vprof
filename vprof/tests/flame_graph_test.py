# pylint: disable=protected-access, missing-docstring
import unittest

from vprof import flame_graph


class StatProfilerUnittest(unittest.TestCase):

    def setUp(self):
        self._profiler = object.__new__(flame_graph._StatProfiler)

    def testCallTreeProperty(self):
        self.maxDiff = None
        self._profiler._call_tree = {}
        self._profiler._stats = {
            (('baz', 'f', 3), ('bar', 'f', 2), ('foo', 'f', 1)): 10,
            (('bar', 'f', 2), ('foo', 'f', 1)): 20,
            (('foo', 'f', 1),): 30,
            (('0', 'e', 4), ('baz', 'f', 3),
             ('bar', 'f', 2), ('foo', 'f', 1)): 40,
        }
        expected_result = {
            'stack': ('foo', 'f', 1),
            'sampleCount': 100,
            'colorHash': 159121963,
            'samplePercentage': 100.0,
            'children': [{
                'stack': ('bar', 'f', 2),
                'sampleCount': 70,
                'colorHash': 152764956,
                'samplePercentage': 70.0,
                'children': [{
                    'stack': ('baz', 'f', 3),
                    'sampleCount': 50,
                    'colorHash': 155386404,
                    'samplePercentage': 50.0,
                    'children': [{
                        'stack': ('0', 'e', 4),
                        'colorHash': 47841558,
                        'sampleCount': 40,
                        'samplePercentage': 40.0,
                        'children': []
                    }]
                }]
            }]
        }
        self.assertDictEqual(self._profiler.call_tree, expected_result)

# pylint:  enable=protected-access, missing-docstring
