"""Module for runtime profiling."""
import cProfile
import pstats

from collections import defaultdict
from vprof import base_profile


class RuntimeProfile(base_profile.BaseProfile):
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

    def _build_call_tree(self, node, callees, stats, seen=set()):  # pylint: disable=dangerous-default-value
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

    def run(self):
        """Collects CProfile stats for specified Python program."""
        prof = cProfile.Profile()
        try:
            with open(self._program_name, 'rb') as srcfile:
                code = compile(srcfile.read(), self._program_name, 'exec')
            prof.runctx(code, self._globs, None)
        except SystemExit:
            pass
        prof.create_stats()
        cprofile_stats = pstats.Stats(prof)
        return {
            'programName': self._program_name,
            'runTime': cprofile_stats.total_tt,
            'primitiveCalls': cprofile_stats.prim_calls,
            'totalCalls': cprofile_stats.total_calls,
            'callStats': self._transform_stats(cprofile_stats)
        }
