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

`match.name` selects an interface. A top-level `name` in an explicit policy names
the policy itself; it does not rename the interface.

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

Different policies may select the same interface. The loader keeps their
contributions separate and does not resolve conflicts between them.

## Values

Use booleans such as `true`, integers such as `1500`, and strings. Null values
and floating-point numbers are not accepted. Quoting a value makes it a string,
so `mtu: "1500"` does not satisfy the integer field.

The [field reference](../reference/fields.md) lists configuration fields and
their allowed values. Read-only properties such as `carrier` and `driver`
describe observations and cannot be set as policy fields.
