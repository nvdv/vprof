/**
 * @file Memory chart rendering.
 */

'use strict';
var d3array = require('d3-array');
var d3axis = require('d3-axis');
var d3format = require('d3-format');
var d3shape = require('d3-shape');
var d3select = require('d3-selection');
var d3scale = require('d3-scale');

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
  this.MIN_RANGE_C = 0.98;
  this.MAX_RANGE_C = 1.02;
  this.MOUSE_X_OFFSET = 10;
  this.TICKS_NUMBER = 10;
  this.FOCUS_RADIUS = 5;
  this.DOT_RADIUS = 3;
  this.TOOLTIP_OFFSET = 35;
  this.SCALE_FACTOR = 3;
  this.MAX_ZOOM_POINTS = 20;
  this.HELP_MESSAGE = (
    '<p>&#8226 Click to zoom highlighted region</p>'+
    '<p>&#8226 Double click to restore original scale</p>');

  this.data_ = data;
  this.parent_ = parent;

  // Memory view div size should be specified in CSS to render
  // SVG graph correctly.
  this.memoryView_ = this.parent_.append('div')
    .attr('class', 'memory-info-container');
  this.objectsTable_ = this.memoryView_.append('div')
    .attr('class', 'memory-table-wrapper') // To display overflow correctly.
    .append('div')
    .attr('class', 'memory-objects-table');
  this.memoryUsageGraph_ = this.memoryView_.append('div')
    .attr('class', 'memory-usage-graph');

  this.TABLE_WIDTH = this.objectsTable_.node().scrollWidth;
  this.HEIGHT = this.memoryUsageGraph_.node().scrollHeight - this.PAD_SIZE;
  this.WIDTH = this.memoryUsageGraph_.node().scrollWidth - this.PAD_SIZE;
  this.GRAPH_HEIGHT = this.HEIGHT - (this.MARGIN_TOP + this.MARGIN_BOTTOM);
  this.GRAPH_WIDTH = this.TABLE_WIDTH + this.WIDTH - (
      this.MARGIN_LEFT + this.MARGIN_RIGHT);
  this.AXIS_TEXT_X = this.GRAPH_WIDTH - this.TABLE_WIDTH;
  this.AXIS_TEXT_Y = 12;
  this.AXIS_TEXT_Y_OFFSET = 30;
  this.LEGEND_X = this.GRAPH_WIDTH - 350;
  this.LEGEND_Y = 100;

  this.xScale_ = d3scale.scaleLinear()
    .domain(d3array.extent(this.data_.codeEvents, function(d) { return d[0]; }))
    .range([0, this.GRAPH_WIDTH]);

  this.xAxis_ = d3axis.axisBottom()
    .scale(this.xScale_)
    .ticks(this.TICKS_NUMBER)
    .tickFormat(d3format.format(',.0f'));

  // Since axis.ticks(n) is only a recommendation, set tick values
  // explicitly when their number is low.
  if (this.data_.codeEvents.length < this.TICKS_NUMBER) {
    var tickValues = Array.apply(null, Array(this.data_.codeEvents.length)).map(
      function (_, i) { return i + 1; });
    this.xAxis_.tickValues(tickValues);
  } else {
    this.xAxis_.ticks(this.TICKS_NUMBER);
  }

  this.yRange_ = d3array.extent(
      this.data_.codeEvents, function(d) { return d[2]; });
  this.yScale_ = d3scale.scaleLinear()
    .domain([
      this.MIN_RANGE_C * this.yRange_[0], this.MAX_RANGE_C * this.yRange_[1]])
    .range([this.GRAPH_HEIGHT, 0]);
  this.yAxis_ = d3axis.axisLeft()
      .scale(this.yScale_);

  var self = this;
  this.memoryGraph_ = d3shape.area()
    .x(function(d) { return self.xScale_(d[0]); })
    .y0(self.GRAPH_HEIGHT)
    .y1(function(d) { return self.yScale_(d[2]); });

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
  var canvas = this.memoryUsageGraph_.append('svg')
    .attr('width', this.WIDTH)
    .attr('height', this.HEIGHT)
    .append('g')
    .attr('transform',
          'translate(' + this.MARGIN_LEFT + ',' + this.MARGIN_TOP + ')');

  var tooltip = this.memoryUsageGraph_.append('div')
    .attr('class', 'content-tooltip content-tooltip-invisible');

  this.renderObjectsTable_();
  this.renderLegend_();
  this.renderHelp_();

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
    .attr('class', 'memory-graph-focus-line')
    .attr('y1', this.GRAPH_HEIGHT);
  var focusYLine = canvas.append('line')
    .attr('class', 'memory-graph-focus-line')
    .attr('x1', 0);
  var focusHiglightArc = canvas.append('path')
    .attr('class', 'memory-graph-focus-line-highlight');

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
    .attr('class', 'x memory-graph-axis')
    .attr('transform', 'translate(0,' + this.GRAPH_HEIGHT + ')')
    .call(this.xAxis_)
    .append('text')
    .attr('x', this.AXIS_TEXT_X)
    .attr('y', this.AXIS_TEXT_Y - this.AXIS_TEXT_Y_OFFSET)
    .attr('dy', '.71em')
    .text('Executed lines');

  canvas.append('g')
    .attr('class', 'y memory-graph-axis')
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
  var crds = d3select.mouse(canvas.node());
  var midIndex = Math.round(this.xScale_.invert(crds[0])) - 1;
  this.updateZoomRangeParams_(midIndex);
  if (this.currZoomRange_.zoomIndexStart < this.currZoomRange_.zoomIndexEnd) {
    if (this.currZoomRange_.zoomIndexRange < this.TICKS_NUMBER) {
      this.xAxis_.ticks(this.currZoomRange_.zoomIndexRange);
    }
    this.xScale_.domain([
      this.data_.codeEvents[this.currZoomRange_.zoomIndexStart][0],
      this.data_.codeEvents[this.currZoomRange_.zoomIndexEnd][0]]);
    var eventsSlice = this.data_.codeEvents.slice(
        this.currZoomRange_.zoomIndexStart,
        this.currZoomRange_.zoomIndexEnd + 1);
    path.attr('d', this.memoryGraph_(eventsSlice));
    canvas.selectAll('g.x.memory-graph-axis')
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
    tooltip.attr('class', 'content-tooltip content-tooltip-visible')
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
      d3array.extent(this.data_.codeEvents, function(d) { return d[0]; }));
  path.attr('d', this.memoryGraph_(this.data_.codeEvents));
  this.xAxis_.ticks(
      Math.min(this.TICKS_NUMBER, this.data_.codeEvents.length));
  canvas.selectAll('g.x.memory-graph-axis')
    .call(this.xAxis_);
};

