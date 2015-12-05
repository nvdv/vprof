var memory_stats = require('./memory_stats.js');

describe('Memory stats test suite', function() {

  it('Check processGCStats_', function() {
    var stats = [
        {'objInGenerations': '1,10,100',
         'timeElapsed': '0.1s',
         'uncollectable': '6',
         'unreachable': '5'},
        {'objInGenerations': '1,10,100',
         'timeElapsed': '0.2s',
         'uncollectable': '0',
         'unreachable': '0'},];
    var expectedResult = (
        '<p>GC runs: 2</p><p>Run:1</p>' +
        '<p>Objects in generations: 1,10,100</p>' +
        '<p>Time elapsed: 0.1s</p>' +
        '<p>Uncollectable: 6</p>'+
        '<p>Unreachable: 5</p>' +
        '<p>Run:2</p>' +
        '<p>Objects in generations: 1,10,100</p>' +
        '<p>Time elapsed: 0.2s</p>' +
        '<p>Uncollectable: 0</p>' +
        '<p>Unreachable: 0</p>');
    expect(memory_stats.processGCStats_(stats)).toBe(expectedResult);
  });
});
