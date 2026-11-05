# Quality gates before delivery

Run all of them on the final versions. Fix what they find, and run them again after each fix.

## 1. LaTeX is clean, locally and on Overleaf

- **Logs.** No errors, no undefined references or citations, no missing files, and no visible overfull boxes, in
  both `main.log` and the Overleaf log.
- **Template placeholders.** `grep -rn FILLME deliverables/report-*/` prints nothing.
- **Citations against the bibliography.**
  - Every `\cite` key exists in `references.bib`.
  - Every bib entry is cited.
  - BibTeX reports no missing fields that would print as blanks.
- **The Overleaf copy.** The Overleaf PDF has the same page count as the local one, and `olcli diff --name-only`
  is empty.

## 2. Every page is full and nothing overflows

- **Render everything and look.** Render every page of every PDF, then look at all of them; a montage helps you
  see a whole document at once.

  ```bash
  pdftoppm -r 50 -png final-report.pdf /tmp/pages/p
  ```

- **Fix what shows.** Half-empty columns, a float stranded after a section break, an unbalanced last page, text
  running into margins, unreadable figures.
- **Page limit.** A report with a page limit meets it.
- **The deck.** Slides have no overflow or overlaps, and the `slides` skill's checks pass.

## 3. The report and deck speak in the authors' voice

- **Search for process words.** Search the report sources (`main.tex`, `sections/`, `tables/`) and the deck,
  speaker notes included:

  ```bash
  grep -rniE 'prompt|agent|\bai\b|generated|the user|provided (document|file)|readme|codebase|repository (shows|contains)|according to the (code|docs)|as requested|this document was' <files>
  ```

  - **Read every hit in context.** "Agent" can be legitimate: an agent can be the subject of the research.
  - **Rewrite** every sentence that narrates how the deliverable was produced, or treats the project's files as
    sources, in the authors' own voice.
- **Search for AI-use statements.** Unless the user explicitly asked for one, no sentence may say that AI tools
  helped build the project or write the deliverable:

  ```bash
  grep -rniE 'assist|claude|chatgpt|copilot|llm|coding agent|disclos|acknowledg' <files>
  ```

  Read every hit in context; a system or a subject under study may legitimately carry these names.
- **Read the abstract, introduction and conclusion once more.** Read them as a reviewer would, and make sure
  nothing in them sounds assembled.
- **Study documents are exempt.**

## 4. Everything agrees

- **Numbers.** Every number in the deck and study documents appears in the fact sheet and in the report, with the
  same value and the same rounding.
- **Names and claims.** Component names and terminology are identical everywhere. Interim and final reports differ
  only in scope.
- **Scripts and the deck.** The study scripts' slide numbers and titles match the final deck.
- **Runbook and cheat sheet.** The demo runbook and cheat sheet match what the demo test actually did.

## 5. Deliver

- **The files.** Put the final files in `deliverables/` under the agreed names.
- **The summary.** Give the user a short summary:
  - each file and its purpose;
  - the Overleaf project, and any setting the user must change by hand, such as the main document;
  - what was run or generated, with its cost if any;
  - whether the research round ran, and how many sources it kept;
  - anything left open, or anything a requirement asked for that the project does not support, including a course
    document's AI-use disclosure requirement, which stays out of the deliverable unless the user asks for it.
