# Evidence: results, figures, diagrams, screenshots

## Is what exists enough?

List the claims the report will make, such as its research questions and contributions, and check that each one has
evidence:
- a result file, a log, a test outcome or a measurement;
- produced by the current code (compare dates and configurations);
- covering the comparison the claim needs (baselines, ablations, variance across runs).

Use the project's outputs where they hold up. Do not regenerate them for their own sake.

## When something is missing, produce it

- **What to run.** Run the tests, experiments, benchmarks or the demo, using the project's own commands and
  configurations.
- **Where outputs go.** Write new outputs under `deliverables/evidence/`. Put analysis and plotting scripts in
  `deliverables/evidence/scripts/`. If the project has a results convention, follow it, but never overwrite
  results that already exist.
- **What to record.** Note every command, its environment and its duration in `deliverables/notes/evidence.md`,
  so the numbers are reproducible and the methods section can state the setup exactly.
- **Keep a log of every run.** A test count or outcome that goes into a deliverable needs a saved log, not a
  remembered result:

  ```bash
  bash -c 'set -o pipefail; <command> 2>&1 | tee deliverables/evidence/<run>.log'
  echo $? > deliverables/evidence/<run>.exit
  ```

- **Commands that rewrite the project's own files.** Test suites and experiment runners often regenerate tracked
  results, figures or lockfiles, so the repository must end the run as it started:
  1. Save `git status --porcelain` before the run.
  2. Copy aside any file that already has uncommitted changes. Those changes are the user's.
  3. After the run, compare the status again. Copy every file the run changed to
     `deliverables/evidence/<run>-regenerated/`, keeping its relative path.
  4. Run `git restore -- <file>` on the tracked files that were clean before. Put the saved copy back for the others.
  5. Compare the regenerated results with the committed ones. A real difference means the committed numbers may be
     stale, so record it in `notes/evidence.md` and in the final summary.
- **The source code stays as it is.** Wrappers, configurations and analysis code live under `deliverables/`.
- **Approval first.** Anything that costs money, uses the user's credentials or runs for hours needs the approval
  from intake.

## Figures, tables and diagrams

- **Data figures.** Regenerate them from the underlying data in one consistent style. For LaTeX, use vector PDF;
  for slides, use PNG at 200 dpi or more. Label axes with units. Make the comparison the figure argues for
  visible at a glance.
- **Architecture and flow diagrams.** These often explain a system better than a page of text. Draw them as
  vector graphics (TikZ, or SVG converted to PDF), with the component names from the fact sheet.
- **Figures in another language than the deliverable.** Leave the project's originals alone. Make translated
  copies from the underlying data or the source SVG, with the script in `deliverables/evidence/scripts/` and the
  output in the report's `figures/`.
  - Translate every title, label and legend, and keep every number as it is.
  - Search the result for words or characters of the source language.
  - Look at each rendered copy. A translated label has a different length and can overflow its box; shorten the
    label rather than the figure's content.
- **SVG to vector PDF without a converter.** When neither `rsvg-convert` nor `inkscape` is available, use headless
  Chrome or Chromium. Inline the SVG in an HTML page whose CSS sets `@page{size:<w>px <h>px;margin:0}` and
  `body{margin:0}`, with the size taken from the SVG's `viewBox`, then run:

  ```bash
  google-chrome --headless=new --disable-gpu --no-pdf-header-footer --print-to-pdf=figure.pdf page.html
  ```

- **Interface screenshots.** Run the application and capture them with a browser automation tool at a fixed
  window size, with realistic data on screen.
- **Code.** Show it only when the code itself is the point. Use a short listing, pseudocode (`algorithmic`), or
  an image of a longer excerpt.
- **Tables.** Use them for exact numbers that will be compared. Write them as booktabs tables in `tables/`.
- **Comparisons with published work.** These come from the research folder's `comparisons.md`. State honestly how
  comparable each setting is.

## The balance rule

Every figure and table carries part of the argument, and the text refers to it and says what to see in it. No
decorative images, and no figure dump. When two figures make the same point, keep the clearer one.
