import mock
import vprof.__main__ as vp
import unittest

_RUN_STATS = {
    ('main',): (10, 10, 0.01, 0.5, ()),
    ('foo',): (5, 5, 0.02, 0.3, ('main')),
    ('bar',): (3, 3, 0.01, 0.5, ('foo'))}

_ANNOTATED_STATS = {
    ('main',): {
        'cum_calls': 10,
        'num_calls': 10,
        'time_per_call': 0.01,
        'cum_time': 0.5,
        'callers': ()},
    ('foo',): {
        'cum_calls': 5,
        'num_calls': 5,
        'time_per_call': 0.02,
        'cum_time': 0.3,
        'callers': ('main')},
    ('bar',): {
        'cum_calls': 3,
        'num_calls': 3,
        'time_per_call': 0.01,
        'cum_time': 0.5,
        'callers': ('foo')}}

_CALLERS = {
    ('main',): {
        ('foo',): (10, 10, 0.01, 0.5),
    },
    ('foo',): {
        ('bar',): (3, 3, 0.01, 0.5),
    },
    ('bar',): {}
}

_CALL_GRAPH = {
    'name': 'main',
    'cum_calls': 10,
    'num_calls': 10,
    'time_per_call': 0.01,
    'cum_time': 0.5,
    'children': [{
        'name': 'foo',
        'cum_calls': 5,
        'num_calls': 5,
        'time_per_call': 0.02,
        'cum_time': 0.3,
        'children': [{
            'name': 'bar',
            'cum_calls': 3,
            'num_calls': 3,
            'time_per_call': 0.01,
            'cum_time': 0.5,
            'children': [],
        }]
    }]
}


class MainUnittest(unittest.TestCase):
    def testAnnotateStats(self):
        self.assertDictEqual(vp._annotate_stats(_RUN_STATS), _ANNOTATED_STATS)

    def testFillStats(self):
        root = max(_ANNOTATED_STATS.items(), key=lambda s: s[1]['cum_time'])
        self.assertDictEqual(
            vp._fill_stats(root[0], _CALLERS, _ANNOTATED_STATS), _CALL_GRAPH)

    @mock.patch('vprof.__main__._annotate_stats')
    def testTransformStats(self, annotate_mock):
        annotate_mock.return_value = _ANNOTATED_STATS
        stats = mock.MagicMock()
        stats.all_callees = _CALLERS
        self.assertDictEqual(vp.transform_stats(stats), _CALL_GRAPH)


if __name__ == "__main__":
    unittest.main()