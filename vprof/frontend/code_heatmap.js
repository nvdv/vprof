/**
 * Renders code heatmap.
 */

/* jshint strict: false, browser: true, globalstrict: true */
/* global require, module */

'use strict';
var d3 = require('d3');
var hljs = require('highlight.js');
require('./highlight.css');  // Includes code highlighter CSS.

/** Class constructor. */
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

/** Changes line background color based on execution count. */
CodeHeatmap.prototype.changeBackgroundColor_ = function(_, i) {
  var runCount = this.data_.heatmap[i + 1];
  return runCount ? this.heatmapScale_(runCount) : '';
};

/** Shows line execution count inside tooltip and adds line highlighting. */
CodeHeatmap.prototype.showTooltip_ = function(element, tooltip, index) {
  var runCount = this.data_.heatmap[index + 1];
  if (runCount) {
    d3.select(element).attr('class', 'src-line-highlight');
    tooltip.attr('class', 'tooltip tooltip-visible')
      .html('Execution count: ' + runCount)
      .style('left', d3.event.pageX)
      .style('top', d3.event.pageY);
  }
};

/** Hides provided tooltip and removes line highlighting. */
CodeHeatmap.prototype.hideTooltip_ = function(element, tooltip) {
  d3.select(element).attr('class', 'src-line-normal');
  tooltip.attr('class', 'tooltip tooltip-invisible');
};

/** Adds line numbers and additional formatting since highlight.js does not
    support them. */
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

/** Factory function to call externally. */
function renderCodeHeatmap(data, parent) {
  var heatmap = new CodeHeatmap(parent, data);
  heatmap.render();
}

module.exports = {
  'CodeHeatmap': CodeHeatmap,
  'renderCodeHeatmap': renderCodeHeatmap,
};
