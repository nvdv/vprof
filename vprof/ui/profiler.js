/**
 * @file Profiler wrapper UI module.
 */

'use strict';
const color = require('./color');
const common = require('./common');
const d3 = require('d3');

/**
 * Represents Python profiler UI.
 * @constructor
 * @param {Object} parent - Parent element for profiler output.
 * @param {Object} data - Data for output rendering.
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

  let records = recordsTable.selectAll('.profiler-record-normal')
    .data(this.data_.callStats)
    .enter()
    .append('tr')
    .attr('class', 'profiler-record-normal')
    .on('mouseover', (d, i, n) => this.showTooltip_(n[i], tooltip, d))
    .on('mouseout', (d, i, n) => this.hideTooltip_(n[i], tooltip));

  records.append('td')
    .attr('class', 'profiler-record-color')
    .style('background', (d) => this.color_(d[9]));

  records.append('td')
    .attr('class', 'profiler-record-percentage')
    .html((d) => d[4] + '%');

  records.append('td')
    .attr('class', 'profiler-record-funcname')
    .html((d) => d[2].replace(/</g, "&lt;").replace(/>/g, "&gt;"));

  records.append('td')
    .attr('class', 'profiler-record-filename')
    .html((d) => common.shortenString(d[0], 70, false));

  records.append('td')
    .attr('class', 'profiler-record-lineno')
    .html((d) => d[1]);

  records.append('td')
    .attr('class', 'profiler-record-cumtime')
    .html((d) => d[3] + 's');

};

/**
 * Shows record tooltip.
 * @param {Object} element - Profiler record element.
 * @param {Object} tooltip - Tooltip element.
 * @param {Object} node - Profiler record info
 */
Profiler.prototype.showTooltip_ = function(element, tooltip, node) {
  d3.select(element).attr('class', 'profiler-record-highlight');
  let funcName = node[2].replace(/</g, "&lt;").replace(/>/g, "&gt;");
  tooltip.attr('class', 'content-tooltip content-tooltip-visible')
    .html('<p><b>Function name:</b> ' + funcName + '</p>' +
          '<p><b>Line number:</b> ' + node[1] +'</p>' +
          '<p><b>Filename:</b> ' + node[0] +'</p>' +
          '<p><b>Cumulative time:</b> ' + node[3] +'s</p>' +
          '<p><b>Number of calls:</b> ' + node[5] +'</p>' +
          '<p><b>Cumulative calls:</b> ' + node[6] +'</p>' +
          '<p><b>Time per call:</b> ' + node[7] +'s</p>')
    .style('left', d3.event.pageX)
    .style('top', d3.event.pageY);
};

/**
 * Hides record tooltip.
 * @param {Object} element - Profiler record element.
 * @param {Object} tooltip - Tooltip element.
 */
Profiler.prototype.hideTooltip_ = function(element, tooltip) {
  d3.select(element).attr('class', 'profiler-record-normal');
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

/** Renders profiler tab help. */
Profiler.prototype.renderHelp_ = function() {
  this.parent_.append('div')
    .attr('class', 'tabhelp inactive-tabhelp')
    .html(this.HELP_MESSAGE);
};

/**
 * Renders profiler output and attaches it to the parent.
 * @param {Object} parent - Profiler output parent element.
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
