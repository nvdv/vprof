"""Profile wrappers."""
import cProfile
import inspect
import multiprocessing
import os
import pstats
import psutil
import sys

from collections import defaultdict
from collections import deque

# For Python 2 and Python 3 compatibility.
try:
    import cStringIO as io
except ImportError:
    import io


_BYTES_IN_MB = 1024 * 1024


def get_memory_usage():
    """Returns memory usage for current process."""
    memory_info = psutil.Process(os.getpid()).memory_info()
    return float(memory_info.rss) / _BYTES_IN_MB


class BaseProfile(object):
    """Base class for profile wrapper."""

    def __init__(self, program_name):  #pylint: disable=W0231
        """Initializes wrapper.

        Args:
            program_name: Name of the program to profile.
        """
        self._program_name = program_name

    def collect_stats(self, run_stats):
        """Collects stats and inserts them into run_stats dict."""
        raise NotImplementedError

    def run(self):
        """Runs profile and returns collected stats.

        Runs profiler in separate process to ensure correct stats collection.
        """
        result_stats = multiprocessing.Manager().dict()  #pylint: disable=E1101
        subprocess = multiprocessing.Process(
            target=self.collect_stats, args=(result_stats,))  #pylint: disable=E1101
        subprocess.start()
        subprocess.join()
        return dict(result_stats)


class RuntimeProfile(BaseProfile):
    """CProfile wrapper.

    This class contains all logic related to cProfile run, stats collection
    and processing. All function call info is contained in stats.Pstats, all
    we have to do is to run cProfile and build call tree from resulting
    pstats.Stats.
    """

    def _build_callees(self, stats):
        """Extracts call tree from pstats.Stats."""
        callees = defaultdict(list)
        for func, (_, _, _, _, callers) in sorted(stats.items()):
            for caller in callers:
                callees[caller].append(func)
        return callees

    def _build_call_tree(self, node, callees, stats, seen=set()):  #pylint: disable=W0102
        """Builds call tree from callees tree and pstats.Stats.

        Args:
            node: Current call tree node.
            callees: Callees tree with call dependencies.
            stats: Profile stats.
            seen: Set to track previously seen nodes to handle recursion.
        Returns:
            A dict representing call tree with all necessary parameters.
        """
        seen.add(node)
        module_name, lineno, func_name = node
        cum_calls, num_calls, time_per_call, cum_time, _ = stats[node]
        return {
            'moduleName': module_name,
            'lineno': lineno,
            'funcName': func_name,
            'primCalls': cum_calls,
            'totalCalls': num_calls,
            'timePerCall': time_per_call,
            'cumTime': cum_time,
            'children': [self._build_call_tree(child, callees, stats, seen)
                         for child in callees[node] if child not in seen]
        }

    def _transform_stats(self, stats):
        """Converts stats from pststs.Stats format to call nested dict."""

        def _statcmp(stat):
            """Comparator by cummulative time."""
            _, params = stat
            return params[3]

        stats.calc_callees()
        callees = self._build_callees(stats.stats)
        root, _ = max(stats.stats.items(), key=_statcmp)
        return self._build_call_tree(root, callees, stats.stats)

    def collect_stats(self, run_stats):
        """Collects CProfile stats for specified Python program."""
        globs = {
            '__file__': self._program_name,
            '__name__': '__main__',
            '__package__': None,
        }
        sys.path.insert(0, os.path.dirname(self._program_name))
        prof = cProfile.Profile()
        try:
            with open(self._program_name, 'rb') as srcfile:
                code = compile(srcfile.read(), self._program_name, 'exec')
            prof.runctx(code, globs, None)
        except SystemExit:
            pass
        prof.create_stats()
        cprofile_stats = pstats.Stats(prof)
        run_stats['programName'] = self._program_name
        run_stats['runTime'] = cprofile_stats.total_tt
        run_stats['primitiveCalls'] = cprofile_stats.prim_calls
        run_stats['totalCalls'] = cprofile_stats.total_calls
        run_stats['callStats'] = self._transform_stats(cprofile_stats)


