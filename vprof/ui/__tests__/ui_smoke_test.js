'use strict';

const assert = require('node:assert/strict');
const {describe, it} = require('node:test');
const d3 = require('d3');
const mainModule = require('../main.js');
const {installFakeDom} = require('./dom_helper.js');

/** @returns {VprofProfilePayload} */
function buildFullPayload() {
  return {
    c: {
      objectName: 'example.py (module)',
      sampleInterval: 0.001,
      runTime: 0.25,
      totalSamples: 25,
      timestamp: 1700000000,
      callStats: {
        stack: ['<module>', 'example.py', 1],
        sampleCount: 25,
        samplePercentage: 100.0,
        colorHash: 111111,
        children: [
          {
            stack: ['work', 'example.py', 10],
            sampleCount: 25,
            samplePercentage: 100.0,
            colorHash: 222222,
            children: [],
          },
        ],
      },
    },
    h: {
      objectName: 'example.py',
      runTime: 0.25,
      heatmaps: [
        {
          name: '/abs/example.py',
          runTime: 0.25,
          srcCode: [
            ['line', 1, 'def work():'],
            ['line', 2, '    return 42'],
          ],
          heatmap: {1: 0.05, 2: 0.2},
          executionCount: {1: 1, 2: 10},
        },
      ],
    },
    m: {
      objectName: 'example.py (module)',
      totalEvents: 2,
      timestamp: 1700000000,
      codeEvents: [
        [1, 1, 20.5, '<module>', 'example.py'],
        [2, 2, 24.0, 'work', 'example.py'],
      ],
      objectsCount: [['class list', 10], ['class dict', 4]],
    },
    p: {
      objectName: 'example.py (module)',
      totalTime: 0.25,
      primitiveCalls: 11,
      totalCalls: 11,
      timestamp: 1700000000,
      callStats: [
        ['example.py', 1, '<module>', 0.25, 100.0, 1, 1, 0.25, 0.25, 111111],
        ['example.py', 10, 'work', 0.2, 80.0, 10, 10, 0.02, 0.02, 222222],
      ],
    },
  };
}

describe('UI DOM E2E smoke test', () => {
  it('Renders all four tabs, switches tabs, and toggles help overlay', () => {
    let env = installFakeDom(d3);
    try {
      mainModule.renderPage(buildFullPayload());

      let headers = env.body.queryAll('li');
      assert.deepStrictEqual(
        headers.map((h) => h.textContent),
        ['Flame graph', 'Code heatmap', 'Memory stats', 'Profiler']);
      assert.ok(headers[0].classes.has('main-tab-selected'));
      assert.ok(headers[1].classes.has('main-tab-not-selected'));

      let flameTab = d3.select('#flame-graph-tab').node();
      let memoryTab = d3.select('#memory-chart-tab').node();
      assert.ok(flameTab.classes.has('active-tab'));
      assert.ok(memoryTab.classes.has('inactive-tab'));

      // Switch to Memory stats tab.
      headers[2].trigger('click');
      assert.ok(memoryTab.classes.has('active-tab'));
      assert.ok(flameTab.classes.has('inactive-tab'));

      // Toggle help panel via the '?' button.
      let helpBtn = env.body.queryAll('.help-button')[0];
      let activeHelp = d3.select('.active-tab .tabhelp').node();
      assert.ok(activeHelp.classes.has('inactive-tabhelp'));
      env.dispatchDocumentClick(helpBtn);
      assert.ok(activeHelp.classes.has('active-tabhelp'));
      env.dispatchDocumentClick(helpBtn);
      assert.ok(activeHelp.classes.has('inactive-tabhelp'));
    } finally {
      env.restore();
    }
  });

  it('Handles empty flame graph callStats and partial configs', () => {
    let env = installFakeDom(d3);
    try {
      let payload = buildFullPayload();
      if (!payload.c) {
        throw new Error('Expected flame graph stats in test payload');
      }
      payload.c.callStats = {};
      payload.c.totalSamples = 0;

      mainModule.renderPage({c: payload.c});
      let headers = env.body.queryAll('li');
      assert.strictEqual(headers.length, 1);
      assert.strictEqual(headers[0].textContent, 'Flame graph');
      assert.strictEqual(
        env.body.queryAll('.flame-graph-no-data-message').length, 1);
    } finally {
      env.restore();
    }
  });
});
