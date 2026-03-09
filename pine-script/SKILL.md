---
name: pine-script
description: "Use this skill for any task involving TradingView Pine Script — writing, fixing, reviewing, or explaining Pine Editor code. Covers indicators, strategies, and libraries in Pine Script v6. Use for: creating technical analysis indicators, backtesting strategies, working with alerts, data requests, multi-timeframe analysis, custom visuals (plots, labels, tables, shapes), user-defined types, collections, repainting concerns, and publishing to TradingView. Also use for debugging Pine Script errors, converting between indicator and strategy types, migrating from older Pine versions, and any Pine-specific language questions."
---

# Pine Script

## Workflow

1. Classify the request as one of: indicator, strategy, library, explanation, review, refactor, migration, or publishing guidance.
2. Start from the correct scaffold: `//@version=6`, then exactly one declaration statement: `indicator()`, `strategy()`, or `library()`.
3. Model runtime behavior before writing logic. Check execution order, time series behavior, qualifiers, persistence (`var` or `varip`), and any history references.
4. Choose the simplest valid language features first. Prefer built-ins and series expressions before loops, objects, or collections — but if the user explicitly requests UDTs, methods, or collections, use them without pushback.
5. Add the request-specific layer:
   - Inputs and user controls.
   - Visuals such as plots, hlines, fills, lines, boxes, labels, or tables.
   - Alerts, `request.*()` calls, session logic, or strategy order commands.
   - Libraries with exported functions, methods, UDTs, enums, or constants.
6. Check repainting explicitly. If the script uses realtime values, higher-timeframe requests, intrabar data, or strategy logic, state whether the result is confirmed-only, realtime-responsive, or potentially repainting.
7. Finish with style, limits, optimization, and publication constraints.

## Reference Routing

- Open [references/foundations.md](references/foundations.md) for scaffolds, execution model, time series, operators, variables, conditionals, and loops.
- Open [references/language-and-data.md](references/language-and-data.md) for the type system, built-ins, functions, UDTs, objects, methods, collections, enums, libraries, and FAQ data-structure guidance.
- Open [references/visuals-and-ux.md](references/visuals-and-ux.md) for inputs, plots, hlines, fills, colors, bar coloring, bar plotting, labels, tables, time handling, and tooltip-related guidance.
- Open [references/data-requests-alerts-and-strategies.md](references/data-requests-alerts-and-strategies.md) for chart data, sessions, non-standard feeds, `request.*()`, repainting, alerts, and strategies.
- Open [references/quality.md](references/quality.md) for style, optimization, limitations, and publishing rules.

## Working Rules

- Ground all answers in the official TradingView manual captured in this skill's references. If requested behavior is not covered, say so rather than guessing.
- Default to Pine Script v6.
- Use imperative, readable code with clear input titles and stable naming.
- Prefer built-in namespaces such as `ta.`, `math.`, `str.`, `request.`, `syminfo.`, `timeframe.`, and `strategy.` over reimplementing standard behavior.
- Keep declaration-only calls in global scope.
- Do not place `plot()`, `plotshape()`, `plotchar()`, `plotarrow()`, `plotbar()`, `plotcandle()`, `hline()`, `fill()`, `alertcondition()`, `indicator()`, `strategy()`, or `library()` inside conditional local blocks.
- When initializing with `na`, add an explicit type when the type is otherwise unclear.
- Prefer indicator scripts over strategies unless the user explicitly needs simulated orders or Strategy Tester output.
- For libraries, expose only reusable exports and keep usage examples separate from the exported API. All exported function parameters must have explicit type declarations; use the `simple` qualifier for non-series parameters such as lookback lengths (e.g. `simple int length`) to avoid qualifier mismatches at call sites.
- In strategies, `strategy.entry()` with an opposing direction automatically closes the current position and opens the new one. Explicit `strategy.close()` is only needed for partial or conditional exits.

## Output Expectations

- Return complete Pine code unless the user asks for analysis only.
- Briefly explain the execution model choices when they affect correctness.
- Call out repainting assumptions whenever the script depends on unconfirmed bars, higher-timeframe requests, intrabar data, or historical plotting offsets.
- When reviewing code, prioritize behavioral bugs, repainting risk, invalid scope usage, type or qualifier mismatches, and limit or optimization issues.


