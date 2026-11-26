'use strict';

module.exports = [
  {
    ignores: ['vprof/ui/vprof_min.js'],
  },
  {
    files: ['vprof/ui/**/*.js'],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'commonjs',
    },
    rules: {
      'camelcase': ['error', {'properties': 'never'}],
      'curly': 'error',
      'comma-spacing': ['error', {'before': false, 'after': true}],
      'eqeqeq': 'error',
      'indent': ['error', 2],
      'linebreak-style': ['error', 'unix'],
      'no-cond-assign': ['error', 'always'],
      'strict': ['error', 'global'],
      'semi': 'error',
      'max-len': ['error', 80, {'ignoreComments': true}],
    },
  },
];
