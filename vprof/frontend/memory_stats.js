/**
 * Renders memory stats.
 */

/* jshint strict: false, browser: true, globalstrict: true */
/* global require, module */

'use strict';
var d3 = require('d3');

var MARGIN_LEFT = 30;
var MARGIN_RIGHT = 0;
var MARGIN_TOP = 0;
var MARGIN_BOTTOM  = 0;
var SCALE = 0.95;
var HEIGHT = window.innerHeight * SCALE - MARGIN_LEFT - MARGIN_RIGHT;
var WIDTH = window.innerWidth * SCALE - MARGIN_TOP - MARGIN_BOTTOM;
var MIN_RANGE_C = 0.95;
var MAX_RANGE_C = 1.05;
var AXIS_TEXT_Y = 12;
var LEGEND_X = WIDTH - 350;
var LEGEND_Y = 100;
var EVENT_COLOR_MAP = {
    'line': '#1f77b4',
};
var ZOOM_DURATION = 250;
var NUMBARS_ZOOM = 100;

/** Renders memory stats legend. */
function renderLegend_(parent, data) {
  parent.append('div')
    .attr('class', 'legend')
    .html('<p>Filename: ' + data.programName + '</p>' +
          '<p>Total events: ' + data.totalEvents + '</p>')
    .style('left', LEGEND_X)
    .style('top', LEGEND_Y);
}

/** Processes stats from other events and returns them as formatted string. */
function processOtherEvents_(stats) {
  var result = '';
  if (stats) {
    var functionName = stats[3].replace('<', '[').replace('>',  ']');
    result += ('<p>Line number: ' + stats[0] + '</p>' +
               '<p>Function name: ' + functionName + '</p>' +
               '<p>Memory usage: ' + stats[1] + ' MB</p>');
  }
  return result;
}

/** Renders memory usage graph. */
function renderMemoryStats(data, parent) {
  var canvas = parent.append('svg')
    .attr('width', WIDTH + MARGIN_LEFT + MARGIN_RIGHT)
    .attr('height', HEIGHT + MARGIN_TOP + MARGIN_BOTTOM)
    .append("g")
    .attr("transform", "translate(" + MARGIN_LEFT + "," + MARGIN_TOP + ")");

  var yRange = d3.extent(data.codeEvents, function(d) { return d[1]; });
  var srcLines = data.codeEvents.map(function (_, i) { return i + 1; });
  var xScale = d3.scale.ordinal()
    .domain(srcLines)
    .rangeBands([0, WIDTH]);
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

  var tooltip = canvas.append('div')
    .attr('class', 'tooltip tooltip-invisible');

  renderLegend_(canvas, data);

  // Draw memory bars.
  var bars = barGroups.append('rect')
    .attr('class', 'memory-bar-normal')
    .attr("x", function(_, i) { return xScale(i + 1); })
    .attr("width", xScale.rangeBand())
    .attr("y", function(d) { return yScale(d[1]); })
    .attr("height", function(d) { return HEIGHT - yScale(d[1]); })
    .attr('fill', function(d) { return EVENT_COLOR_MAP[d[2]]; })
    .on('mouseover', function(d) {
      d3.select(this)
        .attr('class', 'memory-bar-highlight');
      var tooltipText = processOtherEvents_(d);
      tooltip.attr('class', 'tooltip tooltip-visible')
        .html(tooltipText)
        .style('left', d3.event.pageX)
        .style('top', d3.event.pageY);
    })
    .on('mouseout', function(_) {
      d3.select(this).attr('class', 'memory-bar-normal');
      tooltip.attr('class', 'tooltip tooltip-invisible');
    });

  // Zoom in.
  bars.on('click', function(d, i) {
    var range = srcLines.slice(i, i + 1 + NUMBARS_ZOOM);
    xScale.domain(range);
    bars.transition()
      .duration(ZOOM_DURATION)
      .attr("x", function(_, n) { return xScale(n + 1); })
      .attr("width", xScale.rangeBand())
      .style('display', function(_, n) {
          return range.indexOf(n + 1) == -1 ? 'none' : 'block'; });
  });

  // Zoom out.
  canvas.on('dblclick', function(d) {
    xScale.domain(srcLines);
    bars.transition()
      .duration(ZOOM_DURATION)
    .attr("x", function(_, n) { return xScale(n + 1); })
    .attr("width", xScale.rangeBand())
    .style('display', 'block');
  });

  // Draw axis.
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
