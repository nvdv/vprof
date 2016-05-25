var flame_graph = require('./flame_graph.js');

describe('CPU flame graph test suite', function() {
  it('Check getNodeName', function() {
    var node = {
      'moduleName': 'bar/foo.py',
      'funcName': 'bar',
      'lineno': 10
    };
    expect(flame_graph.FlameGraph.getNodeName_(node)).toBe('foo.py:10(bar)');
  });

  it('Check getTruncatedNodeName', function() {
    var node = {
      'moduleName': 'bar/foo.py',
      'funcName': 'bar',
      'lineno': 10
    };
    expect(flame_graph.FlameGraph.getTruncatedNodeName_(node, 1)).toBe('');
    expect(flame_graph.FlameGraph.getTruncatedNodeName_(node, 50))
      .toBe('foo.p...');
    expect(flame_graph.FlameGraph.getTruncatedNodeName_(node, 500))
      .toBe('foo.py:10(bar)');
  });

  it('Check getTimePercentage_', function() {
    expect(flame_graph.FlameGraph.getTimePercentage_(25, 50)).toBe(50);
    expect(flame_graph.FlameGraph.getTimePercentage_(0, 100)).toBe(0);
    expect(flame_graph.FlameGraph.getTimePercentage_(88.8, 88.8)).toBe(100);
  });
});
