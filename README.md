# Midterm Elections Prediction Market: trade record

This repository holds the complete trade record of one account that traded contracts on the 2026 U.S. midterm elections, from Oct 1 to Nov 4, 2026.

- **Contracts**: each one pays 1 if its stated outcome happens and 0 if it does not. "NO" pays 1 if the outcome does not happen.
- **Account**: starting balance 100,000. Trading had no fees.
- **Times**: every row has UTC and US Eastern time.

## Summary

| Number | Value | Recomputed from |
|---|---|---|
| Final account value | 181,892.29, all cash | `fills.csv` + `settlements.csv` |
| Return | +81.9% on 100,000 | same |
| Max drawdown | 3.42% on daily values | `daily_value.csv` |
| Account value at 6:00 pm ET on Nov 3, when the first polls closed | 131,430.65 (+31.4%) | `hourly_value_election.csv` |
| Positions held to settlement | 29; all 29 paid 1 per share (181,885 in total) | `fills.csv` + `settlements.csv` |
| Activity | 1,406 fills, 680 orders, 98 contracts in 68 races | `fills.csv` |

Two notes on the "29 of 29" figure:

- Of the 98 contracts traded, 69 were closed by selling before settlement. Their gains and losses are in the cash totals, not in the 29.
- 6 of the 29 were first bought after 6:00 pm ET on Nov 3. Most of the 29 were on the same side of correlated races, so they are not 29 independent calls.

## Approach

Each contract was priced against a fair value: the average of the Polymarket and Kalshi prices for the same race. Capital went to the contracts with the highest expected return per unit of cash, and was moved when a swap raised the expected value at settlement. The largest position was a basket of correlated contracts on one side, held to settlement.

## Files

- `fills.csv`: every fill, one row each.
  - `fill_id`, `order_id`: the venue's IDs for the fill and its order. Fills with the same `order_id` came from one order.
  - `filled_at_utc`, `filled_at_et`: fill time.
  - `race`, `party`, `side`, `contract`: the contract in readable form.
  - `exchange_id`, `market_id`: the venue's IDs for the contract and its market.
  - `action`: buy or sell.
  - `price`, `shares`, `cash`: price, number of shares, and cash in or out (buys negative). Cash = price × shares.
  - `strategy`: the rule that placed the order. See the table below.
- `settlements.csv`: the 29 settlement payouts.
- `pnl_by_contract.csv`: for each contract, the cash paid, cash from sells, settlement payout and profit (= sells + payout − paid). The `group` column marks the legs of the main basket as `basket` and everything else as `other`. Basket: 67,658.34. Other: 14,233.96. Total: 81,892.29.
- `daily_value.csv`: daily account values.
- `hourly_value_election.csv`: hourly account values from Nov 3, 12:00 UTC, to Nov 4, 12:00 UTC.
- `verify.py`: recomputes every number in the summary table. It needs only the Python standard library.

## Strategy tags

| Tag | Meaning |
|---|---|
| `cheap-vs-external` | Buy below the external fair value by a set margin; hold to settlement. |
| `locked-payout-pair` | Buy a set of contracts in one race whose combined payout is fixed, below that payout. |
| `rotation-to-cheap` | Sell a position with little expected return left; buy one with more. |
| `concentrated-basket` | Buy legs of the main basket. |
| `basket-funding-sell` | Sell other positions to pay for the basket. |
| `pre-election-rotation` | Swaps between basket legs and discounted contracts, Nov 1 to Nov 3. |
| `election-night-rule` | Rule-based sells and reinvestment after polls closed. |
| `copy-signal` | Follow buys of selected Polymarket accounts (first days only). |
| `fast-turnover-trial` | Small trial: buy below the Polymarket price, sell at a profit. |
| `early-judgment-entry`, `two-sided-quoting`, `early-position-exit`, `old-position-sale` | First-days tests and their exits. |
| `exit-for-cash`, `expected-value-exit` | Sales made to free cash for a better use. |
| `fee-test`, `one-share-path-test` | One-share trades that tested the order path. |

Tags describe the rule, not a motive for each trade. Tags for 543 fills come from program logs written at the time; the other 863 were assigned afterwards from the contract and the date.

## How to verify

```
python3 verify.py
```

1. Cash paid for buys = Σ price × shares over buy rows = 287,338.355.
2. Cash received from sells = Σ price × shares over sell rows = 187,345.645.
3. Settlement payouts = Σ `payout` = 181,885.00.
4. Ending cash = 100,000 − 287,338.355 + 187,345.645 + 181,885.00 = **181,892.29**.
5. Return = 81,892.29 ÷ 100,000 = **+81.89%**.
6. Net shares per contract = shares bought − shares sold. Exactly 29 contracts are non-zero. Each matches one settlement record, and each record pays 1 per share.
7. Max drawdown = the largest (running peak − value) ÷ running peak over the daily values = (130,055.01 − 125,608.00) ÷ 130,055.01 = **3.42%**.
8. Value before polls closed = the hourly value at 2026-11-03 23:00 UTC = 131,430.65, or **+31.4%**.

Orders that never filled are left out. Only fills move cash.
