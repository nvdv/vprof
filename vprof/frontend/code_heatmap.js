/**
 * @file Code heatmap rendering.
 */

/* jshint strict: false, browser: true, globalstrict: true */
/* global require, module */

'use strict';
var d3 = require('d3');
var hljs = require('highlight.js');
require('./highlight.css');  // Includes code highlighter CSS.

/**
 * Represents code heatmap.
 * @constructor
 * @param {Object} parent - Parent element for code heatmap.
 * @param {Object} data - Data for code heatmap rendering.
 * @property {number} MIN_RUN_COUNT - Min value for line execution count.
 * @property {number} MAX_RUN_COUNT - Max value for line execution count.
 * @property {string} MIN_RUN_COLOR - Color that represents MIN_RUN_COUNT.
 * @property {string} MAX_RUN_COLOR - Color that represents MAX_RUN_COUNT.
 */
function CodeHeatmap(parent, data) {
  this.MIN_RUN_COUNT = 0;
  this.MAX_RUN_COUNT = 2500;
  this.MIN_RUN_COLOR = '#ebfaeb';
  this.MAX_RUN_COLOR = '#00cc44';

  this.data_ = data;
  this.parent_ = parent;
  this.heatmapScale_ = d3.scale.sqrt()
    .domain([this.MIN_RUN_COUNT, this.MAX_RUN_COUNT])
    .range([this.MIN_RUN_COLOR, this.MAX_RUN_COLOR]);
}

/** Renders code heatmap. */
CodeHeatmap.prototype.render = function() {
  var highlightedCode = CodeHeatmap.postProcessCode_(
      hljs.highlight('python', this.data_.srcCode).value);

  var codeContainer = this.parent_.append('div')
    .attr('id', 'code-container')
    .append('div')
    .attr('class', 'src-code')
    .html(highlightedCode);

  var tooltip = codeContainer.append('div')
    .attr('class', 'tooltip tooltip-invisible');

  var self = this;
  d3.selectAll('.src-line-normal')
    .style('background-color', this.changeBackgroundColor_.bind(this))
    .on('mouseover', function(_, i) { self.showTooltip_(this, tooltip, i); })
    .on('mouseout', function() { self.hideTooltip_(this, tooltip); });
};

/**
 * Returns line background color based on execution count.
 * @param {Object} _ - Unused argument.
 * @param {number} i - Line number.
 * @returns {string}
 */
CodeHeatmap.prototype.changeBackgroundColor_ = function(_, i) {
  var runCount = this.data_.heatmap[i + 1];
  return runCount ? this.heatmapScale_(runCount) : '';
};

/**
 * Shows line execution count inside tooltip and adds line highlighting.
 * @param {Object} element - Element representing highlighted line.
 * @param {Object} tooltip - Element representing tooltip.
 * @param {number} i - Source line number.
 */
CodeHeatmap.prototype.showTooltip_ = function(element, tooltip, i) {
  var runCount = this.data_.heatmap[i + 1];
  if (runCount) {
    d3.select(element).attr('class', 'src-line-highlight');
    tooltip.attr('class', 'tooltip tooltip-visible')
      .html('Execution count: ' + runCount)
      .style('left', d3.event.pageX)
      .style('top', d3.event.pageY);
  }
};

/**
 * Hides provided tooltip and removes line highlighting.
 * @param {Object} element - Element representing highlighted line.
 * @param {Object} tooltip - Element representing tooltip.
 */
CodeHeatmap.prototype.hideTooltip_ = function(element, tooltip) {
  d3.select(element).attr('class', 'src-line-normal');
  tooltip.attr('class', 'tooltip tooltip-invisible');
};

/**
 * Adds line numbers and additional formatting since highlight.js does not
 * support them.
 * @static
 * @param {string} srcCode - Python source code.
 * @returns {string}
 */
CodeHeatmap.postProcessCode_ = function(srcCode) {
  var lines = srcCode.split('\n');
  for (var i = 1; i < lines.length + 1; i++) {
    lines[i - 1] = (
        "<div class='src-line-normal'>" +
            "<div class='src-line-number'>" + i + "</div>" +
            "<div class='src-line-code'>" + lines[i - 1] + "</div>" +
        "</div>");
  }
  return lines.join('');
};

/**
 * Renders code heatmap and attaches it to parent.
 * @param {Object} parent - Parent element for code heatmap.
 * @param {Object} data - Data for code heatmap rendering.
 */
function renderCodeHeatmap(data, parent) {
  var heatmap = new CodeHeatmap(parent, data);
  heatmap.render();
}

module.exports = {
  'CodeHeatmap': CodeHeatmap,
  'renderCodeHeatmap': renderCodeHeatmap,
};
