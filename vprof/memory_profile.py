"""Module for memory profiling."""
import inspect
import os
import psutil
import sys

from collections import deque
from vprof import base_profile

_BYTES_IN_MB = 1024 * 1024


class Error(Exception):
    """Base exception for current module."""
    pass


class MemoryProfilerRunError(Error, base_profile.ProfilerRuntimeException):
    """Runtime exception for memory profiler."""
    pass


def get_memory_usage():
    """Returns memory usage for current process."""
    memory_info = psutil.Process(os.getpid()).memory_info()
    return float(memory_info.rss) / _BYTES_IN_MB


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
            curr_memory = get_memory_usage()
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
            except ImportError:
                raise MemoryProfilerRunError(
                    'Unable to run package %s' % self._run_object)
            except SystemExit:
                pass
        return prof.events_list

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
        return prof.events_list

    def run_as_package_in_namespace(self):
        """Runs object as package in Python namespace."""
        import runpy
        pkg_code = base_profile.get_package_code(self._run_object)
        with CodeEventsTracker() as prof:
            for _, compiled_code in pkg_code.values():
                prof.add_code(compiled_code)
            try:
                runpy.run_module(self._run_object, run_name='__main__')
            except ImportError:
                raise MemoryProfilerRunError(
                    'Unable to run package %s' % self._run_object)
            except SystemExit:
                pass
        return prof.events_list

    def run_as_function(self):
        """Runs object as function."""
        with CodeEventsTracker() as prof:
            prof.add_code(self._run_object.__code__)
            self._run_object(*self._run_args, **self._run_kwargs)
        return prof.events_list

    def run(self):
        """Collects memory stats for specified Python program."""
        run_dispatcher = self.get_run_dispatcher()
        events_list = run_dispatcher()
        return {
            'objectName': self._object_name,  # Set on run dispatching.
            'codeEvents': [
                (i + 1, line, mem, event, func, fname)
                for i, (line, mem, event, func, fname) in enumerate(
                    events_list)],
            'totalEvents': len(events_list)
        }
