/**
 * @file Profiler output rendering.
 */

'use strict';
const color = require('./color');
const common = require('./common');
const d3select = require('d3-selection');
const d3interpolate = require('d3-interpolate');
const d3scale = require('d3-scale');

/**
 * Represents Python profiler output.
 * @constructor
 * @param {Object} parent - Parent element for profiler output.
 * @param {Object} data - Data for rendering.
 */
function Profiler(parent, data) {
  this.PATH_CHAR_COUNT = 70;
  this.HELP_MESSAGE = (
    '<p>&#8226 Hover over record to see detailed stats</p>');

  this.data_ = data;
  this.parent_ = parent;
  this.color_ = color.createColorScale();
}

/** Renders profiler output */
Profiler.prototype.render = function() {
  let content = this.parent_.append('div')
    .attr('class', 'profiler-content');

  let tooltip = this.parent_.append('div')
    .attr('class', 'content-tooltip content-tooltip-invisible');

  let recordsTable = content.append('div')
    .attr('class', 'profiler-record-table-wrapper')
    .append('div')
    .attr('class', 'profiler-record-table');

  recordsTable.append('tr')
    .attr('class', 'profiler-record-table-header')
    .html(
      '<td>Color</td>' +
      '<td>%</td>' +
      '<td>Function name</td>' +
      '<td>Filename</td>' +
      '<td>Line</td>' +
      '<td>Time</td>');

  this.renderLegend_(content);
  this.renderHelp_();

  let self = this;
  let records = recordsTable.selectAll('.profiler-record-normal')
    .data(this.data_.callStats)
    .enter()
    .append('tr')
    .attr('class', 'profiler-record-normal')
    .on('mouseover', function(d) { self.showTooltip_(this, tooltip, d); })
    .on('mouseout', function() { self.hideTooltip_(this, tooltip); });

  records.append('td')
    .attr('class', 'profiler-record-color')
    .style('background', function(d) { return self.color_(d[9]); });

  records.append('td')
    .attr('class', 'profiler-record-percentage')
    .html(function(d) { return d[4] + '%'; });

  records.append('td')
    .attr('class', 'profiler-record-funcname')
    .html(function(d) {
      return d[2].replace(/</g, "&lt;").replace(/>/g, "&gt;");
    });

  records.append('td')
    .attr('class', 'profiler-record-filename')
    .html(function(d) { return common.shortenString(d[0], 70, false); });

  records.append('td')
    .attr('class', 'profiler-record-lineno')
    .html(function(d) { return d[1]; });

  records.append('td')
    .attr('class', 'profiler-record-cumtime')
    .html(function(d) { return d[3] + 's'; });

};

/**
 * Shows tooltip.
 * @param {Object} element - Element representing profiler record.
 * @param {Object} tooltip - Element representing tooltip.
 * @param {Object} node - Object with profiler record info.
 */
Profiler.prototype.showTooltip_ = function(element, tooltip, node) {
  d3select.select(element).attr('class', 'profiler-record-highlight');
  let funcName = node[2].replace(/</g, "&lt;").replace(/>/g, "&gt;");
  tooltip.attr('class', 'content-tooltip content-tooltip-visible')
    .html('<p><b>Function name:</b> ' + funcName + '</p>' +
          '<p><b>Line number:</b> ' + node[1] +'</p>' +
          '<p><b>Filename:</b> ' + node[0] +'</p>' +
          '<p><b>Cumulative time:</b> ' + node[3] +'s</p>' +
          '<p><b>Number of calls:</b> ' + node[5] +'</p>' +
          '<p><b>Cumulative calls:</b> ' + node[6] +'</p>' +
          '<p><b>Time per call:</b> ' + node[7] +'s</p>')
    .style('left', d3select.event.pageX)
    .style('top', d3select.event.pageY);
};

/**
 * Hides tooltip.
 * @param {Object} element - Element representing profiler record.
 * @param {Object} tooltip - Element representing tooltip.
 */
Profiler.prototype.hideTooltip_ = function(element, tooltip) {
  d3select.select(element).attr('class', 'profiler-record-normal');
  tooltip.attr('class', 'content-tooltip content-tooltip-invisible');
};

/** Renders profiler tab legend. */
Profiler.prototype.renderLegend_ = function(parent) {
  parent.append('div')
    .attr('class', 'profiler-legend')
    .append('div')
    .attr('class', 'content-legend')
    .append('text')
    .html('<p><b>Object name:</b> ' + this.data_.objectName + '</p>' +
          '<p><b>Total time:</b> ' + this.data_.totalTime + 's</p>' +
          '<p><b>Primitive calls:</b> ' + this.data_.primitiveCalls + '</p>' +
          '<p><b>Total calls:</b> ' + this.data_.totalCalls + '</p>');
};

/** Renders profiler output help. */
Profiler.prototype.renderHelp_ = function() {
  this.parent_.append('div')
    .attr('class', 'tabhelp inactive-tabhelp')
    .html(this.HELP_MESSAGE);
};

/**
 * Renders profiler output and attaches it to parent.
 * @param {Object} parent - Parent element for profiler output.
 * @param {Object} data - Data for profiler output.
 */
function renderProfilerOutput(data, parent) {
  let profilerOutput = new Profiler(parent, data);
  profilerOutput.render();
}

module.exports = {
  'Profiler': Profiler,
  'renderProfilerOutput': renderProfilerOutput,
};
