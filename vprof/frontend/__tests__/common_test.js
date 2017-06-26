'use strict';

var commonModule = require('../common.js');

describe('Profiler test suite', function() {
  it('Check shortenString', function() {
    expect(commonModule.shortenString('foobar', 6, true)).toBe('foobar');
    expect(commonModule.shortenString('foobarfoobar', 10, true)).toBe(
      '...rfoobar');
    expect(commonModule.shortenString('foobarfoobar', 10, false)).toBe(
      'foobarf...');
  });
});
