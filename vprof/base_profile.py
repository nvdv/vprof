"""Base class for a profile wrapper."""
import os
import sys


class Error(Exception):
    """Base exception for current module."""
    pass


class ProfilerRuntimeException(Error):
    """Base exception for all runtime errors during profiling."""
    pass


def get_package_code(package_name, name_is_path=False):
    """Returns package source code.
    Args:
        package_name: Path to package or package name in Python namespace.
        name_is_path: True if package_name variable contains package name in
            Python namespace, False if package name is path to package.
    Returns:
        A dict containing non-compiled and compiled code for package
        specified by package name.
    """
    import importlib
    import pkgutil

    if not name_is_path:
        package = importlib.import_module(package_name)
        package_path = os.path.dirname(package.__file__)
    else:
        package_path = package_name

    all_code = {}
    for fobj, modname, _ in pkgutil.iter_modules(path=[package_path]):
        filename = os.path.join(fobj.path, '%s.py' % modname)
        if os.path.exists(filename):
            with open(filename, 'r') as srcfile:
                src_code = srcfile.read()
                compiled_code = compile(src_code, package_path, 'exec')
                all_code[filename] = src_code, compiled_code
    return all_code


class BaseProfile(object):
    """Base class for a profile wrapper."""

    def __init__(self, program_cmd):
        """Initializes wrapper.

        Args:
            program_cmd: Name and arguments of the program to profile.
        """
        fullcmd = program_cmd.split()
        self._is_package_dir = os.path.isdir(program_cmd)
        self._is_module_file = os.path.isfile(program_cmd)
        self._program_name, self._program_args = fullcmd[0], fullcmd
        self._globs = {
            '__file__': self._program_name,
            '__name__': '__main__',
            '__package__': None,
        }
        program_path = os.path.dirname(self._program_name)
        if sys.path[0] != program_path:
            sys.path.insert(0, program_path)

    def run_as_package_path(self):
        """Runs program as package specified with filesystem path.

        Runs program specified by self._program_name as package specified by
        path in filesystem. Must be overridden in child classes.
        """
        raise NotImplementedError

    def run_as_package_in_namespace(self):
        """Runs program as package in Python namespace.

        Runs program specified by self._program_name as package in Python
        namespace. Must be overridden in child classes.
        """
        raise NotImplementedError

    def run_as_module(self):
        """Runs program as module.

        Runs program specified by self._program_name as Python module.
        Must be overridden in child classes.
        """
        raise NotImplementedError

    def get_run_dispatcher(self):
        """Returns run dispatcher depending on self._program_name value."""
        if self._is_package_dir:
            return self.run_as_package_path
        elif self._is_module_file:
            return self.run_as_module
        return self.run_as_package_in_namespace

    def run(self):
        """Runs profiler and returns collect stats."""
        raise NotImplementedError
