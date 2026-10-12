# State fields

Set writable fields in a policy. `type` is also accepted as device metadata; [`match.type`](../configuration/policies.md) selects an interface. Other read-only fields describe observed state.

Each download describes one group of state fields. See [policy files](../configuration/policies.md) for the full policy syntax and [dynamic providers](../configuration/providers.md) for provider parameters.

## Common fields

Fields common to every netfyr network device\. Always validated\.

Unlisted fields are rejected in this schema fragment.

| Field | Type | Writable | Constraints | Description |
| --- | --- | --- | --- | --- |
| `type` | string | No | \- | Technology type \(e\.g\. "ethernet"\)\. |
| `name` | string | No | \- | Interface name\. |
| `mac` | string | No | \- | Hardware MAC address\. |
| `carrier` | boolean | No | \- | Whether the link has carrier\. |
| `driver` | string | No | \- | Kernel driver\. |
| `enabled` | boolean | Yes | \- | Admin up/down\. |
| `mtu` | integer | Yes | Minimum: 68; Maximum: 65535 | Maximum transmission unit in bytes\. |

[Download base schema](schemas/base.json)

## Ethernet

Ethernet link properties\. Validated when the state carries an 'ethernet' sub\-object\.

Device type: ethernet.

Unlisted fields are rejected in this schema fragment.

| Field | Type | Writable | Constraints | Description |
| --- | --- | --- | --- | --- |
| `ethernet.speed` | integer | No | \- | Link speed in Mbps\. |
| `ethernet.duplex` | string | No | One of: "full", "half", "unknown" | Link duplex mode\. |
| `ethernet.autoneg` | boolean | No | \- | Whether auto\-negotiation is enabled\. |

[Download ethernet schema](schemas/ethernet.json)

## IPv4

IPv4 configuration\. Validated when the state carries an 'ipv4' sub\-object\.

Unlisted fields are rejected in this schema fragment.

| Field | Type | Writable | Constraints | Description |
| --- | --- | --- | --- | --- |
| `ipv4.addresses` | array | Yes | \- | IPv4 addresses in order; the first is the primary source address\. |
| `ipv4.addresses[]` | object | Yes | No additional fields |  |
| `ipv4.addresses[].ip` | string | Yes | Required; Format: ipv4\-cidr | Address with prefix length \(CIDR\)\. |
| `ipv4.addresses[].valid_lft` | integer | Yes | \- | Address validity lifetime in seconds\. |
| `ipv4.addresses[].preferred_lft` | integer | Yes | \- | Address preferred lifetime in seconds\. |

[Download ipv4 schema](schemas/ipv4.json)

Source: [netfyr `4dbbc01e1e38`](https://github.com/netfyr/netfyr/tree/4dbbc01e1e38d9016201e2df25601c12936f1606/crates/netfyr-state/schemas).
