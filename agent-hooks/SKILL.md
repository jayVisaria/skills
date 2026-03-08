---
name: agent-hooks
description: "Use this skill to automate, gate, or extend Claude Code and VS Code agent behavior at key lifecycle points. Use it when you want to run scripts before or after tool calls, block or approve operations automatically, inject context at session start, format code after edits, run tests and gate Claude on results, or respond to events like prompt submission, session stop, or permission requests. Also use when the user asks about hook configuration, exit codes for hook scripts, PreToolUse, PostToolUse, SessionStart, UserPromptSubmit, or hookSpecificOutput. Covers Claude Code (18 events, 4 handler types) and VS Code (8 events, command handlers with OS-specific overrides)."
---

# Hooks Skill

Hooks are user-defined automations that execute at specific lifecycle points during Claude Code or VS Code agent sessions. They let you enforce security policies, automate code quality, create audit trails, inject context, and control approvals — all deterministically with guaranteed outcomes.

## Quick Start

Hooks fire at lifecycle points. Each hook is configured in a JSON settings file with three levels of nesting:

1. Choose an **event** (e.g., `PreToolUse`, `Stop`)
2. Add a **matcher** to filter when it fires (e.g., only for the `Bash` tool)
3. Define one or more **handlers** to run when matched

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/validate-bash.sh"
          }
        ]
      }
    ]
  }
}
```

## Platform Differences

Before writing hooks, understand the key differences between Claude Code and VS Code:

| Aspect | Claude Code | VS Code |
|--------|-------------|---------|
| Events supported | 18 (full set) | 8 (SessionStart, UserPromptSubmit, PreToolUse, PostToolUse, PreCompact, SubagentStart, SubagentStop, Stop) |
| Handler types | command, http, prompt, agent | command only |
| Matcher behavior | Regex filtering on tool name/event source | Parsed but currently ignored (hooks run on all occurrences) |
| Tool input naming | snake_case (`file_path`) | camelCase (`filePath`) |
| Tool names | `Write`, `Edit`, `Read`, `Bash`, `Glob`, `Grep` | Different names (e.g., `create_file`, `replace_string_in_file`) |
| OS-specific commands | Not supported | `windows`, `linux`, `osx` fields |
| Config locations | `~/.claude/settings.json`, `.claude/settings.json`, `.claude/settings.local.json`, managed policy, plugin `hooks/hooks.json`, skill/agent frontmatter | `.github/hooks/*.json`, `.claude/settings.json`, `.claude/settings.local.json`, `~/.claude/settings.json` |

When adapting hooks between platforms, adjust tool names and input property names accordingly.

## Hook Events Reference

### Events That Can Block Actions

These events fire before an action and can prevent it:

| Event | When | Matcher | Blocking mechanism |
|-------|------|---------|-------------------|
| `PreToolUse` | Before tool execution | Tool name (`Bash`, `Edit`, `Write`, etc.) | `hookSpecificOutput.permissionDecision: "deny"` or exit code 2 |
| `PermissionRequest` | Permission dialog shown (Claude Code only) | Tool name | `hookSpecificOutput.decision.behavior: "deny"` or exit code 2 |
| `UserPromptSubmit` | User submits prompt | None (always fires) | `decision: "block"` or exit code 2 (Claude Code); exit code 2 only (VS Code) |
| `Stop` | Agent finishes responding | None (always fires) | `decision: "block"` or exit code 2 (Claude Code); `hookSpecificOutput.decision` or exit code 2 (VS Code) |
| `SubagentStop` | Subagent finishes | Agent type | `decision: "block"` or exit code 2 |
| `TaskCompleted` | Task marked complete (Claude Code only) | None (always fires) | Exit code 2 |
| `TeammateIdle` | Teammate going idle (Claude Code only) | None (always fires) | Exit code 2 |
| `ConfigChange` | Config file changes (Claude Code only) | Config source | `decision: "block"` or exit code 2 |
| `WorktreeCreate` | Worktree created (Claude Code only) | None (always fires) | Non-zero exit code fails creation |

### Events for Side Effects Only

These events fire for logging, auditing, or context injection but cannot block:

| Event | When | Matcher |
|-------|------|---------|
| `SessionStart` | Session begins/resumes | `startup`, `resume`, `clear`, `compact` |
| `PostToolUse` | Tool succeeds (can return `decision: "block"` as feedback to Claude, but tool already ran) | Tool name |
| `PostToolUseFailure` | Tool fails (Claude Code only) | Tool name |
| `Notification` | Notification sent (Claude Code only) | `permission_prompt`, `idle_prompt`, `auth_success`, `elicitation_dialog` |
| `SubagentStart` | Subagent spawns | Agent type |
| `PreCompact` | Before compaction | `manual`, `auto` |
| `SessionEnd` | Session ends (Claude Code only) | `clear`, `logout`, `prompt_input_exit`, `bypass_permissions_disabled`, `other` |
| `InstructionsLoaded` | CLAUDE.md or rules loaded (Claude Code only) | None (always fires) |
| `WorktreeRemove` | Worktree removed (Claude Code only) | None (always fires) |

For full event-specific input/output schemas, read `references/claude-code-events.md` or `references/vscode-events.md`.

## Hook Handler Types

### Command Hooks (All Platforms)

Shell commands that receive JSON on stdin and return results via exit code + stdout.

```json
{
  "type": "command",
  "command": ".claude/hooks/my-script.sh",
  "timeout": 30
}
```

**Exit codes:**
- **0**: Success. Stdout parsed as JSON for decision control.
- **2**: Blocking error. Stderr fed back as error message. Blocks the action for events that support it.
- **Other**: Non-blocking error. Continues execution.

**VS Code OS-specific commands:**

```json
{
  "type": "command",
  "command": "./scripts/hook.sh",
  "windows": "powershell -File scripts\\hook.ps1",
  "linux": "./scripts/hook-linux.sh",
  "osx": "./scripts/hook-mac.sh"
}
```

### HTTP Hooks (Claude Code Only)

Send event JSON as a POST request to a URL endpoint.

```json
{
  "type": "http",
  "url": "http://localhost:8080/hooks/pre-tool-use",
  "timeout": 30,
  "headers": {
    "Authorization": "Bearer $MY_TOKEN"
  },
  "allowedEnvVars": ["MY_TOKEN"]
}
```

Non-2xx responses, connection failures, and timeouts produce non-blocking errors. To block, return 2xx with appropriate decision JSON in the body.

### Prompt Hooks (Claude Code Only)

Send events to an LLM for single-turn evaluation.

```json
{
  "type": "prompt",
  "prompt": "Evaluate if this tool call is safe: $ARGUMENTS. Respond with {\"ok\": true} or {\"ok\": false, \"reason\": \"...\"}",
  "timeout": 30
}
```

### Agent Hooks (Claude Code Only)

Spawn a subagent with tool access (Read, Grep, Glob) for multi-turn verification.

```json
{
  "type": "agent",
  "prompt": "Verify all unit tests pass before allowing stop. $ARGUMENTS",
  "timeout": 120
}
```

## Common Input Fields

All hook events receive these fields as JSON (via stdin for commands, POST body for HTTP):

```json
{
  "session_id": "abc123",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/path/to/project",
  "permission_mode": "default",
  "hook_event_name": "PreToolUse"
}
```

VS Code uses camelCase field names (`sessionId` instead of `session_id`, `hookEventName` instead of `hook_event_name`) and additionally includes a `timestamp` field. When running inside a subagent (Claude Code), `agent_id` and `agent_type` are included.

## Decision Control Patterns

Different events use different JSON structures to express decisions. Use exit code 2 as a simple alternative for blocking, or exit 0 with JSON for fine-grained control.

### Pattern 1: hookSpecificOutput (PreToolUse)

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Destructive command blocked"
  }
}
```

Values for `permissionDecision`: `"allow"` (bypass permissions), `"deny"` (block), `"ask"` (prompt user). Use `updatedInput` to modify tool parameters before execution.

### Pattern 2: hookSpecificOutput (PermissionRequest, Claude Code Only)

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": {
      "behavior": "allow",
      "updatedInput": { "command": "npm run lint" }
    }
  }
}
```

### Pattern 3: Top-level decision (PostToolUse, UserPromptSubmit, SubagentStop, ConfigChange)

Claude Code Stop and PostToolUseFailure also use this pattern. In VS Code, UserPromptSubmit uses common output format only (no `decision` field), and Stop uses `hookSpecificOutput` instead (see below).

```json
{
  "decision": "block",
  "reason": "Tests must pass before stopping"
}
```

For Stop/SubagentStop: `decision: "block"` prevents Claude from stopping. Omit `decision` or exit 0 with no JSON to allow stopping. For PostToolUse: the `decision: "block"` is returned as feedback to Claude (the tool call has already completed).

**VS Code Stop hook** uses `hookSpecificOutput` nesting (SubagentStop does not):

```json
{
  "hookSpecificOutput": {
    "hookEventName": "Stop",
    "decision": "block",
    "reason": "Run the test suite before finishing"
  }
}
```

### Pattern 4: Universal fields (all events)

```json
{
  "continue": false,
  "stopReason": "Build failed"
}
```

Setting `continue: false` stops Claude entirely regardless of event type.

### Pattern 5: Context injection (SessionStart, UserPromptSubmit, SubagentStart, and others)

```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "Project uses Node 20, TypeScript strict mode"
  }
}
```

## Matcher Patterns

Matchers are regex strings that filter when hooks fire. Omit the matcher or use `"*"` or `""` to match all occurrences.

| Example Pattern | Matches |
|----------------|---------|
| `Bash` | Bash tool only |
| `Edit\|Write` | Edit or Write tools |
| `mcp__memory__.*` | All tools from the memory MCP server |
| `mcp__.*__write.*` | Any write tool from any MCP server |
| `startup` | New session only (SessionStart) |

Events that do not support matchers: `UserPromptSubmit`, `Stop`, `TeammateIdle`, `TaskCompleted`, `WorktreeCreate`, `WorktreeRemove`, `InstructionsLoaded`.

**Important:** VS Code parses matchers but currently ignores them — hooks run on all occurrences regardless.

## Hooks in Skills and Agents (Claude Code Only)

Define hooks directly in skill or agent YAML frontmatter. These are scoped to the component's lifecycle:

```yaml
---
name: secure-operations
description: Perform operations with security checks
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/security-check.sh"
---
```

The `once` field (if `true`) runs the hook only once per session, for skills only.

## Async Hooks (Claude Code Only)

For long-running tasks, set `"async": true` to run in the background without blocking Claude:

```json
{
  "type": "command",
  "command": "/path/to/run-tests.sh",
  "async": true,
  "timeout": 120
}
```

Async hooks cannot return decisions. Output (`systemMessage`, `additionalContext`) is delivered on the next conversation turn.

## SessionStart Environment Variables (Claude Code Only)

SessionStart hooks can persist environment variables using `CLAUDE_ENV_FILE`:

```bash
#!/bin/bash
if [ -n "$CLAUDE_ENV_FILE" ]; then
  echo 'export NODE_ENV=production' >> "$CLAUDE_ENV_FILE"
fi
exit 0
```

## Configuration Locations

Reference `$CLAUDE_PROJECT_DIR` for project-relative paths and `${CLAUDE_PLUGIN_ROOT}` for plugin-bundled scripts.

Hooks snapshot at session startup. Mid-session changes require review via `/hooks` menu before taking effect (Claude Code). In VS Code, use `chat.hookFilesLocations` setting to customize loaded hook file paths.

## Security Best Practices

- Validate and sanitize all inputs from stdin
- Always quote shell variables: `"$VAR"` not `$VAR`
- Check for path traversal (`..` in file paths)
- Use absolute paths for scripts
- Avoid processing `.env`, `.git/`, or key files
- Review all hook scripts before enabling, especially from shared repositories

## Debugging

- Claude Code: Run `claude --debug` for execution details. Toggle verbose mode with `Ctrl+O`.
- VS Code: Check Output panel → "GitHub Copilot Chat Hooks" channel. View agent logs for loaded hooks.

## Reference Files

For complete event-by-event input/output schemas, read the relevant reference:

- `references/claude-code-events.md` — All 18 Claude Code hook events with full input fields, output schemas, and decision control details
- `references/vscode-events.md` — All 8 VS Code hook events with input/output schemas and VS Code-specific considerations
- `references/hook-examples.md` — Common hook patterns: blocking commands, auto-formatting, auditing, auto-approval, context injection
