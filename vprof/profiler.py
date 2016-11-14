"""Module for Python profiler wrapper."""
import cProfile
import operator
import os
import pstats
import runpy

from vprof import base_profiler


class Profiler(base_profiler.BaseProfiler):
    """Python profiler wrapper.

    Runs cProfile against specified program and returns obtained stats.
    """

    def run_as_package(self, prof):
        """Runs program as a Python package."""
        prof.enable()
        try:
            runpy.run_path(self._run_object, run_name='__main__')
        except SystemExit:
            pass
        prof.disable()

    def run_as_module(self, prof):
        """Runs program as Python module."""
        try:
            with open(self._run_object, 'rb') as srcfile:
                code = compile(srcfile.read(), self._run_object, 'exec')
            prof.runctx(code, self._globs, None)
        except SystemExit:
            pass

    def run_as_function(self, prof):
        """Runs object as a Python function."""
        prof.enable()
        self._run_object(*self._run_args, **self._run_kwargs)
        prof.disable()

    def _transform_stats(self, prof):
        """Post-processes obtained stats for UI."""
        records = []
        for info, params in prof.stats.items():
            filename, lineno, funcname = info
            cum_calls, num_calls, time_per_call, cum_time, _ = params
            percentage = round(100 * (cum_time / prof.total_tt), 4)
            cum_time = round(cum_time, 4)
            funcname = funcname.replace('<', '[').replace('>', ']')
            filename = filename.replace('<', '[').replace('>', ']')
            short_path = os.path.basename(filename)
            records.append(
                (filename, lineno, funcname, cum_time, percentage, num_calls,
                 cum_calls, time_per_call, short_path))
        return sorted(records, key=operator.itemgetter(4), reverse=True)

    def run(self):
        """Runs cProfile and retunrs obtained stats."""
        prof = cProfile.Profile()
        run_dispatcher = self.get_run_dispatcher()
        run_dispatcher(prof)
        prof_stats = pstats.Stats(prof)
        prof_stats.calc_callees()
        return {
            'objectName': self._object_name,
            'callStats': self._transform_stats(prof_stats),
            'totalTime': prof_stats.total_tt,
            'primitiveCalls': prof_stats.prim_calls,
            'totalCalls': prof_stats.total_calls
        }
