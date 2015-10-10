/**
 * Renders time profile.
 */

/* jshint strict: false, browser: true, globalstrict: true */
/* global require, module */

'use strict';
var d3 = require('d3');

var HEIGHT_SCALE = 0.9;
var HEIGHT = window.innerHeight * HEIGHT_SCALE;
var HEIGHT_OFFSET = 100;
var WIDTH_SCALE = 0.95;
var WIDTH = window.innerWidth * WIDTH_SCALE;
var ZOOM_DURATION = 250;
var TEXT_OFFSET_X = 5;
var TEXT_OFFSET_Y= 14;
var TEXT_CUTOFF = 0.075 * WIDTH;
var LEGEND_X = WIDTH - 400;
var LEGEND_Y = 100;
var LEGEND_DY = 15;
var LEGEND_HEIGHT = 68;
var LEGEND_WIDTH = 300;
var LEGEND_TEXT_OFFSET = 10;
var LEGEND_RADIUS_X = 10;
var LEGEND_RADIUS_Y = 10;

/** Returns full node name. */
function getNodeName_(d) {
  var tokens = d.moduleName.split('/');
  var filename = tokens[tokens.length - 1];
  return filename + ':' + d.lineno + '(' + d.funcName + ')';
}

/** Returns truncated node name */
function getTruncatedNodeName_(d, rectLength) {
  var fullname = getNodeName_(d);
  var maxSymbols = rectLength / 10;  // Approx. 10 pixels per character.
  if (maxSymbols <= 3) {
    return '';
  } else if (fullname.length > maxSymbols - 3) { // Full name minus ellipsis.
    return fullname.substr(0, maxSymbols) + '...';
  }
  return fullname;
}

/** Returns percentage of cumTime in totalTime. */
function getTimePercentage_(cumTime, totalTime) {
  return 100 * Math.round(cumTime / totalTime * 1000) / 1000;
}

/** Renders profile legend. */
function renderLegend_(parent, data) {
  var legend = parent.append('g')
    .attr('class', 'legend')
    .attr('x', LEGEND_X)
    .attr('y', LEGEND_Y)
    .attr('height', LEGEND_HEIGHT)
    .attr('width', LEGEND_WIDTH);

  legend.append('rect')
    .attr('class', 'tooltip-rect')
    .attr('x', LEGEND_X)
    .attr('y', LEGEND_Y)
    .attr('height', LEGEND_HEIGHT)
    .attr('width', LEGEND_WIDTH)
    .attr('rx', LEGEND_RADIUS_X)
    .attr('ry', LEGEND_RADIUS_Y);

  var legendText = legend.append('text')
    .attr("x", LEGEND_X + LEGEND_TEXT_OFFSET)
    .attr("y", LEGEND_Y);
  legendText.append('tspan')
    .attr('x', LEGEND_X + LEGEND_TEXT_OFFSET)
    .attr('dy', LEGEND_DY)
    .text('Program name: ' + data.programName);
  legendText.append('tspan')
    .attr('x', LEGEND_X + LEGEND_TEXT_OFFSET)
    .attr('dy', LEGEND_DY)
    .text('Total runtime: ' + data.runTime + 's');
  legendText.append('tspan')
    .attr('x', LEGEND_X + LEGEND_TEXT_OFFSET)
    .attr('dy', LEGEND_DY)
    .text('Total calls: ' + data.totalCalls);
  legendText.append('tspan')
    .attr('x', LEGEND_X + LEGEND_TEXT_OFFSET)
    .attr('dy', LEGEND_DY)
    .text('Primitive calls: ' + data.primitiveCalls);
}

