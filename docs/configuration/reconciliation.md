---
description: How netfyr combines policy settings and resolves conflicts when planning network changes.
---

# How policies combine

Reconciliation combines policy settings and compares them with the current
network state to produce a plan. Fields that no policy sets keep their observed
values. The network changes only when an application asks the
[backend](../reference/support.md) to apply the plan; it can preview the plan first.

## Choose field values

Every policy that matches an interface contributes to its configuration. These
two policies set an MTU of 1500 for Ethernet interfaces and override it with 9000
for `eth0`:

```yaml
--8<-- "priority.yaml"
```

If `eth0` is an observed Ethernet interface, both policies match it. Its MTU is
9000 because `uplink-jumbo` has the higher priority. Other matching Ethernet
interfaces get 1500, and all other configuration fields keep their observed values.

netfyr orders contributions by:

| Order | Rule |
| --- | --- |
| 1 | Higher numeric `priority` first. Static policy fields default to 100. |
| 2 | Selector specificity: `name` first, then `mac`, `pci_path`, `driver`, and `type`. |
| 3 | Policy name, in bytewise lexical order. |
| 4 | Contribution key supplied by the application, in bytewise lexical order. |

Each row breaks ties left by the previous row. Specificity depends on the most
specific field in the selector, regardless of how many fields it has. Every
selector field must still match.

The loader applies [directory precedence](policies.md#policy-search-path) first,
so only the selected definition of each policy name contributes.

## Combine fields

For scalar fields such as `mtu` and `enabled`, the first contribution in precedence
order wins. Mappings merge recursively, so policies that set different fields
under `ipv4` can both contribute.

Lists combine in precedence order and keep the first occurrence of each element.
For IPv4 addresses, netfyr compares the address and prefix length to identify
duplicates; the first occurrence keeps its position and attributes. Other lists
deduplicate identical elements. If every contribution omits a field, it keeps its
observed value.

A configured list replaces the observed list after netfyr combines the
contributions. Setting `ipv4.addresses` can therefore remove existing addresses.
Read [IPv4 address behavior](ipv4.md#existing-addresses) before applying an address
policy.

## Review a plan

When contributions disagree about a scalar or the attributes of the same IPv4
address, netfyr selects the winning value and records the competing values in a
`ValueConflict` diagnostic. The MTU example above reports a conflict for `eth0`.
To reject conflicting values, applications can set `ConflictPolicy::Reject` in
the library options. Reconciliation then returns an error instead of a plan.
This option cannot be set in YAML.

When a selector matches no device, netfyr reports `UnmatchedPolicy` and plans no
operations for it. Other matching contributions can still produce a plan.
Invalid contributions fail reconciliation even when they match no device.

A plan contains field changes, backend operations in execution order, diagnostics,
and the contribution keys for changed fields and list elements. Use
`render_text` or `render_json` to display it, then pass its `diff()` to the
backend's `dry_run` method. Check that report before applying the plan: the
backend can reject an [unsupported device or operation](../reference/support.md#supported-changes)
even when the policy passes schema validation.
