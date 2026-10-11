/*
 * bets.js: filtering, grouping and totals for the Bets page.
 *
 * Pure functions (no DOM), shared by the page and by the Node parity tests.
 * Every money total goes through Exact (exact.js); this file never does
 * arithmetic on money itself (tests/test_kalshi_lint.py enforces it).
 *
 * A bet's "event date" is when it finished (settled or sold), or when it was
 * placed if it's still open. The timeline, date filters and month groups all
 * use it.
 */
(function (root, factory) {
    if (typeof module === 'object' && module.exports) {
        module.exports = factory(require('./exact.js'));
    } else {
        root.Bets = factory(root.Exact);
    }
})(typeof self !== 'undefined' ? self : this, function (Exact) {
    'use strict';

    var STATUSES = ['open', 'won', 'lost', 'sold', 'pending'];
    var STATUS_LABELS = { all: 'All', open: 'Open', won: 'Won', lost: 'Lost', sold: 'Sold', pending: 'Pending' };
    var CATEGORY_ORDER = ['NFL', 'NBA', 'College', 'Soccer', 'F1', 'Crypto', 'Politics', 'Other'];
    // NFL regular-season openers (Thursday after Labor Day).
    var NFL_KICKOFFS = ['2025-09-04', '2026-09-10', '2027-09-09'];
    var MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September',
        'October', 'November', 'December'];
    var SHORT_MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    var ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;
    var MONEY_KEYS = ['stake', 'buy_fees', 'cost', 'payout', 'sell_fees', 'net_payout', 'profit'];

    // ---------- Dates (calendar math only, never money) ----------
    function addDays(iso, days) {
        var parts = iso.split('-');
        var moment = new Date(Date.UTC(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]) + days)); // date-part
        return moment.toISOString().slice(0, 10);
    }
    function formatDate(iso) {
        var parts = iso.split('-');
        return SHORT_MONTHS[Number(parts[1]) - 1] + ' ' + Number(parts[2]) + ', ' + parts[0]; // date-part
    }
    function monthLabel(key) {
        var parts = key.split('-');
        return MONTHS[Number(parts[1]) - 1] + ' ' + parts[0]; // date-part
    }

    // ---------- Presets for the timeline chips ----------
    function presets(today, started) {
        var list = [{ key: 'all', label: 'All time', from: null, to: null }];
        var kickoff = NFL_KICKOFFS.filter(function (day) { return day <= today; }).pop();
        if (kickoff) list.push({ key: 'nfl', label: 'This NFL season', from: kickoff, to: null });
        list.push({ key: '30d', label: 'Last 30 days', from: addDays(today, -30), to: null });
        var firstYear = (started || today).slice(0, 4);
        for (var year = firstYear; year <= today.slice(0, 4); year = String(Number(year) + 1)) { // date-part
            list.push({ key: year, label: year, from: year + '-01-01', to: year + '-12-31' });
        }
        return list;
    }

    // ---------- URL state: "#bets?status=open&cat=NFL,Soccer&from=2026-09-01&to=2026-10-11&range=nfl" ----------
    function parseState(query) {
        var state = { status: 'all', cats: [], from: null, to: null, range: 'all' };
        (query || '').replace(/^\?/, '').split('&').forEach(function (pair) {
            if (!pair) return;
            var bits = pair.split('=');
            var key = decodeURIComponent(bits[0]);
            var value = decodeURIComponent(bits.slice(1).join('=') || '');
            if (key === 'status' && (value === 'all' || STATUSES.indexOf(value) >= 0)) state.status = value;
            if (key === 'cat' && value) state.cats = value.split(',').filter(function (cat) { return CATEGORY_ORDER.indexOf(cat) >= 0; });
            if (key === 'from' && ISO_DATE.test(value)) state.from = value;
            if (key === 'to' && ISO_DATE.test(value)) state.to = value;
            if (key === 'range' && value) state.range = value;
        });
        if (!state.from && !state.to) state.range = 'all';
        else if (state.range === 'all') state.range = 'custom';
        return state;
    }

    function stateToQuery(state) {
        var parts = [];
        if (state.status && state.status !== 'all') parts.push('status=' + state.status);
        if (state.cats && state.cats.length) parts.push('cat=' + state.cats.map(encodeURIComponent).join(','));
        if (state.from) parts.push('from=' + state.from);
        if (state.to) parts.push('to=' + state.to);
        if ((state.from || state.to) && state.range && state.range !== 'all' && state.range !== 'custom') parts.push('range=' + state.range);
        return parts.length ? '?' + parts.join('&') : '';
    }

    function withRange(state, preset) {
        return { status: state.status, cats: state.cats.slice(), from: preset.from, to: preset.to, range: preset.key };
    }

    // "Reset to all time": keeps status and categories, drops the date range.
    function resetRange(state) {
        return { status: state.status, cats: state.cats.slice(), from: null, to: null, range: 'all' };
    }

    function isAllTime(state) { return !state.from && !state.to; }

    // ---------- Filtering ----------
    function inRange(bet, state) {
        if (state.from && bet.event_date < state.from) return false;
        if (state.to && bet.event_date > state.to) return false;
        return true;
    }
    function matchesStatus(bet, state) { return state.status === 'all' || bet.outcome === state.status; }
    function matchesCats(bet, state) { return !state.cats.length || state.cats.indexOf(bet.category) >= 0; }

    function filterBets(bets, state) {
        return bets.filter(function (bet) { return inRange(bet, state) && matchesStatus(bet, state) && matchesCats(bet, state); });
    }

    // Facet counts: each control counts what the OTHER filters leave.
    function statusCounts(bets, state) {
        var pool = bets.filter(function (bet) { return inRange(bet, state) && matchesCats(bet, state); });
        var counts = { all: pool.length };
        STATUSES.forEach(function (status) {
            counts[status] = pool.filter(function (bet) { return bet.outcome === status; }).length;
        });
        return counts;
    }
    function categoryCounts(bets, state) {
        var pool = bets.filter(function (bet) { return inRange(bet, state) && matchesStatus(bet, state); });
        var counts = {};
        CATEGORY_ORDER.forEach(function (cat) {
            var count = pool.filter(function (bet) { return bet.category === cat; }).length;
            if (count) counts[cat] = count;
        });
        return counts;
    }

    // ---------- Exact totals ----------
    // Zone A sums over every row. Zone B/C sum over rows that have a value
    // (an open bet without a current bid has none); `unvalued` counts the rest.
    function totals(rows) {
        var valued = rows.filter(function (bet) { return bet.payout !== null && bet.payout !== undefined; });
        function sumOf(list, key) { return Exact.sum(list.map(function (bet) { return bet[key]; })); }
        return {
            count: rows.length,
            unvalued: rows.length - valued.length,
            stake: sumOf(rows, 'stake'),
            buy_fees: sumOf(rows, 'buy_fees'),
            cost: sumOf(rows, 'cost'),
            payout: sumOf(valued, 'payout'),
            sell_fees: sumOf(valued, 'sell_fees'),
            net_payout: sumOf(valued, 'net_payout'),
            profit: sumOf(valued, 'profit'),
            // Cost of only the valued rows, so Net payout - Cost = Profit holds exactly in the footer.
            valued_cost: sumOf(valued, 'cost')
        };
    }

    // Open bets first (their own group), then finished bets by month, newest first.
    function groupRows(rows) {
        var open = rows.filter(function (bet) { return bet.status === 'open'; });
        var closed = rows.filter(function (bet) { return bet.status !== 'open'; });
        var byMonth = {};
        var keys = [];
        closed.forEach(function (bet) {
            var key = bet.event_date.slice(0, 7);
            if (!byMonth[key]) { byMonth[key] = []; keys.push(key); }
            byMonth[key].push(bet);
        });
        keys.sort().reverse();
        return {
            open: { rows: open, totals: totals(open) },
            months: keys.map(function (key) {
                return { key: key, label: monthLabel(key), rows: byMonth[key], totals: totals(byMonth[key]) };
            })
        };
    }

    function rangeLabel(state, today, started, count, presetList) {
        var preset = (presetList || []).filter(function (item) { return item.key === state.range; })[0];
        var name = isAllTime(state) ? 'All time' : (preset ? preset.label : 'Custom range');
        var from = state.from || started || today;
        var to = state.to && state.to < today ? state.to : today;
        return 'Showing: ' + name + ' · ' + formatDate(from) + ' → ' + formatDate(to) + ' · ' + count + ' bet' + (count === 1 ? '' : 's');
    }

    return {
        STATUSES: STATUSES,
        STATUS_LABELS: STATUS_LABELS,
        CATEGORY_ORDER: CATEGORY_ORDER,
        MONEY_KEYS: MONEY_KEYS,
        addDays: addDays,
        formatDate: formatDate,
        monthLabel: monthLabel,
        presets: presets,
        parseState: parseState,
        stateToQuery: stateToQuery,
        withRange: withRange,
        resetRange: resetRange,
        isAllTime: isAllTime,
        filterBets: filterBets,
        statusCounts: statusCounts,
        categoryCounts: categoryCounts,
        totals: totals,
        groupRows: groupRows,
        rangeLabel: rangeLabel
    };
});
