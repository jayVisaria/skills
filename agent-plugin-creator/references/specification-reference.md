# Agent Plugins v1.0.0 — condensed specification reference

This is a working reference for building and validating Agent Plugins packages.
It condenses the normative rules from the Agent Plugins Specification v1.0.0
(agent-plugins.org/specification). Where this file and the live specification
disagree, the specification wins — check it directly for anything load-bearing
or ambiguous. Section numbers (§N) point at the matching section of the
normative spec.

Canonical schema identifiers (copy these exactly — they are compared as exact
strings, not just "looks like a URL"):

- Plugin manifest: `https://agent-plugins.org/schemas/1.0.0/plugin.schema.json`
- MCP configuration: `https://agent-plugins.org/schemas/1.0.0/mcp.schema.json`

## 1. What a plugin is

A plugin is a single directory (the "plugin root"). It must contain exactly
one manifest, `plugin.json`, at that root. Everything else — skills, MCP
config, client extensions — is optional and lives at a fixed location inside
that same root. There's no archive format, registry fetch, or build step in
the spec itself: a plugin is just a directory you can `ls`, `cat`, and put in
git (§4.1).

Every file a client reads or executes from the package must resolve to a path
*inside* the plugin root, even after following symlinks. Any configuration
field that's defined as a plugin-relative path must literally start with
`./`. Command arguments and environment variable values are treated as opaque
strings, not paths, so this containment rule doesn't apply to them (§4.1).

## 2. plugin.json (the manifest)

The manifest is a **closed** JSON object — only these top-level fields are
recognized:

| Field         | Required | Type   | Notes                                                     |
| ------------- | -------- | ------ | ---------------------------------------------------------- |
| `$schema`     | Yes      | string | Must equal the canonical plugin schema URL above, exactly. |
| `name`        | Yes      | string | See naming rules below.                                    |
| `version`     | No       | string | Semantic Versioning recommended, not enforced.              |
| `description` | No       | string | Free text.                                                  |
| `author`      | No       | object | Only `name`, `email`, `url` (all strings) are allowed inside. |
| `homepage`    | No       | string | Free text (not validated as a real URL).                    |
| `repository`  | No       | string | Free text.                                                   |
| `license`     | No       | string | SPDX identifier recommended, not enforced.                   |
| `keywords`    | No       | array  | Array of strings.                                            |
| `extensions`  | No       | object | Client-owned data, keyed by reverse-domain namespace (§8).  |

Metadata strings (`version`, `homepage`, `repository`, `author.email`,
`license`, etc.) are only checked for their JSON *type*. A `version` that
isn't valid semver, or a `license` that isn't a real SPDX id, does **not**
make the manifest invalid — only the JSON type matters for those fields (§5.4).

**Fatal vs. non-fatal manifest problems** — this distinction matters a lot,
because it determines whether the *whole plugin* gets rejected or just one
piece of it:

- **Non-fatal** (client reports it, ignores it, and keeps loading the rest of
  the plugin): an unknown top-level field, or an `extensions` value that
  isn't an object.
- **Fatal** (client rejects the entire plugin — nothing loads, not even
  otherwise-valid skills or MCP servers): missing/wrong-type `$schema` or
  `name`, an unrecognized `$schema` value, a `name` that fails the naming
  rules, any known field with the wrong JSON type, or an `author` object
  containing anything besides `name`/`email`/`url`.

### Plugin name rules (§5.5)

- 1–64 characters.
- Only lowercase `a-z`, `0-9`, `-`, and `.`.
- Must start and end with an alphanumeric character.
- No `--` and no `..` anywhere in the name.
- Valid: `my-plugin`, `acme.tools`, `lint3r`, `a`.
- Invalid: `My-Plugin` (uppercase), `-start`, `has--double`, `too.many..dots`.

The manifest `name` and the plugin's directory name don't have to match, but
keeping them identical is strongly recommended so packaging and discovery
stay predictable.

## 3. Component discovery (§6)

Agent Plugins v1 defines exactly two portable component types. Both live at a
fixed location; `plugin.json` cannot redefine or relocate them, and there's
no way to declare component config inline in the manifest.

| Component type | Fixed location | How it's discovered                                    |
| --------------- | --------------- | -------------------------------------------------------- |
| Skills          | `skills/`       | Immediate child directories that contain a `SKILL.md` regular file. |
| MCP servers     | `mcp.json`      | One JSON document at the plugin root.                    |

A missing location is fine — it's just "this plugin doesn't provide that
component type," not an error. A location that exists but is the *wrong
filesystem kind* (e.g. `skills` is a file, or `mcp.json` is a directory)
invalidates **only that component type**; everything else still loads (§6.2).

