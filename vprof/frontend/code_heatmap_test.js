var code_heatmap = require('./code_heatmap.js');

describe('Code heatmap test suite', function() {

  it('Check getNodeName', function() {
    var srcCode = "def foo():\nreturn 'bar'";
    var expectedResult = (
      "<div class='src-line-normal'>" +
        "<div class='src-line-number'>1</div>" +
        "<div class='src-line-code'>def foo():</div>" +
      "</div>" +
      "<div class='src-line-normal'>"+
        "<div class='src-line-number'>2</div>" +
        "<div class='src-line-code'>return 'bar'</div>" +
      "</div>");
    expect(code_heatmap.postProcessCode_(srcCode)).toBe(expectedResult);
  });

});
