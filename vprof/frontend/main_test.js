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

  it('Check flattenStats', function() {
    var nested = {
      'attr': 'foo',
      'children': [{
          'attr': 'bar',
          'children': [{
              'attr': 'baz',
              'children': []
          }]
      }]
    };
    var flat = [
      {'attr': 'foo'},
      {'attr': 'bar'},
      {'attr': 'baz'}
    ]
    expect(main.flattenStats(nested)).toEqual(flat);
  });

});
