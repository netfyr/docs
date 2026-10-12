# IPv4 addresses

Declare addresses as a list under `ipv4.addresses`:

```yaml
--8<-- "addresses.yaml"
```

Each `ip` value needs an IPv4 address and a prefix length between 0 and 32.

The first entry is the primary source address.
Each entry may also include `valid_lft` and `preferred_lft`, expressed as integer
seconds.

The IPv4 schema has no gateway, route or DNS fields yet.
See [dynamic providers](providers.md) for DHCP declarations and
the [field reference](../reference/fields.md) for each address property.
