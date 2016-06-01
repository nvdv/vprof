var code_heatmap = require('./code_heatmap.js');

describe('Code heatmap test suite', function() {
  it('Check renderCodeWithSkips', function() {
    code_heatmap.CodeHeatmap.prototype.formatSrcLine_ = function(n, l, c) {
      return n;
    };
    var data = {}, parent = {};
    var calculator = new code_heatmap.CodeHeatmap(parent, data);

    var srcCode = [[1, 'foo'], [2, 'bar'], [3, 'baz']];
    var heatmap = {1: 1, 2: 1, 3: 1};
    var skipMap = [[2, 1]];
    var expectedResult = {
      'srcCode': "12<div class='skip-line'>1 lines skipped</div>",
      'lineMap': {0: 1, 1: 1}};
    expect(calculator.renderCodeWithSkips_(srcCode, heatmap, skipMap)).toEqual(
      expectedResult);
  });

  it('Check renderCode', function() {
    code_heatmap.CodeHeatmap.prototype.formatSrcLine_ = function(n, l, c) {
      return n;
    };
    var data = {}, parent = {};
    var calculator = new code_heatmap.CodeHeatmap(parent, data);

    var srcCode = [[1, 'foo'], [2, 'bar'], [3, 'baz']];
    var heatmap = {1: 1, 2: 1, 3: 1};
    var skipMap = [[2, 1]];
    var expectedResult = {
      'srcCode': "123",
      'lineMap': {0: 1, 1: 1, 2: 1}};
    expect(calculator.renderCode_(srcCode, heatmap)).toEqual(
      expectedResult);
  });
});
