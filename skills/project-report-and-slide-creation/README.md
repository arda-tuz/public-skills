# project-report-and-slide-creation

Turns a finished project into its academic deliverables: an IEEE-format report kept on Overleaf, a presentation deck, and private study documents. You answer one round of questions, then the agent works unattended and writes everything from a single fact sheet, so the deliverables never contradict each other or the code.

- **Report.** A two-column IEEE LaTeX project, split into section and table files, compiled locally and on Overleaf with both logs checked. The LaTeX format is fixed and comes from a tested template; the title, sections, length and figures follow your requirements. It supports a proposal, an interim or status report, a final report, or whatever your course calls them.
- **Figures.** Each visual gets the form a strong paper would give it: a table for exact numbers, a data figure when the shape of the data is the argument, a vector diagram for architecture and flow. Data figures are drawn with the [`scientific-figure-making`](https://github.com/ChenLiu-1996/figures4papers) skill where it helps, never by quota. That skill is loaded fresh in every run, so its updates take effect here without a new release, and the revision used is recorded. Where its house style and the paper disagree, the paper decides size and type (figures drawn at 3.5 in or 7.16 in with 7-8 pt text, checked with `pdfinfo` and `pdffonts`); the palette, its meanings and the layout patterns come from the sub-skill.
- **Deck.** A `.pptx` and `.pdf` built with the `slides` skill, top-down and in plain academic language, using the report's own figures and numbers. Team decks are grouped by presenter.
- **Study documents.** A general primer for the team and a personal document per member, with their part of the project, a minute-by-minute script keyed to the final slide numbers, a demo runbook tested step by step, a printable cheat sheet, and likely questions with answers.
- **Real numbers only.** The code is read and checked before anything is written, a document that disagrees with the results loses, and every number traces to a result file, a log or a run. Missing results come from running the project. Runs that cost money or use your credentials need your approval first, and files the run rewrites are saved aside and restored.
- **One research round at most.** When the project's own literature is not enough, one workflow searches the web with a reviewer behind each searcher and a collector that writes one folder with BibTeX. When the sources are enough, it is skipped.
- **Written in the authors' voice.** The report and the deck never mention how they were produced. They carry no AI-use statement unless you explicitly ask for one, so if your course or venue requires one, ask for it.
- **Full pages.** Every page is rendered and inspected. Gaps are fixed through content and float placement, never by changing margins, fonts or spacing.

## Language

Any deliverable can be in any language you ask for. Without an instruction, the report and the deck are in English, and the study documents are in Turkish with the English term in parentheses after each technical term. These defaults, the research team's models and the file names live in plain words in `settings.md`, so edit that file to change them.

## Requirements

- A LaTeX distribution with `pdflatex` and `bibtex`. The template loads `minted`, so a local build needs Python's Pygments and `-shell-escape`.
- [`olcli`](https://www.npmjs.com/package/@aloth/olcli) in a version whose `push` keeps nested folders, and your `overleaf_session2` cookie. Without Overleaf, the skill delivers the folder and a zip you can upload.
- `pdftoppm` (Poppler), to render and inspect the pages.
- The `slides` skill for the deck, or the `pptx` skill or PptxGenJS as a fallback, plus LibreOffice for the PDF export.
- Chrome or Chromium, optional, for converting SVG diagrams and rendering study documents.
- Optional, for data figures: the `scientific-figure-making` skill from [ChenLiu-1996/figures4papers](https://github.com/ChenLiu-1996/figures4papers) (its README shows how to install it) and Python with matplotlib. Without it, data figures are drawn in a consistent style of the skill's own.
- Whatever your own project needs to run.

The research round uses Claude Code's Workflow tool. In other agents it falls back to subagents with the same three roles, or is skipped with a note if neither exists. The Overleaf cookie stays in the report folder's git-ignored `.olauth` and is never printed.

## Status

The report path has been used end to end on a real project, from the questions to the Overleaf compile, and once more with the figure policy and `scientific-figure-making`. The deck, the study documents and the research workflow have not been run on a real project yet.

## Install

Follow the repository's [installation guide](../../README.md#install) using the skill name `project-report-and-slide-creation`. For example:

```bash
npx skills add arda-tuz/public-skills --skill project-report-and-slide-creation --agent claude-code --global
```

## Use

Open the agent in the project's folder and say what you need:

```text
/project-report-and-slide-creation Write the final report (8-10 pages) covering objectives, approach, outcomes and lessons learned.
```

In Codex use `$project-report-and-slide-creation`; as a Claude Code plugin, `/project-report-and-slide-creation:project-report-and-slide-creation`. The agent surveys the project first and asks only what it cannot find out: names, the Overleaf project, scope, and who presents what. Results land in `deliverables/` at the project root. On a later run it reads its earlier notes, so a final report stays consistent with the interim one.

## License

MIT, see [LICENSE](LICENSE).
