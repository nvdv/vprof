"""Base class for a profile wrapper."""
import multiprocessing
import os
import sys


class BaseProfile(object):
    """Base class for profile wrapper."""

    def __init__(self, program_cmd):
        """Initializes wrapper.

        Args:
            program_cmd: Name and arguments of the program to profile.
        """
        fullcmd = program_cmd.split()
        self._program_name, self._program_args = fullcmd[0], fullcmd
        self._globs = {
            '__file__': self._program_name,
            '__name__': '__main__',
            '__package__': None,
        }

    def collect_stats(self, run_stats):
        """Collects program stats and inserts them into run_stats dict."""
        sys.path.insert(0, os.path.dirname(self._program_name))
        sys.argv[:] = self._program_args
        stats = self.run_profiler()  # pylint: disable=no-member
        run_stats.update(stats)

    def run(self):
        """Runs profile and returns collected stats.

        Runs profiler in separate process to ensure correct stats collection.
        """
        result_stats = multiprocessing.Manager().dict()
        subprocess = multiprocessing.Process(
            target=self.collect_stats, args=(result_stats,))
        subprocess.start()
        subprocess.join()
        return dict(result_stats)
