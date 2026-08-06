#!/usr/bin/env python3
"""
Validate an Agent Plugins v1.0.0 package (https://agent-plugins.org).

Checks the root plugin.json manifest, the skills/ directory, and mcp.json
against the Agent Plugins Specification v1.0.0, plus the parts of the
Agent Skills specification that govern SKILL.md frontmatter for skills
discovered inside a plugin. See references/specification-reference.md
in this skill for the condensed normative rules this script implements.

Usage:
    python3 validate_plugin.py <path-to-plugin-root>

Findings are grouped into three severities:
    FATAL    - plugin.json itself is invalid. A conformant client MUST
               reject the whole plugin; nothing in it will load.
    INVALID  - one component, entry, or skill is invalid. Per the spec's
               failure-isolation model this does NOT take down the rest
               of the plugin -- everything else still loads.
    ADVISORY - not a spec violation, just a recommendation (naming
               conventions, deprecated transport, secrets hygiene, etc).

Exit codes:
    0 - no FATAL findings (the plugin core loads)
    1 - at least one FATAL finding (the plugin would be rejected)
    2 - couldn't even run (bad path, missing dependency)
"""

import json
import re
import sys
import urllib.parse
from pathlib import Path

try:
    import yaml
except ImportError:
    print(
        "This script needs PyYAML to read SKILL.md frontmatter.\n"
        "Install it with: pip install pyyaml --break-system-packages",
        file=sys.stderr,
    )
    sys.exit(2)


PLUGIN_SCHEMA_URL = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
MCP_SCHEMA_URL = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"

PLUGIN_NAME_RE = re.compile(r"^(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$")
CWD_RE = re.compile(r"^(?:\./|\$\{PLUGIN_ROOT\}(?:/|$)|\$\{PLUGIN_DATA\}(?:/|$))")
RESERVED_ENV = {"PLUGIN_ROOT", "PLUGIN_DATA"}
CRED_HEADER_HINTS = {
    "authorization", "x-api-key", "api-key", "cookie",
    "x-auth-token", "proxy-authorization", "x-access-token",
}
NAMESPACE_RE = re.compile(r"^[a-z0-9]+(\.[a-z0-9-]+)+$")

ALLOWED_MANIFEST_TOP = {
    "$schema", "name", "version", "description", "author", "homepage",
    "repository", "license", "keywords", "extensions",
}
ALLOWED_AUTHOR_FIELDS = {"name", "email", "url"}
ALLOWED_SKILL_FRONTMATTER = {
    "name", "description", "license", "compatibility", "metadata", "allowed-tools",
}


class Report:
    def __init__(self):
        self.issues = []  # (section, severity, message)

    def fatal(self, section, message):
        self.issues.append((section, "FATAL", message))

    def invalid(self, section, message):
        self.issues.append((section, "INVALID", message))

    def advisory(self, section, message):
        self.issues.append((section, "ADVISORY", message))

    def has_fatal(self):
        return any(sev == "FATAL" for _, sev, _ in self.issues)

    def for_section(self, section):
        return [(sev, msg) for sec, sev, msg in self.issues if sec == section]


def check_skill_name_shape(name):
    """Return a list of human-readable problems with an Agent Skills name."""
    problems = []
    if not re.match(r"^[a-z0-9-]+$", name):
        problems.append("must contain only lowercase letters, digits, and hyphens")
    if name.startswith("-") or name.endswith("-") or "--" in name:
        problems.append("must not start/end with a hyphen or contain consecutive hyphens")
    if len(name) > 64:
        problems.append(f"must be at most 64 characters (got {len(name)})")
    return problems


