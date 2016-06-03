/**
 * @file Memory chart rendering.
 */

/* jshint strict: false, browser: true, globalstrict: true */
/* global require, module */

'use strict';
var d3 = require('d3');

/**
 * Represents memory chart.
 * @constructor
 * @param {Object} parent - Parent element for memory chart.
 * @param {Object} data - Data for memory chart rendering.
 */
function MemoryChart(parent, data) {

  this.MARGIN_LEFT = 40;
  this.MARGIN_RIGHT = 5;
  this.MARGIN_TOP = 15;
  this.MARGIN_BOTTOM  = 30;
  this.PAD_SIZE = 10;
  this.HEIGHT = parent.node().scrollHeight - this.PAD_SIZE;
  this.WIDTH = parent.node().scrollWidth - this.PAD_SIZE;
  this.GRAPH_HEIGHT = this.HEIGHT - (this.MARGIN_TOP + this.MARGIN_BOTTOM);
  this.GRAPH_WIDTH = this.WIDTH - (this.MARGIN_LEFT + this.MARGIN_RIGHT);
  this.MIN_RANGE_C = 0.98;
  this.MAX_RANGE_C = 1.02;
  this.AXIS_TEXT_X = this.GRAPH_WIDTH;
  this.AXIS_TEXT_Y = 12;
  this.AXIS_TEXT_Y_OFFSET = 30;
  this.LEGEND_X = this.GRAPH_WIDTH - 350;
  this.LEGEND_Y = 100;
  this.MOUSE_X_OFFSET = 10;
  this.TICKS_NUMBER = 10;
  this.FOCUS_RADIUS = 5;
  this.DOT_RADIUS = 3;
  this.TOOLTIP_OFFSET = 35;
  this.SCALE_FACTOR = 3;
  this.MAX_ZOOM_POINTS = 20;

  this.data_ = data;
  this.parent_ = parent;
  this.xScale_ = d3.scale.linear()
    .domain(d3.extent(this.data_.codeEvents, function(d) { return d[0]; }))
    .range([0, this.GRAPH_WIDTH]);

  this.xAxis_ = d3.svg.axis()
    .scale(this.xScale_)
    .orient('bottom')
    .ticks(3)
    .tickFormat(d3.format(',.0f'));

  // Since axis.ticks(n) is only a recommendation, set tick values
  // explicitly when their number is low.
  if (this.data_.codeEvents.length < this.TICKS_NUMBER) {
    var tickValues = Array.apply(null, Array(this.data_.codeEvents.length)).map(
      function (_, i) {return i + 1; });
    this.xAxis_.tickValues(tickValues);
  } else {
    this.xAxis_.ticks(this.TICKS_NUMBER);
  }

  this.yRange_ = d3.extent(this.data_.codeEvents, function(d) { return d[2]; });
  this.yScale_ = d3.scale.linear()
    .domain([this.MIN_RANGE_C * this.yRange_[0],
             this.MAX_RANGE_C * this.yRange_[1]])
    .range([this.GRAPH_HEIGHT, 0]);
  this.yAxis_ = d3.svg.axis()
      .scale(this.yScale_)
      .orient('left');

  this.memoryGraph_ = d3.svg.area()
    .x(function(d) { return this.xScale_(d[0]); })
    .y0(this.GRAPH_HEIGHT)
    .y1(function(d) { return this.yScale_(d[2]); });

  this.currZoomRange_ = {
    'highlightStartIndex': 0,
    'highlightEndIndex': 0,
    'highlightIndexRange': 0,
    'zoomIndexStart': 0,
    'zoomIndexEnd': this.data_.codeEvents.length,
    'zoomIndexRange': this.data_.codeEvents.length,
  };
}

