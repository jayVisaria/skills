# Copyable Agent Plugins examples

Working examples for each shape you'll build. Adapt names, descriptions, and
values — don't ship these placeholder strings as-is.

## 1. Minimal plugin (manifest only)

```
weather-lookup/
└── plugin.json
```

```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
  "name": "weather-lookup"
}
```

This alone is a valid, loadable plugin — it just doesn't do anything yet.

## 2. Plugin with a full manifest

```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
  "name": "invoice-tools",
  "version": "1.3.0",
  "description": "Generate, validate, and reconcile customer invoices.",
  "author": {
    "name": "Priya Shah",
    "email": "priya@example.com",
    "url": "https://example.com/priya"
  },
  "homepage": "https://docs.example.com/invoice-tools",
  "repository": "https://github.com/example/invoice-tools",
  "license": "Apache-2.0",
  "keywords": ["invoicing", "finance", "accounting"]
}
```

## 3. Plugin with one skill

```
invoice-tools/
├── plugin.json
└── skills/
    └── reconcile-invoices/
        ├── SKILL.md
        ├── scripts/
        │   └── match_payments.py
        └── references/
            └── reconciliation-rules.md
```

```markdown
---
name: reconcile-invoices
description: Match incoming payments against open invoices and flag mismatches. Use when the user asks to reconcile payments, close out invoices, or find discrepancies between a bank statement and outstanding invoices.
---

# Reconcile Invoices

1. Load the open-invoice list and the payment/bank statement the user provides.
2. Match each payment to an invoice by amount and reference number...
```

The frontmatter `name` (`reconcile-invoices`) matches the directory name
exactly — this is required, not just good style.

## 4. mcp.json with a local (stdio) server

Use this when the plugin ships its own executable and runs it as a
subprocess.

```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
  "mcpServers": {
    "invoice-db": {
      "type": "stdio",
      "command": "./bin/invoice-server",
      "args": ["--data-dir", "${PLUGIN_DATA}/invoices"],
      "env": {
        "CONFIG_PATH": "${PLUGIN_ROOT}/config/invoice-db.json"
      },
      "cwd": "${PLUGIN_ROOT}"
    }
  }
}
```

Notes:
- `command` is a single plugin-relative token (`./bin/invoice-server`) — the
  executable ships inside the plugin package.
- `${PLUGIN_DATA}` holds anything the server writes at runtime (here, a
  generated invoice database) so it survives a plugin update.
- `${PLUGIN_ROOT}` references a file that shipped *with* the package and
  won't change at runtime.

## 5. mcp.json with a remote (streamable-http) server

Use this when the plugin talks to a hosted service instead of bundling an
executable.

```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
  "mcpServers": {
    "invoice-api": {
      "type": "streamable-http",
      "url": "https://api.example.com/mcp",
      "headers": {
        "X-Tenant-Id": "public-demo"
      }
    }
  }
}
```

Do **not** put an API key or bearer token in `headers` — headers are visible
package data. Real credentials are supplied by the client at connection
time, outside the portable package.

## 6. mcp.json mixing stdio, streamable-http, and legacy sse

```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
  "mcpServers": {
    "local-validator": {
      "type": "stdio",
      "command": "./bin/validate",
      "args": ["--strict"]
    },
    "hosted-search": {
      "type": "streamable-http",
      "url": "https://search.example.com/mcp"
    },
    "legacy-notifications": {
      "type": "sse",
      "url": "https://legacy.example.com/events"
    }
  }
}
```

Only reach for `"sse"` if you specifically need to support a client that
hasn't moved to `streamable-http` yet — client support for it is optional,
so treat it as a compatibility fallback, not a default choice.

## 7. Plugin with a client extension

A client extension is how client-specific behavior (hooks, custom commands,
LSP servers, marketplace metadata, etc.) rides along with a plugin without
becoming part of the portable core. Only use a namespace the target client
actually documents — this example uses a placeholder.

```
invoice-tools/
├── plugin.json
├── skills/
│   └── reconcile-invoices/
│       └── SKILL.md
├── mcp.json
└── com.example.editor/
    └── hooks/
        └── on-save.json
```

```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
  "name": "invoice-tools",
  "extensions": {
    "com.example.editor": {
      "runHookOnSave": true
    }
  }
}
```

A client that doesn't implement `com.example.editor` ignores this entirely
and still loads the skill and MCP servers normally.

## 8. Full multi-component layout

```
invoice-tools/
├── plugin.json
├── skills/
│   ├── reconcile-invoices/
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   │   └── match_payments.py
│   │   └── references/
│   │       └── reconciliation-rules.md
│   └── draft-invoice/
│       └── SKILL.md
├── mcp.json
├── com.example.editor/
│   └── hooks/
│       └── on-save.json
├── LICENSE
└── CHANGELOG.md
```

`LICENSE` and `CHANGELOG.md` are ordinary files sitting in the plugin root —
the spec doesn't forbid extra files, it just doesn't assign them any
portable meaning either.
