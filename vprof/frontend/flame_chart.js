/**
 * @file CPU flame chart rendering.
 */

/* jshint strict: false, browser: true, globalstrict: true */
/* global require, module */

'use strict';
var d3 = require('d3');

/**
 * Represents CPU flame chart.
 * @constructor
 * @param {Object} parent - Parent element for flame chart.
 * @param {Object} data - Data for flame chart rendering.
 */
function FlameChart(parent, data) {
  this.PAD_SIZE = 10;
  this.HEIGHT = parent.node().scrollHeight - this.PAD_SIZE;
  this.WIDTH = parent.node().scrollWidth - this.PAD_SIZE;
  this.TEXT_OFFSET_X = 5;
  this.TEXT_OFFSET_Y= 14;
  this.TEXT_CUTOFF = 0.075 * this.WIDTH;
  this.LEGEND_X = this.WIDTH - 400;
  this.LEGEND_Y = 100;

  this.data_ = data;
  this.parent_ = parent;
  this.xScale_ = d3.scale.linear().range([0, this.WIDTH]);
  this.yScale_ = d3.scale.linear().range([0, this.HEIGHT]);
  this.color_ = d3.scale.category10();
  this.flameChart_ = d3.layout.partition()
    .sort(null)
    .value(function(d) { return d.cumTime; });
}

/** Renders flame chart. */
FlameChart.prototype.render = function() {
  var canvas = this.parent_.append('svg')
    .attr('width', this.WIDTH)
    .attr('height', this.HEIGHT);

  var tooltip = this.parent_.append('div')
    .attr('class', 'tooltip tooltip-invisible');

  this.renderLegend_();

  var cells = canvas.selectAll(".cell")
    .data(this.flameChart_.nodes(this.data_.callStats))
    .enter()
    .append('g')
    .attr('class', 'cell');

  // Render flame chart nodes.
  var self = this;
  var nodes = cells.append('rect')
    .attr('class', 'rect-normal')
    .attr('x', function(d) { return self.xScale_(d.x); })
    .attr('y', function(d) { return self.yScale_(1 - d.y - d.dy); })
    .attr('width', function(d) { return self.xScale_(d.dx); })
    .attr('height', function(d) { return self.yScale_(d.dy); })
    .style('fill', function(d) {
      return self.color_(FlameChart.getNodeName_(d) + d.depth); })
    .on('mouseover', function(d) { self.showTooltip_(this, tooltip, d); })
    .on('mouseout', function() { self.hideTooltip_(this, tooltip); });

  var titles = cells.append('text')
    .attr('x', function(d) { return self.xScale_(d.x) + self.TEXT_OFFSET_X; })
    .attr('y', function(d) {
      return self.yScale_(1 - d.y - d.dy) + self.TEXT_OFFSET_Y; })
    .text(function(d) {
      var nodeWidth = this.previousElementSibling.getAttribute('width');
      return FlameChart.getTruncatedNodeName_(d, nodeWidth);
    });

    // Zoom.
    nodes.on('click', function(d) { self.zoomIn_(d, nodes, titles); });
    canvas.on('dblclick', function(d) { self.zoomOut_(nodes, titles); });
};

/**
 * Handles zoom in.
 * @param {Object} node - Focus node.
 * @param {Object} allNodes - All flame chart nodes.
 * @param {Object} titles - All flame chart node titles.
 */
FlameChart.prototype.zoomIn_ = function(node, allNodes, titles) {
  this.xScale_.domain([node.x, node.x + node.dx]);
  this.yScale_.domain([0, 1 - node.y]).range([0, this.HEIGHT]);
  var self = this;
  allNodes.attr('x', function(d) { return self.xScale_(d.x); })
    .attr('y', function(d) { return self.yScale_(1 - d.y - d.dy); })
    .attr('width', function(d) {
      return self.xScale_(d.x + d.dx) - self.xScale_(d.x); })
    .attr('height', function(d) {
      return self.yScale_(1 - d.y) - self.yScale_(1 - d.y - d.dy); });
  this.redrawTitles_(titles);
};

/**
 * Handles zoom out.
 * @param {Object} allNodes - All flame chart nodes.
 * @param {Object} titles - All flame chart node titles.
 */
FlameChart.prototype.zoomOut_ = function(allNodes, titles) {
  this.xScale_.domain([0, 1]);
  this.yScale_.domain([0, 1]);
  var self = this;
  allNodes.attr('x', function(d) { return self.xScale_(d.x); })
    .attr('y', function(d) { return self.yScale_(1 - d.y - d.dy); })
    .attr('width', function(d) { return self.xScale_(d.dx); })
    .attr('height', function(d) { return self.yScale_(d.dy); });
  this.redrawTitles_(titles);
};

