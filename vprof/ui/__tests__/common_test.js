'use strict';

const assert = require('node:assert/strict');
const {describe, it} = require('node:test');
const commonModule = require('../common.js');

describe('Profiler test suite', () => {
  it('Check shortenString', () => {
    assert.strictEqual(
      commonModule.shortenString('foobar', 6, true), 'foobar');
    assert.strictEqual(
      commonModule.shortenString('foobarfoobar', 10, true), '...rfoobar');
    assert.strictEqual(
      commonModule.shortenString('foobarfoobar', 10, false), 'foobarf...');
  });
});
