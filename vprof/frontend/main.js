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
var HEIGHT_OFFSET = 100;
var WIDTH = window.innerWidth / 2;
var ZOOM_DURATION = 250;
var TOOLTIP_X = 0;
var TOOLTIP_HEIGHT = 100;
var TOOLTIP_Y = HEIGHT - TOOLTIP_HEIGHT + 10;
var TOOLTIP_DY = 15;
var TEXT_OFFSET_X = 5;
var TEXT_OFFSET_Y= 14;
var TEXT_CUTOFF = 0.075 * WIDTH;

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
    .append('div')
    .attr('class', 'profile-stats');

  var summary = prof_stats.append('summary');
  summary.append('p')
    .attr('class', 'summary-name')
    .text('Program name: ')
    .append('span')
    .attr('class', 'summary-value')
    .text(data.program_name);
  summary.append('p')
    .attr('class', 'summary-name')
    .text('Total runtime: ')
    .append('span')
    .attr('class', 'summary-value')
    .text(data.run_time + ' s');
  summary.append('p')
    .attr('class', 'summary-name')
    .text('Total calls: ')
    .append('span')
    .attr('class', 'summary-value')
    .text(data.total_calls);
  summary.append('p')
    .attr('class', 'summary-name')
    .text('Primitive calls: ')
    .append('span')
    .attr('class', 'summary-value')
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

/** Renders profile flame chart tooltip. */
function renderFlameChartTooltip(tooltip_area, d, total_time) {
  var tooltip_text = tooltip_area.append('text');
  tooltip_text.append('tspan')
    .attr('x', TOOLTIP_X)
    .attr('y', TOOLTIP_Y)
    .attr('dy', TOOLTIP_DY)
    .text('Function name: ' + d.func_name);
  tooltip_text.append('tspan')
    .attr('x', TOOLTIP_X)
    .attr('dy', TOOLTIP_DY)
    .text('Location: ' + d.module_name);
  tooltip_text.append('tspan')
    .attr('x', TOOLTIP_X)
    .attr('dy', TOOLTIP_DY)
    .text(function() {
      var percent = 100 * Math.round(d.cum_time / total_time * 1000) / 1000;
      return 'Time percent: ' + percent + ' %';
   }());
  tooltip_text.append('tspan')
    .attr('x', TOOLTIP_X)
    .attr('dy', TOOLTIP_DY)
    .text('Cum.time: ' + d.cum_time + ' s');
  tooltip_text.append('tspan')
    .attr('x', TOOLTIP_X)
    .attr('dy', TOOLTIP_DY)
    .text('Time per call: ' + d.time_per_call + ' s');
  tooltip_text.append('tspan')
    .attr('x', TOOLTIP_X)
    .attr('dy', TOOLTIP_DY)
    .text('Primitive calls: ' + d.prim_calls);
}

/** Removes profile flame chart from tooltip area. */
function removeFlameChartTooltip(tooltip_area) {
  tooltip_area.selectAll('text').remove();
}

/** Renders profile flame chart. */
function renderFlameChart(data) {
  var color = d3.scale.category10();
  var canvas = d3.select('body')
    .append('div')
    .attr('class', 'chart')
    .append('svg')
    .attr('width', WIDTH)
    .attr('height', HEIGHT);

  var tooltip_area = canvas.append('g');
  tooltip_area.append('rect')
    .attr('x', TOOLTIP_X)
    .attr('y', TOOLTIP_Y)
    .attr('width', WIDTH)
    .attr('height', TOOLTIP_HEIGHT)
    .attr('fill', 'white');

  var flame_chart = d3.layout.partition()
    .sort(null)
    .value(function(d) { return d.cum_time; });

  var cells = canvas.selectAll(".cell")
    .data(flame_chart.nodes(data.call_stats))
    .enter()
    .append('g')
    .attr('class', 'cell');

  var x_scale = d3.scale.linear().range([0, WIDTH]);
  var y_scale = d3.scale.linear().range([0, HEIGHT - TOOLTIP_HEIGHT]);
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
      renderFlameChartTooltip(tooltip_area, d, data.run_time);
    })
    .on('mouseout', function(d) {
      d3.select(this)
        .attr('class', 'rect-normal');
      removeFlameChartTooltip(tooltip_area);
    });

  // Render flame chart headers.
  var titles = cells.append('text')
    .attr('x', function(d) { return x_scale(d.x) + TEXT_OFFSET_X; })
    .attr('y', function(d) { return y_scale(1 - d.y - d.dy) + TEXT_OFFSET_Y; })
    .text(function(d) {
      var nodeWidth = this.previousElementSibling.getAttribute('width');
      return (nodeWidth > TEXT_CUTOFF) ? d.func_name : '';
    });

  // Zoom in
  nodes.on('click', function(d) {
    x_scale.domain([d.x, d.x + d.dx]);
    y_scale.domain([0, 1 - d.y]).range([0, d.y ? HEIGHT - HEIGHT_OFFSET : HEIGHT]);
    nodes.transition()
      .duration(ZOOM_DURATION)
      .attr('x', function(d) { return x_scale(d.x); })
      .attr('y', function(d) { return y_scale(1 - d.y - d.dy); })
      .attr('width', function(d) { return x_scale(d.x + d.dx) - x_scale(d.x); })
      .attr('height', function(d) { return y_scale(1 - d.y) - y_scale(1 - d.y - d.dy); });

    titles.transition()
      .duration(ZOOM_DURATION)
      .attr('x', function(d) { return x_scale(d.x) + TEXT_OFFSET_X; })
      .attr('y', function(d) { return y_scale(1 - d.y - d.dy) + TEXT_OFFSET_Y; })
      .text(function(d) {
        var nodeWidth = this.previousElementSibling.getAttribute('width');
        return (nodeWidth > TEXT_CUTOFF) ? d.func_name : '';
      });
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