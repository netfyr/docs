#!/usr/bin/env python3
"""Validate a core-sync artifact before copying its allowed files into a PR."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import tomllib

import sync_core


def validate(candidate, commit, root):
    commit = sync_core.revision(commit)
    reference = json.loads((candidate / "core-ref.json").read_text())
    if (reference.get("version"), reference.get("repository"), reference.get("revision")) != (1, sync_core.UPSTREAM, commit):
        raise ValueError("Candidate does not match the validated core revision")
    hashes = reference.get("schemas")
    if not isinstance(hashes, dict) or "base.json" not in hashes:
        raise ValueError("Candidate has no schema inventory")
    if not all(re.fullmatch(r"[a-z][a-z0-9_-]*\.json", name) and
               isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest) for name, digest in hashes.items()):
        raise ValueError("Invalid schema inventory")
    allowed = {"core-ref.json", "docs/reference/fields.md", "checks/examples/Cargo.toml", "checks/examples/Cargo.lock"}
    allowed.update(f"docs/reference/schemas/{name}" for name in hashes)
    files = set()
    for path in candidate.rglob("*"):
        if path.is_symlink():
            raise ValueError("Candidate may not contain symlinks")
        if path.is_file():
            files.add(str(path.relative_to(candidate)))
    if files != allowed:
        raise ValueError("Candidate contains missing or unexpected files")
    schemas = {}
    for name, digest in sorted(hashes.items()):
        data = (candidate / "docs/reference/schemas" / name).read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError(f"Schema hash mismatch: {name}")
        schema = json.loads(data)
        sync_core.validate_schema(schema, name)
        schemas[Path(name).stem] = schema
    if (candidate / "docs/reference/fields.md").read_text() != sync_core.render(schemas, commit):
        raise ValueError("Field reference does not match the schemas")
    current_manifest = (root / "checks/examples/Cargo.toml").read_text()
    expected, count = re.subn(r'rev = "[0-9a-f]{40}"', f'rev = "{commit}"', current_manifest)
    if count != 2 or (candidate / "checks/examples/Cargo.toml").read_text() != expected:
        raise ValueError("The example manifest may change only its two core revisions")
    packages = tomllib.loads((candidate / "checks/examples/Cargo.lock").read_text())["package"]
    source = f"git+{sync_core.UPSTREAM}?rev={commit}#{commit}"
    for name in ["netfyr-policy", "netfyr-state"]:
        if [package.get("source") for package in packages if package["name"] == name] != [source]:
            raise ValueError(f"Lockfile does not pin {name} to the candidate revision")
    return allowed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--body-file", type=Path, required=True)
    args = parser.parse_args()
    allowed = validate(args.candidate, args.revision, sync_core.ROOT)
    previous = sync_core.revision(json.loads((sync_core.ROOT / "core-ref.json").read_text())["revision"])
    for name in sorted(allowed):
        target = sync_core.ROOT / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(args.candidate / name, target)
    for path in (sync_core.ROOT / "docs/reference/schemas").glob("*.json"):
        if str(path.relative_to(sync_core.ROOT)) not in allowed:
            path.unlink()
    args.body_file.write_text(
        f"Update the configuration reference and example checker to [core `{args.revision[:12]}`]"
        f"({sync_core.UPSTREAM}/commit/{args.revision}).\n\n"
        "The sync job passed schema checks, the YAML example tests and a strict site build before opening this PR. "
        "Review the field changes and update any affected guides before merging.\n\n"
        f"[Core changes]({sync_core.UPSTREAM}/compare/{previous}...{args.revision})\n\n"
        "GitHub may require a maintainer to approve the PR workflows. Merge this PR manually after review; "
        "the merge starts the Pages deployment.\n"
    )


if __name__ == "__main__":
    main()
