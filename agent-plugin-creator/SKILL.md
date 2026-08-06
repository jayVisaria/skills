---
name: agent-plugin-creator
description: Build, extend, migrate, or validate Agent Plugins -- the open, vendor-neutral portable package format from agent-plugins.org (spec v1.0.0) that bundles Agent Skills and MCP servers behind one plugin.json manifest so they load unmodified across Cursor, VS Code, GitHub Copilot, ChatGPT/Codex, Kiro, and any other conformant client. Use this whenever the user wants to create an "agent plugin", "AI agent plugin", or "portable plugin" for AI coding agents; mentions plugin.json, mcp.json, agent-plugins.org, or the Agent Plugins specification; wants a skill/MCP-server package that works across multiple AI agents or editors instead of being locked to one client; or wants to migrate, audit, package, or validate an existing Claude/Cursor/Copilot/Codex/Kiro-specific plugin into this portable format -- even if they don't use the exact words "Agent Plugins".
---

# Agent Plugin creator

Agent Plugins is a small, closed package format: a directory with a required
`plugin.json` manifest and two optional, fixed-location components --
`skills/` (Agent Skills) and `mcp.json` (MCP servers). Its entire value
proposition is portability: build the package once, and every conformant
client (Cursor, VS Code, GitHub Copilot, ChatGPT/Codex, Kiro, and others)
loads the same `skills/` and `mcp.json` without you maintaining a
client-specific copy of each. Everything client-specific -- hooks, custom
commands, subagents, LSP servers, install/distribution -- stays out of the
portable core and lives in a namespaced client extension instead.

Note the overlap with Claude's own skill system: Agent Skills (the format
inside `skills/<name>/SKILL.md`) is the same specification Claude's own
skills use. A skill written the normal way for Claude generally drops into
`skills/<name>/` inside an Agent Plugin unchanged.

`references/specification-reference.md` in this skill has the full condensed
rule set. Read it before making judgment calls on anything not covered
below -- this file intentionally keeps only the parts needed for the common
path.

## Figure out which of these four jobs it is

1. **New plugin from scratch** -- nothing exists yet.
2. **Add a component to an existing plugin** -- a skill or MCP server needs
   to be added to a plugin that already has a `plugin.json`.
3. **Migrate an existing client-specific plugin** -- the user has a Claude
   Code / Cursor / Copilot / Codex / Kiro plugin today and wants it portable.
   Follow `references/migration-guide.md` for this path; it has its own
   inventory-classify-migrate-validate workflow. Still run
   `scripts/validate_plugin.py` at the end regardless.
4. **Validate/audit an existing agent-plugins package** -- just run
   `scripts/validate_plugin.py <path>` and walk the user through the
   findings; skip straight to "Validate, every time" below.

For (1) and (2), if the request doesn't already make it clear, ask briefly:
what should the plugin do, does it need a skill (something the agent reads
and follows) or an MCP server (a tool/service the agent calls) or both, and
if MCP -- is it a local executable (stdio) or a hosted service
(streamable-http)? Don't over-ask; a reasonable default plus one clarifying
question beats a long interview.

## Workflow for building or extending a plugin

### 1. Scaffold the skeleton

Use `scripts/scaffold_plugin.py` rather than hand-writing `plugin.json` and
`mcp.json` from scratch -- it gets the exact `$schema` strings, the closed
field sets, and the `${PLUGIN_ROOT}`/`cwd` shapes right by construction,
which are exactly the details that are easy to typo by hand and hard to
notice in review.

```bash
python3 scripts/scaffold_plugin.py invoice-tools \
  --out ./invoice-tools \
  --description "Generate and reconcile customer invoices." \
  --skill "reconcile-invoices:Match payments against open invoices and flag mismatches. Use when reconciling payments or closing out invoices." \
  --mcp-stdio "invoice-db:./bin/invoice-server"
```

Run `python3 scripts/scaffold_plugin.py --help` for every flag (author,
license, keywords, `--mcp-http` for remote servers, etc). It refuses invalid
plugin/skill names up front with the specific rule they violate, and won't
overwrite a non-empty output directory unless you pass `--force`.

If you're adding a component to a plugin that already exists, don't
re-scaffold the whole thing -- just add the new `skills/<name>/SKILL.md` or
the new entry inside the existing `mcp.json`'s `mcpServers` object by hand,
following `references/examples.md` for the exact shape.

### 2. Fill in plugin.json

The manifest schema is **closed** -- only `$schema`, `name`, `version`,
`description`, `author`, `homepage`, `repository`, `license`, `keywords`,
and `extensions` are recognized at the top level. Nothing else goes here,
not even to describe a skill or MCP server -- those are discovered from
`skills/` and `mcp.json`, never declared inline in the manifest.

`name` has a strict pattern: 1-64 chars, lowercase `a-z`/`0-9`/`-`/`.` only,
must start and end alphanumeric, no `--` or `..`. Get this wrong and the
*entire plugin* is rejected by a conformant client -- not just a warning,
the whole thing fails to load. `scaffold_plugin.py` checks this for you; if
editing by hand, check it against `references/specification-reference.md` §2.

### 3. Write each skill

