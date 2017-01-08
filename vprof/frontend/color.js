/**
 * @file Graph coloring functions.
 */

'use strict';
var d3interpolate = require('d3-interpolate');
var d3scale = require('d3-scale');

var COLORS = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00'];
var NUM_COLOR_DOMAIN_POINTS = COLORS.length;
var MAX_COLOR_DOMAIN_VALUE = Math.pow(2, 24) - 1;

/**
 * Creates color scale that maps hashes (integers) to specified color ranges.
 */
function createColorScale() {
  var hashDomain = genHashDomain_(
      NUM_COLOR_DOMAIN_POINTS, MAX_COLOR_DOMAIN_VALUE);
  return d3scale.scaleLinear()
    .domain(hashDomain)
    .range(COLORS)
    .interpolate(d3interpolate.interpolateLab);
};

/**
 * Generates array to be used as domain for coloring.
 * @param (number) numElements - Number of elements in resulting array.
 * @param {number} maxValue - Max value of domain.
 * @returns {Object}
 */
function genHashDomain_(numElements, maxValue) {
  var hashDomain = [];
  for (var i = 0; i < numElements; i++) {
    hashDomain.push(i * maxValue / numElements);
  }
  return hashDomain;
};

module.exports = {
  'createColorScale': createColorScale
};

