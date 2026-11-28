"""Unit tests for runner module."""
import unittest
from unittest import mock

from vprof import runner


class RunnerUnittest(unittest.TestCase):

    @mock.patch('vprof.runner.run_profilers')
    @mock.patch('gzip.compress')
    @mock.patch('urllib.request.urlopen')
    def testRun_CheckResult(self, unused_urlopen_mock,
                            unused_compress_mock, run_mock):
        run_mock.return_value = {
            'h': {'result': 'foobar', 'total': 200},
            'p': {'result': 'foobar', 'total': 500}
        }
        def func(x, y):
            return x + y
        result = runner.run(func, 'hp', args=('foo', 'bar'))
        self.assertEqual(result, 'foobar')

    @mock.patch('vprof.runner.run_profilers')
    @mock.patch('gzip.compress')
    @mock.patch('urllib.request.urlopen')
    @mock.patch('json.dumps')
    def testRun_CheckStats(self, json_mock, unused_urlopen_mock,
                           unused_compress_mock, run_mock):
        run_mock.return_value = {
            'h': {'result': 'foobar', 'total': 200},
            'p': {'result': 'foobar', 'total': 500}
        }
        def func(x, y):
            return x + y
        runner.run(func, 'hp', args=('foo', 'bar'))
        json_mock.assert_called_with({
            'h': {'total': 200},
            'p': {'total': 500}
        })

    def testRunProfilers_AmbiguousConfig(self):
        with self.assertRaises(runner.AmbiguousConfigurationError):
            runner.run_profilers('dummy.py', 'mm')
        with self.assertRaises(runner.AmbiguousConfigurationError):
            runner.run_profilers('dummy.py', 'chc')

    def testRunProfilers_BadOption(self):
        with self.assertRaises(runner.BadOptionError):
            runner.run_profilers('dummy.py', 'z')
        with self.assertRaises(runner.BadOptionError):
            runner.run_profilers('dummy.py', 'mx')

    def testRunProfilers_RunsRequestedProfilers(self):
        prof_m = mock.MagicMock()
        prof_m.return_value.run.return_value = {'m_stat': 1}
        prof_h = mock.MagicMock()
        prof_h.return_value.run.return_value = {'h_stat': 2}
        with mock.patch.object(
                runner, '_PROFILERS', (('m', prof_m), ('h', prof_h))):
            stats = runner.run_profilers('dummy.py', 'hm')
        self.assertEqual(list(stats.keys()), ['m', 'h'])
        self.assertEqual(stats, {'m': {'m_stat': 1}, 'h': {'h_stat': 2}})
