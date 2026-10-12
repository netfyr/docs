# Configuration errors

Validation errors include field paths, including positions in address lists.
A file can report several errors at once.

| Problem | What to check |
| --- | --- |
| Unknown field | Check the spelling and location against the [field reference](reference/fields.md). Configuration fields belong directly beside `match`, not inside `state`. |
| Read-only field | Remove observation fields such as `carrier` from the policy. To select by driver or MAC address, put the value under `match`. |
| MTU out of range | Use an integer between 68 and 65535. |
| Invalid IPv4 address | Include an IPv4 address and prefix, such as `192.0.2.10/24`. |
| Wrong value type | Use `true` or `false` for booleans and unquoted numbers for integer fields. |
| Missing match | Give an explicit policy at least one field under `match`, such as `name`. |
| Duplicate policy name | Choose unique explicit names, or different filenames for unnamed policies. |
| More than one YAML document | Replace `---`-separated documents with a single list of mappings. |

If you cannot resolve an error, include the configuration and full message
when [reporting a problem](https://github.com/netfyr/netfyr/issues). Remove
private addresses or other details you do not want to share.