def validate_manifest(root, report):
    path = root / "plugin.json"
    if not path.exists():
        report.fatal("MANIFEST", "plugin.json not found at the plugin root. Every plugin must include one (spec §4.1, §5.1).")
        return None
    if not path.is_file():
        report.fatal("MANIFEST", "plugin.json exists but is not a regular file.")
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        report.fatal("MANIFEST", f"plugin.json is not valid JSON: {e}")
        return None
    if not isinstance(data, dict):
        report.fatal("MANIFEST", "plugin.json must contain a top-level JSON object (§5.2).")
        return None

    # Unknown top-level fields are explicitly non-fatal: reported and ignored.
    unknown = sorted(set(data.keys()) - ALLOWED_MANIFEST_TOP)
    for key in unknown:
        report.advisory(
            "MANIFEST",
            f"Unknown top-level field \"{key}\" -- a conformant client reports and ignores it "
            f"rather than rejecting the plugin, but it's almost always a mistake. Component "
            f"config belongs in skills/ or mcp.json; client-specific data belongs under "
            f"'extensions' (§5.2, §8).",
        )

    if "$schema" not in data:
        report.fatal("MANIFEST", "Missing required field '$schema' (§5.3).")
    elif not isinstance(data["$schema"], str):
        report.fatal("MANIFEST", "'$schema' must be a string (§5.3).")
    elif data["$schema"] != PLUGIN_SCHEMA_URL:
        report.fatal(
            "MANIFEST",
            f"'$schema' is \"{data['$schema']}\", not the canonical Agent Plugins 1.0.0 "
            f"identifier \"{PLUGIN_SCHEMA_URL}\". A client that doesn't recognize this exact "
            f"string must reject the plugin (§5.2).",
        )

    name = data.get("name")
    if "name" not in data:
        report.fatal("MANIFEST", "Missing required field 'name' (§5.3).")
    elif not isinstance(name, str) or not name:
        report.fatal("MANIFEST", "'name' must be a non-empty string (§5.3, §5.5).")
    else:
        if not (1 <= len(name) <= 64):
            report.fatal("MANIFEST", f"'name' must be 1-64 characters, got {len(name)} (§5.5).")
        if not PLUGIN_NAME_RE.match(name):
            report.fatal(
                "MANIFEST",
                f"'name' \"{name}\" violates the naming rules: lowercase a-z, 0-9, '-', '.' "
                f"only; must start and end with an alphanumeric character; no '--' or '..' (§5.5).",
            )

    for field in ("version", "description", "homepage", "repository", "license"):
        if field in data and not isinstance(data[field], str):
            report.fatal("MANIFEST", f"'{field}' must be a string (§5.4).")

    if "author" in data:
        author = data["author"]
        if not isinstance(author, dict):
            report.fatal("MANIFEST", "'author' must be an object (§5.4).")
        else:
            bad = sorted(set(author.keys()) - ALLOWED_AUTHOR_FIELDS)
            if bad:
                report.fatal(
                    "MANIFEST",
                    f"'author' has unsupported field(s) {', '.join(bad)} -- only name, "
                    f"email, and url are allowed (§5.4).",
                )
            for k in ALLOWED_AUTHOR_FIELDS & set(author.keys()):
                if not isinstance(author[k], str):
                    report.fatal("MANIFEST", f"'author.{k}' must be a string (§5.4).")

    if "keywords" in data:
        kw = data["keywords"]
        if not isinstance(kw, list) or not all(isinstance(x, str) for x in kw):
            report.fatal("MANIFEST", "'keywords' must be an array of strings (§5.4).")

    if "extensions" in data:
        extensions = data["extensions"]
        if not isinstance(extensions, dict):
            report.advisory(
                "MANIFEST",
                "'extensions' is not an object -- reported and ignored (non-fatal), but "
                "unusable as written. It must be an object keyed by client namespace (§8.1).",
            )
        else:
            for ns, val in extensions.items():
                if not isinstance(val, dict):
                    report.advisory(
                        "MANIFEST",
                        f"extensions.\"{ns}\" is not an object -- each namespace's value must "
                        f"be an object; clients ignore malformed entries for namespaces they "
                        f"don't implement, but implementers of \"{ns}\" may reject it (§8.1).",
                    )
                if not NAMESPACE_RE.match(ns):
                    report.advisory(
                        "MANIFEST",
                        f"extensions namespace \"{ns}\" doesn't look like a reverse-domain "
                        f"identifier (e.g. com.example.client) -- recommended so namespaces "
                        f"don't collide (§8).",
                    )

    return data


