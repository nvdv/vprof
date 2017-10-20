/**
 * @file Flame graph UI module.
 */

'use strict';
const color = require('./color');
const common = require('./common');
const d3 = require('d3');

/**
 * Represents flame graph.
 * @constructor
 * @param {Object} parent - Parent element for flame graph.
 * @param {Object} data - Data for flame graph rendering.
 */
class FlameGraph {
  constructor(parent, data) {
    this.PAD_SIZE = 10;
    this.HEIGHT = parent.node().scrollHeight - this.PAD_SIZE;
    this.WIDTH = parent.node().scrollWidth - this.PAD_SIZE;
    this.TEXT_OFFSET_X = 5;
    this.TEXT_OFFSET_Y= 14;
    this.TEXT_CUTOFF = 0.075 * this.WIDTH;
    this.LEGEND_X = this.WIDTH - 500;
    this.LEGEND_Y = 100;
    this.MIN_TEXT_HEIGHT = 18;
    this.HELP_MESSAGE = (
      '<p>&#8226 Hover over node to see node call stats</p>' +
      '<p>&#8226 Click on node to zoom</p>'+
      '<p>&#8226 Double click to restore original scale</p>');
    this.NO_DATA_MESSAGE = (
      'Sorry, no samples. Seems like run time is less than sampling interval.');
    this.data_ = data;
    this.parent_ = parent;
    this.xScale_ = d3.scaleLinear().domain([0, 1]).range([0, this.WIDTH]);
    this.yScale_ = d3.scaleLinear().domain([0, 1]).range([0, this.HEIGHT]);
    this.flameGraph_ = d3.partition();
    this.color_ = color.createColorScale();
  }

  /** Renders flame graph. */
  render() {
    let canvas = this.parent_.append('svg')
      .attr('width', this.WIDTH)
      .attr('height', this.HEIGHT)
      .attr('transform', 'rotate(180)');

    let tooltip = this.parent_.append('div')
      .attr('class', 'content-tooltip content-tooltip-invisible');

    this.renderLegend_();
    this.renderHelp_();

    // Display message and stop if callStats is empty.
    if (Object.keys(this.data_.callStats).length === 0) {
      this.renderNoDataMessage_();
      return;
    }

    let nodes = d3.hierarchy(this.data_.callStats)
      .each((d) => d.value = d.data.sampleCount);

    this.flameGraph_(nodes);

    let cells = canvas.selectAll('.flame-graph-cell')
      .data(nodes.descendants())
      .enter()
      .append('g')
      .attr('class', 'flame-graph-cell');

    // Render flame graph nodes.
    nodes = cells.append('rect')
      .attr('class', 'flame-graph-rect-normal')
      .attr('x', (d) => this.xScale_(d.x0))
      .attr('y', (d) => this.yScale_(d.y0))
      .attr('width', (d) => this.xScale_(d.x1 - d.x0))
      .attr('height', (d) => this.yScale_(d.y1 - d.y0))
      .style('fill', (d) => this.color_(d.data.colorHash))
      .on('mouseover', (d, i, n) => this.showTooltip_(n[i], tooltip, d.data))
      .on('mouseout', (d, i, n) => this.hideTooltip_(n[i], tooltip));

    let titles = cells.append('text')
      .attr('x', (d) => this.xScale_(d.x0) + this.TEXT_OFFSET_X)
      .attr('y', (d) => this.yScale_(d.y0) + this.TEXT_OFFSET_Y)
      .attr('transform', (d) => {
        // Reverse text back.
        let rx = this.xScale_(d.x0) + (
          this.xScale_(d.x1) - this.xScale_(d.x0)) / 2;
        let ry = this.yScale_(d.y0) + (
          this.yScale_(d.y1) - this.yScale_(d.y0)) / 2;
        return 'rotate(180, ' + rx + ', ' + ry + ')';
      })
      .text((d, i, n) => {
        let nodeWidth = n[i].previousElementSibling.getAttribute('width');
        return FlameGraph.getTruncatedNodeName_(d.data, nodeWidth); })
      .attr('visibility', (d, i, n) => {
        let nodeHeight = n[i].previousElementSibling.getAttribute('height');
        return nodeHeight > this.MIN_TEXT_HEIGHT ? 'visible': 'hidden';
      });

    nodes.on('click', (d) => this.zoomIn_(d, nodes, titles));
    canvas.on('dblclick', (d) => this.zoomOut_(nodes, titles));
  }

  /**
   * Handles zoom in.
   * @param {Object} node - Focus node.
   * @param {Object} allNodes - All flame graph nodes.
   * @param {Object} titles - All flame graph node titles.
   */
  zoomIn_(node, allNodes, titles) {
    let leaf = FlameGraph.getLeafWithMaxY0_(node);
    this.xScale_.domain([node.x0, node.x1]);
    this.yScale_.domain([node.y0, leaf.y0 + (leaf.y1 - leaf.y0)]);
    allNodes.attr('x', (d) => this.xScale_(d.x0))
      .attr('y', (d) => this.yScale_(d.y0))
      .attr('width', (d) => this.xScale_(d.x1) - this.xScale_(d.x0))
      .attr('height', (d) => this.yScale_(d.y1) - this.yScale_(d.y0));
    this.redrawTitles_(titles);
  }

  /**
   * Returns leaf node that has max y0 value.
   * Used to determine zoom region.
   * @param {Object} node - Focus node.
   * @returns {Object}
   */
  static getLeafWithMaxY0_(node) {
    let leaves = [];
    let getLeaves = (node) => {
      if (!node.hasOwnProperty('children')) {
        leaves.push(node);
      } else {
        for (let i = 0; i < node.children.length; i++) {
          getLeaves(node.children[i]);
        }
      }
    };
    getLeaves(node);

    let leafWithMaxY0 = leaves[0];
    for (let i = 0; i < leaves.length; i++) {
      if (leaves[i].y0 > leafWithMaxY0.y0) {
        leafWithMaxY0 = leaves[i];
      }
    }
    return leafWithMaxY0;
  }

