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

Unknown DHCPv4 parameters are rejected. Static `ipv4.addresses` and `ipv4.dhcp4`
can appear in the same policy; the loader keeps the static configuration and
provider declaration separate.

DHCP declarations carry a default priority of 50. A policy's `priority` overrides
only its static contribution; it does not change this provider priority.
Reconciliation does not start DHCP or turn a declaration into a lease.

## IPv6 declarations

netfyr also accepts declarations under `ipv6.dhcp6` and `ipv6.ra` for DHCPv6
and router advertisements.
Their parameter maps have no defined fields yet.
DHCPv6 declarations use priority 50, and router-advertisement declarations use
priority 25. Neither provider runs yet, and the current backend does not apply
IPv6 address changes.
