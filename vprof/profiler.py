"""Module for Python profiler wrapper."""
import cProfile
import operator
import pstats
import runpy

from vprof import base_profile


class Profiler(base_profile.BaseProfile):
    """Python profiler wrapper.

    Runs profiler and post-processes obtained stats.
    """

    def run_as_package(self, prof):
        """Runs program as package."""
        prof.enable()
        try:
            runpy.run_path(self._run_object, run_name='__main__')
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

    def run_as_function(self, prof):
        """Runs object as function."""
        prof.enable()
        self._run_object(*self._run_args, **self._run_kwargs)
        prof.disable()

    def _transform_stats(self, prof):
        """Processes profiler stats."""
        records = []
        for info, params in prof.stats.items():
            filename, lineno, funcname = info
            cum_calls, num_calls, time_per_call, cum_time, callers = params
            percentage = round(100 * (cum_time / prof.total_tt), 4)
            records.append(
                (filename, lineno, funcname, cum_time, percentage, num_calls,
                 cum_calls, time_per_call))
        return sorted(records, key=operator.itemgetter(4), reverse=True)

    def run(self):
        """Collects CProfile stats for specified Python program."""
        prof = cProfile.Profile()
        run_dispatcher = self.get_run_dispatcher()
        run_dispatcher(prof)
        prof_stats = pstats.Stats(prof)
        prof_stats.calc_callees()
        return {
            'objectName': self._object_name,
            'callStats': self._transform_stats(prof_stats),
            'totalTime': prof_stats.total_tt
        }
