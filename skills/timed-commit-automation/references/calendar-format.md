# Draft calendar format

## Contents

- Example
- Fields
- Path patterns
- How dates are chosen
- Filled in by the engine
- Common changes

## Example

The request "all of the backend and frontend, and of the AI parts only the image processing that uses local models, done by Thursday 19 November; the whole project by 1 December" in a project with `backend/`, `frontend/` and `ai/` becomes:

```json
{
  "source": {"repo": "owner/project-dev"},
  "target": {"repo": "owner/project"},
  "author": {"name": "Ada Lovelace", "email": "1234567+ada@users.noreply.github.com"},
  "timezone": "Europe/Istanbul",
  "exclude": ["CLAUDE.md"],
  "notes": [
    "The first milestone also includes ai/common/, because the local detector imports it.",
    "Commit messages are in English."
  ],
  "questions": [
    "CLAUDE.md (notes for the AI assistant) is left out of the destination. Keep it out?"
  ],
  "milestones": [
    {
      "id": "core-and-local-vision",
      "title": "Backend, frontend and local-model image processing",
      "request": "all of the backend and frontend, and of the AI parts only the image processing that uses local models, by Thursday 19 November",
      "deadline": "2026-11-19",
      "weekday": "thu",
      "scope": ["backend/", "frontend/", "ai/vision/local/", "ai/common/"]
    },
    {
      "id": "everything",
      "title": "Whole project",
      "request": "the whole project by 1 December",
      "deadline": "2026-12-01",
      "scope": ["**"]
    }
  ],
  "commits": [
    {"message": "chore: set up project structure and tooling", "paths": [".gitignore", "package.json", "package-lock.json", "tsconfig.json"]},
    {"message": "feat(db): add schema, migrations and models", "paths": ["backend/db/", "backend/models/"]},
    {"message": "feat(api): add REST endpoints and authentication", "paths": ["backend/"]},
    {"message": "feat(ui): add app shell, routing and shared components", "paths": ["frontend/src/app/", "frontend/src/components/"]},
    {"message": "feat(ui): add dashboard and settings pages", "paths": ["frontend/"]},
    {"message": "feat(vision): add on-device inference with local models", "paths": ["ai/common/", "ai/vision/local/"]},
    {"message": "feat(ai): add cloud vision and chat assistants", "paths": ["ai/"]},
    {"message": "docs: add README, CI and deployment notes", "paths": ["**"]}
  ]
}
```

This example has no misspelled weekday and no dependency on a left-out part; [planning.md](planning.md) says how those become questions. The question keeps `install` blocked until the user answers it and you remove it. Had the request said Tuesday 19 November (`"weekday": "tue"`), `plan` would add its own question, because 2026-11-19 is a Thursday.

## Fields

| Field | Required | Meaning |
|---|---|---|
| `source.repo`, `target.repo` | yes | `owner/name`; GitHub URLs are accepted |
| `source.branch`, `target.branch` | no | default: the repository's default branch (`main` for an empty destination) |
| `author.name`, `author.email` | yes | the user's GitHub identity from `inspect`. The noreply address (`ID+login@users.noreply.github.com`) always links commits to the account and never exposes a private email |
| `timezone` | yes | IANA name; `inspect`'s timezone unless the user says otherwise |
| `schedule.start` | no | first day a commit may be planned (default: today) |
| `schedule.per_day` | no | most commits on one day (default 1) |
| `schedule.weekdays` | no | days commits may fall on, such as `["mon", "tue", "wed", "thu", "fri"]` (default: every day) |
| `schedule.skip` | no | dates without commits, `["2026-11-02"]` |
| `schedule.margin_days` | no | spare days kept before each deadline (default 1) |
| `schedule.run_times` | no | local times the routine runs (default `["10:07", "20:07"]`; all on the same minute) |
| `exclude` | no | path patterns never copied; `timed-commit-automation-skill/` is always excluded |
| `notes` | no | sentences the review and the installed calendar show: assumptions, additions and why |
| `questions` | no | decisions only the user can make, with the options; `install` refuses while any remain |
| `milestones[].id` | yes | lowercase slug; names the progress report file |
| `milestones[].title` | yes | short name shown in the calendar |
| `milestones[].request` | recommended | the part of the user's words for this milestone, in their language |
| `milestones[].deadline` | yes | `"YYYY-MM-DD"`: in the destination before that day starts. `"YYYY-MM-DDTHH:MM"`: by that moment |
| `milestones[].weekday` | if the user named one | `mon` ... `sun`; the engine checks it against the date |
| `milestones[].scope` | yes | path patterns of everything that must be in the destination by the deadline; a leading `!` leaves matching files out |
| `commits[].message` | yes | full commit message; first line at most 72 characters |
| `commits[].paths` | yes | path patterns of what the commit brings |
| `commits[].date`, `commits[].pin` | no | `"pin": true` fixes the commit to `date` |
| `commits[].remove` | no | destination paths the commit deletes (needed only after files disappear from the source, see `--repin`) |

## Path patterns

Patterns are anchored at the repository root. `backend` or `backend/` selects everything under `backend`; `*` and `?` stay inside one path segment; `**` crosses segments (`**/*.test.ts`); `**` alone is everything.

A file goes into the first commit whose patterns match it and whose content the destination does not have yet. Broad patterns in later commits pick up only what is left, so the last commit is usually `["**"]`. Check its file count in `review.md`: if it swallows a large part nobody planned, give that part its own commit.

## How dates are chosen

Milestones split the calendar into windows. A milestone's commits are planned from the end of the previous window until its deadline minus `margin_days`, and every later commit after its deadline, so the destination holds exactly that milestone's commits at the deadline. Inside a window the commits are spread evenly over the allowed days, at most `per_day` a day. A pinned commit keeps its day and the others spread around it. Already-pushed commits keep their dates; a re-plan schedules the rest from today.

## Filled in by the engine

`source.commit` (the snapshot being migrated), `target.base_commit` (the destination's commit when the calendar was first installed; `null` for an empty destination), `utc_offset`, `ci_from` (the commit that brings the CI configuration: the last one), every unpinned `date`, and after installing `pushed_at`, `target_sha`, `reached_at` and `reached_by`. Keep these fields when you edit an exported calendar.

## Common changes

| The user asks for | Change |
|---|---|
| more or fewer commits | split or merge commits, then `plan` again |
| a commit on a given day | set its `date` and `"pin": true` |
| a later start, no weekends, days off | `schedule.start`, `schedule.weekdays`, `schedule.skip` |
| two commits a day | `schedule.per_day: 2` |
| another deadline or scope | the milestone's `deadline`, `weekday` or `scope` |
| leave files out | add patterns to `exclude` |
| other wording or language | the commit messages |
