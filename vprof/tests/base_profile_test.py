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

    @mock.patch('os.path.isdir')
    @mock.patch('os.path.isfile')
    def testInit(self, isfile_mock, isdir_mock):
        isfile_mock.return_value, isdir_mock.return_value = True, False
        program_cmd = 'foo.py --bar --baz'
        self._profile.__init__(program_cmd)
        self.assertEqual(self._profile._program_name, 'foo.py')
        self.assertEqual(self._profile._program_args, ['foo.py', '--bar', '--baz'])
        self.assertDictEqual(self._profile._globs, {
            '__file__': 'foo.py',
            '__name__': '__main__',
            '__package__': None
        })
        self.assertFalse(self._profile._is_package_dir)
        self.assertTrue(self._profile._is_module_file)

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

    def testGetRunDispatcher(self):
        self._profile._is_package_dir = True
        self.assertEqual(
            self._profile.get_run_dispatcher(),
            self._profile.run_as_package_path)

        self._profile._is_package_dir = False
        self._profile._is_module_file = True
        self.assertEqual(
            self._profile.get_run_dispatcher(),
            self._profile.run_as_module)

        self._profile._is_module_file = False
        self.assertEqual(
            self._profile.get_run_dispatcher(),
            self._profile.run_as_package_in_namespace)
