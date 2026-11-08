---
name: project-report-and-slide-creation
description: Turns a finished project in the workspace into its academic deliverables, end to end and unattended after one round of questions. It writes an IEEE-format LaTeX report (proposal, interim/status or final), kept in sync with and compiled on Overleaf. It draws data figures with the scientific-figure-making skill where they serve the paper best. It builds the presentation deck (.pptx and .pdf) with the slides skill. It writes personal study documents (a project primer, a per-person study guide, a minute-by-minute presentation script, a demo runbook and cheat sheet, and likely questions with answers). It runs the project when results are missing and runs one literature research round when the existing sources are not enough. On request it structures every deliverable around one storyline, from the big picture to the details. Use it whenever the user wants a report, paper, write-up, proposal, interim or status report, presentation, slides, or material to prepare for presenting or demoing a project, solo or team, even if they only say "raporu yaz", "sunumu hazırla" or "write the final report".
license: MIT
metadata:
  version: "1.2.0"
---

# Project report and slide creation

One run takes a finished project and produces the deliverables the user asks for. They agree with each other and with the code:

- **Reports**: IEEE two-column LaTeX projects, compiled locally and on Overleaf. A run can produce several kinds (proposal, interim or status, final, or whatever the course calls them).
- **Presentation**: one shared deck, as `.pptx` and `.pdf`, grouped by presenter when it is a team.
- **Study documents**: one general primer for the whole team, plus a personal document for each member who wants one. A personal document can hold their part of the project, their script, the demo runbook, the cheat sheet, and the likely questions.

The code is assumed to be complete. Results, figures and a literature review may or may not exist yet; the run produces what is missing.

Before anything else, read `settings.md`. It holds the research team's models and limits and the defaults for anything the user leaves open, including each deliverable's language. Any deliverable can be in any language the user asks for. The user maintains it in plain words, so translate its wording into the identifiers your tools accept.

## How a run goes

1. **Look before asking** (`references/intake.md`). Survey the project read-only and quickly. Find out:
   - what the project is and how it runs;
   - which results, figures, literature, earlier reports and course documents exist;
   - who worked on which parts;
   - whether there is a demo, and what running things would cost.

   The survey decides which questions are worth asking.
2. **Ask once** (`references/intake.md`). Gather in one round everything only the user can give, such as names, Overleaf project and cookie, deliverables, scope, lengths and who presents what. Offer defaults. After this round the run is autonomous. Stop again only for a genuine blocker, such as a rejected cookie, a cost the user did not approve, or overwriting someone's Overleaf content.
3. **Understand the project and write the fact sheet** (`references/scope.md`).
   - Read the code itself; documentation tells you where to look, and the code tells you what is true.
   - Material already written for the report comes first: an earlier report, or a document prepared as the report's source. Reuse its text, tables, figures and numbers after checking them against the code, and change only the form.
   - Record every claim, number, name and contributor in `notes/facts.md`. Every deliverable is written from that sheet.
   - Decide what each report kind covers and how the team's parts map onto sections, slides and study documents.
4. **Make sure the evidence exists** (`references/evidence.md`).
   - Use the project's outputs where they are good enough.
   - Otherwise run the project, its experiments and its demo to produce results, figures and screenshots, and record how you produced them.
   - Choose the form of every visual (table, data figure, diagram) with `references/figures.md`. Data figures are drawn with the `scientific-figure-making` skill, loaded fresh in each run, wherever it serves the paper; it is never required.
5. **Research, once, only if needed** (`references/research-round.md`). Compare what the report needs with the literature the project already has: related work, comparisons with published results, and the origins of methods and data.
   - If there is a gap, plan every research question first. Then run the bundled research workflow a single time: parallel web searchers, a reviewer behind each one, and one collector that writes one research folder with BibTeX. The models and limits come from `settings.md`.
   - Invoking this skill is the user's opt-in to that one workflow run.
6. **Write the report** (`references/latex-report.md`, `references/overleaf.md`).
   - Start from `assets/ieee-report/`.
   - Fill the sections the user requires and design the rest.
   - Compile locally, push to Overleaf, compile there and read both logs.
7. **Build the deck** (`references/slides.md`) with the `slides` skill. Work top-down and in simple academic language, from the report's own figures and numbers, re-rendering the figure scripts at slide size (`references/figures.md`).
8. **Write the study documents** (`references/study-documents.md`) after the deck is final, because the scripts point at its slide numbers.
   - Before writing a demo runbook, run the demo yourself, following the runbook step by step.
9. **Check everything together, then deliver** (`references/quality-gates.md`).
   - Check compile logs, page fill, voice, and cross-document consistency.
   - Finish with a summary: the files, the Overleaf project, what you ran or generated, the research round status, and anything still open.
   - If `notes/intake.md` has no story-mode line yet, end the summary with one question: whether to restructure the deliverables around a storyline (see "Story mode").

## Story mode

Story mode structures every deliverable around one storyline:
- the big picture;
- a few categories;
- for each category, what was aimed for, achieved and not achieved;
- the evidence, simple before detailed.

