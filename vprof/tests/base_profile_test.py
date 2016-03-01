import unittest

from vprof import base_profile

# For Python 2 and Python 3 compatibility.
try:
    import mock
except ImportError:
    from unittest import mock


class BaseProfileUnittest(unittest.TestCase):
    def setUp(self):
        self._profile = object.__new__(base_profile.BaseProfile)

    def testInit(self):
        program_cmd = 'foo.py --bar --baz'
        self._profile.__init__(program_cmd)
        self.assertEqual(self._profile._program_name, 'foo.py')
        self.assertEqual(self._profile._program_args, ['foo.py', '--bar', '--baz'])
        self.assertDictEqual(self._profile._globs, {
            '__file__': 'foo.py',
            '__name__': '__main__',
            '__package__': None
        })

    def testRun(self):
        with self.assertRaises(NotImplementedError):
            self._profile.run()
