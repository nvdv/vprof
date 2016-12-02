/**
 * @file Code heatmap rendering.
 */

'use strict';
var d3scale = require('d3-scale');
var d3select = require('d3-selection');

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
  this.MIN_RUN_COUNT = 1;
  this.MAX_RUN_COUNT = 10000;
  this.MIN_RUN_COLOR = '#ebfaeb';
  this.MAX_RUN_COLOR = '#47d147';
  this.COLOR_SCALE_POWER = 0.25;
  this.HELP_MESSAGE = (
    '<p>&#8226 Hover over line to see line execution count.</p>');

  this.data_ = data;
  this.parent_ = parent;
  this.heatmapScale_ = d3scale.scaleLog()
    .domain([this.MIN_RUN_COUNT, this.MAX_RUN_COUNT])
    .range([this.MIN_RUN_COLOR, this.MAX_RUN_COLOR]);
}

/** Renders code heatmap. */
CodeHeatmap.prototype.render = function() {
  var pageContainer = this.parent_.append('div')
    .attr('id', 'heatmap-layout');

  this.renderHelp_();

  var moduleList = pageContainer.append('div')
    .attr('class', 'heatmap-module-list');

  moduleList.append('div')
    .attr('class', 'heatmap-module-header')
    .html('Inspected modules');

  moduleList.selectAll('.heatmap-module-name')
    .data(this.data_)
    .enter()
    .append('a')
    .attr('href', function(d) { return '#' + d.objectName; })
    .append('div')
    .attr('class', 'heatmap-module-name')
    .append('text')
    .html(function(d) { return d.objectName; });

  var codeContainer = pageContainer.append('div')
    .attr('class', 'heatmap-code-container');

  var heatmapContainer = codeContainer.selectAll('div')
    .data(this.data_)
    .enter()
    .append('div')
    .attr('class', 'heatmap-src-file');

  heatmapContainer.append('a')
    .attr('href', function(d) { return '#' + d.objectName; })
    .attr('class', 'heatmap-src-code-header')
    .attr('id', function(d) { return d.objectName; })
    .append('text')
    .html(function(d) { return d.objectName; });

  var renderedSources = [];
  for (var i = 0; i < this.data_.length; i++) {
    renderedSources.push(
        this.renderCode_(this.data_[i].srcCode,
                         this.data_[i].heatmap));
  }

  var fileContainers = heatmapContainer.append('div')
    .attr('class', 'heatmap-src-code')
    .append('text')
    .html(function(_, i) { return renderedSources[i].srcCode; })
    .nodes();

  var tooltip = pageContainer.append('div')
    .attr('class', 'content-tooltip content-tooltip-invisible');

  var self = this;
  codeContainer.selectAll('.heatmap-src-file')
    .each(function(_, i) {
      d3select.select(fileContainers[i]).selectAll('.heatmap-src-line-normal')
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
  d3select.select(element).attr('class', 'heatmap-src-line-highlight');
  tooltip.attr('class', 'content-tooltip content-tooltip-visible')
    .html('<b>Execution count: </b>' + runCount)
    .style('left', d3select.event.pageX)
    .style('top', d3select.event.pageY);
};

/**
 * Hides provided tooltip and removes line highlighting.
 * @param {Object} element - Element representing highlighted line.
 * @param {Object} tooltip - Element representing tooltip.
 */
CodeHeatmap.prototype.hideTooltip_ = function(element, tooltip) {
  d3select.select(element).attr('class', 'heatmap-src-line-normal');
  tooltip.attr('class', 'content-tooltip content-tooltip-invisible');
};

/**
 * Renders code.
 * @param {string} srcCode - Python source code.
 * @param {Object} heatmap - Python source heatmap.
 * @returns {Object}
 */
CodeHeatmap.prototype.renderCode_ = function(srcCode, heatmap) {
  var resultCode = [], lineMap = {}, srcIndex = 0;
  for (var i = 0; i < srcCode.length; i++) {
    if (srcCode[i][0] === 'line') {
      var lineNumber = srcCode[i][1], codeLine = srcCode[i][2];
      var runCount = heatmap[lineNumber];
      resultCode.push(
          this.formatSrcLine_(lineNumber, codeLine, runCount));
      lineMap[srcIndex] = runCount;
      srcIndex++;
    } else if (srcCode[i][0] === 'skip') {
      resultCode.push(
          "<div class='heatmap-skip-line'>" + srcCode[i][1] +
          ' lines skipped</div>');
    }
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
CodeHeatmap.prototype.formatSrcLine_ = function(lineNumber, codeLine,
                                                runCount) {
  var highlightedLine = hljs.highlight('python', codeLine).value;
  var backgroundColor = runCount ? this.heatmapScale_(runCount) : '';
  return (
      "<div class='heatmap-src-line-normal' style='background-color: " +
        backgroundColor + "'>" +
          "<div class='heatmap-src-line-number'>" + lineNumber + "</div>" +
          "<div class='heatmap-src-line-code'>" + highlightedLine + "</div>" +
      "</div>");
};

/** Renders code heatmap help. */
CodeHeatmap.prototype.renderHelp_ = function() {
  this.parent_.append('div')
    .attr('class', 'tabhelp inactive-tabhelp')
    .html(this.HELP_MESSAGE);
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
