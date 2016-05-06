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
    .attr('class', 'module-list');

  moduleList.append('div')
    .attr('class', 'module-header')
    .html('Inspected modules');

  moduleList.selectAll('.module-name')
    .data(this.data_)
    .enter()
    .append('a')
    .attr('href', function(d) { return '#' + d.objectName; })
    .append('div')
    .attr('class', 'module-name')
    .append('text')
    .html(function(d) { return d.objectName; });

  var codeContainer = pageContainer.append('div')
    .attr('class', 'code-container');

  var heatmapContainer = codeContainer.selectAll('div')
    .data(this.data_)
    .enter()
    .append('div')
    .attr('class', 'src-file');

  heatmapContainer.append('a')
    .attr('href', function(d) { return '#' + d.objectName; })
    .attr('class', 'src-code-header')
    .attr('id', function(d) { return d.objectName; })
    .append('text')
    .html(function(d) { return d.objectName; });

  var renderedSources = [];
  for (var i = 0; i < this.data_.length; i++) {
    renderedSources.push(
        this.processCode_(this.data_[i].srcCode,
                          this.data_[i].heatmap,
                          this.data_[i].skipMap));
  }

  var fileContainers = heatmapContainer.append('div')
    .attr('class', 'src-code')
    .append('text')
    .html(function(_, i) { return renderedSources[i].srcCode; });

  var tooltip = pageContainer.append('div')
    .attr('class', 'tooltip tooltip-invisible');

  var self = this;
  codeContainer.selectAll('.src-file')
    .each(function(_, i) {
      d3.select(fileContainers[0][i]).selectAll('.src-line-normal')
        .on('mouseover', function(_, j) {
          var runCount = renderedSources[i].lineMap[j];
          if(runCount) {
            self.showTooltip_(this, tooltip, runCount); }})
        .on('mouseout', function() { self.hideTooltip_(this, tooltip); });
    });
};

/**
 * Shows line execution count inside tooltip and adds line highlighting.
 * @param {Object} element - Element representing highlighted line.
 * @param {Object} tooltip - Element representing tooltip.
 * @param {number} runCount - Number of line runs.
 */
CodeHeatmap.prototype.showTooltip_ = function(element, tooltip, runCount) {
  d3.select(element).attr('class', 'src-line-highlight');
  tooltip.attr('class', 'tooltip tooltip-visible')
    .html('Execution count: ' + runCount)
    .style('left', d3.event.pageX)
    .style('top', d3.event.pageY);
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
 * @param {string} srcCode - Python source code.
 * @param {Object} heatmap - Python source heatmap.
 * @param {Object} skipMap - Mapping that shows correspondence between lines
 *                           on the screen and Python sources.
 * @returns {Object}
 */
CodeHeatmap.prototype.processCode_ = function(srcCode, heatmap, skipMap) {
  if (Object.keys(skipMap).length !== 0) {
    return this.renderCodeWithSkips_(srcCode, heatmap, skipMap);
  }
  return this.renderCode_(srcCode, heatmap);
};

/**
 * Renders code without skip map.
 * @param {string} srcCode - Python source code.
 * @param {Object} heatmap - Python source heatmap.
 * @returns {Object}
 */
CodeHeatmap.prototype.renderCode_ = function(srcCode, heatmap) {
  var resultCode = [], lineMap = {};
  for (var i = 0; i < srcCode.length; i++) {
    var lineNumber = srcCode[i][0], codeLine = srcCode[i][1];
    var runCount = heatmap[lineNumber];
    resultCode.push(
        this.formatSrcLine_(lineNumber, codeLine, runCount));
    lineMap[i] = runCount;
  }
  return {'srcCode': resultCode.join(''), 'lineMap': lineMap};
};

/**
 * Renders code with skip map.
 * @param {string} srcCode - Python source code.
 * @param {Object} heatmap - Python source heatmap.
 * @param {Object} skipMap - Mapping that shows correspondence between lines
 *                           on the screen and Python sources.
 * @returns {Object}
 */
CodeHeatmap.prototype.renderCodeWithSkips_ = function(srcCode, heatmap, skipMap) {
  var resultCode = [], lineMap = {};
  var codeIndex = 0, currSkipLine = 0;
  for (var i = 0; i < skipMap.length; i++) {
    var skipLine = skipMap[i][0], skipLength = skipMap[i][1];
    for (var j = currSkipLine; j < skipLine; j++) {
      var lineNumber = srcCode[j][0], codeLine = srcCode[j][1];
      var runCount = heatmap[lineNumber];
      resultCode.push(
          this.formatSrcLine_(lineNumber, codeLine, runCount));
      lineMap[codeIndex] = runCount;
      codeIndex++;
    }
    currSkipLine = skipLine + skipLength - 1;
    resultCode.push(
        "<div class='skip-line'>" + skipLength + ' lines skipped</div>');
  }
  return {'srcCode': resultCode.join(''), 'lineMap': lineMap};
};

/**
 * Formats single line of Python source file.
 * @param {number} lineNumber - Line number for code browser.
 * @param {string} codeLine - Source line.
 * @param {number} runCount - Number of line runs.
 * @returns {string}
 */
CodeHeatmap.prototype.formatSrcLine_ = function(lineNumber, codeLine, runCount) {
  var highlightedLine = hljs.highlight('python', codeLine).value;
  var backgroundColor = runCount ? this.heatmapScale_(runCount) : '';
  return (
      "<div class='src-line-normal' style='background-color: " +
        backgroundColor + "'>" +
          "<div class='src-line-number'>" + lineNumber + "</div>" +
          "<div class='src-line-code'>" + highlightedLine + "</div>" +
      "</div>");
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
