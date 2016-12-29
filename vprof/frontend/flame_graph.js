/**
 * @file CPU flame graph rendering.
 */

'use strict';
var d3hierarchy = require('d3-hierarchy');
var d3scale = require('d3-scale');
var d3select = require('d3-selection');

/**
 * Represents CPU flame graph.
 * @constructor
 * @param {Object} parent - Parent element for flame graph.
 * @param {Object} data - Data for flame graph rendering.
 */
function FlameGraph(parent, data) {
  this.PAD_SIZE = 10;
  this.HEIGHT = parent.node().scrollHeight - this.PAD_SIZE;
  this.WIDTH = parent.node().scrollWidth - this.PAD_SIZE;
  this.TEXT_OFFSET_X = 5;
  this.TEXT_OFFSET_Y= 14;
  this.TEXT_CUTOFF = 0.075 * this.WIDTH;
  this.LEGEND_X = this.WIDTH - 400;
  this.LEGEND_Y = 100;
  this.MIN_TEXT_HEIGHT = 18;
  this.HELP_MESSAGE = (
    '<p>&#8226 Hover over node to see node stats</p>' +
    '<p>&#8226 Click on node to zoom</p>'+
    '<p>&#8226 Double click to restore original scale</p>');
  this.NO_DATA_MESSAGE = (
    'Sorry, no samples. Seems like run time is less than sampling interval.');

  this.data_ = data;
  this.parent_ = parent;
  this.xScale_ = d3scale.scaleLinear().domain([0, 1]).range([0, this.WIDTH]);
  this.yScale_ = d3scale.scaleLinear().range([0, this.HEIGHT]);
  this.flameGraph_ = d3hierarchy.partition();

  var hashDomain = [];
  var max = Math.pow(2, 24) - 1;
  var parts = 5;
  for (var i = 0; i < parts; i++) {
    hashDomain.push(i * max / parts);
  }

  this.color_ = d3scale.scaleLinear()
    .domain(hashDomain)
    .range(['#a6611a', '#dfc27d', '#f5f5f5', '#80cdc1', '#018571']);
}

/** Renders flame graph. */
FlameGraph.prototype.render = function() {
  var canvas = this.parent_.append('svg')
    .attr('width', this.WIDTH)
    .attr('height', this.HEIGHT);

  var tooltip = this.parent_.append('div')
    .attr('class', 'content-tooltip content-tooltip-invisible');

  this.renderLegend_();
  this.renderHelp_();

  // Display message and stop if callStats is empty.
  if (Object.keys(this.data_.callStats).length === 0) {
    this.renderNoDataMessage_();
    return;
  }

  var nodes = d3hierarchy.hierarchy(this.data_.callStats)
    .each(function(d) { d.value = d.data.sampleCount; });

  this.flameGraph_(nodes);

  var cells = canvas.selectAll('.flame-graph-cell')
    .data(nodes.descendants())
    .enter()
    .append('g')
    .attr('class', 'flame-graph-cell');

  // Render flame graph nodes.
  var self = this;
  var nodes = cells.append('rect')
    .attr('class', 'flame-graph-rect-normal')
    .attr('x', function(d) { return self.xScale_(d.x0); })
    .attr('y', function(d) { return self.yScale_(1 - d.y0 - (d.y1 - d.y0)); })
    .attr('width', function(d) { return self.xScale_(d.x1 - d.x0); })
    .attr('height', function(d) { return self.yScale_(d.y1 - d.y0); })
    .style('fill', function(d) { return self.color_(d.data.colorHash); })
    .on('mouseover', function(d) { self.showTooltip_(this, tooltip, d.data); })
    .on('mouseout', function() { self.hideTooltip_(this, tooltip); });

  var titles = cells.append('text')
    .attr('x', function(d) { return self.xScale_(d.x0) + self.TEXT_OFFSET_X; })
    .attr('y', function(d) {
      return self.yScale_(1 - d.y0 - (d.y1 - d.y0)) + self.TEXT_OFFSET_Y; })
    .text(function(d) {
      var nodeWidth = this.previousElementSibling.getAttribute('width');
      return FlameGraph.getTruncatedNodeName_(d.data, nodeWidth); })
    .attr('visibility', function(d) {
      var nodeHeight = this.previousElementSibling.getAttribute('height');
      return nodeHeight > self.MIN_TEXT_HEIGHT ? 'visible': 'hidden';
    });

  // Zoom.
  nodes.on('click', function(d) { self.zoomIn_(d, nodes, titles); });
  canvas.on('dblclick', function(d) { self.zoomOut_(nodes, titles); });
};

/**
 * Handles zoom in.
 * @param {Object} node - Focus node.
 * @param {Object} allNodes - All flame graph nodes.
 * @param {Object} titles - All flame graph node titles.
 */
FlameGraph.prototype.zoomIn_ = function(node, allNodes, titles) {
  this.xScale_.domain([node.x0, node.x0 + node.x1 - node.x0]);
  this.yScale_.domain([0, 1 - node.y0]);
  var self = this;
  allNodes.attr('x', function(d) { return self.xScale_(d.x0); })
    .attr('y', function(d) { return self.yScale_(1 - d.y0 - (d.y1 - d.y0)); })
    .attr('width', function(d) {
      return self.xScale_(d.x0 + d.x1 - d.x0) - self.xScale_(d.x0); })
    .attr('height', function(d) {
      return self.yScale_(1 - d.y0) -
             self.yScale_(1 - d.y0 - (d.y1 - d.y0)); });
  this.redrawTitles_(titles);
};

