---
description: Select interfaces, name policies, and organize netfyr configuration in YAML files and directories.
---

# Policy files

A policy has a name, an interface selector under `match`, and configuration
fields. Explicit policies use `kind: policy` and a nonempty `name`. Without
`kind`, or with `kind: state`, the filename supplies the policy name.

## Select an interface

The `match` mapping accepts these string values:

| Field | Matches |
| --- | --- |
| `name` | Interface name, such as `eth0` |
| `type` | Device type, such as `ethernet` |
| `driver` | Kernel driver name |
| `pci_path` | PCI address, such as `0000:00:02.0` |
| `mac` | MAC address |

Every field you supply must match. Values are literal; `eth*` is not a wildcard.
MAC addresses are case insensitive. Other values are case sensitive.
An explicit policy requires at least one selector.

One policy can match several interfaces, for example by selecting
`type: ethernet`. A selector that matches no observed interface produces a
diagnostic during [reconciliation](reconciliation.md#review-a-plan).

`match.name` selects an interface. A top-level `name` in an explicit policy names
the policy itself; it does not rename the interface.

## Policy options

Alongside `kind`, `name`, and `match`, a policy accepts:

| Field | Meaning |
| --- | --- |
| `priority` | Optional integer from -2147483648 to 2147483647. Sets the static contribution's priority; the default is 100. Higher values win when policies disagree. |
| `metadata` | Optional mapping of annotations retained on the policy. It does not configure the interface. |

`priority` does not change a dynamic provider's priority. See
[reconciliation](reconciliation.md) for precedence and field merging.

## Multiple policies

Use a YAML list to put several policies in one file:

```yaml
--8<-- "interfaces.yaml"
```

Named policies keep their names. Unnamed entries use the filename followed by
their position, starting at 1. An unnamed
entry in the first position in `interfaces.yaml` becomes `interfaces-1`.

Use one YAML document per file. Separate documents divided by `---` are not
accepted.

## Names and directories

Policy names must be unique within a loaded file or directory. Two files named
`uplink.yaml` in different subdirectories still produce the same default policy
name. Give them explicit names or use different filenames.

Directory loading includes `.yaml` and `.yml` files in subdirectories, in lexical
path order. It skips hidden files, hidden directories, and symbolic links.

Different policies may select the same interface. Loading keeps their
contributions separate; [reconciliation](reconciliation.md) combines the fields
of all matching policies.

## Policy search path

The library's `load_policy_tiers` function accepts directories in precedence
order, highest first. `DEFAULT_POLICY_PATHS` defines this order:

| Precedence | Directory |
| --- | --- |
| 1 | `/run/netfyr/policies` |
| 2 | `/etc/netfyr/policies` |
| 3 | `/usr/lib/netfyr/policies` |

The first tier to define a policy name supplies the entire policy. For example,
an `office` policy in `/etc/netfyr/policies` replaces the same-named policy in
`/usr/lib/netfyr/policies`, including its fields and provider declarations.
Distinct policy names coexist, even when they match the same interface.
Directory precedence selects definitions by name; the `priority` field controls
how the selected policies' contributions combine later.

Duplicate names within one tier are errors. Every tier is loaded and validated,
so an invalid policy in a lower tier still fails the load even if a higher tier
shadows its name. Missing roots and roots that are not directories are skipped;
errors reading an existing directory fail the load.

Applications must call this loader to use the search path. The core libraries
do not watch these directories or automatically apply saved files.

## Reuse observed state

A document without `kind`, or with `kind: state`, can omit `match` and use a
top-level `name` as the interface selector. The policy still takes its name from
the filename. With the default loader options, `name: eth0` becomes
`match.name: eth0`; applications can choose matching by MAC instead through
`ApplyOptions`.

During this conversion, observed `type` becomes a type selector, and fields
that cannot be set, such as `carrier`, are dropped with warnings. Review those
warnings before using the converted policy. A document with an explicit
`match` is validated as a policy instead, so read-only fields are errors.

## Values

Use booleans such as `true`, integers such as `1500`, and strings. Null values
and floating-point numbers are not accepted. Quoting a value makes it a string,
so `mtu: "1500"` does not satisfy the integer field.

The [field reference](../reference/fields.md) lists configuration fields and
their allowed values. Read-only properties such as `carrier` and `driver`
describe observations and cannot be set as policy fields.
