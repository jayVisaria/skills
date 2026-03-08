# Hook Examples and Patterns

Common hook patterns for Claude Code and VS Code. Each example includes the JSON configuration and the hook script.

## Table of Contents

- [Block Dangerous Commands](#block-dangerous-commands)
- [Auto-Format After File Changes](#auto-format-after-file-changes)
- [Log Tool Usage for Auditing](#log-tool-usage-for-auditing)
- [Auto-Approve Safe Operations](#auto-approve-safe-operations)
- [Inject Project Context at Session Start](#inject-project-context-at-session-start)
- [Validate Prompts Before Processing](#validate-prompts-before-processing)
- [Run Tests Before Allowing Stop](#run-tests-before-allowing-stop)
- [Block Sensitive File Access](#block-sensitive-file-access)
- [MCP Tool Logging](#mcp-tool-logging)
- [Async Test Runner After File Edits](#async-test-runner-after-file-edits)
- [Enforce Task Completion Criteria](#enforce-task-completion-criteria)

---

## Block Dangerous Commands

Prevent destructive shell commands before they execute.

**Configuration (`.claude/settings.json`):**

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/block-dangerous.sh"
          }
        ]
      }
    ]
  }
}
```

**Script (`.claude/hooks/block-dangerous.sh`):**

```bash
#!/bin/bash
COMMAND=$(jq -r '.tool_input.command')

if echo "$COMMAND" | grep -qE 'rm -rf|DROP TABLE|format |mkfs'; then
  jq -n '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: "Destructive command blocked by security policy"
    }
  }'
else
  exit 0
fi
```

---

## Auto-Format After File Changes

Run a formatter automatically after any file write or edit.

**Configuration:**

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/auto-format.sh"
          }
        ]
      }
    ]
  }
}
```

**Script (`.claude/hooks/auto-format.sh`):**

```bash
#!/bin/bash
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# Run prettier on supported file types
if [[ "$FILE_PATH" =~ \.(ts|tsx|js|jsx|json|css|md)$ ]]; then
  npx prettier --write "$FILE_PATH" 2>&1
fi

exit 0
```

**VS Code variant** (adjusts for camelCase tool input):

```bash
#!/bin/bash
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.filePath // .tool_input.file_path // empty')

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

npx prettier --write "$FILE_PATH" 2>&1
exit 0
```

---

## Log Tool Usage for Auditing

Log every tool invocation to a file.

**Configuration:**

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/audit-log.sh"
          }
        ]
      }
    ]
  }
}
```

**Script (`.claude/hooks/audit-log.sh`):**

```bash
#!/bin/bash
INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name')
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id')
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

LOG_DIR="$CLAUDE_PROJECT_DIR/.claude/logs"
mkdir -p "$LOG_DIR"

echo "{\"timestamp\":\"$TIMESTAMP\",\"session\":\"$SESSION_ID\",\"tool\":\"$TOOL_NAME\",\"input\":$(echo "$INPUT" | jq -c '.tool_input')}" >> "$LOG_DIR/tool-usage.jsonl"

exit 0
```

---

## Auto-Approve Safe Operations

Automatically approve read-only operations while requiring confirmation for writes.

**Configuration:**

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Read|Glob|Grep",
        "hooks": [
          {
            "type": "command",
            "command": "echo '{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"allow\",\"permissionDecisionReason\":\"Read-only operation auto-approved\"}}'"
          }
        ]
      }
    ]
  }
}
```

---

## Inject Project Context at Session Start

Add project-specific information when a session begins.

**Configuration:**

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/inject-context.sh"
          }
        ]
      }
    ]
  }
}
```

**Script (`.claude/hooks/inject-context.sh`):**

```bash
#!/bin/bash
BRANCH=$(git -C "$CLAUDE_PROJECT_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
NODE_VERSION=$(node --version 2>/dev/null || echo "not installed")

jq -n --arg branch "$BRANCH" --arg node "$NODE_VERSION" '{
  hookSpecificOutput: {
    hookEventName: "SessionStart",
    additionalContext: ("Branch: " + $branch + " | Node: " + $node)
  }
}'
```

---

## Validate Prompts Before Processing

Block prompts containing sensitive patterns.

**Configuration:**

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/validate-prompt.sh"
          }
        ]
      }
    ]
  }
}
```

