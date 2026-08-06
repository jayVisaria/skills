# Migrating an existing plugin to Agent Plugins v1

Use this when the user already has a plugin built for one specific client
(a Claude Code plugin, a Cursor extension, a VS Code/Copilot extension, a
Codex config, a Kiro power, etc.) and wants it to also load — unmodified —
in every other Agent Plugins-conformant client.

The guiding principle: **migrate additively.** Never delete or break the
existing client-specific setup until the portable version is built,
validated, and smoke-tested. If a piece of behavior has no portable
equivalent, it's not a defect in the migration — it just stays client-owned.

## Step 1 — Inventory before moving anything

List every artifact the current plugin has, and which client(s) load it:
manifests, skills or skill-like prompts, slash commands, subagents/agents,
MCP or tool-server configs, hooks, LSP servers, UI resources, scripts,
secrets/credential requirements, and any marketplace or catalog entry. If
there's an existing test suite or manual smoke test, run it first so you
have a working baseline to compare against after migrating.

## Step 2 — Classify each artifact into one of four buckets

| Bucket | What goes here | Where it ends up |
| --- | --- | --- |
| Portable core | Skills, MCP servers | `skills/<name>/SKILL.md`, `mcp.json` |
| Client extension | Anything a specific client defines a reverse-domain namespace for (hooks, commands, agents, LSP, UI) | `extensions.<namespace>` in `plugin.json` and/or a `<namespace>/` directory |
| Compatibility layer | Legacy files a client still needs in its own format, kept until that client adopts the portable or namespaced form | Left in place, outside the portable structure |
| Distribution metadata | Marketplace listings, install policy, signing, release config | Outside the spec entirely — not part of any plugin package |

Never assume an artifact silently "becomes portable" just because you moved
it — only skills and MCP servers actually are portable core components. If
there's no documented namespace for something like a hook, it stays in the
compatibility layer; it does not get a namespace you made up.

## Step 3 — Add the portable manifest without deleting anything

Create `plugin.json` at the plugin root:

```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
  "name": "your-plugin-name"
}
```

Add only the supported metadata fields (`version`, `description`, `author`,
`homepage`, `repository`, `license`, `keywords`). Do **not** put component
config or client-specific fields (`hooks`, `agents`, `commands`, `skills`,
`mcpServers`, etc.) at the top level — the manifest schema is closed, and
those belong in `mcp.json` or under `extensions` instead.

## Step 4 — Normalize the portable components

- Move or copy each reusable skill/prompt into `skills/<skill-name>/SKILL.md`.
  Make the frontmatter `name` match the directory name exactly, and check it
  against the Agent Skills naming rules (lowercase, hyphens only, ≤64 chars).
  Only *immediate* children of `skills/` are discovered — don't nest deeper.
- If the client-specific plugin had an MCP/tool-server config in some other
  shape, translate it into root `mcp.json` with the matching 1.0.0 schema
  version and an explicit `stdio`, `streamable-http`, or `sse` `type` for
  every entry (many client-native formats infer the transport instead of
  declaring it — you have to make it explicit here).
- Prefer `${PLUGIN_ROOT}` for files that ship with the package and
  `${PLUGIN_DATA}` for anything the server writes at runtime.

## Step 5 — Preserve what doesn't have a portable equivalent

- Use a client extension namespace **only** if the target client actually
  publishes one and documents its contents. Put manifest-level settings
  under `extensions.<namespace>` and any files under a top-level
  `<namespace>/` directory.
- If a client still needs its legacy layout (e.g. a `.cursor/` or
  `.claude/` config it hasn't updated to read the portable structure), keep
  generating or maintaining that separately — but treat the portable files
  as the source of truth, and generate the legacy copy from them rather than
  hand-maintaining two diverging versions.
- Don't invent a namespace for a client that hasn't documented one and hope
  it gets picked up; it won't be.

## Step 6 — Validate, then test each client, then clean up

1. Run `scripts/validate_plugin.py <plugin-root>` and fix every FATAL and
   INVALID finding.
2. Load the plugin in each client you're targeting (see the
   agent-plugins.org "Compatible Clients" list) and confirm the skills and
   MCP servers actually work there, plus any compatibility-layer behavior
   you kept.
3. Only remove old client-specific files once the portable + extension +
   compatibility-layer replacement passes the same checks the original
   setup did.

## What to report back when you're done

- What format the plugin was migrated from, and which clients it now
  targets.
- A mapping from every original artifact to where it ended up: portable
  core, client extension, compatibility layer, distribution metadata, or
  (rarely) dropped, with a reason.
- Which files were added, moved, generated, kept as-is, or intentionally
  left out.
- Validation results and any manual smoke-test results.
- Remaining client-specific risks — anything that only works in one client
  and why.

Never claim that something became a portable v1 component when it's really
sitting in a client extension or compatibility layer — that distinction is
the entire point of the migration.