// TODO (nvdv): Split this function.
/** Renders profile flame chart. */
function renderProfile(data, parent) {
  var color = d3.scale.category10();
  var chart =  parent.append('div')
    .attr('class', 'chart');

  var canvas = chart.append('svg')
    .attr('width', WIDTH)
    .attr('height', HEIGHT);

  var tooltip = chart.append('div')
    .attr('class', 'tooltip tooltip-invisible');

  renderLegend_(canvas, data);

  var flameChart = d3.layout.partition()
    .sort(null)
    .value(function(d) { return d.cumTime; });

  var cells = canvas.selectAll(".cell")
    .data(flameChart.nodes(data.callStats))
    .enter()
    .append('g')
    .attr('class', 'cell');

  // Render flame chart nodes.
  var xScale = d3.scale.linear().range([0, WIDTH]);
  var yScale = d3.scale.linear().range([0, HEIGHT]);
  var nodes = cells.append('rect')
    .attr('class', 'rect-normal')
    .attr('x', function(d) { return xScale(d.x); })
    .attr('y', function(d) { return yScale(1 - d.y - d.dy); })
    .attr('width', function(d) { return xScale(d.dx); })
    .attr('height', function(d) { return yScale(d.dy); })
    .style('fill', function(d) { return color(getNodeName_(d) + d.depth); })
    .on('mouseover', function(d) {
      d3.select(this)
        .attr('class', 'rect-highlight');
      var timePercentage = getTimePercentage_(d.cumTime, data.runTime);
      tooltip.attr('class', 'tooltip tooltip-visible')
        .html('<p>Function name: ' + d.funcName + '</p>' +
              '<p>Location: ' + d.moduleName +'</p>' +
              '<p>Time percentage: ' + timePercentage + ' %</p>' +
              '<p>Cum.time: ' + d.cumTime + ' s</p>' +
              '<p>Time per call: ' + d.timePerCall + ' s</p>' +
              '<p>Primitive calls: ' + d.primCalls + '</p>')
        .style('left', d3.event.pageX)
        .style('top', d3.event.pageY);
    })
    .on('mouseout', function(d) {
      d3.select(this)
        .attr('class', 'rect-normal');
      tooltip.attr('class', 'tooltip tooltip-invisible');
    });

  // Render flame chart headers.
  var titles = cells.append('text')
    .attr('x', function(d) { return xScale(d.x) + TEXT_OFFSET_X; })
    .attr('y', function(d) { return yScale(1 - d.y - d.dy) + TEXT_OFFSET_Y; })
    .text(function(d) {
      var nodeWidth = this.previousElementSibling.getAttribute('width');
      return getTruncatedNodeName_(d, nodeWidth);
    });


  // Zoom in.
  nodes.on('click', function(d) {
    xScale.domain([d.x, d.x + d.dx]);
    yScale.domain([0, 1 - d.y]).range([0, HEIGHT]);

    nodes.transition()
      .duration(ZOOM_DURATION)
      .attr('x', function(d) { return xScale(d.x); })
      .attr('y', function(d) { return yScale(1 - d.y - d.dy); })
      .attr('width', function(d) { return xScale(d.x + d.dx) - xScale(d.x); })
      .attr('height', function(d) {
        return yScale(1 - d.y) - yScale(1 - d.y - d.dy);
      });

    titles.transition()
      .duration(ZOOM_DURATION)
      .attr('x', function(d) { return xScale(d.x) + TEXT_OFFSET_X; })
      .attr('y', function(d) {
        return yScale(1 - d.y - d.dy) + TEXT_OFFSET_Y;
      })
      .text(function(d) {
        var nodeWidth = xScale(d.x + d.dx) - xScale(d.x);
        return getTruncatedNodeName_(d, nodeWidth);
      });
  });

  // Zoom out.
  canvas.on('dblclick', function(d) {
    xScale.domain([0, 1]);
    yScale.domain([0, 1]);
    nodes.transition()
      .duration(ZOOM_DURATION)
    .attr('x', function(d) { return xScale(d.x); })
    .attr('y', function(d) { return yScale(1 - d.y - d.dy); })
    .attr('width', function(d) { return xScale(d.dx); })
    .attr('height', function(d) { return yScale(d.dy); });

    titles.transition()
      .duration(ZOOM_DURATION)
      .attr('x', function(d) { return xScale(d.x) + TEXT_OFFSET_X; })
      .attr('y', function(d) {
        return yScale(1 - d.y - d.dy) + TEXT_OFFSET_Y;
      })
      .text(function(d) {
        var nodeWidth = xScale(d.x + d.dx) - xScale(d.x);
        return getTruncatedNodeName_(d, nodeWidth);
      });
  });
}

module.exports = {
  'getNodeName_': getNodeName_,
  'getTruncatedNodeName_': getTruncatedNodeName_,
  'renderProfile': renderProfile,
};