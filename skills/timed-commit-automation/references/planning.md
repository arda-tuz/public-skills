# Planning the calendar

## Contents

- Dates
- Scopes
- Commits
- Messages
- Notes and questions
- Before running plan

## Dates

- Take today's date and the timezone from `inspect`; never assume them.
- A date without a year is its next occurrence on or after today.
- A deadline the user gave as a date: write `"YYYY-MM-DD"` exactly as said. The engine reads it as "in the destination before that day starts" (23:59 the day before), so "12 December" means pushed by 11 December 23:59.
- A deadline with a time: `"YYYY-MM-DDTHH:MM"`.
- Phrases: "by the end of November" is `"2026-11-30T23:59"`; "in three weeks" is today plus 21 days, as a date; "next Friday" is that date. Show the resolved date in the review.
- If the user names a valid weekday, also write it in `weekday`; the engine turns a contradiction with the date into a question. A misspelled or ambiguous weekday ("Thuesday" is one letter from both Tuesday and Thursday) goes straight into `questions`, offering both readings with their dates (the other reading is that weekday in the same week); keep the date as written in the draft and leave `weekday` out until the user answers. Never guess.
- The whole project needs a deadline. If the user gave none, ask for it.

## Scopes

- Map every part the user describes to concrete paths after reading the code, not from folder names alone. "The image processing that uses local models" means the modules that load local weights (ONNX, PyTorch, TFLite, and so on), not clients of a cloud vision API.
- Add the code an in-scope part needs to work (shared utilities, config, types, model files it loads) to that milestone's scope, and say what you added and why in `notes`.
- When such a dependency is something the user explicitly left out ("only ..."), do not decide: ask in `questions`, offering both options. Leave a file out of a scope with a `!` pattern (`["backend/", "!backend/app/services/summaries.py"]`). Example: the backend imports an AI summarizer, but the user wanted only local image processing by the deadline; either the summarizer comes early with the backend, or the backend file that imports it waits for the next milestone.
- Everything else belongs to the final milestone, with scope `["**"]`.
- AI tool files that `inspect` lists (`CLAUDE.md`, `.claude/`, `AGENTS.md`, ...): put them in `exclude` and ask in `questions` whether the user agrees.

## Commits

- Order: setup → shared core → data layer → features in dependency order, each after the modules it imports → integration (routes, pages, wiring) → README and docs last. Setup holds the manifests and lock files (even when they list dependencies of later parts), configs, `.gitignore`, `LICENSE` and root tooling such as `Makefile` or `docker-compose.yml`.
- One commit is one coherent unit: a feature, module or layer together with its tests and assets. Never one commit per file. A file no earlier commit names lands in the final `["**"]` commit.
- Count the natural units. Commits = that number, but no more than the days available until the final deadline, and at least one per milestone. Ask before going beyond one commit per day.
- Milestones split the calendar into phases: a phase's commits come after the previous milestone's deadline and before its own. Balance the commit count of each phase roughly to its number of days, because the engine spreads each phase's commits evenly over its days.
- CI configuration (`.github/workflows/` and similar) always arrives with the last commit, so no CI run sees an unfinished project. The engine holds it back by itself; do not plan a separate CI commit.

## Messages

Conventional Commits, imperative mood, subject at most 72 characters, optional body of one or two lines saying what the commit adds. English unless the user asks for another language; say which in `notes`. Describe the code as if it were being written now. Never mention the tooling or the process: no AI assistance, Claude, migration between repositories, scheduling or this skill. The project's own subject matter is fine (`feat(ai): ...`, `feat(db): add migrations`).

- `chore: set up project structure and tooling`
- `feat(api): add authentication endpoints and JWT middleware`
- `feat(vision): add on-device inference with local ONNX models`
- `test(api): cover authentication flows`
- `docs: add README with setup instructions`

## Notes and questions

- `request`: the part of the user's words that belongs to this milestone, in the user's language.
- `notes`: one sentence per assumption or addition the user should know about: dependencies added to a scope, defaults chosen, the message language. They appear in the review and stay in the installed calendar.
- `questions`: one sentence per decision only the user can make, each with the options and the one the draft currently uses (write the option you recommend into the draft, so `plan` can schedule it). `install` refuses while any remain; remove a question once its answer is in the draft. A decision that comes up while you read a review also goes here.
- Write `notes` and `questions` in English, like the rest of the calendar; translate them when you present the review.

## Before running plan

- Every deadline is in ISO form and in the future; the whole project has one.
- `author` is the identity from `inspect`, or the one the user gave.
- `exclude` covers what the user does not want published.
- The last commit is `["**"]`, or every file is named.
