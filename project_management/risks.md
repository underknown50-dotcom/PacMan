# Risks and mitigations

| Risk | Mitigation / current limit |
| --- | --- |
| Assigned generator is changed accidentally | Read-only inspection; original SHA-256 record; identical vendor wheel; final before/after comparison required. |
| Wrong public constructor example | Use verified size tuple; real-wheel integration tests exercise it. |
| Even-size center is blocked by `42` | Select nearest reachable center without altering any walls. |
| Corners or items become unreachable/overlap | Use connected topology and distinct reserved corner-region placements. |
| Invalid masks, open borders or asymmetric walls | Reject generation with a visible safe error instead of inventing a fallback maze. |
| Generator reseeds global random | AI and placement use separate Random instances. |
| Frame timing causes wall crossing or repeated damage | Fixed simulation steps, graph-edge travel, continuous positions, inactive eaten ghosts and respawn protection. |
| Pause leaves hidden clocks running | One model update boundary freezes all gameplay timers. |
| Short or invalid config creates fewer than ten levels | Repair/pad with warnings; validate numeric types including bool rejection. |
| Score path escapes or install directory is read-only | Safe path validation, symlink escape checks and frozen user-data redirection. |
| Corrupt/unwritable score file | Skip invalid records, retain memory, show warning, atomic temp/replace save and tests for failures. |
| Two application instances save simultaneously | Saves are atomic but not merged; last writer wins. Concurrent leaderboard editing is outside current scope. |
| pygame feature exceeds MLX equivalents | Small central facade and documented operation mapping; shapes are rasterized in application pixel code. |
| Headless tests miss native desktop behavior | Dummy-driver tests verify lifecycle/rendering; the team still needs a real desktop keyboard and visual check. |
| New glibc build fails on older Linux | State platform target; rebuild on the oldest intended Linux distribution. No cross-platform compatibility is claimed. |
| Tests pass but long-run difficulty is unbalanced | Reviewer tools make features inspectable; human unassisted difficulty/playability tuning remains a joint team review activity. |
| A member cannot explain their assigned part or shared interfaces | Follow team_organization.md, review actual modules/tests, and practice small defense changes together. |
| Team responsibility split becomes inconsistent | Use the agreed Part 2/Part 1 assignment: mal-jama handles UI/application/services/release; mewaysi handles engine/maze/gameplay; both review integration. |
| Local release mistaken for platform publication | Explicit manual itch.io procedure; only a verified real URL closes that release gate. |

Final test/build outcomes are recorded separately in acceptance_tests.md rather
than guessed here. The supplied assignment PDF is excluded from the public
game archive; game branding and original generated artwork remain distinguishable
from that local assignment input.
