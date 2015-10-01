var profile = require('./profile.js');

describe('Profile test suite', function() {

  it('Check getNodeName', function() {
    var node = {
      'moduleName': 'bar/foo.py',
      'funcName': 'bar',
      'lineno': 10
    };
    expect(profile.getNodeName_(node)).toBe('foo.py:10(bar)');
  });

  it('Check getTruncatedNodeName', function() {
    var node = {
      'moduleName': 'bar/foo.py',
      'funcName': 'bar',
      'lineno': 10
    };
    expect(profile.getTruncatedNodeName_(node, 1)).toBe('');
    expect(profile.getTruncatedNodeName_(node, 50)).toBe('foo.p...');
    expect(profile.getTruncatedNodeName_(node, 500)).toBe('foo.py:10(bar)');
  });
});
