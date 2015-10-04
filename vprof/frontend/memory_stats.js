/**
 * Renders memory stats.
 */

/* jshint strict: false, browser: true, globalstrict: true */
/* global require, module */

'use strict';
var d3 = require('d3');

var HEIGHT_SCALE = 0.9;
var HEIGHT = window.innerHeight * HEIGHT_SCALE;
var WIDTH_SCALE = 0.95;
var WIDTH = window.innerWidth * WIDTH_SCALE;
var MIN_RANGE_C = 0.95;
var MAX_RANGE_C = 1.05;

/** Renders memory usage graph. */
function renderMemoryStats(data, parent) {
  var chart =  parent.append('div')
    .attr('class', 'chart');

  var canvas = chart.append('svg')
    .attr('width', WIDTH)
    .attr('height', HEIGHT);

  var yRange = d3.extent(data.memoryStats, function(d) { return d[1]; });
  var srcLines = data.memoryStats.map(function(d) { return d[0]; });
  var xScale = d3.scale.ordinal()
    .domain(srcLines)
    .rangeRoundBands([0, WIDTH]);
  var yScale = d3.scale.linear()
    .domain([MIN_RANGE_C * yRange[0], MAX_RANGE_C * yRange[1]])
    .range([HEIGHT, 0]);

  var xAxis = d3.svg.axis()
    .scale(xScale)
    .orient('top');
  var yAxis = d3.svg.axis()
    .scale(yScale)
    .orient('right');

  var line = d3.svg.line()
    .x(function(d) { return xScale(d[0]); })
    .y(function(d) { return yScale(d[1]); });

  canvas.append('path')
    .datum(data.memoryStats)
    .attr('class', 'memory-line')
    .attr('d', line);

  canvas.append("g")
    .attr('class', 'axis')
    .attr('transform', 'translate(0,' + HEIGHT + ')')
    .call(xAxis);

  canvas.append('g')
    .attr('class', 'axis')
    .call(yAxis);
}

module.exports = {
  'renderMemoryStats': renderMemoryStats,
};