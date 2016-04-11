"""Code heatmap end to end tests."""
import json
import functools
import threading
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

_HOST, _PORT = 'localhost', 12345
_MODULE_FILENAME = 'vprof/tests/test_pkg/dummy_module.py'
_PACKAGE_PATH = 'vprof/tests/test_pkg/'
_PACKAGE_NAME = 'vprof.tests.test_pkg'


class CodeHeatmapModuleEndToEndTest(unittest.TestCase):

    def setUp(self):
        program_stats = code_heatmap.CodeHeatmapProfile(
            _MODULE_FILENAME).run()
        stats_handler = functools.partial(
            stats_server.StatsHandler, program_stats)
        self.server = stats_server.StatsServer(
            (_HOST, _PORT), stats_handler)
        threading.Thread(target=self.server.serve_forever).start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def testRequest(self):
        response = urllib.request.urlopen(
            'http://%s:%s/profile' % (_HOST, _PORT))
        stats = json.loads(response.read().decode('utf-8'))
        self.assertEqual(stats['programName'], _MODULE_FILENAME)
        self.assertDictEqual(stats['heatmap'][0]['fileHeatmap'], {'1': 1})


class CodeHeatmapPackageAsPathEndToEndTest(unittest.TestCase):

    def setUp(self):
        program_stats = code_heatmap.CodeHeatmapProfile(
            _PACKAGE_PATH).run()
        stats_handler = functools.partial(
            stats_server.StatsHandler, program_stats)
        self.server = stats_server.StatsServer(
            (_HOST, _PORT), stats_handler)
        threading.Thread(target=self.server.serve_forever).start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def testRequest(self):
        response = urllib.request.urlopen(
            'http://%s:%s/profile' % (_HOST, _PORT))
        stats = json.loads(response.read().decode('utf-8'))
        self.assertEqual(stats['programName'], _PACKAGE_PATH)
        self.assertTrue(
            stats['heatmap'][0]['filename'].endswith(
                'vprof/tests/test_pkg/__main__.py'))
        self.assertDictEqual(
            stats['heatmap'][0]['fileHeatmap'], {'1': 1, '3': 1})
        self.assertTrue(
            stats['heatmap'][1]['filename'].endswith(
                'vprof/tests/test_pkg/dummy_module.py'))
        self.assertEqual(stats['heatmap'][1]['fileHeatmap']['2'], 15)
        self.assertEqual(stats['heatmap'][1]['fileHeatmap']['3'], 8)
        self.assertEqual(stats['heatmap'][1]['fileHeatmap']['4'], 7)


class CodeHeatmapImportedPackageEndToEndTest(unittest.TestCase):

    def setUp(self):
        program_stats = code_heatmap.CodeHeatmapProfile(
            _PACKAGE_NAME).run()
        stats_handler = functools.partial(
            stats_server.StatsHandler, program_stats)
        self.server = stats_server.StatsServer(
            (_HOST, _PORT), stats_handler)
        threading.Thread(target=self.server.serve_forever).start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def testRequest(self):
        response = urllib.request.urlopen(
            'http://%s:%s/profile' % (_HOST, _PORT))
        stats = json.loads(response.read().decode('utf-8'))

        self.assertEqual(stats['programName'], _PACKAGE_NAME)
        self.assertTrue(
            stats['heatmap'][0]['filename'].endswith(
                'vprof/tests/test_pkg/__main__.py'))
        self.assertDictEqual(
            stats['heatmap'][0]['fileHeatmap'], {'1': 1, '3': 1})
        self.assertTrue(
            stats['heatmap'][1]['filename'].endswith(
                'vprof/tests/test_pkg/dummy_module.py'))
        self.assertEqual(stats['heatmap'][1]['fileHeatmap']['2'], 15)
        self.assertEqual(stats['heatmap'][1]['fileHeatmap']['3'], 8)
        self.assertEqual(stats['heatmap'][1]['fileHeatmap']['4'], 7)
