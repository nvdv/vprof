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

    def testCollectStats(self):
        result = {'foo': 'bar', 'baz': 'mno'}
        self._profile._program_name = 'foo.py'
        self._profile._program_args = ['--foo', '--bar']
        self._profile.run_profiler = mock.MagicMock(return_value=result)
        run_stats = {}
        self._profile.collect_stats(run_stats)
        self.assertDictEqual(run_stats, result)
