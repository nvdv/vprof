"""Base class for a profile wrapper."""
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
        program_path = os.path.dirname(self._program_name)
        if sys.path[0] != program_path:
            sys.path.insert(0, program_path)

    def run(self):
        """Runs profiler and returns collect stats."""
        raise NotImplementedError
