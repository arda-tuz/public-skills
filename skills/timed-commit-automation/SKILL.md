---
name: timed-commit-automation
description: Migrates a finished project from a source GitHub repository into a destination repository as a calendar of meaningful commits that a Claude Code cloud routine creates and pushes on their planned days, authored by the user's own GitHub account and never backdated. Turns plain-language deadlines such as "backend and frontend by 19 November, everything by 1 December" into a commit calendar the user reviews, keeps the calendar and per-deadline progress reports only in the source repository, and checks, re-plans or repairs a running migration. Use when the user wants to move, port or gradually publish code from one repository to another over days or weeks, or asks for timed, scheduled or drip-fed commits.
argument-hint: "[source-repo] [destination-repo] [deadlines in plain language]"
metadata:
  version: "1.0.0"
---

# Timed commit automation

Moves a finished project from a **source** repository into a **destination** repository as a calendar of commits that a cloud routine pushes on their planned days. You analyze the project, design the commits and keep the user in the loop. The engine does every git operation and every date calculation:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/tca.py <command> ...
```

Its last stdout line is one JSON object (`status`, and `problems` / `questions` / `warnings` lists where relevant); exit code 0 means success. For `plan`, only `status: valid` exits 0; `questions` and `invalid` exit 1.

## Rules

- Never commit to, push to or rewrite the destination yourself, and never use `--date`, `cherry-pick`, `rebase` or `filter-repo` for this task. The engine creates each destination commit when it pushes it, authored and committed by the calendar's `author`, unsigned, without trailers.
- Never write or edit project code: destination files are byte-identical to the source.
- Nothing from this skill may reach the destination. Its files live only in the source repository's `timed-commit-automation-skill/` folder: `calendar.md` (the calendar and progress), `progress-report/` (one report per deadline) and `tca.py` (the engine copy the routine runs). The engine keeps that folder out of every destination commit; commit messages must not mention the tooling either. The engine's own commits in the source (calendar updates) also use the calendar's `author`.
- Get the user's explicit approval before `install` and before creating the routine.
- Let the engine compute dates. Your part is turning the user's words into ISO dates.

## Workflow

If `inspect` reports `"calendar_installed": true` for the source, the user is checking, changing or repairing a running migration: follow [references/operations.md](references/operations.md) instead. (Look at `inspect`, not at the working tree: the engine never moves the clones' local branches.)

Copy this checklist and keep it updated:

```
- [ ] 1. Inputs collected
- [ ] 2. Repositories cloned and inspected
- [ ] 3. Deadlines and scopes interpreted
- [ ] 4. Draft calendar written
- [ ] 5. Plan valid
- [ ] 6. Calendar approved by the user
- [ ] 7. Installed
- [ ] 8. Routine created and verified
- [ ] 9. Handed over
```

### 1. Collect inputs

Required: the source repository, the destination repository, and when the whole project must be in the destination. Optional: intermediate deadlines with a scope ("the backend by ..."), a start date, days to avoid, weekdays only, commits per day, the commit message language. Ask once, and only for missing required inputs; optional ones take their defaults, which the review lists.

### 2. Clone and inspect

Needs `git`, `python3` 3.9 or newer, and `gh` signed in with access to both repositories: run `gh auth status` (without `gh`, clone with `git clone https://github.com/OWNER/REPO.git`). Clone into a new folder, and repeat its absolute path in every later command (shell variables do not survive between commands):

```bash
WORK="$(mktemp -d "${TMPDIR:-/tmp}/tca.XXXXXX")" && echo "$WORK"
gh repo clone OWNER/SOURCE "$WORK/source" -- --quiet
gh repo clone OWNER/DESTINATION "$WORK/target" -- --quiet
python3 ${CLAUDE_SKILL_DIR}/scripts/tca.py inspect --source "$WORK/source" --target "$WORK/target"
```

`inspect` reports today's date and timezone, a suggested commit author (from `gh api user`, otherwise from the source history; confirm the latter in the review), the source tree by folder, the destination's existing files, AI-tool files such as `CLAUDE.md`, and anything GitHub would reject. Then read the project (manifests, entry points, imports) until you know its parts and what depends on what.

