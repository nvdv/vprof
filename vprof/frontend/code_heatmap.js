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
  var pageContainer = this.parent_.append('div')
    .attr('id', 'heatmap-layout');

  var moduleList = pageContainer.append('div')
    .attr('class', 'module-list')
    .html('Modules')
    .selectAll('div')
    .data(this.data_)
    .enter()
    .append('a')
    .attr('href', function(d) { return '#' + d.objectName; })
    .append('div')
    .attr('class', 'src-code-header')
    .append('text')
    .html(function(d) { return d.objectName; });

  var codeContainer = pageContainer.append('div')
    .attr('class', 'code-container');

  var heatmapContainer = codeContainer.selectAll('div')
    .data(this.data_)
    .enter()
    .append('div')
    .attr('class', 'src-file');

  heatmapContainer.append('div')
    .append('a')
    .attr('href', function(d) { return '#' + d.objectName; })
    .attr('class', 'src-code-header')
    .attr('id', function(d) { return d.objectName; })
    .append('text')
    .html(function(d) { return d.objectName; });

  var fileContainers = heatmapContainer.append('div')
    .attr('class', 'src-code')
    .append('text')
    .html(function(d) { return CodeHeatmap.processCode_(d.srcCode); });

  var tooltip = pageContainer.append('div')
    .attr('class', 'tooltip tooltip-invisible');

  var self = this;
  codeContainer.selectAll('.src-file')
    .each(function(d, i) {
      d3.select(fileContainers[0][i]).selectAll('.src-line-normal')
        .style('background-color', function(_, j) {
            return self.changeBackgroundColor_(d, j); })
        .on('mouseover', function(_, j) {
            self.showTooltip_(this, tooltip, d, j); })
        .on('mouseout', function() {
            self.hideTooltip_(this, tooltip); });
    });
};

/**
 * Returns line background color based on execution count.
 * @param {Object} data - Object with heatmap data for current src file.
 * @param {number} i - Line number.
 * @returns {string}
 */
CodeHeatmap.prototype.changeBackgroundColor_ = function(data, i) {
  var codeLine = data.srcCode[i][0];
  var runCount = data.heatmap[codeLine];
  return runCount ? this.heatmapScale_(runCount) : '';
};

/**
 * Shows line execution count inside tooltip and adds line highlighting.
 * @param {Object} element - Element representing highlighted line.
 * @param {Object} tooltip - Element representing tooltip.
 * @param {Object} data - Object with heatmap data for current src file.
 * @param {number} i - Source line number.
 */
CodeHeatmap.prototype.showTooltip_ = function(element, tooltip, data, i) {
  var codeLine = data.srcCode[i][0];
  var runCount = data.heatmap[codeLine];
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
 * Adds line numbers and code highlighting.
 * @static
 * @param {string} srcCode - Python source code.
 * @returns {string}
 */
CodeHeatmap.processCode_ = function(srcCode) {
  var code = [];
  for (var i = 0; i < srcCode.length; i++) {
    var lineNumber = srcCode[i][0], codeLine = srcCode[i][1];
    var highlightedLine = hljs.highlight('python', codeLine).value;
    var currLine = (
        "<div class='src-line-normal'>" +
            "<div class='src-line-number'>" + lineNumber + "</div>" +
            "<div class='src-line-code'>" + highlightedLine + "</div>" +
        "</div>");
    code.push(currLine);
  }
  return code.join('');
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
