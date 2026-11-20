---
description: Understand netfyr policy precedence, field merging, conflict diagnostics, and plans for network changes.
---

# How policies combine

Reconciliation compares policy contributions with an observation of the network
and produces a plan. It keeps the fields each policy requests and uses observed
values for fields no policy sets. It does not change the network itself; an
application passes the plan to the [backend](../reference/support.md) to preview
or apply it.

## Choose field values

All policies whose selectors match an interface contribute to its configuration.
For example, these policies set a default MTU for Ethernet interfaces and a
higher-priority value for `eth0`:

```yaml
--8<-- "priority.yaml"
```

For an observed Ethernet interface named `eth0`, the resulting MTU is 9000.
Other matching Ethernet interfaces receive 1500. No other configuration fields
change.

Contributions are considered in this order:

| Order | Rule |
| --- | --- |
| 1 | Higher numeric `priority` first. Static policy fields default to 100. |
| 2 | For equal priorities, the most specific selector field wins: `name`, then `mac`, `pci_path`, `driver`, and `type`. |
| 3 | For equal priority and specificity, the policy name sorts first in bytewise lexical order. |
| 4 | For a remaining tie, the application-supplied contribution key sorts first in bytewise lexical order. |

Specificity uses the highest-ranked field present in the selector, not the
number of fields. Every selector field must still match.

[Directory precedence](policies.md#policy-search-path) happens before this step:
only the selected definition of each policy name contributes.

## Combine fields

Scalar values, such as `mtu` and `enabled`, take the first value in precedence
order. Mappings merge recursively, so policies setting different fields under
`ipv4` can both contribute.

Lists form an ordered union across contributions. IPv4 addresses are identified
by their address and prefix length; the first occurrence keeps its position and
attributes. Other lists deduplicate identical elements. Fields omitted by every
contribution retain their observed values.

An explicitly configured list replaces the observed list after the contributions
have been combined. In particular, setting `ipv4.addresses` can remove existing
addresses. Read [IPv4 address behavior](ipv4.md#existing-addresses) before applying
an address policy.

## Review a plan

When contributions disagree about a scalar or the attributes of the same IPv4
address, the default behavior selects the winning value and records a
`ValueConflict` diagnostic with the competing values. The MTU example above
therefore reports a conflict for `eth0`. Applications can set
`ConflictPolicy::Reject` to return an error instead of a plan when values conflict.
This is a library option, not a YAML policy field.

An unmatched selector produces an `UnmatchedPolicy` diagnostic and no operations
for that selector. Other matching contributions can still produce a plan.
Invalid contributions fail reconciliation even when their selectors match no
device.

A plan contains field changes, ordered backend operations, diagnostics, and the
contribution keys responsible for changes and list elements. Applications can
render it as text or JSON with `render_text` or `render_json`, then pass its
`diff()` to the backend's `dry_run` method. Inspect that report before applying:
fields accepted by the schema can still target an
[unsupported device or operation](../reference/support.md#supported-changes).
