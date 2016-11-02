/**
 * @file Profiler output rendering.
 */

'use strict';
var d3 = require('d3');

/**
 * Represents Python profiler output.
 * @constructor
 * @param {Object} parent - Parent element for profiler output.
 * @param {Object} data - Data for rendering.
 */
function Profiler(parent, data) {
  this.data_ = data;
  this.parent_ = parent;
}

/** Renders profiler output */
Profiler.prototype.render = function() {
  var content = this.parent_.append('div')
    .attr('class', 'profiler-content');

  var tooltip = this.parent_.append('div')
    .attr('class', 'content-tooltip content-tooltip-invisible');

  var self = this;
  content.selectAll('.profiler-record')
    .data(this.data_.callStats)
    .enter()
    .append('div')
    .attr('class', 'profiler-record')
    .append('text')
    .html(Profiler.formatProfilerRecord_)
    .on('mouseover', function(d) { self.showTooltip_(this, tooltip, d); })
    .on('mouseout', function() { self.hideTooltip_(this, tooltip); });

};

/**
 * Shows tooltip.
 * @param {Object} element - Element representing profiler record.
 * @param {Object} tooltip - Element representing tooltip.
 * @param {Object} node - Object with profiler record info.
 */
Profiler.prototype.showTooltip_ = function(element, tooltip, node) {
  var filename = node[0].replace('<', '[').replace('>', ']');
  var lineno = node[1];
  var cumulativeTime = node[3];
  var numberOfCalls = node[5];
  var cumulativeCalls = node[6];
  var timePerCall = node[7];
  tooltip.attr('class', 'content-tooltip content-tooltip-visible')
    .html('<p><b>Line number:</b> ' + lineno +'</p>' +
          '<p><b>Filename:</b> ' + filename +'</p>' +
          '<p><b>Cumulative time:</b> ' + cumulativeTime +'s</p>' +
          '<p><b>Number of calls:</b> ' + numberOfCalls +'</p>' +
          '<p><b>Cumulative calls:</b> ' + cumulativeCalls +'</p>' +
          '<p><b>Time per call:</b> ' + timePerCall +'s</p>')
    .style('left', d3.event.pageX)
    .style('top', d3.event.pageY);
};

/**
 * Hides tooltip.
 * @param {Object} element - Element representing profiler record.
 * @param {Object} tooltip - Element representing tooltip.
 */
Profiler.prototype.hideTooltip_ = function(element, tooltip) {
  tooltip.attr('class', 'content-tooltip content-tooltip-invisible');
};

/** Formats profiler record. */
Profiler.formatProfilerRecord_ = function(data) {
  var functionName = data[2].replace('<', '[').replace('>', ']');
  return '<p>' + data[4] + '% '+ functionName + '</p>';
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
