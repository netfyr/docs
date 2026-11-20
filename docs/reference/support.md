---
description: What netfyr can query and change, and what to check before applying a plan.
---

# Current support

netfyr is available as Rust libraries for loading policies, planning changes,
and accessing Linux networks. The command-line tool and code to run dynamic
providers are still in development. These guides cover the core revision linked
from the [state field reference](fields.md).

## Library workflow

| Library | Purpose |
| --- | --- |
| `netfyr-state` | Represent observed and desired state, decode YAML with schemas, and validate field values. |
| `netfyr-policy` | Load files, directories, or ordered directory tiers; produce static state and separate provider declarations. |
| `netfyr-reconcile` | Combine contributions for matching interfaces, plan changes, and report conflicts and the source of each change. |
| `netfyr-backend` | Query a Linux network namespace, preview explicit operations, and apply supported changes over netlink. |

Call `produce()` on loaded policies to separate their static contributions from
provider declarations. Give each static contribution a unique key and pass them
to `reconcile()` with a backend observation. Review the plan, then call
`dry_run(plan.diff())` before deciding whether to call `apply(plan.diff())`.
Producing or reconciling a policy does not change the network or run its providers.

Build the library API reference with `make docs` in the
[core checkout](https://github.com/netfyr/netfyr). Open
`target/doc/netfyr_state/index.html` and use the Crates sidebar to select a library.

## Supported changes

The current backend modifies existing Ethernet and veth interfaces. veth
interfaces use the device type `ethernet`.

| Operation | Support |
| --- | --- |
| Query interfaces and IPv4 addresses | Reads the selected network namespace. IPv4 inventories cover Ethernet and veth interfaces. The backend observes other interface types but cannot change them. Diagnostics identify incomplete information. |
| Set `mtu` | Supports values allowed by the schema, kernel, and device. |
| Set `enabled` | Brings an interface administratively up or down. Bringing it up does not guarantee carrier or connectivity. |
| Add, remove, or replace IPv4 addresses | Supports explicit address operations, including lifetimes and ordered changes within address groups. |
| Set `ethernet.speed`, `ethernet.duplex`, or `ethernet.autoneg` | These are read-only observation fields. Policies cannot set them. |
| Create or remove interfaces | Not implemented. A policy can only configure an interface that already exists. |
| Configure routes, gateways, DNS, or IPv6 addresses | Not implemented. DHCPv6 and RA declarations do not enable IPv6 configuration. |

Check the backend's diagnostics before changing an MTU or bringing an interface
down. An MTU below 1280 disables IPv6 and removes its addresses. Bringing an
interface down removes its IPv4 routes and, unless `keep_addr_on_down` is set,
its IPv6 addresses. The kernel makes these changes even though the backend
cannot configure those routes or IPv6 addresses.

The [field reference](fields.md) tells you which fields a policy can set.
The backend must also support the device and the requested operation.

Each `NetlinkBackend` instance uses one network namespace. Opening the current
namespace needs no extra privilege; entering another namespace does. Writes
require permission in the selected namespace. You can query and apply through
the library without a netfyr daemon.

## Preview and apply

A dry run queries the network and checks each operation against the state the
preceding operations would leave behind, without making changes. It reports
which operations would write, be skipped, or fail. A later write can still fail,
including when the caller lacks permission to make the change.

Plans identify an interface by its namespace, index, and generation, along with
other observed identity fields. The backend rechecks that identity and the
expected state of each address group. If either has changed, query again and
rebuild the plan.

The apply report lists which operations succeeded, failed, or were skipped.
When an operation fails, the backend skips operations that depend on it and
continues with independent ones. It does not roll back changes already made.

Dropping an apply future requests cancellation. An operation in progress may
still write or finish without reporting its result. After an interruption or an
`OutcomeUnknown` result, query the network before retrying or undoing the change.
See [troubleshooting](../troubleshooting.md) for help with these reports and
other errors.
