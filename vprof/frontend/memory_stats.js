/**
 * Renders memory stats.
 */

/* jshint strict: false, browser: true, globalstrict: true */
/* global require, module */

'use strict';
var d3 = require('d3');

var MARGIN_LEFT = 50;
var MARGIN_RIGHT = 20;
var MARGIN_TOP = 20;
var MARGIN_BOTTOM  = 20;
var HEIGHT_SCALE = 0.9;
var HEIGHT = window.innerHeight * HEIGHT_SCALE - MARGIN_LEFT - MARGIN_RIGHT;
var WIDTH_SCALE = 0.95;
var WIDTH = window.innerWidth * WIDTH_SCALE - MARGIN_TOP - MARGIN_BOTTOM;
var MIN_RANGE_C = 0.95;
var MAX_RANGE_C = 1.05;
var AXIS_TEXT_Y = 12;

/** Renders memory usage graph. */
function renderMemoryStats(data, parent) {
  var chart =  parent.append('div')
    .attr('class', 'chart');

  var canvas = chart.append('svg')
    .attr('width', WIDTH + MARGIN_LEFT + MARGIN_RIGHT)
    .attr('height', HEIGHT + MARGIN_TOP + MARGIN_BOTTOM)
    .append("g")
    .attr("transform", "translate(" + MARGIN_LEFT + "," + MARGIN_TOP + ")");

  var yRange = d3.extent(data.memoryStats, function(d) { return d[1]; });
  var srcLines = data.memoryStats.map(function(d) { return d[0]; });
  var xScale = d3.scale.ordinal()
    .domain(srcLines)
    .rangeRoundBands([0, WIDTH]);
  var yScale = d3.scale.linear()
    .domain([MIN_RANGE_C * yRange[0], MAX_RANGE_C * yRange[1]])
    .range([HEIGHT, 0]);

  var yAxis = d3.svg.axis()
    .scale(yScale)
    .orient('left');

  var barGroups = canvas.selectAll('.bar')
    .data(data.memoryStats)
    .enter()
    .append('g');

  var tooltip = chart.append('div')
    .attr('class', 'tooltip tooltip-invisible');

  // Draw memory bars.
  barGroups.append('rect')
    .attr('class', 'bar rect-normal')
    .attr("x", function(d) { return xScale(d[0]); })
    .attr("width", xScale.rangeBand())
    .attr("y", function(d) { return yScale(d[1]); })
    .attr("height", function(d) { return HEIGHT - yScale(d[1]); })
    .on('mouseover', function(d) {
      d3.select(this)
        .attr('class', 'bar rect-highlight');
      var functionName = d[0][2].replace('<', '[').replace('>',  ']');
      tooltip.attr('class', 'tooltip tooltip-visible')
        .html('<p>Location: ' + d[0][0] + '</p>' +
              '<p>Line number: ' + d[0][1] + '</p>' +
              '<p>Function name: ' + functionName + '</p>' +
              '<p>Memory usage: ' + d[1] + ' MB</p>'
              )
        .style('left', d3.event.pageX)
        .style('top', d3.event.pageY);
    })
    .on('mouseout', function(d) {
      d3.select(this).attr('class', 'bar rect-normal');
      tooltip.attr('class', 'tooltip tooltip-invisible');
    });

  canvas.append('g')
    .attr('class', 'axis')
    .call(yAxis)
    .append('text')
    .attr('transform', 'rotate(-90)')
    .attr('y', AXIS_TEXT_Y)
    .attr('dy', '.71em')
    .text('Memory usage, MB');
}

module.exports = {
  'renderMemoryStats': renderMemoryStats,
};