# pylint: disable=protected-access, missing-docstring, too-many-locals
import unittest

from collections import deque
from vprof import memory_profiler

# For Python 2 and Python 3 compatibility.
try:
    import mock
except ImportError:
    from unittest import mock  # pylint: disable=ungrouped-imports


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

    def testAddCode(self):
        code = mock.MagicMock()
        self._tracker._all_code = set()
        self._tracker.add_code(code)
        self.assertIn(code, self._tracker._all_code)

    def testTraceMemoryUsage(self):
        self._tracker._process = mock.MagicMock()
        event, arg = 'line', mock.MagicMock()
        memory_info = mock.MagicMock()
        curr_memory = memory_info.rss
        self._tracker._process.memory_info.return_value = memory_info
        frame1, frame2 = mock.MagicMock(), mock.MagicMock()
        frame3, frame4 = mock.MagicMock(), mock.MagicMock()
        frame1.f_lineno, frame2.f_lineno = 1, 2
        frame3.f_lineno, frame4.f_lineno = 3, 4
        code1, code2 = frame1.f_code, frame2.f_code
        code3, code4 = frame3.f_code, frame4.f_code
        name1, name2 = code1.co_name, code2.co_name
        name3, name4 = code3.co_name, code4.co_name
        fname1, fname2 = code1.co_filename, code2.co_filename
        fname3, fname4 = code3.co_filename, code4.co_filename
        self._tracker._all_code = set((code1, code2, code3, code4))
        self._tracker._events_list = deque()

        self._tracker._trace_memory_usage(frame1, event, arg)
        self._tracker._trace_memory_usage(frame2, event, arg)
        self._tracker._trace_memory_usage(frame3, event, arg)
        self._tracker._trace_memory_usage(frame4, event, arg)

        self.assertEqual(
            self._tracker._events_list,
            deque(((1, curr_memory, name1, fname1),
                   (2, curr_memory, name2, fname2),
                   (3, curr_memory, name3, fname3),
                   (4, curr_memory, name4, fname4))))

    def testCodeEvents_NoDuplicates(self):
        self._tracker._resulting_events = []
        self._tracker.mem_overhead = 0
        frame1, frame2 = mock.MagicMock(), mock.MagicMock()
        frame3, frame4 = mock.MagicMock(), mock.MagicMock()
        code1, code2 = frame1.f_code, frame2.f_code
        code3, code4 = frame3.f_code, frame4.f_code
        name1, name2 = code1.co_name, code2.co_name
        name3, name4 = code3.co_name, code4.co_name
        fname1, fname2 = code1.co_filename, code2.co_filename
        fname3, fname4 = code3.co_filename, code4.co_filename

        self._tracker._events_list = deque((
            (1, 1024 * 1024, name1, fname1),
            (2, 1024 * 1024, name2, fname2),
            (3, 1024 * 1024, name3, fname3),
            (4, 1024 * 1024, name4, fname4)))

        self.assertListEqual(
            self._tracker.code_events,
            [[1, 1, 1.0, name1, fname1],
             [2, 2, 1.0, name2, fname2],
             [3, 3, 1.0, name3, fname3],
             [4, 4, 1.0, name4, fname4]])

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

# pylint: enable=protected-access, missing-docstring, too-many-locals