## 4. Skills (§7.1)

Agent Plugins doesn't define its own skill format — it defers entirely to the
Agent Skills specification (agentskills.io/specification) for what goes
inside `SKILL.md`. Agent Plugins only defines *where* skills live inside a
plugin and how a broken one is contained.

- Only immediate children of `skills/` are scanned. A `SKILL.md` nested two
  or more levels deep (e.g. `skills/a/b/SKILL.md`) is never discovered — not
  an error, just invisible to the plugin loader.
- If a discovered skill's `SKILL.md` doesn't conform to the Agent Skills
  spec, that one skill is skipped. Every other skill and component keeps
  loading normally (isolated failure, not fatal).

Agent Skills frontmatter rules worth restating here because they're the most
common source of an "invalid skill" finding:

- `name`: required, 1–64 chars, lowercase alphanumeric + hyphens only, no
  leading/trailing/double hyphens, and **must exactly match the skill's
  parent directory name**.
- `description`: required, 1–1024 chars, non-empty.
- `license`, `compatibility` (≤500 chars), `metadata` (string→string map),
  `allowed-tools` are optional.
- Unknown frontmatter fields aren't part of the spec's allowed set:
  `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`.
- Keep the `SKILL.md` body under ~500 lines and push detail into
  `scripts/`, `references/`, and `assets/` inside that same skill directory —
  clients load the body in full once a skill activates, so a bloated body
  costs context on every use.

Because Anthropic's own Claude Skills already use the Agent Skills format,
any skill you'd normally write for Claude can generally be dropped straight
into `skills/<name>/` inside an Agent Plugin unchanged.

## 5. MCP servers — mcp.json (§7.2)

`mcp.json` sits at the plugin root and is itself a **closed** document: only
`$schema` and `mcpServers` are allowed at the top level, both required.
`mcpServers` is an object whose keys are server names and whose values are
server configs; it can be empty.

The whole document targets one Agent Plugins version via its `$schema`, and
that version **must match** the version declared by `plugin.json`'s
`$schema`. If `mcp.json` is missing, malformed, targets an unsupported or
mismatched version, or has an unrecognized top-level field, **MCP is
disabled for the whole plugin** — but skills and everything else still load,
because this failure is isolated to the MCP component type, not fatal to the
manifest (§7.2.2).

Below the top level, each server entry is validated independently: one bad
entry is skipped, its siblings and other component types are unaffected.

### stdio transport

| Field     | Required | Type              | Notes                                                        |
| --------- | -------- | ----------------- | -------------------------------------------------------------- |
| `type`    | Yes      | `"stdio"`          |                                                                  |
| `command` | Yes      | string             | **One** executable token — not a shell command line.           |
| `args`    | No       | array of strings   | Pass extra words here, never appended to `command`.            |
| `env`     | No       | object of strings  | Cannot set `PLUGIN_ROOT` or `PLUGIN_DATA` (reserved, see below).|
| `cwd`     | No       | string             | See allowed forms below. Defaults to the plugin root.          |

`command` must be either a bare executable name (resolved via the platform's
normal executable search) or a plugin-relative path starting with `./`.
Absolute paths, `..`-escaping paths, and multi-word shell strings
(`"python script.py --flag"`) are all invalid — split extra words into
`args`. No placeholder expansion happens inside `command` itself.

`cwd`, when present, must take one of these three forms and must resolve
within the boundary it names:

1. A plugin-relative path starting with `./` (stays inside the plugin root).
2. `${PLUGIN_ROOT}` alone, or `${PLUGIN_ROOT}/...` (stays inside the plugin root).
3. `${PLUGIN_DATA}` alone, or `${PLUGIN_DATA}/...` (stays inside the writable data dir).

A bare relative string like `"data"` (no `./` prefix) is **not** a valid
`cwd` — this is a common mistake.

### streamable-http and sse (remote transports)

| Field     | Required | Type                            | Notes                                             |
| --------- | -------- | -------------------------------- | --------------------------------------------------- |
| `type`    | Yes      | `"streamable-http"` or `"sse"`   | `sse` is the deprecated legacy transport.           |
| `url`     | Yes      | string                            | Absolute http(s) URL, no userinfo, no fragment.     |
| `headers` | No       | object of strings                | Literal HTTP headers sent on connect.               |

Rules for `url`:

- Must be absolute `http://` or `https://`.
- No `user:pass@host` component, no `#fragment`.
- Non-loopback hosts **must** use HTTPS. Loopback (`localhost`, `127.0.0.0/8`,
  `::1`) may use plain HTTP.
