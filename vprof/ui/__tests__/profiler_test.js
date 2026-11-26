'use strict';

const assert = require('node:assert/strict');
const {describe, it} = require('node:test');
const profilerModule = require('../profiler.js');

describe('Profiler test suite', () => {
  it('Dummy test', () => {
    assert.strictEqual(typeof profilerModule.Profiler, 'function');
  });
});
