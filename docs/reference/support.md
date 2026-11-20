---
description: Current netfyr library capabilities, supported Linux network changes, and limits of dry-run and apply.
---

# Current support

netfyr currently provides Rust libraries for policy loading, reconciliation, and
Linux network access. The end-user command-line tool and dynamic provider
execution are still in development. These guides describe the core revision
linked from the [state field reference](fields.md).

## Library workflow

| Library | Available behavior |
| --- | --- |
| `netfyr-state` | Represent observed and desired state, decode YAML with schemas, and validate field values. |
| `netfyr-policy` | Load files, directories, or ordered directory tiers; produce static state and separate provider declarations. |
| `netfyr-reconcile` | Bind contributions to observed interfaces, merge fields, and produce a plan with diagnostics and provenance. |
| `netfyr-backend` | Query a Linux network namespace, preview explicit operations, and apply supported changes over netlink. |

An application loads policies, calls `produce()` for their static contributions,
and supplies those contributions with unique keys to `reconcile()`, together
with a backend observation. It reviews the resulting plan and calls
`dry_run(plan.diff())` before deciding whether to call `apply(plan.diff())`.
Producing or reconciling a policy does not apply it or execute its providers.

Build the library API reference with `make docs` in the
[core checkout](https://github.com/netfyr/netfyr). Open
`target/doc/netfyr_state/index.html` and use the Crates sidebar to select a library.

## Supported changes

The current backend modifies existing Ethernet and veth interfaces. veth
interfaces use the device type `ethernet`.

| Operation | Support |
| --- | --- |
| Query interfaces and IPv4 addresses | Available in the backend's selected network namespace. IPv4 inventories cover Ethernet and veth interfaces; other interface types are observed read-only. Diagnostics report incomplete information. |
| Set `mtu` | Available, subject to schema limits and kernel or device restrictions. |
| Set `enabled` | Available; changes the administrative up/down state. It does not guarantee carrier or connectivity. |
| Add, remove, or replace IPv4 addresses | Available through explicit address operations, including address lifetimes and ordered group changes. |
| Set `ethernet.speed`, `ethernet.duplex`, or `ethernet.autoneg` | These are read-only observation fields. Policies cannot set them. |
| Create or remove interfaces | Not implemented. A policy can only configure an interface that already exists. |
| Configure routes, gateways, DNS, or IPv6 addresses | Not implemented. DHCPv6 and RA declarations do not enable IPv6 configuration. |

Review the backend's side-effect diagnostics before applying MTU or
administrative-state changes. An MTU below 1280 disables IPv6 and removes its
addresses. Disabling an interface removes its IPv4 routes and, unless
`keep_addr_on_down` is set, its IPv6 addresses. These kernel effects can occur
even though the backend cannot configure those routes or IPv6 addresses.

The [field reference](fields.md) describes schema acceptance and writability.
A writable field is not a promise that the current backend can apply it.

Each `NetlinkBackend` instance is bound to one network namespace. Opening the
current namespace does not require the privilege needed to enter another one;
network writes still require permission in the selected namespace. Querying or
applying through the library does not require a netfyr daemon.

## Preview and apply

A dry run queries the network and validates operations against projected state
without writing. It reports operations that would write, be skipped, or fail.
It cannot guarantee that a later kernel write will succeed, including whether
the caller has permission to make the change.

Plans target an observed interface identity, including its namespace, index,
and generation. The backend rechecks the target and address-group preconditions;
if the state has changed, query again and rebuild the plan.

Apply reports succeeded, failed, and skipped operations separately. A failed
operation blocks dependent operations, while independent operations can
continue. Changes already made are not automatically rolled back.

Dropping an apply future requests cancellation. An operation already in progress
may still write or complete without being reported. After an interruption or an
`OutcomeUnknown` result, query the network before retrying or attempting to undo
the change. See [troubleshooting](../troubleshooting.md) for these reports and
other errors.
