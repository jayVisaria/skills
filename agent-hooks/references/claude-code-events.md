# Claude Code Hook Events Reference

Complete input/output schemas for all 18 Claude Code hook events.

## Table of Contents

- [SessionStart](#sessionstart)
- [InstructionsLoaded](#instructionsloaded)
- [UserPromptSubmit](#userpromptsubmit)
- [PreToolUse](#pretooluse)
- [PermissionRequest](#permissionrequest)
- [PostToolUse](#posttooluse)
- [PostToolUseFailure](#posttoolusefailure)
- [Notification](#notification)
- [SubagentStart](#subagentstart)
- [SubagentStop](#subagentstop)
- [Stop](#stop)
- [TeammateIdle](#teammateidle)
- [TaskCompleted](#taskcompleted)
- [ConfigChange](#configchange)
- [WorktreeCreate](#worktreecreate)
- [WorktreeRemove](#worktreeremove)
- [PreCompact](#precompact)
- [SessionEnd](#sessionend)

---

## SessionStart

Fires when a session begins or resumes. Only `type: "command"` hooks are supported. Keep these fast.

**Matcher values:** `startup` (new session), `resume` (--resume/--continue/\/resume), `clear` (\/clear), `compact` (auto/manual compaction)

**Input:**

```json
{
  "session_id": "abc123",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/path/to/project",
  "permission_mode": "default",
  "hook_event_name": "SessionStart",
  "source": "startup",
  "model": "claude-sonnet-4-6"
}
```

If started with `claude --agent <name>`, includes `agent_type`.

**Output — context injection:**

```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "Context string added to Claude's context"
  }
}
```

Plain text stdout is also added as context.

**Environment variables:** SessionStart hooks can write to `$CLAUDE_ENV_FILE` to persist env vars for all subsequent Bash commands:

```bash
#!/bin/bash
if [ -n "$CLAUDE_ENV_FILE" ]; then
  echo 'export NODE_ENV=production' >> "$CLAUDE_ENV_FILE"
fi
exit 0
```

**Cannot block.** Exit code 2 shows stderr to user only.

---

## InstructionsLoaded

Fires when a CLAUDE.md or `.claude/rules/*.md` file is loaded into context. Fires at session start for eager loads and later for lazy loads. Runs asynchronously. No matcher support.

**Input:**

```json
{
  "session_id": "abc123",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/path/to/project",
  "permission_mode": "default",
  "hook_event_name": "InstructionsLoaded",
  "file_path": "/path/to/CLAUDE.md",
  "memory_type": "Project",
  "load_reason": "session_start"
}
```

Additional fields: `globs` (for `path_glob_match` loads), `trigger_file_path` (for lazy loads), `parent_file_path` (for `include` loads).

`memory_type` values: `"User"`, `"Project"`, `"Local"`, `"Managed"`
`load_reason` values: `"session_start"`, `"nested_traversal"`, `"path_glob_match"`, `"include"`

**No decision control.** Exit code is ignored. Use for audit logging or compliance tracking.

---

## UserPromptSubmit

Fires when the user submits a prompt, before Claude processes it. No matcher support.

**Input:**

```json
{
  "session_id": "abc123",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/path/to/project",
  "permission_mode": "default",
  "hook_event_name": "UserPromptSubmit",
  "prompt": "The user's submitted text"
}
```

**Output — block prompt:**

```json
{
  "decision": "block",
  "reason": "Reason shown to user"
}
```

**Output — add context:**

```json
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "Context added to Claude"
  }
}
```

Plain text stdout is also added as context. Exit code 2 blocks prompt processing and erases the prompt.

---

## PreToolUse

Fires before a tool call executes. Matches on tool name.

**Matcher values:** `Bash`, `Edit`, `Write`, `Read`, `Glob`, `Grep`, `Agent`, `WebFetch`, `WebSearch`, and any MCP tool names (`mcp__<server>__<tool>`).

**Input:**

```json
{
  "session_id": "abc123",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/path/to/project",
  "permission_mode": "default",
  "hook_event_name": "PreToolUse",
  "tool_name": "Bash",
  "tool_input": {
    "command": "npm test"
  },
  "tool_use_id": "toolu_01ABC123..."
}
```

**Tool input schemas by tool:**

- **Bash**: `command` (string), `description` (string, optional), `timeout` (number, optional), `run_in_background` (boolean, optional)
- **Write**: `file_path` (string), `content` (string)
- **Edit**: `file_path` (string), `old_string` (string), `new_string` (string), `replace_all` (boolean, optional)
- **Read**: `file_path` (string), `offset` (number, optional), `limit` (number, optional)
- **Glob**: `pattern` (string), `path` (string, optional)
- **Grep**: `pattern` (string), `path` (string, optional), `glob` (string, optional), `output_mode` (string, optional), `-i` (boolean, optional), `multiline` (boolean, optional)
- **WebFetch**: `url` (string), `prompt` (string)
- **WebSearch**: `query` (string), `allowed_domains` (array, optional), `blocked_domains` (array, optional)
- **Agent**: `prompt` (string), `description` (string), `subagent_type` (string), `model` (string, optional)

**Output — decision control:**

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Reason shown to Claude (for deny) or user (for allow/ask)",
    "updatedInput": {
      "command": "modified command"
    },
    "additionalContext": "Context added before tool executes"
  }
}
```

`permissionDecision` values:
- `"allow"`: Bypasses permission system entirely
- `"deny"`: Prevents the tool call. Reason shown to Claude.
- `"ask"`: Prompts user to confirm

Exit code 2 also blocks the tool call (stderr shown to Claude).

---

## PermissionRequest

Fires when a permission dialog is about to be shown. Matches on tool name (same as PreToolUse).

**Input:** Same as PreToolUse but without `tool_use_id`. Includes `permission_suggestions` array with "always allow" options.

```json
{
  "session_id": "abc123",
  "hook_event_name": "PermissionRequest",
  "tool_name": "Bash",
  "tool_input": {
    "command": "rm -rf node_modules"
  },
  "permission_suggestions": [
    { "type": "toolAlwaysAllow", "tool": "Bash" }
  ]
}
```

**Output — allow/deny:**

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": {
      "behavior": "allow",
      "updatedInput": { "command": "safe-command" },
      "updatedPermissions": [{ "type": "toolAlwaysAllow", "tool": "Bash" }]
    }
  }
}
```

For deny: `"behavior": "deny"`, `"message": "Why denied"`, `"interrupt": true` (optional, stops Claude).

Exit code 2 denies the permission.

---

## PostToolUse

Fires after a tool completes successfully. Matches on tool name.

**Input:**

```json
{
  "session_id": "abc123",
  "hook_event_name": "PostToolUse",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/path/to/file.txt",
    "content": "file content"
  },
  "tool_response": {
    "filePath": "/path/to/file.txt",
    "success": true
  },
  "tool_use_id": "toolu_01ABC123..."
}
```

**Output:**

```json
{
  "decision": "block",
  "reason": "Lint errors found, fix before proceeding",
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "Additional info for Claude"
  }
}
```

For MCP tools: `updatedMCPToolOutput` replaces the tool's output.

**Cannot truly block** (tool already ran). `decision: "block"` shows the reason to Claude as feedback. Exit code 2 shows stderr to Claude.

---

## PostToolUseFailure

Fires when a tool execution fails. Matches on tool name.

**Input:**

```json
{
  "session_id": "abc123",
  "hook_event_name": "PostToolUseFailure",
  "tool_name": "Bash",
  "tool_input": { "command": "npm test" },
  "tool_use_id": "toolu_01ABC123...",
  "error": "Command exited with non-zero status code 1",
  "is_interrupt": false
}
```

**Output:**

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUseFailure",
    "additionalContext": "Info about the failure"
  }
}
```

**Cannot block.** Exit code 2 shows stderr to Claude.

---

## Notification

Fires when Claude Code sends notifications. Matches on notification type.

**Matcher values:** `permission_prompt`, `idle_prompt`, `auth_success`, `elicitation_dialog`

**Input:**

```json
{
  "session_id": "abc123",
  "hook_event_name": "Notification",
  "message": "Claude needs your permission",
  "title": "Permission needed",
  "notification_type": "permission_prompt"
}
```

**Output:** `additionalContext` to add context. **Cannot block notifications.**

---

## SubagentStart

Fires when a subagent is spawned. Matches on agent type.

**Matcher values:** `Bash`, `Explore`, `Plan`, or custom agent names.

**Input:**

```json
{
  "session_id": "abc123",
  "hook_event_name": "SubagentStart",
  "agent_id": "agent-abc123",
  "agent_type": "Explore"
}
```

**Output:** `additionalContext` injected into the subagent's context. **Cannot block subagent creation.**

---

## SubagentStop

Fires when a subagent finishes. Matches on agent type.

**Input:**

```json
{
  "session_id": "abc123",
  "hook_event_name": "SubagentStop",
  "stop_hook_active": false,
  "agent_id": "def456",
  "agent_type": "Explore",
  "agent_transcript_path": "~/.claude/projects/.../subagents/agent-def456.jsonl",
  "last_assistant_message": "Analysis complete."
}
```

**Output:** Same as Stop — `decision: "block"` with `reason` to prevent stopping.

---

## Stop

Fires when the main agent finishes responding. Does not fire on user interrupt. No matcher support.

**Input:**

```json
{
  "session_id": "abc123",
  "hook_event_name": "Stop",
  "stop_hook_active": false,
  "last_assistant_message": "I've completed the refactoring."
}
```

Check `stop_hook_active` to prevent infinite loops — if `true`, the agent is already continuing from a previous stop hook.

**Output:**

```json
{
  "decision": "block",
  "reason": "Run the test suite before finishing"
}
```

Exit code 2 also prevents stopping (stderr sent to Claude as reason to continue).

---

## TeammateIdle

Fires when an agent team teammate is about to go idle. No matcher support.

**Input:**

```json
{
  "session_id": "abc123",
  "hook_event_name": "TeammateIdle",
  "teammate_name": "researcher",
  "team_name": "my-project"
}
```

**Blocking:** Exit code 2 → teammate receives stderr and continues working. JSON `{"continue": false, "stopReason": "..."}` stops the teammate entirely.

---

## TaskCompleted

Fires when a task is being marked complete. No matcher support.

**Input:**

```json
{
  "session_id": "abc123",
  "hook_event_name": "TaskCompleted",
  "task_id": "task-001",
  "task_subject": "Implement user auth",
  "task_description": "Add login and signup endpoints",
  "teammate_name": "implementer",
  "team_name": "my-project"
}
```

**Blocking:** Exit code 2 → task not marked complete, stderr fed back as feedback. JSON `{"continue": false, "stopReason": "..."}` stops the teammate.

---

## ConfigChange

Fires when a configuration file changes during a session. Matches on config source.

**Matcher values:** `user_settings`, `project_settings`, `local_settings`, `policy_settings`, `skills`

**Input:**

```json
{
  "session_id": "abc123",
  "hook_event_name": "ConfigChange",
  "source": "project_settings",
  "file_path": "/path/to/.claude/settings.json"
}
```

**Output:**

```json
{
  "decision": "block",
  "reason": "Config changes require admin approval"
}
```

`policy_settings` changes cannot be blocked (hooks still fire for audit logging).

---

## WorktreeCreate

Fires when a worktree is being created. No matcher support. Only `type: "command"` hooks.

Replaces default git worktree behavior. The hook must print the absolute path to the created worktree directory on stdout.

**Input:**

```json
{
  "session_id": "abc123",
  "hook_event_name": "WorktreeCreate",
  "name": "feature-auth"
}
```

**Output:** Print the absolute worktree path to stdout. Non-zero exit code fails creation.

---

## WorktreeRemove

Fires when a worktree is being removed. No matcher support. Only `type: "command"` hooks.

**Input:**

```json
{
  "session_id": "abc123",
  "hook_event_name": "WorktreeRemove",
  "worktree_path": "/path/to/worktree"
}
```

**No decision control.** Failures logged in debug mode only.

---

## PreCompact

Fires before compaction. Matches on trigger type.

**Matcher values:** `manual` (\/compact), `auto` (context window full)

**Input:**

```json
{
  "session_id": "abc123",
  "hook_event_name": "PreCompact",
  "trigger": "manual",
  "custom_instructions": ""
}
```

For `manual`, `custom_instructions` contains what the user passed to \/compact.

**No decision control.** Exit code 2 shows stderr to user only.

---

## SessionEnd

Fires when a session terminates. Matches on exit reason.

**Matcher values:** `clear`, `logout`, `prompt_input_exit`, `bypass_permissions_disabled`, `other`

**Input:**

```json
{
  "session_id": "abc123",
  "hook_event_name": "SessionEnd",
  "reason": "other"
}
```

**No decision control.** Cannot block session termination.
