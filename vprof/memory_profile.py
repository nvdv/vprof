"""Module for memory profiling."""
import inspect
import os
import psutil
import sys

from collections import deque
from vprof import base_profile


_BYTES_IN_MB = 1024 * 1024


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
                    [frame.f_lineno, curr_memory, event, frame.f_code.co_name])
        return self._trace_memory_usage


class MemoryProfile(base_profile.BaseProfile):
    """Memory profiler wrapper.

    Runs memory profiler and processes all obtained stats.
    """

    def run(self):
        """Collects memory stats for specified Python program."""
        try:
            with open(self._program_name, 'rb') as srcfile,\
                CodeEventsTracker() as prof:
                code = compile(srcfile.read(), self._program_name, 'exec')
                prof.add_code(code)
                exec(code, self._globs, None)
        except SystemExit:
            pass
        return {
            'programName': self._program_name,
            'codeEvents': [
                (i + 1, line, mem, event, func)
                for i, (line, mem, event, func) in enumerate(prof.events_list)],
            'totalEvents': len(prof.events_list)
        }