For each skill, use the same judgment you'd use writing any Claude skill:
clear triggering conditions in the description, step-by-step instructions in
the body, and detail pushed into `scripts/`, `references/`, and `assets/`
subdirectories under that skill's own directory rather than bloated into
`SKILL.md` itself (clients load the whole `SKILL.md` body once the skill
activates). Two rules specific to Agent Plugins skill discovery, not general
skill-writing, are easy to miss:

- The frontmatter `name` must **exactly match the directory name**. A skill
  at `skills/reconcile-invoices/SKILL.md` with `name: reconcile_invoices` (or
  any other mismatch) is an invalid skill -- skipped by clients, not fixed
  by clients.
- Only *immediate* children of `skills/` are scanned. Nesting a skill inside
  another skill's directory, or one level too deep, makes it invisible to
  every client -- not an error, just silently never discovered.

### 4. Configure MCP servers

Every entry in `mcp.json`'s `mcpServers` needs an explicit `type`: `stdio`
for something the plugin runs as a local subprocess, `streamable-http` for
a hosted service, or `sse` only if you specifically need to support a
client that hasn't moved off the deprecated legacy transport (client
support for `sse` is optional, so don't default to it).

The details that most often go wrong, all covered with examples in
`references/examples.md`:

- `command` (stdio) is **one executable token** -- a bare name or a
  `./`-relative path -- never a shell string like `"python script.py --x"`.
  Put extra words in `args`.
- `cwd`, when set, must literally start with `./`, `${PLUGIN_ROOT}`, or
  `${PLUGIN_DATA}` -- a bare relative string like `"data"` is invalid.
- Use `${PLUGIN_ROOT}` for files shipped with the package, `${PLUGIN_DATA}`
  for anything the server writes at runtime (it persists across updates).
- `env` can't set `PLUGIN_ROOT` or `PLUGIN_DATA` -- those names are reserved
  for the client to supply.
- Remote `url` must be absolute http(s), no userinfo, no fragment, and HTTPS
  unless the host is loopback (`localhost`, `127.0.0.0/8`, `::1`).
- **Never put credentials in `headers` or `env`.** Both are visible package
  data, not a secrets mechanism -- v1 has no portable credential fields at
  all; authentication is entirely client-managed.

### 5. Add client extensions only when a client actually documents one

Hooks, custom commands, subagents, LSP servers, and UI/marketplace metadata
are not portable v1 components. If (and only if) the user needs one of
these for a specific client, and that client publishes a reverse-domain
namespace for it, put the data under `extensions.<namespace>` in
`plugin.json` and/or a top-level `<namespace>/` directory. Don't invent a
namespace speculatively -- an undocumented namespace is simply ignored by
every client, including the one you were hoping would read it.

### 6. Validate, every time

Before telling the user it's done, always run:

```bash
python3 scripts/validate_plugin.py <path-to-plugin-root>
```

Read the output as three tiers, not one pass/fail:

- **FATAL** -- `plugin.json` itself is broken. The *entire plugin* is
  rejected; nothing loads, not even valid skills or servers. Always fix
  every FATAL finding before calling anything done.
- **INVALID** -- one specific skill or MCP server entry is broken. Per the
  spec's failure-isolation design this doesn't take down the rest of the
  plugin, but it does mean that specific thing silently won't load for
  anyone. Fix these too unless the user explicitly wants to ship with a
  known gap.
- **ADVISORY** -- not a spec violation (naming conventions, the deprecated
  `sse` transport, a credential-shaped header name, etc). Worth mentioning,
  not blocking.

The exit code is `0` unless there's a FATAL finding, so don't rely on exit
code alone to mean "ready to ship" -- read the INVALID count too.

## Reporting back to the user

After scaffolding/editing and validating, tell the user:

1. The resulting directory tree.
2. The validator's summary line (fatal / invalid / advisory counts) and
   anything you fixed vs. anything still outstanding and why.
3. What's *not* covered by this spec, so they don't expect it for free:
   installation, distribution/marketplace listing, update/enable UX,
   permission prompts, and how a client visually presents a skill are all
   client-owned, not part of the package format. Point them at
   agent-plugins.org/compatible-clients to check which clients they're
   targeting actually support, and suggest testing in at least one real
   client before considering it done.

## Bundled resources

- `scripts/scaffold_plugin.py` -- generates a schema-correct skeleton
  (`plugin.json`, optional skill stubs, optional `mcp.json`). Stdlib only,
  no dependencies. `--help` lists every flag.
- `scripts/validate_plugin.py` -- full static validator for `plugin.json`,
  `skills/` discovery and frontmatter, `mcp.json` (all three transports),
  and client extension directories. Needs PyYAML (`pip install pyyaml
  --break-system-packages` if missing). Exit code `1` only on a FATAL
  finding.
- `references/specification-reference.md` -- condensed normative rules for
  every section of the spec (manifest, discovery, skills, MCP, plugin
  variables, client extensions, versioning, failure isolation). The source
  of truth for anything this file doesn't cover.
- `references/examples.md` -- copyable examples: minimal plugin, full
  manifest, a skill, stdio MCP, remote MCP, mixed transports, a client
  extension, and a full multi-component layout.
- `references/migration-guide.md` -- step-by-step workflow for converting
  an existing client-specific plugin into the portable core plus a client
  extension, without breaking what already works.
