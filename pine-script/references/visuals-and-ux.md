# Visuals and UX

Reference for everything a user sees or configures directly on the chart: inputs, plots, fills, colors, bar visuals, backgrounds, levels, lines/boxes/polylines, tables, text, and shapes.

## Contents
1. [Inputs](#1-inputs)
2. [Plots](#2-plots-plot)
3. [Fills](#3-fills)
4. [Colors](#4-colors)
5. [Backgrounds](#5-backgrounds-bgcolor)
6. [Bar Coloring](#6-bar-coloring-barcolor)
7. [Bar Plotting](#7-bar-plotting)
8. [Levels](#8-levels-hline)
9. [Lines and Boxes](#9-lines-and-boxes)
10. [Tables](#10-tables)
11. [Text and Shapes](#11-text-and-shapes)
12. [Text Formatting (Labels, Boxes, Tables)](#12-text-formatting-labels-boxes-tables)
13. [Visual Output Selection Guide](#13-visual-output-selection-guide)
14. [Scaffold Examples](#14-scaffold-examples)

---

## 1. Inputs

### Input Functions

Pine has 14 input functions:

| Function | Return type | Widget |
|---|---|---|
| `input(defval)` | int/float/bool/color/string or `series float` | Depends on defval type |
| `input.int()` | `input int` | Number field or dropdown |
| `input.float()` | `input float` | Number field or dropdown |
| `input.bool()` | `input bool` | Checkbox |
| `input.color()` | `input color` | Color picker |
| `input.string()` | `input string` | Text field or dropdown |
| `input.text_area()` | `input string` | Multi-line text field |
| `input.timeframe()` | `input string` | Timeframe dropdown |
| `input.symbol()` | `input string` | Symbol search |
| `input.source()` | `series float` | Source dropdown |
| `input.session()` | `input string` | Session picker |
| `input.time()` | `input int` | Date + time fields + chart marker |
| `input.price()` | `input float` | Float field + horizontal chart marker |
| `input.enum()` | enum member | Dropdown of enum field titles |

**All `input.*()` calls return `input`-qualified values** except `input.source()`, which returns `series float`.

Recommended location: top of script, before all other code (per Style guide).

### Common Parameters (all input functions)

| Parameter | Type required | Purpose |
|---|---|---|
| `defval` | `const *` (usually) | Default value shown to user |
| `title` | `const string` | Label in Inputs tab |
| `tooltip` | `const string` | `i` icon hover text in Inputs tab |
| `inline` | `const string` | Groups inputs on same line by matching string |
| `group` | `const string` | Creates collapsible section heading |
| `display` | `const int` | Where value appears: `display.all`, `display.status_line`, `display.data_window`, `display.none` |
| `active` | `input bool` | If `false`, input is dimmed and non-editable; can depend on another input |

**`active`** accepts `input bool` — so one input can control whether another is enabled:
```pine
showMA = input.bool(true, "Show MA")
maLength = input.int(14, "MA Length", active = showMA)
```

### Parameters for Numeric Inputs

- `minval` / `maxval` — restrict allowed range
- `step` — increment for value scrolling
- `options` — provides fixed list as dropdown (tuple format: `[opt1, opt2, ...]`); cannot combine with `minval`/`maxval`
- `confirm` — if `true`, prompts user to set value when script is first added to chart

### Function-Specific Notes

**`input()` (generic)**
- Auto-detects type from `defval`: int → `input int`, float → `input float`, bool → `input bool`, color → `input color`, string → `input string`, price series → `series float`

**`input.int()` / `input.float()`**
- Two signatures: with `options` (dropdown) or with `minval`/`maxval`/`step` (numeric field)

**`input.color()`**
- Creates color picker in Inputs tab
- Required when dynamic colors are used (makes Style tab color pickers disappear)

**`input.string()`**
- With `options` → dropdown; without → free text
- Backslash `\` treated as literal character; no escape sequences

**`input.text_area()`**
- Multi-line free text; `\` literal; line terminators and tabs auto-parsed
- Returns `input string`

**`input.timeframe()`**
- Dropdown of chart timeframe + common timeframes
- Add custom options via `options` parameter
- Returns timeframe string compatible with `request.*()` calls

**`input.symbol()`**
- Mirrors chart symbol search
- Default `""` = current chart symbol

**`input.session()`**
- Session time range picker (pairs well with a `days` string input)

**`input.time()`**
- Returns UNIX timestamp in milliseconds
- Adds vertical marker on chart
- Pairing with `input.price()` on same `inline` value creates draggable point marker:
```pine
float p1 = input.price(0, "Price 1", inline = "1", confirm = true)
int   t1 = input.time (0, "Time 1",  inline = "1", confirm = true)
```
- Multiple pairs (each unique `inline`) → multiple point markers

**`input.price()`**
- Like `input.float()` but adds horizontal line marker on chart

**`input.enum()`**
- Creates dropdown whose items are the titles of all members of the specified enum type
- `input.enum(EnumName.fieldName, "Title")` → returns the matching enum member
- Requires enum to be declared with `export` if used in a library

**`indicator()`/`strategy()` parameters that add Inputs tab entries:** `timeframe`, `timeframe_gaps`, `calc_bars_count`

---

## 2. Plots (`plot()`)

### Full Signature
```
plot(series, title, color, linewidth, style, trackprice, histbase, offset,
     join, editable, show_last, display, format, precision, force_overlay, linestyle) → plot
```

Returns a `plot` ID usable in `fill()`.

### Key Parameters

**`series`** — the only mandatory parameter; must be `series int/float`; `bool` must be cast: `boolVar ? 1 : 0`

**`title`** — `const string`; appears in: Data Window, status line, Settings/Style tab, `input.source()` dropdowns, alert Condition field, CSV export headers

**`color`** — `series color`; plotting `na` or any color with transparency 100 hides the plot without affecting the scale

**`linewidth`** — pixels for line styles; relative size unit for circles/crosses; no effect on columns

**`style`** — controls visual appearance:

| Style constant | Description |
|---|---|
| `plot.style_line` | Continuous line (default); bridges over `na` values |
| `plot.style_linebr` | Discontinuous line; does NOT bridge `na` gaps |
| `plot.style_stepline` | Staircase effect with vertical transitions at bar midpoints |
| `plot.style_stepline_diamond` | Like stepline with diamond markers |
| `plot.style_area` | Line + fill to `histbase`; color used for both; bridges `na` |
| `plot.style_areabr` | Like area but no bridge over `na`; scale uses only visible values |
| `plot.style_columns` | Volume-style columns; `linewidth` has no effect |
| `plot.style_histogram` | Columns where `linewidth` controls column width (pixels); must be `input int` |
| `plot.style_circles` | Unjoined circles; relative sizing via `linewidth` |
| `plot.style_cross` | Unjoined crosses; relative sizing via `linewidth` |

**`linestyle`** — for line-based styles only: `plot.linestyle_solid`, `plot.linestyle_dashed`, `plot.linestyle_dotted`

**`histbase`** — reference level for area/columns/histogram; requires `input int/float` (static)

**`offset`** — shifts the plot left (negative) or right (positive) in bars; must be `simple` (cannot change at runtime)

**`join`** — `circles`/`cross` only: connects shapes with 1px line when `true`

**`editable`** — `bool`; controls if plot appears in Settings/Style tab for color editing

**`show_last`** — `input int`; limits how many bars back the plot is visible

**`display`** — combination of `display.*` constants using `+` or `-`:
- `display.all` — default; show everywhere
- `display.none` — calculations still run; useful for alert placeholders: `{{plot("RSI")}}`
- `display.all - display.pane` — hide visual but show in Data Window/status

**`format`** — `format.price`, `format.percent`, or `format.volume`

**`precision`** — 0 to 16 digits after decimal

**`force_overlay`** — if `true`, always displays on main chart pane even if script is in separate pane

### Plot Count Limit

- Maximum **64 plots** per script
- `plot()` with `const color` = **1 plot**
- `plot()` with `simple`, `input`, or `series color` = **2 plots**
- `alertcondition()` calls also count toward the total
- `plotchar()`, `plotshape()`, `plotarrow()`, `plotcandle()`, `plotbar()` also count

### Conditional Plotting

`plot()` **cannot** be called inside `if` blocks. Control output via:
- Value: pass `na` to suppress: `plot(condition ? close : na, ...)`
- Color: pass `na` as color to hide: `plot(close, color = condition ? color.red : na)`

### Other `plot*` Functions
```
plotchar(series, title, char, location, color, ...) → void
plotshape(series, title, style, location, color, ...) → void
plotarrow(series, title, colorup, colordown, ...) → void
plotcandle(open, high, low, close, title, color, wickcolor, ...) → void
plotbar(open, high, low, close, title, color, ...) → void
```

---

## 3. Fills

### `fill()` — Between Plots or HLines
```
fill(plot1, plot2, color, title, editable, show_last, fillgaps) → void
fill(hline1, hline2, color, title, editable, fillgaps) → void
```

- Accepts IDs returned by `plot()` or `hline()` calls
- **Cannot mix** `plot` and `hline` IDs in the same call
- `color` accepts `series color` — can change per bar
- To fill between a constant level and a fluctuating series, use `plot(0, ...)` instead of `hline(0)` to get a `plot` ID

### `linefill` — Between Two Line Objects
```
linefill.new(line1, line2, color) → series linefill
linefill.set_color(id, color) → void
linefill.get_line1(id) → series line
linefill.get_line2(id) → series line
```

- Fills the region between two `line` drawing objects
- One linefill per pair; new call to `linefill.new()` with same lines replaces existing
- Linefills automatically follow the lines they reference — no need to update
- Only `z`-order: fills have higher z-index than plots and lines

### Box and Polyline Built-in Fills

- **Box**: `bgcolor` parameter in `box.new()` — fills interior of the box
- **Polyline**: `fill_color` parameter in `polyline.new()` — fills closed shape interior
  - Requires `closed = true` for fill to be visible

---

## 4. Colors

### 17 Built-in Color Constants

`color.aqua`, `color.black`, `color.blue`, `color.fuchsia`, `color.gray`, `color.green`, `color.lime`, `color.maroon`, `color.navy`, `color.olive`, `color.orange`, `color.purple`, `color.red`, `color.silver`, `color.teal`, `color.white`, `color.yellow`

### Transparency Scale

Pine uses 0–100: **0 = fully opaque, 100 = fully transparent**  
Hex color format `#RRGGBBaa`: `aa` is alpha where **00 = transparent, FF = opaque** (reversed from Pine scale)

### Color Functions

| Function | Purpose |
|---|---|
| `color.new(color, transparency)` | Modify transparency of existing color |
| `color.rgb(r, g, b, transparency)` | Build color from RGBA components (r/g/b: 0–255) |
| `color.from_gradient(value, bottom_value, top_value, bottom_color, top_color)` | Linear gradient; clamped at boundaries |
| `color.r(color)` | Extract red component |
| `color.g(color)` | Extract green component |
| `color.b(color)` | Extract blue component |
| `color.t(color)` | Extract transparency component |

### Color Picker Availability in Settings/Style Tab

Auto color pickers appear in Settings/Style IF all calculated colors are `const color`:
- `const color` → Colors determined at compile time → pickers available
- `simple color` or `series color` → No pickers in Style tab

**To keep pickers while adding transparency**, wrap each base color separately:
```pine
// GOOD — each color.new() call returns const color
plotColor = close > open ? color.new(color.teal, 50) : color.new(color.red, 50)

// BAD — color.new() receives a series condition → series color → no pickers
plotColor = color.new(close > open ? color.teal : color.red, 50)
```

### `color.from_gradient()` Details

- Value clamped at `bottom_value` / `top_value` boundaries (color plateaus)
- Interpolation is linear across all RGBA components
- `na` can be used as `bottom_color` or `top_color` to fade in/out
- Common pattern for unbounded series: use fixed extremes like -200/200 for CCI

---

## 5. Backgrounds (`bgcolor()`)

```
bgcolor(color, offset, editable, show_last, title, force_overlay) → void
```

- `color` accepts `series color` — dynamic is fine
- On `overlay = true` scripts: colors the **chart** background
- On pane scripts: colors the **pane** background
- `force_overlay = true` forces background onto main chart even from a pane script

---

## 6. Bar Coloring (`barcolor()`)

```
barcolor(color, offset, editable, show_last, title, display) → void
```

- Colors bars on the **main chart** regardless of whether script is in pane or overlay
- `color` accepts `series color` — conditional coloring is the primary use case
- `na` → leaves bar color unchanged
- Does NOT affect the script pane background

---

## 7. Bar Plotting

### `plotcandle()`
```
plotcandle(open, high, low, close, title, color, wickcolor, editable, show_last, bordercolor, display) → void
```

### `plotbar()`
```
plotbar(open, high, low, close, title, color, editable, show_last, display, force_overlay) → void
```

**Key rules:**
- If any of open/high/low/close is `na`, no bar/candle is drawn
- `color` and `wickcolor` accept `series color` — conditional coloring works
- `plotbar()` has no `bordercolor` or `wickcolor` — conventional bars have no wick
- Can use custom OHLC values (smoothed, HTF, computed) instead of chart values
- Fetch HTF OHLC via tuple: `[o, h, l, c] = request.security(syminfo.tickerid, "D", [open, high, low, close], gaps = barmerge.gaps_on)`
- Use `behind_chart = false` or "Visual Order/Bring to Front" to overlay on chart candles

---

## 8. Levels (`hline()`)

```
hline(price, title, color, linestyle, linewidth, editable, display) → hline
```

Returns an `hline` ID usable in `fill()`.

**Constraints vs `plot()`:**
- `price` requires `input int/float` — **no dynamic series**
- `color` requires `input color` — **no series colors**

**Line styles:**

| Constant | Description |
|---|---|
| `hline.style_solid` | Solid line (default) |
| `hline.style_dotted` | Dotted line |
| `hline.style_dashed` | Dashed line |

**Fill between hlines:**
```pine
h1 = hline(100, "Upper", color.lime)
h2 = hline(0, "Zero", color.gray)
fill(h1, h2, color.new(color.lime, 90))
```

---

## 9. Lines and Boxes

### chart.point

Required for overloaded constructors of line, box, and label:

| Constructor | x-coordinate source | Fields set |
|---|---|---|
| `chart.point.now(price)` | Current bar time AND index | `.time`, `.index`, `.price` |
| `chart.point.from_index(index, price)` | bar index only (no time) | `.index`, `.price` |
| `chart.point.from_time(time, price)` | bar time only (no index) | `.time`, `.price` |
| `chart.point.new(time, index, price)` | Explicit all fields | `.time`, `.index`, `.price` |

When `xloc = xloc.bar_index` → uses `.index` field; when `xloc = xloc.bar_time` → uses `.time` field.

### Lines

```pine
// Overload 1: chart.point parameters
line.new(pt1, pt2, xloc, extend, color, style, width, force_overlay) → series line

// Overload 2: explicit coordinates
line.new(x1, y1, x2, y2, xloc, extend, color, style, width, force_overlay) → series line
```

**Key parameters:**
- `xloc` — `xloc.bar_index` (default) or `xloc.bar_time`
- `extend` — `extend.none` (default), `extend.left`, `extend.right`, `extend.both`
- Min x with `xloc.bar_index`: `bar_index - 10000`; use `xloc.bar_time` for larger offsets
- Max future x: `bar_index + 500`

**Line styles:**

| Constant | Appearance |
|---|---|
| `line.style_solid` | Solid |
| `line.style_dotted` | Dotted |
| `line.style_dashed` | Dashed |
| `line.style_arrow_left` | Arrow at start |
| `line.style_arrow_right` | Arrow at end |
| `line.style_arrow_both` | Arrows at both ends |

**Setter functions:** `line.set_xy1()`, `line.set_xy2()`, `line.set_x1()`, `line.set_x2()`, `line.set_y1()`, `line.set_y2()`, `line.set_first_point()`, `line.set_second_point()`, `line.set_color()`, `line.set_style()`, `line.set_width()`, `line.set_extend()`, `line.set_xloc()`

**Getter functions:** `line.get_x1()`, `line.get_x2()`, `line.get_y1()`, `line.get_y2()`, `line.get_price(id, x)` (extended price at arbitrary x)

**Management:** `line.copy()`, `line.delete()`, `line.all` (built-in array of all visible line IDs)

**Limit:** `max_lines_count` in `indicator()` (default ~50, max 500); garbage collection removes oldest.

### Boxes

```pine
// Overload 1: chart.point parameters
box.new(top_left, bottom_right, border_color, border_width, border_style, extend, xloc,
        bgcolor, text, text_size, text_color, text_halign, text_valign, text_wrap,
        text_font_family, text_formatting, force_overlay) → series box

// Overload 2: explicit coordinates
box.new(left, top, right, bottom, border_color, border_width, border_style, extend, xloc,
        bgcolor, ...) → series box
```

**Border styles:** `box.style_solid`, `box.style_dotted`, `box.style_dashed`

**Text alignment constants:**
- Horizontal: `text.align_left`, `text.align_center`, `text.align_right`
- Vertical: `text.align_top`, `text.align_center`, `text.align_bottom`

**Setter functions:** `box.set_top()`, `box.set_bottom()`, `box.set_left()`, `box.set_right()`, `box.set_top_left_point()`, `box.set_bottom_right_point()`, `box.set_border_color()`, `box.set_border_width()`, `box.set_border_style()`, `box.set_extend()`, `box.set_bgcolor()`, `box.set_text()`, `box.set_text_size()`, `box.set_text_color()`, `box.set_text_halign()`, `box.set_text_valign()`, `box.set_text_wrap()`, `box.set_text_font_family()`, `box.set_text_formatting()`

**Getter functions:** `box.get_top()`, `box.get_bottom()`, `box.get_left()`, `box.get_right()`

**Management:** `box.copy()`, `box.delete()`, `box.all`; `max_boxes_count` (default ~50, max 500)

### Polylines

```pine
polyline.new(points, curved, closed, xloc, line_color, fill_color, line_style, line_width,
             force_overlay) → series polyline
```

- `points` — `array<chart.point>`; order determines drawing sequence
- `curved = true` → smooth curve; `curved = false` → straight segments (default)
- `closed = true` → closes shape to first point; enables `fill_color`
- `fill_color` only visible when `closed = true`
- **NO setter functions** — to modify, call `polyline.delete()` then `polyline.new()` with new points
- `polyline.delete()` — deletes instance; `polyline.all` — built-in array of visible polylines
- `max_polylines_count` in `indicator()` (default ~50, max 100)
- Shares line styles from `line.style_*` namespace

---

## 10. Tables

### Creating Tables
```pine
table.new(position, columns, rows, bgcolor, frame_color, frame_width, border_color, border_width) → series table
```

**Position constants** (`position.*`):

| Row | Left | Center | Right |
|---|---|---|---|
| Top | `position.top_left` | `position.top_center` | `position.top_right` |
| Middle | `position.middle_left` | `position.middle_center` | `position.middle_right` |
| Bottom | `position.bottom_left` | `position.bottom_center` | `position.bottom_right` |

### Populating Cells
```pine
table.cell(id, column, row, text, width, height, text_color, text_halign, text_valign,
           text_size, text_font_family, text_formatting, bgcolor) → void
```

- Column and row indices start at **0**
- `width`/`height` = 0 → auto-size from content (default)
- Non-zero `width`/`height` → percentage of indicator's visual space
- **Each `table.cell()` call overwrites ALL cell properties** — use `table.cell_set_*()` to modify individual properties after population

### Table and Cell Setter Functions

**Table setters:** `table.set_position()`, `table.set_bgcolor()`, `table.set_frame_color()`, `table.set_frame_width()`, `table.set_border_color()`, `table.set_border_width()`

**Cell setters:** `table.cell_set_text()`, `table.cell_set_width()`, `table.cell_set_height()`, `table.cell_set_text_color()`, `table.cell_set_text_halign()`, `table.cell_set_text_valign()`, `table.cell_set_text_size()`, `table.cell_set_text_font_family()`, `table.cell_set_text_formatting()`, `table.cell_set_bgcolor()`, `table.cell_set_tooltip()`

**Management:** `table.delete()`, `table.clear()`

### Table Usage Rules

1. **Always use `var`** to declare the table — prevents reinitializing on every bar
2. **Enclose cell population inside `if barstate.islast`** — table always shows last state
3. Functions that must run every bar (like `ta.sma()`) must be called OUTSIDE the `if barstate.islast` block
4. In strategies with `calc_on_every_tick = false`, tables in `if barstate.islast` blocks don't update on real-time ticks
5. Tables float in visual space — not anchored to bars; do not move when scrolling

```pine
// Correct pattern
var table t = table.new(position.top_right, 2, 3, bgcolor = color.gray)
float myVal = ta.atr(14)             // runs every bar
if barstate.islast
    table.cell(t, 0, 0, "ATR", text_color = color.white)
    table.cell(t, 1, 0, str.tostring(myVal, format.mintick), text_color = color.white)
```

---

## 11. Text and Shapes

### Comparison of Text Methods

| Method | Dynamic text | Conditional | Max count | Anchored to bar |
|---|---|---|---|---|
| `plotchar()` | No (`const string`) | Via `series bool` arg | Unlimited | Yes |
| `plotshape()` | No (`const string`) | Via `series bool` arg | Unlimited | Yes |
| `plotarrow()` | No | Via series value | Unlimited | Yes |
| `label.new()` | Yes (`series string`) | Full `if` blocks | ~50/500 | Yes |
| `table.cell()` | Yes | Full `if` blocks | Varies | No (fixed) |

### `plotchar()`
```
plotchar(series, title, char, location, color, offset, text, textcolor, editable, size,
         show_last, display, format, precision, force_overlay) → void
```

- `series` — `series bool`; `true` = show, `false`/`na` = hide
- `char` — a single Unicode character (use `""` for data-window-only display)
- `text` — `const string`; non-dynamic, shows above/below the char
- **Location constants** (`location.*`): `abovebar`, `belowbar`, `top`, `bottom`, `absolute`, `absl`
- Use `location.top` to show value in Data Window without affecting scale: `plotchar(bar_index, "Bar Index", "", location.top)`
- **Size constants** (`size.*`): `auto`, `tiny`, `small`, `normal`, `large`, `huge`

### `plotshape()`
```
plotshape(series, title, style, location, color, offset, text, textcolor, editable, size,
          show_last, display, format, precision, force_overlay) → void
```

- `series` — `series bool`
- `text` — `const string`; use `\n` to position text above/below shape
  - Text going up (abovebar): end with `\n` to lift text above shape
  - Text going down (belowbar): start with `\n` to push text below shape
- `size` controls shape size, not text size
- Use `color = na` to show text only with invisible shape

**Shape styles (`shape.*`):**
`xcross`, `cross`, `circle`, `triangleup`, `triangledown`, `flag`, `arrowup`, `arrowdown`, `square`, `diamond`, `labelup`, `labeldown`

### `plotarrow()`
```
plotarrow(series, title, colorup, colordown, offset, minheight, maxheight, editable,
          show_last, display, format, precision, force_overlay) → void
```

- `series` — `series int/float` (not bool)
- `> 0` → up arrow (proportional magnitude); `< 0` → down arrow; `= 0` or `na` → no arrow
- `minheight`/`maxheight` — min/max arrow height in pixels

### Labels

```pine
// Overload 1: chart.point
label.new(point, text, xloc, yloc, color, style, textcolor, size, textalign, tooltip,
          text_font_family, force_overlay, text_formatting) → series label

// Overload 2: explicit coordinates
label.new(x, y, text, xloc, yloc, color, style, textcolor, size, textalign, tooltip,
          text_font_family, force_overlay, text_formatting) → series label
```

**Key parameters:**
- `text` — `series string`; dynamic values via `str.tostring()`; `+` for concatenation; `\n` for newlines
- `yloc` — `yloc.price` (default), `yloc.abovebar`, `yloc.belowbar`
- `xloc` — `xloc.bar_index` (default), `xloc.bar_time`
- `tooltip` — `series string`; shows on hover

**Label style constants (`label.style_*`):**

| Shape styles | Bubble/callout styles |
|---|---|
| `style_none` | `style_label_up` |
| `style_xcross` | `style_label_down` |
| `style_cross` | `style_label_left` |
| `style_circle` | `style_label_right` |
| `style_square` | `style_label_center` |
| `style_diamond` | `style_label_lower_left` |
| `style_triangleup` | `style_label_lower_right` |
| `style_triangledown` | `style_label_upper_left` |
| `style_flag` | `style_label_upper_right` |
| `style_arrowup` | |
| `style_arrowdown` | |

**x-offset range:** -10,000 bars into past, +500 bars into future (with `xloc.bar_index`)

**Count limit:** Default ~50; `max_labels_count` in `indicator()`/`strategy()` up to 500. When calling `label.new()` unconditionally on every bar (not inside `barstate.islast`), always declare `max_labels_count = 500` in the `indicator()` or `strategy()` call — without it, only the most recent ~50 labels are visible and all earlier ones are silently dropped.

```pine
//@version=6
indicator("Per-Bar Labels", overlay = true, max_labels_count = 500)

label.new(bar_index, high, str.tostring(close, format.mintick),
          yloc = yloc.abovebar, style = label.style_label_down,
          textcolor = color.white, size = size.small)
```

**Getter functions:** `label.get_x()`, `label.get_y()`, `label.get_text()`

**Setter functions:** `label.set_x()`, `label.set_y()`, `label.set_xy()`, `label.set_point()`, `label.set_text()`, `label.set_xloc()`, `label.set_yloc()`, `label.set_color()`, `label.set_style()`, `label.set_textcolor()`, `label.set_size()`, `label.set_textalign()`, `label.set_tooltip()`, `label.set_text_font_family()`, `label.set_text_formatting()`

**Management:** `label.copy()`, `label.delete()`, `label.all` (auto-maintained array of visible label IDs)

**Efficient pattern for last-bar label:**
```pine
// BAD: creates and deletes every bar
lbl = label.new(bar_index, high, str.tostring(high))
label.delete(lbl[1])

// GOOD: create once, update with setters
if barstate.islast
    var lbl = label.new(na, na)
    label.set_xy(lbl, bar_index, high)
    label.set_text(lbl, str.tostring(high, format.mintick))
```

---

## 12. Text Formatting (Labels, Boxes, Tables)

### Typographic Emphasis (`text_formatting` parameter)

| Constant | Effect |
|---|---|
| `text.format_none` | No special formatting (default) |
| `text.format_bold` | Bold text |
| `text.format_italic` | Italic text |
| `text.format_bold + text.format_italic` | Bold AND italic |

### Font Family (`text_font_family` parameter)

| Constant | Font |
|---|---|
| `font.family_default` | System default font |
| `font.family_monospace` | Monospace font |

### Size Constants vs Integer Sizes

| `size.*` constant | `int` equivalent (labels) | `int` equivalent (tables/boxes) |
|---|---|---|
| `size.auto` | `0` | `0` |
| `size.tiny` | `8` | ~`7` |
| `size.small` | `10` | ~`10` |
| `size.normal` | `14` | `12` |
| `size.large` | `20` | `18` |
| `size.huge` | `36` | `24` |

- `label.new()` uses `size` parameter
- `box.new()` and `table.cell()` use `text_size` parameter
- Both accept either string `size.*` constants or integer values

---

## 13. Visual Output Selection Guide

| Need | Best tool |
|---|---|
| Continuous numeric series | `plot()` |
| Fixed horizontal reference levels | `hline()` |
| Fill between two plots/levels | `fill()` |
| Gradient fills or dynamic level fills | Use two `plot()` calls + `fill()` |
| Fill between geometric lines | `linefill.new()` |
| Chart background | `bgcolor()` |
| Bar color | `barcolor()` |
| Custom OHLC bars | `plotcandle()` or `plotbar()` |
| Simple per-bar symbols | `plotchar()` or `plotshape()` |
| Proportional arrows | `plotarrow()` |
| Bar-anchored dynamic text with tooltip | `label.new()` |
| Fixed geometric shapes, trend lines | `line.new()`, `box.new()`, `polyline.new()` |
| Fixed-position dashboard/panel | `table.new()` + `table.cell()` |

---

## 14. Scaffold Examples

### Inputs + Plot + Bgcolor
```pine
//@version=6
indicator("RSI with zones", overlay = false)

lengthInput   = input.int(14, "RSI Length", minval = 1)
obInput       = input.float(70.0, "Overbought", minval = 50, maxval = 100)
osInput       = input.float(30.0, "Oversold",   minval = 0,  maxval = 50)
bullColorInput = input.color(color.lime,   "Bull", inline = "cols")
bearColorInput = input.color(color.red,    "Bear", inline = "cols")

rsi = ta.rsi(close, lengthInput)
rsiColor = rsi > obInput ? bullColorInput : rsi < osInput ? bearColorInput : color.gray

plot(rsi, "RSI", rsiColor, 2)
hline(obInput, "OB", color.red,  hline.style_dashed)
hline(osInput, "OS", color.lime, hline.style_dashed)
bgcolor(rsi > obInput ? color.new(color.red, 90) : rsi < osInput ? color.new(color.lime, 90) : na)
```

### Label + Table Dashboard
```pine
//@version=6
indicator("Dashboard", overlay = true)

// ATR for volatility display
atr14 = ta.atr(14)

// Table: always use var, populate only on last bar
var table dash = table.new(position.top_right, 2, 2, bgcolor = #1E222D, frame_color = color.gray, frame_width = 1)
if barstate.islast
    table.cell(dash, 0, 0, "ATR",  text_color = color.silver, bgcolor = #1E222D)
    table.cell(dash, 1, 0, str.tostring(atr14, format.mintick), text_color = color.white, bgcolor = #1E222D)
    table.cell(dash, 0, 1, "Bar",  text_color = color.silver, bgcolor = #1E222D)
    table.cell(dash, 1, 1, str.tostring(bar_index), text_color = color.white, bgcolor = #1E222D)

// Label: track highest high
var label hiLabel = label.new(na, na, "", style = label.style_label_down, color = color.orange)
var float runHigh = na
if high > nz(runHigh, high)
    runHigh := high
    label.set_xy(hiLabel, bar_index, high)
    label.set_text(hiLabel, "H: " + str.tostring(high, format.mintick))
```

### Lines + Linefill Channel
```pine
//@version=6
indicator("Linear Regression Channel", overlay = true)

lenInput = input.int(100, "Length", minval = 2)

var line basisLine = line.new(na, na, na, na, extend = extend.right, color = chart.fg_color, width = 2)
var line upperLine = line.new(na, na, na, na, extend = extend.right, color = color.teal, width = 1)
var line lowerLine = line.new(na, na, na, na, extend = extend.right, color = color.maroon, width = 1)
var linefill upperFill = linefill.new(basisLine, upperLine, color.new(color.teal, 85))
var linefill lowerFill = linefill.new(basisLine, lowerLine, color.new(color.maroon, 85))

// Update line coordinates each bar
basisLine.set_xy1(bar_index + 1 - lenInput, ta.linreg(close, lenInput, lenInput - 1))
basisLine.set_xy2(bar_index, ta.linreg(close, lenInput, 0))
float stdev = ta.stdev(close, lenInput)
upperLine.set_xy1(bar_index + 1 - lenInput, ta.linreg(close, lenInput, lenInput - 1) + stdev)
upperLine.set_xy2(bar_index, ta.linreg(close, lenInput, 0) + stdev)
lowerLine.set_xy1(bar_index + 1 - lenInput, ta.linreg(close, lenInput, lenInput - 1) - stdev)
lowerLine.set_xy2(bar_index, ta.linreg(close, lenInput, 0) - stdev)
// linefills auto-update — no action needed
```
