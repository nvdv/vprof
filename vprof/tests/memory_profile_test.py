import unittest

from collections import deque
from vprof import memory_profile

# For Python 2 and Python 3 compatibility.
try:
    import mock
except ImportError:
    from unittest import mock


class CodeEventsTrackerUnittest(unittest.TestCase):
    def setUp(self):
        self._tracker = object.__new__(memory_profile.CodeEventsTracker)

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

    @mock.patch('vprof.memory_profile.get_memory_usage')
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

    @mock.patch('vprof.memory_profile.get_memory_usage')
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

    @mock.patch('vprof.memory_profile.get_memory_usage')
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
