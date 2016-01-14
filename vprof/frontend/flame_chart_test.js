var flame_chart = require('./flame_chart.js');

describe('Flame chart test suite', function() {

  it('Check getNodeName', function() {
    var node = {
      'moduleName': 'bar/foo.py',
      'funcName': 'bar',
      'lineno': 10
    };
    expect(flame_chart.getNodeName_(node)).toBe('foo.py:10(bar)');
  });

  it('Check getTruncatedNodeName', function() {
    var node = {
      'moduleName': 'bar/foo.py',
      'funcName': 'bar',
      'lineno': 10
    };
    expect(flame_chart.getTruncatedNodeName_(node, 1)).toBe('');
    expect(flame_chart.getTruncatedNodeName_(node, 50)).toBe('foo.p...');
    expect(flame_chart.getTruncatedNodeName_(node, 500)).toBe('foo.py:10(bar)');
  });

  it('Check getTimePercentage_', function() {
    expect(flame_chart.getTimePercentage_(25, 50)).toBe(50);
    expect(flame_chart.getTimePercentage_(0, 100)).toBe(0);
    expect(flame_chart.getTimePercentage_(88.8, 88.8)).toBe(100);
  });

});
