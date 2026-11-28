'use strict';

const assert = require('node:assert/strict');
const {describe, it} = require('node:test');
const d3 = require('d3');
const profilerModule = require('../profiler.js');
const {installFakeDom} = require('./dom_helper.js');

describe('Profiler test suite', () => {
  it('Renders profiler records and escapes function names', () => {
    let env = installFakeDom(d3);
    try {
      /** @type {ProfilerStats} */
      let data = {
        objectName: 'app.py (module)',
        totalTime: 0.42,
        primitiveCalls: 10,
        totalCalls: 12,
        timestamp: 1700000000,
        callStats: [
          ['app.py', 1, '<module>', 0.42, 100.0, 1, 1, 0.42, 0.42, 12345],
          ['app.py', 10, 'compute', 0.21, 50.0, 5, 5, 0.042, 0.042, 67890],
        ],
      };
      let parent = d3.select('body').append('div').attr('id', 'profiler-tab');
      profilerModule.renderProfilerOutput(data, parent);

      let rows = env.body.queryAll('.profiler-record-normal');
      assert.strictEqual(rows.length, 2);
      let funcCells = env.body.queryAll('.profiler-record-funcname');
      assert.strictEqual(funcCells[0].htmlContent, '&lt;module&gt;');
      assert.strictEqual(funcCells[1].htmlContent, 'compute');

      let tooltip = env.body.queryAll('.content-tooltip')[0];
      assert.ok(tooltip.classes.has('content-tooltip-invisible'));

      rows[0].trigger('mouseover');
      assert.ok(tooltip.classes.has('content-tooltip-visible'));
      assert.ok(tooltip.htmlContent.includes('&lt;module&gt;'));
      assert.ok(rows[0].classes.has('profiler-record-highlight'));

      rows[0].trigger('mouseout');
      assert.ok(tooltip.classes.has('content-tooltip-invisible'));
      assert.ok(rows[0].classes.has('profiler-record-normal'));
    } finally {
      env.restore();
    }
  });
});
