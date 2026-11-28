'use strict';

const assert = require('node:assert/strict');
const {describe, it} = require('node:test');
const commonModule = require('../common.js');

describe('Common module test suite', () => {
  it('Check shortenString', () => {
    assert.strictEqual(
      commonModule.shortenString('foobar', 6, true), 'foobar');
    assert.strictEqual(
      commonModule.shortenString('foobarfoobar', 10, true), '...rfoobar');
    assert.strictEqual(
      commonModule.shortenString('foobarfoobar', 10, false), 'foobarf...');
  });

  it('Check formatTimestamp', () => {
    let ts = Math.floor(new Date(2026, 4, 15, 9, 30, 45).getTime() / 1000);
    assert.strictEqual(commonModule.formatTimestamp(ts), '5/15/2026 9:30:45');
  });
});
