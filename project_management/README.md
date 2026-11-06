# Project-management record

This directory contains the Pac-Man team's plan, decisions, risks and recorded
verification results. **Team members: mal-jama and mewaysi.** Record dates
identify when the checks or changes were recorded; they do not establish who
originally authored a particular file.

| Record | Purpose |
| --- | --- |
| [plan.md](plan.md) | Requirements, sequence, responsibilities and release gates |
| [progress.md](progress.md) | Actual progress against that plan |
| [decisions.md](decisions.md) | Design choices and alternatives considered |
| [risks.md](risks.md) | Concrete risks, mitigations and remaining limits |
| [acceptance_tests.md](acceptance_tests.md) | Repeatable checks and actual evidence |
| [issues.md](issues.md) | Fixed integration issues and outstanding manual tasks |
| [artifact_hashes.json](artifact_hashes.json) | Original supplied artifact SHA-256 values |
| [pacing_check.json](pacing_check.json) | Actual ten-level route traversal with unchanged countdowns |
| [screenshots/](screenshots/) | Actual rendered screens, including returning and waiting eyes |
| [visual_logging_update.md](visual_logging_update.md) | Returning eyes, separate result gardens and persistent logging integration |
| [finish_performance.json](finish_performance.json) | Measured cold/warm result-screen drawing at native/minimum sizes |

## Team organization

Current responsibilities follow
[PACMAN_TEAM_PARTS.md](../PACMAN_TEAM_PARTS.md):

| Member | Study, testing and defense lead |
| --- | --- |
| **mal-jama** | Part 2: application, UI, configuration, highscores, release and documentation |
| **mewaysi** | Part 1: engine, maze, movement, ghosts and gameplay |
| **Both** | Application/model integration, smoke checks, subject requirements and review evidence |

Members prepare their assigned explanations and tests, then review shared
interfaces together. These are current responsibilities, not a reconstructed
individual authorship history. No unrecorded peer sign-off or deployment is
claimed. Native desktop review and a verified free unlisted/private platform
upload remain release gates. Final test/build results are tracked in the
acceptance record.
