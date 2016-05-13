"""Module for runtime profiling."""
import cProfile
import pstats

from vprof import base_profile


class Error(Exception):
    """Base exception for current module."""
    pass


class RuntimeProfilerRunError(Error, base_profile.ProfilerRuntimeException):
    """Runtime exception for runtime profiler."""
    pass


class RuntimeProfile(base_profile.BaseProfile):
    """CProfile wrapper.

    This class contains all logic related to cProfile run, stats collection
    and processing. All function call info is contained in stats.Pstats, all
    we have to do is to run cProfile and build call tree from resulting
    pstats.Stats.
    """

    def _build_call_tree(self, node, callees, stats, seen=set()):  # pylint: disable=dangerous-default-value
        """Builds call tree from callees tree.

        Args:
            node: Current call tree node.
            callees: Call tree node stats.
            stats: Profile stats.
            seen: Set to track previously seen nodes to handle recursion.
        Returns:
            A dict representing call tree with all necessary parameters.
        """
        module_name, lineno, func_name = node
        cum_calls, num_calls, time_per_call, cum_time = stats
        seen.add(node + stats)
        return {
            'moduleName': module_name,
            'lineno': lineno,
            'funcName': func_name,
            'primCalls': cum_calls,
            'totalCalls': num_calls,
            'timePerCall': time_per_call,
            'cumTime': cum_time,
            'children': [
                self._build_call_tree(child, callees, child_stats)
                for child, child_stats in callees[node].items()
                if child + child_stats not in seen]
        }

    def _transform_stats(self, stats):
        """Converts stats from pststs.Stats to nested dict."""

        def _statcmp(stat):
            """Comparator by cumulative time."""
            _, params = stat
            return params[3]

        stats.calc_callees()
        root, _ = max(stats.stats.items(), key=_statcmp)
        return self._build_call_tree(
            root, stats.all_callees, stats.stats[root][:-1])

    def run_as_package_path(self, prof):
        """Runs program as package specified with file path."""
        import runpy
        prof.enable()
        try:
            runpy.run_path(self._run_object, run_name='__main__')
        except ImportError:
            raise RuntimeProfilerRunError(
                'Unable to run package %s' % self._run_object)
        except SystemExit:
            pass
        prof.disable()

    def run_as_module(self, prof):
        """Runs program as module."""
        try:
            with open(self._run_object, 'rb') as srcfile:
                code = compile(srcfile.read(), self._run_object, 'exec')
            prof.runctx(code, self._globs, None)
        except SystemExit:
            pass

    def run_as_package_in_namespace(self, prof):
        """Runs program as package in Python namespace."""
        import runpy
        prof.enable()
        try:
            runpy.run_module(self._run_object, run_name='__main__')
        except ImportError:
            raise RuntimeProfilerRunError(
                'Unable to run package %s' % self._run_object)
        except SystemExit:
            pass
        finally:
            prof.disable()

    def run_as_function(self, prof):
        """Runs object as function."""
        prof.enable()
        self._run_object(*self._run_args, **self._run_kwargs)
        prof.disable()

    def run(self):
        """Collects CProfile stats for specified Python program."""
        prof = cProfile.Profile()
        run_dispatcher = self.get_run_dispatcher()
        run_dispatcher(prof)
        cprofile_stats = pstats.Stats(prof)
        return {
            'objectName': self._object_name,  # Set on run dispatching.
            'runTime': cprofile_stats.total_tt,
            'primitiveCalls': cprofile_stats.prim_calls,
            'totalCalls': cprofile_stats.total_calls,
            'callStats': self._transform_stats(cprofile_stats)
        }
