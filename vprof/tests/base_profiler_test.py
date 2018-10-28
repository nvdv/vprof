# pylint: disable=protected-access, missing-docstring
import sys
import unittest

from vprof import base_profiler
from unittest import mock


class GetPkgModuleNamesUnittest(unittest.TestCase):

    @mock.patch('pkgutil.iter_modules')
    @mock.patch('os.path.exists')
    def testGetPackageCode(self, exists_mock, iter_modules_mock):
        package_path = mock.MagicMock()
        _ = mock.MagicMock()
        modname1, modname2 = 'module1', 'module2'
        fobj1, fobj2 = mock.MagicMock(), mock.MagicMock()
        fobj1.path = '/path/to/module'
        fobj2.path = '/path/to/module'
        iter_modules_mock.return_value = [
            (fobj1, modname1, _), (fobj2, modname2, _)]
        exists_mock.return_value = True
        result = base_profiler.get_pkg_module_names(package_path)
        self.assertEqual(
            result, {'/path/to/module/module1.py',
                     '/path/to/module/module2.py'})


class BaseProfileUnittest(unittest.TestCase):
    def setUp(self):
        self.profiler = object.__new__(base_profiler.BaseProfiler)

    def testGetRunObjectType_Function(self):
        func = (lambda x: x, ('foo',), ('bar',))
        self.assertEqual(
            self.profiler.get_run_object_type(func), 'function')

    @mock.patch('os.path.isdir')
    def testGetRunObjectType_Module(self, isdir_mock):
        isdir_mock.return_value = False
        modpath = 'foo.py -v'
        self.assertEqual(
            self.profiler.get_run_object_type(modpath), 'module')

    @mock.patch('os.path.isdir')
    def testGetRunObjectType_Package(self, isdir_mock):
        isdir_mock.return_value = True
        pkgpath = 'foo'
        self.assertEqual(
            self.profiler.get_run_object_type(pkgpath), 'package')

    def testInitFunction(self):
        _func = lambda foo: foo
        self.profiler.__init__((_func, ('bar'), {'bar': 'baz'}))
        self.assertEqual(self.profiler._run_object, _func)
        self.assertEqual(self.profiler._run_args, ('bar'))
        self.assertDictEqual(self.profiler._run_kwargs, {'bar': 'baz'})

    @mock.patch('os.path.isdir')
    def testInitPackage(self, isdir_mock):
        isdir_mock.return_value = True
        self.profiler.__init__('test/test_pkg')
        self.assertEqual(self.profiler._run_object, 'test/test_pkg')
        self.assertEqual(self.profiler._run_args, '')
        self.profiler.__init__('test/test_pkg --help')
        self.assertEqual(self.profiler._run_object, 'test/test_pkg')
        self.assertEqual(self.profiler._run_args, '--help')

    @mock.patch('os.path.isdir')
    def testInitModule(self, isdir_mock):
        isdir_mock.return_value = False
        self.profiler.__init__('foo.py')
        self.assertEqual(self.profiler._run_object, 'foo.py')
        self.assertEqual(self.profiler._run_args, '')
        self.profiler.__init__('foo.py --bar --baz')
        self.assertEqual(self.profiler._run_object, 'foo.py')
        self.assertEqual(self.profiler._run_args, '--bar --baz')
        self.assertDictEqual(self.profiler._globs, {
            '__file__': 'foo.py',
            '__name__': '__main__',
            '__package__': None
        })

    def testRun(self):
        self.profiler.profile = lambda: 1
        self.assertEqual(self.profiler.run(), 1)

    def testRunAsModule(self):
        with self.assertRaises(NotImplementedError):
            self.profiler.profile_module()

    def testRunAsPackage(self):
        with self.assertRaises(NotImplementedError):
            self.profiler.profile_package()

    def testRunAsFunction(self):
        with self.assertRaises(NotImplementedError):
            self.profiler.profile_function()

    def testReplaceSysargs(self):
        self.profiler._run_object = mock.MagicMock()
        self.profiler._run_args = ''
        with mock.patch.object(sys, 'argv', []):
            self.profiler._replace_sysargs()
            self.assertEqual(sys.argv, [self.profiler._run_object])

        self.profiler._run_args = '-s foo -a bar -e baz'
        with mock.patch.object(sys, 'argv', []):
            self.profiler._replace_sysargs()
            self.assertEqual(
                sys.argv,
                [self.profiler._run_object,
                 '-s', 'foo', '-a', 'bar', '-e', 'baz']
            )

# pylint: enable=protected-access, missing-docstring