/** Renders memory chart. */
MemoryChart.prototype.render = function() {
  var canvas = this.parent_.append('svg')
    .attr('width', this.WIDTH)
    .attr('height', this.HEIGHT)
    .append('g')
    .attr('transform',
          'translate(' + this.MARGIN_LEFT + ',' + this.MARGIN_TOP + ')');
  var tooltip = this.parent_.append('div')
    .attr('class', 'tooltip tooltip-invisible');

  this.renderLegend_();

  var path = canvas.append('path')
    .attr('class', 'memory-graph')
    .attr('d', this.memoryGraph_(this.data_.codeEvents));

  var focus = canvas.append('circle')
    .style('display', 'none')
    .attr('class', 'memory-graph-focus')
    .attr('r', this.FOCUS_RADIUS)
    .attr('transform',
          'translate(' + (-100) + ', '  + (-100) + ')');  // Hide focus.
  var focusXLine = canvas.append('line')
    .attr('class', 'focus-line')
    .attr('y1', this.GRAPH_HEIGHT);
  var focusYLine = canvas.append('line')
    .attr('class', 'focus-line')
    .attr('x1', 0);
  var focusHiglightArc = canvas.append('path')
    .attr('class', 'focus-line-highlight');

  var self = this;
  canvas.style('pointer-events', 'all')
    .on('mouseover', function() {
        self.showFocus_(focus, focusXLine, focusYLine, focusHiglightArc); })
    .on('mouseout', function() { self.hideFocus_(
        focus, tooltip, focusXLine, focusYLine, focusHiglightArc); })
    .on('mousemove', function() { self.redrawFocus_(
        canvas, focus, tooltip, focusXLine, focusYLine, focusHiglightArc); });

  // Draw axes.
  canvas.append('g')
    .attr('class', 'x axis')
    .attr('transform', 'translate(0,' + this.GRAPH_HEIGHT + ')')
    .call(this.xAxis_)
    .append('text')
    .attr('x', this.AXIS_TEXT_X)
    .attr('y', this.AXIS_TEXT_Y - this.AXIS_TEXT_Y_OFFSET)
    .attr('dy', '.71em')
    .text('Executed lines');

  canvas.append('g')
    .attr('class', 'y axis')
    .call(this.yAxis_)
    .append('text')
    .attr('transform', 'rotate(-90)')
    .attr('y', this.AXIS_TEXT_Y)
    .attr('dy', '.71em')
    .text('Memory usage, MB');

  // Zoom in.
  canvas.on('click', function() {
      self.zoomIn_(path, canvas, focus, tooltip, focusXLine,
                   focusYLine, focusHiglightArc); });
  // Zoom out.
  this.parent_.on('dblclick', function() { self.zoomOut_(path, canvas); });
};

/**
 * Handles zoom in.
 * @param {Object} path - Represents memory graph.
 * @param {Object} canvas - Represents drawing canvas.
 * @param {Object} focus - Object representing focus circle.
 * @param {Object} tooltip - Object representing tooltip.
 * @param {Object} focusXLine - Object representing focus line parallel to OY.
 * @param {Object} focusYLine - Object representing focus line parallel to OX.
 * @param {Object} focusHiglightArc - Object representing focus highlight region.
 */
MemoryChart.prototype.zoomIn_ = function(path, canvas, focus, tooltip,
    focusXLine, focusYLine, focusHiglightArc) {
  var crds = d3.mouse(canvas.node());
  var midIndex = Math.round(this.xScale_.invert(crds[0])) - 1;
  this.updateZoomRangeParams_(midIndex);
  if (this.currZoomRange_.zoomIndexStart < this.currZoomRange_.zoomIndexEnd) {
    if (this.currZoomRange_.zoomIndexRange < this.TICKS_NUMBER) {
      this.xAxis_.ticks(this.currZoomRange_.zoomIndexRange);
    }
    this.xScale_.domain(
      [this.data_.codeEvents[this.currZoomRange_.zoomIndexStart][0],
       this.data_.codeEvents[this.currZoomRange_.zoomIndexEnd][0]]);
    var eventsSlice = this.data_.codeEvents.slice(
        this.currZoomRange_.zoomIndexStart,
        this.currZoomRange_.zoomIndexEnd + 1);
    path.attr('d', this.memoryGraph_(eventsSlice));
    canvas.selectAll('g.x.axis')
      .call(this.xAxis_);

    var closestX = this.xScale_(this.data_.codeEvents[midIndex][0]);
    var closestY = this.yScale_(this.data_.codeEvents[midIndex][2]);
    focus.attr('transform', 'translate(' + closestX + ', ' +
                closestY + ')');
    focusXLine.attr('x1', closestX)
      .attr('x2', closestX)
      .attr('y2', closestY);
    focusYLine.attr('y1', closestY)
      .attr('x2', closestX)
      .attr('y2', closestY);
    var tooltipText = MemoryChart.generateTooltipText_(
        this.data_.codeEvents[midIndex]);
    tooltip.attr('class', 'tooltip tooltip-visible')
      .html(tooltipText)
      .style('left', closestX)
      .style('top', closestY - this.TOOLTIP_OFFSET);
    if (this.currZoomRange_.zoomIndexRange > this.MAX_ZOOM_POINTS) {
      this.updateHighlightRangeParams_(midIndex);
      var highlightSlice = this.data_.codeEvents.slice(
          this.currZoomRange_.highlightStartIndex,
          this.currZoomRange_.highlightEndIndex + 1);
      focusHiglightArc.attr('d', this.memoryGraph_(highlightSlice));
    } else {
      focusHiglightArc.style('display', 'none');
    }
  }
};

