/**
 * Renders memory stats.
 */

/* jshint strict: false, browser: true, globalstrict: true */
/* global require, module */

'use strict';
var d3 = require('d3');

var MARGIN_LEFT = 35;
var MARGIN_RIGHT = 0;
var MARGIN_TOP = 10;
var MARGIN_BOTTOM  = 30;
var SCALE = 0.95;
var FULL_HEIGHT = window.innerHeight * SCALE;
var FULL_WIDTH = window.innerWidth * SCALE;
var GRAPH_HEIGHT = FULL_HEIGHT - (MARGIN_LEFT + MARGIN_RIGHT) * SCALE;
var GRAPH_WIDTH = FULL_WIDTH - (MARGIN_TOP + MARGIN_BOTTOM) * SCALE;
var MIN_RANGE_C = 0.98;
var MAX_RANGE_C = 1.02;
var AXIS_TEXT_X = GRAPH_WIDTH;
var AXIS_TEXT_Y = 12;
var AXIS_TEXT_Y_OFFSET = 30;
var LEGEND_X = GRAPH_WIDTH - 350;
var LEGEND_Y = 100;
var MOUSE_X_OFFSET = 10;
var TICKS_NUMBER = 10;
var FOCUS_RADIUS = 5;
var DOT_RADIUS = 3;
var TOOLTIP_OFFSET = 20;
var SCALE_FACTOR = 3;

/** Renders memory stats legend. */
function renderLegend_(parent, data) {
  parent.append('div')
    .attr('class', 'legend')
    .html('<p>Filename: ' + data.programName + '</p>' +
          '<p>Total lines executed: ' + data.totalEvents + '</p>')
    .style('left', LEGEND_X)
    .style('top', LEGEND_Y);
}

/** Generates tooltip text from line stats. */
function generateTooltipText_(stats) {
  var result = '';
  if (stats) {
    var functionName = stats[3].replace('<', '[').replace('>',  ']');
    result += ('<p>Executed line: ' + stats[0] + '</p>' +
               '<p>Line number: ' + stats[1] + '</p>' +
               '<p>Function name: ' + functionName + '</p>' +
               '<p>Memory usage: ' + stats[2] + ' MB</p>');
  }
  return result;
}

/** Calculates params of zoomed region on memory graph. */
function getZoomRangeParams_(midIndex, indexRange, maxLength) {
  var startIndex = midIndex - Math.floor(
      (indexRange / SCALE_FACTOR) * 0.5);
  var endIndex = midIndex + Math.floor(
      (indexRange / SCALE_FACTOR) * 0.5);
  return {
    'startIndex': Math.max(startIndex, 0),
    'endIndex': Math.min(endIndex, maxLength),
    'indexRange': endIndex - startIndex
  };
}

