/**
 * @file Module for common UI functions.
 */

'use strict';

/**
 * Truncates string if length is greater than maxLength.
 * @param {string} s - Input string.
 * @param {number} maxLength - Length of the output string.
 * @param {boolean} front - Whether append ellipsis at the start or at the end
 *                          of the string.
 * @returns {string}
 */
function shortenString(s, maxLength, front) {
  if (s.length <= maxLength) {
    return s;
  }
  if (front) {
    return '...' + s.substr(3 + (s.length - maxLength), s.length);
  }
  return s.substr(0, maxLength - 3) + '...';
}

module.exports = {
  'shortenString': shortenString,
};
