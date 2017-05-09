/**
 * @file Common UI functions.
 */

'use strict';

/**
 * Truncates string if length is greater than maxLength.
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