/** Renders memory usage graph. */
function renderMemoryStats(data, parent) {
  var canvas = parent.append('svg')
    .attr('width', FULL_WIDTH)
    .attr('height', FULL_HEIGHT)
    .append('g')
    .attr('transform', 'translate(' + MARGIN_LEFT + ',' + MARGIN_TOP + ')');

  var xScale = d3.scale.linear()
    .domain(d3.extent(data.codeEvents, function(d) { return d[0]; }))
    .range([0, GRAPH_WIDTH]);

  var yRange = d3.extent(data.codeEvents, function(d) { return d[2]; });
  var yScale = d3.scale.linear()
    .domain([MIN_RANGE_C * yRange[0], MAX_RANGE_C * yRange[1]])
    .range([GRAPH_HEIGHT, 0]);

  var xAxis = d3.svg.axis()
    .scale(xScale)
    .ticks(Math.min(TICKS_NUMBER, data.codeEvents.length))
    .tickFormat(d3.format(',.0f'))
    .orient('bottom');

  var yAxis = d3.svg.axis()
    .scale(yScale)
    .orient('left');

  var tooltip = parent.append('div')
    .attr('class', 'tooltip tooltip-invisible');

  renderLegend_(parent, data);

  var memoryGraph = d3.svg.area()
    .x(function(d) { return xScale(d[0]); })
    .y0(GRAPH_HEIGHT)
    .y1(function(d) { return yScale(d[2]); });

  var path = canvas.append('path')
    .attr('class', 'memory-graph')
    .attr('d', memoryGraph(data.codeEvents));

  var focus = canvas.append('circle')
    .style('display', 'none')
    .attr('class', 'memory-graph-focus')
    .attr('r', FOCUS_RADIUS)
    .attr('transform', 'translate(' + (-100) + ', '  + (-100) + ')');

  var focusXLine = canvas.append('line')
    .attr('class', 'focus-line')
    .attr('y1', GRAPH_HEIGHT);

  var focusYLine = canvas.append('line')
    .attr('class', 'focus-line')
    .attr('x1', 0);

  canvas.style('pointer-events', 'all')
    .on('mouseover', function() {
      focus.style('display', null);
      focusXLine.style('display', null);
      focusYLine.style('display', null);
    })
    .on('mouseout', function() {
      focus.style('display', 'none');
      tooltip.attr('class', 'tooltip tooltip-invisible');
      focusXLine.style('display', 'none');
      focusYLine.style('display', 'none');
    })
    .on('mousemove', function() {
      var crds = d3.mouse(canvas.node());
      var closestIndex = Math.round(xScale.invert(crds[0])) - 1;
      var closestX = xScale(data.codeEvents[closestIndex][0]);
      var closestY = yScale(data.codeEvents[closestIndex][2]);
      focus.attr('transform', 'translate(' + closestX + ', ' +
                  closestY + ')');
      focusXLine.attr('x1', closestX)
        .attr('x2', closestX)
        .attr('y2', closestY);
      focusYLine.attr('y1', closestY)
        .attr('x2', closestX)
        .attr('y2', closestY);
      var tooltipText = generateTooltipText_(data.codeEvents[closestIndex]);
      tooltip.attr('class', 'tooltip tooltip-visible')
        .html(tooltipText)
        .style('left', closestX)
        .style('top', closestY - TOOLTIP_OFFSET);
    });

  // Draw axes.
  canvas.append('g')
    .attr('class', 'x axis')
    .attr('transform', 'translate(0,' + GRAPH_HEIGHT + ')')
    .call(xAxis)
    .append('text')
    .attr('x', AXIS_TEXT_X)
    .attr('y', AXIS_TEXT_Y - AXIS_TEXT_Y_OFFSET)
    .attr('dy', '.71em')
    .text('Executed lines');

  canvas.append('g')
    .attr('class', 'y axis')
    .call(yAxis)
    .append('text')
    .attr('transform', 'rotate(-90)')
    .attr('y', AXIS_TEXT_Y)
    .attr('dy', '.71em')
    .text('Memory usage, MB');

  // Zoom in.
  var indexRange = data.codeEvents.length;
  canvas.on('click', function(d) {
    var crds = d3.mouse(canvas.node());
    var midIndex = Math.round(xScale.invert(crds[0])) - 1;
    var range = getZoomRangeParams_(
        midIndex, indexRange, data.codeEvents.length - 1);
    indexRange = range.indexRange;
    if (range.startIndex < range.endIndex) {
      if (indexRange < TICKS_NUMBER) {
        xAxis.ticks(indexRange);
      }
      xScale.domain([data.codeEvents[range.startIndex][0],
                     data.codeEvents[range.endIndex][0]]);
      var eventsSlice = data.codeEvents.slice(
          range.startIndex, range.endIndex + 1);
      path.attr('d', memoryGraph(eventsSlice));
      canvas.selectAll('g.x.axis')
        .call(xAxis);

      var closestX = xScale(data.codeEvents[midIndex][0]);
      var closestY = yScale(data.codeEvents[midIndex][2]);
      focus.attr('transform', 'translate(' + closestX + ', ' +
                  closestY + ')');
      focusXLine.attr('x1', closestX)
        .attr('x2', closestX)
        .attr('y2', closestY);
      focusYLine.attr('y1', closestY)
        .attr('x2', closestX)
        .attr('y2', closestY);
      var tooltipText = generateTooltipText_(data.codeEvents[midIndex]);
      tooltip.attr('class', 'tooltip tooltip-visible')
        .html(tooltipText)
        .style('left', closestX)
        .style('top', closestY - TOOLTIP_OFFSET);
    }
  });

  // Zoom out.
  parent.on('dblclick', function(d) {
    xScale.domain(d3.extent(data.codeEvents, function(d) { return d[0]; }));
    path.attr('d', memoryGraph(data.codeEvents));
    xAxis.ticks(Math.min(TICKS_NUMBER, data.codeEvents.length));
    canvas.selectAll('g.x.axis')
      .call(xAxis);
  });
}

module.exports = {
  'renderMemoryStats': renderMemoryStats,
};
