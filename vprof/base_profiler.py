"""Base class for a profile wrapper."""
import multiprocessing
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
    """Hashes name and trims resulting hash."""
    return zlib.adler32(name.encode('utf-8'))


class ProcessWithException(multiprocessing.Process):
    """Process subclass that propagates exceptions to parent process."""

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.parent_conn, self.child_conn = multiprocessing.Pipe()

    def run(self):
        try:
            super(self.__class__, self).run()
            self.child_conn.send(None)
        except Exception as exc:  # pylint: disable=broad-except
            self.child_conn.send(exc)

    @property
    def exception(self):
        """Returns exception from child process."""
        return self.parent_conn.recv()


def run_in_another_process(func):
    """Runs wrapped function in separate process.

    Function arguments and output should be serializable.
    """
    def multiprocessing_wrapper(*args, **kwargs):
        """Wraps function to be executed in separate process."""

        def remote_wrapper(manager_dict):  # pylint: disable=missing-docstring
            output_dict = func(*args, **kwargs)
            manager_dict.update(output_dict)

        manager = multiprocessing.Manager()
        manager_dict = manager.dict()
        process = ProcessWithException(
            target=remote_wrapper, args=(manager_dict,))
        process.start()
        process.join()
        exc = process.exception
        if exc:
            raise exc
        return manager_dict._getvalue()  # pylint: disable=protected-access
    return multiprocessing_wrapper


class BaseProfiler(object):
    """Base class for a profile wrapper."""

    def __init__(self, run_object):
        """Initializes wrapper.

        Args:
            run_object: object that will be run under profiler.
        """
        self._set_run_object_type(run_object)
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

    def _set_run_object_type(self, run_object):
        """Sets type flags depending on run_object value."""
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

    def _replace_sysargs(self):
        """Replaces sys.argv with proper args to pass to script."""
        if self._run_args:
            sys.argv[:] = [self._run_object] + self._run_args.split()
        else:
            sys.argv[:] = [self._run_object]

    def profile_package(self):
        """Profiles package specified by filesystem path.

        Runs object specified by self._run_object as package specified by
        path in filesystem. Must be overridden in child classes.
        """
        raise NotImplementedError

    def profile_module(self):
        """Profiles module.

        Runs object specified by self._run_object as Python module.
        Must be overridden in child classes.
        """
        raise NotImplementedError

    def profile_function(self):
        """Profiles function.

        Runs object specified by self._run_object as Python function with args.
        Must be overridden in child classes.
        """
        raise NotImplementedError

    def _get_dispatcher(self):
        """Returns dispatcher depending on self._run_object value."""
        if self._is_run_obj_function:
            self._object_name = '%s (function)' % self._run_object.__name__
            return self.profile_function
        elif self._is_run_obj_package:
            self._object_name = '%s (package)' % self._run_object
            return self.profile_package
        self._object_name = '%s (module)' % self._run_object
        return self.profile_module

    def run(self):
        """Runs profiler and returns collected stats."""
        dispatcher = self._get_dispatcher()
        return dispatcher()
