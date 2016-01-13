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

/** Creates empty hidden div with specified ID. */
function createHiddenTabContent_(content_id) {
  return d3.select('body')
    .append('div')
    .attr('class', 'tab-content')
    .attr('id', content_id)
    .attr('style', 'display: none');
}

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

  var props = Object.keys(data);
  for (var i = 0; i < props.length; i++) {
    var status = (i === 0) ? 'selected' : 'not-selected';
    var display = (i === 0) ? 'block' : 'none';
    switch (props[i]) {
      case 'c':
        createFlameChartTab_(tabHeader, status);
        var flameChart = createHiddenTabContent_('flame-chart');
        flame_chart.renderFlameChart(data.c, flameChart);
        flameChart.attr('style', 'display: ' + display);
        break;
      case 'm':
        createMemoryChartTab_(tabHeader, status);
        var memoryChart = createHiddenTabContent_('memory-chart');
        memory_stats.renderMemoryStats(data.m, memoryChart);
        memoryChart.attr('style', 'display: ' + display);
        break;
      case 'h':
        createCodeHeatmapTab_(tabHeader, status);
        var codeHeatmap = createHiddenTabContent_('code-heatmap');
        code_heatmap.renderCodeHeatmap(data.h, codeHeatmap);
        codeHeatmap.attr('style', 'display: ' + display);
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
