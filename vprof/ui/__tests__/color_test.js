'use strict';

const assert = require('node:assert/strict');
const {describe, it} = require('node:test');
const colorModule = require('../color.js');

describe('Color module test suite', () => {
  it('Check createColorScale maps hashes to color strings', () => {
    let scale = colorModule.createColorScale();
    assert.strictEqual(typeof scale, 'function');
    let c1 = scale(0);
    let c2 = scale(123456789);
    let c3 = scale(Math.pow(2, 32));
    assert.strictEqual(typeof c1, 'string');
    assert.strictEqual(typeof c2, 'string');
    assert.strictEqual(typeof c3, 'string');
    assert.notStrictEqual(c1, c2);
  });
});
