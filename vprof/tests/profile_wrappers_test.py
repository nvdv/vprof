import collections
import copy
import vprof.profile_wrappers as profile_wrappers
import sys
import unittest

from collections import defaultdict
from collections import deque

# For Python 2 and Python 3 compatibility.
try:
    import mock
except ImportError:
    from unittest import mock

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


class BaseProfileUnittest(unittest.TestCase):
    def setUp(self):
        self._profile = object.__new__(profile_wrappers.BaseProfile)

    def testInit(self):
        program_cmd = 'foo.py --bar --baz'
        self._profile.__init__(program_cmd)
        self.assertEqual(self._profile._program_name, 'foo.py')
        self.assertEqual(self._profile._program_args, ['foo.py', '--bar', '--baz'])
        self.assertDictEqual(self._profile._globs, {
            '__file__': 'foo.py',
            '__name__': '__main__',
            '__package__': None
        })

    def testCollectStats(self):
        result = {'foo': 'bar', 'baz': 'mno'}
        self._profile._program_name = 'foo.py'
        self._profile._program_args = ['--foo', '--bar']
        self._profile.run_profiler = mock.MagicMock(return_value=result)
        run_stats = {}
        self._profile.collect_stats(run_stats)
        self.assertDictEqual(run_stats, result)


class RuntimeProfileUnittest(unittest.TestCase):
    def setUp(self):
        self._profile = object.__new__(profile_wrappers.RuntimeProfile)

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

    def testTraceMemoryUsage_OtherCode(self):
        code = mock.MagicMock()
        frame, event, arg = mock.MagicMock(), 'line', mock.MagicMock()
        self._tracker._all_code = set()
        self._tracker.events_list = deque()
        self._tracker._trace_memory_usage(frame, event, arg)
        self.assertFalse(self._tracker.events_list)

    @mock.patch('vprof.profile_wrappers.get_memory_usage')
    def testTraceMemoryUsage_EmptyEventsList(self, get_memory_mock):
        frame, event, arg = mock.MagicMock(), 'line', mock.MagicMock()
        curr_memory = get_memory_mock.return_value
        lineno, co_name = frame.f_lineno, frame.f_code.co_name
        code = frame.f_code
        self._tracker._all_code = set((code,))
        self._tracker.events_list = deque()
        self._tracker._trace_memory_usage(frame, event, arg)
        self.assertListEqual(
            self._tracker.events_list[-1],
            [lineno, curr_memory, event, co_name])

    @mock.patch('vprof.profile_wrappers.get_memory_usage')
    def testTraceMemoryUsage_NormalUsage(self, get_memory_mock):
        event, arg = 'line', mock.MagicMock()
        curr_memory = get_memory_mock.return_value
        frame1, frame2 = mock.MagicMock(), mock.MagicMock()
        frame3, frame4 = mock.MagicMock(), mock.MagicMock()
        frame1.f_lineno, frame2.f_lineno = 1, 2
        frame3.f_lineno, frame4.f_lineno = 3, 4
        code1, code2 = frame1.f_code, frame2.f_code
        code3, code4 = frame3.f_code, frame4.f_code
        name1, name2 = code1.co_name, code2.co_name
        name3, name4 = code3.co_name, code4.co_name
        self._tracker._all_code = set((code1, code2, code3, code4))
        self._tracker.events_list = deque()

        self._tracker._trace_memory_usage(frame1, event, arg)
        self._tracker._trace_memory_usage(frame2, event, arg)
        self._tracker._trace_memory_usage(frame3, event, arg)
        self._tracker._trace_memory_usage(frame4, event, arg)

        self.assertEqual(
            self._tracker.events_list,
            deque(([1, curr_memory, event, name1],
                   [2, curr_memory, event, name2],
                   [3, curr_memory, event, name3],
                   [4, curr_memory, event, name4])))

    @mock.patch('vprof.profile_wrappers.get_memory_usage')
    def testTraceMemoryUsage_SameLine(self, get_memory_mock):
            event, arg = 'line', mock.MagicMock()
            get_memory_mock.side_effect = [10, 20, 30, 40]
            frame1, frame2 = mock.MagicMock(), mock.MagicMock()
            frame1.f_lineno, frame2.f_lineno = 1, 2
            code1, code2 = frame1.f_code, frame2.f_code
            name1, name2 = code1.co_name, code2.co_name
            self._tracker._all_code = set((code1, code2))
            self._tracker.events_list = deque()

            self._tracker._trace_memory_usage(frame1, event, arg)
            self._tracker._trace_memory_usage(frame1, event, arg)
            self._tracker._trace_memory_usage(frame1, event, arg)
            self._tracker._trace_memory_usage(frame2, event, arg)

            self.assertEqual(
                self._tracker.events_list,
                deque(([1, 30, event, name1],
                       [2, 40, event, name2])))


class CodeHeatmapCalculator(unittest.TestCase):
    def setUp(self):
        self._calc = object.__new__(profile_wrappers.CodeHeatmapCalculator)

    def testInit(self):
        self._calc.__init__()
        self.assertEqual(self._calc._all_code, set())
        self.assertEqual(self._calc._original_trace_function, sys.gettrace())
        self.assertEqual(self._calc.heatmap, defaultdict(int))

    def testAddCode(self):
        code = mock.MagicMock()
        self._calc._all_code = set()
        self._calc.add_code(code)
        self.assertIn(code, self._calc._all_code)

    def testCalcHeatmap(self):
        self._calc.heatmap = defaultdict(int)
        event, arg = 'line', mock.MagicMock()
        frame1, frame2 = mock.MagicMock(), mock.MagicMock()
        frame1.f_code, frame1.f_code = 'foo1', 'foo2'
        frame1.f_lineno, frame2.f_lineno = 1, 2
        self._calc._all_code = set((frame1.f_code, frame2.f_code))

        self._calc._calc_heatmap(frame1, event, arg)
        self._calc._calc_heatmap(frame2, event, arg)

        self.assertEqual(self._calc.heatmap[frame1.f_lineno], 1)
        self.assertEqual(self._calc.heatmap[frame2.f_lineno], 1)
