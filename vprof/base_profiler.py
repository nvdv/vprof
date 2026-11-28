"""Base class of a profiler wrapper."""
from collections.abc import Callable
import inspect
import multiprocessing
import os
import pkgutil
import sys
from typing import Any
import zlib


def get_pkg_module_names(package_path: str) -> set[str]:
    """Returns module filenames from package.

    Args:
        package_path: Path to Python package.
    Returns:
        A set of module filenames.
    """
    module_names = set()
    for fobj, modname, _ in pkgutil.iter_modules(path=[package_path]):
        fobj_path = getattr(fobj, 'path', package_path)
        filename = os.path.join(fobj_path, f'{modname}.py')
        if os.path.exists(filename):
            module_names.add(os.path.abspath(filename))
    return module_names


def hash_name(name: str) -> int:
    """Computes hash of the name."""
    return zlib.adler32(name.encode('utf-8'))


class ProcessWithException(multiprocessing.Process):
    """Process subclass that propagates exceptions to parent process.

    Also handles sending function output to parent process.
    Args:
        parent_conn: Parent end of multiprocessing.Pipe.
        child_conn: Child end of multiprocessing.Pipe.
    """

    _target: Callable[..., Any]
    _args: tuple[Any, ...]
    _kwargs: dict[str, Any]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.parent_conn, self.child_conn = multiprocessing.Pipe()

    def run(self) -> None:
        self.parent_conn.close()
        try:
            output = self._target(*self._args, **self._kwargs)
            self.child_conn.send((output, None))
        except Exception as exc:  # pylint: disable=broad-except
            self.child_conn.send((None, exc))
        finally:
            self.child_conn.close()

    def recv_result(self) -> tuple[Any, Exception | None]:
        """Returns (output, exception) tuple from child process."""
        try:
            return self.parent_conn.recv()
        finally:
            self.parent_conn.close()


def run_in_separate_process(
        func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Runs function in separate process.

    This function is used instead of a decorator, since Python multiprocessing
    module can't serialize decorated function on all platforms.
    """
    process = ProcessWithException(target=func, args=args, kwargs=kwargs)
    process.start()
    process.child_conn.close()
    try:
        output, exc = process.recv_result()
    finally:
        process.join()
    if exc:
        raise exc
    return output


class BaseProfiler:
    """Base class for a profiler wrapper."""

    _run_object: Any
    _run_args: Any
    _run_kwargs: dict[str, Any]
    _object_name: str
    _globs: dict[str, Any]
    profile: Callable[[], Any]

    def __init__(self, run_object: Any) -> None:
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
    def get_run_object_type(run_object: Any) -> str:
        """Determines run object type."""
        if isinstance(run_object, tuple):
            return 'function'
        run_object, _, _ = run_object.partition(' ')
        if os.path.isdir(run_object):
            return 'package'
        return 'module'

    def init_module(self, run_object: str) -> None:
        """Initializes profiler with a module."""
        self.profile = self.profile_module
        self._run_object, _, self._run_args = run_object.partition(' ')
        self._object_name = f'{self._run_object} (module)'
        self._globs = {
            '__file__': self._run_object,
            '__name__': '__main__',
            '__package__': None,
        }
        program_path = os.path.dirname(self._run_object)
        if sys.path[0] != program_path:
            sys.path.insert(0, program_path)
        self._replace_sysargs()

    def init_package(self, run_object: str) -> None:
        """Initializes profiler with a package."""
        self.profile = self.profile_package
        self._run_object, _, self._run_args = run_object.partition(' ')
        self._object_name = f'{self._run_object} (package)'
        self._replace_sysargs()

    def init_function(
            self,
            run_object: tuple[Callable[..., Any], Any, dict[str, Any]]
    ) -> None:
        """Initializes profiler with a function."""
        self.profile = self.profile_function
        self._run_object, self._run_args, self._run_kwargs = run_object
        filename = inspect.getsourcefile(self._run_object)
        self._object_name = (
            f'{self._run_object.__name__} @ {filename} (function)')

    def _replace_sysargs(self) -> None:
        """Replaces sys.argv with proper args to pass to script."""
        sys.argv[:] = [self._run_object]
        if self._run_args:
            sys.argv += self._run_args.split()

    def profile_package(self) -> Any:
        """Profiles package specified by filesystem path.

        Runs object self._run_object as a package specified by filesystem path.
        Must be overridden.
        """
        raise NotImplementedError

    def profile_module(self) -> Any:
        """Profiles a module.

        Runs object self._run_object as a Python module.
        Must be overridden.
        """
        raise NotImplementedError

    def profile_function(self) -> Any:
        """Profiles a function.

        Runs object self._run_object as a Python function.
        Must be overridden.
        """
        raise NotImplementedError

    def run(self) -> dict[str, Any]:
        """Runs a profiler and returns collected stats."""
        return self.profile()