/**
 * Handles zoom out.
 * @param {Object} path - Represents memory graph.
 * @param {Object} canvas - Represents drawing canvas.
 */
MemoryChart.prototype.zoomOut_ = function(path, canvas) {
  this.resetZoomRangeParams_();
  this.xScale_.domain(
      d3.extent(this.data_.codeEvents, function(d) { return d[0]; }));
  path.attr('d', this.memoryGraph_(this.data_.codeEvents));
  this.xAxis_.ticks(
      Math.min(this.TICKS_NUMBER, this.data_.codeEvents.length));
  canvas.selectAll('g.x.axis')
    .call(this.xAxis_);
};

/** Renders memory chart legend. */
MemoryChart.prototype.renderLegend_ = function() {
  this.parent_.append('div')
    .attr('class', 'legend')
    .html('<p>Object name: ' + this.data_.objectName + '</p>' +
          '<p>Total lines executed: ' + this.data_.totalEvents + '</p>')
    .style('left', this.LEGEND_X)
    .style('top', this.LEGEND_Y);
};

/**
 * Hides focus, it's guiding lines and tooltip.
 * @param {Object} focus - Object representing focus circle.
 * @param {Object} tooltip - Object representing tooltip.
 * @param {Object} focusXLine - Object representing focus line parallel to OY.
 * @param {Object} focusYLine - Object representing focus line parallel to OX.
 * @param {Object} focusHiglightArc - Object representing focus highlight region.
 */
MemoryChart.prototype.hideFocus_ = function(focus, tooltip, focusXLine,
    focusYLine, focusHiglightArc) {
  focus.style('display', 'none');
  tooltip.attr('class', 'tooltip tooltip-invisible');
  focusXLine.style('display', 'none');
  focusYLine.style('display', 'none');
  focusHiglightArc.style('display', 'none');
};

/**
 * Shows focus, it's guiding lines and tooltip.
 * @param {Object} focus - Object representing focus circle.
 * @param {Object} tooltip - Object representing tooltip.
 * @param {Object} focusXLine - Object representing focus line parallel to OY.
 * @param {Object} focusYLine - Object representing focus line parallel to OX.
 * @param {Object} focusHiglightArc - Object representing focus highlight region.
 */
MemoryChart.prototype.showFocus_ = function(focus, focusXLine,
    focusYLine, focusHiglightArc) {
  focus.style('display', null);
  focusXLine.style('display', null);
  focusYLine.style('display', null);
  if (this.currZoomRange_.zoomIndexRange > this.MAX_ZOOM_POINTS) {
    focusHiglightArc.style('display', null);
  }
};

/**
 * Redraws focus, it's guiding lines and tooltip.
 * @param {Object} canvas - Object representing canvas.
 * @param {Object} focus - Object representing focus circle.
 * @param {Object} tooltip - Object representing tooltip.
 * @param {Object} focusXLine - Object representing focus line parallel to OY.
 * @param {Object} focusYLine - Object representing focus line parallel to OX.
 * @param {Object} focusHiglightArc - Object representing focus highlight region.
 */
