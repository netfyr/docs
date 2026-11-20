---
description: Declare DHCP and IPv6 router-advertisement providers in netfyr policies. Provider execution is not available yet.
---

# Dynamic providers

A policy can declare a dynamic provider alongside static configuration.
netfyr validates these declarations but cannot run the providers yet.

## DHCPv4

Place DHCPv4 parameters under `ipv4.dhcp4`:

```yaml
--8<-- "dhcp.yaml"
```

Both parameters are optional; `dhcp4: {}` uses neither.

| Parameter | Accepted value |
| --- | --- |
| `send-hostname` | Boolean |
| `route-metric` | Integer greater than or equal to 0 |

The loader rejects unknown DHCPv4 parameters. Static `ipv4.addresses` and
`ipv4.dhcp4` can appear in the same policy; the loader keeps the static
configuration and provider declaration separate.

DHCP declarations have a default priority of 50. The policy's `priority` applies
only to its static fields, so it leaves this provider priority unchanged.
Reconciliation does not start DHCP or acquire a lease.

## IPv6 declarations

Declare DHCPv6 under `ipv6.dhcp6` and router advertisements under `ipv6.ra`.
Their parameter maps have no defined fields yet. DHCPv6 declarations use
priority 50, and router advertisements use 25. Neither provider runs yet, and
the current backend cannot apply IPv6 address changes.
