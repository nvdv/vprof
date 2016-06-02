var code_heatmap = require('./code_heatmap.js');

describe('Code heatmap test suite', function() {
  it('Check renderCode', function() {
    code_heatmap.CodeHeatmap.prototype.formatSrcLine_ = function(n, l, c) {
      return n;
    };
    var data = {}, parent = {};
    var calculator = new code_heatmap.CodeHeatmap(parent, data);

    var srcCode = [['line', 1, 'foo'], ['line', 2, 'bar'], ['line', 3, 'baz']];
    var heatmap = {1: 1, 2: 1, 3: 1};
    var expectedResult = {
      'srcCode': "123",
      'lineMap': {0: 1, 1: 1, 2: 1}};
    expect(calculator.renderCode_(srcCode, heatmap)).toEqual(
      expectedResult);

    srcCode = [['line', 1, 'foo'], ['line', 2, 'bar'],
               ['skip', 5], ['line', 8, 'hahaha']];
    heatmap = {1: 1, 2: 1, 8: 1};
    expectedResult = {
      'srcCode': "12<div class='skip-line'>5 lines skipped</div>8",
      'lineMap': {0: 1, 1: 1, 3: 1}};
    expect(calculator.renderCode_(srcCode, heatmap)).toEqual(
      expectedResult);
  });
});
