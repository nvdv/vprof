/**
 * @file Page rendering module.
 */

/* jshint strict: false, browser: true, globalstrict: true */
/* global require, module */

'use strict';
var d3 = require('d3');
var flame_chart = require('./flame_chart.js');
var memory_stats = require('./memory_stats.js');
var code_heatmap = require('./code_heatmap.js');

var JSON_URI = 'profile';
var POLL_INTERVAL = 500;  // msec

/**
 * Creates empty div with specified ID and class tab-content.
 * @param {string} id - div ID.
 */
function createTabContent_(id) {
  return d3.select('body')
    .append('div')
    .attr('class', 'tab-content')
    .attr('id', id);
}

/**
 *  Creates flame chart tab header with specified status and
 *  appends it to the parent node.
 *  @param {Object} parent - Parent element to append tab to.
 *  @param {status} status - Specified tab status.
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

/**
 *  Creates memory stats tab header with specified status and
 *  appends it to the parent node.
 *  @param {Object} parent - Parent element to append tab to.
 *  @param {status} status - Specified tab status.
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

/**
 *  Creates code heatmap tab header with specified status and
 *  appends it to the parent node.
 *  @param {Object} parent - Parent element to append tab to.
 *  @param {status} status - Specified tab status.
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

/**
 * Renders stats page.
 * @param {Object} data - Data for page rendering.
 */
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
        var flameChart = createTabContent_('flame-chart');
        flame_chart.renderFlameChart(data.c, flameChart);
        flameChart.attr('style', 'display: ' + display);
        break;
      case 'm':
        createMemoryChartTab_(tabHeader, status);
        var memoryChart = createTabContent_('memory-chart');
        memory_stats.renderMemoryStats(data.m, memoryChart);
        memoryChart.attr('style', 'display: ' + display);
        break;
      case 'h':
        createCodeHeatmapTab_(tabHeader, status);
        var codeHeatmap = createTabContent_('code-heatmap');
        code_heatmap.renderCodeHeatmap(data.h, codeHeatmap);
        codeHeatmap.attr('style', 'display: ' + display);
        break;
    }
  }
}

/**
  * Makes tab specified by tabId active.
  * @param {string} tabId - Next active tab identifier.
  */
function showTab_(tabId) {
  var allTabs = document.getElementsByClassName('tab-content');
  for (var i = 0; i < allTabs.length; i++) {
    allTabs[i].style.display = 'none';
  }
  var currentTab = document.getElementById(tabId);
  currentTab.style.display = 'block';
}

/** Makes request to server and renders page with received data. */
function main() {
  var timerId = setInterval(function() {
    d3.json(JSON_URI, function(data) {
      if (Object.keys(data).length !== 0) {
        renderPage(data);
        clearInterval(timerId);
      }
    });
  }, POLL_INTERVAL);
}

main();