  /**
   * Handles zoom out.
   * @param {Object} allNodes - All flame graph nodes.
   * @param {Object} titles - All flame graph node titles.
   */
  zoomOut_(allNodes, titles) {
    this.xScale_.domain([0, 1]);
    this.yScale_.domain([0, 1]);
    allNodes.attr('x', (d) => this.xScale_(d.x0))
      .attr('y', (d) => this.yScale_(d.y0))
      .attr('width', (d) => this.xScale_(d.x1 - d.x0))
      .attr('height', (d) => this.yScale_(d.y1 - d.y0));
    this.redrawTitles_(titles);
  }

  /**
   * Redraws node titles based on current xScale and yScale states.
   * @param {Object} titles - All flame graph node titles.
   */
  redrawTitles_(titles) {
    titles.attr('x', (d) => this.xScale_(d.x0) + this.TEXT_OFFSET_X)
      .attr('y', (d) => this.yScale_(d.y0) + this.TEXT_OFFSET_Y)
      .attr('transform', (d) => {
        // Reverse text back.
        let rx = this.xScale_(d.x0) + (
          this.xScale_(d.x1) - this.xScale_(d.x0)) / 2;
        let ry = this.yScale_(d.y0) + (
          this.yScale_(d.y1) - this.yScale_(d.y0)) / 2;
        return 'rotate(180, ' + rx + ', ' + ry + ')';
      })
      .text((d) => {
        let nodeWidth = this.xScale_(d.x1) - this.xScale_(d.x0);
        return FlameGraph.getTruncatedNodeName_(d.data, nodeWidth);
        return d.data;
      })
      .attr('visibility', (d, i, n) => {
        let nodeHeight = n[i].previousElementSibling.getAttribute('height');
        return (nodeHeight > this.MIN_TEXT_HEIGHT) ? 'visible': 'hidden';
      });
  }

  /**
   * Shows tooltip and highlights flame graph node.
   * @param {Object} element - Flame graph node.
   * @param {Object} tooltip - Tooltip element.
   * @param {Object} node - Function call info.
   */
  showTooltip_(element, tooltip, node) {
    d3.select(element).attr('class', 'flame-graph-rect-highlight');
    let funcName = node.stack[0].replace(/</g, "&lt;").replace(/>/g, "&gt;");
    tooltip.attr('class', 'content-tooltip content-tooltip-visible')
      .html('<p><b>Function name:</b> ' + funcName + '</p>' +
            '<p><b>Line number:</b> ' + node.stack[2] +'</p>' +
            '<p><b>Filename:</b> ' + node.stack[1] +'</p>' +
            '<p><b>Sample count:</b> ' + node.sampleCount + '</p>' +
            '<p><b>Percentage:</b> ' + node.samplePercentage +'%</p>')
      .style('left', d3.event.pageX)
      .style('top', d3.event.pageY);
  }

  /**
   * Hides tooltip.
   * @param {Object} element - Highlighted flame graph node.
   * @param {Object} tooltip - Tooltip element.
   */
  hideTooltip_(element, tooltip) {
    d3.select(element).attr('class', 'flame-graph-rect-normal');
    tooltip.attr('class', 'content-tooltip content-tooltip-invisible');
  };

  /** Renders flame graph legend. */
  renderLegend_() {
    this.parent_.append('div')
      .attr('class', 'content-legend')
      .html('<p><b>Object name:</b> ' + this.data_.objectName + '</p>' +
            '<p><b>Run time:</b> ' + this.data_.runTime + ' s</p>' +
            '<p><b>Total samples:</b> ' + this.data_.totalSamples + '</p>' +
            '<p><b>Sample interval:</b> ' + this.data_.sampleInterval +
            ' s</p>')
      .style('left', this.LEGEND_X)
      .style('top', this.LEGEND_Y);
  }

  /** Renders flame graph help. */
  renderHelp_() {
    this.parent_.append('div')
      .attr('class', 'tabhelp inactive-tabhelp')
      .html(this.HELP_MESSAGE);
  }

  /** Renders message when callStats is empty. */
  renderNoDataMessage_() {
    this.parent_.append('div')
      .attr('class', 'flame-graph-no-data-message')
      .html(this.NO_DATA_MESSAGE);
  }

  /**
   * Returns function info.
   * @static
   * @param {Object} d - Object representing function call info.
   * @returns {string}
   */
  static getNodeName_(d) {
    return d.stack[0] + ':' + d.stack[2] + ' (' + d.stack[1] + ')';
  }

  /**
   * Truncates function name depending on flame graph node length.
   * @static
   * @param {Object} d - Function info.
   * @param {number} rectLength - Length of flame graph node.
   * @returns {string}
   */
  static getTruncatedNodeName_(d, rectLength) {
    let fullname = FlameGraph.getNodeName_(d);
    let maxSymbols = rectLength / 10;  // ~ 10 pixels per character.
    return maxSymbols <= 3 ? '' : common.shortenString(
      fullname, maxSymbols, false);
  }
}

/**
 * Renders flame graph and attaches it to the parent.
 * @param {Object} parent - Flame graph parent element.
 * @param {Object} data - Data for flame graph rendering.
 */
function renderFlameGraph(data, parent) {
  let flameGraph = new FlameGraph(parent, data);
  flameGraph.render();
}

module.exports = {
  'FlameGraph': FlameGraph,
  'renderFlameGraph': renderFlameGraph,
};
