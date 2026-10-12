import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from prepare_sync_pr import validate


class SyncArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.candidate = Path(self.temporary.name)
        reference = json.loads((ROOT / "core-ref.json").read_text())
        self.commit = reference["revision"]
        files = ["core-ref.json", "docs/reference/fields.md", "checks/examples/Cargo.toml", "checks/examples/Cargo.lock"]
        files += [f"docs/reference/schemas/{name}" for name in reference["schemas"]]
        for name in files:
            target = self.candidate / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)

    def test_real_generated_reference_is_accepted(self):
        allowed = validate(self.candidate, self.commit, ROOT)
        self.assertIn("core-ref.json", allowed)
        self.assertNotIn("README.md", allowed)

    def test_artifact_cannot_replace_scripts(self):
        (self.candidate / "run.py").write_text("raise SystemExit(0)")
        with self.assertRaisesRegex(ValueError, "unexpected files"):
            validate(self.candidate, self.commit, ROOT)

    def test_manifest_may_only_update_core_revisions(self):
        path = self.candidate / "checks/examples/Cargo.toml"
        path.write_text(path.read_text().replace('publish = false', 'publish = false\nbuild = "run.rs"'))
        with self.assertRaisesRegex(ValueError, "only its two core revisions"):
            validate(self.candidate, self.commit, ROOT)

    def test_changed_schema_bytes_are_rejected(self):
        path = self.candidate / "docs/reference/schemas/base.json"
        path.write_text(path.read_text() + "\n")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            validate(self.candidate, self.commit, ROOT)

    def test_reference_prose_must_match_generated_schema_tables(self):
        path = self.candidate / "docs/reference/fields.md"
        path.write_text(path.read_text() + "Unexpected content\n")
        with self.assertRaisesRegex(ValueError, "does not match the schemas"):
            validate(self.candidate, self.commit, ROOT)

    def test_symlinks_are_rejected(self):
        path = self.candidate / "checks/examples/Cargo.lock"
        path.unlink()
        path.symlink_to(ROOT / "checks/examples/Cargo.lock")
        with self.assertRaisesRegex(ValueError, "symlinks"):
            validate(self.candidate, self.commit, ROOT)


if __name__ == "__main__":
    unittest.main()
