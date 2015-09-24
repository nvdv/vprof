var main = require('./main.js');

describe('Main test suite', function() {

  it('Check getNodeName', function() {
    var node = {
      'moduleName': 'bar/foo.py',
      'funcName': 'bar',
      'lineno': 10
    };
    expect(main.getNodeName(node)).toBe('foo.py:10(bar)');
  });

  it('Check getTruncatedNodeName', function() {
    var node = {
      'moduleName': 'bar/foo.py',
      'funcName': 'bar',
      'lineno': 10
    };
    expect(main.getTruncatedNodeName(node, 1)).toBe('');
    expect(main.getTruncatedNodeName(node, 50)).toBe('foo.p...');
    expect(main.getTruncatedNodeName(node, 500)).toBe('foo.py:10(bar)');
  });
});
