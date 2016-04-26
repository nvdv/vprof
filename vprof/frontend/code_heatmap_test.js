var code_heatmap = require('./code_heatmap.js');

describe('Code heatmap test suite', function() {
  it('Check changeBackgroundColor_', function() {
    var heatmap = new code_heatmap.CodeHeatmap();
    var data = {
      'heatmap': {1: 2, 2: 7, 3: 5},
      'srcCode': [[1, 'def foo():'], [2, 'x = 2'], [3, 'return x']]
     };

    expect(heatmap.changeBackgroundColor_(data, 0)).not.toBe('');
    expect(heatmap.changeBackgroundColor_(data, 1)).not.toBe('');
    expect(heatmap.changeBackgroundColor_(data, 2)).not.toBe('');
  });
});
