"use strict";

var flameGraphModule = require('./flame_graph.js');

describe('CPU flame graph test suite', function() {
  it('Check getNodeName', function() {
    var node = {
      'moduleName': 'bar/foo.py',
      'funcName': 'bar',
      'lineno': 10
    };
    expect(flameGraphModule.FlameGraph.getNodeName_(node)).toBe(
      'foo.py:10(bar)');
  });

  it('Check getTruncatedNodeName', function() {
    var node = {
      'moduleName': 'bar/foo.py',
      'funcName': 'bar',
      'lineno': 10
    };
    expect(flameGraphModule.FlameGraph.getTruncatedNodeName_(node, 1)).toBe('');
    expect(flameGraphModule.FlameGraph.getTruncatedNodeName_(node, 50))
      .toBe('foo.p...');
    expect(flameGraphModule.FlameGraph.getTruncatedNodeName_(node, 500))
      .toBe('foo.py:10(bar)');
  });

  it('Check getTimePercentage_', function() {
    expect(flameGraphModule.FlameGraph.getTimePercentage_(25, 50)).toBe(50);
    expect(flameGraphModule.FlameGraph.getTimePercentage_(0, 100)).toBe(0);
    expect(flameGraphModule.FlameGraph.getTimePercentage_(
      88.8, 88.8)).toBe(100);
  });
});
