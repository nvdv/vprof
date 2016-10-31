"""Module for Python profiler wrapper."""
import cProfile
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

    def _transform_stats(self, stats):
        """Processes profiler stats."""
        result = []
        for info, params in stats.items():
            modname, funcname, lineno = info
            cum_calls, num_calls, time_per_call, cum_time, callers = params
            result.append(info)
        return result

    def run(self):
        """Collects CProfile stats for specified Python program."""
        prof = cProfile.Profile()
        run_dispatcher = self.get_run_dispatcher()
        run_dispatcher(prof)
        prof_stats = pstats.Stats(prof)
        prof_stats.calc_callees()
        return {
            'objectName': self._object_name,
            'callStats': self._transform_stats(prof_stats.stats)
        }
