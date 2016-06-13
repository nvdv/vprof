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
  this.TIME_CUTOFF = 0.5;

  this.data_ = data;
  FlameGraph.pruneNodes_(
      this.data_.callStats, this.TIME_CUTOFF, this.data_.runTime);
  this.parent_ = parent;
  this.xScale_ = d3.scale.linear().domain([0, 1]).range([0, this.WIDTH]);
  this.yScale_ = d3.scale.linear().range([0, this.HEIGHT]);
  this.color_ = d3.scale.category10();
  this.flameGraph_ = d3.layout.partition()
    .sort(null)
    .value(function(d) { return d.cumTime; });
}

/** Renders flame graph. */
FlameGraph.prototype.render = function() {
  var canvas = this.parent_.append('svg')
    .attr('width', this.WIDTH)
    .attr('height', this.HEIGHT);

  var tooltip = this.parent_.append('div')
    .attr('class', 'tooltip tooltip-invisible');

  this.renderLegend_();

  var cells = canvas.selectAll(".cell")
    .data(this.flameGraph_.nodes(this.data_.callStats))
    .enter()
    .append('g')
    .attr('class', 'cell');

  // Render flame graph nodes.
  var self = this;
  var nodes = cells.append('rect')
    .attr('class', 'rect-normal')
    .attr('x', function(d) {
      self.maybeRecalcNode_(d);
      return self.xScale_(d.x); })
    .attr('y', function(d) { return self.yScale_(1 - d.y - d.dy); })
    .attr('width', function(d) { return self.xScale_(d.dx); })
    .attr('height', function(d) { return self.yScale_(d.dy); })
    .style('fill', function(d) {
      return self.color_(FlameGraph.getNodeName_(d) + d.depth); })
    .on('mouseover', function(d) { self.showTooltip_(this, tooltip, d); })
    .on('mouseout', function() { self.hideTooltip_(this, tooltip); });

  var titles = cells.append('text')
    .attr('x', function(d) { return self.xScale_(d.x) + self.TEXT_OFFSET_X; })
    .attr('y', function(d) {
      return self.yScale_(1 - d.y - d.dy) + self.TEXT_OFFSET_Y; })
    .text(function(d) {
      var nodeWidth = this.previousElementSibling.getAttribute('width');
      return FlameGraph.getTruncatedNodeName_(d, nodeWidth);
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
 * Recalculates node horizontal position and width if necessary.
 * Since d3 does not provide ability to customize partition calculation.
 * @param {Object} node - Current flame graph node.
 */
FlameGraph.prototype.maybeRecalcNode_ = function(node) {
  if (node.children) {
    // Recalculate children nodes.
    var currX = node.x;
    for (var i = 0; i < node.children.length; i++) {
      node.children[i].x = currX;
      node.children[i].dx = node.children[i].cumTime / this.data_.runTime;
      currX += node.children[i].dx;
    }

    // In some cases width of children might be larger than
    // parent width - we need to fix this.
    var childrenWidth = 0;
    node.children.forEach(function(child) { childrenWidth += child.dx; });
    var scale = 1;
    if (childrenWidth > node.dx) {
      scale = node.dx / childrenWidth;
    }

    // Rescale children.
    currX = node.x;
    for (var j = 0; j < node.children.length; j++) {
      node.children[j].x = currX;
      node.children[j].dx *= scale;
      currX += node.children[j].dx;
    }
  }
};

/**
 * Redraws node titles based on current xScale and yScale.
 * @param {Object} titles - All flame graph node titles.
 */
FlameGraph.prototype.redrawTitles_ = function(titles) {
  var self = this;
  titles.attr('x', function(d) { return self.xScale_(d.x) + self.TEXT_OFFSET_X; })
    .attr('y', function(d) {
      return self.yScale_(1 - d.y - d.dy) + self.TEXT_OFFSET_Y; })
    .text(function(d) {
      var nodeWidth = self.xScale_(d.x + d.dx) - self.xScale_(d.x);
      return FlameGraph.getTruncatedNodeName_(d, nodeWidth);
    });
};

/**
 * Shows tooltip and flame graph rectangle highlighting.
 * @param {Object} element - Element representing flame graph rectangle.
 * @param {Object} tooltip - Element representing tooltip.
 * @param {Object} node - Object representing function call info.
 */
FlameGraph.prototype.showTooltip_ = function(element, tooltip, node) {
  d3.select(element).attr('class', 'rect-highlight');
  var timePercentage = FlameGraph.getTimePercentage_(
      node.cumTime, this.data_.runTime);
  var functionName = node.funcName.replace('<', '[').replace('>',  ']');
  tooltip.attr('class', 'tooltip tooltip-visible')
    .html('<p>Function name: ' + functionName + '</p>' +
          '<p>Location: ' + node.moduleName +'</p>' +
          '<p>Line number: ' + node.lineno + '</p>' +
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
FlameGraph.prototype.hideTooltip_ = function(element, tooltip) {
  d3.select(element).attr('class', 'rect-normal');
  tooltip.attr('class', 'tooltip tooltip-invisible');
};

/** Renders flame graph legend. */
FlameGraph.prototype.renderLegend_ = function() {
  this.parent_.append('div')
    .attr('class', 'legend')
    .html('<p>Object name: ' + this.data_.objectName + '</p>' +
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
FlameGraph.getNodeName_ = function(d) {
  var tokens = d.moduleName.split('/');
  var filename = tokens[tokens.length - 1];
  return filename + ':' + d.lineno + '(' + d.funcName + ')';
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
 * Returns percentage that cumTime takes in totalTime.
 * @static
 * @param {number} cumTime - Function cumulative run time.
 * @param {number} totalTime - Program run time.
 * @returns {number}
 */
FlameGraph.getTimePercentage_ = function(cumTime, totalTime) {
  return 100 * Math.round(cumTime / totalTime * 1000) / 1000;
};

/**
 * Removes call graph nodes if their cumulative time is lower
 * than cutoff percenteag.
 * @static
 * @param {object} node - Current call graph node.
 * @param {number} cutoff - Percentage cutoff.
 * @param {number} totalRuntime - Program run time.
 */
FlameGraph.pruneNodes_ = function(node, cutoff, totalRuntime) {
  var i = node.children.length;
  while (i--) {
    if (FlameGraph.getTimePercentage_(
          node.children[i].cumTime, totalRuntime) < cutoff) {
      node.children.splice(i, 1);
    }
  }
  for (var j = 0; j < node.children.length; j++) {
    FlameGraph.pruneNodes_(node.children[j], cutoff, totalRuntime);
  }
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