class CodeEventsTracker(object):
    """Tracks specified events during code execution.

    Class that contains all logic related to measuring memory usage after
    specified events occur during Python program execution.
    """

    def __init__(self):
        self._all_code = set()
        self.events_list = deque()
        self._original_trace_function = sys.gettrace()
        self._prev_line = None
        self._prev_event = None
        self._prev_memory = None
        self._stderr = None
        self._redirect_file = io.StringIO()

    def add_code(self, code):
        """Recursively adds code to be examined."""
        if code not in self._all_code:
            self._all_code.add(code)
            for subcode in filter(inspect.iscode, code.co_consts):
                self.add_code(subcode)

    def __enter__(self):
        """Enables events tracker."""
        sys.settrace(self._trace_memory_usage)
        self._stderr = sys.stderr
        sys.stderr = self._redirect_file
        return self

    def __exit__(self, exc_type, exc_val, exc_tbf):
        """Disables events tracker."""
        sys.settrace(self._original_trace_function)
        sys.stderr = self._stderr

    def _trace_memory_usage(self, frame, event, arg):  #pylint: disable=W0613
        """Tracks memory usage when specified events occur."""
        if event == 'line' and frame.f_code in self._all_code:
            curr_memory = get_memory_usage()
            if not self.events_list:
                self.events_list.append(
                    [frame.f_lineno, curr_memory, event, frame.f_code.co_name])
            else:
                if (event == self._prev_event and
                        frame.f_code.co_name == self._prev_line):
                    # Update if memory consumption is greater on the same line.
                    if curr_memory != self._prev_memory:
                        curr_memory = max(curr_memory, self._prev_memory)
                        self.events_list[-1][1] = curr_memory
                else:
                    self.events_list.append([frame.f_lineno, curr_memory, event,
                                             frame.f_code.co_name])
            self._prev_line = frame.f_code.co_name
            self._prev_event = event
            self._prev_memory = curr_memory
        return self._trace_memory_usage


class MemoryProfile(BaseProfile):
    """Memory profiler wrapper.

    Runs memory profiler and processes all obtained stats.
    """

    def _transform_stats(self, code_stats):
        memory_stats = []
        for code, lines in code_stats.items():
            for line, usage in lines.items():
                line_id = (code.co_filename, line, code.co_name)
                memory_stats.append((line_id, usage))
        return memory_stats

    def collect_stats(self, run_stats):
        """Collects memory stats for specified Python program."""
        globs = {
            '__file__': self._program_name,
            '__name__': '__main__',
            '__package__': None,
        }
        sys.path.insert(0, os.path.dirname(self._program_name))
        try:
            with open(self._program_name, 'rb') as srcfile,\
                CodeEventsTracker() as prof:
                code = compile(srcfile.read(), self._program_name, 'exec')
                prof.add_code(code)
                exec(code, globs, None)
                events_list = prof.events_list
        except SystemExit:
            pass
        run_stats['programName'] = self._program_name
        run_stats['codeEvents'] = [
            (i + 1, lineno, mem, e, fname)
            for i, (lineno, mem, e, fname) in enumerate(events_list)]
        run_stats['totalEvents'] = len(events_list)

    def run(self):
        """Runs profile and returns collected stats.

        Runs memory stats collection in current process to avoid copy-on-write.
        """
        memory_stats = {}
        self.collect_stats(memory_stats)
        return memory_stats


class CodeHeatmapCalculator(object):
    """Calculates Python code heatmap.

    Class that contains all logic related to calculating execution heatmap
    for Python program.
    """

    def __init__(self):
        self._all_code = set()
        self._original_trace_function = sys.gettrace()
        self.heatmap = defaultdict(int)

    def add_code(self, code):
        """Recursively adds code to be examined."""
        if code not in self._all_code:
            self._all_code.add(code)
            for subcode in filter(inspect.iscode, code.co_consts):
                self.add_code(subcode)

    def __enter__(self):
        """Enables heatmap calculator."""
        sys.settrace(self._calc_heatmap)
        return self

    def __exit__(self, exc_type, exc_val, exc_tbf):
        """Disables heatmap calculator."""
        sys.settrace(self._original_trace_function)

    def _calc_heatmap(self, frame, event, arg):  #pylint: disable=W0613
        """Calculates code heatmap."""
        if event == 'line' and frame.f_code in self._all_code:
            self.heatmap[frame.f_lineno] += 1
        return self._calc_heatmap


class CodeHeatmapProfile(BaseProfile):
    """Code heatmap wrapper.

    Contains all logic related to heatmap calculation and processing.
    """

    def collect_stats(self, run_stats):
        """Calculates code heatmap for specified Python program."""
        globs = {
            '__file__': self._program_name,
            '__name__': '__main__',
            '__package__': None,
        }
        sys.path.insert(0, os.path.dirname(self._program_name))
        try:
            with open(self._program_name, 'rb') as srcfile,\
                CodeHeatmapCalculator() as prof:
                src_code = srcfile.read()
                code = compile(src_code, self._program_name, 'exec')
                prof.add_code(code)
                exec(code, globs, None)
                heatmap = prof.heatmap
        except SystemExit:
            pass
        run_stats['programName'] = self._program_name
        run_stats['srcCode'] = src_code
        run_stats['heatmap'] = list(sorted(heatmap.items()))
