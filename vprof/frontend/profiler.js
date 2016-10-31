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

  content.selectAll('.profiler-record')
    .data(this.data_.callStats)
    .enter()
    .append('div')
    .attr('class', 'profiler-record')
    .append('text')
    .html(Profiler.formatProfilerRecord_);
};

/** Formats profiler record. */
Profiler.formatProfilerRecord_ = function(data) {
  var functionName = data[2].replace('<', '[').replace('>', ']');
  return '<p>' + data[4] + "%  "+ functionName + '</p>';
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
