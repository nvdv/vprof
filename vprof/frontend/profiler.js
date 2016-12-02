/**
 * @file Profiler output rendering.
 */

'use strict';
var d3select = require('d3-selection');

/**
 * Represents Python profiler output.
 * @constructor
 * @param {Object} parent - Parent element for profiler output.
 * @param {Object} data - Data for rendering.
 */
function Profiler(parent, data) {
  this.HELP_MESSAGE = (
    '<p>&#8226 Hover over record to see detailed stats</p>');

  this.data_ = data;
  this.parent_ = parent;
}

/** Renders profiler output */
Profiler.prototype.render = function() {
  var content = this.parent_.append('div')
    .attr('class', 'profiler-content');

  var tooltip = this.parent_.append('div')
    .attr('class', 'content-tooltip content-tooltip-invisible');

  var recordsTable = content.append('div')
    .attr('class', 'profiler-record-table-wrapper')
    .append('div')
    .attr('class', 'profiler-record-table');

  this.renderLegend_(content);
  this.renderHelp_();

  var self = this;
  var records = recordsTable.selectAll('.profiler-record-normal')
    .data(this.data_.callStats)
    .enter()
    .append('tr')
    .attr('class', 'profiler-record-normal')
    .on('mouseover', function(d) { self.showTooltip_(this, tooltip, d); })
    .on('mouseout', function() { self.hideTooltip_(this, tooltip); });

  records.html(Profiler.formatProfilerRecord_);
};

/**
 * Shows tooltip.
 * @param {Object} element - Element representing profiler record.
 * @param {Object} tooltip - Element representing tooltip.
 * @param {Object} node - Object with profiler record info.
 */
Profiler.prototype.showTooltip_ = function(element, tooltip, node) {
  d3select.select(element).attr('class', 'profiler-record-highlight');
  tooltip.attr('class', 'content-tooltip content-tooltip-visible')
    .html('<p><b>Line number:</b> ' + node[1] +'</p>' +
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

/**
 * Formats profiler record.
 * @static
 * */
Profiler.formatProfilerRecord_ = function(data) {
  return (
      '<td class="profiler-record-percentage">' + data[4] + '%</td>' +
      '<td class="profiler-record-name">' +
        '<span class="profiler-record-funcname">' + data[2] + '</span>' + ' ' +
        '<span class="profiler-record-filename">' + data[8] + '</span>' + ':' +
        '<span class="profiler-record-lineno">' + data[1] + '</span>' +
      '</td>' +
      '<td class="profiler-record-cumtime">' + data[3] + 's</td>');
};

/** Renders profiler tab legend. */
Profiler.prototype.renderLegend_ = function(parent) {
  parent.append('div')
    .attr('class', 'profiler-legend')
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
  var profilerOutput = new Profiler(parent, data);
  profilerOutput.render();
}

module.exports = {
  'Profiler': Profiler,
  'renderProfilerOutput': renderProfilerOutput,
};
