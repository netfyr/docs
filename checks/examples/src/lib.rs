#[cfg(test)]
mod tests {
    use std::fs;
    use std::path::{Path, PathBuf};

    use netfyr_policy::load_policy_file;
    use netfyr_state::ApplyOptions;

    fn yaml_files(path: &Path) -> Vec<PathBuf> {
        let mut files: Vec<_> = fs::read_dir(path)
            .unwrap_or_else(|error| panic!("cannot read {}: {error}", path.display()))
            .map(|entry| entry.expect("cannot read example directory entry").path())
            .filter(|path| {
                matches!(
                    path.extension().and_then(|extension| extension.to_str()),
                    Some("yaml" | "yml")
                )
            })
            .collect();
        files.sort();
        files
    }

    #[test]
    fn documented_examples_load_and_produce_without_warnings() {
        let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("../../examples");
        let examples = yaml_files(&root);
        assert!(!examples.is_empty(), "no YAML examples found");

        for path in examples {
            let loaded = load_policy_file(&path, ApplyOptions::default())
                .unwrap_or_else(|error| panic!("{}: {error}", path.display()));
            assert!(
                loaded.warnings.is_empty(),
                "{}: {:?}",
                path.display(),
                loaded.warnings
            );
            assert!(
                !loaded.policies.is_empty(),
                "{} contains no policies",
                path.display()
            );

            for policy in loaded.policies {
                policy.produce().unwrap_or_else(|error| {
                    panic!("{} ({}): {error}", path.display(), policy.name)
                });
            }
        }
    }
}
