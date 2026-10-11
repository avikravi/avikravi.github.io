/*
 * exact.js: exact decimal arithmetic for the Kalshi dashboard.
 *
 * The ONLY place the page does arithmetic on money (tests/test_kalshi_lint.py
 * enforces this). Amounts stay decimal strings everywhere; this module turns
 * them into BigInt integers at a fixed scale of SCALE decimal places, adds or
 * subtracts them exactly, and turns the result back into a trimmed decimal
 * string. There is no floating point anywhere. A value with more than SCALE
 * decimal places is refused (it would otherwise be silently rounded); Python
 * checks data.json's max_decimal_places against SCALE.
 *
 * Works as a browser global (window.Exact) and as a Node module (for tests).
 */
(function (root, factory) {
    if (typeof module === 'object' && module.exports) {
        module.exports = factory();
    } else {
        root.Exact = factory();
    }
})(typeof self !== 'undefined' ? self : this, function () {
    'use strict';

    var SCALE = 18;
    var UNIT = BigInt('1' + '0'.repeat(SCALE));
    var PATTERN = /^([+-]?)(\d+)(?:\.(\d+))?$/;

    // "-1.4878" -> -1487800000000000000n (scaled integer). Strings only.
    function toScaled(text) {
        if (typeof text !== 'string') {
            throw new TypeError('Exact needs a decimal string, got ' + typeof text);
        }
        var match = PATTERN.exec(text.trim());
        if (!match) {
            throw new Error('not a decimal string: "' + text + '"');
        }
        var frac = match[3] || '';
        if (frac.length > SCALE) {
            throw new RangeError('more than ' + SCALE + ' decimal places: "' + text + '"');
        }
        var scaled = BigInt(match[2] + frac.padEnd(SCALE, '0'));
        return match[1] === '-' ? -scaled : scaled;
    }

    // -1487800000000000000n -> "-1.4878" (trailing zeros trimmed, never "-0").
    function fromScaled(scaled) {
        var negative = scaled < 0n;
        var magnitude = negative ? -scaled : scaled;
        var whole = (magnitude / UNIT).toString();
        var frac = (magnitude % UNIT).toString().padStart(SCALE, '0').replace(/0+$/, '');
        var text = whole + (frac ? '.' + frac : '');
        return negative && text !== '0' ? '-' + text : text;
    }

    function add(left, right) { return fromScaled(toScaled(left) + toScaled(right)); }
    function sub(left, right) { return fromScaled(toScaled(left) - toScaled(right)); }
    function neg(value) { return fromScaled(-toScaled(value)); }
    function sum(values) {
        var total = 0n;
        values.forEach(function (value) { total += toScaled(value); });
        return fromScaled(total);
    }
    function cmp(left, right) {
        var diff = toScaled(left) - toScaled(right);
        return diff < 0n ? -1 : (diff > 0n ? 1 : 0);
    }
    function isZero(value) { return toScaled(value) === 0n; }
    function isNeg(value) { return toScaled(value) < 0n; }
    function isPos(value) { return toScaled(value) > 0n; }
    function normalize(value) { return fromScaled(toScaled(value)); }

    return {
        SCALE: SCALE,
        add: add,
        sub: sub,
        neg: neg,
        sum: sum,
        cmp: cmp,
        isZero: isZero,
        isNeg: isNeg,
        isPos: isPos,
        normalize: normalize
    };
});
