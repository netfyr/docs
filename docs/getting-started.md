# Write a policy

Save this example as `office.yaml`:

```yaml
--8<-- "office.yaml"
```

`name` identifies the policy; `match.name` selects the interface. Replace `eth0`
with your interface name and `192.0.2.10/24` with your address and prefix.
The policy requests an enabled interface with a 1500-byte MTU.

Put configuration fields beside `match`. Omit fields you do not need to set.

To set only the MTU, save this as `uplink.yaml`:

```yaml
--8<-- "uplink.yaml"
```

This policy gets its name, `uplink`, from the filename. See
[policy files](configuration/policies.md) for multiple policies and other ways
to select an interface.
