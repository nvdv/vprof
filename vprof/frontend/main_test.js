var main = require('./main.js');

describe('Main test suite', function() {
  it('Check getNodeName', function() {
    var node = {
      'module_name': 'foo',
      'func_name': 'bar',
      'lineno': 10
    };
    expect(main.getNodeName(node)).toBe('foo.bar@10');
  });
});
