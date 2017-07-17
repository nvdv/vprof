'use strict';

const commonModule = require('../common.js');

describe('Profiler test suite', () => {
  it('Check shortenString', () => {
    expect(commonModule.shortenString('foobar', 6, true)).toBe('foobar');
    expect(commonModule.shortenString('foobarfoobar', 10, true)).toBe(
      '...rfoobar');
    expect(commonModule.shortenString('foobarfoobar', 10, false)).toBe(
      'foobarf...');
  });
});
