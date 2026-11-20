---
description: Write your first netfyr policy to select an interface and declare its network configuration.
---

# Write a policy

The examples below can be loaded with the `netfyr-policy` Rust library. Saving
a file does not apply it to the network; the command-line tool is still in
development. See [current support](reference/support.md) for the library workflow.

Save this example as `office.yaml`:

```yaml
--8<-- "office.yaml"
```

`name` identifies the policy; `match.name` selects the interface. Replace `eth0`
with your interface name and `192.0.2.10/24` with your address and prefix.
The policy requests an enabled interface with a 1500-byte MTU.

If applied, the [merged address list](configuration/ipv4.md#existing-addresses)
replaces the interface's existing IPv4 addresses. Include every address you
intend to keep, or omit `ipv4.addresses` to leave addresses unchanged.

Put configuration fields beside `match`. Omit fields you do not need to set.

To set only the MTU, save this as `uplink.yaml`:

```yaml
--8<-- "uplink.yaml"
```

This policy gets its name, `uplink`, from the filename. See
[policy files](configuration/policies.md) for multiple policies and other ways
to select an interface, and [reconciliation](configuration/reconciliation.md)
for what happens when several policies match.
