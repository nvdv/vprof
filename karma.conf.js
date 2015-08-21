// Karma configuration

module.exports = function(config) {
  config.set({
    basePath: 'vprof/frontend',
    frameworks: ['jasmine', 'browserify'],
    files: [
      '*_test.js',
    ],
    preprocessors: {
      '*_test.js': ['browserify']
    },
    reporters: ['progress'],
    port: 9876,
    colors: true,
    logLevel: config.LOG_INFO,
    autoWatch: true,
    browsers: ['PhantomJS'],
    singleRun: true
  })
}
