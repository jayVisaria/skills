#!/usr/bin/env python3
"""
Scaffold a new Agent Plugins v1.0.0 package skeleton (https://agent-plugins.org).

Writes a schema-correct plugin.json (getting the exact $schema string and
closed field set right is easy to fumble by hand), plus optional skill
stubs and an mcp.json with correctly-shaped server entries. This gets the
mechanical, easy-to-typo parts right; you still need to fill in real skill
instructions and real MCP commands/URLs afterward. Always run
validate_plugin.py on the result before calling it done.

Examples:
    # Minimal plugin, just the manifest
    python3 scaffold_plugin.py hello-plugin

    # Plugin with one skill and a local (stdio) MCP server
    python3 scaffold_plugin.py deploy-tools \\
        --description "Deployment helpers for the Acme platform." \\
        --skill "deploy:Deploy a service to the Acme platform. Use when the user asks to deploy, roll back, or check deployment status." \\
        --mcp-stdio "deploy-api:./bin/deploy-server"

    # Plugin with a remote MCP server
    python3 scaffold_plugin.py search-tools \\
        --mcp-http "search:https://search.example.com/mcp"
"""

import argparse
import json
import re
import sys
from pathlib import Path

PLUGIN_NAME_RE = re.compile(r"^(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$")
PLUGIN_SCHEMA_URL = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
MCP_SCHEMA_URL = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"


def fail(msg):
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


def check_skill_name_shape(name):
    problems = []
    if not re.match(r"^[a-z0-9-]+$", name):
        problems.append("must contain only lowercase letters, digits, and hyphens")
    if name.startswith("-") or name.endswith("-") or "--" in name:
        problems.append("must not start/end with a hyphen or contain consecutive hyphens")
    if len(name) > 64:
        problems.append(f"must be at most 64 characters (got {len(name)})")
    return problems


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def split_spec(spec, flag, sep=":"):
    if sep not in spec:
        fail(f"{flag} expects NAME{sep}VALUE, got '{spec}'")
    name, value = spec.split(sep, 1)
    return name.strip(), value.strip()


def build_parser():
    p = argparse.ArgumentParser(
        description="Scaffold a new Agent Plugins v1.0.0 package skeleton.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("name", help="Plugin name: lowercase a-z/0-9/-/. only, 1-64 chars.")
    p.add_argument("--out", default=None, help="Output directory (default: ./<name>)")
    p.add_argument("--description")
    p.add_argument("--version")
    p.add_argument("--author-name")
    p.add_argument("--author-email")
    p.add_argument("--author-url")
    p.add_argument("--homepage")
    p.add_argument("--repository")
    p.add_argument("--license")
    p.add_argument("--keywords", help="Comma-separated keywords")
    p.add_argument(
        "--skill", action="append", default=[], metavar="NAME:DESCRIPTION",
        help="Add a skill stub at skills/NAME/SKILL.md. Repeatable.",
    )
    p.add_argument(
        "--mcp-stdio", action="append", default=[], metavar="NAME:COMMAND",
        help="Add a local (stdio) MCP server entry. COMMAND should be a bare "
             "executable name or a plugin-relative path like ./bin/server. Repeatable.",
    )
    p.add_argument(
        "--mcp-http", action="append", default=[], metavar="NAME:URL",
        help="Add a remote (streamable-http) MCP server entry. Repeatable.",
    )
    p.add_argument("--force", action="store_true", help="Write into an existing, non-empty output directory.")
    return p


def main():
    args = build_parser().parse_args()

    if not (1 <= len(args.name) <= 64) or not PLUGIN_NAME_RE.match(args.name):
        fail(
            f"'{args.name}' is not a valid Agent Plugins name: 1-64 chars, lowercase "
            f"a-z/0-9/-/. only, must start and end alphanumeric, no '--' or '..'."
        )

    out_dir = Path(args.out) if args.out else Path(args.name)
    if out_dir.exists() and any(out_dir.iterdir()) and not args.force:
        fail(f"{out_dir} already exists and is not empty. Pass --force to write into it anyway.")
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = {"$schema": PLUGIN_SCHEMA_URL, "name": args.name}
    if args.description:
        manifest["description"] = args.description
    if args.version:
        manifest["version"] = args.version
    author = {}
    if args.author_name:
        author["name"] = args.author_name
    if args.author_email:
        author["email"] = args.author_email
    if args.author_url:
        author["url"] = args.author_url
    if author:
        manifest["author"] = author
    if args.homepage:
        manifest["homepage"] = args.homepage
    if args.repository:
        manifest["repository"] = args.repository
    if args.license:
        manifest["license"] = args.license
    if args.keywords:
        manifest["keywords"] = [k.strip() for k in args.keywords.split(",") if k.strip()]

    write_json(out_dir / "plugin.json", manifest)
    created = ["plugin.json"]

    for spec in args.skill:
        sname, sdesc = split_spec(spec, "--skill")
        problems = check_skill_name_shape(sname)
        if problems:
            fail(f"skill name '{sname}' invalid: {'; '.join(problems)}")
        if not sdesc:
            fail(f"skill '{sname}' needs a non-empty description after the colon")
        skill_dir = out_dir / "skills" / sname
        skill_dir.mkdir(parents=True, exist_ok=True)
        title = sname.replace("-", " ").title()
        (skill_dir / "SKILL.md").write_text(
            "---\n"
            f"name: {sname}\n"
            f"description: {sdesc}\n"
            "---\n\n"
            f"# {title}\n\n"
            "<!-- Replace this body with real step-by-step instructions, worked examples,\n"
            "     and edge cases for this skill. This directory IS the skill root -- add\n"
            "     scripts/, references/, and assets/ subdirectories here as needed. -->\n",
            encoding="utf-8",
        )
        created.append(f"skills/{sname}/SKILL.md")

    mcp_servers = {}
    for spec in args.mcp_stdio:
        mname, command = split_spec(spec, "--mcp-stdio")
        mcp_servers[mname] = {
            "type": "stdio",
            "command": command,
            "args": [],
            "cwd": "${PLUGIN_ROOT}",
        }
    for spec in args.mcp_http:
        mname, url = split_spec(spec, "--mcp-http")
        mcp_servers[mname] = {"type": "streamable-http", "url": url}

    if mcp_servers:
        write_json(out_dir / "mcp.json", {"$schema": MCP_SCHEMA_URL, "mcpServers": mcp_servers})
        created.append("mcp.json")

    print(f"Created Agent Plugin skeleton at {out_dir}/")
    for c in created:
        print(f"  + {c}")
    print("\nNext steps:")
    print("  1. Fill in real skill instructions and real MCP commands/URLs.")
    print(f"  2. Run: python3 validate_plugin.py {out_dir}")


if __name__ == "__main__":
    main()