/** Renders memory chart legend. */
MemoryChart.prototype.renderLegend_ = function() {
  this.parent_.append('div')
    .attr('class', 'content-legend')
    .html('<p><b>Object name:</b> ' + this.data_.objectName + '</p>' +
          '<p><b>Total lines executed:</b> ' + this.data_.totalEvents + '</p>')
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
  tooltip.attr('class', 'content-tooltip content-tooltip-invisible');
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
  var crds = d3select.mouse(canvas.node());
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
  tooltip.attr('class', 'content-tooltip content-tooltip-visible')
    .html(tooltipText)
    .style('left', this.TABLE_WIDTH + closestX)
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
    var functionName = stats[3].replace('<', '[').replace('>',  ']');
    result = ('<p><b>Executed line:</b> ' + stats[0] + '</p>' +
              '<p><b>Line number:</b> ' + stats[1] + '</p>' +
              '<p><b>Function name:</b> ' + functionName + '</p>' +
              '<p><b>Filename:</b> ' + stats[4] + '</p>' +
              '<p><b>Memory usage:</b> ' + stats[2] + ' MB</p>');
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

/** Renders memory chart help. */
MemoryChart.prototype.renderHelp_ = function() {
  this.parent_.append('div')
    .attr('class', 'tabhelp inactive-tabhelp')
    .html(this.HELP_MESSAGE);
};

/** Renders object count table. */
MemoryChart.prototype.renderObjectsTable_ = function() {
  var tableName = this.objectsTable_.append('tr')
    .attr('class', 'memory-table-name');

  tableName.append('td')
    .text('Objects left in memory');
  tableName.append('td')
    .text('');

  var tableHeader = this.objectsTable_.append('tr')
    .attr('class', 'memory-table-header');

  tableHeader.append('td')
    .text('Object type');
  tableHeader.append('td')
    .text('Count');

  var countRows = this.objectsTable_.selectAll('.memory-table-row')
    .data(this.data_.objectsCount)
    .enter()
    .append('tr')
    .attr('class', 'memory-table-row');

  countRows.append('td')
    .text(function(d) { return d[0]; });
  countRows.append('td')
    .text(function(d) { return d[1]; });
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
