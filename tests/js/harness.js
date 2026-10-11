// Node harness for the Kalshi JS modules, driven by the Python tests.
// Reads one JSON request on stdin, runs the SAME kalshi/exact.js and
// kalshi/bets.js the page loads, and prints JSON results. No arithmetic here.
'use strict';
const path = require('path');
const fs = require('fs');
const root = path.join(__dirname, '..', '..', 'kalshi');
const Exact = require(path.join(root, 'exact.js'));
const Bets = require(path.join(root, 'bets.js'));

const request = JSON.parse(fs.readFileSync(0, 'utf8'));
const out = {};

if (request.exact) {
    out.exact = request.exact.map(function (op) {
        try {
            if (op.op === 'sum') return { ok: Exact.sum(op.args) };
            if (op.op === 'add') return { ok: Exact.add(op.args[0], op.args[1]) };
            if (op.op === 'sub') return { ok: Exact.sub(op.args[0], op.args[1]) };
            if (op.op === 'neg') return { ok: Exact.neg(op.args[0]) };
            if (op.op === 'cmp') return { ok: Exact.cmp(op.args[0], op.args[1]) };
            if (op.op === 'normalize') return { ok: Exact.normalize(op.args[0]) };
            return { error: 'unknown op' };
        } catch (err) {
            return { error: err.name + ': ' + err.message };
        }
    });
    out.scale = Exact.SCALE;
}

if (request.bets) {
    const data = JSON.parse(fs.readFileSync(request.bets.data, 'utf8'));
    const today = request.bets.today;
    out.presets = Bets.presets(today, data.summary.started);
    out.states = request.bets.states.map(function (query) {
        const state = Bets.parseState(query);
        const rows = Bets.filterBets(data.bets, state);
        const groups = Bets.groupRows(rows);
        return {
            query: query,
            state: state,
            round_trip: Bets.stateToQuery(state),
            reset: Bets.stateToQuery(Bets.resetRange(state)),
            label: Bets.rangeLabel(state, today, data.summary.started, rows.length, out.presets),
            indexes: rows.map(function (bet) { return data.bets.indexOf(bet); }),
            status_counts: Bets.statusCounts(data.bets, state),
            category_counts: Bets.categoryCounts(data.bets, state),
            totals: Bets.totals(rows),
            open: { indexes: groups.open.rows.map(function (bet) { return data.bets.indexOf(bet); }), totals: groups.open.totals },
            months: groups.months.map(function (month) {
                return { key: month.key, label: month.label, indexes: month.rows.map(function (bet) { return data.bets.indexOf(bet); }), totals: month.totals };
            })
        };
    });
}

process.stdout.write(JSON.stringify(out));
