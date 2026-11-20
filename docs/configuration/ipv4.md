---
description: IPv4 address lists, lifetimes, and the effects of applying an address policy.
---

# IPv4 addresses

Declare addresses as a list under `ipv4.addresses`:

```yaml
--8<-- "addresses.yaml"
```

Each `ip` value needs an IPv4 address and a prefix length between 0 and 32.

Within each subnet and prefix group, the first address is primary. Keep the
intended primary address first when listing several addresses in the same group.

## Existing addresses

If any matching contribution sets `ipv4.addresses`, netfyr uses the
[merged list](reconciliation.md#combine-fields) as the interface's complete IPv4
address list. It plans to remove any observed addresses missing from that list.

Omit `ipv4.addresses` to leave existing addresses unchanged. Use `addresses: []`
to request an empty list, provided no other matching contribution supplies
addresses. Other policies can still contribute addresses because netfyr combines
their lists before comparing the result with the observed state.

Changing the primary address or reordering addresses within a group can require
removing and re-adding that group's addresses. Review the operations in the plan;
this can interrupt traffic using those addresses.

## Address lifetimes

Each entry may include `valid_lft` and `preferred_lft` in integer seconds.
Reconciliation and the backend accept these values:

| Property | Accepted value | Default when omitted |
| --- | --- | --- |
| `valid_lft` | 1 through 4294967295 | Forever |
| `preferred_lft` | 0 through `valid_lft` | The valid lifetime |

The value 4294967295 means forever. A preferred lifetime of 0 deprecates an
address. netfyr rejects a valid lifetime of 0 when adding or replacing an address.
The [state schema](../reference/fields.md#ipv4) checks that lifetimes are integers;
reconciliation and the backend also check their ranges and order.

## Planning limits

netfyr needs a complete IPv4 observation to manage an address list. Reconciliation
rejects observed peer addresses, non-global scopes, and kernel address groupings
it cannot safely express. It also rejects a rebuild that would lose flags it
cannot restore on an address you want to keep. A policy that only changes the MTU
can omit the address list and leave those addresses alone.

The IPv4 schema has no gateway, route or DNS fields yet.
See [dynamic providers](providers.md) for DHCP declarations and
the [field reference](../reference/fields.md) for each address property.
