# netfyr documentation

User documentation for [netfyr](https://github.com/netfyr/netfyr), built with
[Material for MkDocs](https://squidfunk.github.io/mkdocs-material/).

## Preview

Use Python 3.13:

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements.txt
.venv/bin/mkdocs serve
```

## Check

`core-ref.json` pins the core commit used by the reference and YAML examples.
Clone core once to check the generated files against that commit:

```sh
git clone https://github.com/netfyr/netfyr .cache/core
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/sync_core.py --check
cargo test --locked --manifest-path checks/examples/Cargo.toml
.venv/bin/mkdocs build --strict
```

The guides include the files in `examples/`. Rust tests load each file through
core's policy parser and call `produce()` without changing the network.

## Updates from core

The **Update from core** workflow runs daily or on demand. It imports core's
state schemas, regenerates the field reference and updates the example checker.
It opens a PR after validation passes. Review the linked core changes and update
affected guides before merging.

The workflow waits while an update PR is open. It skips previously proposed
core commits, including closed PRs; reopen the PR to reconsider one.

Validation uses read-only access. A separate job publishes the reference and
example dependency pins. Enable the repository's
**Allow GitHub Actions to create and approve pull requests** setting.
GitHub may require a maintainer to approve workflows on a bot-created PR.
Merge reviewed updates manually so the merge triggers the normal Pages build.

For a local update, fetch core, choose a full commit SHA, then run:

```sh
git -C .cache/core fetch origin main
.venv/bin/python scripts/sync_core.py --revision FULL_CORE_COMMIT_SHA
cargo update --manifest-path checks/examples/Cargo.toml -p netfyr-policy -p netfyr-state
```

Run the checks before committing. Syncing fails on unsupported schema constraints.

## License

Documentation and site code: MIT. Fonts: SIL OFL 1.1. Logo artwork: all rights
reserved. See [NOTICE](NOTICE).
