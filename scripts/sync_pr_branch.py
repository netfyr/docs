#!/usr/bin/env python3
"""Choose a core-update branch unless an existing PR blocks the proposal."""

import argparse
import json
import subprocess
import sys

from sync_core import revision


def branch_for_update(core, base, pull_requests):
    prefix = f"docs/core-{core}"
    for pull_request in pull_requests:
        head = pull_request["head"]["ref"]
        if pull_request["state"] == "open" and head.startswith("docs/core-"):
            return None
        if head == prefix or head.startswith(prefix + "-"):
            return None
    return f"{prefix}-{base}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", type=revision, required=True)
    parser.add_argument("--base", type=revision, required=True)
    args = parser.parse_args()
    pages = json.loads(subprocess.check_output([
        "gh", "api", "repos/{owner}/{repo}/pulls?state=all&per_page=100",
        "--paginate", "--slurp",
    ], text=True))
    branch = branch_for_update(args.revision, args.base,
                               (pull_request for page in pages for pull_request in page))
    if branch:
        print(branch)
    else:
        print("An update is awaiting review, or this revision was already proposed.",
              file=sys.stderr)


if __name__ == "__main__":
    main()
