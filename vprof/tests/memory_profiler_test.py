"""Unit tests for memory profiler module."""
# pylint: disable=protected-access
from collections import deque
import unittest
from unittest import mock

from vprof import memory_profiler


class GetObjectCountByTypeUnittest(unittest.TestCase):

    def testGetObjectByType(self):
        objects = [1, 2, 3, 'a', 'b', 'c', {}, []]
        obj_count = memory_profiler._get_object_count_by_type(objects)
        self.assertEqual(obj_count[int], 3)
        self.assertEqual(obj_count[str], 3)
        self.assertEqual(obj_count[dict], 1)
        self.assertEqual(obj_count[list], 1)


class GetObjCountDifferenceUnittest(unittest.TestCase):

    def testGetCountObjByType(self):
        objects1 = [1, 2, 3, 'a', 'b', 'c', {}, []]
        objects2 = [1, 2, 'a', 'b', {}]
        self.assertDictEqual(
            memory_profiler._get_obj_count_difference(objects1, objects2),
            {int: 1, str: 1, list: 1})


class CodeEventsTrackerUnittest(unittest.TestCase):
    def setUp(self):
        self._tracker = object.__new__(memory_profiler._CodeEventsTracker)

    def testTraceMemoryUsage(self):
        self._tracker._process = mock.MagicMock()
        event, arg = 'line', mock.MagicMock()
        memory_info = mock.MagicMock()
        curr_memory = memory_info.rss
        self._tracker._process.memory_info.return_value = memory_info
        frames = [mock.MagicMock(f_lineno=i) for i in range(1, 5)]
        self._tracker.target_modules = {f.f_code.co_filename for f in frames}
        self._tracker._events_list = deque()

        for frame in frames:
            self._tracker._trace_memory_usage(frame, event, arg)

        self.assertEqual(
            self._tracker._events_list,
            deque((f.f_lineno, curr_memory, f.f_code.co_name,
                   f.f_code.co_filename) for f in frames))

    def testCodeEvents_NoDuplicates(self):
        self._tracker._resulting_events = []
        self._tracker.mem_overhead = 0
        codes = [mock.MagicMock() for _ in range(4)]

        self._tracker._events_list = deque(
            (i + 1, 1024 * 1024, c.co_name, c.co_filename)
            for i, c in enumerate(codes))

        self.assertListEqual(
            self._tracker.code_events,
            [[i + 1, i + 1, 1.0, c.co_name, c.co_filename]
             for i, c in enumerate(codes)])

    def testCodeEvents_Duplicates(self):
        self._tracker._resulting_events = []
        self._tracker.mem_overhead = 0
        frame1, frame2 = mock.MagicMock(), mock.MagicMock()
        code1, code2 = frame1.f_code, frame2.f_code
        name1, name2 = code1.co_name, code2.co_name
        fname1, fname2 = code1.co_filename, code2.co_filename

        self._tracker._events_list = deque((
            (1, 1024 * 1024, name1, fname1),
            (1, 1024 * 1024 * 2, name1, fname1),
            (1, 1024 * 1024 * 3, name1, fname1),
            (2, 1024 * 1024, name2, fname2)))

        self.assertListEqual(
            self._tracker.code_events,
            [[1, 1, 1.0, name1, fname1],
             [2, 1, 2.0, name1, fname1],
             [3, 1, 3.0, name1, fname1],
             [4, 2, 1.0, name2, fname2]])