/**
 * Handles zoom out.
 * @param {Object} allNodes - All flame graph nodes.
 * @param {Object} titles - All flame graph node titles.
 */
FlameGraph.prototype.zoomOut_ = function(allNodes, titles) {
  this.xScale_.domain([0, 1]);
  this.yScale_.domain([0, 1]);
  var self = this;
  allNodes.attr('x', function(d) { return self.xScale_(d.x0); })
    .attr('y', function(d) { return self.yScale_(1 - d.y0 - (d.y1 - d.y0)); })
    .attr('width', function(d) { return self.xScale_(d.x1 - d.x0); })
    .attr('height', function(d) { return self.yScale_(d.y1 - d.y0); });
  this.redrawTitles_(titles);
};

/**
 * Redraws node titles based on current xScale and yScale.
 * @param {Object} titles - All flame graph node titles.
 */
FlameGraph.prototype.redrawTitles_ = function(titles) {
  var self = this;
  titles.attr('x', function(d) {
    return self.xScale_(d.x0) + self.TEXT_OFFSET_X; })
    .attr('y', function(d) {
      return self.yScale_(1 - d.y0 - (d.y1 - d.y0)) + self.TEXT_OFFSET_Y; })
    .text(function(d) {
      var nodeWidth = self.xScale_(d.x0 + d.x1 - d.x0) - self.xScale_(d.x0);
      return FlameGraph.getTruncatedNodeName_(d.data, nodeWidth); })
    .attr('visibility', function(d) {
      var nodeHeight = this.previousElementSibling.getAttribute('height');
      return (nodeHeight > self.MIN_TEXT_HEIGHT) ? 'visible': 'hidden';
    });
};

/**
 * Shows tooltip and flame graph node highlighting.
 * @param {Object} element - Element representing flame graph node.
 * @param {Object} tooltip - Element representing tooltip.
 * @param {Object} node - Object representing function call info.
 */
FlameGraph.prototype.showTooltip_ = function(element, tooltip, node) {
  d3select.select(element).attr('class', 'flame-graph-rect-highlight');
  tooltip.attr('class', 'content-tooltip content-tooltip-visible')
    .html('<p><b>Function name:</b> ' + node.stack[0] + '</p>' +
          '<p><b>Line number:</b> ' + node.stack[2] +'</p>' +
          '<p><b>Filename:</b> ' + node.stack[1] +'</p>' +
          '<p><b>Sample count:</b> ' + node.sampleCount + '</p>' +
          '<p><b>Percentage:</b> ' + node.stack[3] +'%</p>')
    .style('left', d3select.event.pageX)
    .style('top', d3select.event.pageY);
};

/**
 * Hides tooltip and removes node highlighting.
 * @param {Object} element - Element representing highlighted rectangle.
 * @param {Object} tooltip - Element representing tooltip.
 */
FlameGraph.prototype.hideTooltip_ = function(element, tooltip) {
  d3select.select(element).attr('class', 'flame-graph-rect-normal');
  tooltip.attr('class', 'content-tooltip content-tooltip-invisible');
};

/** Renders flame graph legend. */
FlameGraph.prototype.renderLegend_ = function() {
  this.parent_.append('div')
    .attr('class', 'content-legend')
    .html('<p><b>Object name:</b> ' + this.data_.objectName + '</p>' +
          '<p><b>Run time:</b> ' + this.data_.runTime + ' s</p>' +
          '<p><b>Total samples:</b> ' + this.data_.totalSamples + '</p>' +
          '<p><b>Sample interval:</b> ' + this.data_.sampleInterval + ' s</p>')
    .style('left', this.LEGEND_X)
    .style('top', this.LEGEND_Y);
};

/** Renders flame graph help. */
FlameGraph.prototype.renderHelp_ = function() {
  this.parent_.append('div')
    .attr('class', 'tabhelp inactive-tabhelp')
    .html(this.HELP_MESSAGE);
};

/** Renders message when callStats is empty. */
FlameGraph.prototype.renderNoDataMessage_ = function() {
  this.parent_.append('div')
    .attr('class', 'flame-graph-no-data-message')
    .html(this.NO_DATA_MESSAGE);
};

/**
 * Returns function info.
 * @static
 * @param {Object} d - Object representing function call info.
 * @returns {string}
 */
FlameGraph.getNodeName_ = function(d) {
  return d.stack[0] + ':' + d.stack[2] + ' (' + d.stack[1] + ')';
};

/**
 * Truncates function name depending on flame graph rectangle length.
 * @static
 * @param (Object) d - Object representing function info.
 * @param {number} rectLength - Length of flame graph rectangle.
 * @returns {string}
 */
FlameGraph.getTruncatedNodeName_ = function(d, rectLength) {
  var fullname = FlameGraph.getNodeName_(d);
  var maxSymbols = rectLength / 10;  // Approx. 10 pixels per character.
  if (maxSymbols <= 3) {
    return '';
  } else if (fullname.length > maxSymbols - 3) { // Full name minus ellipsis.
    return fullname.substr(0, maxSymbols) + '...';
  }
  return fullname;
};

/**
 * Renders flame graph and attaches it to parent.
 * @param {Object} parent - Parent element for flame graph.
 * @param {Object} data - Data for flame graph rendering.
 */
function renderFlameGraph(data, parent) {
  var flameGraph = new FlameGraph(parent, data);
  flameGraph.render();
}

module.exports = {
  'FlameGraph': FlameGraph,
  'renderFlameGraph': renderFlameGraph,
};
