/**
 * @file CPU flame graph rendering.
 */

'use strict';
var d3 = require('d3');

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
    '<p>&#8226 Hover to see node stats</p>' +
    '<p>&#8226 Click on node to zoom</p>'+
    '<p>&#8226 Double click to restore original scale</p>');

  this.data_ = data;
  this.parent_ = parent;
  this.xScale_ = d3.scale.linear().domain([0, 1]).range([0, this.WIDTH]);
  this.yScale_ = d3.scale.linear().range([0, this.HEIGHT]);
  this.color_ = d3.scale.category10();
  this.flameGraph_ = d3.layout.partition()
    .sort(null)
    .value(function(d) { return d.sampleCount; });
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

  var cells = canvas.selectAll(".flame-graph-cell")
    .data(this.flameGraph_.nodes(this.data_.callStats))
    .enter()
    .append('g')
    .attr('class', 'flame-graph-cell');

  // Render flame graph nodes.
  var self = this;
  var nodes = cells.append('rect')
    .attr('class', 'flame-graph-rect-normal')
    .attr('x', function(d) {
      self.recalcNode_(d);
      return self.xScale_(d.x); })
    .attr('y', function(d) { return self.yScale_(1 - d.y - d.dy); })
    .attr('width', function(d) { return self.xScale_(d.dx); })
    .attr('height', function(d) { return self.yScale_(d.dy); })
    .style('fill', function(d) {
      return self.color_(FlameGraph.getNodeName_(d)); })
    .on('mouseover', function(d) { self.showTooltip_(this, tooltip, d); })
    .on('mouseout', function() { self.hideTooltip_(this, tooltip); });

  var titles = cells.append('text')
    .attr('x', function(d) { return self.xScale_(d.x) + self.TEXT_OFFSET_X; })
    .attr('y', function(d) {
      return self.yScale_(1 - d.y - d.dy) + self.TEXT_OFFSET_Y; })
    .text(function(d) {
      var nodeWidth = this.previousElementSibling.getAttribute('width');
      return FlameGraph.getTruncatedNodeName_(d, nodeWidth); })
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
  this.xScale_.domain([node.x, node.x + node.dx]);
  this.yScale_.domain([0, 1 - node.y]);
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
 * @param {Object} allNodes - All flame graph nodes.
 * @param {Object} titles - All flame graph node titles.
 */
FlameGraph.prototype.zoomOut_ = function(allNodes, titles) {
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
 * Recalculates node horizontal position and width, because
 * d3 partition width is not customizable.
 * @param {Object} node - Current flame graph node.
 */
FlameGraph.prototype.recalcNode_ = function(node) {
  if (node.children) {
    var currX = node.x;
    for (var i = 0; i < node.children.length; i++) {
      node.children[i].x = currX;
      node.children[i].dx = node.children[i].sampleCount / this.data_.totalSamples;
      currX += node.children[i].dx;
    }
  }
};

/**
 * Redraws node titles based on current xScale and yScale.
 * @param {Object} titles - All flame graph node titles.
 */
FlameGraph.prototype.redrawTitles_ = function(titles) {
  var self = this;
  titles.attr('x', function(d) {
    return self.xScale_(d.x) + self.TEXT_OFFSET_X; })
    .attr('y', function(d) {
      return self.yScale_(1 - d.y - d.dy) + self.TEXT_OFFSET_Y; })
    .text(function(d) {
      var nodeWidth = self.xScale_(d.x + d.dx) - self.xScale_(d.x);
      return FlameGraph.getTruncatedNodeName_(d, nodeWidth); })
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
  d3.select(element).attr('class', 'flame-graph-rect-highlight');
  var percentage = FlameGraph.getPercentage_(
      node.sampleCount, this.data_.totalSamples);
  var functionName = node.stack[0].replace('<', '[').replace('>', ']');
  var filename = node.stack[1].replace('<', '[').replace('>', ']');
  var lineno = node.stack[2];
  tooltip.attr('class', 'content-tooltip content-tooltip-visible')
    .html('<p><b>Function name:</b> ' + functionName + '</p>' +
          '<p><b>Line number:</b> ' + lineno +'</p>' +
          '<p><b>Filename:</b> ' + filename +'</p>' +
          '<p><b>Sample count:</b> ' + node.sampleCount + '</p>' +
          '<p><b>Percentage:</b> ' + percentage +'</p>')
    .style('left', d3.event.pageX)
    .style('top', d3.event.pageY);
};

/**
 * Hides tooltip and removes node highlighting.
 * @param {Object} element - Element representing highlighted rectangle.
 * @param {Object} tooltip - Element representing tooltip.
 */
FlameGraph.prototype.hideTooltip_ = function(element, tooltip) {
  d3.select(element).attr('class', 'flame-graph-rect-normal');
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
 * Returns percentage that val takes in total.
 */
FlameGraph.getPercentage_ = function(val, total) {
  return 100 * Math.round(val / total * 1000) / 1000;
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
