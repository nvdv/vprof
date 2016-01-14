/**
 * Renders code heatmap.
 */

/* jshint strict: false, browser: true, globalstrict: true */
/* global require, module */

'use strict';
var d3 = require('d3');
var hljs = require('highlight.js');
require('./highlight.css');  // Includes code highlighter CSS.

var MIN_RUN_COUNT = 0;
var MAX_RUN_COUNT = 2500;
var MIN_RUN_COLOR = '#ebfaeb';
var MAX_RUN_COLOR = '#00cc44';

/** Adds line numbers and additional formatting since highlight.js does not
    support them. */
function postProcessCode_(srcCode) {
  var lines = srcCode.split('\n');
  for (var i = 1; i < lines.length + 1; i++) {
    lines[i - 1] = (
        "<div class='src-line-normal'>" +
            "<div class='src-line-number'>" + i + "</div>" +
            "<div class='src-line-code'>" + lines[i - 1] + "</div>" +
        "</div>");
  }
  return lines.join('');
}

/** Renders code heatmap. */
function renderCodeHeatmap(data, parent) {
  var highlightedCode = postProcessCode_(
      hljs.highlight('python', data.srcCode).value);

  var codeContainer = parent.append('div')
    .attr('id', 'code-container')
    .append('div')
    .attr('class', 'src-code')
    .html(highlightedCode);

  var tooltip = codeContainer.append('div')
    .attr('class', 'tooltip tooltip-invisible');

  var heatmapScale = d3.scale.sqrt()
    .domain([MIN_RUN_COUNT, MAX_RUN_COUNT])
    .range([MIN_RUN_COLOR, MAX_RUN_COLOR]);

  d3.selectAll('.src-line-normal')
    .style('background-color', function(d, i) {
      var runCount = data.heatmap[i + 1];
      return runCount ? heatmapScale(runCount) : '';
    })
    .on('mouseover', function(d, i) {
      var runCount = data.heatmap[i + 1];
      if (runCount) {
        d3.select(this).attr('class', 'src-line-highlight');
        tooltip.attr('class', 'tooltip tooltip-visible')
          .html('Execution count: ' + runCount)
          .style('left', d3.event.pageX)
          .style('top', d3.event.pageY);
      }
    })
    .on('mouseout', function(d) {
      d3.select(this).attr('class', 'src-line-normal');
      tooltip.attr('class', 'tooltip tooltip-invisible');
    });
}

module.exports = {
  'postProcessCode_': postProcessCode_,
  'renderCodeHeatmap': renderCodeHeatmap,
};