def validate_skills(root, report):
    skills_dir = root / "skills"
    if not skills_dir.exists():
        return []
    if not skills_dir.is_dir():
        report.invalid(
            "SKILLS",
            "'skills' exists but is not a directory -- the skills component type is invalid "
            "for this plugin; other component types still load (§6.2).",
        )
        return []

    discovered = []
    for child in sorted(skills_dir.iterdir()):
        if not child.is_dir():
            continue  # only immediate child directories are candidates (§7.1)
        skill_md = child / "SKILL.md"
        if not skill_md.is_file():
            continue  # absence of SKILL.md here is not an error, just not a skill

        discovered.append(child.name)
        text = skill_md.read_text(encoding="utf-8")
        m = re.match(r"^---\n(.*?)\n---\s*\n?", text, re.DOTALL)
        if not m:
            report.invalid(
                "SKILLS",
                f"skills/{child.name}/SKILL.md has no YAML frontmatter block -- this skill "
                f"is skipped, siblings are unaffected (Agent Skills spec).",
            )
            continue
        try:
            fm = yaml.safe_load(m.group(1)) or {}
        except yaml.YAMLError as e:
            report.invalid("SKILLS", f"skills/{child.name}/SKILL.md has invalid YAML frontmatter: {e} -- skipped.")
            continue
        if not isinstance(fm, dict):
            report.invalid("SKILLS", f"skills/{child.name}/SKILL.md frontmatter must be a mapping -- skipped.")
            continue

        unknown = sorted(set(fm.keys()) - ALLOWED_SKILL_FRONTMATTER)
        if unknown:
            report.advisory(
                "SKILLS",
                f"skills/{child.name}: unexpected frontmatter field(s) {', '.join(unknown)}. "
                f"Allowed: {', '.join(sorted(ALLOWED_SKILL_FRONTMATTER))}.",
            )

        name = fm.get("name")
        if not name or not isinstance(name, str):
            report.invalid("SKILLS", f"skills/{child.name}/SKILL.md is missing a required string 'name' -- skipped.")
        else:
            if name != child.name:
                report.invalid(
                    "SKILLS",
                    f"skills/{child.name}: frontmatter name \"{name}\" must exactly match its "
                    f"directory name \"{child.name}\" (Agent Skills spec).",
                )
            shape_problems = check_skill_name_shape(name)
            if shape_problems:
                report.invalid(f"SKILLS", f"skills/{child.name}: name \"{name}\" {'; '.join(shape_problems)}.")

        desc = fm.get("description")
        if not desc or not isinstance(desc, str):
            report.invalid("SKILLS", f"skills/{child.name}/SKILL.md is missing a required string 'description' -- skipped.")
        elif len(desc) > 1024:
            report.invalid("SKILLS", f"skills/{child.name}: description is {len(desc)} characters, over the 1024 max.")

        compat = fm.get("compatibility")
        if compat is not None and (not isinstance(compat, str) or len(compat) > 500):
            report.advisory("SKILLS", f"skills/{child.name}: 'compatibility' should be a string of at most 500 characters.")

    # Nested SKILL.md files deeper than one level are never discovered -- flag for awareness.
    for md in skills_dir.rglob("SKILL.md"):
        rel = md.relative_to(skills_dir)
        if len(rel.parts) != 2:
            report.advisory(
                "SKILLS",
                f"skills/{rel} is nested deeper than one level under skills/ and will NOT be "
                f"discovered -- only immediate children of skills/ are scanned (§7.1).",
            )

    return discovered