- No placeholder expansion (`${PLUGIN_ROOT}` etc.) happens inside `url` or
  `headers` — those are for stdio's `args`/`env`/`cwd` only.

Rules for `headers`:

- Header names are compared case-insensitively; the same name twice under
  different casing is an invalid entry.
- Headers are **visible package data, not a secrets mechanism**. Never put
  API keys, tokens, or credentials in a header value — authentication is
  entirely client-managed in v1 (no portable OAuth or credential-reference
  fields exist).
- Client-generated auth/protocol headers win over a configured header with
  the same name.

`sse` selects the *deprecated* legacy HTTP+SSE transport specifically —
support for it is optional for clients, so prefer `streamable-http` unless
you have a concrete reason to target a legacy-only client. (Note: SSE
streams used *within* `streamable-http` are a different thing and are not
what `type: "sse"` refers to.)

### Transport support and fallback

A client that implements MCP servers at all must support at least one of
`stdio` or `streamable-http`, and is encouraged to support both; `sse`
support is fully optional. Whichever `type` a server entry declares is used
for the *initial* connection attempt — the spec defines no automatic
fallback if that attempt fails (§7.2.1).

## 6. Plugin variables (§9)

Clients that launch a stdio subprocess must inject two environment
variables into it:

- `PLUGIN_ROOT` — absolute path to the plugin's own root directory.
- `PLUGIN_DATA` — absolute path to a per-plugin, writable directory that
  persists across updates (create dependencies, caches, generated files,
  and other state that should survive a plugin upgrade here).

Use `PLUGIN_ROOT` to reference files you *shipped* with the plugin (scripts,
binaries, bundled config). Use `PLUGIN_DATA` for anything the plugin
*writes* at runtime.

`${PLUGIN_ROOT}` and `${PLUGIN_DATA}` are expanded — as a single, literal,
non-recursive text substitution — inside `args` entries, `env` values, and
`cwd`. They are **not** expanded in `command`, in remote `url`/`headers`, or
in environment variable *names*. A plugin's `env` object cannot define a key
named `PLUGIN_ROOT` or `PLUGIN_DATA` — those names are reserved for the
client to set.

## 7. Client extensions (§8)

Anything a specific client wants to add beyond skills and MCP — hooks,
custom agents, slash commands, LSP servers, UI resources, marketplace
metadata — is **not** part of the portable v1 core. It goes through a
client-owned, reverse-domain-namespaced extension instead, in one or both of
these forms:

- **Manifest data**: an entry under `extensions` in `plugin.json`, keyed by
  the namespace (e.g. `extensions["com.example.client"]`).
- **A directory**: a top-level directory in the plugin root whose name is
  exactly the namespace (e.g. `com.example.client/`).

The namespace owner (that client) defines what's valid inside its own
namespace — Agent Plugins assigns no portable meaning, validation, or
failure behavior to extension contents. Other clients simply ignore
namespaces they don't implement, without validating them.

Only use a namespace that the target client actually documents. Don't invent
one and hope a client picks it up — that's not how discovery works here.

## 8. Versioning (§10)

- The spec version, the plugin manifest schema, and the MCP schema are
  released together and share one version number (currently `1.0.0`).
- `plugin.json`'s `$schema` declares which Agent Plugins version the whole
  package targets. If `mcp.json` is present, its `$schema` version must
  match — a mismatch disables MCP for that plugin (isolated, not fatal to
  the manifest).
- Plugin `version` (the metadata field, not `$schema`) should follow
  Semantic Versioning: major = breaking change, minor = backward-compatible
  addition, patch = backward-compatible fix.

## 9. Failure isolation — the model to keep in your head

This is the idea that ties the whole spec together, and it's why the
validator bundled with this skill separates FATAL from INVALID findings:

- A broken **manifest** brings down the *entire plugin* — nothing loads.
- A broken **skill**, a broken **individual MCP server entry**, or a broken
  **`mcp.json` as a whole** only takes down that one thing. Every other
  component keeps loading.

In practice: get `plugin.json` right first and treat it as non-negotiable.
Everything else can be imperfect in a shipped plugin without making the
whole thing unusable — though you should still fix INVALID findings before
calling a plugin done, since they mean a real skill or server silently won't
load for anyone.

## 10. What's deliberately outside this spec

Agent Plugins only standardizes the *package format*. It has nothing to say
about: how a plugin gets installed, distributed, or discovered by users
(registries, marketplaces); how a client enables/updates/caches a plugin;
permission prompts, trust policy, or sandboxing; how a client actually
presents a skill to its model or its user; or what happens inside a client
extension namespace. All of that is client-owned. Don't try to standardize
it inside `plugin.json` — that's exactly what the closed schema and the
`extensions` namespace split are for.
