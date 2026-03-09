# Quality

Reference for code style, internal compiler limits, profiling, optimization techniques, and publishing rules.

## Contents
1. [Style Guide](#1-style-guide)
2. [Limitations](#2-limitations)
3. [Profiling and Optimization](#3-profiling-and-optimization)
4. [Publishing Rules](#4-publishing-rules)
5. [Final Review Checklist](#5-final-review-checklist)

---

## 1. Style Guide

### Naming Conventions

| Pattern | Usage |
|---|---|
| `camelCase` | All variables and functions — `ma`, `maFast`, `showLinesInput`, `calcRSI()` |
| `SNAKE_CASE` (ALL CAPS) | Constants — `BULL_COLOR`, `MAX_LOOKBACK`, `MS_IN_DAY` |
| Qualifying suffixes | Add context to names — `maLengthInput`, `bearColorInput`, `volumesArray`, `resultsTable`, `maPlotID` |

### Recommended Script Organization Order

```
// License comment (if open-source)
//@version=6
indicator(...)           // or strategy() or library()

// Import statements
import <library>

// Constants (SNAKE_CASE, const-qualified)
int MS_IN_MIN = 60 * 1000

// Inputs (suffix with "Input")
int lengthInput = input.int(...)

// User-defined functions (all must be in global scope)
calcSomething(...) => ...

// Calculations (core logic)
float myValue = ...

// Strategy calls (strategies only)
strategy.entry(...)

// Visuals (plots, fills, backgrounds, drawings)
plot(...)

// Alerts
alertcondition(...)
alert(...)
```

### Spaces and Formatting

- Put spaces on **both sides** of all binary operators: `a = b + c`, not `a=b+c`
- Exception: unary operators have no space before the operand: `-1`, `not flag`
- Put a space after commas: `plot(series = close, color = color.red)`
- Use named arguments for clarity in function calls

### Line Wrapping

- Long lines can be wrapped using any non-multiple-of-4 indentation (unless inside parentheses)
- Inside parentheses (function args, tuples, etc.), any indentation works including multiples of 4
- For long string literals, use concatenation with `+` across lines

### Explicit Typing

Declaring the type of variables is optional but recommended:
```pine
float myRatio = close / open       // clear that it returns float
array<float> prices = array.new<float>()  // type makes intent obvious
```

### Constants

- Use constants instead of repeating literal values
- Do NOT use `var` for constants (minor runtime penalty; `var` is for series-persisted values)
- Constants only used in a local block should be declared in that block

### Vertical Alignment

Use vertical alignment for blocks of similar declarations to improve readability and multi-cursor editing:
```pine
color BULL_COLOR = color.green
color BEAR_COLOR = color.red
color NEUT_COLOR = color.gray
```

---

## 2. Limitations

### Time Limits

| Limit | Value |
|---|---|
| Script compilation timeout | 2 minutes (3 consecutive warnings → 1-hour ban) |
| Script execution (basic accounts) | 20 seconds |
| Script execution (paid plans) | 40 seconds |
| Single loop on a single bar | 500 milliseconds |

### Chart Visuals

**Plot counts:**
- Maximum **64 plot counts** per script
- Functions that consume plot counts:
  - `plot()` — 1 per call (more if `color` is `series`)
  - `plotarrow()` — 1–3 depending on which series args use `series color`
  - `plotbar()` — 4–5 depending on `color` arg
  - `plotcandle()` — 4–7 depending on `color`, `wickcolor`, `bordercolor` args
  - `plotchar()` — 1–3 depending on `color` and `textcolor` args
  - `plotshape()` — 1–3 depending on `color` and `textcolor` args
  - `alertcondition()` — 1 per call
  - `bgcolor()` — 1 per call
  - `barcolor()` — 1 per call
  - `fill()` — 1 per call, but only if `color` is a `series` type
- Functions that do NOT consume plot counts: `hline()`, `line.new()`, `label.new()`, `table.new()`, `box.new()`

**Drawing limits:**
- Lines, boxes, polylines, labels: default **last 50** objects shown
- Increase via `max_lines_count`, `max_boxes_count`, `max_polylines_count`, `max_labels_count` in declaration
- Objects with `na` x coordinates still count toward the limit → use conditional `if` to avoid creating unnecessary objects

**Table limits:**
- Maximum **9 tables** on the chart (one per position constant)
- Multiple tables in the same position: only the last one created shows

### `request.*()` Limits

| Limit | Value |
|---|---|
| Unique `request.*()` calls | 40 (64 for Ultimate plan) |
| Intrabars (lower TF data) — Basic/Essential/Plus/Premium | 100,000 |
| Intrabars — Expert | 125,000 |
| Intrabars — Ultimate | 200,000 |
| Tuple elements across all requests combined | 127 |

- **Identical calls** (same function + same args) count only once toward the limit
- Calls inside imported libraries count separately from the main script's calls
- **Tuple workaround**: use a UDT with fields instead of a 128-element tuple

### Script Size and Memory

| Limit | Value |
|---|---|
| Compiled IL tokens per script | 100,000 |
| Compiled tokens from all imported libraries | 1,000,000 |
| Variables per scope | 1,000 |
| Compilation request size | 5 MB (includes unused code) |
| Collection elements (array, matrix) | 100,000 |
| Map key-value pairs | 50,000 |

- Unused variables/functions/types are excluded from compiled token count
- Identical functions are deduplicated by compiler (only one version compiled)

### Historical Buffers

- History-referencing operator `[]` limited to **5,000 bars** for most series
- Built-in OHLCV and `time` series support up to **10,000 bars**
- To declare explicit buffer size: `max_bars_back(myVariable, 500)`
- Also configurable via `max_bars_back` parameter in `indicator()` or `strategy()`
- Excessive implicit buffer calculations cause re-execution → use `max_bars_back()` proactively

### Drawing Position Limits

- Past position via `xloc.bar_index`: **10,000 bars** in the past
- Future position via `xloc.bar_index`: **500 bars** in the future
- Use `maxval = 500` in `input.int()` for user-controlled forward bars

### Historical Bar Counts by Plan

| Plan | Max chart bars |
|---|---|
| Ultimate | 40,000 |
| Expert | 25,000 |
| Premium | 20,000 |
| Essential / Plus | 10,000 |
| Other (free) | 5,000 |

### Backtest Trade Orders

- Maximum **9,000 orders** in backtesting (oldest trimmed when exceeded)
- Use `strategy.closedtrades.first_index` to find index of earliest untrimmed trade
- Deep Backtesting: **1,000,000 orders**

---

## 3. Profiling and Optimization

### Pine Profiler

- Available in Pine Editor via "More" → "Profiler mode" switch
- Shows per-line runtime % bars and tooltips with: line number, runtime %, total time, execution count
- Overhead added by Profiler increases script runtime — results are **estimates**
- Profiler is per-run; run multiple times (change a dummy input) to average variance
- If Profiler causes script to exceed runtime limit: use `calc_bars_count` to limit historical data

**Reading results:**
- **Single-line**: bar/% = fraction of total runtime on that line
- **Code block**: bar/% = total runtime in the block header line
- **UDFs**: each call site shows separately; more calls → more total executions × runtime
- **request.*() functions**: profiled including all bars in requested context
- **Unused/redundant code**: NOT shown (compiler removes it; no results at all)

### Optimization Techniques

**1. Prefer built-ins over loops:**
```pine
// Slow — manual loop:
highest(source, length) =>
    float result = na
    for i = 0 to length - 1
        result := math.max(result, source[i])
    result

// Fast — built-in:
ta.highest(close, 20)
```

**2. Reduce repetition (store results before using multiple times):**
```pine
// Slow — same expensive call repeated 10+ times:
count = switch
    data.valuesAbove(99) <= 10 => ...
    data.valuesAbove(99) <= 20 => ...

// Fast — compute once, branch on result:
count = data.valuesAbove(99)
color plotColor = switch
    count <= 10 => ...
    count <= 20 => ...
```

**3. Minimize `request.*()` calls — use tuples:**
```pine
// 9 separate calls — slow:
float r1 = request.security(sym, tf, ta.percentrank(close, 10))
float r2 = request.security(sym, tf, ta.percentrank(close, 20))
// ... 7 more

// 1 call with tuple — faster:
[r1, r2, r3, ...] = request.security(sym, tf, [
    ta.percentrank(close, 10),
    ta.percentrank(close, 20),
    ...])
```

**4. Avoid redrawing (use setters instead of delete + new):**
```pine
// Slow — delete and recreate box every bar:
box.delete(myBox)
myBox := box.new(...)

// Fast — update properties of existing box:
box.set_lefttop(myBox, x1, y)
box.set_rightbottom(myBox, x2, 0.0)
```

**5. Reduce drawing updates (gate to `barstate.islast` when applicable):**
```pine
// Slow — update table cells on every bar:
for i = 0 to 19
    table.cell_set_text(...)   // runs on every historical bar

// Fast — update only on last bar (users see same result):
if barstate.islast
    for i = 0 to 19
        table.cell_set_text(...)
```

**6. Store calculated values (avoid loop recalculation):**
```pine
// Slow — loop recalculates expensive result every bar:
for i = 1 to length
    result += expensiveFunction()

// Fast — compute once, use var to persist:
var float cached = na
if someCondition
    cached := expensiveFunction()
```

**7. Eliminate loops (use math relationships):**
```pine
// Loop version:
avgDiff(source, length) =>
    float sum = 0.0
    for i = 1 to length
        sum += source - source[i]
    sum / length

// Loop-free equivalent:
fast_avgDiff(source, length) =>
    (source * length - math.sum(source, length)[1]) / length
```

**8. Loop-invariant code motion (hoist unchanging calcs out of loop):**
```pine
// Slow — array.min() recalculated on every iteration:
for item in dataArray
    result.push((item - array.min(dataArray)) / array.range(dataArray))

// Fast — compute min/range once before the loop:
float minValue   = array.min(dataArray)
float rangeValue = array.range(dataArray)
for item in dataArray
    result.push((item - minValue) / rangeValue)
```

**9. Specify historical buffers explicitly:**
```pine
float source = close - ta.sma(close, 20)
max_bars_back(source, 500)    // declare buffer; prevents re-execution
```

---

## 4. Publishing Rules

### Privacy Types

| Type | Visibility | Editable after publish? |
|---|---|---|
| Public | Discoverable globally in Community Scripts | 15 minutes only |
| Private | URL only, not in Community feed | Always |

### Visibility Types

| Type | Code access | Who can use it? |
|---|---|---|
| Open | Source visible to all | Anyone |
| Protected | Code hidden | Anyone (paid plans only as author) |
| Invite-only | Code hidden | Invited users only (Premium+ author plans) |

- Visibility type is **permanent** — cannot be changed after publishing
- Open-source scripts are eligible for Editors' Picks
- All open-source scripts default to Mozilla Public License 2.0
- Invite-only is the **only** type authors can charge for; selling private scripts is prohibited

### Publication Checklist

**Source code:**
- Original and unique — no rehashing of existing scripts
- Verified correct with Pine Logs and test runs
- No `request.security(expr, lookahead_on)` without `[1]` offset (future leak = prohibited)
- Profiled — no unnecessary loops or excessive `request.*()` calls
- Input `minval`/`maxval`/`options` set where relevant
- `runtime.error()` added for unintended use cases
- Identifiers named clearly; inputs/plots have meaningful titles
- Compiler annotations (`///@function`, `///@param`, `///@returns`) on exported library functions

**Chart:**
- Script must be active and visible on the chart
- No unnecessary other scripts, drawings, or images on the chart
- Default settings used
- Symbol, timeframe, and script name visible in status line
- Price series visible
- Do NOT use non-standard charts (Heikin Ashi, Renko, Kagi, etc.) for strategies or signal scripts

**Strategy report:**
- Realistic `initial_capital` (not exaggerated)
- Realistic commission and slippage settings
- Sustainable position sizing (not >10% per trade typically)
- At least 100 trades for valid statistical inference
- No Strategy Tester warnings

**Description:**
- English first; other languages can follow
- Self-contained — explains purpose, how it works, how to use it, why it's original
- No unsubstantiated claims (e.g., "90% win rate")
- No social media links or advertising
- Code blocks, formatting, and TradingView markup tags used appropriately

**Updates:**
- Release notes should explain what changed and why
- Release notes are **immediately finalized** — use private drafts to validate first

### Private Draft Workflow (recommended)

1. Publish as **Private** first
2. Verify widget, script page, chart, description
3. Fix any issues by publishing updates to the private version
4. Copy the verified description text
5. Create new **Public** publication with updated code + verified description

---

## 5. Final Review Checklist

- Script declaration type matches intent (`indicator` / `strategy` / `library`)
- Version annotation `///@version=6` is present
- `alertcondition()` calls are at global scope (not inside `if`)
- `request.security()` HTF calls use non-repainting pattern (`[1]` + `lookahead_on`)
- Plot count is below 64
- Drawing counts within `max_*_count` limits declared in `indicator()`/`strategy()`
- `request.*()` calls are below 40 (64 for Ultimate)
- Any tuple from `request.*()` is below 127 elements
- Code follows `camelCase` / `SNAKE_CASE` naming conventions
- No future-leak `lookahead_on` without `[1]` offset
- Script tested on both historical and realtime bars for repainting



