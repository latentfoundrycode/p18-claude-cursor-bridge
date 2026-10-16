# Open list (fixture)

A small open list for the status-line cases; only the three tables are read.

## Product types

| Key | Name | Definition | Workflow name | Default traits | Written | Planned |
|---|---|---|---|---|---|---|
| host-extension | Host extension | Runs inside another application | Host Extension Development | installable | yes | — |
| web-app | Web app | Used in a browser | Web App Development | has-screens | yes | — |
| library | Library | Included by other programs | Library Development | — | no | — |

## Sub-types

| Key | Name | Of type | Definition | Sub-workflow name | Default traits | Written | Planned |
|---|---|---|---|---|---|---|---|
| claude-code-extension | Claude Code extension | host-extension | Runs inside Claude Code | Claude Code Extension | installable | yes | — |
| browser-extension | Browser extension | host-extension | Runs inside a browser | Browser Extension | installable | yes | — |
| local-web-app | Local web app | web-app | Opened at a local address | Local Web App | installable | no | — |

## Traits

| Key | Name | Definition | Written | Planned |
|---|---|---|---|---|
| has-screens | Has screens | Shows a visual interface | yes | — |
| installable | Installable | Delivered as something installed | yes | — |
| spends-money | Spends money | Its actions cost money | no | — |
