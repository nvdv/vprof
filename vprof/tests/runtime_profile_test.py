# pylint: disable=protected-access, missing-docstring
import unittest

from vprof import runtime_profile


class StatProrilerUnittest(unittest.TestCase):
    def setUp(self):
        self._profiler = object.__new__(runtime_profile._StatProfiler)

    def testCallTreeProperty(self):
        self.maxDiff = None
        self._profiler._call_tree = {}
        self._profiler._stats = {
            (('baz', 3, 'f'), ('bar', 2, 'f'), ('foo', 1, 'f')): 10,
            (('bar', 2, 'f'), ('foo', 1, 'f')): 20,
            (('foo', 1, 'f'),): 30,
            (('0', 4, 'e'), ('baz', 3, 'f'), ('bar', 2, 'f'), ('foo', 1, 'f')): 40,
        }
        expected_result = {
            'stack': ('base', 1, ''),
            'sampleCount': 100,
            'children': [{
                'stack': ('foo', 1, 'f'),
                'sampleCount': 100,
                'children': [{
                    'stack': ('bar', 2, 'f'),
                    'sampleCount': 70,
                    'children': [{
                        'stack': ('baz', 3, 'f'),
                        'sampleCount': 50,
                        'children': [{
                            'stack': ('0', 4, 'e'),
                            'sampleCount': 40,
                            'children': []
                        }]
                    }]
                }]
            }]
        }
        self.assertDictEqual(self._profiler.call_tree, expected_result)

# pylint:  enable=protected-access, missing-docstring
