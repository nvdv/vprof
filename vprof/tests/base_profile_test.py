import unittest

from vprof import base_profile

# For Python 2 and Python 3 compatibility.
try:
    import mock
except ImportError:
    from unittest import mock


# TODO(nvdv): Write unittest for this function.
class GetPackageCodeUnittest(unittest.TestCase):
    def testGetPackageCode(self):
        pass


class BaseProfileUnittest(unittest.TestCase):
    def setUp(self):
        self._profile = object.__new__(base_profile.BaseProfile)

    def testInit_RunObjFunction(self):
        _func = lambda foo: foo
        self._profile.__init__((_func, ('bar'), {'bar': 'baz'}))
        self.assertEqual(self._profile._run_object, _func)
        self.assertEqual(self._profile._run_args, ('bar'))
        self.assertDictEqual(self._profile._run_kwargs, {'bar': 'baz'})

    @mock.patch('os.path.isdir')
    def testInit_RunObjPackagePath(self, isdir_mock):
        isdir_mock.return_value = True
        self._profile.__init__('test/test_pkg')
        self.assertEqual(self._profile._run_object, 'test/test_pkg')
        self.assertEqual(self._profile._run_args, '')
        self._profile.__init__('test/test_pkg --help')
        self.assertEqual(self._profile._run_object, 'test/test_pkg')
        self.assertEqual(self._profile._run_args, '--help')

    @mock.patch('os.path.isdir')
    @mock.patch('os.path.isfile')
    def testInit_RunObjModule(self, isfile_mock, isdir_mock):
        isfile_mock.return_value, isdir_mock.return_value = True, False
        self._profile.__init__('foo.py')
        self.assertEqual(self._profile._run_object, 'foo.py')
        self.assertEqual(self._profile._run_args, '')
        self._profile.__init__('foo.py --bar --baz')
        self.assertEqual(self._profile._run_object, 'foo.py')
        self.assertEqual(self._profile._run_args, '--bar --baz')
        self.assertDictEqual(self._profile._globs, {
            '__file__': 'foo.py',
            '__name__': '__main__',
            '__package__': None
        })

    @mock.patch('os.path.isdir')
    @mock.patch('os.path.isfile')
    def testInit_RunObjImportedPackage(self, isfile_mock, isdir_mock):
        isfile_mock.return_value, isdir_mock.return_value = False, False
        self._profile.__init__('test_pkg')
        self.assertEqual(self._profile._run_object, 'test_pkg')
        self.assertEqual(self._profile._run_args, '')
        self._profile.__init__('test_pkg --bar --baz')
        self.assertEqual(self._profile._run_object, 'test_pkg')
        self.assertEqual(self._profile._run_args, '--bar --baz')

    def testRun(self):
        with self.assertRaises(NotImplementedError):
            self._profile.run()

    def testRunAsModule(self):
        with self.assertRaises(NotImplementedError):
            self._profile.run_as_module()

    def testRunAsPackageInNamespace(self):
        with self.assertRaises(NotImplementedError):
            self._profile.run_as_package_in_namespace()

    def testRunAsPackagePath(self):
        with self.assertRaises(NotImplementedError):
            self._profile.run_as_package_path()

    def testRunAsFunction(self):
        with self.assertRaises(NotImplementedError):
            self._profile.run_as_function()

    def testGetRunDispatcher(self):
        self._profile._is_run_obj_function = True
        self.assertEqual(
            self._profile.get_run_dispatcher(),
            self._profile.run_as_function)

        self._profile._is_run_obj_function = False
        self._profile._is_run_obj_package_dir = True
        self.assertEqual(
            self._profile.get_run_dispatcher(),
            self._profile.run_as_package_path)

        self._profile._is_run_obj_package_dir = False
        self._profile._is_run_obj_module = True
        self.assertEqual(
            self._profile.get_run_dispatcher(),
            self._profile.run_as_module)

        self._profile._is_run_obj_module = False
        self.assertEqual(
            self._profile.get_run_dispatcher(),
            self._profile.run_as_package_in_namespace)
