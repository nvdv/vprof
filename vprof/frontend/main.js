/**
 * Renders all profiles.
 */

/* jshint strict: false, browser: true, globalstrict: true */
/* global require, module */

'use strict';
var d3 = require('d3');
var memory_stats = require('./memory_stats.js');
var profile = require('./profile.js');

var JSON_URI = 'profile';

/** Creates profile chart tab header with specified status and
 *  appends it to the parent node.
 */
function createProfileChartTab_(parent, status) {
  parent.append('li')
    .attr('class', status)
    .text('Time profile')
    .on('click', function(d) {
      d3.selectAll('li')
        .attr('class', 'not-selected');
      d3.select(this)
        .attr('class', 'selected');
      showTab_('profile-chart');
    });
}

/** Creates profile chart tab header with specified status and
 *  appends it to the parent node.
 */
function createMemoryChartTab_(parent, status) {
  parent.append('li')
    .attr('class', status)
    .text('Memory usage')
    .on('click', function(d) {
      d3.selectAll('li')
        .attr('class', 'not-selected');
      d3.select(this)
        .attr('class', 'selected');
      showTab_('memory-chart');
    });
}

/** Renders whole page. */
function renderPage(data) {
  var tabHeader = d3.select('body')
    .append('ul')
    .attr('class', 'tab-header');

  var profileChart = d3.select('body')
    .append('div')
    .attr('class', 'profile-chart tab-content')
    .attr('id', 'profile-chart');

  var memoryChart = d3.select('body')
    .append('div')
    .attr('class', 'memory-chart tab-content')
    .attr('id', 'memory-chart');

  var props = Object.keys(data);
  for (var i = 0; i < props.length; i++) {
    var status = (i === 0) ? 'selected' : 'not-selected';
    if (props[i] == 'c') {
      createProfileChartTab_(tabHeader, status);
      profile.renderProfile(data.c, profileChart);
    } else if (props[i] == 'm') {
      createMemoryChartTab_(tabHeader, status);
      memory_stats.renderMemoryStats(data.m, memoryChart);
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