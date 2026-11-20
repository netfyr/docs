---
description: Resolve netfyr policy validation errors, reconciliation diagnostics, and network backend failures.
---

# Troubleshooting

## Configuration errors

Validation errors include field paths, including positions in address lists.
A file can report several errors at once.

| Problem | What to check |
| --- | --- |
| Unknown field | Check the spelling and location against the [field reference](reference/fields.md). Configuration fields belong directly beside `match`, not inside `state`. |
| Read-only field | Remove observation fields such as `carrier` from the policy. To select by driver or MAC address, put the value under `match`. |
| MTU out of range | Use an integer between 68 and 65535. |
| Invalid IPv4 address | Include an IPv4 address and prefix, such as `192.0.2.10/24`. |
| Wrong value type | Use `true` or `false` for booleans and unquoted numbers for integer fields. |
| Missing match | Give an explicit policy at least one field under `match`, such as `name`. |
| Duplicate policy name | Choose unique explicit names, or different filenames for unnamed policies. |
| Invalid priority | Use an unquoted integer from -2147483648 to 2147483647. |
| More than one YAML document | Replace `---`-separated documents with a single list of mappings. |

When using [policy tiers](configuration/policies.md#policy-search-path), duplicate
names are rejected within each tier. A duplicate across tiers selects the
higher-precedence definition. Invalid lower-tier files still need to be corrected
even if their policy names are shadowed.

## Reconciliation diagnostics

| Report | What to check |
| --- | --- |
| `UnmatchedPolicy` | Check the selector against the observation from the intended network namespace. All supplied selector fields must match. No interface is created for an unmatched policy. |
| `ValueConflict` | Inspect the competing values and winning contribution. Adjust the policies or their [priority](configuration/reconciliation.md#choose-field-values) if the selected value is unintended. With `ConflictPolicy::Reject`, conflicting values prevent a plan. |
| Duplicate contribution keys | The calling application must assign a unique key to every contribution passed to `reconcile()`. |
| Incomplete IPv4 inventory | Obtain a complete observation before managing `ipv4.addresses`. If only changing another field, omit the address list. |
| Unsafe address group | The observed peer, scope, grouping, or flags cannot be safely preserved by the planned address operations. Inspect the reported group; do not discard observation details to force a plan. |
| Invalid IPv4 lifetime | Use a positive valid lifetime and a preferred lifetime no greater than it. See [address lifetimes](configuration/ipv4.md#address-lifetimes). |

## Backend reports

| Report | Next step |
| --- | --- |
| `UnsupportedEntityType` | The current backend modifies existing Ethernet and veth interfaces. Check the selected interface type. |
| `UnsupportedOperation` | Check [supported changes](reference/support.md#supported-changes); schema acceptance alone does not establish backend support. |
| `PermissionDenied` | Check the caller's permissions to enter or modify the selected network namespace. A successful dry run does not prove write permission. |
| `NotFound` or `StaleState` | Query the intended namespace again and rebuild the plan from the current interface identity and address inventory. |
| `ApplyFailed` | Inspect the failed operation, kernel error number, and extended acknowledgement when present. Earlier operations may have succeeded. |
| `OutcomeUnknown` | A write may have taken effect. Query the network before retrying or attempting to undo it. |
| `DependencyFailed` | Resolve the earlier failed or blocked operation, then query and rebuild the plan. Independent operations may already have succeeded. |

Apply is not transactional and does not automatically roll back earlier writes.
After an interrupted apply, query the network before building another plan.

If you cannot resolve an error, include the configuration and full message
when [reporting a problem](https://github.com/netfyr/netfyr/issues). Remove
private addresses or other details you do not want to share.
