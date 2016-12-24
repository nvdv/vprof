'use strict';

var profilerModule = require('../profiler.js');

describe('Profiler test suite', function() {
  it('Check formatProfilerRecord_', function() {
    var data = [0, 10, 'func', 100, 15, 5, 6, 7, 'foo.py'];
    var expectedResult = (
      '<td class="profiler-record-percentage">15%</td>' +
      '<td class="profiler-record-name">' +
        '<span class="profiler-record-funcname">func</span>' + ' ' +
        '<span class="profiler-record-filename">foo.py</span>' + ':' +
        '<span class="profiler-record-lineno">10</span>' +
      '</td>' +
      '<td class="profiler-record-cumtime">100s</td>');

    expect(profilerModule.Profiler.formatProfilerRecord_(data)).toBe(
        expectedResult);
  });
});