def validate_server_entry(name, cfg, report):
    prefix = f"mcpServers.{name}"
    if not isinstance(cfg, dict):
        report.invalid("MCP", f"{prefix}: entry must be an object -- server skipped, siblings unaffected (§7.2.2).")
        return

    t = cfg.get("type")
    if t not in ("stdio", "streamable-http", "sse"):
        report.invalid(
            "MCP",
            f"{prefix}: 'type' is {t!r}, must be 'stdio', 'streamable-http', or 'sse' -- "
            f"server skipped (§7.2.1).",
        )
        return

    if t == "stdio":
        allowed = {"type", "command", "args", "env", "cwd"}
        unknown = sorted(set(cfg.keys()) - allowed)
        if unknown:
            report.invalid("MCP", f"{prefix}: unknown field(s) {', '.join(unknown)} for a stdio server -- skipped (§7.2.1).")

        command = cfg.get("command")
        if not isinstance(command, str) or not command:
            report.invalid("MCP", f"{prefix}: 'command' is required and must be a non-empty string -- skipped (§7.2.1).")
        else:
            if " " in command:
                report.invalid(
                    "MCP",
                    f"{prefix}: 'command' (\"{command}\") looks like a shell command line. It "
                    f"must be ONE executable token; put the rest in 'args' (§7.2.1).",
                )
            if ".." in Path(command).parts:
                report.invalid("MCP", f"{prefix}: 'command' must not escape the plugin root via '..' (§4.1).")
            elif command.startswith("/") or (len(command) > 1 and command[1] == ":"):
                report.invalid(
                    "MCP",
                    f"{prefix}: 'command' is an absolute path. Use a bare executable name or a "
                    f"plugin-relative path beginning with './' (§7.2.1).",
                )

        args = cfg.get("args")
        if args is not None and (not isinstance(args, list) or not all(isinstance(a, str) for a in args)):
            report.invalid("MCP", f"{prefix}: 'args' must be an array of strings.")

        env = cfg.get("env")
        if env is not None:
            if not isinstance(env, dict) or not all(isinstance(v, str) for v in env.values()):
                report.invalid("MCP", f"{prefix}: 'env' must be an object of string values.")
            else:
                reserved = RESERVED_ENV & set(env.keys())
                if reserved:
                    report.invalid(
                        "MCP",
                        f"{prefix}: 'env' sets reserved variable(s) {', '.join(sorted(reserved))} "
                        f"-- clients supply these; a plugin cannot override them (§9.2).",
                    )

        cwd = cfg.get("cwd")
        if cwd is not None:
            if not isinstance(cwd, str) or not CWD_RE.match(cwd):
                report.invalid(
                    "MCP",
                    f"{prefix}: 'cwd' (\"{cwd}\") must start with './', '${{PLUGIN_ROOT}}', or "
                    f"'${{PLUGIN_DATA}}' -- server skipped (§7.2.1).",
                )
            elif ".." in Path(cwd.split("}", 1)[-1]).parts:
                report.invalid("MCP", f"{prefix}: 'cwd' must not contain '..' segments that could escape its rooted directory (§4.1).")

    else:  # streamable-http or sse
        allowed = {"type", "url", "headers"}
        unknown = sorted(set(cfg.keys()) - allowed)
        if unknown:
            report.invalid("MCP", f"{prefix}: unknown field(s) {', '.join(unknown)} for {t} -- skipped (§7.2.1).")

        url = cfg.get("url")
        if not isinstance(url, str) or not url:
            report.invalid("MCP", f"{prefix}: 'url' is required and must be a non-empty string -- skipped (§7.2.1).")
        else:
            parsed = urllib.parse.urlsplit(url)
            if parsed.scheme not in ("http", "https"):
                report.invalid("MCP", f"{prefix}: 'url' must be an absolute http(s) URL -- skipped (§7.2.1).")
            if parsed.fragment:
                report.invalid("MCP", f"{prefix}: 'url' must not contain a fragment (#...) (§7.2.1).")
            if parsed.username or parsed.password:
                report.invalid("MCP", f"{prefix}: 'url' must not contain user information (§7.2.1).")
            host = parsed.hostname or ""
            is_loopback = host in ("localhost", "::1") or host.startswith("127.")
            if parsed.scheme == "http" and not is_loopback:
                report.invalid(
                    "MCP",
                    f"{prefix}: non-loopback endpoints must use HTTPS; \"{host}\" is not "
                    f"localhost or a loopback address (§7.2.1).",
                )

        headers = cfg.get("headers")
        if headers is not None:
            if not isinstance(headers, dict) or not all(isinstance(v, str) for v in headers.values()):
                report.invalid("MCP", f"{prefix}: 'headers' must be an object of string values.")
            else:
                seen = {}
                for h in headers:
                    lo = h.lower()
                    if lo in seen:
                        report.invalid(
                            "MCP",
                            f"{prefix}: header \"{h}\" collides with \"{seen[lo]}\" once "
                            f"case-insensitivity is applied -- invalid (§7.2.1).",
                        )
                    seen[lo] = h
                    if lo in CRED_HEADER_HINTS:
                        report.advisory(
                            "MCP",
                            f"{prefix}: header \"{h}\" looks credential-related. Headers are "
                            f"visible package data -- never embed secrets here (§7.2.1).",
                        )

        if t == "sse":
            report.advisory(
                "MCP",
                f"{prefix}: uses the deprecated legacy HTTP+SSE transport. Client support is "
                f"OPTIONAL; prefer 'streamable-http' unless you specifically need a legacy client (§7.2.1).",
            )


