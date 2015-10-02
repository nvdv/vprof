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

/** Renders memory usage graph. */
function renderMemoryStats(data, parent) {
  var chart =  parent.append('div')
    .attr('class', 'chart');

  var canvas = chart.append('svg')
    .attr('width', WIDTH)
    .attr('height', HEIGHT);

  var xScale = d3.scale.linear()
    .range([0, WIDTH]);
  var yScale = d3.scale.linear()
    .range([0, HEIGHT]);

  var xAxis = d3.svg.axis()
    .scale(xScale)
    .orient('bottom');
  var yAxis = d3.svg.axis()
    .scale(yScale)
    .orient('left');

  var counter = 0;
  var valueline = d3.svg.line()
    .x(function(d) {
      return xScale(counter++);
    })
    .y(function(d) { return d[1]; });

  canvas.append('path')
    .attr('class', 'memory-line')
    .attr('d', valueline(data.memoryStats));

  canvas.append('g')
    .attr('class', 'axis')
    .attr('transform', 'translate(0,' + HEIGHT + ')')
    .call(xAxis);

  canvas.append("g")
    .attr('class', 'axis')
    .call(yAxis);
}

module.exports = {
  'renderMemoryStats': renderMemoryStats,
};