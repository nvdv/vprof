/**
 * @file Code heatmap rendering.
 */

'use strict';
var d3scale = require('d3-scale');
var d3select = require('d3-selection');

var hljs = require('highlight.js');
try {
  require('./highlight.css');  // Includes code highlighter CSS.
} catch (e) {
  // Do nothing, it's workaround for Jest test runner.
}

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
  this.MIN_RUN_TIME = 0.000001;
  this.MAX_RUN_TIME = data.runTime;
  this.MIN_RUN_COLOR = '#ebfaeb';
  this.MAX_RUN_COLOR = '#47d147';
  this.HELP_MESSAGE = (
    '<p>&#8226 Hover over line to see line execution count.</p>');

  this.data_ = data;
  this.parent_ = parent;
  this.heatmapScale_ = d3scale.scalePow()
    .exponent(0.6)
    .domain([this.MIN_RUN_TIME, this.MAX_RUN_TIME])
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

  var moduleTooltip = pageContainer.append('div')
    .attr('class', 'content-tooltip content-tooltip-invisible');

  var self = this;
  moduleList.selectAll('.heatmap-module-name')
    .data(this.data_.heatmaps)
    .enter()
    .append('a')
    .attr('href', function(d) { return '#' + d.name; })
    .append('div')
    .attr('class', 'heatmap-module-name')
    .style('background-color', function(d) {
      return self.heatmapScale_(d.runTime); })
    .on('mouseover', function(d) {
      self.showModuleTooltip_(moduleTooltip, d.runTime, self.data_.runTime);
    })
    .on('mouseout', function() { self.hideModuleTooltip_(moduleTooltip); })
    .append('text')
    .html(function(d) { return d.name; });

  var codeContainer = pageContainer.append('div')
    .attr('class', 'heatmap-code-container');

  var heatmapContainer = codeContainer.selectAll('div')
    .data(this.data_.heatmaps)
    .enter()
    .append('div')
    .attr('class', 'heatmap-src-file');

  heatmapContainer.append('a')
    .attr('href', function(d) { return '#' + d.name; })
    .attr('class', 'heatmap-src-code-header')
    .attr('id', function(d) { return d.name; })
    .append('text')
    .html(function(d) { return d.name; });

  var renderedSources = [];
  for (var i = 0; i < this.data_.heatmaps.length; i++) {
    renderedSources.push(this.renderCode_(this.data_.heatmaps[i]));
  }

  var fileContainers = heatmapContainer.append('div')
    .attr('class', 'heatmap-src-code')
    .append('text')
    .html(function(_, i) { return renderedSources[i].srcCode; })
    .nodes();

  var codeTooltip = pageContainer.append('div')
    .attr('class', 'content-tooltip content-tooltip-invisible');

  var self = this;
  codeContainer.selectAll('.heatmap-src-file')
    .each(function(_, i) {
      d3select.select(fileContainers[i]).selectAll('.heatmap-src-line-normal')
        .on('mouseover', function(_, j) {
          self.showCodeTooltip_(
              this, codeTooltip, renderedSources, i, j, self.data_.runTime);
        })
        .on('mouseout', function() {
          self.hideCodeTooltip_(this, codeTooltip); });
    });
};

/**
 * Shows module tooltip with running time.
 * @param {Object} tooltip - Element representing tooltip.
 * @param {number} moduleTime - Module running time.
 * @param {number} totalTime - Total running time.
 */
CodeHeatmap.prototype.showModuleTooltip_ = function(tooltip, moduleTime,
                                                    totalTime) {
  var percentage = Math.round(10000 * moduleTime / totalTime) / 100;
  tooltip.attr('class', 'content-tooltip content-tooltip-visible')
    .html('<p><b>Time spent: </b>'+ moduleTime + ' s</p>' +
          '<p><b>Total running time: </b>' + totalTime + ' s</p>' +
          '<p><b>Percentage: </b>' + percentage + '%</p>')
    .style('left', d3select.event.pageX)
    .style('top', d3select.event.pageY);
};

