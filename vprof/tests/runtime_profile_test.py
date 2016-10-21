# pylint: disable=protected-access, missing-docstring
import operator
import unittest

from vprof import runtime_profile

# For Python 2 and Python 3 compatibility.
try:
    import mock
except ImportError:
    from unittest import mock  # pylint: disable=ungrouped-imports

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
    ('testscript.py', 1, '<module>'): {
        ('~', 0, '<range>'): (1, 1, 1e-06, 1e-06),
        ('testscript.py', 1, 'prod'): (9, 10, 6e-06, 6e-06),
    },
    ('testscript.py', 1, 'prod'): {
        ('testscript.py', 1, 'prod'): (9, 10, 6e-06, 6e-06)
    },
    ('~', 0, '<range>'): {}
}

_CALL_GRAPH = {
    'moduleName': 'testscript.py',
    'funcName': '<module>',
    'totalCalls': 1,
    'primCalls': 1,
    'timePerCall': 1.49,
    'cumTime': 2.3e-05,
    'lineno': 1,
    'children': [
        {'funcName': '<range>',
         'primCalls': 1,
         'totalCalls': 1,
         'timePerCall': 1e-06,
         'cumTime': 1e-06,
         'lineno': 0,
         'moduleName': '~',
         'children': []},
        {'funcName': 'prod',
         'primCalls': 9,
         'totalCalls': 10,
         'timePerCall': 6e-06,
         'cumTime': 6e-06,
         'lineno': 1,
         'moduleName': 'testscript.py',
         'children': []}
    ]
}


class RuntimeProfileUnittest(unittest.TestCase):
    def setUp(self):
        self._profile = object.__new__(runtime_profile.RuntimeProfile)

    def testTransformStats(self):
        stats = mock.MagicMock()
        stats.stats, stats.all_callees = _RUN_STATS, _CALLEES
        result = self._profile._transform_stats(stats)
        self.assertEqual(result['moduleName'], _CALL_GRAPH['moduleName'])
        self.assertEqual(result['funcName'], _CALL_GRAPH['funcName'])
        self.assertEqual(result['cumTime'], _CALL_GRAPH['cumTime'])
        self.assertListEqual(
            sorted(result['children'], key=operator.itemgetter('funcName')),
            sorted(_CALL_GRAPH['children'],
                   key=operator.itemgetter('funcName')))

# pylint:  enable=protected-access, missing-docstring