**Script (`.claude/hooks/validate-prompt.sh`):**

```bash
#!/bin/bash
INPUT=$(cat)
PROMPT=$(echo "$INPUT" | jq -r '.prompt')

# Block prompts with potential API keys or secrets
if echo "$PROMPT" | grep -qEi '(sk-[a-zA-Z0-9]{20,}|AKIA[0-9A-Z]{16}|ghp_[a-zA-Z0-9]{36})'; then
  jq -n '{
    decision: "block",
    reason: "Prompt appears to contain API keys or secrets. Remove them before submitting."
  }'
else
  exit 0
fi
```

---

## Run Tests Before Allowing Stop

Prevent Claude from finishing until tests pass (Claude Code command hook version).

**Configuration:**

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/check-tests.sh"
          }
        ]
      }
    ]
  }
}
```

**Script (`.claude/hooks/check-tests.sh`):**

```bash
#!/bin/bash
INPUT=$(cat)
STOP_HOOK_ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active')

# Prevent infinite loops
if [ "$STOP_HOOK_ACTIVE" = "true" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR"
if ! npm test 2>&1; then
  echo "Tests are failing. Fix them before stopping." >&2
  exit 2
fi

exit 0
```

**Prompt hook version (Claude Code only):**

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Evaluate if Claude should stop: $ARGUMENTS. Check if all tasks are complete and no errors remain.",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

---

## Block Sensitive File Access

Prevent reading or writing sensitive configuration files.

**Configuration:**

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Read|Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/block-sensitive.sh"
          }
        ]
      }
    ]
  }
}
```

**Script (`.claude/hooks/block-sensitive.sh`):**

```bash
#!/bin/bash
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# Block access to sensitive files
SENSITIVE_PATTERNS=('.env' '.env.local' '.git/config' 'id_rsa' 'id_ed25519' '.npmrc' '.pypirc')
for pattern in "${SENSITIVE_PATTERNS[@]}"; do
  if [[ "$FILE_PATH" == *"$pattern"* ]]; then
    jq -n --arg file "$FILE_PATH" '{
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason: ("Access to sensitive file blocked: " + $file)
      }
    }'
    exit 0
  fi
done

# Block path traversal
if echo "$FILE_PATH" | grep -q '\.\.'; then
  jq -n '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: "Path traversal detected and blocked"
    }
  }'
  exit 0
fi

exit 0
```

---

## MCP Tool Logging

Log all operations from a specific MCP server (Claude Code only, MCP tools follow `mcp__<server>__<tool>` naming).

**Configuration:**

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__memory__.*",
        "hooks": [
          {
            "type": "command",
            "command": "echo 'Memory MCP operation' >> ~/mcp-operations.log"
          }
        ]
      }
    ]
  }
}
```

---

## Async Test Runner After File Edits

Run tests in the background after file changes without blocking Claude (Claude Code only).

**Configuration:**

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/run-tests-async.sh",
            "async": true,
            "timeout": 300
          }
        ]
      }
    ]
  }
}
```

**Script (`.claude/hooks/run-tests-async.sh`):**

```bash
#!/bin/bash
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Only run tests for source files
if [[ "$FILE_PATH" != *.ts && "$FILE_PATH" != *.js ]]; then
  exit 0
fi

RESULT=$(npm test 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
  echo "{\"systemMessage\": \"Tests passed after editing $FILE_PATH\"}"
else
  echo "{\"systemMessage\": \"Tests failed after editing $FILE_PATH: $RESULT\"}"
fi
```

---

## Enforce Task Completion Criteria

Block task completion until tests pass (Claude Code only, for agent teams).

**Configuration:**

```json
{
  "hooks": {
    "TaskCompleted": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/check-task-completion.sh"
          }
        ]
      }
    ]
  }
}
```

**Script (`.claude/hooks/check-task-completion.sh`):**

```bash
#!/bin/bash
INPUT=$(cat)
TASK_SUBJECT=$(echo "$INPUT" | jq -r '.task_subject')

if ! npm test 2>&1; then
  echo "Tests not passing. Fix failing tests before completing: $TASK_SUBJECT" >&2
  exit 2
fi

exit 0
```
