/**
 * @file Code heatmap UI module.
 */

'use strict';
const d3 = require('d3');
const hljs = require('highlight.js');
try {
  require('./css/highlight.css');  // Necessary for code highlighter to work.
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
 * @property {string} HELP_MESSAGE - Tooltip help message.
 */
function CodeHeatmap(parent, data) {
  this.MIN_RUN_TIME = 0.000001;
  this.MAX_RUN_TIME = data.runTime;
  this.MIN_RUN_COLOR = '#ebfaeb';
  this.MAX_RUN_COLOR = '#47d147';
  this.HELP_MESSAGE = (
    '<p>&#8226 Hover over line to see execution time and ' +
    'line execution count.</p>');

  this.data_ = data;
  this.parent_ = parent;
  this.heatmapScale_ = d3.scalePow()
    .exponent(0.6)
    .domain([this.MIN_RUN_TIME, this.MAX_RUN_TIME])
    .range([this.MIN_RUN_COLOR, this.MAX_RUN_COLOR]);
}

/** Renders code heatmap. */
CodeHeatmap.prototype.render = function() {
  let pageContainer = this.parent_.append('div')
    .attr('id', 'heatmap-layout');

  this.renderHelp_();

  let moduleList = pageContainer.append('div')
    .attr('class', 'heatmap-module-list');

  moduleList.append('div')
    .attr('class', 'heatmap-module-header')
    .html('Inspected modules');

  let moduleTooltip = pageContainer.append('div')
    .attr('class', 'content-tooltip content-tooltip-invisible');

  moduleList.selectAll('.heatmap-module-name')
    .data(this.data_.heatmaps)
    .enter()
    .append('a')
    .attr('href', (d) => '#' + d.name)
    .append('div')
    .attr('class', 'heatmap-module-name')
    .style('background-color', (d) => this.heatmapScale_(d.runTime))
    .on('mouseover', (d) => this.showModuleTooltip_(
      moduleTooltip, d.runTime, this.data_.runTime))
    .on('mouseout', () => this.hideModuleTooltip_(moduleTooltip))
    .append('text')
    .html((d) => d.name);

  let codeContainer = pageContainer.append('div')
    .attr('class', 'heatmap-code-container');

  let heatmapContainer = codeContainer.selectAll('div')
    .data(this.data_.heatmaps)
    .enter()
    .append('div')
    .attr('class', 'heatmap-src-file');

  heatmapContainer.append('a')
    .attr('href', (d) => '#' + d.name)
    .attr('class', 'heatmap-src-code-header')
    .attr('id', (d) => d.name)
    .append('text')
    .html((d) => d.name);

  let renderedSources = [];
  for (let i = 0; i < this.data_.heatmaps.length; i++) {
    renderedSources.push(this.renderCode_(this.data_.heatmaps[i]));
  }

  let fileContainers = heatmapContainer.append('div')
    .attr('class', 'heatmap-src-code')
    .append('text')
    .html((d, i) => renderedSources[i].srcCode)
    .nodes();

  let codeTooltip = pageContainer.append('div')
    .attr('class', 'content-tooltip content-tooltip-invisible');

  codeContainer.selectAll('.heatmap-src-file')
    .each((d, i) => {
      d3.select(fileContainers[i]).selectAll('.heatmap-src-line-normal')
        .on('mouseover', (d, j, nodes) => {
          this.showCodeTooltip_(
            nodes[j], codeTooltip, renderedSources, i, j, this.data_.runTime);
        })
        .on('mouseout', (d, j, nodes) => {
          this.hideCodeTooltip_(nodes[j], codeTooltip); });
    });
};

/**
 * Shows tooltip with module running time.
 * @param {Object} tooltip - Tooltip element.
 * @param {number} moduleTime - Module running time.
 * @param {number} totalTime - Total running time.
 */
CodeHeatmap.prototype.showModuleTooltip_ = function(tooltip, moduleTime,
  totalTime) {
  let percentage = Math.round(10000 * moduleTime / totalTime) / 100;
  tooltip.attr('class', 'content-tooltip content-tooltip-visible')
    .html('<p><b>Time spent: </b>'+ moduleTime + ' s</p>' +
          '<p><b>Total running time: </b>' + totalTime + ' s</p>' +
          '<p><b>Percentage: </b>' + percentage + '%</p>')
    .style('left', d3.event.pageX)
    .style('top', d3.event.pageY);
};

/**
 * Hides tooltip with module running time.
 * @param {Object} tooltip - Tooltip element.
 */
CodeHeatmap.prototype.hideModuleTooltip_ = function(tooltip) {
  tooltip.attr('class', 'content-tooltip content-tooltip-invisible');
};

/**
 * Shows tooltip with line running time.
 * @param {Object} element - Highlighted line.
 * @param {Object} tooltip - Tooltip element.
 * @param {Object} sources - Code and code stats.
 * @param {number} fileIndex - Index of source code file.
 * @param {number} lineIndex - Index of line in file.
 * @param {number} totalTime - Module running time.
 */
CodeHeatmap.prototype.showCodeTooltip_ = function(
  element, tooltip, sources, fileIndex, lineIndex, totalTime) {
  if (!sources[fileIndex].countMap[lineIndex]) {
    return;
  }
  let lineRuntime = sources[fileIndex].timeMap[lineIndex];
  let lineRuncount = sources[fileIndex].countMap[lineIndex];
  let percentage = Math.round(10000 * lineRuntime / totalTime) / 100;
  d3.select(element).attr('class', 'heatmap-src-line-highlight');
  tooltip.attr('class', 'content-tooltip content-tooltip-visible')
    .html('<p><b>Time spent: </b>' + lineRuntime + ' s</p>' +
          '<p><b>Total running time: </b>' + totalTime + ' s</p>' +
          '<p><b>Percentage: </b>' + percentage + '%</p>' +
          '<p><b>Run count: </b>' + lineRuncount + '</p>')
    .style('left', d3.event.pageX)
    .style('top', d3.event.pageY);
};

/**
 * Hides tooltip with line running time.
 * @param {Object} element - Element representing highlighted line.
 * @param {Object} tooltip - Element representing tooltip.
 */
CodeHeatmap.prototype.hideCodeTooltip_ = function(element, tooltip) {
  d3.select(element).attr('class', 'heatmap-src-line-normal');
  tooltip.attr('class', 'content-tooltip content-tooltip-invisible');
};

/**
 * Renders profiled sources.
 * @param {Object} stats - Source code and all code stats.
 * @returns {Object}
 */
CodeHeatmap.prototype.renderCode_ = function(stats) {
  let outputCode = [], timeMap = {}, srcIndex = 0, countMap = {};
  for (let i = 0; i < stats.srcCode.length; i++) {
    if (stats.srcCode[i][0] === 'line') {
      let lineNumber = stats.srcCode[i][1], codeLine = stats.srcCode[i][2];
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
 * Formats single line of source code.
 * @param {number} lineNumber - Line number in code browser.
 * @param {string} codeLine - Current line of source code.
 * @param {number} lineRuntime - Line runtime.
 * @returns {string}
 */
CodeHeatmap.prototype.formatSrcLine_ = function(lineNumber, codeLine,
  lineRuntime) {
  let highlightedLine = hljs.highlight('python', codeLine).value;
  let backgroundColor = lineRuntime ? this.heatmapScale_(lineRuntime) : '';
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
 * Renders code heatmap and attaches it to the parent.
 * @param {Object} parent - Code heatmap parent element.
 * @param {Object} data - Data for code heatmap rendering.
 */
function renderCodeHeatmap(data, parent) {
  let heatmap = new CodeHeatmap(parent, data);
  heatmap.render();
}

module.exports = {
  'CodeHeatmap': CodeHeatmap,
  'renderCodeHeatmap': renderCodeHeatmap,
};
