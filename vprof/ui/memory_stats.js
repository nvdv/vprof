/**
 * @file Memory profiler UI module.
 */

'use strict';
const d3 = require('d3');

/**
 * Represents memory chart.
 * @constructor
 * @param {Object} parent - Parent element for memory chart.
 * @param {Object} data - Data for memory chart rendering.
 */
function MemoryChart(parent, data) {
  this.MARGIN_LEFT = 27;
  this.MARGIN_RIGHT = 5;
  this.MARGIN_TOP = 15;
  this.MARGIN_BOTTOM  = 30;
  this.HEIGHT_PAD = 10;
  this.WIDTH_PAD = 25;
  this.MIN_RANGE_C = 0.8;
  this.MAX_RANGE_C = 1.2;
  this.MOUSE_X_OFFSET = 10;
  this.TICKS_NUMBER = 10;
  this.FOCUS_RADIUS = 5;
  this.DOT_RADIUS = 3;
  this.TOOLTIP_OFFSET = 35;
  this.HELP_MESSAGE = (
    '<p>&#8226 Scroll on graph to zoom</p>'+
    '<p>&#8226 Drag to select required area</p>');

  this.data_ = data;
  this.parent_ = parent;

  // Memory view div size should be specified in CSS to render SVG correctly.
  this.memoryView_ = this.parent_.append('div')
    .attr('class', 'memory-info-container');
  this.objectsTable_ = this.memoryView_.append('div')
    .attr('class', 'memory-table-wrapper')
    .append('div')
    .attr('class', 'memory-objects-table');
  this.memoryUsageGraph_ = this.memoryView_.append('div')
    .attr('class', 'memory-usage-graph');

  this.TABLE_WIDTH = this.objectsTable_.node().scrollWidth;
  this.HEIGHT = this.memoryUsageGraph_.node().scrollHeight - this.HEIGHT_PAD;
  this.WIDTH = this.memoryUsageGraph_.node().scrollWidth - this.WIDTH_PAD;
  this.GRAPH_HEIGHT = this.HEIGHT - (this.MARGIN_TOP + this.MARGIN_BOTTOM);
  this.GRAPH_WIDTH = this.TABLE_WIDTH + this.WIDTH - (
    this.MARGIN_LEFT + this.MARGIN_RIGHT);
  this.AXIS_TEXT_X = this.GRAPH_WIDTH - this.TABLE_WIDTH;
  this.AXIS_TEXT_Y = 12;
  this.AXIS_TEXT_Y_OFFSET = 30;
  this.LEGEND_X = this.GRAPH_WIDTH - 450;
  this.LEGEND_Y = 100;
  this.ZOOM_SCALE_EXTENT = [1, 100];
  this.ZOOM_TRANSLATE_EXTENT = [[0, 0], [this.WIDTH, this.HEIGHT]];

  this.xScale_ = d3.scaleLinear()
    .domain(d3.extent(this.data_.codeEvents, (d) => d[0]))
    .range([0, this.GRAPH_WIDTH]);
  this.xAxis_ = d3.axisBottom()
    .scale(this.xScale_)
    .ticks(this.TICKS_NUMBER)
    .tickFormat(d3.format(',.0f'));

  // Set tick values explicitly when number of events is small.
  if (this.data_.codeEvents.length < this.TICKS_NUMBER) {
    let tickValues = [];
    for (let i = 0; i < this.data_.codeEvents.length; i++) {
      tickValues.push(i);
    }
    this.xAxis_.tickValues(tickValues);
  } else {
    this.xAxis_.ticks(this.TICKS_NUMBER);
  }

  this.yRange_ = d3.extent(this.data_.codeEvents, (d) => d[2]);
  this.yScale_ = d3.scaleLinear()
    .domain([
      this.MIN_RANGE_C * this.yRange_[0], this.MAX_RANGE_C * this.yRange_[1]])
    .range([this.GRAPH_HEIGHT, 0]);
  this.yAxis_ = d3.axisLeft()
    .scale(this.yScale_);

  this.memoryGraph_ = d3.area()
    .x((d) => this.xScale_(d[0]))
    .y0(this.GRAPH_HEIGHT)
    .y1((d) => this.yScale_(d[2]));
}

