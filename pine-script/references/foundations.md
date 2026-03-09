# Foundations

Use this file for the baseline rules that determine whether Pine code is structurally valid and runtime-correct.

## TOC
1. [What Pine Is](#what-pine-is)
2. [Script Structure](#script-structure)
3. [Identifiers](#identifiers)
4. [Operators](#operators)
5. [Variable Declarations](#variable-declarations)
6. [Conditional Structures](#conditional-structures)
7. [Loops](#loops)
8. [Execution Model and Time Series](#execution-model-and-time-series)
9. [Baseline Scaffolds](#baseline-scaffolds)

---

## What Pine Is

Pine Script is TradingView's cloud-based programming language for creating custom technical indicators, strategies, and libraries. All scripts run on TradingView servers; 150,000+ community scripts exist.

**Script types:**
- **Indicator** – studies and overlays; faster, no backtesting broker emulator
- **Strategy** – drives the broker emulator and Strategy Tester for backtesting; heavier resource use
- **Library** – reusable code; must export at least one function, method, UDT, or enum

**Resource limits** (cloud-based): data access limits, execution time budgets, memory caps, script-size limits.

---

## Script Structure

General shape of every Pine script:

```
<version>
<declaration_statement>
<code>
```

### Version annotation

```pine
//@version=6
```

- Required to specify Pine version (1–6). Always use 6.
- Syntactically allowed anywhere, but place it at the very top.

### Declaration statement

Each script must have **exactly one** declaration call:

| Type | Function | Minimum requirement |
|---|---|---|
| Indicator | `indicator()` | At least one output call (`plot()`, `plotshape()`, `barcolor()`, `line.new()`, `alert()`, `log.info()`, etc.) |
| Strategy | `strategy()` | At least one order-placement command or output function |
| Library | `library()` | At least one `export` of a function, method, UDT, or enum |

Key parameters for `indicator()`:
- `title` (required) – name shown on chart
- `overlay = true` – draw on main chart pane; `false` draws in a separate pane
- `max_labels_count`, `max_lines_count`, `max_boxes_count`, `max_polylines_count` – drawing object limits
- `scale` – pane scale (price, percent, index)

Key parameters for `strategy()`:
- `title`, `overlay`, `initial_capital`, `currency`, `commission_value`, `commission_type`, `slippage`
- `calc_on_every_tick = false` (default) – execute only on bar close on realtime bars
- `calc_on_order_fills = false` – execute after order fills

### Code

Valid statements:
- Variable declarations and reassignments
- Function / method definitions
- Built-in and user-defined function calls
- `if`, `for`, `while`, `switch`, `type`, `enum` structures

Rules:
- Global scope: lines must start at column 0 (no leading whitespace)
- Local blocks: indent exactly 4 spaces or 1 tab relative to the parent block
- Multiple one-liner statements can be joined with commas on one line
- Long lines can be wrapped; wrapped continuations inside `()` may use any indentation; outside `()` avoid multiples of 4

### Comments

```pine
// Single-line comment
a = close  // inline comment
```

Keyboard shortcut in Pine Editor: `Ctrl + /` to toggle comment on selected lines.

### Compiler annotations

Special instructions embedded as comments:

| Annotation | Purpose |
|---|---|
| `//@version=6` | Specify Pine version |
| `//@description` | Custom description for a `library()` |
| `//@function` | Document a user-defined function |
| `//@param` | Document a function parameter |
| `//@returns` | Document a function's return value |
| `//@type` | Document a UDT |
| `//@enum` | Document an enum type |
| `//@field` | Document a UDT field or enum field |
| `//@variable` | Document a variable (hover popup in editor) |
| `//@strategy_alert_message` | Default message text for strategy alerts |
| `//#region` / `//#endregion` | Create collapsible code regions in the editor |

---

## Identifiers

Rules:
- Must begin with `A-Z`, `a-z`, or `_`
- Subsequent characters: letters, `_`, digits `0-9`
- Case-sensitive: `myVar` ≠ `MyVar`
- `3barsDown` is invalid (starts with digit)

Style guide conventions (Pine Style Guide):
- **UPPER_SNAKE_CASE** for constants: `GREEN_COLOR = #4CAF50`, `MAX_LOOKBACK = 100`
- **camelCase** for all other identifiers: `fastLength`, `emaValue`, `isUptrend`

Examples:
```pine
myVar         // valid
_myVar        // valid
my123Var      // valid
MAX_LEN       // valid (constant)
3barsDown     // INVALID
```

Special: `_` as a single-underscore identifier marks a variable as unused; it can be declared multiple times in the same scope and cannot be read afterward. Used to discard unwanted tuple values.

---

## Operators

### Arithmetic

| Op | Meaning |
|---|---|
| `+` | Addition; also string concatenation |
| `-` | Subtraction; unary negation |
| `*` | Multiplication |
| `/` | Division (always returns float if operands differ; `5/2 = 2.5`) |
| `%` | Modulo (floor-based: `a - b * floor(a/b)`) |

If any operand is `na`, result is `na`. If any operand is `float`, result is `float`. Use `int()`, `math.round()`, `math.floor()`, or `math.ceil()` to get integer division results.

### Comparison

| Op | Meaning |
|---|---|
| `<` | Less than |
| `<=` | Less than or equal |
| `>` | Greater than |
| `>=` | Greater than or equal |
| `==` | Equal (works on any fundamental type including color, string) |
| `!=` | Not equal |

Comparison expressions return `bool`. `==` and `!=` work on all fundamental types; the ordering operators only work on numbers.

### Logical

| Op | Meaning |
|---|---|
| `not` | Unary negation |
| `and` | Logical AND (both must be true) |
| `or` | Logical OR (at least one true) |

### Ternary operator `?:`

```pine
condition ? valueIfTrue : valueIfFalse
```

Can be chained left-to-right. Does **not** create a local scope (unlike `if`).

```pine
timeframe.isintraday ? color.red :
  timeframe.isdaily   ? color.green :
  timeframe.ismonthly ? color.blue : na
```

### History-referencing operator `[]`

Access a series value N bars back from the current bar:

```pine
close[0]    // current bar (same as close)
close[1]    // previous bar's close
close[N]    // N bars ago
volume[2]   // two bars ago volume
ta.sma(close, 10)[1]  // SMA from previous bar
```

- Returns `na` when the offset reaches beyond the first bar of the dataset
- `close[1][2]` is **not** allowed — apply `[]` only once per expression
- Use `na()` or `nz()` to handle potential `na` returns

### Operator precedence (high to low)

| Level | Operators |
|---|---|
| 9 | `[]` |
| 8 | unary `+`, unary `-`, `not` |
| 7 | `*`, `/`, `%` |
| 6 | `+`, `-` |
| 5 | `>`, `<`, `>=`, `<=` |
| 4 | `==`, `!=` |
| 3 | `and` |
| 2 | `or` |
| 1 | `?:` |

Operators at the same level evaluate left to right. Use `()` to override.

### Assignment operator `=`

Declares a new variable and gives it its initial value. Used **only** at declaration time.

```pine
i = 1
showPlot = input.bool(true, "Show plots")
plotColor = color.green
```

### Reassignment operator `:=`

Assigns a new value to an already-declared variable.

```pine
var float pHi = na
pHi := nz(ta.pivothigh(5, 5), pHi)
```

### Compound assignment operators

Shorthand for `var := var op expression`:

| Op | Meaning |
|---|---|
| `+=` | Addition (also string concatenation) |
| `-=` | Subtraction |
| `*=` | Multiplication |
| `/=` | Division |
| `%=` | Modulo |

- `+=` and `-=` also work with `plot_display` values (e.g., `display.all` constants)
- `+=` works on strings for concatenation

### Qualifier propagation

Expressions inherit the **strongest** qualifier from their operands:
- `const` < `input` < `simple` < `series`
- `"input int" * "series int"` → `"series int"`
- If a `ta.*` function needs `"simple int"` length and gets `"series int"`, it's a compile error. Use `ta.sma()` instead of `ta.ema()` when the length is `"series"`.

---

## Variable Declarations

### Single-variable syntax

```
[export] [var | varip] [[qualifier] <type>] <identifier> = <expression> | <structure>
```

- `export`: library only; makes the constant available to importing scripts (requires `const` qualifier)
- `var` / `varip`: persistence modes (see Declaration Modes)
- qualifier: `const`, `simple`, or `series`
- type: `int`, `float`, `bool`, `color`, `string`, `line`, `linefill`, `box`, `polyline`, `label`, `table`, `chart.point`, `array<T>`, `matrix<T>`, `map<K,V>`, enum name, or UDT name
- Type keywords are optional when they can be inferred; required when initializing with `na`, when including a qualifier keyword, or when exporting from a library

```pine
oc2    = (open + close) / 2           // series float (inferred)
const float MULT = 2.5                // const float
float ratio = na                      // float (required: na initializer)
var label timeLabel = label.new(...)  // persistent label reference
```

### Tuple declarations

Declare multiple variables at once from a function returning a tuple:

```pine
[bbMiddle, bbUpper, bbLower] = ta.bb(close, 5, 4)
[macd, sig, hist] = ta.macd(close, 12, 26, 9)
[_, visibleHigh, visibleLow, _, _] = visChart.ohlcv()  // _ discards values
```

- Tuple declarations do not support `var`, `varip`, or type keywords; each variable inherits the type of its assigned value
- All variables created by tuple declarations use the **default** declaration mode

### Qualified types

**Type keywords** set the data type explicitly:
- Built-in: `int`, `float`, `bool`, `color`, `string`, `line`, `box`, `label`, `table`, `linefill`, `polyline`, `chart.point`, `plot`, `hline`
- Collection: `array<int>`, `matrix<float>`, `map<string, color>`
- User types: enum names and UDT names

**Qualifier keywords** set the value's availability and mutability:
- `const` – compile-time constant; prevents reassignment; weakest qualifier
- `simple` – available on the first bar, consistent across all bars; cannot be reassigned with series values
- `series` – changes each bar; strongest qualifier; implicit when omitted with dynamic data

No keyword for `"input"` — it is inherited automatically when the variable's value comes from `input.*()` calls.

### Variable reassignment

```pine
myVar := 10          // reassignment operator
sample += math.random()   // compound: sample = sample + math.random()
```

- Must declare a variable before reassigning it
- `const` variables cannot be reassigned
- Cannot reassign global variables from inside user-defined functions or methods
- Reassigning can strengthen the qualifier (e.g., assigning a `series` value to a `const`-initialized variable makes it `series`)

### Declaration modes

**Default (no keyword):** Variable is re-initialized on every execution of its scope. Its prior values are still accessible via `[]` because Pine saves series history, but the variable itself resets.

```pine
int count = 0
count += 1   // always 1, because count resets to 0 on each bar
```

**`var`:** Variable is initialized **once** (on the closing tick of the first bar it reaches), then persists across bars. Changes on intrabar ticks are rolled back by Pine before the next tick.

```pine
var int count = 0
count += 1   // accumulates: 1, 2, 3… across bars
```

```pine
var array<float> myArray = array.new<float>()
if bar_index % 5 == 0
    array.push(myArray, close)  // array grows, reference persists
```

**`varip`:** Like `var` but persists across every tick including intrabar realtime ticks; NOT rolled back. "ip" = "intrabar persist".

```pine
varip float highLevel = na     // holds value even between real-time ticks
```

Compatible types for `varip`:
- Fundamental types (`int`, `float`, `bool`, `color`, `string`)
- Enum members
- `chart.point`, `footprint`, `volume_row` IDs
- UDT object IDs
- Collections of the above types

**Important:** In strategies (which execute once per bar by default), `varip` behaves identically to `var`. It only differs from `var` on indicators (or strategies with `calc_on_every_tick = true`) because those execute on every realtime tick.

### Scopes

- **Global scope**: any line not inside a structure's indented block; accessible throughout the script
- **Local scope**: code inside a function, conditional structure, or loop body; only accessible within that block
- A variable declared in a local scope is not visible to outer scopes
- Variables in outer scopes are accessible to nested inner scopes
- Same-scope variables must have unique names (except `_`)
- **Shadowing**: if a nested scope declares a variable with the same name as an outer-scope variable, the outer variable becomes inaccessible in that nested scope. The compiler warns. Avoid by using `:=` instead of `=` when intending to reassign.

---

## Conditional Structures

### `if` — side effects only

```pine
if <expression>
    <local_block>
{else if <expression>
    <local_block>}
[else
    <local_block>]
```

Execute a block when condition is true, with optional `else if` and `else` branches. When no block executes and the structure is not assigned, `na` is returned.

```pine
if ta.crossover(source, lower)
    strategy.entry("BBandLE", strategy.long, stop = lower, oca_name = "BollingerBands",
                   oca_type = strategy.oca.cancel, comment = "BBandLE")
else
    strategy.cancel(id = "BBandLE")
```

### `if` — returning a value

```pine
[<declaration_mode>] [<type>] <identifier> = if <expression>
    <local_block>
{else if <expression>
    <local_block>}
[else
    <local_block>]
```

Returns the last expression value of the executed block. If no block executes, returns `na` (or `false` for `bool` branches).

```pine
string barState = if barstate.islastconfirmedhistory
    "islastconfirmedhistory"
else if barstate.isnew
    "isnew"
else if barstate.isrealtime
    "isrealtime"
else
    "other"
```

Nested `if` is allowed but prefer compound conditions with `and` for performance:

```pine
// Preferred:
if condition1 and condition2 and condition3
    expression

// Avoid deeply nesting:
if condition1
    if condition2
        if condition3
            expression
```

### `switch` — with key expression

```pine
[[<declaration_mode>] [<type>] <identifier> = ]switch <expression>
    {<expression> => <local_block>}
    => <local_block>   // default fallback
```

Only one matching block executes (no fall-through). Default `=>` block acts as catch-all.

```pine
float ma = switch maType
    "EMA" => ta.ema(close, maLength)
    "SMA" => ta.sma(close, maLength)
    "RMA" => ta.rma(close, maLength)
    "WMA" => ta.wma(close, maLength)
    =>
        runtime.error("No matching MA type found.")
        float(na)
```

### `switch` — without key expression

```pine
switch
    {<expression> => <local_block>}
    => <local_block>
```

Each branch evaluates its own expression; the first `true` branch executes.

```pine
switch
    longCondition  => strategy.entry("Long ID", strategy.long)
    shortCondition => strategy.entry("Short ID", strategy.short)
```

**Critical:** Evaluate `ta.*` calls **before** entering a `switch` structure. Calling them inside `switch` branches means they don't execute on every bar, causing incorrect historical buffers and a compiler warning:

```pine
// INCORRECT — ta.crossover only executes on one branch per bar:
switch
    ta.crossover(ta.sma(close, 14), ta.sma(close, 28)) => strategy.entry("Long ID", strategy.long)
    ta.crossunder(ta.sma(close, 14), ta.sma(close, 28)) => strategy.entry("Short ID", strategy.short)

// CORRECT — evaluate first, then switch:
bool longCondition  = ta.crossover( ta.sma(close, 14), ta.sma(close, 28))
bool shortCondition = ta.crossunder(ta.sma(close, 14), ta.sma(close, 28))
switch
    longCondition  => strategy.entry("Long ID", strategy.long)
    shortCondition => strategy.entry("Short ID", strategy.short)
```

### Matching local block type requirement

When assigning a conditional structure to a variable, **all** local blocks must return the same type:

```pine
x = if close > open
    close    // float ✓
else
    open     // float ✓ — same type

// ERROR: type mismatch
x = if close > open
    close    // float
else
    "open"   // string — different type
```

### Functions banned inside conditional local blocks

These built-ins cannot be called inside `if`/`switch`/loop local blocks:

`barcolor()`, `bgcolor()`, `plot()`, `plotshape()`, `plotchar()`, `plotarrow()`, `plotcandle()`, `plotbar()`, `hline()`, `fill()`, `alertcondition()`, `indicator()`, `strategy()`, `library()`

**Pattern:** Compute conditional values first; pass them as arguments to the globally-scoped function call:

```pine
// Compute condition and color
color plotColor = close > open ? color.green : color.red

// Call plot() in global scope — never inside if/switch/for
plot(close, "Close", plotColor)
```

`input.*()` calls are allowed in local blocks but behave identically to global-scope calls (they are always evaluated).

---

## Loops

### When loops are NOT needed

Pine's bar-by-bar execution effectively loops over all bars. Use built-ins instead:

```pine
// Avoid — manually summing with a loop:
float closeSum = 0
for i = 0 to lengthInput - 1
    closeSum += close[i]
float avgClose = closeSum / lengthInput

// Preferred — built-in equivalent:
float avgClose = ta.sma(close, lengthInput)
```

### When loops ARE needed

- Iterating through or manipulating collections (arrays, matrices, maps)
- Performing logic that references current-bar info while looking back (since that current-bar value wasn't available on past bars)
- Custom calculations with no built-in equivalent

### Loop syntax (all types)

```
[variables = | :=] loop_header
    statements | continue | break
    return_expression
```

- `continue` — skip remaining statements in current iteration, go to next
- `break` — exit the loop entirely
- `return_expression` — the last expression in the body; its result can be assigned to a variable after the loop
- If a `var` or `varip` variable is initialized from a loop's result (`var x = for ...`), the loop executes only one iteration. To assign to a `var` variable while allowing full loop execution, declare it before the loop and use `:=`

### `for` loop

```pine
[variables = | :=] for counter = from_num to to_num [by step_num]
    statements | continue | break
    return_expression
```

- Counter is auto-managed; do not manually increment it
- Counts up when `to_num > from_num`, down when `to_num < from_num`; `step_num` must be positive
- `to_num` is re-evaluated each iteration — can create dynamic stopping conditions
- Counter variable is local to the loop's scope

```pine
// Basic counting (0 to 10)
for i = 0 to 10
    label.new(bar_index + i, 0, str.tostring(i), textcolor = color.white)

// Downward counting
for i = lookbackInput to 1
    float diff = vwmaOpen[i] - vwmaOpen
    label.new(bar_index - i, open[i], str.tostring(diff, "0.00"))

// Use _ to discard unused counter
for _ = 1 to 20
    sample += math.random()
```

### `while` loop

```pine
[variables = | :=] while condition
    statements | continue | break
    return_expression
```

- Condition evaluated before each iteration; exits when `false`
- Must manually manage any counter variable (`j += 1`)
- Use when iteration count is unknown in advance

```pine
int j = 0
while j <= 10
    label.new(bar_index + j, 0, str.tostring(j))
    j += 1  // must manually increment; otherwise infinite loop → runtime error
```

### `for...in` loop

Two forms:

```pine
// Form 1: access items only
for item in collection_id
    ...

// Form 2: access index + item (required for maps)
for [index, item] in collection_id
```

Behaviors by collection type:
- **array** → element-wise iteration
- **matrix** → row-wise iteration (each `item` is a row array)
- **map** → pair-wise iteration (Form 2 required; `index` = key, `item` = value)

Maps cannot change size while being directly iterated with `for...in`. To modify map size during iteration, iterate over `map.keys()` array, use a copy, or switch to `for`/`while`.

```pine
// Array iteration
for price in intrabarPrices
    if price > close
        strength -= 1
    else if price < close
        strength += 1

// Array with index
for [index, element] in stringArray
    if index == 2
        continue
    labelText += str.tostring(index + 1) + ": " + element + "\n"

// Matrix row iteration
for rowArray in myMatrix
    float rowAvg = rowArray.avg()

// Map iteration
for [key, value] in simpleMap
    displayText += key + ": " + str.tostring(value, "#.##") + "\n"
```

### Scope rules for loops

- All variables declared inside a loop body (including the counter) belong to the loop's **local scope**
- Global variables are accessible and modifiable within a loop
- Local loop variables are not accessible outside their loop
- Nested loops have separate local scopes; outer-loop variables are visible to inner loops

---

## Execution Model and Time Series

### Bar-by-bar execution

Pine runs sequentially on each bar from the oldest (left) to newest (right). On each bar, the script re-evaluates all expressions in global scope.

- **Historical bars**: all closed bars at script load time; each executes once
- **Realtime bar**: the currently open bar; indicators re-execute on every new incoming tick; the script then rolls back all `var`/non-`varip` data to the previous bar's close state before the next tick

### Rollback

Between realtime ticks, Pine resets (rolls back) all values for variables without `varip`. Only data from the closing tick persists into subsequent bars. This prevents half-executed states from corrupting history.

### `var` vs `varip` on realtime bars

| Feature | `var` | `varip` |
|---|---|---|
| Initializes on | First closing tick | First execution (any tick) |
| Persists | Between bar closes | Between every tick |
| Rolled back on realtime ticks? | YES | NO |
| Strategies (default) | Once per bar | Same as `var` |

### Time series and the `[]` operator

Every variable is a time series. `close` = series of all close prices; `close[1]` = last bar's close; `close[0]` = current bar's close.

- `bar_index` starts at 0 for the first bar and increments
- Referencing beyond the beginning returns `na`
- Historical buffers are auto-sized (up to 5000 bars by default)
- Call `max_bars_back(source, N)` at the global level to manually extend a buffer beyond auto-detected size

### Global scope vs local scope time series

**Critical rule**: Always call `ta.*` functions and other functions that accumulate historical state in **global scope**, not inside `if`, `switch`, ternary branches, or loops.

```pine
// WRONG — ta.rsi() runs only when condition is true → incomplete historical buffer
myRsi = if condition
    ta.rsi(close, 14)   // compiler warning + wrong results

// CORRECT — call in global scope, use result conditionally
myRsi = ta.rsi(close, 14)
myFilteredRsi = condition ? myRsi : na
```

Rationale: local scopes may execute 0, 1, or many times per bar. Functions that depend on consistent execution every bar (such as all `ta.*`, `request.*`, etc.) produce incorrect results when skipped on any bar.

### `barstate.*` variables

| Variable | True when |
|---|---|
| `barstate.ishistory` | Executing on a historical bar |
| `barstate.isrealtime` | Executing on the open (realtime) bar |
| `barstate.isconfirmed` | Executing on the closing tick of a bar |
| `barstate.isnew` | First execution on a new bar |
| `barstate.islast` | Currently on the last bar of the dataset |
| `barstate.islastconfirmedhistory` | Last confirmed historical bar |

### Events that trigger execution

- Adding the script to a chart
- Saving the script in the editor
- Changing an input value
- Changing the chart's symbol or timeframe
- Chart data refresh or new tick arrival
- Opening Pine Logs panel
- Opening Pine Profiler

Each unique combination of inputs, symbol, timeframe, Pine Logs enabled, and Profiler enabled creates a separate cached execution.

### Strategy calculation modes

By default, strategies recalculate only on bar close on realtime bars. Change with:
- `calc_on_every_tick = true` — recalculate on every incoming tick (like an indicator)
- `calc_on_order_fills = true` — recalculate immediately after an order fills

---

## Baseline Scaffolds

### Indicator

```pine
//@version=6
indicator("My Indicator", overlay = true)

// Inputs
int lengthInput = input.int(20, "Length", minval = 1)

// Calculation
float smaValue = ta.sma(close, lengthInput)

// Outputs
plot(smaValue, "SMA", color.blue, 2)
```

### Strategy

```pine
//@version=6
strategy("My Strategy", overlay = true, initial_capital = 10000,
         commission_value = 0.1, commission_type = strategy.commission.percent)

// Inputs
int fastInput = input.int(14, "Fast Length", minval = 1)
int slowInput = input.int(28, "Slow Length", minval = 2)

// Signal calculation (in global scope)
bool longCondition  = ta.crossover( ta.sma(close, fastInput), ta.sma(close, slowInput))
bool shortCondition = ta.crossunder(ta.sma(close, fastInput), ta.sma(close, slowInput))

// Order execution
if longCondition
    strategy.entry("Long", strategy.long)
if shortCondition
    strategy.entry("Short", strategy.short)
```

### Library

```pine
//@version=6
library("MyLib", overlay = false)

//@function Returns the midpoint between high and low.
//@param src (float) Source series.
//@returns (float) Midpoint value.
export midpoint(float src_high, float src_low) =>
    (src_high + src_low) / 2.0
```

### MACD using built-ins

```pine
//@version=6
indicator("MACD", overlay = false)

int fastInput   = input.int(12, "Fast")
int slowInput   = input.int(26, "Slow")
int signalInput = input.int(9,  "Signal")

[macdLine, signalLine, histLine] = ta.macd(close, fastInput, slowInput, signalInput)

plot(macdLine,   "MACD",       color.blue)
plot(signalLine, "Signal",     color.orange)
plot(histLine,   "Histogram",  color.gray, style = plot.style_columns)
```

### Confirmed breakout with `var` for state tracking

```pine
//@version=6
indicator("Breakout", overlay = true)

int lookbackInput = input.int(20, "Lookback", minval = 1)

// Calculate in global scope
float highestPrev = ta.highest(high, lookbackInput)[1]
bool breakout = close > highestPrev

// Track consecutive breakout bars
var int streakCount = 0
streakCount := breakout ? streakCount + 1 : 0

plotshape(breakout, "Breakout", shape.triangleup, location.abovebar, color.green)
bgcolor(streakCount >= 3 ? color.new(color.green, 85) : na, title = "Streak BG")
```
