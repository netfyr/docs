import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
CORE = "b" * 40
LEGACY_BRANCH = f"docs/core-{CORE}"


class SyncRetryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.checkout = self.root / "checkout"
        self.checkout.mkdir()
        self.remote = self.root / "remote.git"
        self.fixture = self.root / "github.json"
        self.created = self.root / "created-pr.json"
        binary_dir = self.root / "bin"
        binary_dir.mkdir()
        self.env = {
            **os.environ,
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": "Sync test",
            "GIT_AUTHOR_EMAIL": "sync@example.test",
            "GIT_COMMITTER_NAME": "Sync test",
            "GIT_COMMITTER_EMAIL": "sync@example.test",
            "GH_REPO": "netfyr/docs",
            "CORE_REVISION": CORE,
            "RUNNER_TEMP": str(self.root),
            "SYNC_FIXTURE": str(self.fixture),
            "SYNC_CREATED_PR": str(self.created),
            "PATH": str(binary_dir) + os.pathsep + os.environ["PATH"],
        }
        gh = binary_dir / "gh"
        gh.write_text('''#!/usr/bin/env python3
import json
import os
from pathlib import Path
import sys

args = sys.argv[1:]
fixture = json.loads(Path(os.environ["SYNC_FIXTURE"]).read_text())
if args[0] == "api":
    endpoint = next(arg for arg in args if arg.startswith("repos/"))
    if endpoint.endswith("/commits/main"):
        print(fixture["base"])
    elif "/pulls?" in endpoint:
        if fixture.get("api_failure"):
            sys.exit(42)
        pages = fixture["pages"] if "--paginate" in args else fixture["pages"][:1]
        if "--slurp" in args:
            print(json.dumps(pages))
        else:
            for page in pages:
                print(json.dumps(page))
    else:
        raise SystemExit(f"unexpected API endpoint: {endpoint}")
elif args[:2] == ["pr", "list"]:
    pulls = [pr for page in fixture["pages"] for pr in page]
    if "--head" in args:
        head = args[args.index("--head") + 1]
        pulls = [pr for pr in pulls if pr["head"]["ref"] == head]
    if args[args.index("--state") + 1] == "open":
        pulls = [pr for pr in pulls if pr["state"] == "open"]
    print(len(pulls))
elif args == ["auth", "setup-git"]:
    pass
elif args[:2] == ["pr", "create"]:
    Path(os.environ["SYNC_CREATED_PR"]).write_text(json.dumps(args))
else:
    raise SystemExit(f"unexpected gh command: {args}")
''')
        gh.chmod(0o755)
        self.git("init", "--bare", str(self.remote))
        self.git("init", "-b", "main")
        self.git("remote", "add", "origin", str(self.remote))
        self.write("README.md", "Original guide\n")
        self.write("core-ref.json", json.dumps({"revision": "a" * 40}))
        self.write("docs/reference/fields.md", "Original fields\n")
        self.write("docs/reference/schemas/base.json", "{}\n")
        self.write("checks/examples/Cargo.toml", "original manifest\n")
        self.write("checks/examples/Cargo.lock", "original lockfile\n")
        for script in (ROOT / "scripts").glob("*.py"):
            self.write(f"scripts/{script.name}", script.read_text())
        self.git("add", ".")
        self.git("commit", "-m", "Initial docs")
        self.git("switch", "-c", LEGACY_BRANCH)
        self.write("core-ref.json", json.dumps({"revision": CORE}))
        self.write("docs/reference/fields.md", "Old generated fields\n")
        self.git("commit", "-am", "Orphaned core update")
        self.orphan = self.git("rev-parse", "HEAD")
        self.git("push", "origin", LEGACY_BRANCH)
        self.git("switch", "main")
        self.git("update-ref", "-d", f"refs/heads/{LEGACY_BRANCH}", self.orphan)
        self.write("README.md", "Updated guide\n")
        self.git("add", ".")
        self.git("commit", "-m", "Update guides and generator")
        self.base = self.git("rev-parse", "HEAD")
        self.git("push", "origin", "main")
        self.env["DOCS_BASE"] = self.base
        self.github()
        self.write("core-ref.json", json.dumps({"revision": CORE}))
        self.write("docs/reference/fields.md", "New generated fields\n")
        self.write("checks/examples/Cargo.toml", "updated manifest\n")
        self.write("checks/examples/Cargo.lock", "updated lockfile\n")
        self.write("../core-update.md", "Update core reference.\n")
        workflow = yaml.safe_load((ROOT / ".github/workflows/sync-core.yml").read_text())
        self.script = next(step["run"] for step in workflow["jobs"]["propose"]["steps"]
                           if step.get("name") == "Open update PR")

    def write(self, name, content):
        target = self.checkout / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)

    def git(self, *args, check=True):
        result = subprocess.run(["git", *args], cwd=self.checkout, env=self.env,
                                text=True, capture_output=True)
        if check and result.returncode:
            self.fail(f"git {args}: {result.stdout}{result.stderr}")
        return result.stdout.strip()

    def github(self, pages=None, api_failure=False):
        self.fixture.write_text(json.dumps({
            "base": self.base, "pages": pages or [[]], "api_failure": api_failure,
        }))

    def run_publish(self):
        return subprocess.run(["bash", "-e", "-o", "pipefail", "-c", self.script],
                              cwd=self.checkout, env=self.env, text=True, capture_output=True)

    def seed_candidate(self, branch, guide="Updated guide\n"):
        self.write("README.md", guide)
        self.git("add", ".")
        tree = self.git("write-tree")
        commit = self.git("commit-tree", tree, "-p", self.base, "-m", "Existing candidate")
        self.git("push", "origin", f"{commit}:refs/heads/{branch}")
        self.git("restore", "--source", self.base, "--staged", "--worktree", "README.md")
        return commit

    def test_retry_after_docs_advance_preserves_guides_and_orphan_branch(self):
        result = self.run_publish()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        args = json.loads(self.created.read_text())
        branch = args[args.index("--head") + 1]
        self.assertNotEqual(branch, LEGACY_BRANCH)
        self.assertEqual(self.git("show", f"origin/{branch}:README.md"), "Updated guide")
        self.assertEqual(self.git("show", f"origin/{branch}:docs/reference/fields.md"),
                         "New generated fields")
        self.assertEqual(self.git("rev-parse", f"origin/{LEGACY_BRANCH}"), self.orphan)

    def test_retry_reuses_identical_candidate(self):
        branch = f"{LEGACY_BRANCH}-{self.base}"
        existing = self.seed_candidate(branch)
        result = self.run_publish()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(self.created.exists())
        self.assertEqual(self.git("rev-parse", f"origin/{branch}"), existing)

    def test_retry_does_not_overwrite_changes_to_existing_candidate(self):
        branch = f"{LEGACY_BRANCH}-{self.base}"
        existing = self.seed_candidate(branch, guide="Manual branch edit\n")
        result = self.run_publish()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.created.exists())
        self.assertEqual(self.git("rev-parse", f"origin/{branch}"), existing)

    def test_closed_update_is_not_reproposed_after_docs_advance(self):
        for branch in [LEGACY_BRANCH, f"{LEGACY_BRANCH}-{'c' * 40}"]:
            with self.subTest(branch=branch):
                self.github(pages=[[], [{"state": "closed", "head": {"ref": branch}}]])
                result = self.run_publish()
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertFalse(self.created.exists())
                self.assertEqual(self.git("rev-parse", "HEAD"), self.base)

    def test_open_update_for_another_core_revision_blocks_new_proposal(self):
        self.github(pages=[[{"state": "open", "head": {"ref": f"docs/core-{'d' * 40}"}}]])
        result = self.run_publish()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(self.created.exists())

    def test_api_failure_stops_publication(self):
        self.github(api_failure=True)
        result = self.run_publish()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.created.exists())


if __name__ == "__main__":
    unittest.main()
