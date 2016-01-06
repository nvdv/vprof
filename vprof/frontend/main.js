/**
 * Renders all stats.
 */

/* jshint strict: false, browser: true, globalstrict: true */
/* global require, module */

'use strict';
var d3 = require('d3');
var flame_chart = require('./flame_chart.js');
var memory_stats = require('./memory_stats.js');
var code_heatmap = require('./code_heatmap.js');

var JSON_URI = 'profile';

/** Creates flame chart tab header with specified status and
 *  appends it to the parent node.
 */
function createFlameChartTab_(parent, status) {
  parent.append('li')
    .attr('class', status)
    .text('Flame chart')
    .on('click', function(d) {
      d3.selectAll('li')
        .attr('class', 'not-selected');
      d3.select(this)
        .attr('class', 'selected');
      showTab_('flame-chart');
    });
}

/** Creates memory stats tab header with specified status and
 *  appends it to the parent node.
 */
function createMemoryChartTab_(parent, status) {
  parent.append('li')
    .attr('class', status)
    .text('Memory stats')
    .on('click', function(d) {
      d3.selectAll('li')
        .attr('class', 'not-selected');
      d3.select(this)
        .attr('class', 'selected');
      showTab_('memory-chart');
    });
}

/** Creates code heatmap tab header with specified status and
 *  appends it to the parent node.
 */
function createCodeHeatmapTab_(parent, status) {
  parent.append('li')
    .attr('class', status)
    .text('Code heatmap')
    .on('click', function(d) {
      d3.selectAll('li')
        .attr('class', 'not-selected');
      d3.select(this)
        .attr('class', 'selected');
      showTab_('code-heatmap');
    });
}

/** Renders whole page. */
function renderPage(data) {
  var tabHeader = d3.select('body')
    .append('ul')
    .attr('class', 'tab-header');

  var flameChart = d3.select('body')
    .append('div')
    .attr('class', 'flame-chart tab-content')
    .attr('id', 'flame-chart')
    .attr('style', 'display: none');

  var memoryChart = d3.select('body')
    .append('div')
    .attr('class', 'memory-chart tab-content')
    .attr('id', 'memory-chart')
    .attr('style', 'display: none');

  var codeHeatmap = d3.select('body')
    .append('div')
    .attr('class', 'code-heatmap tab-content')
    .attr('id', 'code-heatmap')
    .attr('style', 'display: none');

  // TODO(nvdv): Refactor this loop.
  var props = Object.keys(data);
  for (var i = 0; i < props.length; i++) {
    var status = (i === 0) ? 'selected' : 'not-selected';
    var display = (i === 0) ? 'block' : 'none';
    switch (props[i]) {
      case 'c':
        createFlameChartTab_(tabHeader, status);
        flame_chart.renderFlameChart(data.c, flameChart);
        flameChart.attr('style', 'display: ' + display);
        break;
      case 'm':
        createMemoryChartTab_(tabHeader, status);
        memory_stats.renderMemoryStats(data.m, memoryChart);
        memoryChart.attr('style', 'display: ' + display);
        break;
      case 'h':
        createCodeHeatmapTab_(tabHeader, status);
        code_heatmap.renderCodeHeatmap(data.h, codeHeatmap);
        codeHeatmap.attr('style', 'display:' + display);
        break;
    }
  }
}

/** Shows tab specified by tabID. */
function showTab_(tabId) {
  var allTabs = document.getElementsByClassName('tab-content');
  for (var i = 0; i < allTabs.length; i++) {
    allTabs[i].style.display = 'none';
  }
  var currentTab = document.getElementById(tabId);
  currentTab.style.display = 'block';
}

/** Main function. */
function main() {
  d3.json(JSON_URI, function(data) {
    renderPage(data);
  });
}

main();
