'use strict';

const assert = require('node:assert/strict');
const {describe, it} = require('node:test');
const flameGraphModule = require('../flame_graph.js');

describe('CPU flame graph test suite', () => {
  it('Check getNodeName', () => {
    let node = {'stack': ['foo', 'bar', 10]};
    assert.strictEqual(
      flameGraphModule.FlameGraph.getNodeName_(node), 'foo:10 (bar)');
  });

  it('Check getTruncatedNodeName', () => {
    let node = {'stack': ['foo', 'bar.py', 10]};

    assert.strictEqual(
      flameGraphModule.FlameGraph.getTruncatedNodeName_(node, 1), '');
    assert.strictEqual(
      flameGraphModule.FlameGraph.getTruncatedNodeName_(node, 50), 'foo:...');
    assert.strictEqual(
      flameGraphModule.FlameGraph.getTruncatedNodeName_(node, 500),
      'foo:10 (bar.py)');
  });

  it('Check getLeafWithMaxY0', () => {
    let node1 = {'y0': 1};
    let node2 = {'y0': 2};
    let nested = {'y0': 3};
    let branch = {'y0': 1, 'children': [nested]};
    let nodes = {'children': [node1, node2, branch]};
    assert.strictEqual(
      flameGraphModule.FlameGraph.getLeafWithMaxY0_(nodes), nested);
  });
});
