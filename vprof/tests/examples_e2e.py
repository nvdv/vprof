"""End-to-end tests for examples."""
import contextlib
import json
import os
import signal
import subprocess
import sys
import tempfile
import unittest

from vprof import __main__
from vprof import runner

_STATIC_SITE_PATH = 'examples/static_site.py'
_LOG_PIPELINE_PATH = 'examples/log_pipeline.py'
_CONFIG = 'cmhp' if hasattr(signal, 'SIGPROF') else 'mhp'


@contextlib.contextmanager
def _suppress_stdout():
    with open(os.devnull, 'w', encoding='utf-8') as devnull:
        old_stdout_fd = os.dup(1)
        try:
            os.dup2(devnull.fileno(), 1)
            with contextlib.redirect_stdout(devnull):
                yield
        finally:
            os.dup2(old_stdout_fd, 1)
            os.close(old_stdout_fd)


class ExamplesEndToEndTest(unittest.TestCase):

    def _assert_example_profile(
            self, script_path: str, expected_func: str
    ) -> None:
        with _suppress_stdout():
            stats = runner.run_profilers(script_path, _CONFIG)
        self.assertEqual(set(stats.keys()), set(_CONFIG))

        self.assertIn(script_path, stats['m']['objectName'])
        self.assertGreater(stats['m']['totalEvents'], 0)
        self.assertGreater(len(stats['m']['codeEvents']), 0)

        self.assertEqual(stats['h']['objectName'], script_path)
        self.assertGreater(stats['h']['runTime'], 0)
        self.assertEqual(len(stats['h']['heatmaps']), 1)
        heatmap = stats['h']['heatmaps'][0]
        self.assertIn(os.path.abspath(script_path), heatmap['name'])

        self.assertIn(script_path, stats['p']['objectName'])
        self.assertGreater(stats['p']['totalCalls'], 0)
        func_names = {record[2] for record in stats['p']['callStats']}
        self.assertIn(expected_func, func_names)

        if 'c' in _CONFIG:
            self.assertIn(script_path, stats['c']['objectName'])
            self.assertGreater(stats['c']['runTime'], 0)

    def testStaticSiteExample(self):
        self._assert_example_profile(_STATIC_SITE_PATH, 'build_site')

    def testLogPipelineExample(self):
        self._assert_example_profile(_LOG_PIPELINE_PATH, 'run_log_pipeline')

    def testCliOutputFile(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, 'profile.json')
            cmd = [
                sys.executable, '-m', 'vprof',
                '-c', _CONFIG, _LOG_PIPELINE_PATH,
                '--output-file', output_file,
            ]
            proc = subprocess.run(
                cmd, capture_output=True, text=True, check=False)
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)

            with open(output_file, encoding='utf-8') as infile:
                saved_stats = json.load(infile)

            self.assertEqual(saved_stats['version'], __main__.__version__)
            for mode in _CONFIG:
                self.assertIn(mode, saved_stats)
