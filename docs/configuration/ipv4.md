---
description: Declare IPv4 addresses and lifetimes, preserve existing addresses, and understand address reconciliation limits.
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

When any matching contribution sets `ipv4.addresses`, the
[merged list](reconciliation.md#combine-fields) becomes the complete desired IPv4
address list for that interface. Observed addresses missing from it are scheduled
for removal.

Omit `ipv4.addresses` to leave existing addresses unchanged. An explicit
`addresses: []` requests an empty list when no other matching contribution
supplies addresses. It does not erase addresses contributed by other policies:
their lists are combined before comparison with the observed state.

Changing the primary address or reordering addresses within a group can require
removing and re-adding that group's addresses. Review the operations in the plan;
this can interrupt traffic using those addresses.

## Address lifetimes

Each entry may include `valid_lft` and `preferred_lft`, expressed as integer
seconds. Reconciliation and the backend require:

| Property | Accepted value | Default when omitted |
| --- | --- | --- |
| `valid_lft` | 1 through 4294967295 | Forever |
| `preferred_lft` | 0 through `valid_lft` | The valid lifetime |

The value 4294967295 represents forever. A preferred lifetime of 0 deprecates an
address; a valid lifetime of 0 is rejected for an address to add or replace.
These execution constraints are stricter than the integer types in the
[state schema](../reference/fields.md#ipv4).

## Planning limits

Managing an address list requires a complete IPv4 observation. Reconciliation
also rejects observed peer addresses, non-global scopes, and kernel address
groupings it cannot safely express. If a rebuild would discard flags on a
retained address that cannot be restored, it returns an error instead of a plan.
An MTU-only policy that omits the address list does not require rebuilding or
validating those addresses.

The IPv4 schema has no gateway, route or DNS fields yet.
See [dynamic providers](providers.md) for DHCP declarations and
the [field reference](../reference/fields.md) for each address property.
