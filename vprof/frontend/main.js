/**
 * @file Page rendering module.
 */

'use strict';
const d3request = require('d3-request');
const d3select = require('d3-selection');
const codeHeatmapModule = require('./code_heatmap.js');
const flameGraphModule = require('./flame_graph.js');
const memoryStatsModule = require('./memory_stats.js');
const profilerModule = require('./profiler.js');

const JSON_URI = 'profile';
const POLL_INTERVAL = 200;  // msec

/**
 * Creates empty div with specified ID.
 * @param {string} id - div ID.
 */
function createTabContent_(id) {
  return d3select.select('body')
    .append('div')
    .attr('class', 'main-tab-content')
    .attr('id', id);
}

/**
 *  Creates flame graph tab header with specified status and
 *  appends it to the parent node.
 *  @param {Object} parent - Parent element to append tab to.
 *  @param {status} status - Specified tab status.
 */
function createFlameGraphTab_(parent, status) {
  parent.append('li')
    .attr('class', status)
    .text('Flame graph')
    .on('click', function(d) {
      d3select.selectAll('li')
        .attr('class', 'main-tab-not-selected');
      d3select.select(this)
        .attr('class', 'main-tab-selected');
      showTab_('flame-graph-tab');
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
      d3select.selectAll('li')
        .attr('class', 'main-tab-not-selected');
      d3select.select(this)
        .attr('class', 'main-tab-selected');
      showTab_('memory-chart-tab');
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
      d3select.selectAll('li')
        .attr('class', 'main-tab-not-selected');
      d3select.select(this)
        .attr('class', 'main-tab-selected');
      showTab_('code-heatmap-tab');
    });
}

/**
 *  Creates profiler tab header with specified status and
 *  appends it to the parent node.
 *  @param {Object} parent - Parent element to append tab to.
 *  @param {status} status - Specified tab status.
 */
function createProfilerTab_(parent, status) {
  parent.append('li')
    .attr('class', status)
    .text('Profiler')
    .on('click', function(d) {
      d3select.selectAll('li')
        .attr('class', 'main-tab-not-selected');
      d3select.select(this)
        .attr('class', 'main-tab-selected');
      showTab_('profiler-tab');
    });
}

/**
 * Renders stats page.
 * @param {Object} data - Data for page rendering.
 */
function renderPage(data) {
  // Remove all existing tabs and their content
  // in case if user is refreshing main page.
  d3select.select('body').selectAll('*').remove();

  let tabHeader = d3select.select('body')
    .append('ul')
    .attr('class', 'main-tab-header');

  let props = Object.keys(data);
  props.sort();
  for (let i = 0; i < props.length; i++) {
    let status = (i === 0) ? 'main-tab-selected' : 'main-tab-not-selected';
    let displayClass = (i === 0) ? 'active-tab' : 'inactive-tab';
    switch (props[i]) {
    case 'c':
      createFlameGraphTab_(tabHeader, status);
      let flameGraph = createTabContent_('flame-graph-tab');
      flameGraphModule.renderFlameGraph(data.c, flameGraph);
      flameGraph.classed(displayClass, true);
      break;
    case 'm':
      createMemoryChartTab_(tabHeader, status);
      let memoryChart = createTabContent_('memory-chart-tab');
      memoryStatsModule.renderMemoryStats(data.m, memoryChart);
      memoryChart.classed(displayClass, true);
      break;
    case 'h':
      createCodeHeatmapTab_(tabHeader, status);
      let codeHeatmap = createTabContent_('code-heatmap-tab');
      codeHeatmapModule.renderCodeHeatmap(data.h, codeHeatmap);
      codeHeatmap.classed(displayClass, true);
      break;
    case 'p':
      createProfilerTab_(tabHeader, status);
      let profilerOutput = createTabContent_('profiler-tab');
      profilerModule.renderProfilerOutput(data.p, profilerOutput);
      profilerOutput.classed(displayClass, true);
      break;
    }
  }

  let helpButton = tabHeader.append('div')
    .attr('class', 'help-button')
    .text('?');

  document.addEventListener('click', function(event) {
    handleHelpDisplay(event, helpButton);
  });
}

/**
  * Handles tab help display..
  * @param {Object} event - Mouse click event.
  */
function handleHelpDisplay(event, helpButton) {
  if (event.target === helpButton.node()) {
    let helpActiveTab = d3select.select('.active-tab .tabhelp');
    helpActiveTab.classed(
      'active-tabhelp', !helpActiveTab.classed('active-tabhelp'))
      .classed('inactive-tabhelp', !helpActiveTab.classed('inactive-tabhelp'));
  }
}

/**
  * Makes tab specified by tabId active.
  * @param {string} tabId - Next active tab identifier.
  */
function showTab_(tabId) {
  d3select.selectAll('.main-tab-content')
    .classed('active-tab', false)
    .classed('inactive-tab', true);
  d3select.select('#' + tabId)
    .classed('active-tab', true)
    .classed('inactive-tab', false);
}

/** Makes request to server and renders page with received data. */
function main() {
  let progressIndicator = d3select.select('body')
    .append('div')
    .attr('id', 'main-progress-indicator');

  // TODO (nvdv): Simplify this code.
  d3request.json(JSON_URI, function(data) {
    if (Object.keys(data).length !== 0) {
      progressIndicator.remove();
      renderPage(data);
    } else {
      let timerId = setInterval(function() {
        d3request.json(JSON_URI, function(data) {
          if (Object.keys(data).length !== 0) {
            progressIndicator.remove();
            clearInterval(timerId);
            renderPage(data);
          }
        });
      }, POLL_INTERVAL);
    }
  });
}

main();
