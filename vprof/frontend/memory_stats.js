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
var SCALE = 0.95;
var HEIGHT = window.innerHeight * SCALE - MARGIN_LEFT - MARGIN_RIGHT;
var WIDTH = window.innerWidth * SCALE - MARGIN_TOP - MARGIN_BOTTOM;
var MIN_RANGE_C = 0.95;
var MAX_RANGE_C = 1.05;
var AXIS_TEXT_Y = 12;
var LEGEND_X = WIDTH - 350;
var LEGEND_Y = 100;
var EVENT_COLOR_MAP = {
    'return': '#2ca02c',
    'call': '#d62728',
    'line': '#1f77b4',
};
var PATTERN_WIDTH = 5;
var PATTERN_HEIGHT = 5;

/** Renders memory stats legend. */
function renderLegend_(parent, data) {
  parent.append('div')
    .attr('class', 'legend')
    .html('<p>Filename: ' + data.programName + '</p>' +
          '<p>Total events: ' + data.totalEvents + '</p>')
    .style('left', LEGEND_X)
    .style('top', LEGEND_Y);
}

/** Processes GC stats and returns them as formatted string. */
function processGCStats_(stats) {
  var result = '';
  if (stats) {
    result += '<p>GC runs: ' + stats.length + '</p>';
    for (var i = 0; i < stats.length; i++) {
      result += (
          '<p>Run:' + (i + 1) + '</p>' +
          '<p>Objects in generations: ' + stats[i].objInGenerations + '</p>'+
          '<p>Time elapsed: ' + stats[i].timeElapsed + '</p>' +
          '<p>Uncollectable: ' + stats[i].uncollectable + '</p>' +
          '<p>Unreachable: ' + stats[i].unreachable + '</p>');
    }
  }
  return result;
}

/** Renders memory usage graph. */
function renderMemoryStats(data, parent) {
  var chart =  parent.append('div')
    .attr('class', 'chart');

  var canvas = chart.append('svg')
    .attr('width', WIDTH + MARGIN_LEFT + MARGIN_RIGHT)
    .attr('height', HEIGHT + MARGIN_TOP + MARGIN_BOTTOM)
    .append("g")
    .attr("transform", "translate(" + MARGIN_LEFT + "," + MARGIN_TOP + ")");

  canvas.append('defs')
    .append('pattern')
    .attr('id', 'diagFill')
    .attr('patternUnits', 'userSpaceOnUse')
    .attr('width', PATTERN_WIDTH)
    .attr('height', PATTERN_HEIGHT)
    .append('path')
    .attr('d', 'M-1,1 l2,-2 M0,4 l4,-4 M3,5 l2,-2')
    .attr('stroke', '#000000');

  var yRange = d3.extent(data.codeEvents, function(d) { return d[2]; });
  var srcLines = data.codeEvents.map(function(d) { return d[0]; });
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
    .data(data.codeEvents)
    .enter()
    .append('g');

  var tooltip = chart.append('div')
    .attr('class', 'tooltip tooltip-invisible');

  renderLegend_(chart, data);

  // Draw memory bars.
  barGroups.append('rect')
    .attr('class', 'memory-bar-normal')
    .attr("x", function(d) { return xScale(d[0]); })
    .attr("width", xScale.rangeBand())
    .attr("y", function(d) { return yScale(d[2]); })
    .attr("height", function(d) { return HEIGHT - yScale(d[2]); })
    .attr('fill', function(d) {
        return d[5] ? 'url(#diagFill)' : EVENT_COLOR_MAP[d[3]]; })
    .on('mouseover', function(d) {
      d3.select(this)
        .attr('class', 'memory-bar-highlight');
      var functionName = d[4].replace('<', '[').replace('>',  ']');
      var gcStats = processGCStats_(d[5]);
      tooltip.attr('class', 'tooltip tooltip-visible')
        .html('<p>Line number: ' + d[1] + '</p>' +
              '<p>Event type: ' + d[3] + '</p>' +
              '<p>Function name: ' + functionName + '</p>' +
              '<p>Memory usage: ' + d[2] + ' MB</p>' + gcStats)
        .style('left', d3.event.pageX)
        .style('top', d3.event.pageY);
    })
    .on('mouseout', function(d) {
      d3.select(this).attr('class', 'memory-bar-normal');
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