MemoryChart.prototype.redrawFocus_ = function(canvas, focus, tooltip,
    focusXLine, focusYLine, focusHiglightArc) {
  var crds = d3.mouse(canvas.node());
  var closestIndex = Math.round(this.xScale_.invert(crds[0])) - 1;
  var closestX = this.xScale_(this.data_.codeEvents[closestIndex][0]);
  var closestY = this.yScale_(this.data_.codeEvents[closestIndex][2]);
  focus.attr('transform', 'translate(' + closestX + ', ' +
              closestY + ')');
  focusXLine.attr('x1', closestX)
    .attr('x2', closestX)
    .attr('y2', closestY);
  focusYLine.attr('y1', closestY)
    .attr('x2', closestX)
    .attr('y2', closestY);
  var tooltipText = MemoryChart.generateTooltipText_(
    this.data_.codeEvents[closestIndex]);
  tooltip.attr('class', 'tooltip tooltip-visible')
    .html(tooltipText)
    .style('left', closestX)
    .style('top', closestY - this.TOOLTIP_OFFSET);

  if (this.currZoomRange_.zoomIndexRange > this.MAX_ZOOM_POINTS) {
    this.updateHighlightRangeParams_(closestIndex);
    var highlightSlice = this.data_.codeEvents.slice(
        this.currZoomRange_.highlightStartIndex,
        this.currZoomRange_.highlightEndIndex + 1);
    focusHiglightArc.attr('d', this.memoryGraph_(highlightSlice));
  }
};

/**
 * Generates tooltip text from line stats.
 * @static
 * @param {Object[]} stats - Line memory stats.
 * @returns {string} - Text for tooltip with line stats.
 */
MemoryChart.generateTooltipText_ = function(stats) {
  var result = '';
  if (stats) {
    var functionName = stats[4].replace('<', '[').replace('>',  ']');
    result += ('<p>Executed line: ' + stats[0] + '</p>' +
               '<p>Line number: ' + stats[1] + '</p>' +
               '<p>Function name: ' + functionName + '</p>' +
               '<p>Filename: ' + stats[5] + '</p>' +
               '<p>Memory usage: ' + stats[2] + ' MB</p>');
  }
  return result;
};

/**
 * Updates zoom highlight params based on previous params and mid index.
 * @param {number} midIndex - Mid index of zoom region.
 */
MemoryChart.prototype.updateHighlightRangeParams_ = function(midIndex) {
  var startIndex = midIndex - Math.floor(
      0.5 * this.currZoomRange_.zoomIndexRange / this.SCALE_FACTOR);
  var endIndex = midIndex + Math.floor(
      0.5 * this.currZoomRange_.zoomIndexRange / this.SCALE_FACTOR);
  this.currZoomRange_.highlightStartIndex = Math.max(
      startIndex, this.currZoomRange_.zoomIndexStart);
  this.currZoomRange_.highlightEndIndex = Math.min(
      endIndex, this.currZoomRange_.zoomIndexEnd);
  this.currZoomRange_.highlightIndexRange = (
      this.currZoomRange_.highlightEndIndex -
      this.currZoomRange_.highlightStartIndex);
};

/**
 * Updates zoom region params based on previous params and mid index.
 * @param {number} midIndex - Mid index of zoom region.
 */
MemoryChart.prototype.updateZoomRangeParams_ = function(midIndex) {
  var startIndex = midIndex - Math.floor(
      0.5 * this.currZoomRange_.zoomIndexRange / this.SCALE_FACTOR);
  var endIndex = midIndex + Math.floor(
      0.5 * this.currZoomRange_.zoomIndexRange / this.SCALE_FACTOR);
  this.currZoomRange_.zoomIndexStart = Math.max(startIndex, 0);
  this.currZoomRange_.zoomIndexEnd = Math.min(
      endIndex, this.data_.codeEvents.length - 1);
  this.currZoomRange_.zoomIndexRange = (
      this.currZoomRange_.zoomIndexEnd -
      this.currZoomRange_.zoomIndexStart);
};

/** Resets zoom range params. */
MemoryChart.prototype.resetZoomRangeParams_ = function() {
  this.currZoomRange_.highlightStartIndex = 0;
  this.currZoomRange_.highlightEndIndex = 0;
  this.currZoomRange_.highlightIndexRange =  0;
  this.currZoomRange_.zoomIndexStart = 0;
  this.currZoomRange_.zoomIndexEnd = this.data_.codeEvents.length;
  this.currZoomRange_.zoomIndexRange = this.data_.codeEvents.length;
};

/**
 * Renders memory chart and attaches it to parent.
 * @param {Object} parent - Parent element for memory chart.
 * @param {Object} data - Data for memory chart rendering.
 */
function renderMemoryStats(data, parent) {
  var memoryChart = new MemoryChart(parent, data);
  memoryChart.render();
}

module.exports = {
  'MemoryChart': MemoryChart,
  'renderMemoryStats': renderMemoryStats,
};
