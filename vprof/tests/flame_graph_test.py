# pylint: disable=protected-access, missing-docstring
import unittest

from vprof import flame_graph


class StatProfilerUnittest(unittest.TestCase):

    def setUp(self):
        self._profiler = object.__new__(flame_graph._StatProfiler)

    def testExtractStackParams(self):
        total_samples = 100
        node = {
            'stack': ('<funcname>', '<filename>', 10),
            'sampleCount': 100
        }
        self.assertEqual(
            self._profiler._extract_stack_params(node, total_samples),
            ('[funcname]', '[filename]', 10, 100.0))

        total_samples = 0
        self.assertEqual(
            self._profiler._extract_stack_params(node, total_samples),
            ('[funcname]', '[filename]', 10, 0.0))

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
            'stack': ('foo', 'f', 1, 100.0),
            'sampleCount': 100,
            'colorHash': 159121963,
            'children': [{
                'stack': ('bar', 'f', 2, 70.0),
                'sampleCount': 70,
                'colorHash': 152764956,
                'children': [{
                    'stack': ('baz', 'f', 3, 50.0),
                    'sampleCount': 50,
                    'colorHash': 155386404,
                    'children': [{
                        'stack': ('0', 'e', 4, 40.0),
                        'colorHash': 47841558,
                        'sampleCount': 40,
                        'children': []
                    }]
                }]
            }]
        }
        self.assertDictEqual(self._profiler.call_tree, expected_result)

# pylint:  enable=protected-access, missing-docstring