/** Renders memory chart. */
MemoryChart.prototype.render = function() {
  let canvas = this.memoryUsageGraph_.append('svg')
    .attr('width', this.WIDTH)
    .attr('height', this.HEIGHT)
    .append('g')
    .attr('transform',
      'translate(' + this.MARGIN_LEFT + ',' + this.MARGIN_TOP + ')');

  let tooltip = this.memoryUsageGraph_.append('div')
    .attr('class', 'content-tooltip content-tooltip-invisible');

  this.renderObjectsTable_();
  this.renderLegend_();
  this.renderHelp_();

  let path = canvas.append('path')
    .attr('class', 'memory-graph')
    .attr('d', this.memoryGraph_(this.data_.codeEvents));

  let focus = canvas.append('circle')
    .style('display', 'none')
    .attr('class', 'memory-graph-focus')
    .attr('r', this.FOCUS_RADIUS)
    .attr('transform', 'translate(' + (-100) + ', '  + (-100) + ')');
  let focusXLine = canvas.append('line')
    .attr('class', 'memory-graph-focus-line')
    .attr('y1', this.GRAPH_HEIGHT);
  let focusYLine = canvas.append('line')
    .attr('class', 'memory-graph-focus-line')
    .attr('x1', 0);

  let xGroup = canvas.append('g')
    .attr('class', 'x memory-graph-axis')
    .attr('transform', 'translate(0,' + this.GRAPH_HEIGHT + ')')
    .call(this.xAxis_);
  xGroup.append('text')
    .attr('x', this.AXIS_TEXT_X)
    .attr('y', this.AXIS_TEXT_Y - this.AXIS_TEXT_Y_OFFSET)
    .attr('dy', '.71em')
    .text('Executed lines');

  let yGroup = canvas.append('g')
    .attr('class', 'y memory-graph-axis')
    .call(this.yAxis_);
  yGroup.append('text')
    .attr('transform', 'rotate(-90)')
    .attr('y', this.AXIS_TEXT_Y)
    .attr('dy', '.71em')
    .text('Memory usage, MB');

  let zoom = d3.zoom()
    .scaleExtent(this.ZOOM_SCALE_EXTENT)
    .translateExtent(this.ZOOM_TRANSLATE_EXTENT)
    .on('zoom', () => {
      let t = d3.event.transform;
      xGroup.call(this.xAxis_.scale(t.rescaleX(this.xScale_)));
      path.attr(
        'transform', 'translate(' + t.x + ' 0) ' + 'scale(' + t.k + ' 1)');
    });

  canvas.call(zoom);
  canvas.style('pointer-events', 'all')
    .on('mouseover', () => this.showFocus_(focus, focusXLine, focusYLine))
    .on('mouseout', () => this.hideFocus_(
      focus, tooltip, focusXLine, focusYLine))
    .on('mousemove', () => this.redrawFocus_(
      canvas, focus, tooltip, focusXLine, focusYLine));
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
 * Hides graph focus, guiding lines and tooltip.
 * @param {Object} focus - Focus circle.
 * @param {Object} tooltip - Graph tooltip.
 * @param {Object} focusXLine - Guiding line parallel to OY.
 * @param {Object} focusYLine - Guiding line parallel to OX.
 */
MemoryChart.prototype.hideFocus_ = function(focus, tooltip, focusXLine,
  focusYLine) {
  focus.style('display', 'none');
  tooltip.attr('class', 'content-tooltip content-tooltip-invisible');
  focusXLine.style('display', 'none');
  focusYLine.style('display', 'none');
};

/**
 * Shows graph focus, guiding lines and tooltip.
 * @param {Object} focus - Focus circle.
 * @param {Object} tooltip - Graph tooltip.
 * @param {Object} focusXLine - Guiding line parallel to OY.
 * @param {Object} focusYLine - Guiding line parallel to OX.
 */
MemoryChart.prototype.showFocus_ = function(focus, focusXLine, focusYLine) {
  focus.style('display', null);
  focusXLine.style('display', null);
  focusYLine.style('display', null);
};

/**
 * Redraws graph focus, guiding lines and tooltip.
 * @param {Object} canvas - Graph canvas.
 * @param {Object} focus - Focus circle.
 * @param {Object} tooltip - Graph tooltip.
 * @param {Object} focusXLine - Guiding line parallel to OY.
 * @param {Object} focusYLine - Guiding line parallel to OX.
 */
MemoryChart.prototype.redrawFocus_ = function(canvas, focus, tooltip,
  focusXLine, focusYLine) {
  let t = d3.zoomTransform(canvas.node());
  let crds = d3.mouse(canvas.node());
  let xCoord = (crds[0] - t.x) / t.k;
  let closestIndex = Math.round(this.xScale_.invert(xCoord)) - 1;
  let closestY = this.yScale_(this.data_.codeEvents[closestIndex][2]);
  let closestX = t.k * this.xScale_(
    this.data_.codeEvents[closestIndex][0]) + t.x;

  focus.attr('transform', 'translate(' + closestX + ', ' +
             closestY + ')');
  focusXLine.attr('x1', closestX)
    .attr('x2', closestX)
    .attr('y2', closestY);
  focusYLine.attr('y1', closestY)
    .attr('x2', closestX)
    .attr('y2', closestY);
  let tooltipText = MemoryChart.generateTooltipText_(
    this.data_.codeEvents[closestIndex]);
  tooltip.attr('class', 'content-tooltip content-tooltip-visible')
    .html(tooltipText)
    .style('left', this.TABLE_WIDTH + closestX)
    .style('top', closestY - this.TOOLTIP_OFFSET);
};

/**
 * Generates tooltip text from line stats.
 * @static
 * @param {Object[]} stats - Memory stats of line of code.
 * @returns {string}
 */
MemoryChart.generateTooltipText_ = function(stats) {
  let result = '';
  if (stats) {
    let functionName = stats[3].replace('<', '[').replace('>',  ']');
    result = ('<p><b>Executed line:</b> ' + stats[0] + '</p>' +
              '<p><b>Line number:</b> ' + stats[1] + '</p>' +
              '<p><b>Function name:</b> ' + functionName + '</p>' +
              '<p><b>Filename:</b> ' + stats[4] + '</p>' +
              '<p><b>Memory usage:</b> ' + stats[2] + ' MB</p>');
  }
  return result;
};

/** Renders memory chart help. */
MemoryChart.prototype.renderHelp_ = function() {
  this.parent_.append('div')
    .attr('class', 'tabhelp inactive-tabhelp')
    .html(this.HELP_MESSAGE);
};

/** Renders object count table. */
MemoryChart.prototype.renderObjectsTable_ = function() {
  let tableName = this.objectsTable_.append('tr')
    .attr('class', 'memory-table-name');

  tableName.append('td')
    .text('Objects in memory');
  tableName.append('td')
    .text('');

  let tableHeader = this.objectsTable_.append('tr')
    .attr('class', 'memory-table-header');

  tableHeader.append('td')
    .text('Objects');
  tableHeader.append('td')
    .text('Count');

  let countRows = this.objectsTable_.selectAll('.memory-table-row')
    .data(this.data_.objectsCount)
    .enter()
    .append('tr')
    .attr('class', 'memory-table-row');

  countRows.append('td')
    .text((d) => d[0]);
  countRows.append('td')
    .text((d) => d[1]);
};

/**
 * Renders memory chart and attaches it to the parent.
 * @param {Object} parent - Memory chart parent element.
 * @param {Object} data - Data for memory chart rendering.
 */
function renderMemoryStats(data, parent) {
  let memoryChart = new MemoryChart(parent, data);
  memoryChart.render();
}

module.exports = {
  'MemoryChart': MemoryChart,
  'renderMemoryStats': renderMemoryStats,
};