def validate_mcp(root, report):
    path = root / "mcp.json"
    if not path.exists():
        return []
    if not path.is_file():
        report.invalid("MCP", "'mcp.json' exists but is not a regular file -- MCP is disabled for this plugin; other components still load (§6.2).")
        return []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        report.invalid("MCP", f"mcp.json is not valid JSON: {e} -- MCP disabled for this plugin (§7.2.2).")
        return []
    if not isinstance(data, dict):
        report.invalid("MCP", "mcp.json must be a JSON object -- MCP disabled for this plugin (§7.2.1).")
        return []

    unknown = sorted(set(data.keys()) - {"$schema", "mcpServers"})
    if unknown:
        report.invalid(
            "MCP",
            f"mcp.json has unknown top-level field(s) {', '.join(unknown)}; it is closed to "
            f"'$schema' and 'mcpServers' -- MCP disabled for this plugin (§7.2.1).",
        )

    if "$schema" not in data:
        report.invalid("MCP", "mcp.json is missing required '$schema' -- MCP disabled for this plugin (§7.2.1).")
    elif data["$schema"] != MCP_SCHEMA_URL:
        report.invalid(
            "MCP",
            f"mcp.json '$schema' is \"{data['$schema']}\", not the canonical Agent Plugins "
            f"1.0.0 MCP identifier \"{MCP_SCHEMA_URL}\" -- MCP disabled for this plugin (§7.2.1).",
        )

    if "mcpServers" not in data:
        report.invalid("MCP", "mcp.json is missing required 'mcpServers' -- MCP disabled for this plugin (§7.2.1).")
        return []
    servers = data["mcpServers"]
    if not isinstance(servers, dict):
        report.invalid("MCP", "'mcpServers' must be an object -- MCP disabled for this plugin (§7.2.1).")
        return []

    for server_name, cfg in servers.items():
        validate_server_entry(server_name, cfg, report)

    return sorted(servers.keys())


def validate_extensions(root, manifest_data, report):
    known_top = {"plugin.json", "mcp.json", "skills"}
    ext_dirs = sorted(
        c.name for c in root.iterdir()
        if c.is_dir() and c.name not in known_top and not c.name.startswith(".")
    )

    manifest_ns = set()
    if isinstance(manifest_data, dict) and isinstance(manifest_data.get("extensions"), dict):
        manifest_ns = set(manifest_data["extensions"].keys())

    for d in ext_dirs:
        if not NAMESPACE_RE.match(d):
            report.advisory(
                "EXTENSIONS",
                f"Top-level directory \"{d}/\" doesn't look like a reverse-domain client "
                f"namespace (e.g. com.example.client). If it's meant to be a client extension, "
                f"rename it to your namespace (§8.2); if not, it simply won't be discovered as "
                f"a portable component.",
            )
    for ns in manifest_ns:
        if ns not in ext_dirs:
            report.advisory(
                "EXTENSIONS",
                f"extensions.\"{ns}\" is declared in plugin.json with no matching \"{ns}/\" "
                f"directory -- fine if that client only reads manifest data, just confirm it's intentional.",
            )

    return ext_dirs


