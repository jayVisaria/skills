# Language And Data

Covers Pine's type system and the advanced language features that support reusable, nontrivial scripts.

## Contents
1. [Type System](#1-type-system)
2. [Built-in Variables and Functions](#2-built-in-variables-and-functions)
3. [User-Defined Functions](#3-user-defined-functions)
4. [Objects and UDTs](#4-objects-and-udts)
5. [Methods](#5-methods)
6. [Arrays](#6-arrays)
7. [Matrices (Overview)](#7-matrices-overview)
8. [Maps](#8-maps)
9. [Enums](#9-enums)
10. [Libraries](#10-libraries)
11. [Data-Structure Selection Guide](#11-data-structure-selection-guide)
12. [Scaffold Examples](#12-scaffold-examples)

---

## 1. Type System

### 1.1 Qualifiers

Pine Script uses four qualifiers that form a strict hierarchy from strongest to weakest restriction:

| Qualifier | When available | Changes after first bar? |
|-----------|---------------|--------------------------|
| `const`   | Compile time  | Never — immutable        |
| `input`   | Input time (script load) | Never — triggers full reload |
| `simple`  | Before first bar executes | No                      |
| `series`  | Any bar execution | Yes, can vary per bar  |

**Rules:**
- A qualifier can be used where a weaker or equal qualifier is required, but never in a position requiring a stronger qualifier. E.g., a `const int` can be passed where `simple int` is expected; a `series int` cannot.
- Qualifier propagates: any expression mixing `series` values produces a `series` result.
- All built-in bar data variables (`open`, `high`, `low`, `close`, `volume`, `time`, `bar_index`) are always `series`.
- Most `ta.*` functions return `series` results.
- `input.*()` functions return `input` qualified values — EXCEPT `input.source()`, which returns `series float`.
- Library exported constants require the `const` qualifier.

### 1.2 Value Types vs. Reference Types

**Value types** (directly store the value; can have any qualifier):
- `int`, `float`, `bool`, `color`, `string`, enum types

**Reference types** (hold IDs/references to objects; ALWAYS `series` qualifier; arithmetic/logical operators do NOT apply):
- `plot`, `hline`
- Drawing types: `line`, `linefill`, `box`, `polyline`, `label`, `table`
- `chart.point`
- `footprint`, `volume_row`
- Collections: `array<T>`, `matrix<T>`, `map<K,V>`
- User-defined types (UDTs)

### 1.3 Value Type Details

**`int`**
- Integer (whole number) values.
- Built-ins: `bar_index` (0-based bar count), `time` (Unix ms), `timenow`, `dayofmonth`, `strategy.wintrades`, `strategy.losstrades`.

**`float`**
- Floating point (fractional) values.
- `int` auto-converts to `float` when needed.
- Built-ins: `close`, `open`, `high`, `low`, `hl2`, `hlc3`, `ohlc4`, `hlcc4`, `volume`, `ta.vwap`, `strategy.position_size`, `strategy.equity`.

**`bool`**
- `true` or `false` ONLY. A `bool` is NEVER `na` — when no data, returns `false` instead.
- All comparison operators (`==`, `!=`, `<`, `>`, `<=`, `>=`) and logical operators (`and`, `or`, `not`) return `bool`.
- Cannot auto-convert from `int` or `float`. Use `bool()` explicitly.

**`color`**
- Hex format: `#RRGGBBAA` where AA is alpha (00 = fully transparent, FF = fully opaque).
- Built-in constants: `color.green`, `color.red`, `color.blue`, `color.white`, `color.black`, `color.yellow`, `color.orange`, `color.purple`, `color.navy`, `color.maroon`, `color.gray`, `color.silver`, `chart.bg_color`, `chart.fg_color`.
- `color.rgb(r, g, b[, transp])` — r/g/b in 0-255, transp in 0-100 (0 = opaque, 100 = invisible).
- `color.new(color, transp)` — modifies transparency of an existing color.
- `color.from_gradient(value, bottom_val, top_val, bottom_color, top_color)` — interpolates between two colors.

**`string`**
- Enclosed in `"..."` or `'...'`.
- Concatenate with `+`.
- `str.*()` namespace: `str.format()`, `str.length()`, `str.tonumber()`, `str.tostring()`, `str.split()`, `str.contains()`, `str.replace()`, `str.trim()`, `str.lower()`, `str.upper()`, `str.startswith()`, `str.endswith()`.
- Built-ins: `syminfo.tickerid`, `syminfo.currency`, `timeframe.period`.

### 1.4 Reference Type Details

**`plot` and `hline`**
- `plot()` and `hline()` return usable IDs for `fill()`. All other plot functions (`plotshape()`, `plotchar()`, `plotarrow()`, `plotbar()`, `plotcandle()`) return `void`.
- Must be in global scope. Cannot vary which plot/hline they reference across bars.

**Drawing types: `line`, `linefill`, `box`, `polyline`, `label`, `table`**
- Each has a namespace with `.new()`, `.delete()`, `.copy()`, and `.set_*()` / `.get_*()` functions.
- `.new()` always creates a NEW object on every call (use `var` to persist across bars).
- All drawing limits apply (default: 50 lines/labels/boxes, etc.; increase with `max_lines_count` etc. in `indicator()`).

**`chart.point`**
- Struct with `time`, `index`, `price` fields.
- Create with: `chart.point.now(price)`, `chart.point.from_index(index, price)`, `chart.point.from_time(time, price)`, `chart.point.copy(id)`.

**`footprint` and `volume_row`**
- Used with `request.footprint()` results.
- Access via `footprint.*()` and `volume_row.*()` functions.

### 1.5 Collections

- `array<T>`, `matrix<T>`, `map<K,V>` — can store all value types, enum types, and specific reference types.
- Collections CANNOT directly store other collections as elements. Use a UDT wrapper with a collection field to nest collections.
- Maximum 100,000 elements per collection.

### 1.6 User-Defined Types (UDTs)

**Declaration:**
```pine
[export] type UDT_name
    [varip] [field_type] field_name [= default_value]
    [varip] [field_type] field_name [= default_value]
    ...
```

**Rules:**
- Default values must be literals or compatible built-in variables — NOT function calls.
- UDTs can reference themselves (recursive/linked-list types).
- CANNOT use fundamental type keywords (`int`, `float`, `string`, `bool`, `color`) as UDT names.
- UDT names CAN shadow built-in namespaces like `syminfo`, `ta`, `line`, etc. (but avoid this for clarity).
- `UDT.new()` and `UDT.copy()` are auto-generated for each UDT.
- `export type` exports the UDT from a library.

**Compiler annotations for UDTs:**
```pine
//@type <description>
//@field fieldName <description>
```

### 1.7 `void` and `na`

**`void`**: Returned by functions that produce side effects but no usable value (e.g., `array.push()`, `label.delete()`). Cannot be assigned or used in calculations.

**`na`**: Represents "no value." Key rules:
- `float myVar = na` — requires explicit type keyword when initializing with `na`.
- Test with `na(myVar)` — returns `bool`.
- `nz(value, replacement)` — returns `replacement` if value is `na`, otherwise returns `value`. Default replacement is 0.
- `fixnan(value)` — replaces `na` with the last non-`na` value.
- `bool` values are NEVER `na` — return `false` instead.

### 1.8 Type Casting

**Auto-conversion:** `int` → `float` only.

**Explicit casting functions:**
- `int(x)` — truncates to integer (does NOT round). Use `math.round()` first if rounding needed.
- `float(x)`, `bool(x)`, `color(x)`, `string(x)`.
- Reference type casts: `line(id)`, `label(id)`, `box(id)`, `table(id)`.

### 1.9 Tuples

- Functions can return multiple values: `=> [val1, val2, val3]`
- Destructure with: `[a, b, c] = myFunction()`
- Use `_` to discard unwanted items: `[_, second, _] = myFunction()`
- All tuple items inherit the SAME qualifier (the strongest one in the calculation).
- Tuple items CAN have different types.

---

## 2. Built-in Variables and Functions

### 2.1 Key Built-in Variables

**Price/Volume:**
- `open`, `high`, `low`, `close`, `hl2` (=(H+L)/2), `hlc3` (=(H+L+C)/3), `ohlc4` (=(O+H+L+C)/4), `hlcc4` (=(H+L+C+C)/4), `volume`

**Bar State:**
- `barstate.isfirst` — true on bar 0
- `barstate.islast` — true on last bar (may repaint in realtime)
- `barstate.ishistory` — true on all historical bars
- `barstate.isrealtime` — true on realtime bars
- `barstate.isconfirmed` — true when bar closes (confirmed)
- `barstate.isnew` — true on first execution for a bar
- `barstate.islastconfirmedhistory` — true on the bar before the current realtime bar

**Symbol Info (`syminfo.*`):**
- `syminfo.basecurrency`, `syminfo.currency`, `syminfo.description`, `syminfo.tickerid`, `syminfo.main_tickerid`, `syminfo.mintick`, `syminfo.pointvalue`, `syminfo.prefix`, `syminfo.type`, `syminfo.timezone`

**Timeframe (`timeframe.*`):**
- `timeframe.period` — string like `"D"`, `"60"`, `"W"`
- `timeframe.multiplier` — numeric multiplier
- `timeframe.isseconds`, `timeframe.isminutes`, `timeframe.isintraday`, `timeframe.isdaily`, `timeframe.isweekly`, `timeframe.ismonthly`, `timeframe.isdwm`

**Strategy (`strategy.*` variables):**
- `strategy.equity`, `strategy.initial_capital`, `strategy.grossloss`, `strategy.grossprofit`, `strategy.netprofit`
- `strategy.wintrades`, `strategy.losstrades`, `strategy.eventrades`
- `strategy.position_size`, `strategy.position_avg_price`
- `strategy.openprofit`, `strategy.max_drawdown`, `strategy.max_runup`

### 2.2 Key Built-in Namespaces

**`ta.*` — Technical Analysis:**
| Function/Variable | Description |
|-------------------|-------------|
| `ta.sma(source, length)` | Simple moving average |
| `ta.ema(source, length)` | Exponential moving average |
| `ta.rma(source, length)` | RMA (Wilder's smoothing) |
| `ta.wma(source, length)` | Weighted moving average |
| `ta.hma(source, length)` | Hull moving average |
| `ta.vwma(source, length)` | Volume-weighted moving average |
| `ta.rsi(source, length)` | RSI |
| `ta.macd(source, fast, slow, signal)` | Returns `[macd, signal, hist]` |
| `ta.bb(source, length, mult)` | Returns `[upper, basis, lower]` |
| `ta.supertrend(factor, atrPeriod)` | Returns `[supertrend, direction]` |
| `ta.stdev(source, length)` | Standard deviation |
| `ta.highest(source, length)` | Highest value in last n bars |
| `ta.lowest(source, length)` | Lowest value in last n bars |
| `ta.barssince(condition)` | Bars since condition was true |
| `ta.crossover(a, b)` | True when a crosses above b |
| `ta.crossunder(a, b)` | True when a crosses below b |
| `ta.pivothigh(leftLegs, rightLegs)` | Pivot high detection |
| `ta.pivotlow(leftLegs, rightLegs)` | Pivot low detection |
| `ta.valuewhen(condition, source, n)` | nth most recent value when condition |
| `ta.percentrank(source, length)` | Percentile rank |
| `ta.median(source, length)` | Median value |
| `ta.range(source, length)` | Range (max - min) |
| `ta.tr` | True range (variable) |
| `ta.tr(handle_na)` | True range — if `true`, uses `high-low` when `na` |
| `ta.vwap` | VWAP (variable) |

**`math.*` — Math:**
- `math.abs(x)`, `math.log(x)`, `math.log10(x)`, `math.exp(x)`, `math.sqrt(x)`, `math.pow(base, exp)`
- `math.max(a, b, ...)`, `math.min(a, b, ...)`
- `math.floor(x)`, `math.ceil(x)`, `math.round(x)`, `math.round(x, decimals)`
- `math.round_to_mintick(x)` — rounds to nearest tick using `syminfo.mintick`
- `math.random([min, max])` — pseudorandom float; use `math.random(0, 10)` for a range
- `math.sign(x)`, `math.sin(x)`, `math.cos(x)`, `math.asin(x)`, `math.acos(x)`, `math.atan(x)`
- `math.pi`, `math.phi`, `math.e`, `math.rphi`

**`str.*` — Strings:**
- `str.format(formatStr, ...)` — template formatting: `str.format("Price: {0,number,#.##}", close)`
- `str.tostring(value)` / `str.tostring(value, format)` — formats: `format.mintick`, `format.percent`, etc.
- `str.tonumber(string)` — converts string to float
- `str.length(string)` — character count
- `str.split(string, separator)` — returns `array<string>`
- `str.join(array, separator)` — joins array elements (equivalent to `array.join()`)
- `str.contains(source, str)`, `str.startswith(source, str)`, `str.endswith(source, str)`
- `str.replace(source, target, replacement[, occurrence])`, `str.replace_all(source, target, replacement)`
- `str.lower(string)`, `str.upper(string)`, `str.trim(string)`
- `str.match(string, regex)` — returns match or `na`
- `str.substring(source, begin[, end])`

**`input.*` — User Inputs:**
- `input(defVal, title, ...)` — generic input
- `input.int(defVal, title, minval, maxval, step, ...)` 
- `input.float(defVal, title, minval, maxval, step, ...)`
- `input.bool(defVal, title, ...)`
- `input.color(defVal, title, ...)`
- `input.string(defVal, title, options, ...)`
- `input.symbol(defVal, title, ...)` — symbol picker
- `input.timeframe(defVal, title, options, ...)`
- `input.session(defVal, title, options, ...)`
- `input.source(defVal, title, ...)` — returns `series float` (NOT `input`; exception to rule)
- `input.enum(defVal, title, ...)` — enum dropdown; returns the enum's member type
- `input.time(defVal, title, ...)`
- `input.text_area(defVal, title, ...)`

**`color.*` — Colors:**
- `color.rgb(r, g, b[, transp])` — r/g/b: 0-255, transp: 0-100
- `color.new(color, transp)` — change transparency only
- `color.from_gradient(value, bottom_val, top_val, bottom_color, top_color)` — gradient

**`request.*` — External Data:**
- `request.security(symbol, timeframe, expression, ...)` — request data from another context
- `request.security_lower_tf(symbol, timeframe, expression)` — returns array of intrabar values
- `request.dividends(ticker, field, ...)`, `request.earnings(ticker, field, ...)`, `request.splits(ticker, field, ...)`
- `request.financial(symbol, financial_id, period, ...)` — financial data
- `request.quandl(ticker, gaps, index)` — Quandl data
- `request.footprint(...)` — footprint/volume profile data

**`strategy.*` — Strategy Orders (global scope only):**
- `strategy.entry(id, direction, qty, ...)` — open a position
- `strategy.exit(id, from_entry, ...)` — exit a position
- `strategy.close(id, ...)` — close by entry id
- `strategy.cancel(id)` — cancel pending order
- `strategy.order(id, direction, qty, ...)` — flexible order
- `strategy.close_all(...)` — close all positions

### 2.3 Calling Built-ins

- **Positional:** `ta.ema(close, 20)`
- **Keyword:** `ta.ema(source = close, length = 20)`
- **Mixed:** positional first, then keyword after any skip — `indicator("Ex", "E", true, max_bars_back = 100)`
- A keyword argument cannot precede a positional argument.
- Some built-ins have both a variable form and a function form:
  - `ta.tr` (variable, uses `na` for the first bar) vs `ta.tr(true)` (function — uses `high - low` when previous `close` is `na`)
  - `time` (current bar open time) vs `time(timeframe, session, timezone)` (function form)
- Check the Reference Manual at https://www.tradingview.com/pine-script-reference/v6/ for required qualified type of each parameter.

---

## 3. User-Defined Functions

### 3.1 Syntax

**Single-line:**
```pine
functionName(param1, param2) => expression
```

**Multi-line:**
```pine
[export] [method] functionName([qualifier type] paramName [= defaultValue], ...) =>
    statement1
    statement2
    returnExpression  // last value is returned
```

### 3.2 Rules

- Definitions must be in **global scope** — no nested function definitions.
- Cannot modify global variables or parameters via `:=` or compound operators.
- CAN modify reference-type objects that global variables point to (via `.set_*()`, field reassignment, etc.) — side effects through references ARE allowed.
- Cannot call itself — **no recursion**. Use loops instead.
- Cannot call global-only functions in the body: `indicator()`, `strategy()`, `library()`, `plot()`, `hline()`, `fill()`, `plotshape()`, `plotchar()`, `plotarrow()`, `plotbar()`, `plotcandle()`, `barcolor()`, `bgcolor()`, `alertcondition()`.
- Each **written call** to a function has its own independent scope and history. Two written calls `f()` and `f()` at different places are completely independent scopes.
- Return type must be consistent across all executions of the same written call.
- Variables inside a function body are NOT visible outside it.

### 3.3 Parameter Type Declarations

```pine
functionName(paramName) =>                           // no keywords: inherits argument type per call
functionName(float paramName) =>                     // type keyword: restricts to float; qualifier inferred
functionName(simple float paramName) =>              // qualifier + type: enforces simple float
functionName(series float paramName) =>              // enforces series float
functionName(float paramName = na) =>                // default na: requires type keyword
```

**Rules:**
- Without type keywords: parameter accepts any type except `void`; type is inferred from the argument.
- With type keyword: restricts argument to that type; compiler infers qualifier (tries `series`, then `simple`).
- With qualifier keyword: enforces qualifier restriction; qualifier keywords only affect value types (reference types are always `series`).
- Type declaration is **required** when: parameter default is `na`, qualifier keyword is used, function is exported, or it's the first parameter of a method definition.

### 3.4 Function Overloading

- Multiple functions can share the same name if they differ in required parameter count OR in the type at the same parameter position.
- Compiler selects the right overload based on argument types.

### 3.5 Documentation Annotations

```pine
//@function  Calculates a simple moving average.
//@param source  The series to average.
//@param length  The number of bars to include.
//@returns  A series float representing the SMA.
mySma(float source, simple int length) =>
    math.sum(source, length) / length
```

These appear in the Pine Editor's autocomplete and hover popups.

---

## 4. Objects and UDTs

### 4.1 Declaring a UDT

```pine
type PivotPoint
    int barIdx
    float price
    bool isHigh = true    // default value; must be a literal or compatible built-in var
    string label = "Pivot"
```

### 4.2 Creating Instances

```pine
// Create with all defaults:
pt = PivotPoint.new()

// Positional arguments:
pt = PivotPoint.new(bar_index, high, true, "H")

// Keyword arguments:
pt = PivotPoint.new(barIdx = bar_index, price = high)

// Placeholder (requires type prefix when using na):
PivotPoint pt = na
```

### 4.3 Accessing and Modifying Fields

```pine
pt.barIdx        // read
pt.price := 100  // reassign with :=
```

### 4.4 `var` with Objects

Applying `var` to a UDT variable applies it to ALL fields automatically — the entire object persists across bars:

```pine
var PivotPoint lastHigh = PivotPoint.new()
```

### 4.5 `varip` with Object Fields

Applying `varip` to the object variable does NOT make fields intrabar-persistent. Must apply `varip` to each individual field inside the type declaration:

```pine
type Counter
    int bars = 0
    varip int ticks = 0   // only 'ticks' persists intrabar; 'bars' does not
```

### 4.6 Objects Are Reference Types

Assignment copies the reference, NOT the object:

```pine
pt2 = pt1           // both point to the SAME object; pt2.price := 99 also changes pt1.price
pt2 = PivotPoint.copy(pt1)   // shallow copy — independent value fields; nested reference fields still shared
```

**Deep copy** requires manually copying each reference-type field:

```pine
method deepCopy(PivotPoint this) =>
    PivotPoint.new(this.barIdx, this.price, this.isHigh, this.label)
```

### 4.7 Collections of Objects

```pine
var array<PivotPoint> pts = array.new<PivotPoint>()
array.push(pts, PivotPoint.new(bar_index, high))
```

### 4.8 UDT Shadowing Rules

- UDT names MAY shadow built-in namespaces (e.g., a UDT named `Line` shadows `line.*`).
- UDT names CANNOT be: `int`, `float`, `string`, `bool`, `color`.

---

## 5. Methods

### 5.1 Built-in Methods

Built-in methods are equivalent to their namespace function counterparts. All types in the `array`, `matrix`, `map`, `line`, `linefill`, `box`, `polyline`, `label`, `table`, `chart.point` namespaces support method syntax:

```pine
// These are equivalent:
array.get(myArr, 0)   ==   myArr.get(0)
array.push(myArr, v)  ==   myArr.push(v)
label.delete(lbl)     ==   lbl.delete()
```

### 5.2 User-Defined Methods

```pine
[export] method methodName(Type this, [qualifier type] param [= default], ...) =>
    body
```

- `method` keyword is required before the name.
- The **first parameter's type must be explicitly declared** — this determines which type the method is associated with.
- All other UDF rules apply.
- Call with dot notation: `myObj.methodName(otherArgs)`.

```pine
method normalize(array<float> this, simple int length) =>
    avg = array.avg(this)
    stdev = array.stdev(this)
    (array.get(this, length - 1) - avg) / stdev

score = myArray.normalize(20)
```

### 5.3 Method Chaining

When a method returns the same type it operates on, methods can be chained:

```pine
// maintainQueue returns array<float>, so calcBB can chain on it:
myArray.maintainQueue(newVal, true).calcBB(multiplier, true)
```

### 5.4 Method Overloading

- Can override built-in methods with the same name.
- Can define multiple overloads for different types under the same method name.
- Compiler selects based on the callee object's type.

---

## 6. Arrays

### 6.1 Declaration and Creation

```pine
// Declaration syntax:
[var/varip] [array<type>] identifier = expression

// Create empty array:
prices = array.new<float>(0)

// Create with size and initial value (all elements set to close):
prices = array.new<float>(2, close)

// Create from explicit values:
states = array.from(close > open, high != close)   // array<bool>

// Declare with na (type required):
array<float> prices = na
```

- Use `array.new<type>()` — works for all types including UDTs.
- Legacy `array.new_float()`, `array.new_int()`, etc. exist but are deprecated.
- `var` on an array variable: array persists across bars (grows with `array.push()`).
- `varip` on array variables: same as `var` but updates persist intrabar. For `varip`, array can store only fundamental types, `chart.point`, `footprint`, `volume_row`, or UDTs whose fields only contain those types.

### 6.2 Reading and Writing Elements

```pine
array.get(id, index)       // read element at index (0-based)
array.set(id, index, val)  // set element at index
id.get(index)              // method syntax
id.set(index, val)

// Negative indexing (from end):
id.get(-1)   // last element
id.get(-2)   // second-to-last
```

### 6.3 Size and Iteration

```pine
array.size(id)    // number of elements (also: id.size())

// for loop:
for i = 0 to array.size(myArr) - 1
    val = myArr.get(i)

// for...in loop (value iteration):
for price in myArr
    // price is each element value (copy of value for value types)

// for...in loop (index + value):
for [i, price] in myArr
    // i is index, price is value
```

### 6.4 Inserting Elements

```pine
array.push(id, val)        // append to end; increases size by 1
array.unshift(id, val)     // insert at beginning (index 0); shifts existing elements
array.insert(id, index, val)  // insert at specific index; shifts elements at or after index
```

### 6.5 Removing Elements

```pine
array.pop(id)              // removes and returns last element
array.shift(id)            // removes and returns first element
array.remove(id, index)    // removes and returns element at index
array.clear(id)            // removes ALL elements (does NOT delete referenced objects)
```

### 6.6 Stack and Queue Patterns

**Stack (LIFO):**
```pine
array.push(stack, val)    // push
val = array.pop(stack)    // pop
```

**Queue (FIFO — maintain fixed size):**
```pine
array.push(queue, newVal)
if array.size(queue) > maxSize
    array.shift(queue)    // dequeue oldest
```

### 6.7 Calculations on Arrays

Arrays have special aggregate functions (regular math functions don't work element-wise):

```pine
array.avg(id)         // mean
array.sum(id)         // sum
array.min(id)         // minimum value
array.max(id)         // maximum value
array.median(id)      // median
array.mode(id)        // mode
array.stdev(id)       // standard deviation
array.variance(id)    // variance
array.covariance(id1, id2)  // covariance
array.abs(id)         // absolute values (returns new array)
array.percentile_linear_interpolation(id, percentage)
array.percentile_nearest_rank(id, percentage)
```

### 6.8 Manipulation

```pine
array.sort(id)                     // ascending (default); modifies in place
array.sort(id, order.descending)   // descending; order.ascending or order.descending
array.sort_indices(id)             // returns sorted index array without modifying original
array.reverse(id)                  // reverses in place
array.concat(id1, id2)             // appends id2 to end of id1; returns id1
array.copy(id)                     // returns a new independent copy
array.slice(id, from, to)          // returns a shallow copy of the range [from, to)
array.join(id, separator)          // joins int/float/string elements into a string
```

### 6.9 Searching

```pine
array.includes(id, val)            // true if val found in array
array.indexof(id, val)             // index of first occurrence, or -1
array.lastindexof(id, val)         // index of last occurrence, or -1
array.binary_search(id, val)       // requires sorted ascending; returns index or -1
array.binary_search_leftmost(id, val)  // return leftmost position if not found
array.binary_search_rightmost(id, val) // return rightmost position if not found
```

### 6.10 History Referencing

Arrays support history referencing with `[]`:

```pine
a = array.new<float>(1)
array.set(a, 0, close)
prevArray = a[1]   // array assigned to 'a' on the previous bar
```

### 6.11 Scope

Scripts can modify globally-assigned arrays from within local scopes (functions, methods, conditionals). This is a key difference from value-type global variables.

### 6.12 Common Array Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Index xx out of bounds (size yy) | Index < 0 or >= size | Guard: `i = 0 to array.size(a) == 0 ? na : array.size(a) - 1` |
| Cannot call methods on na array | Array variable is `na` | Initialize: `a = array.new<float>(0)` |
| Array too large (max 100,000) | Exceeded limit | Limit array growth |
| Cannot use pop/shift if empty | Calling pop/shift on empty array | Check `array.size() > 0` first |

---

## 7. Matrices (Overview)

A matrix is a two-dimensional collection `matrix<T>`. Access and manipulation via `matrix.*()` functions. See https://www.tradingview.com/pine-script-docs/language/matrices/ for full details.

```pine
m = matrix.new<float>(rows, cols, initialValue)
matrix.get(m, row, col)
matrix.set(m, row, col, value)
matrix.rows(m), matrix.columns(m)
matrix.row(m, index)       // returns array<T>
matrix.col(m, index)       // returns array<T>
matrix.add_row(m, index, rowArray)
matrix.add_col(m, index, colArray)
matrix.remove_row(m, index)
matrix.remove_col(m, index)
matrix.copy(m)
matrix.concat(m1, m2)      // vertically concatenates
// Math operations: matrix.sum(), matrix.diff(), matrix.mult(), matrix.transpose(), matrix.inv(), matrix.det()
```

---

## 8. Maps

### 8.1 Declaration and Creation

Map keys must be value types (fundamental or enum). Keys CANNOT be reference types. Values CAN be any type, including UDTs.

```pine
// Syntax:
[var/varip] [map<keyType, valueType>] identifier = expression

// Create empty map:
myMap = map.new<string, float>()

// Declare with na (type required):
map<string, float> myMap = na

// With var (map persists across bars):
var colorMap = map.new<string, color>()
```

### 8.2 Reading and Writing

```pine
map.put(id, key, value)    // add or overwrite a key-value pair
map.get(id, key)           // returns value for key, or na if not found
map.contains(id, key)      // returns bool

// Method syntax:
id.put(key, value)
id.get(key)
id.contains(key)
```

- `map.put()` on an existing key **replaces** the value but **preserves its insertion order position**.
- Map maintains internal insertion order (though it is logically unordered).

### 8.3 Inspecting Keys and Values

```pine
map.keys(id)     // returns array<keyType> in insertion order
map.values(id)   // returns array<valueType> in insertion order
map.size(id)     // number of key-value pairs
```

### 8.4 Removing Pairs

```pine
map.remove(id, key)    // removes specific key; returns its value or na if not found
map.clear(id)          // removes all pairs
map.put_all(id1, id2)  // puts all pairs from id2 into id1 (overwrites duplicates, preserves order)
```

### 8.5 Iterating Over a Map

```pine
// Recommended — iterates in insertion order:
for [key, value] in myMap
    // process key and value

// Alternative:
for key in myMap.keys()
    value = myMap.get(key)
```

### 8.6 Copying Maps

```pine
mCopy = map.copy(id)   // shallow copy; changes to copy don't affect original at the map level, but shared reference values do
```

For maps with reference-type values, deep copy requires manually copying each referenced object.

### 8.7 Maps of Other Collections

Maps cannot directly store other collections as values. Use a UDT wrapper:

```pine
type Wrapper
    map<string, float> data

mapOfMaps = map.new<string, Wrapper>()
mapOfMaps.put("EUR", Wrapper.new(map.new<string, float>()))
```

### 8.8 Map Scope and History

Maps support history referencing (`myMap[1]`) and can be modified from local scopes (same as arrays).

---

## 9. Enums

### 9.1 Declaring an Enum

```pine
[export] enum EnumName
    field1 [= "Title 1"]   // optional string title
    field2 [= "Title 2"]
    field3                  // if no title, title = field name as string
```

**Rules:**
- Each field is a unique named member (value) of the enum type.
- Enum fields are `const` qualified.
- Use `//@enum` and `//@field` annotations to document.
- Enum names CANNOT match any built-in namespace (e.g., `ta`, `syminfo`, `polyline` are forbidden). Case matters — `Syminfo` is OK.

```pine
//@enum            An enumeration of signal states.
//@field buy       Represents a buy signal.
//@field sell      Represents a sell signal.
//@field neutral   Represents a neutral state.
enum Signal
    buy     = "Buy signal"
    sell    = "Sell signal"
    neutral                  // title = "neutral"
```

### 9.2 Using Enums

```pine
// Access member with dot notation:
mySignal = Signal.neutral

// Type required when initializing with na:
Signal mySignal = na

// Comparison (only == and != available):
if mySignal == Signal.buy
    ...
if mySignal != Signal.neutral
    ...

// In switch:
result = switch mySignal
    Signal.buy     => ta.rsi(close, 14)
    Signal.sell    => ta.rsi(close, 14) * -1
    =>               0.0
```

### 9.3 Enum Field Titles

```pine
// Get the title string of an enum member:
titleStr = str.tostring(mySignal)    // returns the title, e.g., "Buy signal"

// str.format() and log.*() cannot accept enum members directly.
// Convert to string first:
log.info("Signal: " + str.tostring(mySignal))
```

### 9.4 Enum Inputs

```pine
OscType oscInput = input.enum(OscType.rsi, "Oscillator")
// Shows a dropdown with all field titles in the Settings/Inputs tab.
```

### 9.5 Collecting Enum Members

Collections can store enum members:

```pine
array<Signal> signalArr = array.new<Signal>()
array.push(signalArr, Signal.buy)

// Enums are unique as map keys (unlike other non-fundamental types):
map<Signal, int> counters = map.new<Signal, int>()
counters.put(Signal.buy, 0)
counters.put(Signal.sell, 0)
```

- Each declared enum is a **unique type** — cannot mix members of different enums even if they have identical names.

---

## 10. Libraries

### 10.1 Library Declaration

```pine
//@version=6
// @description  Provides functions for range calculations.
library("MyLibrary", overlay = true)
```

- `library()` replaces `indicator()` or `strategy()` as the declaration statement.
- Library's global code can demonstrate usage.
- Must contain at least one exported function, method, UDT, or enum.

### 10.2 Exporting Functions

```pine
//@function      Calculates all-time high.
//@param val     The series to track.
//@returns       All-time high of val.
export hi(float val = high) =>
    var float ath = val
    ath := math.max(ath, val)
```

**Exported function requirements:**
- `export` keyword is mandatory.
- Parameter type keywords are mandatory (unlike non-exported functions).
- Can include `simple` or `series` qualifier keywords on parameters.
- CANNOT use variables from the library's global scope except those with `const` qualifier.
- CANNOT include `input.*()` calls.
- CAN include `request.*()` calls in local scope (if `dynamic_requests` is not `false` in `library()`), but `expression` arguments cannot depend on exported function parameters.
- Always return `simple` or `series` results — NEVER `const` or `input`. So their return values cannot be used where `const int` or `input` is required (e.g., `show_last` in `plot()`).

### 10.3 Qualified Type Control in Libraries

Compiler auto-determines parameter qualifiers based on how parameters are used internally:

```pine
// x must be "simple int" because ta.ema() requires "simple int" for length:
export myEma(int x) =>
    ta.ema(close, length = x)
// myLib.myEma(20) works; myLib.myEma(bar_index) fails (series int can't become simple)
```

Force `simple` results by using `simple` keyword on parameters:
```pine
export makeTickerId(simple string prefix, simple string ticker) =>
    prefix + ":" + ticker   // returns "simple string"
```

Note: Reference types always produce `series` results regardless of `simple` keyword.

### 10.4 Exporting UDTs and Enums

```pine
export type Point
    int x
    float y
    bool isHi
    bool wasBreached = false

export enum State
    long  = "Long"
    short = "Short"
    neutral = "Neutral"
```

A library MUST export a UDT if:
- Any exported function/method accepts or returns objects of that type.
- The fields of another exported UDT use that type.

A library MUST export an enum if:
- Any exported function/method accepts or returns the enum's members.
- A field of an exported UDT accepts values of that enum type.

### 10.5 Importing a Library

```pine
import username/LibraryName/version as alias
```

```pine
import PineCoders/AllTimeHighLow/1 as allTime

indicator("My Script", overlay = true)
plot(allTime.hi())
plot(allTime.lo())
plot(allTime.hi(close))  // use close as the series
```

- `<version>` must be specified explicitly — no "latest" auto-tracking.
- `as <alias>` is optional. When omitted, the library name becomes the namespace.
- Access exported functions/UDTs/enums with `alias.name` syntax.
- For imported UDTs, use `alias.TypeName` as the type keyword.

### 10.6 Library Publishing Rules

- Libraries are always open-source.
- Must be published before use.
- Public scripts can only use public libraries.
- Private/personal scripts can use public or private libraries.
- A library can use other libraries or previous versions of itself.

---

## 11. Data-Structure Selection Guide

| Scenario | Best Choice |
|----------|-------------|
| Return multiple values from a function | Tuple `[a, b, c]` |
| Ordered list, stack (LIFO), or queue (FIFO) | `array<T>` |
| Fixed set of named possible values | `enum` |
| Grid/matrix of values | `matrix<T>` |
| Structured record with named fields | UDT (object) |
| Key-based lookup (string→float, enum→int, etc.) | `map<K,V>` |
| Group of related data objects | `array<UDT>` or `map<key,UDT>` |
| Nested collections | UDT wrapper containing collection field |

---

## 12. Scaffold Examples

### UDT + Method + Array

```pine
//@version=6
indicator("UDT Demo", overlay=true)

type PivotPoint
    int   barIdx
    float price
    bool  isHigh

//@function  Creates a string representation of a PivotPoint.
method toString(PivotPoint this) =>
    (this.isHigh ? "H" : "L") + " @ " + str.tostring(this.price, format.mintick)

var array<PivotPoint> pivots = array.new<PivotPoint>()

ph = ta.pivothigh(3, 3)
pl = ta.pivotlow(3, 3)

if not na(ph)
    array.push(pivots, PivotPoint.new(bar_index[3], ph, true))
if not na(pl)
    array.push(pivots, PivotPoint.new(bar_index[3], pl, false))

// Keep last 10
while array.size(pivots) > 10
    array.shift(pivots)

if barstate.islast and array.size(pivots) > 0
    last = pivots.get(-1)
    label.new(last.barIdx, last.price, last.toString(), style=label.style_label_down)
```

### Enum + Map Counter

```pine
//@version=6
indicator("Enum Map Demo")

enum Trend
    up    = "Uptrend"
    down  = "Downtrend"
    flat  = "Flat"

var map<Trend, int> counts = map.new<Trend, int>()
if barstate.isfirst
    counts.put(Trend.up, 0)
    counts.put(Trend.down, 0)
    counts.put(Trend.flat, 0)

float emaVal = ta.ema(close, 20)
Trend state = switch
    close > emaVal * 1.001 => Trend.up
    close < emaVal * 0.999 => Trend.down
    =>                         Trend.flat

counts.put(state, counts.get(state) + 1)

plot(counts.get(Trend.up), "Up bars", color.green)
plot(counts.get(Trend.down), "Down bars", color.red)
plot(counts.get(Trend.flat), "Flat bars", color.gray)
```

### Library Pattern

```pine
//@version=6
// @description  Price range utilities.
library("PriceRangeUtils", overlay=false)

//@function      Returns the ATR as a percentage of close.
//@param length  ATR period.
//@returns       ATR / close as a float.
export atrPct(simple int length = 14) =>
    ta.atr(length) / close * 100
```

