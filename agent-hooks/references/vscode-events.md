# VS Code Hook Events Reference

Complete input/output schemas for all 8 VS Code agent hook events.

## Important VS Code-Specific Notes

1. **Matchers are currently ignored.** VS Code parses matcher syntax from Claude Code configs, but hooks run on all occurrences regardless of matcher value.
2. **Tool names differ from Claude Code.** VS Code uses names like `create_file`, `replace_string_in_file`, `editFiles` instead of `Write`, `Edit`, etc. Check `tool_name` in your hook input.
3. **Tool input uses camelCase.** E.g., `filePath` instead of `file_path`.
4. **Only `type: "command"` hooks are supported.** HTTP, prompt, and agent hooks are not available.
5. **OS-specific commands are supported.** Use `windows`, `linux`, `osx` fields for platform-specific overrides.
6. **Default timeout is 30 seconds** (vs 600 seconds in Claude Code).

## Configuration Locations

VS Code searches these locations (controlled by `chat.hookFilesLocations` setting):

- `.github/hooks/*.json` — Project hooks shared with team (workspace, takes precedence)
- `.claude/settings.local.json` — Local workspace hooks (not committed)
- `.claude/settings.json` — Workspace-level hooks
- `~/.claude/settings.json` — Personal hooks across all workspaces

Customize with:

```json
"chat.hookFilesLocations": {
  ".github/hooks": true,
  "custom/hooks": true,
  "~/.claude/settings.json": false
}
```

## Hook Command Properties

```json
{
  "type": "command",
  "command": "./scripts/hook.sh",
  "windows": "powershell -File scripts\\hook.ps1",
  "linux": "./scripts/hook-linux.sh",
  "osx": "./scripts/hook-mac.sh",
  "cwd": "relative/to/repo/root",
  "env": { "CUSTOM_VAR": "value" },
  "timeout": 30
}
```

OS-specific commands are selected based on the extension host platform. In remote development (SSH, Containers, WSL), this may differ from your local OS.

---

## SessionStart

Fires when a new agent session begins.

**Input:**

```json
{
  "timestamp": "2026-02-09T10:30:00.000Z",
  "cwd": "/path/to/workspace",
  "sessionId": "session-id",
  "hookEventName": "SessionStart",
  "transcript_path": "/path/to/transcript.json",
  "source": "new"
}
```

`source` is currently always `"new"`.

**Output — inject context:**

```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "Project: my-app v2.1.0 | Branch: main | Node: v20.11.0"
  }
}
```

---

## UserPromptSubmit

Fires when the user submits a prompt.

**Input:**

```json
{
  "timestamp": "2026-02-09T10:30:00.000Z",
  "cwd": "/path/to/workspace",
  "sessionId": "session-id",
  "hookEventName": "UserPromptSubmit",
  "transcript_path": "/path/to/transcript.json",
  "prompt": "The user's submitted text"
}
```

**Output:** Uses common output format only (`continue`, `stopReason`, `systemMessage`).

---

## PreToolUse

Fires before the agent invokes a tool.

**Input:**

```json
{
  "timestamp": "2026-02-09T10:30:00.000Z",
  "cwd": "/path/to/workspace",
  "sessionId": "session-id",
  "hookEventName": "PreToolUse",
  "transcript_path": "/path/to/transcript.json",
  "tool_name": "editFiles",
  "tool_input": { "files": ["src/main.ts"] },
  "tool_use_id": "tool-123"
}
```

Note: `tool_name` values differ from Claude Code (e.g., `editFiles` vs `Edit`).

