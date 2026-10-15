# Running migrations: status, changes and repairs

## Contents

- Setup
- Status
- Change the plan
- The source changed
- A manual commit in the destination
- Failed runs
- Pause, stop and finish
- Troubleshooting

## Setup

Clone both repositories into a new folder, as in SKILL.md step 2. Every command below reads the installed calendar from the source repository's remote default branch.

## Status

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/tca.py status --source "$WORK/source" --target "$WORK/target"
```

It reports commits pushed and total, the next commit, each milestone's status (`on track`, `behind schedule`, `reached`, `missed`) and warnings. The same is visible to the user in `timed-commit-automation-skill/calendar.md` in the source repository, and per deadline in `progress-report/`. For the routine itself: `RemoteTrigger` `list`, then `list_runs` and `get_run_log`.

## Change the plan

1. Export the installed calendar, with its recorded state:
   ```bash
   python3 ${CLAUDE_SKILL_DIR}/scripts/tca.py export --source "$WORK/source" --out "$WORK/replan.json"
   ```
2. Edit only commits that are not pushed yet (they have no `target_sha`). Keep `pushed_at`, `target_sha`, `reached_at`, `reached_by` and pins; the engine recomputes every unpinned `date` and `ci_from`.
   - A changed deadline: update the milestone's `weekday` (or remove it) and add the user's new words to its `request`.
   - Update every `note` that no longer holds.
3. Run `plan`, review with the user and `install`, as in SKILL.md steps 5 to 7. Pushed commits are locked: the engine refuses a plan that changes them. Unpinned dates are recomputed from today, and the review marks each moved date with "(was ...)": confirm those with the user, and pin a commit to keep its old date. Progress report files are named after their deadline, so a changed deadline renames its report. The routine needs no change.

## The source changed

`status` and every run warn "the source branch changed after this calendar was planned" when the source repository has new commits; those changes are not migrated by themselves. To include them: export, `plan --repin`, and for each file the source deleted but the destination already has, add it to a later commit's `remove`; then review and `install --repin`. Pushed commits keep their content; the remaining commits carry the new versions.

## A manual commit in the destination

The routine stops with "the destination has commits that are not in the calendar" and pushes nothing. Either revert the manual commits in the destination (a revert commit is fine; the routine continues once the files match the last pushed calendar commit again), or move the change into the source repository, revert it in the destination and re-plan with `--repin`. Never force-push.

## Failed runs

A failed run opens an issue titled "timed-commit-automation: scheduled run failed" in the source repository (later failures add comments), and the next successful run closes it. Everything due is pushed by the next successful run, in order. With two runs a day and one spare day before every deadline, a day of failures does not miss a deadline.

## Pause, stop and finish

- Pause or resume: the routine's switch at claude.ai/code/routines, or `RemoteTrigger` `update` with `{"enabled": false}`.
- After status `complete`, delete the routine at claude.ai/code/routines (it cannot be deleted through `RemoteTrigger`). Work in the destination after completion is never treated as drift.
- `timed-commit-automation-skill/` can stay in the source as a record; remove it only if the user asks.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| "no clone of the destination ... was found" | the routine lacks the destination repository: add it |
| clone or push fails with 403 or "repository not found" | cloud GitHub access: `/web-setup`, or the Claude GitHub App on that repository |
| push rejected on the destination | branch protection or a ruleset on its branch: allow the user's account to push |
| commits arrive but the calendar does not update, runs end with "refused the push" for the source | the source's default branch is protected: allow the user's account to push to it (the calendar is committed there) |
| push rejected for `.github/workflows` files | the `gh` token lacks the `workflow` scope: `gh auth refresh -s workflow`, then `/web-setup` |
| no runs appear | routine disabled, GitHub connection expired (runs are skipped for 72 hours, then the routine turns off), or usage limits reached |
| "the destination history was rewritten" | someone force-pushed the destination: restore its history, or plan a new calendar |
| commits marked "Unverified" | the user enabled vigilant mode; commits are unsigned by design |
