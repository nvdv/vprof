import collections
import copy
import mock
import vprof.profile_wrappers as profile_wrappers
import unittest


class AbstractProfileUnittest(unittest.TestCase):
    def testAbstractness(self):
        self.assertRaises(TypeError, profile_wrappers.BaseProfile)


_RUN_STATS = {
    ('testscript.py', 1, 'prod'): (1, 10, 7e-06, 7e-06, {
        ('testscript.py', 1, '<module>'): (1, 1, 1e-06, 7e-06),
        ('testscript.py', 1, 'prod'): (9, 1, 6e-06, 6e-06)
    }),
    ('testscript.py', 1, '<module>'): (1, 1, 1.49, 2.3e-05, {}),
    ('~', 0, '<range>'): (1, 1, 1e-06, 1e-06, {
        ('testscript.py', 1, '<module>'): (1, 1, 1e-06, 1e-06)
    })
}

_CALLEES = {
    ('testscript.py', 1, '<module>'): [
        ('testscript.py', 1, 'prod'),
        ('~', 0, '<range>'),
    ],
    ('testscript.py', 1, 'prod'): [
        ('testscript.py', 1, 'prod')
    ]
}

_CALL_GRAPH = {
    'moduleName': 'testscript.py',
    'funcName': '<module>',
    'totalCalls': 1,
    'primCalls': 1,
    'timePerCall': 1.49,
    'cumTime': 2.3e-05,
    'lineno': 1,
    'children': [
        {'funcName': 'prod',
         'primCalls': 1,
         'totalCalls': 10,
         'timePerCall': 7e-06,
         'cumTime': 7e-06,
         'lineno': 1,
         'moduleName': 'testscript.py',
         'children': []},
        {'funcName': '<range>',
         'primCalls': 1,
         'totalCalls': 1,
         'timePerCall': 1e-06,
         'cumTime': 1e-06,
         'lineno': 0,
         'moduleName': '~',
         'children': []}
    ]
}


class RuntimeProfileUnittest(unittest.TestCase):
    def setUp(self):
        self._profile = object.__new__(profile_wrappers.RuntimeProfile)

    def testInit(self):
        filename = mock.MagicMock()
        self._profile.__init__(filename)
        self.assertEqual(self._profile._program_name, filename)

    def testBuildCallees(self):
        self.assertDictEqual(
            dict(self._profile._build_callees(_RUN_STATS)), _CALLEES)

    def testTransformStats(self):
        stats = mock.MagicMock()
        stats.stats = _RUN_STATS
        self.assertDictEqual(
            self._profile._transform_stats(stats), _CALL_GRAPH)


class MemoryProfileUnittest(unittest.TestCase):
    def setUp(self):
        self._profile = object.__new__(profile_wrappers.MemoryProfile)

    def testTransformStats(self):
        code_obj1, code_obj2 = mock.MagicMock(), mock.MagicMock()
        code_obj1.co_filename, code_obj2.co_filename = 'foo.py', 'bar.py'
        code_obj1.co_name, code_obj2.co_name = 'baz', 'mno'
        code_stats = collections.OrderedDict()
        code_stats[code_obj1] = {10: 20}
        code_stats[code_obj2] = {30: 40}
        self.assertListEqual(
            self._profile._transform_stats(code_stats),
            [(('foo.py', 10, 'baz'), 20), (('bar.py', 30, 'mno'), 40)])


class CodeEventsTrackerUnittest(unittest.TestCase):
    def setUp(self):
        self._tracker = object.__new__(profile_wrappers.CodeEventsTracker)

    def testAddCode(self):
        code = mock.MagicMock()
        self._tracker._all_code = set()
        self._tracker.add_code(code)
        self.assertIn(code, self._tracker._all_code)