/**
 * Hides module tooltip.
 * @param {Object} tooltip - Element representing tooltip.
 */
CodeHeatmap.prototype.hideModuleTooltip_ = function(tooltip) {
  tooltip.attr('class', 'content-tooltip content-tooltip-invisible');
};

/**
 * Shows line execution count inside code tooltip and adds line highlighting.
 * @param {Object} element - Element representing highlighted line.
 * @param {Object} tooltip - Element representing tooltip.
 * @param {Object} sources - Object that represents sources with stats.
 * @param {number} fileIndex - Index of file with source code.
 * @param {number} lineIndex - Index of line in file.
 * @param {number} totalTime - Module running time.
 */
CodeHeatmap.prototype.showCodeTooltip_ = function(
    element, tooltip, sources, fileIndex, lineIndex, totalTime) {
  if (!sources[fileIndex].countMap[lineIndex]) {
    return;
  }
  var lineRuntime = sources[fileIndex].timeMap[lineIndex];
  var lineRuncount = sources[fileIndex].countMap[lineIndex];
  var percentage = Math.round(10000 * lineRuntime / totalTime) / 100;
  d3select.select(element).attr('class', 'heatmap-src-line-highlight');
  tooltip.attr('class', 'content-tooltip content-tooltip-visible')
    .html('<p><b>Time spent: </b>' + lineRuntime + ' s</p>' +
          '<p><b>Total running time: </b>' + totalTime + ' s</p>' +
          '<p><b>Percentage: </b>' + percentage + '%</p>' +
          '<p><b>Run count: </b>' + lineRuncount + '</p>')
    .style('left', d3select.event.pageX)
    .style('top', d3select.event.pageY);
};

/**
 * Hides code tooltip and removes line highlighting.
 * @param {Object} element - Element representing highlighted line.
 * @param {Object} tooltip - Element representing tooltip.
 */
CodeHeatmap.prototype.hideCodeTooltip_ = function(element, tooltip) {
  d3select.select(element).attr('class', 'heatmap-src-line-normal');
  tooltip.attr('class', 'content-tooltip content-tooltip-invisible');
};

/**
 * Renders source code.
 * @param {Object} stats - Object that contains source code and all code stats.
 * @returns {Object}
 */
CodeHeatmap.prototype.renderCode_ = function(stats) {
  var outputCode = [], timeMap = {}, srcIndex = 0, countMap = {};
  for (var i = 0; i < stats.srcCode.length; i++) {
    if (stats.srcCode[i][0] === 'line') {
      var lineNumber = stats.srcCode[i][1], codeLine = stats.srcCode[i][2];
      outputCode.push(
          this.formatSrcLine_(lineNumber, codeLine, stats.heatmap[lineNumber]));
      timeMap[srcIndex] = stats.heatmap[lineNumber];
      countMap[srcIndex] = stats.executionCount[lineNumber];
      srcIndex++;
    } else if (stats.srcCode[i][0] === 'skip') {
      outputCode.push(
          "<div class='heatmap-skip-line'>" + stats.srcCode[i][1] +
          ' lines skipped</div>');
    }
  }
  return {
    'srcCode': outputCode.join(''),
    'timeMap': timeMap,
    'countMap': countMap
  };
};

/**
 * Formats single line of Python source file.
 * @param {number} lineNumber - Line number for code browser.
 * @param {string} codeLine - Source line.
 * @param {number} lineRuntime - Line run time.
 * @returns {string}
 */
CodeHeatmap.prototype.formatSrcLine_ = function(lineNumber, codeLine,
                                                lineRuntime) {
  var highlightedLine = hljs.highlight('python', codeLine).value;
  var backgroundColor = lineRuntime ? this.heatmapScale_(lineRuntime) : '';
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
