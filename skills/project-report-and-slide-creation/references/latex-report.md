# Writing the LaTeX report

## Start from the template

Copy `assets/ieee-report/` (dotfiles included) to `deliverables/report-<kind>/`. When the report goes to
Overleaf, do the project setup in `overleaf.md` first, then copy the template over the pulled folder.

**The fixed format.** `main.tex` holds the format the user wrote and tested by hand:
- `\documentclass[conference]{IEEEtran}`;
- the package list, exactly as it stands (`placeins` is loaded twice on purpose, once with `[section]`);
- `\bibliographystyle{IEEEtran}` with `\bibliography{references}`.

**The three additions.** Each one serves a requirement:
- `subfiles`, for the multi-file structure;
- `\hypersetup{hidelinks}`, so links stay clickable without colored boxes, as in the reference PDF;
- the `\headerlink` and `\headerlinks` macros for the red link line.

Keep all of it. Add a package only when the content cannot be written without it, and check that it does not
clash with this set first.

**Reports not in English.**
- Add `\usepackage[T1]{fontenc}` and the language's `babel`, for Turkish
  `\usepackage[turkish,shorthands=off]{babel}`. Babel then localizes captions and headings, such as Özet, Şekil,
  Tablo and Kaynaklar, and hyphenates correctly.
- Overleaf has every babel language. If a local build reports an unknown babel option, install the TeX Live
  language pack, or rely on the Overleaf compile for that check.

## Project layout

```text
report-<kind>/
├── main.tex              preamble, title and links, authors, abstract, index terms, the \subfile list, bibliography
├── sections/NN-name.tex  one file per section, numbered in reading order (01-introduction.tex, 02-related-work.tex)
├── figures/              figures, vector PDF where possible, named for what they show (architecture-overview.pdf)
├── tables/               one .tex per table (main-results.tex), \input from its section
├── code/                 code excerpts as images, if any
├── references.bib        only the entries the text cites
├── .olignore             keeps local build files out of Overleaf
└── .gitignore            keeps .olauth and build files out of git
```

- **Section files.** Each one starts with `\documentclass[../main.tex]{subfiles}`, so it also compiles on its own.
  Inside a section file, write paths relative to `sections/` and wrap them in `\subfix`, as in
  `\input{\subfix{../tables/main-results}}`.
- **Figures.** Refer to them by bare name: `\graphicspath` already covers `figures/` and `code/`.
- **Template leftovers.** Delete `section-template.tex`, `table-template.tex` and the placeholder bib entry once
  the real files exist.

## Title, links, authors

- **Title.** In `\title{...}`.
- **Header links.**
  - They sit right under the title, centered, `\Large`, bold, red and underlined, with the reference PDF's spacing.
  - Write `\headerlinks{\headerlink{URL}{Label}}`, and separate several links with `\quad`, for example GitHub
    Repository, Google Drive or Demo Video.
  - With no links, write the plain title.
- **Author block.** Keep the exact layout of the template: `\IEEEauthorblockN{name}` and
  `\IEEEauthorblockA{\textit{Student No: ...} \\ \textit{Department} \\ \textit{University} \\ City, Country \\ e-mail}`,
  authors separated by `\and`, in the user's order.
  - Fill it only with what the user gave.
  - Drop lines the user does not use, such as a student number in a non-course paper.
- **Abstract and index terms.** Both are always present.
  - The abstract stands alone. It states the problem, the approach, the key results with numbers, and why they
    matter.
  - Index terms are a handful of lowercase IEEE-style keywords.

## Sections

- The user's mandatory sections come first, in the order and with the names they gave.
- Design the rest for the report kind (`scope.md`) and for the strongest possible paper: add sections and
  subsections where the material calls for them, and merge where it is thin.
- Use `\section`, `\subsection`, `\paragraph{}` for fine structure, and `\subsubsection*{}` where it helps.
- Label everything you refer to with a prefix: `sec:`, `fig:`, `tab:`, `eq:`.

## Writing standard

**Level.** Write at the level of a strong graduate or PhD seminar paper:
- conceptual clarity;
- precise methodology;
- critical comparison with prior work;
- awareness of where the field is heading;
- practical relevance.

**Density.**
- Compact but dense: no surface-level summaries and no padding.
- Every claim is specific, with numbers, units and the conditions under which they hold. No vague superlatives.

