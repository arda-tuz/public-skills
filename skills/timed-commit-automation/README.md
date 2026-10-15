# timed-commit-automation

A Claude Code skill that moves a finished project from one GitHub repository to another as a calendar of meaningful commits. A Claude Code cloud routine pushes each commit on its planned day, at the real time, authored by your own GitHub account.

- **Plain-language deadlines in, reviewed calendar out.** "Backend and frontend by 19 November, everything by 1 December" becomes a commit list with dates that you approve or change. By default there is at most one commit per day, and only as many commits as the project has natural units.
- **Never backdated.** Each commit is created at the moment it is pushed.
- **Nothing extra in the destination.** Its files are byte-identical to the source. The calendar, the per-deadline progress reports and the engine stay in the source repository's `timed-commit-automation-skill/` folder. Commits carry no co-author or tool trailers, and CI configuration arrives with the last commit, so CI never runs on an unfinished project.
- **Self-healing.** Progress is read from the destination itself, missed runs are caught up in order, manual changes in the destination stop the routine instead of being overwritten, and failed runs open an issue in the source repository.

## Requirements

- Claude Code signed in with a claude.ai plan that includes cloud sessions and routines
- `git`, `python3` 3.9 or newer, and `gh` signed in with access to both repositories
- GitHub access for cloud sessions: `/web-setup`, or the Claude GitHub App on both repositories

## Install

See the [installation guide](../../README.md#install) of this repository and use the Claude Code instructions with the skill name `timed-commit-automation`. User level is the usual choice.

## Use

```text
/timed-commit-automation owner/private-repo owner/public-repo backend done by 19 November, everything by 1 December
```

Installed as a plugin, the command is `/timed-commit-automation:timed-commit-automation`.

The skill clones both repositories, inspects the project, drafts the calendar and shows it for review. After your approval it installs the calendar, pushes the commits already due and creates the cloud routine. Run it again later to check the status or change the plan.

## How it works

`scripts/tca.py` is the engine; the agent never runs git against the destination itself.

| Command | Purpose |
|---|---|
| `inspect` | facts about both repositories, for planning |
| `plan` | validate and schedule a draft calendar, write `review.md` and a preview |
| `install` | save the calendar and the engine in the source repository, push due commits |
| `run` | push due commits and record progress (what the routine runs twice a day) |
| `status`, `export`, `routine` | progress summary, editable copy of the installed calendar, routine configuration |

A date without a time means "in the destination before that day starts", so "12 December" means pushed by 11 December 23:59. Every deadline also keeps one spare day.

## Test

```bash
scripts/e2e_test.sh
```

The end-to-end test uses local bare repositories as stand-ins for GitHub and simulates cloud routine runs. It covers planning, installing, catching up, re-planning, source changes, drift, failure issues and the final state.