/**
 * Redraws node titles based on current xScale and yScale.
 * @param {Object} titles - All flame chart node titles.
 */
FlameChart.prototype.redrawTitles_ = function(titles) {
  var self = this;
  titles.attr('x', function(d) { return self.xScale_(d.x) + self.TEXT_OFFSET_X; })
    .attr('y', function(d) {
      return self.yScale_(1 - d.y - d.dy) + self.TEXT_OFFSET_Y; })
    .text(function(d) {
      var nodeWidth = self.xScale_(d.x + d.dx) - self.xScale_(d.x);
      return FlameChart.getTruncatedNodeName_(d, nodeWidth);
    });
};

/**
 * Shows tooltip and flame graph rectangle highlighting.
 * @param {Object} element - Element representing flame chart rectangle.
 * @param {Object} tooltip - Element representing tooltip.
 * @param {Object} node - Object representing function call info.
 */
FlameChart.prototype.showTooltip_ = function(element, tooltip, node) {
  d3.select(element).attr('class', 'rect-highlight');
  var timePercentage = FlameChart.getTimePercentage_(
      node.cumTime, this.data_.runTime);
  var functionName = node.funcName.replace('<', '[').replace('>',  ']');
  tooltip.attr('class', 'tooltip tooltip-visible')
    .html('<p>Function name: ' + functionName + '</p>' +
          '<p>Location: ' + node.moduleName +'</p>' +
          '<p>Time percentage: ' + timePercentage + ' %</p>' +
          '<p>Cumulative time: ' + node.cumTime + ' s</p>' +
          '<p>Time per call: ' + node.timePerCall + ' s</p>' +
          '<p>Primitive calls: ' + node.primCalls + '</p>')
    .style('left', d3.event.pageX)
    .style('top', d3.event.pageY);
};

/**
 * Hides tooltip and removes rect highlighting.
 * @param {Object} element - Element representing highlighted rectangle.
 * @param {Object} tooltip - Element representing tooltip.
 */
FlameChart.prototype.hideTooltip_ = function(element, tooltip) {
  d3.select(element).attr('class', 'rect-normal');
  tooltip.attr('class', 'tooltip tooltip-invisible');
};

/** Renders flame chart legend. */
FlameChart.prototype.renderLegend_ = function() {
  this.parent_.append('div')
    .attr('class', 'legend')
    .html('<p>Filename: ' + this.data_.programName + '</p>' +
          '<p>Total runtime: ' + this.data_.runTime + 's</p>' +
          '<p>Total calls: ' + this.data_.totalCalls + '</p>' +
          '<p>Primitive calls: ' + this.data_.primitiveCalls + '</p>')
    .style('left', this.LEGEND_X)
    .style('top', this.LEGEND_Y);
};

/**
 * Returns function info.
 * @static
 * @param {Object} d - Object representing function call info.
 * @returns {string}
 */
FlameChart.getNodeName_ = function(d) {
  var tokens = d.moduleName.split('/');
  var filename = tokens[tokens.length - 1];
  return filename + ':' + d.lineno + '(' + d.funcName + ')';
};

/**
 * Truncates function name depending on flame chart rectangle length.
 * @static
 * @param (Object) d - Object representing function info.
 * @param {number} rectLength - Length of flame chart rectangle.
 * @returns {string}
 */
FlameChart.getTruncatedNodeName_ = function(d, rectLength) {
  var fullname = FlameChart.getNodeName_(d);
  var maxSymbols = rectLength / 10;  // Approx. 10 pixels per character.
  if (maxSymbols <= 3) {
    return '';
  } else if (fullname.length > maxSymbols - 3) { // Full name minus ellipsis.
    return fullname.substr(0, maxSymbols) + '...';
  }
  return fullname;
};

/**
 * Returns percentage that cumTime takes in totalTime.
 * @static
 * @param {number} cumTime - Function cumulative run time.
 * @param {number} totalTime - Program run time.
 * @returns {number}
 */
FlameChart.getTimePercentage_ = function(cumTime, totalTime) {
  return 100 * Math.round(cumTime / totalTime * 1000) / 1000;
};

/**
 * Renders flame chart and attaches it to parent.
 * @param {Object} parent - Parent element for flame chart.
 * @param {Object} data - Data for flame chart rendering.
 */
function renderFlameChart(data, parent) {
  var flameChart = new FlameChart(parent, data);
  flameChart.render();
}

module.exports = {
  'FlameChart': FlameChart,
  'renderFlameChart': renderFlameChart,
};
