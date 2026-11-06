# Session plan and responsibility

Implementation/check records begin on 2026-10-22; the garden-menu update is
recorded on 2026-10-26. The table below maps the work areas to the team's
**current study and defense leads**, as specified in
[PACMAN_TEAM_PARTS.md](../PACMAN_TEAM_PARTS.md). It does not assign historical
implementation authorship.

| Order | Deliverable | Acceptance gate | Study/defense lead |
| --- | --- | --- | --- |
| 1 | Inspect PDF and original wheel | Public API, wall encoding and original artifact hashes understood | Both; mewaysi leads generator details |
| 2 | Explain modular boundaries | Configuration, model, maze and score-store roles are clear | Both |
| 3 | Review generator adapter | Direct unchanged-wheel import, reciprocal walls, safe center/corners | mewaysi |
| 4 | Review run rules | Ten levels, chase/flee, scoring, lives and pause timers | mewaysi |
| 5 | Review complete window flow | Main menu, play, pause, finish, name entry, scores and instructions | mal-jama |
| 6 | Demonstrate review tools | F1 tools exercise progression, loss, powers and movement | mewaysi; both demonstrate through the UI |
| 7 | Verify and investigate failures | Required lint, assigned tests and headless diagnostics | Both, following the test split |
| 8 | Package and document | Linux archive, controls, dependencies and repeatable build | mal-jama |
| 9 | Prepare joint defense | Explain shared boundaries and perform small practice changes | Both |
| 10 | Publish free unlisted/private game | Authorized upload, verified URL and downloaded-build check | mal-jama leads; both validate |

Shared APIs connect the application and renderer to the gameplay model.
Cross-part changes should identify the affected interface and be checked by
both members before release. Assigned file lists and test subsets are linked
from the team document rather than inferred from file names or past dates.

Definition of local completion: source launch accepts one config argument;
the real wheel generates and validates every level; gameplay and menus work;
expected failures remain readable; required lint and developer tests pass;
the standalone build launches and exercises a maze; original artifacts remain
unchanged; documentation names genuine remaining external actions.

Full submission completion additionally requires joint defense preparation,
native desktop review and a verified public-platform URL with free
unlisted/private access. An authorized team member must complete the upload
and downloaded-build check; a local archive alone does not establish publication.
