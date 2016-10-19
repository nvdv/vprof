"use strict";

var flameGraphModule = require('./flame_graph.js');

describe('CPU flame graph test suite', function() {
  it('Check getNodeName', function() {
    var node = {'stack': ['foo', 'bar', 10]};
    expect(flameGraphModule.FlameGraph.getNodeName_(node)).toBe(
      'foo:10 (bar)');
  });

  it('Check getTruncatedNodeName', function() {
    var node = {'stack': ['foo', 'bar.py', 10]};

    expect(flameGraphModule.FlameGraph.getTruncatedNodeName_(node, 1)).toBe('');
    expect(flameGraphModule.FlameGraph.getTruncatedNodeName_(node, 50))
      .toBe('foo:1...');
    expect(flameGraphModule.FlameGraph.getTruncatedNodeName_(node, 500))
      .toBe('foo:10 (bar.py)');
  });

  it('Check getPercentage_', function() {
    expect(flameGraphModule.FlameGraph.getPercentage_(25, 50)).toBe(50);
    expect(flameGraphModule.FlameGraph.getPercentage_(0, 100)).toBe(0);
    expect(flameGraphModule.FlameGraph.getPercentage_(
      88.8, 88.8)).toBe(100);
  });
});
