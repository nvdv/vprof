"""Code heatmap end to end tests."""
import json
import multiprocessing
import unittest

from six.moves import builtins
from six.moves import urllib

from vprof import code_heatmap
from vprof import stats_server

# For Python 2 and Python 3 compatibility.
try:
    import mock
except ImportError:
    from unittest import mock

_TEST_FILE = """
def fib(n):
    a, b = 0, 1
    for _ in range(n):
        yield a, b
        a, b = b, a + b

list(fib(20))
"""
_HOST, _PORT = 'localhost', 12345


class CodeHeatmapEndToEndTest(unittest.TestCase):

    def setUp(self):
        self.patch = mock.patch.object(
            builtins, 'open', mock.mock_open(read_data=_TEST_FILE))
        self.patch.start()
        program_stats = code_heatmap.CodeHeatmapProfile('foo.py').run()
        self.process = multiprocessing.Process(
            target=stats_server.start, args=(
                _HOST, _PORT, program_stats, True))
        self.process.start()

    def tearDown(self):
        self.process.terminate()
        self.patch.stop()

    def testRequest(self):
        response = urllib.request.urlopen(
            'http://%s:%s/profile' % (_HOST, _PORT))
        stats = json.loads(response.read().decode('utf-8'))
        self.assertEqual(stats['programName'], 'foo.py')
        self.assertEqual(stats['srcCode'], _TEST_FILE)
        self.assertDictEqual(
            stats['heatmap'],
            {'2': 1, '3': 1, '4': 21, '5': 20, '6': 20, '8': 1})
