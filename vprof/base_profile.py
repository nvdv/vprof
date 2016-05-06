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

    def __init__(self, run_object):
        """Initializes wrapper.

        Args:
            run_object: object that will be run under profiler.
        """
        self._is_run_obj_function, self._is_run_obj_package_dir = False, False
        self._is_run_obj_module, self._is_run_obj_imported_pkg = False, False
        if isinstance(run_object, tuple):
            self._run_object, self._run_args, self._run_kwargs = run_object
            self._is_run_obj_function = True
        else:
            self._run_object, _, self._run_args = run_object.partition(' ')
            if os.path.isdir(self._run_object):
                self._is_run_obj_package_dir = True
            elif os.path.isfile(self._run_object):
                self._is_run_obj_module = True
            else:
                self._is_run_obj_imported_pkg = True

        if self._is_run_obj_module:
            self._globs = {
                '__file__': self._run_object,
                '__name__': '__main__',
                '__package__': None,
            }
            program_path = os.path.dirname(self._run_object)
            if sys.path[0] != program_path:
                sys.path.insert(0, program_path)
        self._replace_sysargs()
        self._object_name = None

    def _replace_sysargs(self):
        """Replaces sys.argv with proper args to pass to script."""
        if self._run_args:
            sys.argv[:] = [self._run_object, self._run_args]
        else:
            sys.argv[:] = [self._run_object]

    def run_as_package_path(self):
        """Runs object as package specified with filesystem path.

        Runs object specified by self._run_object as package specified by
        path in filesystem. Must be overridden in child classes.
        """
        raise NotImplementedError

    def run_as_package_in_namespace(self):
        """Runs object as package in Python namespace.

        Runs object specified by self._run_object as package in Python
        namespace. Must be overridden in child classes.
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
        elif self._is_run_obj_package_dir:
            self._object_name = '%s (package)' % self._run_object
            return self.run_as_package_path
        elif self._is_run_obj_module:
            self._object_name = '%s (module)' % self._run_object
            return self.run_as_module
        self._object_name = '%s (package)' % self._run_object
        return self.run_as_package_in_namespace

    def run(self):
        """Runs profiler and returns collect stats."""
        raise NotImplementedError
