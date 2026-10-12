#!/usr/bin/env python3
"""Import state schemas from one core commit and render their field reference."""

import argparse
import hashlib
import html
import json
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent
UPSTREAM = "https://github.com/netfyr/netfyr"
SCHEMAS = "crates/netfyr-state/schemas"
KEYWORDS = {
    "$schema", "title", "description", "type", "properties", "items", "required",
    "additionalProperties", "enum", "minimum", "maximum", "format",
    "x-netfyr-writable", "x-netfyr-device-type",
}


def revision(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{40}", value):
        raise ValueError("Core revision must be a full lowercase commit SHA")
    return value


def git(source, *arguments):
    return subprocess.check_output(["git", "-C", str(source), *arguments])


def validate_schema(node, location):
    if not isinstance(node, dict):
        raise ValueError(f"{location}: expected a schema object")
    unknown = node.keys() - KEYWORDS
    if unknown:
        raise ValueError(f"{location}: unsupported schema keywords: {', '.join(sorted(unknown))}")
    if node.get("type") not in {"object", "array", "string", "integer", "boolean", "number", "null"}:
        raise ValueError(f"{location}: missing or unsupported field type")
    if "additionalProperties" in node and not isinstance(node["additionalProperties"], bool):
        raise ValueError(f"{location}: additionalProperties must be boolean")
    if "x-netfyr-writable" in node and not isinstance(node["x-netfyr-writable"], bool):
        raise ValueError(f"{location}: writability must be boolean")
    if "enum" in node and (node["type"] != "string" or not isinstance(node["enum"], list)
                           or not all(isinstance(value, str) for value in node["enum"])):
        raise ValueError(f"{location}: enum requires a string field and a list of strings")
    if node["type"] == "object":
        properties = node.get("properties", {})
        required = node.get("required", [])
        if not isinstance(properties, dict) or not isinstance(required, list):
            raise ValueError(f"{location}: invalid properties or required list")
        if not all(isinstance(name, str) and name in properties for name in required):
            raise ValueError(f"{location}: required fields must be declared properties")
        for name, child in properties.items():
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", name):
                raise ValueError(f"{location}: unsupported field name: {name}")
            validate_schema(child, f"{location}.{name}")
    elif node["type"] == "array":
        validate_schema(node.get("items"), f"{location}[]")


def cell(value):
    escaped = re.sub(r"([\\`*_{}\[\]()#+\-.!])", r"\\\1", str(value))
    return html.escape(escaped, quote=False).replace("|", "&#124;").replace("\n", " ")


def constraints(node, required):
    result = ["Required"] if required else []
    for key, label in [("minimum", "Minimum"), ("maximum", "Maximum"), ("format", "Format")]:
        if key in node:
            result.append(f"{label}: {node[key]}")
    if "enum" in node:
        result.append("One of: " + ", ".join(json.dumps(value, ensure_ascii=False) for value in node["enum"]))
    if node["type"] == "object" and node.get("additionalProperties", False) is False:
        result.append("No additional fields")
    return "; ".join(result) or "-"


def field_rows(field, node, required=False, writable=None):
    if writable is None:
        writable = node.get("x-netfyr-writable", False)
    values = [node["type"], "Yes" if writable else "No",
              constraints(node, required), node.get("description", "")]
    yield f"| `{field}` | " + " | ".join(cell(value) for value in values) + " |"
    if node["type"] == "object":
        yield from rows(node, field)
    elif node["type"] == "array":
        yield from field_rows(field + "[]", node["items"], writable=writable)


def rows(node, prefix=""):
    for name, child in node.get("properties", {}).items():
        field = f"{prefix}.{name}" if prefix else name
        yield from field_rows(field, child, name in node.get("required", []))


def render(schemas, commit):
    lines = [
        "# State fields", "",
        "Set writable fields in a policy. `type` is also accepted as device metadata; "
        "[`match.type`](../configuration/policies.md) selects an interface. "
        "Other read-only fields describe observed state.", "",
        "Each download describes one group of state fields. See [policy files](../configuration/policies.md) "
        "for the full policy syntax and [dynamic providers](../configuration/providers.md) for provider parameters.", "",
    ]
    for name, schema in schemas.items():
        prefix = "" if name == "base" else name
        title = "Common fields" if name == "base" else "IPv4" if name == "ipv4" else name.capitalize()
        lines += [f"## {title}", "", cell(schema.get("description", "")), ""]
        if schema.get("x-netfyr-device-type"):
            lines += [f"Device type: {cell(schema['x-netfyr-device-type'])}.", ""]
        if schema.get("additionalProperties", False) is False:
            lines += ["Unlisted fields are rejected in this schema fragment.", ""]
        lines += ["| Field | Type | Writable | Constraints | Description |",
                  "| --- | --- | --- | --- | --- |", *rows(schema, prefix), "",
                  f"[Download {name} schema](schemas/{name}.json)", ""]
    lines += [f"Source: [netfyr `{commit[:12]}`]({UPSTREAM}/tree/{commit}/{SCHEMAS}).", ""]
    return "\n".join(lines)


def collect(source, commit):
    commit = revision(commit)
    resolved = git(source, "rev-parse", "--verify", f"{commit}^{{commit}}").decode().strip()
    if resolved != commit:
        raise ValueError("Core revision did not resolve to the requested commit")
    entries = git(source, "ls-tree", "-z", commit, f"{SCHEMAS}/").split(b"\0")
    blobs = {}
    for entry in filter(None, entries):
        metadata, raw_path = entry.split(b"\t", 1)
        path = raw_path.decode()
        name = Path(path).name
        if not name.endswith(".json"):
            continue
        if metadata.split()[0] != b"100644" or not re.fullmatch(r"[a-z][a-z0-9_-]*\.json", name):
            raise ValueError(f"Unsupported schema file: {path}")
        blobs[name] = git(source, "show", f"{commit}:{path}")
    if "base.json" not in blobs:
        raise ValueError("Core has no base state schema")
    schemas = {}
    for name, data in sorted(blobs.items()):
        schema = json.loads(data)
        validate_schema(schema, name)
        if schema["type"] != "object":
            raise ValueError(f"{name}: state fragments must describe objects")
        schemas[Path(name).stem] = schema
    return blobs, schemas


def outputs(source, commit):
    blobs, schemas = collect(source, commit)
    reference = {"version": 1, "repository": UPSTREAM, "revision": commit,
                 "schemas": {name: hashlib.sha256(data).hexdigest() for name, data in sorted(blobs.items())}}
    result = {"core-ref.json": (json.dumps(reference, indent=2) + "\n").encode(),
              "docs/reference/fields.md": render(schemas, commit).encode()}
    result.update({f"docs/reference/schemas/{name}": data for name, data in blobs.items()})
    manifest = (ROOT / "checks/examples/Cargo.toml").read_text()
    manifest, count = re.subn(r'rev = "[0-9a-f]{40}"', f'rev = "{commit}"', manifest)
    if count != 2 or manifest.count(f'git = "{UPSTREAM}"') != 2:
        raise ValueError("Expected exactly two pinned core dependencies in the example checker")
    result["checks/examples/Cargo.toml"] = manifest.encode()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / ".cache/core", help="Local git checkout of core")
    parser.add_argument("--revision", help="Full core commit SHA; defaults to core-ref.json")
    parser.add_argument("--check", action="store_true", help="Fail on drift without writing files")
    args = parser.parse_args()
    reference = json.loads((ROOT / "core-ref.json").read_text())
    if reference.get("repository") != UPSTREAM or reference.get("version") != 1:
        raise ValueError("Unsupported core reference")
    commit = revision(args.revision or reference["revision"])
    generated = outputs(args.source, commit)
    schema_dir = ROOT / "docs/reference/schemas"
    obsolete = {p for p in schema_dir.glob("*.json") if str(p.relative_to(ROOT)) not in generated}
    changed = [name for name, data in generated.items() if not (ROOT / name).exists() or (ROOT / name).read_bytes() != data]
    if args.check:
        if changed or obsolete:
            raise ValueError("Generated core reference is out of date: " + ", ".join(changed + [str(p.relative_to(ROOT)) for p in obsolete]))
        print(f"Core reference matches {commit}")
        return
    for name, data in generated.items():
        target = ROOT / name
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + ".tmp")
        temporary.write_bytes(data)
        temporary.replace(target)
    for path in obsolete:
        path.unlink()
    print(f"Imported {len(list(schema_dir.glob('*.json')))} state schemas from {commit}")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"Core sync failed: {error}", file=sys.stderr)
        sys.exit(1)
