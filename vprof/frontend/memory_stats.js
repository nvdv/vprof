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
    'gc': '#ff7f0e',
};
var GC_EVENT = 'gc';
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

/** Processes GC stats and returns them as formatted string. */
function processGCStats_(stats) {
  var result = '';
  if (stats) {
    result += '<p>GC runs: ' + stats.length + '</p>';
    for (var i = 0; i < stats.length; i++) {
      result += (
          '<p>Run:' + (i + 1) + '</p>' +
          '<p>Objects in generations: ' + stats[i].objInGenerations + '</p>'+
          '<p>Time elapsed: ' + stats[i].timeElapsed + '</p>');
      if (stats[i].uncollectable) {
        result += '<p>Uncollectable: ' + stats[i].uncollectable + '</p>';
      }
      if (stats[i].unreachable) {
        result += '<p>Unreachable: ' + stats[i].unreachable + '</p>';
      }
    }
  }
  return result;
}

/** Processes stats from other events and returns them as formatted string. */
function processOtherEvents_(stats) {
  var result = '';
  if (stats) {
    var functionName = stats[4].replace('<', '[').replace('>',  ']');
    result += ('<p>Line number: ' + stats[1] + '</p>' +
               '<p>Event type: ' + stats[3] + '</p>' +
               '<p>Function name: ' + functionName + '</p>' +
               '<p>Memory usage: ' + stats[2] + ' MB</p>');
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

  var yRange = d3.extent(data.codeEvents, function(d) { return d[2]; });
  var srcLines = data.codeEvents.map(function(d) { return d[0]; });
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

  var tooltip = chart.append('div')
    .attr('class', 'tooltip tooltip-invisible');

  renderLegend_(chart, data);

  // Draw memory bars.
  var bars = barGroups.append('rect')
    .attr('class', 'memory-bar-normal')
    .attr("x", function(d) { return xScale(d[0]); })
    .attr("width", xScale.rangeBand())
    .attr("y", function(d) { return yScale(d[2]); })
    .attr("height", function(d) { return HEIGHT - yScale(d[2]); })
    .attr('fill', function(d) { return EVENT_COLOR_MAP[d[3]]; })
    .on('mouseover', function(d) {
      d3.select(this)
        .attr('class', 'memory-bar-highlight');
      var tooltipText = d[3] == GC_EVENT ?
        processGCStats_(d[4]) : processOtherEvents_(d);
      tooltip.attr('class', 'tooltip tooltip-visible')
        .html(tooltipText)
        .style('left', d3.event.pageX)
        .style('top', d3.event.pageY);
    })
    .on('mouseout', function(d) {
      d3.select(this).attr('class', 'memory-bar-normal');
      tooltip.attr('class', 'tooltip tooltip-invisible');
    });

  // Zoom in.
  bars.on('click', function(d, i) {
    var range = srcLines.slice(i, i + 1 + NUMBARS_ZOOM);
    xScale.domain(range);
    bars.transition()
      .duration(ZOOM_DURATION)
      .attr("x", function(d) { return xScale(d[0]); })
      .attr("width", xScale.rangeBand())
      .style('display', function(d) {
          return range.indexOf(d[0]) == -1 ? 'none' : 'block'; });
  });

  // Zoom out.
  chart.on('dblclick', function(d) {
    xScale.domain(srcLines);
    bars.transition()
      .duration(ZOOM_DURATION)
    .attr("x", function(d) { return xScale(d[0]); })
    .attr("width", xScale.rangeBand())
    .attr('display', 'block');
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
