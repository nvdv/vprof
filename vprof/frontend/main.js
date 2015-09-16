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
var WIDTH_SCALE = 0.95;
var WIDTH = window.innerWidth * WIDTH_SCALE;
var ZOOM_DURATION = 250;
var TOOLTIP_X = 0;
var TOOLTIP_HEIGHT = 100;
var TOOLTIP_Y = 0;
var TOOLTIP_DY = 15;
var TEXT_OFFSET_X = 5;
var TEXT_OFFSET_Y= 14;
var TEXT_CUTOFF = 0.075 * WIDTH;
var LEGEND_X = WIDTH - 400;
var LEGEND_Y = 100;
var LEGEND_HEIGHT = 68;
var LEGEND_WIDTH = 300;
var LEGEND_TEXT_OFFSET = 10;
var LEGEND_RADIUS_X = 10;
var LEGEND_RADIUS_Y = 10;

/** Returns full node name. */
function getNodeName(d) {
  var tokens = d.module_name.split('/');
  var filename = tokens[tokens.length - 1];
  return filename + ':' + d.lineno + '(' + d.func_name + ')';
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
  var chart =  d3.select('body')
    .append('div')
    .attr('class', 'chart');

  var canvas = chart.append('svg')
    .attr('width', WIDTH)
    .attr('height', HEIGHT - TOOLTIP_HEIGHT);

  var tooltip_area = chart.append('svg')
    .attr('width', WIDTH)
    .attr('height', TOOLTIP_HEIGHT);

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

  // Render flame chart nodes.
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
      return (nodeWidth > TEXT_CUTOFF) ? getNodeName(d) : '';
    });

  // Render legend.
  var legend = canvas.append('g')
    .attr('class', 'legend')
    .attr('x', LEGEND_X)
    .attr('y', LEGEND_Y)
    .attr('height', LEGEND_HEIGHT)
    .attr('width', LEGEND_WIDTH);

  legend.append('rect')
    .attr('class', 'tooltip-rect')
    .attr('x', LEGEND_X)
    .attr('y', LEGEND_Y)
    .attr('height', LEGEND_HEIGHT)
    .attr('width', LEGEND_WIDTH)
    .attr('rx', LEGEND_RADIUS_X)
    .attr('ry', LEGEND_RADIUS_Y);

  var legend_text = legend.append('text')
    .attr("x", LEGEND_X + LEGEND_TEXT_OFFSET)
    .attr("y", LEGEND_Y);
  legend_text.append('tspan')
    .attr('x', LEGEND_X + LEGEND_TEXT_OFFSET)
    .attr('dy', TOOLTIP_DY)
    .text('Program name: ' + data.program_name);
  legend_text.append('tspan')
    .attr('x', LEGEND_X + LEGEND_TEXT_OFFSET)
    .attr('dy', TOOLTIP_DY)
    .text('Total runtime: ' + data.run_time + 's');
  legend_text.append('tspan')
    .attr('x', LEGEND_X + LEGEND_TEXT_OFFSET)
    .attr('dy', TOOLTIP_DY)
    .text('Total calls: ' + data.total_calls);
  legend_text.append('tspan')
    .attr('x', LEGEND_X + LEGEND_TEXT_OFFSET)
    .attr('dy', TOOLTIP_DY)
    .text('Primitive calls: ' + data.primitive_calls);

  // Zoom in.
  nodes.on('click', function(d) {
    x_scale.domain([d.x, d.x + d.dx]);
    y_scale.domain([0, 1 - d.y]).range([0, HEIGHT - TOOLTIP_HEIGHT]);

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
        var nodeWidth = x_scale(d.x + d.dx) - x_scale(d.x);
        return (nodeWidth > TEXT_CUTOFF) ? getNodeName(d) : '';
      });
  });

  // Zoom out.
  canvas.on('dblclick', function(d) {
    x_scale.domain([0, 1]);
    y_scale.domain([0, 1]);
    nodes.transition()
      .duration(ZOOM_DURATION)
    .attr('x', function(d) { return x_scale(d.x); })
    .attr('y', function(d) { return y_scale(1 - d.y - d.dy); })
    .attr('width', function(d) { return x_scale(d.dx); })
    .attr('height', function(d) { return y_scale(d.dy); });

    titles.transition()
      .duration(ZOOM_DURATION)
      .attr('x', function(d) { return x_scale(d.x) + TEXT_OFFSET_X; })
      .attr('y', function(d) { return y_scale(1 - d.y - d.dy) + TEXT_OFFSET_Y; })
      .text(function(d) {
        var nodeWidth = x_scale(d.x + d.dx) - x_scale(d.x);
        return (nodeWidth > TEXT_CUTOFF) ? d.func_name : '';
      });
  });
}

/** Renders whole page. */
function renderView() {
  d3.json(JSON_URI, function(data) {
    renderFlameChart(data);
  });
}

module.exports = {
  'getNodeName': getNodeName,
};

renderView();