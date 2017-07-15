'use strict';

const flameGraphModule = require('../flame_graph.js');

describe('CPU flame graph test suite', function() {
  it('Check getNodeName', function() {
    let node = {'stack': ['foo', 'bar', 10]};
    expect(flameGraphModule.FlameGraph.getNodeName_(node)).toBe(
      'foo:10 (bar)');
  });

  it('Check getTruncatedNodeName', function() {
    let node = {'stack': ['foo', 'bar.py', 10]};

    expect(flameGraphModule.FlameGraph.getTruncatedNodeName_(node, 1)).toBe('');
    expect(flameGraphModule.FlameGraph.getTruncatedNodeName_(node, 50))
      .toBe('fo...');
    expect(flameGraphModule.FlameGraph.getTruncatedNodeName_(node, 500))
      .toBe('foo:10 (bar.py)');
  });

});
