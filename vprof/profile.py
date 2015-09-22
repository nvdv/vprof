"""Various profile wrappers"""
import abc
import cProfile
import inspect
import memory_profiler
import os
import pstats
import sys

from collections import defaultdict
from collections import OrderedDict


class Profile(object):
    """Base class for profile processing."""
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self):
        pass

    @abc.abstractmethod
    def run(self):
        """Runs profile and returns profile stats."""
        pass


class CProfile(Profile):
    """Class that contains CProfile stats processing logic.

    This class contains all logic related to cProfile run, stats collection
    and processing. All function call info is contained in stats.Pstats, all
    we have to do is to run cProfile and build call tree from resulting
    pstats.Stats.
    """

    def __init__(self, program_name):
        """Initializes cProfile wrapper.

        Args:
            program_name: Name of the program to profile.
        """
        self._program_name = program_name

    def _build_callees(self, stats):
        """Extracts call tree from cProfile stats."""
        callees = defaultdict(list)
        for func, (_, _, _, _, callers) in stats.iteritems():
            for caller in callers:
                callees[caller].append(func)
        return callees

    def _build_call_tree(self, node, callees, stats, seen=set()):
        """Builds call tree from callees tree and cProfile stats.

        Args:
            node: Call to build tree from.
            callees: Calless tree with call dependencies.
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
            'timeOerCall': time_per_call,
            'cumTime': cum_time,
            'children': [self._build_call_tree(child, callees, stats, seen)
                         for child in callees[node] if child not in seen]
        }

    def _transform_stats(self, stats):
        """Converts stats from cProfile format to call tree format."""

        def _statcmp(stat):
            """Comparator by cummulative time."""
            _, params = stat
            return params[3]

        stats.calc_callees()
        callees = self._build_callees(stats.stats)
        root, _ = max(stats.stats.iteritems(), key=_statcmp)
        return self._build_call_tree(root, callees, stats.stats)

    def run(self):
        """Returns CProfile stats for specified Python program."""
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
        return {
            'programName': self._program_name,
            'runTime': cprofile_stats.total_tt,
            'primitiveCalls': cprofile_stats.prim_calls,
            'totalCalls': cprofile_stats.total_calls,
            'callStats': self._transform_stats(cprofile_stats),
        }


class _TracingLineProfiler(memory_profiler.LineProfiler):
    """Subclass of memory_profiler.LineProfiler.

    Used to track order of code execution by using OrderedDict instead
    of just Python dictionary.
    """

    def __init__(self, **kw):
        super(_TracingLineProfiler, self).__init__(*kw)
        self.code_map = OrderedDict()

    def add_code(self, code, toplevel_code=None):
        if code not in self.code_map:
            self.code_map[code] = OrderedDict()
            for subcode in filter(inspect.iscode, code.co_consts):
                self.add_code(subcode)


class MemoryProfile(Profile):
    """Class that contains memory profiler stats processing logic.

    Runs memory profiler and extracts collected info from code_map.
    """

    def __init__(self, program_name):
        """Initializes memory profile wrapper.

        Args:
            program_name: Name of the program to profile.
        """
        self._program_name = program_name

    def _transform_stats(self, code_stats):
        """Converts stats from memory_profiler format."""
        memory_stats = []
        for code, lines in code_stats.items():
            for line, usage in lines.items():
                line_id = '%s:%s(%s)' % (code.co_filename, line, code.co_name)
                memory_stats.append((line_id, usage))
        return memory_stats

    def run(self):
        """Returns memory stats for specified Python program."""
        globs = {
            '__file__': self._program_name,
            '__name__': '__main__',
            '__package__': None,
        }
        sys.path.insert(0, os.path.dirname(self._program_name))
        prof = _TracingLineProfiler()
        try:
            with open(self._program_name, 'rb') as srcfile:
                code = compile(srcfile.read(), self._program_name, 'exec')
            prof.add_code(code)
            prof.enable()
            exec(code, globs, None)
            prof.disable()
        except SystemExit:
            pass
        return {
            'programName': self._program_name,
            'memoryStats': self._transform_stats(prof.code_map),
        }
