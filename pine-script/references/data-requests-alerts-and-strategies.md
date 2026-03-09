# Data Requests, Alerts, and Strategies

Reference for chart context variables, external data requests, sessions, non-standard feeds, repainting, alerts, and strategy simulation.

## Contents
1. [Chart Context Variables](#1-chart-context-variables)
2. [Other Timeframes and Data (`request.*()`)](#2-other-timeframes-and-data-request)
3. [Sessions](#3-sessions)
4. [Repainting](#4-repainting)
5. [Alerts](#5-alerts)
6. [Strategies](#6-strategies)
7. [Scaffold Examples](#7-scaffold-examples)

---

## 1. Chart Context Variables

### Prices and Volume

| Variable | Description |
|---|---|
| `open` | Opening price |
| `high` | Highest price (or highest tick so far on realtime bar) |
| `low` | Lowest price (or lowest tick so far on realtime bar) |
| `close` | Closing price (or current price on realtime bar) |
| `volume` | Volume traded (shares/lots/contracts/base currency depending on instrument) |
| `hl2` | `(high + low) / 2` |
| `hlc3` | `(high + low + close) / 3` |
| `ohlc4` | `(open + high + low + close) / 4` |

On historical bars: values are fixed at bar close. On realtime bars: `high`, `low`, `close` fluctuate until bar closes. `open` does not change on realtime bars.

### Symbol Information (`syminfo.*`)

| Variable | Type | Description |
|---|---|---|
| `syminfo.tickerid` | `simple string` | "EXCHANGE:SYMBOL" — recommended for `request.*()` calls |
| `syminfo.ticker` | `simple string` | Symbol name without exchange |
| `syminfo.prefix` | `simple string` | Exchange prefix |
| `syminfo.description` | `simple string` | Long display name |
| `syminfo.type` | `simple string` | "stock", "futures", "forex", "crypto", "index", "fund", "cfd", "bond", etc. |
| `syminfo.currency` | `simple string` | Quote currency |
| `syminfo.basecurrency` | `simple string` | Base currency (BTC in BTCUSD) |
| `syminfo.mintick` | `simple float` | Minimum price increment |
| `syminfo.pointvalue` | `simple float` | Contract multiplier (50 for ES1!) |
| `syminfo.mincontract` | `simple float` | Smallest tradeable quantity |
| `syminfo.session` | `simple string` | Active session name (e.g. `session.regular`, `session.extended`) |
| `syminfo.timezone` | `simple string` | IANA timezone name, e.g. "America/New_York" |
| `syminfo.root` | `simple string` | Root prefix for structured tickers (ES for ES1!) |
| `syminfo.main_tickerid` | `simple string` | Always represents the chart's ticker, even inside `request.*()` contexts |

### Chart Timeframe (`timeframe.*`)

**Boolean type flags:**
`timeframe.isseconds`, `timeframe.isminutes`, `timeframe.isintraday`, `timeframe.isdaily`, `timeframe.isweekly`, `timeframe.ismonthly`, `timeframe.isdwm`

**Numeric details:**
- `timeframe.multiplier` — `simple int`; intraday returns minutes, daily returns 1, monthly returns number of months
- `timeframe.period` — `simple string`; "1D", "60", "W", etc.; references requested context when inside `request.*()` expression
- `timeframe.main_period` — `simple string`; always the script's main timeframe, even inside requested contexts

**Utility functions:**
- `timeframe.in_seconds(tf)` — converts timeframe string to seconds
- `timeframe.from_seconds(int)` — builds valid timeframe string from seconds count
- `timeframe.change(tf)` — returns `true` on first chart bar of a new higher-TF bar

---

## 2. Other Timeframes and Data (`request.*()`)

### `request.security()` — Core HTF/Cross-Symbol Request

```
request.security(symbol, timeframe, expression, gaps, lookahead,
                 ignore_invalid_symbol, currency, calc_bars_count) → series <type>
```

**`symbol`** — ticker ID:
- String: `"AAPL"`, `"NYSE:IBM"`, `"AMD/INTC"` (spread)
- Built-in: `syminfo.tickerid` (recommended) or `syminfo.ticker`
- Custom: result of `ticker.new()`, `ticker.modify()`, `ticker.heikinashi()`, etc.
- Empty string `""` = current chart symbol

**`timeframe`** — timeframe string:
- `timeframe.period` or `""` = same as chart
- Higher TF: "D", "W", "240", "1D"
- Lower TF: only use `request.security_lower_tf()` for this in most cases

**`expression`** — what to evaluate in the requested context:
- Built-in variable: `close`, `high`, `volume`, etc.
- Declared variable: `float priceReturn = (close - close[1]) / close[1]`
- Built-in function call: `ta.sma(close, 20)`
- Tuple: `[open, high, low, close]` (destructure with `[o, h, l, c] = request.security(...)`)
- `chart.point` ID: returns chart.point from requested context
- Collections (arrays, maps): elements must be fundamental types or UDTs with valid field types
- UDT objects: fields must be fundamental types, chart.points, collections, or nested UDTs

**`gaps`** — `barmerge.gaps_off` *(default)* or `barmerge.gaps_on`:
- `gaps_off` — uses previous value when no new data (fills gaps)
- `gaps_on` — returns `na` when no new data (useful for session-filtered data, HTF candle detection)

**`lookahead`** — `barmerge.lookahead_off` *(default)* or `barmerge.lookahead_on`:
- `lookahead_off` — returns last confirmed value of the HTF bar; safe on historical
- `lookahead_on` — **DO NOT use without offset**: leaks future data on historical bars
- **Correct non-repainting pattern**: `request.security(sym, tf, close[1], lookahead = barmerge.lookahead_on)`

**`calc_bars_count`** — int; restricts how many chart bars the request evaluates

### Higher-Timeframe Non-Repainting Pattern (Critical)

```pine
// WRONG — future leak on historical bars:
htfHigh = request.security(syminfo.tickerid, "D", high, lookahead = barmerge.lookahead_on)

// WRONG — repaints on realtime bars (unconfirmed values):
htfClose = request.security(syminfo.tickerid, "D", close)

// CORRECT — non-repainting:
htfClose = request.security(syminfo.tickerid, "D", close[1], lookahead = barmerge.lookahead_on)

// Reusable wrapper:
noRepaintSecurity(symbol, tf, expr) =>
    request.security(symbol, tf, expr[1], lookahead = barmerge.lookahead_on)
```

### `request.security_lower_tf()`

```
request.security_lower_tf(symbol, timeframe, expression, ignore_invalid_symbol,
                           currency, ignore_invalid_timeframe, calc_bars_count) → array<type>
```

- Returns `array<type>` containing **all** intrabar values for each chart bar
- `timeframe` must be ≤ chart timeframe (raises runtime error if higher)
- Maximum 200,000 intrabars total across the chart history
- Preferred over `request.security()` for LTF data

### Other `request.*()` Functions

| Function | Purpose |
|---|---|
| `request.currency_rate(from, to, ignore_invalid_currency)` | Daily cross-rate for currency conversion |
| `request.dividends(ticker, field, gaps, lookahead, ignore_invalid_symbol, currency)` | Dividend info (field: `dividends.gross`, `dividends.net`) |
| `request.splits(ticker, field, gaps, lookahead, ignore_invalid_symbol)` | Split info (field: `splits.denominator`, `splits.numerator`) |
| `request.earnings(ticker, field, gaps, lookahead, ignore_invalid_symbol, currency)` | Earnings (field: `earnings.actual`, `earnings.estimate`, `earnings.standardized`) |
| `request.financial(symbol, financial_id, period, gaps, ignore_invalid_symbol, currency)` | FactSet financial data (e.g. `"OPER_INCOME"`, `"TOTAL_REVENUE"`) |
| `request.economic(country_code, field)` | Economic/industry data by country code (e.g. `"US"`, `"GB"`) and field code (e.g. `"GDPQQ"`, `"CPI"`) |
| `request.footprint(symbol, timeframe, expression)` | Volume footprint data → `footprint` object |
| `request.seed(source, symbol, expression)` | Data from user-maintained GitHub repository |

### Custom Tickers (`ticker.*()`)

Combined with `request.security()` for custom contexts:

```pine
ticker.new(prefix, ticker, session, adjustment)         // build from parts
ticker.modify(tickerid, session, adjustment)             // modify existing tickerid
ticker.heikinashi(symbol)                                // Heikin-Ashi prices
ticker.renko(symbol, box_size_type, box_size)            // Renko bars
ticker.linebreak(symbol, number_of_lines)                // Line Break bars
ticker.kagi(symbol, reversal_amount_type, amount)        // Kagi bars
ticker.pointfigure(symbol, source, box_size_type, box_size, reversal)  // PnF bars
```

**Non-standard chart feeds:**
- Heikin-Ashi: synthetic OHLC averaged from real OHLC; visual smoothing; NOT suitable for backtesting
- Renko/Line Break/Kagi/PnF: constructed from lower-TF price data; approximate tick-data calculations

### Dynamic Requests

`request.security()` accepts series strings for both `symbol` and `timeframe`, allowing dynamic values per bar. The number of unique contexts is still constrained at runtime.

---

## 3. Sessions

### Time-Based Session Strings

Format: `"HHMM-HHMM"` or `"HHMM-HHMM:DDDDDDD"` (D = 1=Sun through 7=Sat)

Examples:
- `"0930-1600"` — US regular session
- `"0830-1530:23456"` — Mon-Fri only
- `"0000-0000"` — all hours of all days (24×7)

**Three functions that accept time-based sessions:**
- `time(timeframe, session, timezone)` — returns UNIX timestamp (ms) if bar opens in session, else `na`
- `time_close(timeframe, session, timezone)` — returns close timestamp if bar closes in session, else `na`
- `input.session(defval, title, ...)` — user input for session string

```pine
// Check if bar opens in session:
inSession = not na(time(timeframe.period, "0930-1600"))
bgcolor(inSession ? color.new(color.green, 90) : na)

// Dynamic session (series string):
session = dayofweek == dayofweek.saturday or dayofweek == dayofweek.sunday
    ? "0000-0000"
    : "0700-2000"
inSession = not na(time(timeframe.period, session))
```

### Named Sessions

Named sessions have exchange-defined strings:
- `session.regular` — regular session (const string `"regular"`)
- `session.extended` — extended session (const string `"extended"`)
- Symbol-specific names like `"xetr_regular"`, `"fwb_regular"`, `"us_regular"` etc.
- Retrieve active session name via `syminfo.session`

**Creating session-specific tickers:**
```pine
extTicker = ticker.new(syminfo.prefix, syminfo.ticker, session.extended)
extClose  = request.security(extTicker, timeframe.period, close, barmerge.gaps_on)
```

### Session State Variables

**Market state:**
- `session.ismarket` — in regular (market hours) session
- `session.ispremarket` — in pre-market session
- `session.ispostmarket` — in post-market session

**Session boundary:**
- `session.isfirstbar` — first bar of today's session (including pre-market if selected)
- `session.isfirstbar_regular` — first bar of regular session only
- `session.islastbar` — last bar of today's session
- `session.islastbar_regular` — last bar of regular session only

---

## 4. Repainting

Repainting = script behaves differently on historical vs. realtime bars.

### Categories

| Type | Acceptable? | Cause |
|---|---|---|
| Fluid values (RSI, close changing intrabar) | Often acceptable | Using `close`/`high`/`low` on open bar |
| HTF unconfirmed | Sometimes acceptable | `request.security()` without `[1]` offset |
| Plotting into the past | Potentially misleading | `label.new(bar_index[5], ...)` for pivot markers |
| Future leak | Never acceptable | `lookahead_on` without `[1]` offset |
| `varip` repainting | Situational | `varip` variables update intrabar |
| `calc_on_every_tick` strategies | Often misleading | Backtests vs. realtime diverge |

### Avoiding Repainting

**Use `barstate.isconfirmed`** (cleanest for most cases):
```pine
xUp = ta.crossover(close, ma) and barstate.isconfirmed
```

**Offset expression with `[1]`** (confirmed prior bar):
```pine
xUp = ta.crossover(close, ma)[1]
```

**Use `open` instead of `close`** (doesn't change intrabar):
```pine
xUp = ta.crossover(open, ma[1])
```

**Non-repainting HTF data** — combine `[1]` offset + `lookahead_on`:
```pine
htfClose = request.security(syminfo.tickerid, "D", close[1], lookahead = barmerge.lookahead_on)
```

### Plotting Into the Past

Pivot-labeling patterns commonly place labels 5 bars in the past:
```pine
pHi = ta.pivothigh(5, 5)
if not na(pHi)
    label.new(bar_index[5], na, str.tostring(pHi, format.mintick), yloc = yloc.abovebar)
```
This is a repainting pattern — the label will appear retroactively on a realtime bar. Best practice: make it optional via an input.

---

## 5. Alerts

### Three Alert Mechanisms

| Mechanism | Works in | Frequency control | Message type |
|---|---|---|---|
| `alert()` function | Indicators + Strategies | `freq` parameter | `series string` (dynamic) |
| `alertcondition()` function | Indicators only | User chooses in UI | `const string` + placeholders |
| Order fill events | Strategies only | Automatic on order fill | Custom via `alert_message` param |

### `alert()` Function

```
alert(message, freq) → void
```

- `message` — `series string`; can be constructed dynamically at runtime
- `freq` — `alert.freq_once_per_bar` *(default)*, `alert.freq_once_per_bar_close`, `alert.freq_all`
- Can be called inside `if` blocks (unlike `alertcondition()`)
- In strategies: by default only fires at bar close (= `alert.freq_once_per_bar_close`); requires `calc_on_every_tick = true` for intrabar alerts

```pine
if ta.crossover(close, ma) and barstate.isconfirmed
    alert("Bullish cross at " + str.tostring(close, format.mintick))
```

### `alertcondition()` Function

```
alertcondition(condition, title, message) → void
```

- `condition` — `series bool`; when `true`, alert fires
- `title` — `const string`; appears in Create Alert dialog's Condition dropdown
- `message` — `const string`; can contain placeholders
- **Must be in global scope (column 0)** — cannot be inside `if` blocks
- Multiple `alertcondition()` calls → multiple selectable conditions in the dialog
- Frequency set by the user in Create Alert UI (not in code)
- Does NOT work in strategies

**Placeholders for `alertcondition()` messages:**

| Placeholder | Value |
|---|---|
| `{{exchange}}` | Exchange name |
| `{{ticker}}` | Symbol ticker |
| `{{interval}}` | Timeframe of chart |
| `{{open}}`, `{{high}}`, `{{low}}`, `{{close}}`, `{{volume}}` | Bar OHLCV values |
| `{{plot_0}}` through `{{plot_19}}` | Value of corresponding plot by index |
| `{{plot("Plot Title")}}` | Value of named plot (use single quotes around message) |
| `{{time}}` | Bar open time in UTC (ISO 8601) |
| `{{timenow}}` | Alert trigger time |

### Strategy Order Fill Alerts

- Automatically available on any strategy — no extra code needed
- Custom messages via `alert_message` parameter in order functions:
  ```pine
  strategy.entry("Long", strategy.long, alert_message = "Buy at " + str.tostring(close))
  ```
- User must add `{{strategy.order.alert_message}}` to the Message field in Create Alert dialog
- Use compiler annotation for default message: `///@strategy_alert_message {{strategy.order.action}} {{ticker}} @ {{strategy.order.price}}`

### Alert Design Principles

- **Repainting alerts**: If frequency is not "Once Per Bar Close" and condition uses `close`/`high`/`low`, it can trigger intrabar and then become false at close
- **Non-repainting**: Use `barstate.isconfirmed` + `alert.freq_once_per_bar_close` to guarantee only confirmed bars trigger
- Alerts run on TradingView servers; once created, changing script inputs or chart symbol does NOT update the running alert

---

## 6. Strategies

### Declaration

```pine
strategy(title, shorttitle, overlay, format, precision, scale, pyramiding,
         calc_on_order_fills, calc_on_every_tick, max_bars_back,
         backtest_fill_model, default_qty_type, default_qty_value,
         initial_capital, currency, slippage, commission_type, commission_value,
         process_orders_on_close, close_entries_rule, margin_long, margin_short,
         risk_free_rate, use_bar_magnifier, explicit_plot_zorder,
         max_lines_count, max_labels_count, max_boxes_count, max_polylines_count,
         force_overlay, behind_chart, calc_bars_count, fill_orders_on_standard_ohlc)
```

Key parameters:
- `initial_capital` — starting equity
- `currency` — account currency (e.g. `currency.USD`)
- `default_qty_type` — `strategy.fixed`, `strategy.cash`, `strategy.percent_of_equity`
- `default_qty_value` — default size per order
- `pyramiding` — max allowed entries in same direction at one time
- `calc_on_every_tick` — recalculate on every realtime tick (affects `alert()` and order fill timing)
- `process_orders_on_close` — fill orders on bar close instead of next bar open
- `commission_type` / `commission_value` — simulated commission
- `slippage` — simulated slippage in ticks

### Order Placement and Cancellation

**Entry:**
```pine
strategy.entry(id, direction, qty, limit, stop, oca_name, oca_type, comment, alert_message, disable_alert)
```
- `direction` — `strategy.long` or `strategy.short`
- No `qty` or `qty = na` → uses `default_qty_value`
- If same `id` is used again without closing: existing order is replaced or pyramided based on settings

**General order:**
```pine
strategy.order(id, direction, qty, limit, stop, oca_name, oca_type, comment, alert_message, disable_alert)
```
- Unlike `strategy.entry()`, does not respect pyramiding rules
- Used for custom order accumulation logic

**Exit:**
```pine
strategy.exit(id, from_entry, qty, qty_percent, profit, limit, loss, stop,
              trail_price, trail_points, trail_offset, oca_name, comment,
              comment_profit, comment_loss, comment_trailing, alert_message, alert_profit,
              alert_loss, alert_trailing, disable_alert)
```
- `from_entry` — ID of the entry to exit; `""` = any/last open entry
- `profit`/`loss` — in ticks
- `limit`/`stop` — price levels
- `trail_points`/`trail_offset` — trailing stop

**Close:**
```pine
strategy.close(id, comment, qty, qty_percent, alert_message, immediately, disable_alert)
strategy.close_all(comment, alert_message, immediately, disable_alert)
```

**Cancel:**
```pine
strategy.cancel(id, comment)
strategy.cancel_all(comment)
```

### Order Types

| Type | How | Example |
|---|---|---|
| Market | No `limit` or `stop` | `strategy.entry("Buy", strategy.long)` |
| Limit | `limit = price` | `strategy.entry("Buy", strategy.long, limit = low)` |
| Stop | `stop = price` | `strategy.entry("Buy", strategy.long, stop = high)` |
| Stop-limit | Both `limit` and `stop` | `strategy.entry("Buy", strategy.long, limit = l, stop = s)` |

### Position Sizing

```pine
strategy.entry("Long", strategy.long, qty = myQty)
```

- `strategy.fixed` — fixed number of contracts/shares
- `strategy.cash` — dollar amount
- `strategy.percent_of_equity` — percentage of current equity

Override `default_qty_value` by passing `qty` to order functions (pass `na` to use default).

### OCA Groups

One-Cancels-All groups allow linked orders:
- `strategy.oca.cancel` — cancel all others when one fills
- `strategy.oca.reduce` — reduce qty of others proportionally
- `strategy.oca.none` — independent (default)

### Strategy Information Variables

**Account and performance:**
`strategy.equity`, `strategy.initial_capital`, `strategy.account_currency`, `strategy.netprofit`, `strategy.netprofit_percent`, `strategy.grossprofit`, `strategy.grossloss`, `strategy.openprofit`, `strategy.max_runup`, `strategy.max_drawdown`

**Trade counts:**
`strategy.opentrades`, `strategy.closedtrades`, `strategy.wintrades`, `strategy.losstrades`, `strategy.eventrades`

**Position:**
`strategy.position_size`, `strategy.position_avg_price`, `strategy.position_entry_name`

**Open trade data** (`strategy.opentrades.*`):
`entry_id()`, `entry_price()`, `entry_bar_index()`, `entry_time()`, `entry_comment()`, `size()`, `profit()`, `commission()`, `max_runup()`, `max_drawdown()`, `capital_held`

**Closed trade data** (`strategy.closedtrades.*`):
All `entry_*` and all `exit_*` functions: `exit_id()`, `exit_price()`, `exit_bar_index()`, `exit_time()`, `exit_comment()`

### Strategy Tester Tabs

- **Overview**: Equity curve, drawdown bars, buy-and-hold comparison
- **Performance Summary**: Win rate, Sharpe ratio, Sortino ratio, max drawdown, profit factor, etc.
- **List of Trades**: Chronological entry/exit details
- **Properties**: Date range, symbol info, strategy inputs

### Risk Management

```pine
strategy.risk.max_drawdown(value, type)       // stop trading after drawdown
strategy.risk.max_intraday_loss(value, type)  // daily loss limit
strategy.risk.max_intraday_filled_orders(count) // daily order count limit
```

### Strategy Alerts

- Strategies use `alert()` for custom events AND order fill events for automatic alerts
- By default `alert()` in strategies only fires at bar close
- `calc_on_every_tick = true` enables intrabar `alert()` calls
- Order fill alerts fire immediately regardless of `calc_on_every_tick`
- Use `///@strategy_alert_message` annotaton to set default Create Alert message

---

## 7. Scaffold Examples

### Non-Repainting HTF Data
```pine
//@version=6
indicator("Non-Repainting Daily Close", overlay = true)

// Always use [1] + lookahead_on for confirmed HTF values
htfClose = request.security(syminfo.tickerid, "D", close[1], lookahead = barmerge.lookahead_on)
plot(htfClose, "Daily Close", color.orange, 2)

// Mark when a new daily bar begins
plotshape(timeframe.change("D"), "New Day", shape.diamond, location.top, color.orange, size = size.small)
```

### Session Background
```pine
//@version=6
indicator("NY Session", overlay = true)

sessionInput = input.session("0930-1600:23456", "Session")
inSession    = not na(time(timeframe.period, sessionInput))
bgcolor(inSession ? color.new(color.blue, 88) : na, title = "Session BG")
```

### Confirmed Alert
```pine
//@version=6
indicator("Confirmed Cross Alert", overlay = true)

fastLen = input.int(10, "Fast")
slowLen = input.int(20, "Slow")
fast    = ta.sma(close, fastLen)
slow    = ta.sma(close, slowLen)

// alertcondition fires on confirmed bar only because it uses barstate.isconfirmed
bullCross = ta.crossover(fast, slow) and barstate.isconfirmed
bearCross = ta.crossunder(fast, slow) and barstate.isconfirmed

plot(fast, "Fast", color.teal)
plot(slow, "Slow", color.orange)

// Two selectable conditions in Create Alert dialog:
alertcondition(bullCross, "Bull Cross", "Bull cross on {{ticker}}: fast={{plot_0}}, slow={{plot_1}}")
alertcondition(bearCross, "Bear Cross", "Bear cross on {{ticker}}: fast={{plot_0}}, slow={{plot_1}}")
```

### Simple MA Crossover Strategy
```pine
//@version=6
strategy("MA Cross Strategy", overlay = true, default_qty_type = strategy.percent_of_equity,
         default_qty_value = 10, initial_capital = 10000)

fastLen = input.int(10, "Fast MA")
slowLen = input.int(20, "Slow MA")
fast    = ta.sma(close, fastLen)
slow    = ta.sma(close, slowLen)

if ta.crossover(fast, slow)
    strategy.entry("Long",  strategy.long,
                   alert_message = "Long entry at " + str.tostring(close, format.mintick))
if ta.crossunder(fast, slow)
    strategy.entry("Short", strategy.short,
                   alert_message = "Short entry at " + str.tostring(close, format.mintick))

plot(fast, "Fast", color.teal)
plot(slow, "Slow", color.orange)
```

### Cross-Symbol Correlation
```pine
//@version=6
indicator("SPY Correlation", overlay = false)

symbolInput = input.symbol("SPY", "Compare Symbol")
lengthInput = input.int(60, "Correlation Length", 1)

float chartReturn  = (close - close[1]) / close[1]
float compareClose = request.security(symbolInput, timeframe.period, close)
float compareReturn = (compareClose - compareClose[1]) / compareClose[1]

corr = ta.correlation(chartReturn, compareReturn, lengthInput)
plot(corr, "Correlation", corr > 0 ? color.teal : color.red, 2)
hline(0, "Zero", color.gray, hline.style_dashed)
```

