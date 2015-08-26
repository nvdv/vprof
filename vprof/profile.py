"""Various profile wrappers"""
import abc
import cProfile
import os
import pstats
import sys
from collections import defaultdict


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
    """Class that wraps CProfile stats."""

    def __init__(self, program_name, prune_threshold):
        """Initializes cProfile wrapper.

        Args:
            program_name: Name of the program to profile.
            prune_threshold: A threshold for cummulative time fraction to cut
                call tree nodes below.
        """
        self._program_name = program_name
        self._prune_threshold = prune_threshold

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
            'module_name': module_name,
            'lineno': lineno,
            'func_name': func_name,
            'prim_calls': cum_calls,
            'total_calls': num_calls,
            'time_per_call': time_per_call,
            'cum_time': cum_time,
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
        call_tree = self._build_call_tree(root, callees, stats.stats)
        self._prune(call_tree, call_tree['cum_time'])
        return call_tree

    def _prune(self, node, total_cum_time):
        """Prunes call tree nodes below prune threshold."""
        node['children'][:] = [
            child for child in node['children']
            if child['cum_time'] / total_cum_time >= self._prune_threshold]
        for child in node['children']:
            self._prune(child, total_cum_time)

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
            'program_name': self._program_name,
            'run_time': cprofile_stats.total_tt,
            'primitive_calls': cprofile_stats.prim_calls,
            'total_calls': cprofile_stats.total_calls,
            'call_stats': self._transform_stats(cprofile_stats),
            'cutoff': self._prune_threshold
        }
