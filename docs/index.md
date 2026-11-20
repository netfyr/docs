---
title: Linux network configuration
description: Configure Linux network interfaces with netfyr YAML policies.
---

# Linux network configuration {#netfyr}

A netfyr policy selects one or more interfaces and describes their configuration
in YAML.

The Rust libraries load and validate policies, combine their settings, and plan
changes against the current network state. The Linux backend can query existing
Ethernet and veth interfaces, change their MTU, bring them up or down, and manage
their IPv4 addresses.

The command-line tool is still in development. See
[current support](reference/support.md) for the available library operations
and their limits.

[Start with a policy](getting-started.md), then read about
[policy files](configuration/policies.md),
[how policies combine](configuration/reconciliation.md), and
[IPv4 addresses](configuration/ipv4.md).
The [field reference](reference/fields.md) lists accepted values and read-only
properties.

[Source code](https://github.com/netfyr/netfyr)