**Output:**

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked by policy",
    "updatedInput": { "files": ["src/safe.ts"] },
    "additionalContext": "User has read-only access"
  }
}
```

`permissionDecision` values: `"allow"`, `"deny"`, `"ask"`

When multiple hooks run for the same tool, the most restrictive decision wins:
1. `deny` (most restrictive)
2. `ask`
3. `allow` (least restrictive)

`updatedInput` must match the expected tool schema (check agent logs for schema). If it doesn't match, it is ignored.

---

## PostToolUse

Fires after a tool completes successfully.

**Input:**

```json
{
  "timestamp": "2026-02-09T10:30:00.000Z",
  "cwd": "/path/to/workspace",
  "sessionId": "session-id",
  "hookEventName": "PostToolUse",
  "transcript_path": "/path/to/transcript.json",
  "tool_name": "editFiles",
  "tool_input": { "files": ["src/main.ts"] },
  "tool_use_id": "tool-123",
  "tool_response": "File edited successfully"
}
```

**Output:**

```json
{
  "decision": "block",
  "reason": "Post-processing validation failed",
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "The edited file has lint errors"
  }
}
```

---

## PreCompact

Fires before conversation context is compacted.

**Input:**

```json
{
  "timestamp": "2026-02-09T10:30:00.000Z",
  "cwd": "/path/to/workspace",
  "sessionId": "session-id",
  "hookEventName": "PreCompact",
  "transcript_path": "/path/to/transcript.json",
  "trigger": "auto"
}
```

`trigger` values: `"auto"` (conversation too long).

**Output:** Common output format only.

---

## SubagentStart

Fires when a subagent is spawned.

**Input:**

```json
{
  "timestamp": "2026-02-09T10:30:00.000Z",
  "cwd": "/path/to/workspace",
  "sessionId": "session-id",
  "hookEventName": "SubagentStart",
  "transcript_path": "/path/to/transcript.json",
  "agent_id": "subagent-456",
  "agent_type": "Plan"
}
```

**Output — inject context:**

```json
{
  "hookSpecificOutput": {
    "hookEventName": "SubagentStart",
    "additionalContext": "Follow project coding guidelines"
  }
}
```

---

## SubagentStop

Fires when a subagent completes.

**Input:**

```json
{
  "timestamp": "2026-02-09T10:30:00.000Z",
  "cwd": "/path/to/workspace",
  "sessionId": "session-id",
  "hookEventName": "SubagentStop",
  "transcript_path": "/path/to/transcript.json",
  "agent_id": "subagent-456",
  "agent_type": "Plan",
  "stop_hook_active": false
}
```

**Output:**

```json
{
  "decision": "block",
  "reason": "Verify subagent results before completing"
}
```

---

## Stop

Fires when the agent session ends.

**Input:**

```json
{
  "timestamp": "2026-02-09T10:30:00.000Z",
  "cwd": "/path/to/workspace",
  "sessionId": "session-id",
  "hookEventName": "Stop",
  "transcript_path": "/path/to/transcript.json",
  "stop_hook_active": false
}
```

Check `stop_hook_active` to prevent infinite loops. When `true`, the agent is already continuing from a previous stop hook.

**Output:**

```json
{
  "hookSpecificOutput": {
    "hookEventName": "Stop",
    "decision": "block",
    "reason": "Run the test suite before finishing"
  }
}
```

**Warning:** Stop hooks that block consume additional premium requests. Always check `stop_hook_active`.

> **Platform difference:** VS Code Stop uses `hookSpecificOutput` nesting, but SubagentStop uses top-level `decision`/`reason`. Claude Code uses top-level `decision` for both.

---

## Compatibility with Claude Code Configs

When VS Code reads Claude Code hook configurations:

- Tool input property names: Claude Code uses `snake_case` (e.g., `tool_input.file_path`), VS Code tools use `camelCase` (e.g., `tool_input.filePath`). Update hook scripts accordingly.
- Tool names: Claude Code uses `Write`/`Edit` for file operations, VS Code uses different names like `create_file`/`replace_string_in_file`. Check `tool_name` in input.
- Matchers: Parsed but not applied. All hooks run on every matching event regardless of matcher.

When VS Code reads Copilot CLI hook configurations:

- lowerCamelCase event names (e.g., `preToolUse`) are converted to PascalCase (`PreToolUse`).
- `bash` command property maps to `osx` and `linux`.
- `powershell` command property maps to `windows`.

## Configuring Hooks via UI

- Type `/hooks` in chat input
- Command Palette: `Chat: Configure Hooks`
- Settings icon in Chat view → Hooks
- `/create-hook` in chat to have AI generate a hook configuration

## Troubleshooting

- **View loaded hooks:** Check logs for "Load Hooks" entries
- **View hook output:** Output panel → "GitHub Copilot Chat Hooks" channel
- **Hook not executing:** Verify file is in `.github/hooks/` with `.json` extension and has `type: "command"`
- **Permission denied:** Ensure scripts have execute permissions (`chmod +x`)
- **Timeout errors:** Increase `timeout` value (default: 30 seconds)
- **JSON parse errors:** Verify stdout outputs valid JSON only
