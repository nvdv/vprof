/**
 * Main module
 */
var d3 = require('d3');

var JSON_URI = "profile";

// Treemap parameters
var WIDTH = 900;
var HEIGHT_SCALE = 0.95;
var PAD_TOP = 20;
var PAD_RIGHT = 3;
var PAD_BOTTOM = 3;
var PAD_LEFT = 3;
var TEXT_OFFSET_X = 5;
var TEXT_OFFSET_Y= 14;
var ROUND_RADIUS_X = 7;
var ROUND_RADIUS_Y = 7;

/** Calculates node rendering params. */
function calculateNode(d, n) {
  // Adjusting treemap layout.
  if (!d.parent) {
    d.start_y = d.y;
    d.height = d.dy;
  }
  // TODO(nvdv)
  // In some cases total cummulative run time of children can
  // be greater than cummulative run time of parent which
  // affects rendering.
  if (!d.children) return;
  var curr_y = d.start_y + PAD_TOP;
  var usable_height = d.height - (PAD_BOTTOM + PAD_TOP);
  for (var i = 0; i < d.children.length; i++) {
    d.children[i].start_y = curr_y;
    var c = d.children[i].cum_time / d.cum_time;
    d.children[i].height = usable_height * Math.round(c * 1000) / 1000;
    curr_y += d.children[i].height;
  }
}

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

/** Renders treemap. */
function renderTreeMap(data) {
  var color = d3.scale.category10();

  var canvas = d3.select("body")
    .append("svg")
    .attr("width", WIDTH)
    .attr("height", HEIGHT_SCALE * window.innerHeight);

  var treemap = d3.layout.treemap()
    .size([WIDTH, HEIGHT_SCALE * window.innerHeight])
    .mode('dice')
    .value(function(d) { return d.cum_time; })
    .padding([PAD_TOP, PAD_RIGHT, PAD_BOTTOM, PAD_LEFT])
    .nodes(data.call_stats);

  var cells = canvas.selectAll(".cell")
    .data(treemap)
    .enter()
    .append("g")
    .attr("class", "cell")
    .each(calculateNode);

  cells.append("rect")
    .attr("x", function(d) { return d.x; })
    .attr("y", function(d) { return d.start_y; })
    .attr('rx', ROUND_RADIUS_X)
    .attr('ry', ROUND_RADIUS_Y)
    .attr("width", function(d) { return d.dx; })
    .attr("height", function(d) { return d.height; })
    .attr("fill", function(d) { return color(getNodeName(d) + d.depth.toString()); });

  cells.append("text")
    .attr("x", function(d) { return d.x + TEXT_OFFSET_X; })
    .attr("y", function(d) { return d.start_y + TEXT_OFFSET_Y; })
    .style("font-size","13px")
    .text(function(d) { return getNodeName(d); });
}

/** Renders profile stats. */
function renderTable(data) {
  var columns = [
    {
      head: 'Name',
      cl: 'title',
      text: function(row) { return getNodeName(row); }},
    {
      head: 'Time %',
      cl: 'num',
      text: function(row) {
        var percent = row.cum_time / data.run_time;
        return Math.round(percent * 1000) / 1000;
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
      head: 'Num. calls',
      cl: 'num',
      text: function(row) { return row.num_calls; }
    }, {
      head: 'Cum. calls',
      cl: 'num',
      text: function(row) { return row.cum_calls; }},
  ];

  var prof_stats = d3.select("body")
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

/** Renders whole page. */
function renderView() {
  d3.json(JSON_URI, function(data) {
    renderTreeMap(data);
    renderTable(data);
  });
}

renderView();