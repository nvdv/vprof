/**
 * @file Graph coloring functions.
 */

'use strict';
var d3interpolate = require('d3-interpolate');
var d3scale = require('d3-scale');

var MAX_COLOR_DOMAIN_VALUE = Math.pow(2, 32);

/**
 * Creates color scale that maps hashes (integers) to specified color ranges.
 */
function createColorScale() {
  return d3scale.scaleSequential(d3scale.interpolateRainbow)
    .domain([0, MAX_COLOR_DOMAIN_VALUE]);
};

module.exports = {
  'createColorScale': createColorScale
};

