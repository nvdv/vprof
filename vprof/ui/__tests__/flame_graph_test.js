'use strict';

const flameGraphModule = require('../flame_graph.js');

describe('CPU flame graph test suite', () => {
  it('Check getNodeName', () => {
    let node = {'stack': ['foo', 'bar', 10]};
    expect(flameGraphModule.FlameGraph.getNodeName_(node)).toBe(
      'foo:10 (bar)');
  });

  it('Check getTruncatedNodeName', () => {
    let node = {'stack': ['foo', 'bar.py', 10]};

    expect(flameGraphModule.FlameGraph.getTruncatedNodeName_(node, 1)).toBe('');
    expect(flameGraphModule.FlameGraph.getTruncatedNodeName_(node, 50))
      .toBe('fo...');
    expect(flameGraphModule.FlameGraph.getTruncatedNodeName_(node, 500))
      .toBe('foo:10 (bar.py)');
  });

  it('Check getLeafWithMaxY0', () => {
    let node1 = {'y0': 1};
    let node2 = {'y0': 2};
    let nodes = {'children': [node1, node2]};
    expect(flameGraphModule.FlameGraph.getLeafWithMaxY0_(nodes)).toBe(node2);
  });
});
