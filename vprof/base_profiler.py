"""Base class for a profile wrapper."""
import os
import sys
import zlib


def get_package_code(package_path):
    """Returns package source code.

    Args:
        package_path: Path to Python package.
    Returns:
        A dict containing non-compiled and compiled code for package
        specified by package name.
    """
    import pkgutil

    all_code = {}
    for fobj, modname, _ in pkgutil.iter_modules(path=[package_path]):
        filename = os.path.join(fobj.path, '%s.py' % modname)
        if os.path.exists(filename):
            with open(filename, 'r') as srcfile:
                src_code = srcfile.read()
                compiled_code = compile(src_code, package_path, 'exec')
                all_code[filename] = src_code, compiled_code
    return all_code


def hash_name(name):
    """Hash name and trim resulting hash."""
    return zlib.adler32(name.encode('utf-8'))


class BaseProfiler(object):
    """Base class for a profile wrapper."""

    def __init__(self, run_object):
        """Initializes wrapper.

        Args:
            run_object: object that will be run under profiler.
        """
        self._is_run_obj_function, self._is_run_obj_package = False, False
        self._is_run_obj_module = False
        if isinstance(run_object, tuple):
            self._run_object, self._run_args, self._run_kwargs = run_object
            self._is_run_obj_function = True
        else:
            self._run_object, _, self._run_args = run_object.partition(' ')
            if os.path.isdir(self._run_object):
                self._is_run_obj_package = True
            elif os.path.isfile(self._run_object):
                self._is_run_obj_module = True

        if self._is_run_obj_module:
            self._globs = {
                '__file__': self._run_object,
                '__name__': '__main__',
                '__package__': None,
            }
            program_path = os.path.dirname(self._run_object)
            if sys.path[0] != program_path:
                sys.path.insert(0, program_path)
        if not self._is_run_obj_function:
            self._replace_sysargs()
        self._object_name = None

    def _replace_sysargs(self):
        """Replaces sys.argv with proper args to pass to script."""
        if self._run_args:
            sys.argv[:] = [self._run_object] + self._run_args.split()
        else:
            sys.argv[:] = [self._run_object]

    def run_as_package(self):
        """Runs object as package specified by filesystem path.

        Runs object specified by self._run_object as package specified by
        path in filesystem. Must be overridden in child classes.
        """
        raise NotImplementedError

    def run_as_module(self):
        """Runs object as module.

        Runs object specified by self._run_object as Python module.
        Must be overridden in child classes.
        """
        raise NotImplementedError

    def run_as_function(self):
        """Runs object as function.

        Runs object specified by self._run_object as Python function with args.
        Must be overridden in child classes.
        """
        raise NotImplementedError

    def get_run_dispatcher(self):
        """Returns run dispatcher depending on self._run_object value."""
        if self._is_run_obj_function:
            self._object_name = '%s (function)' % self._run_object.__name__
            return self.run_as_function
        elif self._is_run_obj_package:
            self._object_name = '%s (package)' % self._run_object
            return self.run_as_package
        self._object_name = '%s (module)' % self._run_object
        return self.run_as_module

    def run(self):
        """Runs profiler and returns collect stats."""
        raise NotImplementedError
