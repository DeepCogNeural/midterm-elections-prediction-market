#!/usr/bin/env python3
"""Recompute the summary numbers in README.md from the CSV files in this folder.

Standard library only. Run: python3 verify.py
"""
import csv
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
START = Decimal('100000')
RECORDED_END = Decimal('181892.29')      # account value after settlement, as recorded
POLLS_CLOSE_UTC = '2026-11-03T23:00:00.000Z'  # 6:00 pm ET, first polls close


def rows(name):
    with open(HERE / name, newline='') as fh:
        return list(csv.DictReader(fh))


fills, settles = rows('fills.csv'), rows('settlements.csv')
daily, hourly = rows('daily_value.csv'), rows('hourly_value_election.csv')

# 1. Cash reconciliation: start - buys + sells + settlement payouts
paid = sum(Decimal(r['price']) * int(r['shares']) for r in fills if r['action'] == 'buy')
received = sum(Decimal(r['price']) * int(r['shares']) for r in fills if r['action'] == 'sell')
payouts = sum(Decimal(r['payout']) for r in settles)
assert sum(Decimal(r['cash']) for r in fills) == received - paid
end = START - paid + received + payouts
print(f'fills {len(fills)}, orders {len({r["order_id"] for r in fills})}, '
      f'markets {len({r["race"] for r in fills})}, '
      f'contracts {len({r["contract"] for r in fills})}')
print(f'cash paid for buys      {paid:>14,.4f}')
print(f'cash received for sells {received:>14,.4f}')
print(f'settlement payouts      {payouts:>14,.2f}')
print(f'ending cash = 100,000 - buys + sells + payouts = {end:,.4f}')
print(f'recorded account value {RECORDED_END:,.2f}; residual {end - RECORDED_END:+.4f}')
print(f'return {(end - START) / START:.2%}')

# 2. Positions held to settlement: net shares from fills vs settlement records
net = defaultdict(int)
for r in fills:
    net[r['contract']] += int(r['shares']) * (1 if r['action'] == 'buy' else -1)
held = {k: v for k, v in net.items() if v != 0}
paid_out = {r['contract']: int(r['shares']) for r in settles}
assert all(v > 0 for v in held.values()), 'negative position'
assert held == paid_out, 'net shares from fills do not match settlement shares'
wins = sum(1 for r in settles if r['side'] == r['market_result'] and Decimal(r['payout_per_share']) == 1)
print(f'positions held to settlement {len(held)}; paid 1 per share {wins}; '
      f'closed before settlement {len(net) - len(held)}')
late = {r['contract'] for r in fills
        if r['action'] == 'buy' and r['filled_at_utc'] >= POLLS_CLOSE_UTC}
first = {}
for r in fills:
    k = r['contract']
    if r['action'] == 'buy' and k not in first:
        first[k] = r['filled_at_utc']
opened_late = sum(1 for k in held if first[k] >= POLLS_CLOSE_UTC)
print(f'of these, opened after 6 pm ET Nov 3: {opened_late}; '
      f'opened earlier but added to after 6 pm ET: {len(late & held.keys()) - opened_late}')

pnl = rows('pnl_by_contract.csv')
by_group = defaultdict(Decimal)
for r in pnl:
    by_group[r['group']] += Decimal(r['profit'])
assert sum(by_group.values()) == end - START
print('profit by group: ' + ', '.join(f'{g} {v:,.2f}' for g, v in sorted(by_group.items())))

# 3. Max drawdown on daily values
peak, mdd, at = Decimal(0), Decimal(0), ''
for r in daily:
    v = Decimal(r['total_value'])
    peak = max(peak, v)
    if (peak - v) / peak > mdd:
        mdd, at = (peak - v) / peak, r['time_utc'][:10]
print(f'max drawdown on {len(daily)} daily values {mdd:.2%} (low on {at})')

# 4. Value before polls closed (hourly value at 6:00 pm ET Nov 3)
v = Decimal(next(r['total_value'] for r in hourly if r['time_utc'] == POLLS_CLOSE_UTC))
print(f'value at {POLLS_CLOSE_UTC} (6:00 pm ET): {v:,.2f}, {(v - START) / START:+.1%}')

# 5. Profit / traded value, and Sharpe ratio on daily returns
import math, statistics
volume = paid + received
print(f'traded value {volume:,.2f}; profit / traded value {(end - START) / volume:.2%}')
vals = [float(r['total_value']) for r in daily]
rets = [b / a - 1 for a, b in zip(vals, vals[1:])]
sh = statistics.mean(rets) / statistics.stdev(rets)
print(f'daily returns {len(rets)}; largest {max(rets):+.1%}; '
      f'Sharpe x sqrt(252) {sh * math.sqrt(252):.2f}, x sqrt(365) {sh * math.sqrt(365):.2f}')
