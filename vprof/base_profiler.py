"""Base class for a profile wrapper."""
import inspect
import multiprocessing
import os
import pkgutil
import sys
import zlib


def get_pkg_module_names(package_path):
    """Returns module filenames from package.

    Args:
        package_path: Path to Python package.
    Returns:
        A set of module filenames.
    """
    module_names = set()
    for fobj, modname, _ in pkgutil.iter_modules(path=[package_path]):
        filename = os.path.join(fobj.path, '%s.py' % modname)
        if os.path.exists(filename):
            module_names.add(os.path.abspath(filename))
    return module_names


def hash_name(name):
    """Computes hash of the name."""
    return zlib.adler32(name.encode('utf-8'))


class ProcessWithException(multiprocessing.Process):
    """Process subclass that propagates exceptions to parent process.

    Also handles sending function output to parent process.
    Args:
        parent_conn: Parent end of multiprocessing.Pipe.
        child_conn: Child end of multiprocessing.Pipe.
        result: Result of the child process.
    """

    def __init__(self, result, *args, **kwargs):
        super(ProcessWithException, self).__init__(*args, **kwargs)
        self.parent_conn, self.child_conn = multiprocessing.Pipe()
        self.result = result

    def run(self):
        try:
            self.result.update(
                self._target(*self._args, **self._kwargs))
            self.child_conn.send(None)
        except Exception as exc:  # pylint: disable=broad-except
            self.child_conn.send(exc)

    @property
    def exception(self):
        """Returns exception from child process."""
        return self.parent_conn.recv()

    @property
    def output(self):
        """Returns target function output."""
        return self.result._getvalue()  # pylint: disable=protected-access


def run_in_separate_process(func, *args, **kwargs):
    """Runs function in separate process.

    This function is used instead of a decorator, since Python multiprocessing
    module can't serialize decorated function on all platforms.
    """
    manager = multiprocessing.Manager()
    manager_dict = manager.dict()
    process = ProcessWithException(
        manager_dict, target=func, args=args, kwargs=kwargs)
    process.start()
    process.join()
    exc = process.exception
    if exc:
        raise exc
    return process.output


class BaseProfiler(object):
    """Base class for a profiler."""

    def __init__(self, run_object):
        """Initializes profiler.

        Args:
            run_object: object to be profiled.
        """
        run_obj_type = self.get_run_object_type(run_object)
        if run_obj_type == 'module':
            self.init_module(run_object)
        elif run_obj_type == 'package':
            self.init_package(run_object)
        else:
            self.init_function(run_object)

    @staticmethod
    def get_run_object_type(run_object):
        """Determines run object type."""
        if isinstance(run_object, tuple):
            return 'function'
        run_object, _, _ = run_object.partition(' ')
        if os.path.isdir(run_object):
            return 'package'
        return 'module'

    def init_module(self, run_object):
        """Initializes profiler with a module."""
        self.profile = self.profile_module
        self._run_object, _, self._run_args = run_object.partition(' ')
        self._object_name = '%s (module)' % self._run_object
        self._globs = {
            '__file__': self._run_object,
            '__name__': '__main__',
            '__package__': None,
        }
        program_path = os.path.dirname(self._run_object)
        if sys.path[0] != program_path:
            sys.path.insert(0, program_path)
        self._replace_sysargs()

    def init_package(self, run_object):
        """Initializes profiler with a package."""
        self.profile = self.profile_package
        self._run_object, _, self._run_args = run_object.partition(' ')
        self._object_name = '%s (package)' % self._run_object
        self._replace_sysargs()

    def init_function(self, run_object):
        """Initializes profiler with a function."""
        self.profile = self.profile_function
        self._run_object, self._run_args, self._run_kwargs = run_object
        filename = inspect.getsourcefile(self._run_object)
        self._object_name = '%s @ %s (function)' % (
            self._run_object.__name__, filename)

    def _replace_sysargs(self):
        """Replaces sys.argv with proper args to pass to script."""
        sys.argv[:] = [self._run_object]
        if self._run_args:
            sys.argv += self._run_args.split()

    def profile_package(self):
        """Profiles package specified by filesystem path.

        Runs object self._run_object as a package specified by filesystem path.
        Must be overridden.
        """
        raise NotImplementedError

    def profile_module(self):
        """Profiles module.

        Runs object self._run_object as a Python module.
        Must be overridden.
        """
        raise NotImplementedError

    def profile_function(self):
        """Profiles function.

        Runs object self._run_object as a Python function.
        Must be overridden.
        """
        raise NotImplementedError

    def run(self):
        """Runs profiler and returns collected stats."""
        return self.profile()
