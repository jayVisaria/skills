# Agent Skills

A collection of reusable skills for AI coding agents — Claude Code, VS Code, Cursor, Codex, and more.

Each skill extends your agent with specialized knowledge and capabilities for specific workflows.

---

## Skills

| Skill | Description |
|-------|-------------|
| [agent-hooks](agent-hooks/) | Automate, gate, and extend agent behavior at lifecycle points (PreToolUse, PostToolUse, SessionStart, Stop, and more) |

---

## Installation

Install any skill using the `skills` CLI:

```bash
# Install a specific skill
npx skills add jayVisaria/skills --skill agent-hooks

# List all available skills in this repo
npx skills add jayVisaria/skills --list
```

---

## Supported Agents

Skills in this repo work with any agent that supports the [Agent Skills specification](https://agentskills.io/), including:

- Claude Code
- VS Code (GitHub Copilot agent)
- Cursor
- Codex
- OpenCode
- Windsurf
- [and more](https://github.com/vercel-labs/skills#supported-agents)

---

## Contributing

1. Fork this repository
2. Create a new folder for your skill with a `SKILL.md` inside
3. Open a pull request

---

