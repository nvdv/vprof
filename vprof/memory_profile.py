"""Module for memory profiling."""
import gc
import inspect
import os
import operator
import psutil
import re
import sys

from collections import deque
from collections import Counter
from vprof import base_profile

_BYTES_IN_MB = 1024 * 1024


def _remove_duplicates(objects):
    """Removes duplicate objects.

    Taken from http://www.peterbe.com/plog/uniqifiers-benchmark.
    """
    seen, uniq = set(), []
    for obj in objects:
        obj_id = id(obj)
        if obj_id in seen:
            continue
        seen.add(obj_id)
        uniq.append(obj)
    return uniq


def _get_in_memory_objects():
    """Returns all objects in memory."""
    gc.collect()
    return gc.get_objects()


def _process_in_memory_objects(objects):
    """Processes objects tracked by GC.

    Processing is done in separate function to avoid generating overhead.
    """
    return _remove_duplicates(
        [obj for obj in objects if not inspect.isframe(obj)])


def _get_memory_usage():
    """Returns memory usage for current process."""
    memory_info = psutil.Process(os.getpid()).memory_info()
    return float(memory_info.rss) / _BYTES_IN_MB


def _get_object_count_by_type(objects):
    """Counts Python objects by type."""
    return Counter(map(type, objects))


def _get_obj_count_difference(objs1, objs2):
    """Returns count difference in two collections of Python objects."""
    clean_obj_list1 = _process_in_memory_objects(objs1)
    clean_obj_list2 = _process_in_memory_objects(objs2)
    obj_count_1 = _get_object_count_by_type(clean_obj_list1)
    obj_count_2 = _get_object_count_by_type(clean_obj_list2)
    return obj_count_1 - obj_count_2


def _format_obj_count(obj_count):
    """Formats object count."""
    result = []
    regex = re.compile(r'<(?P<type>\w+) \'(?P<name>\S+)\'>')
    for obj_type, obj_count in obj_count.items():
        if obj_count != 0:
            match = re.findall(regex, repr(obj_type))
            t, name = match[0]
            pretty_type = 'instance' if t == 'class' else 'class'
            result.append(('%s %s' % (pretty_type, name), obj_count))
    return sorted(result, key=operator.itemgetter(1), reverse=True)


class CodeEventsTracker(object):
    """Tracks specified events during code execution.

    Class that contains all logic related to measuring memory usage after
    specified events occur during Python program execution.
    """

    def __init__(self):
        self._all_code = set()
        self.events_list = deque()
        self._original_trace_function = sys.gettrace()

    def add_code(self, code):
        """Recursively adds code to be examined."""
        if code not in self._all_code:
            self._all_code.add(code)
            for subcode in filter(inspect.iscode, code.co_consts):
                self.add_code(subcode)

    def __enter__(self):
        """Enables events tracker."""
        sys.settrace(self._trace_memory_usage)
        return self

    def __exit__(self, exc_type, exc_val, exc_tbf):
        """Disables events tracker."""
        sys.settrace(self._original_trace_function)

    def _trace_memory_usage(self, frame, event, arg):  #pylint: disable=unused-argument
        """Tracks memory usage when specified events occur."""
        if event == 'line' and frame.f_code in self._all_code:
            curr_memory = _get_memory_usage()
            if (self.events_list and self.events_list[-1][2] == event and
                    self.events_list[-1][0] == frame.f_lineno and
                    self.events_list[-1][1] != curr_memory):
                # Update previous if memory usage is greater on the same line.
                self.events_list[-1][1] = max(
                    curr_memory, self.events_list[-1][1])
            else:
                self.events_list.append(
                    [frame.f_lineno, curr_memory, event,
                     frame.f_code.co_name, frame.f_code.co_filename])
        return self._trace_memory_usage

    def get_obj_overhead(self):
        """Returns all objects that are counted as profiler overhead.

        Objects are hardcoded for convenience.
        """
        overhead = [
            self,
            self.events_list,
            self._all_code,
        ]
        overhead.extend(self.events_list)
        overhead_count = _get_object_count_by_type(overhead)
        # One for reference to __dict__ and one for reference to
        # the current module.
        overhead_count[dict] += 2
        return overhead_count


class MemoryProfile(base_profile.BaseProfile):
    """Memory profiler wrapper.

    Runs memory profiler and processes all obtained stats.
    """

    def run_as_package_path(self):
        """Runs program as package specified with file path."""
        import runpy
        pkg_code = base_profile.get_package_code(
            self._run_object, name_is_path=True)
        with CodeEventsTracker() as prof:
            for _, compiled_code in pkg_code.values():
                prof.add_code(compiled_code)
            try:
                runpy.run_path(self._run_object, run_name='__main__')
            except SystemExit:
                pass
        return prof

    def run_as_module(self):
        """Runs program as module."""
        try:
            with open(self._run_object, 'rb') as srcfile,\
                CodeEventsTracker() as prof:
                code = compile(srcfile.read(), self._run_object, 'exec')
                prof.add_code(code)
                exec(code, self._globs, None)
        except SystemExit:
            pass
        return prof

    def run_as_package_in_namespace(self):
        """Runs object as package in Python namespace."""
        import runpy
        pkg_code = base_profile.get_package_code(self._run_object)
        with CodeEventsTracker() as prof:
            for _, compiled_code in pkg_code.values():
                prof.add_code(compiled_code)
            try:
                runpy.run_module(self._run_object, run_name='__main__')
            except SystemExit:
                pass
        return prof

    def run_as_function(self):
        """Runs object as function."""
        with CodeEventsTracker() as prof:
            prof.add_code(self._run_object.__code__)
            self._run_object(*self._run_args, **self._run_kwargs)
        return prof

    def run(self):
        """Collects memory stats for specified Python program."""
        run_dispatcher = self.get_run_dispatcher()
        existing_objects = _get_in_memory_objects()
        prof = run_dispatcher()
        new_objects = _get_in_memory_objects()
        profiler_overhead = prof.get_obj_overhead()

        new_obj_count = _get_obj_count_difference(new_objects, existing_objects)
        result_obj_count = new_obj_count - profiler_overhead

        # existing_objects list is also profiler overhead
        result_obj_count[list] -= 1
        pretty_obj_count = _format_obj_count(result_obj_count)
        return {
            'objectName': self._object_name,  # Set on run dispatching.
            'codeEvents': [
                (i + 1, line, mem, event, func, fname)
                for i, (line, mem, event, func, fname) in enumerate(
                    prof.events_list)],
            'totalEvents': len(prof.events_list),
            'objectsCount': pretty_obj_count
        }