It is off until the user turns it on, and it never changes a fact.

**The toggle.** One line in `notes/intake.md`, `Story mode: on` or `Story mode: off`, records the user's choice for
the project.
- **No line yet.** Offer it once, as the last line of a run's final summary, never mid-run. The default in
  `settings.md` decides whether to offer it.
- **Off.** Never ask again in that project.
- **Switching.** The user can switch it either way at any time by saying so ("hikayeleştir", "make it a story",
  "drop the story mode").

**Turning it on.**
1. Read `references/storyline.md` once.
2. Derive `notes/story.md` from the fact sheet.
3. Restructure the existing deliverables from it: reorder, regroup, add lead sentences. Do not rewrite them from
   scratch.

**On from the start** (the user asked at intake, or `settings.md` says always on): derive `notes/story.md` right after the
fact sheet in step 3, before the first deliverable, so nothing is written twice.

**While it is on.** Every later deliverable reads only `notes/story.md`. Reread `storyline.md` only to derive the story
again after the facts change.

## Rules that hold in every run

**The deliverables speak in the authors' voice.**
- The report and the deck, speaker notes included, read as if the authors wrote them directly for a journal or a talk.
- They describe the problem, the system, the method and the evidence. They never reveal how they were produced:
  - nothing about prompts, drafts or an AI writing them;
  - no "the user", "the provided documents", "the codebase contains" or "according to the README";
  - no file-by-file narration of the repository.
- **No AI-use disclosure, unless the user explicitly asks for one in this run.** The report and the deck carry no statement, acknowledgment, footnote or contribution note saying that AI tools, coding agents or AI assistance were used to build the project or to write the deliverable.
  - Do not ask about it at intake, and do not offer it.
  - Leave such mentions out when reusing a source document.
  - If a course document requires a disclosure, still leave it out, and name that requirement in the final summary so the user can decide.
- When the project itself is about AI, agents or prompts, those words are subject matter, not process.
- Naming system components, linking the repository and adding a short reproducibility note are normal academic content.
- This rule matters more than any other, because a single such sentence makes the whole report look machine-made.
- Study documents are the exception. They are private preparation material and should point at files, commands and code freely.

**The LaTeX format is fixed; nothing else is.**
- Fixed: the class, the package list, the bibliography style, the author block layout and the red header link style in `assets/ieee-report/main.tex`. The user wrote and tested them by hand, so reproduce them exactly.
- Open: title, sections, length, depth, figures and structure. These come from the user's requirements, or from your judgment where the user is silent.

**Every number and every source is real.**
- Every number in a deliverable traces to a result file, a log or a run you made.
- Every citation comes from the project's own sources or from the verified research folder.
- When something cannot be supported, leave it out or state it as a limitation. Never estimate it or cite from memory.

**There is at most one research round per run.**
- Decide everything the round must answer before starting it.
- Academic sources come only from the project and from that round.
- A research folder from an earlier run is reused unless the user asks for new research.

**The deliverables never contradict each other.**
- The report, deck and study documents share one fact sheet, one set of names for things and one scope.
- An interim report and a final report may differ in coverage, but never in facts.

**Pages are full.**
- PDFs carry no unnecessary white space: no half-empty columns before a float, no stranded figures, no ragged last page when it can be balanced.
- Fix gaps through content and float placement, never by changing the class's margins, fonts or spacing.

**Accounts, money and the user's files are handled with care.**
- The Overleaf cookie lives only in the report folder's git-ignored `.olauth`; never print it.
- Before replacing an existing Overleaf project's content, back it up.
- Runs that cost money or need the user's credentials happen only with their approval from intake.
- Commit or push the project's git repository only when asked.

## Freedom

Everything that the user's requirements and the rules above do not fix is yours to decide, including:
- section structure and the number of figures;
- diagrams, chart types, slide design and study document layout;
- the tools you use.

You may install any package or tool, run the project and its tests, start its servers, drive a browser, and take screenshots. Prefer what makes the deliverables clearer and more convincing over what is quickest to produce.

## Where things go

Unless the user names another place, everything goes under `deliverables/` at the project root:

```text
deliverables/
├── notes/           intake.md, facts.md, plan.md, evidence.md, figures.md, story.md (working notes, not handed in)
├── research/        the research round's folder, if one ran (README.md, references.bib, literature.md, ...)
├── evidence/        results, figures and screenshots this run generated, with the scripts that made them
├── report-<kind>/   one LaTeX project per report, mirrored on Overleaf (main.tex, sections/, figures/, tables/, code/)
├── slides/          deck source and build files
├── study/           study document sources
└── final files      e.g. final-report.pdf, presentation.pptx, presentation.pdf, general-study-document.pdf,
                     <name>-study-document.pdf, <name>-demo-cheat-sheet.pdf (names from settings.md or the user)
```

On a rerun, read `notes/` first. The earlier intake answers and fact sheet keep the new deliverables consistent with the old ones.
