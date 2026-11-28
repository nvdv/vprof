'use strict';

const assert = require('node:assert/strict');
const {describe, it} = require('node:test');
const memoryStatsModule = require('../memory_stats.js');

describe('Memory stats test suite', () => {
  it('Check generateTooltipText_', () => {
    /** @type {MemoryEvent} */
    let stats = [10, 11, 15, '<func>', 'foo.py'];
    let expectedResult = (
      '<p><b>Executed line:</b> 10</p>' +
      '<p><b>Line number:</b> 11</p>' +
      '<p><b>Function name:</b> [func]</p>' +
      '<p><b>Filename:</b> foo.py</p>' +
      '<p><b>Memory usage:</b> 15 MB</p>');

    assert.strictEqual(
      memoryStatsModule.MemoryChart.generateTooltipText_(stats),
      expectedResult);
    assert.strictEqual(
      memoryStatsModule.MemoryChart.generateTooltipText_(null), '');
  });
});
