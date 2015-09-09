/**
 * Renders front page from provided profiles.
 */

 /* jshint strict: false, browser: true, globalstrict: true */
 /* global require, module */

'use strict';
var d3 = require('d3');

var JSON_URI = 'profile';

// Flame chart parameters
var HEIGHT_SCALE = 0.95;
var HEIGHT = window.innerHeight * HEIGHT_SCALE;
var WIDTH = window.innerWidth / 2;

/** Returns full node name. */
function getNodeName(d) {
  return d.module_name + '.' + d.func_name + '@' + d.lineno.toString();
}

/** Flattens stats object. */
function flattenStats(stats) {

  function processNode(node) {
    var curr_node = {};
    for (var stat in node) {
      if (node.hasOwnProperty(stat) && stat != 'children') {
        curr_node[stat] = node[stat];
      }
    }
    results.push(curr_node);
    if (!node.hasOwnProperty('children')) {
      return;
    }
    node.children.forEach(function(child) { processNode(child); });
  }

  var results = [];
  processNode(stats);
  return results;
}

/** Renders profile stats. */
function renderTable(data) {
  var columns = [
    {
      head: 'Function name',
      cl: 'title',
      text: function(row) { return row.func_name; }
    }, {
      head: 'Location',
      cl: 'title',
      text: function(row) { return row.module_name + ' @ ' + row.lineno.toString(); }
    }, {
      head: 'Time %',
      cl: 'num',
      text: function(row) {
        var percent = row.cum_time / data.run_time;
        return 100 * Math.round(percent * 1000) / 1000;
      }
    }, {
      head: 'Cum. time',
      cl: 'num',
      text: function(row) { return row.cum_time; }
    }, {
      head: 'Time per call',
      cl: 'num',
      text: function(row) { return row.time_per_call; }
    }, {
      head: 'Total calls',
      cl: 'num',
      text: function(row) { return row.total_calls; }
    }, {
      head: 'Primitive calls',
      cl: 'num',
      text: function(row) { return row.prim_calls; }},
  ];

  var prof_stats = d3.select('body')
    .append('profile_stats');

  var summary = prof_stats.append('summary');
  summary.append('p')
    .attr('class', 'summary_name')
    .text('Program name: ')
    .append('span')
    .attr('class', 'summary_value')
    .text(data.program_name);
  summary.append('p')
    .attr('class', 'summary_name')
    .text('Total runtime: ')
    .append('span')
    .attr('class', 'summary_value')
    .text(data.run_time + ' s');
  summary.append('p')
    .attr('class', 'summary_name')
    .text('Total calls: ')
    .append('span')
    .attr('class', 'summary_value')
    .text(data.total_calls);
  summary.append('p')
    .attr('class', 'summary_name')
    .text('Primitive calls: ')
    .append('span')
    .attr('class', 'summary_value')
    .text(data.primitive_calls);

  var table = prof_stats.append('table');

  table.append('thead')
   .append('tr')
   .selectAll('th')
   .data(columns)
   .enter()
   .append('th')
   .attr('class', function(col) { return col.cl; })
   .text(function(col) { return col.head; });

  var stats = flattenStats(data.call_stats);

  table.append('tbody')
   .selectAll('tr')
   .data(stats)
   .enter()
   .append('tr')
   .selectAll('td')
   .data(function(row, i) {
      return columns.map(function(c) {
        var cell = {};
        d3.keys(c).forEach(function(k) {
            cell[k] = typeof c[k] == 'function' ? c[k](row,i) : c[k];
        });
        return cell;
      });
   })
   .enter()
   .append('td')
   .text(function(d) { return d.text; })
   .attr('class', function(d) { return d.cl; });
}

function renderFlameChart(data) {
  var color = d3.scale.category10();
  var canvas = d3.select('body')
    .append('div')
    .attr('class', 'chart')
    .append('svg')
    .attr('width', WIDTH)
    .attr('height', HEIGHT);
  var x_scale = d3.scale.linear().range([0, WIDTH]);
  var y_scale = d3.scale.linear().range([0, HEIGHT]);

  var flame_chart = d3.layout.partition()
    .sort(null)
    .value(function(d) { return d.cum_time; });

  var call_graph = flame_chart.nodes(data.call_stats);
  var cells = canvas.selectAll(".cell")
    .data(call_graph)
    .enter()
    .append('g')
    .attr('class', 'cell');

  var nodes = cells.append('rect')
    .attr('class', 'rect-normal')
    .attr('x', function(d) { return x_scale(d.x); })
    .attr('y', function(d) { return y_scale(1 - d.y - d.dy); })
    .attr('width', function(d) { return x_scale(d.dx); })
    .attr('height', function(d) { return y_scale(d.dy); })
    .style('fill', function(d) { return color(getNodeName(d) + d.depth.toString()); })
    .on('mouseover', function(d) {
      d3.select(this)
        .attr('class', 'rect-highlight');
    })
    .on('mouseout', function(d) {
      d3.select(this)
        .attr('class', 'rect-normal');
    });
}

/** Renders whole page. */
function renderView() {
  d3.json(JSON_URI, function(data) {
    renderFlameChart(data);
    renderTable(data);
  });
}

module.exports = {
  'getNodeName': getNodeName,
  'flattenStats': flattenStats
};

renderView();