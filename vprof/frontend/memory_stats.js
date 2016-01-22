/**
 * Renders memory stats.
 */

/* jshint strict: false, browser: true, globalstrict: true */
/* global require, module */

'use strict';
var d3 = require('d3');

var MARGIN_LEFT = 35;
var MARGIN_RIGHT = 0;
var MARGIN_TOP = 5;
var MARGIN_BOTTOM  = 30;
var SCALE = 0.95;
var FULL_HEIGHT = window.innerHeight * SCALE;
var FULL_WIDTH = window.innerWidth * SCALE;
var GRAPH_HEIGHT = FULL_HEIGHT - (MARGIN_LEFT + MARGIN_RIGHT) * SCALE;
var GRAPH_WIDTH = FULL_WIDTH - (MARGIN_TOP + MARGIN_BOTTOM) * SCALE;
var MIN_RANGE_C = 0.95;
var MAX_RANGE_C = 1.05;
var AXIS_TEXT_X = GRAPH_WIDTH;
var AXIS_TEXT_Y = 12;
var AXIS_TEXT_Y_OFFSET = 30;
var LEGEND_X = GRAPH_WIDTH - 350;
var LEGEND_Y = 100;
var MOUSE_X_OFFSET = 10;
var TICKS_NUMBER = 10;
var CIRCLE_RADIUS = 5;
var TOOLTIP_OFFSET = 20;

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
function generateTooltipText_(executedLine, stats) {
  var result = '';
  if (stats) {
    var functionName = stats[3].replace('<', '[').replace('>',  ']');
    result += ('<p>Executed line: ' + executedLine + '</p>' +
               '<p>Line number: ' + stats[0] + '</p>' +
               '<p>Function name: ' + functionName + '</p>' +
               '<p>Memory usage: ' + stats[1] + ' MB</p>');
  }
  return result;
}

/** Renders memory usage graph. */
function renderMemoryStats(data, parent) {
  var canvas = parent.append('svg')
    .attr('width', FULL_WIDTH)
    .attr('height', FULL_HEIGHT)
    .append("g")
    .attr("transform", "translate(" + MARGIN_LEFT + "," + MARGIN_TOP + ")");

  var srcLines = data.codeEvents.map(function (_, i) { return i + 1; });
  var xScale = d3.scale.linear()
    .domain([srcLines[0], srcLines[srcLines.length - 1]])
    .range([0, GRAPH_WIDTH]);

  var yRange = d3.extent(data.codeEvents, function(d) { return d[1]; });
  var yScale = d3.scale.linear()
    .domain([MIN_RANGE_C * yRange[0], MAX_RANGE_C * yRange[1]])
    .range([GRAPH_HEIGHT, 0]);

  var xAxis = d3.svg.axis()
    .scale(xScale)
    .ticks(Math.min(TICKS_NUMBER, srcLines.length))
    .tickFormat(d3.format(",.0f"))
    .orient("bottom");

  var yAxis = d3.svg.axis()
    .scale(yScale)
    .orient('left');

  var tooltip = parent.append('div')
    .attr('class', 'tooltip tooltip-invisible');

  renderLegend_(parent, data);

  var memoryGraph = d3.svg.area()
    .x(function (_, i) { return xScale(i + 1); })
    .y0(GRAPH_HEIGHT)
    .y1(function (d) { return yScale(d[1]); });

  canvas.append('path')
    .datum(data.codeEvents)
    .attr('class', 'memory-graph')
    .attr('d', memoryGraph);

  var circle = canvas.append("circle")
    .style('display', 'none')
    .attr('class', 'memory-graph-dot')
    .attr("r", CIRCLE_RADIUS)
    .attr('transform', 'translate(' + (-100) + ', '  + (-100) + ')');

  canvas.style("pointer-events", "all")
    .on("mouseover", function() { circle.style("display", null); })
    .on("mouseout", function() {
      circle.style("display", "none");
      tooltip.attr('class', 'tooltip tooltip-invisible');
    })
    .on("mousemove", function() {
      var crds = d3.mouse(canvas.node());
      var closestIndex = Math.round(xScale.invert(crds[0] - MOUSE_X_OFFSET));
      var closestX = xScale(closestIndex);
      var closestY = yScale(data.codeEvents[closestIndex - 1][1]);
      circle.attr('transform', 'translate(' + closestX + ', ' +
                  closestY + ')');
      var tooltipText = generateTooltipText_(closestIndex,
          data.codeEvents[closestIndex - 1]);
      tooltip.attr('class', 'tooltip tooltip-visible')
        .html(tooltipText)
        .style('left', closestX)
        .style('top', closestY - TOOLTIP_OFFSET);
    });

  // Draw axes.
  canvas.append("g")
    .attr("class", "axis")
    .attr("transform", "translate(0," + GRAPH_HEIGHT + ")")
    .call(xAxis)
    .append('text')
    .attr('x', AXIS_TEXT_X)
    .attr('y', AXIS_TEXT_Y - AXIS_TEXT_Y_OFFSET)
    .attr('dy', '.71em')
    .text('Executed lines');

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
