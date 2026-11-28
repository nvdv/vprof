'use strict';

const assert = require('node:assert/strict');
const {describe, it} = require('node:test');
const codeHeatmapModule = require('../code_heatmap.js');

describe('Code heatmap test suite', () => {
  it('Check renderCode', () => {
    let origFormat = codeHeatmapModule.CodeHeatmap.prototype.formatSrcLine_;
    try {
      codeHeatmapModule.CodeHeatmap.prototype.formatSrcLine_ = (n) => String(n);
      let data = {objectName: 'test.py', runTime: 1.0, heatmaps: []};
      let calculator = new codeHeatmapModule.CodeHeatmap({}, data);

      let codeStats1 = {
        'srcCode': [
          ['line', 1, 'foo'], ['line', 2, 'bar'], ['line', 3, 'baz']],
        'heatmap': {1: 0.1, 2: 0.2, 3: 0.2},
        'executionCount': {1: 1, 2: 1, 3: 1},
      };

      let expectedResult1 = {
        'srcCode': '123',
        'timeMap': {0: 0.1, 1: 0.2, 2: 0.2},
        'countMap': {0: 1, 1: 1, 2: 1}
      };
      assert.deepStrictEqual(
        calculator.renderCode_(codeStats1), expectedResult1);

      let codeStats2 = {
        'srcCode': [
          ['line', 1, 'foo'], ['line', 2, 'bar'],
          ['skip', 5], ['line', 8, 'hahaha']],
        'heatmap': {1: 0.1, 2: 0.1, 8: 0.3},
        'executionCount': {1: 1, 2: 1, 8: 1},
      };

      let expectedResult2 = {
        'srcCode': "12<div class='heatmap-skip-line'>5 lines skipped</div>8",
        'timeMap': {0: 0.1, 1: 0.1, 2: 0.3},
        'countMap': {0: 1, 1: 1, 2: 1}
      };
      assert.deepStrictEqual(
        calculator.renderCode_(codeStats2), expectedResult2);
    } finally {
      codeHeatmapModule.CodeHeatmap.prototype.formatSrcLine_ = origFormat;
    }
  });

  it('Check formatSrcLine highlights Python and applies heat color', () => {
    let calculator = new codeHeatmapModule.CodeHeatmap(
      {}, {objectName: 'test.py', runTime: 1.0, heatmaps: []});
    let hotLine = calculator.formatSrcLine_(10, 'def foo():', 0.5);
    assert.ok(hotLine.includes('heatmap-src-line-normal'));
    assert.ok(hotLine.includes('10'));
    assert.ok(hotLine.includes('hljs-keyword'));
    assert.ok(!hotLine.includes("background-color: '"));

    let coldLine = calculator.formatSrcLine_(11, 'pass', 0);
    assert.ok(coldLine.includes("background-color: '"));
  });
});
