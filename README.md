# Agent Skills

A collection of reusable skills for AI coding agents — Claude Code, VS Code, Cursor, Codex, and more.

These skills help agents perform specialized workflows without writing custom prompts every time. Install a skill once, then use it for repeatable tasks like plugin packaging, hook automation, or Pine Script development.

---

## Featured Skills

| Skill | What it helps with |
|-------|---------------------|
| [agent-hooks](agent-hooks/) | Automate, gate, and extend agent behavior at lifecycle points such as PreToolUse, PostToolUse, SessionStart, and Stop. |
| [agent-plugin-creator](agent-plugin-creator/) | Create, validate, migrate, and package portable Agent Plugins that bundle skills and MCP servers for cross-client compatibility. |
| [pine-script](pine-script/) | Write, fix, review, and explain TradingView Pine Script, including indicators, strategies, libraries, alerts, and multi-timeframe logic. |

---

## Quick Start

Install a skill from this repository with the `skills` CLI:

```bash
# Install one specific skill
npx skills add jayVisaria/skills --skill agent-plugin-creator

# List all available skills in this repo
npx skills add jayVisaria/skills --list
```

### Try it with real prompts

- Agent Hooks: “Set up a pre-tool hook that blocks risky file writes and logs them for review.”
- Agent Plugin Creator: “Create an Agent Plugin for a small invoice toolkit with one skill and one stdio MCP server.”
- Pine Script: “Write a Pine Script strategy that buys on a bullish breakout and exits on a trailing stop.”

---

## Why use skills?

Skills make agent workflows more reliable by giving the model structured guidance for common tasks. Instead of repeating the same instructions in every prompt, you install a reusable package once and reuse it across sessions.

---

## Supported Agents

These skills work with any agent that supports the [Agent Skills specification](https://agentskills.io/), including:

- Claude Code
- VS Code (GitHub Copilot agent)
- Cursor
- Codex
- OpenCode
- Windsurf
- [and more](https://github.com/vercel-labs/skills#supported-agents)

---
