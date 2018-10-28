# pylint: disable=protected-access, missing-docstring
import unittest

from vprof import runner
from unittest import mock


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
        func = lambda x, y: x + y
        result = runner.run(func, 'hp', args=('foo', 'bar'))
        self.assertEqual(result, 'foobar')

    @mock.patch('vprof.runner.run_profilers')
    @mock.patch('gzip.compress')
    @mock.patch('urllib.request.urlopen')
    @mock.patch('json.dumps')
    def testRun_CheckStats(self, json_mock, unused_urlopen_mock, # pylint: disable=no-self-use
                           unused_compress_mock, run_mock):
        run_mock.return_value = {
            'h': {'result': 'foobar', 'total': 200},
            'p': {'result': 'foobar', 'total': 500}
        }
        func = lambda x, y: x + y
        runner.run(func, 'hp', args=('foo', 'bar'))
        json_mock.assert_called_with({
            'h': {'total': 200},
            'p': {'total': 500}
        })

# pylint:  enable=protected-access, missing-docstring