**Content.**
- Related work reads as the foundation the project built on (`research-round.md`).
- Limitations and threats to validity are stated plainly. Honest negative results strengthen a paper.

**Voice.** Use the authors' voice only (see the rules in `SKILL.md`). The paper describes the work; it never
mentions how the paper was put together.

## Figures, tables, code

Which form each visual takes, and how data figures are drawn, is in `figures.md`.

- **Captions and order.** Figure captions go below the image and table captions above the table. Each float
  appears after the paragraph that first refers to it, and the text says what the reader should see in it.
- **Placement.** Most floats take `[!t]` in two columns; small ones can take `[!htbp]`. Wide floats use
  `figure*`/`table*` with `[!t]`, or `[!b]`, which `stfloats` allows. Use `subcaption` for subfigures.
- **Tables.** Use booktabs rules (`\toprule`, `\midrule`, `\bottomrule`) and no vertical lines. Keep each table
  narrow enough for its column, or make it a `table*`.
- **Equations.** Use `amsmath`; number only the equations you refer to.
- **Code.** `minted` stays in the preamble, but keep listings short. Locally it needs `-shell-escape`, and
  Overleaf ships a newer minted. Long excerpts go in `code/` as images, and pseudocode uses `algorithmic`.
- **Missing images.** Never leave an `\includegraphics` pointing at a file that does not exist.

## No wasted space

Dense pages are part of the format: the reference report fills every column.

- **Where floats go.**
  - `[section]{placeins}` flushes pending floats at every `\section`, so put each float early in its section,
    right after its first mention.
  - Size figures to their information: a one-column figure at `\columnwidth`, not tall and thin.
  - Use `\FloatBarrier` only where a float must not drift. A barrier can open a gap of its own.
- **Wide floats at a section break.** A `figure*` or `table*` lands at the top of a later page, or with `[!b]` at
  the bottom of the current one if it still fits. If it is still waiting when the next `\section` starts,
  `[section]{placeins}` flushes it: the text stops, the float takes a new page, and the rest of the current page
  stays empty. The sign is a gap right before a section heading, with the next page opening on the wide float. Fix
  it in this order:
  1. Introduce the float earlier in its section, so enough text follows it to reach the next page before the
     section ends.
  2. Move the float, with the paragraph that discusses it, into the next section, where it is no longer pending at
     the barrier.
  3. Make it a one-column float if it stays readable.

  Do not remove `placeins` or its `[section]` option; both belong to the fixed format.
- **Closing a gap.**
  - Move a float by a paragraph, or resize it slightly.
  - Split or merge a table, or turn a wide figure into a `figure*`.
  - Tighten or extend the nearby text.
  - Never change margins, font sizes or float spacing parameters, and never use `\vspace` tricks.
- **The last page.** Balance its columns. When content alone does not do it, put `\IEEEtriggeratref{n}` right
  before `\bibliography` in `main.tex`. It starts a new column at reference `n`; try values until both columns end
  at about the same height, and compile twice after each change.
  - A value carried over from an earlier version of the report is stale once floats or text change.
  - Remove it and tune it again; a stale trigger can leave a last page with one column of references.
- **Page limit.** When the user gives one, the compiled PDF meets it, references included. Fit the content to
  the limit; never squeeze the layout.

## Bibliography

- Cite in IEEE numeric style (`\cite{key}` gives [1]); `cite` sorts and compresses ranges.
- `references.bib` holds only entries the text cites, each from the project's sources or the research folder,
  with complete fields: authors, title, venue, year, pages or DOI, and URL where useful.
- Never write an entry from memory.

## Compile and check locally

```bash
pdflatex -shell-escape -interaction=nonstopmode main.tex
bibtex main
pdflatex -shell-escape -interaction=nonstopmode main.tex
pdflatex -shell-escape -interaction=nonstopmode main.tex
# or, where latexmk exists: latexmk -pdf -shell-escape main.tex
```

Read `main.log`. Expect no errors, no undefined references or citations, no missing files, and no overfull boxes
that show. The only expected warning is caption's "Unknown document class", which comes from `subcaption` under
IEEEtran and is part of the tested format.

"Text page N contains only floats" is acceptable when the float-only column is full and its floats are discussed on
the same or the facing page. A whole page of floats, or a float-only column with a gap, is not; fix it as in "No
wasted space". Then go through `quality-gates.md`.
