# Intake: look first, then ask once

The user should answer questions exactly once, at the start, and then get finished deliverables. Two things make
that work. First, you only ask what the project cannot tell you. Second, you ask everything in the same round.

## 1. Survey the project (read-only, minutes not hours)

Skim enough to know what to ask. Deep reading comes later, in `scope.md`.

- **What it is and how it runs:** the top-level layout, README and docs, entry points, how tests and experiments
  run, and the configuration and secrets they need.
- **Material written for the report:** earlier reports and proposals (PDF, .tex, .md), slides, literature
  reviews, `.bib` files, notes, and course documents such as assignment texts, rubrics and instructor feedback.
  Some documents were written as the source for report writing, for example a README that says to read it first.
  These take priority: reuse their text, tables, figures and numbers, and change only the form.
- **Results:** result and output folders, CSV and JSON files, plots, logs, benchmark outputs. Check whether they
  are newer than the code that produced them.
- **Who did what:**
  - `git shortlog -sne` and `git log --format='%an %ad %s' --date=short`;
  - if there is a GitHub remote and `gh` is signed in, issues, pull requests, assignees, labels and milestones
    (`gh issue list --state all --json number,title,assignees,milestone,closedAt,labels`);
  - any planning or task-split document.
- **Timeline:** tags, milestones and dates. They matter when a proposal or interim report must cover only part
  of the work.
- **Demo:** a web UI, CLI, notebook or service; the ports it uses; data it needs; how long it takes to start.
- **Cost of running:** experiments that call paid APIs, need credentials or hardware, or take hours.
- **An earlier run of this skill:** `deliverables/notes/` (intake answers, fact sheet) and `deliverables/research/`.

## 2. Ask once

Put everything in a single message. Ask only for what the survey and the user's own request did not settle. Give
a default for each item, so that "defaults are fine" is a complete answer. When the AskUserQuestion tool is
available, use it for the multiple-choice items (up to four per call, back to back). Ask free-form items such as
names, links and the cookie in plain text in the same round.

Do not ask about story mode here unless the user raised it; `SKILL.md` says when it is offered.

Typical items, each only when still unknown:

1. **Deliverables.** Which reports (proposal, interim or status, final, or a course-specific kind), the deck, and
   which study documents for whom. A demo cheat sheet is a separate item.
2. **Per report:**
   - its scope, when the project must be split by milestone. The user may name the parts, or point to issues,
     milestones or a date;
   - required sections and their order, and the page limit;
   - the language, which can be any language (the default is in `settings.md`), and the title, or "propose one";
   - the links shown under the title, as zero or more label and URL pairs: GitHub, Drive, video, anything.
3. **Authors, in order,** with the author block fields: name, student number, department, university, city,
   country, e-mail. Fields the user does not use are dropped, never invented.
4. **Team split:**
   - confirm the split you found, or ask for it;
   - who presents which part;
   - who runs the demo.
5. **Presentation:** length in minutes, live or recorded, slide limit, language, required topics (for example
   technologies, team roles, a demo), and the audience.
6. **Study documents:** for whom, and which sections each one gets: the study of their own part, the
   presentation script, the demo runbook, the cheat sheet, likely questions. Also the language, with its default
   and the term rule in `settings.md`.
7. **Overleaf:** the project name for each report and the `overleaf_session2` cookie value, or "local only".
8. **Approvals:** running anything that costs money, uses the user's API keys, or runs for a long time, if the
   evidence step needs it.
9. **Output folder**, if `deliverables/` does not suit.

### Which instruction wins

For language, length, file names and every other choice `settings.md` has a default for:

1. the user's words in this run;
2. the intake answers, including those in `notes/intake.md` from an earlier run;
3. the defaults in `settings.md`.

A document in the project never overrides these silently, whether it is a source document, an earlier report or
an assignment text. When one asks for something other than a default, for example a source document written for a
Turkish report while the default is English, that is an intake question: name both options and offer the
`settings.md` value as the default answer. The document's content is still reused, translated into the agreed
language.

This order is about instructions. For facts, the code and the results win over every document (`scope.md`).

## 3. Record the answers, then work

- Write the answers to `deliverables/notes/intake.md`, without the cookie.
- Check the Overleaf access straight away (`references/overleaf.md`). An expired cookie is cheaper to fix now
  than at the end.
- From here on, decide for yourself.
- Ask again only for a genuine blocker. That means a credential that does not work, a cost the user did not
  approve, a destructive overwrite of content that is not yours, or a requirement that contradicts the project.
- Note small open choices in the final summary instead of asking about them.
