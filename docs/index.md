---
title: Linux network configuration
description: Define Linux network configuration in YAML, understand how policies merge, and check current netfyr support.
---

# Linux network configuration {#netfyr}

Each netfyr policy selects an interface and describes its configuration in YAML.

The core libraries load and validate policies, merge their contributions against
observed network state, and build a plan. The Linux backend can query interfaces
and apply MTU, administrative-state, and IPv4 address changes to existing
Ethernet and veth interfaces.

These features are available through Rust libraries. The end-user command-line
tool is still in development. See [current support](reference/support.md) for
the available operations and their limits.

[Start with a policy](getting-started.md), then read about
[policy files](configuration/policies.md),
[how policies combine](configuration/reconciliation.md), and
[IPv4 addresses](configuration/ipv4.md).
The [field reference](reference/fields.md) lists accepted values and read-only
properties.

[Source code](https://github.com/netfyr/netfyr)