### 3. Interpret deadlines and scopes

Read [references/planning.md](references/planning.md), then turn each request into a milestone: its deadline, the weekday the user said (if any), and path patterns for its scope. Write a deadline the way the user said it. A bare date (`"2026-12-12"`) means the work is in the destination before that day starts; the engine applies that rule itself (2026-12-11 23:59). Each milestone is a checkpoint: at its deadline the destination holds exactly the commits up to the milestone's last commit, and the engine plans every later commit after the deadline.

### 4. Write the draft calendar

Write `$WORK/draft.json` as described in [references/calendar-format.md](references/calendar-format.md). Group the files into coherent commits in their natural development order. Default size: at most one commit per day, and only as many commits as the project has natural units (a module, a layer, a feature), so a small project gets a short list and no commit is a lone trivial file. The user can ask for more or fewer. Put what you assumed or added, and why, in `notes`; put every decision only the user can make in `questions`.

### 5. Plan until valid

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/tca.py plan --draft "$WORK/draft.json" \
  --source "$WORK/source" --target "$WORK/target" --out "$WORK/preview"
```

The engine assigns the dates and checks that every file arrives, that each milestone's files arrive before its deadline, and that GitHub will accept the content. `status` is `invalid` while `problems` remain: fix each one in the draft and run `plan` again. `questions` (yours, and the engine's, such as a weekday that contradicts its date) do not stop the schedule; they lead `review.md` and block only `install`. Before showing the review, read it yourself and fix anything clearly wrong.

### 6. Review with the user

Present `$WORK/preview/review.md` in the user's language: the open questions first, then the total number of commits; each milestone with its scope, its requested deadline, the moment it must be in the destination and the commit that completes it; the commit list; the assumptions. Ask the user to answer the questions and to approve or change the calendar. Apply every answer and change to the draft (an answered question leaves `questions`), go back to step 5, and present the new review. Approval means the user accepts a review that has no open questions. [references/calendar-format.md](references/calendar-format.md) lists how to express the usual changes.

### 7. Install

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/tca.py install --draft "$WORK/draft.json" \
  --source "$WORK/source" --target "$WORK/target"
```

`install` validates and schedules again from today, so if the user approved on an earlier day, run `plan` first and confirm any dates that moved. It commits `timed-commit-automation-skill/` to the source repository's default branch and pushes every commit already due (normally commit 1, when the calendar starts today). Check `pushed_now` in the JSON and run `tca.py status --source "$WORK/source" --target "$WORK/target"`. The engine pushes from its own refs and leaves the clones' local branches alone, so inspect the destination through `origin/<branch>` or `gh api "repos/OWNER/DESTINATION/commits?per_page=1"`: author, message and date.

### 8. Create the cloud routine

The routine runs `tca.py run` twice a day in Anthropic's cloud, also while the user's computer is off.

1. Cloud sessions need GitHub access to both repositories: the user runs `/web-setup` (it uses their own `gh` login and installs nothing on the destination), or installs the Claude GitHub App on both repositories.
2. Get the exact configuration:
   ```bash
   python3 ${CLAUDE_SKILL_DIR}/scripts/tca.py routine --source "$WORK/source"
   ```
3. Invoke the `schedule` skill and ask it to create a routine with exactly these values: `name`, both `repositories`, `cron_utc` (already UTC; tell it so), `model`, `allowed_tools`, no connectors, and `prompt` verbatim. Any cloud environment works (the engine needs only `git` and `python3`), so the Default one is fine. If the `schedule` skill is not available, give the user the same values for claude.ai/code/routines.
4. Verify with the `RemoteTrigger` tool: `run` the routine once, then `list_runs` and `get_run_log`. The run must end with a JSON status of `up_to_date` or `pushed`; otherwise see [references/operations.md](references/operations.md).

### 9. Hand over

Tell the user where the calendar is (`timed-commit-automation-skill/calendar.md` in the source repository) and what the progress reports show, the next commit and its date, the routine's link, that a failed run opens an issue in the source repository, and that invoking this skill again checks status or changes the plan. Remind them not to commit to the destination by hand until the calendar is complete.