SEVERITY_LABEL = {"FATAL": "[FATAL]  ", "INVALID": "[INVALID]", "ADVISORY": "[ADVISORY]"}


def print_section(report, section, title):
    items = report.for_section(section)
    print(f"\n{title}")
    print("-" * len(title))
    if not items:
        print("  (nothing to report)")
        return
    for sev, msg in items:
        print(f"  {SEVERITY_LABEL[sev]} {msg}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 validate_plugin.py <path-to-plugin-root>")
        sys.exit(2)

    root = Path(sys.argv[1]).resolve()
    if not root.is_dir():
        print(f"Error: {root} is not a directory.", file=sys.stderr)
        sys.exit(2)

    report = Report()
    manifest_data = validate_manifest(root, report)
    skill_names = validate_skills(root, report)
    server_names = validate_mcp(root, report)
    ext_dirs = validate_extensions(root, manifest_data, report)

    plugin_name = manifest_data.get("name") if isinstance(manifest_data, dict) else None
    print("=" * 60)
    print(f"Agent Plugins validation: {root}")
    if plugin_name:
        print(f"Plugin name: {plugin_name}")
    print("=" * 60)

    print_section(report, "MANIFEST", "plugin.json")
    print(f"\nskills/  ({len(skill_names)} discovered: {', '.join(skill_names) or '-'})")
    print("-" * 60)
    for sev, msg in report.for_section("SKILLS"):
        print(f"  {SEVERITY_LABEL[sev]} {msg}")
    if not report.for_section("SKILLS"):
        print("  (nothing to report)")

    print(f"\nmcp.json  ({len(server_names)} server(s): {', '.join(server_names) or '-'})")
    print("-" * 60)
    for sev, msg in report.for_section("MCP"):
        print(f"  {SEVERITY_LABEL[sev]} {msg}")
    if not report.for_section("MCP"):
        print("  (nothing to report)")

    print(f"\nClient extension directories  ({', '.join(ext_dirs) or 'none'})")
    print("-" * 60)
    for sev, msg in report.for_section("EXTENSIONS"):
        print(f"  {SEVERITY_LABEL[sev]} {msg}")
    if not report.for_section("EXTENSIONS"):
        print("  (nothing to report)")

    n_fatal = sum(1 for _, sev, _ in report.issues if sev == "FATAL")
    n_invalid = sum(1 for _, sev, _ in report.issues if sev == "INVALID")
    n_advisory = sum(1 for _, sev, _ in report.issues if sev == "ADVISORY")

    print("\n" + "=" * 60)
    print(f"SUMMARY: {n_fatal} fatal, {n_invalid} isolated invalid, {n_advisory} advisory")
    if n_fatal:
        print("RESULT: REJECTED -- plugin.json is invalid, so a conformant client will not")
        print("        load anything from this plugin. Fix the FATAL items above first.")
    elif n_invalid:
        print("RESULT: LOADS WITH GAPS -- plugin.json is valid, so the plugin loads, but")
        print("        the INVALID item(s) above mean those specific skills/servers will")
        print("        be skipped rather than failing the whole plugin.")
    else:
        print("RESULT: CLEAN -- no spec violations found.")
        if n_advisory:
            print("        The ADVISORY notes above are optional polish, not requirements.")
    print("=" * 60)

    sys.exit(1 if n_fatal else 0)


if __name__ == "__main__":
    main()
