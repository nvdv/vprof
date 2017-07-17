'use strict';

const codeHeatmapModule = require('../code_heatmap.js');

describe('Code heatmap test suite', () => {
  it('Check renderCode', () => {
    codeHeatmapModule.CodeHeatmap.prototype.formatSrcLine_ = (n, l, c) => n;
    let data = {}, parent = {};
    let calculator = new codeHeatmapModule.CodeHeatmap(parent, data);

    let srcCode = [['line', 1, 'foo'], ['line', 2, 'bar'], ['line', 3, 'baz']];
    let heatmap = {1: 0.1, 2: 0.2, 3: 0.2};
    let executionCount = {1: 1, 2: 1, 3: 1};
    let codeStats = {
      'srcCode': srcCode,
      'heatmap': heatmap,
      'executionCount': executionCount,
    };

    let expectedResult = {
      'srcCode': "123",
      'timeMap': {0: 0.1, 1: 0.2, 2: 0.2},
      'countMap': {0: 1, 1: 1, 2: 1}
    };
    expect(calculator.renderCode_(codeStats)).toEqual(expectedResult);

    srcCode = [
      ['line', 1, 'foo'], ['line', 2, 'bar'],
      ['skip', 5], ['line', 8, 'hahaha']];
    heatmap = {1: 0.1, 2: 0.1, 8: 0.3};
    executionCount = {1: 1, 2: 1, 8: 1};
    codeStats = {
      'srcCode': srcCode,
      'heatmap': heatmap,
      'executionCount': executionCount,
    };

    expectedResult = {
      'srcCode': "12<div class='heatmap-skip-line'>5 lines skipped</div>8",
      'timeMap': {0: 0.1, 1: 0.1, 2: 0.3},
      'countMap': {0: 1, 1: 1, 2: 1}
    };
    expect(calculator.renderCode_(codeStats)).toEqual(expectedResult);
  });
});
