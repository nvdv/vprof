import mock
import vprof.__main__ as vp
import unittest

_RUN_STATS = {
    ('testscript.py', 1, 'prod'): (1, 10, 7e-06, 7e-06, {
        ('testscript.py', 1, '<module>'): (1, 1, 1e-06, 7e-06),
        ('testscript.py', 1, 'prod'): (9, 1, 6e-06, 6e-06)
    }),
    ('testscript.py', 1, '<module>'): (1, 1, 1.49, 2.3e-05, {}),
    ('~', 0, '<range>'): (1, 1, 1e-06, 1e-06, {
        ('testscript.py', 1, '<module>'): (1, 1, 1e-06, 1e-06)
    })
}

_CALLEES = {
    ('testscript.py', 1, '<module>'): [
        ('testscript.py', 1, 'prod'),
        ('~', 0, '<range>'),
    ],
    ('testscript.py', 1, 'prod'): [
        ('testscript.py', 1, 'prod')
    ]
}

_CALL_GRAPH = {
    'module_name': 'testscript.py',
    'func_name': '<module>',
    'total_calls': 1,
    'prim_calls': 1,
    'time_per_call': 1.49,
    'cum_time': 2.3e-05,
    'lineno': 1,
    'children': [
        {'func_name': 'prod',
         'prim_calls': 1,
         'total_calls': 10,
         'time_per_call': 7e-06,
         'cum_time': 7e-06,
         'lineno': 1,
         'module_name': 'testscript.py',
         'children': []},
        {'func_name': '<range>',
         'prim_calls': 1,
         'total_calls': 1,
         'time_per_call': 1e-06,
         'cum_time': 1e-06,
         'lineno': 0,
         'module_name': '~',
         'children': []}
    ]
}


class MainUnittest(unittest.TestCase):
    def testBuildCallees(self):
        self.assertDictEqual(dict(vp._build_callees(_RUN_STATS)), _CALLEES)

    def testTransformStats(self):
        stats = mock.MagicMock()
        stats.stats = _RUN_STATS
        self.assertDictEqual(vp.transform_stats(stats), _CALL_GRAPH)


if __name__ == "__main__":
    unittest.main()