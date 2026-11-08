# project-report-and-slide-creation

Turns a finished project into its academic deliverables: an IEEE-format report kept on Overleaf, a presentation deck, and private study documents. You answer one round of questions, then the agent works unattended and writes everything from a single fact sheet, so the deliverables never contradict each other or the code.

- **Report.** A two-column IEEE LaTeX project, split into section and table files, compiled locally and on Overleaf with both logs checked. The LaTeX format is fixed and comes from a tested template; the title, sections, length and figures follow your requirements. It supports a proposal, an interim or status report, a final report, or whatever your course calls them.
- **Figures.** Each visual gets the form a strong paper would give it: a table for exact numbers, a data figure when the shape of the data is the argument, a vector diagram for architecture and flow. Data figures are drawn with the [`scientific-figure-making`](https://github.com/ChenLiu-1996/figures4papers) skill where it helps, never by quota. The plugin installs that skill with this one and tracks its upstream repository, so its updates take effect here without a new release of this skill; each run loads the installed version fresh and records its revision. Where its house style and the paper disagree, the paper decides size and type (figures drawn at 3.5 in or 7.16 in with 7-8 pt text, checked with `pdfinfo` and `pdffonts`); the palette, its meanings and the layout patterns come from the sub-skill.
- **Deck.** A `.pptx` and `.pdf` built with the `slides` skill (or Anthropic's `pptx` skill when `slides` is missing), top-down and in plain academic language, using the report's own figures and numbers. Team decks are grouped by presenter.
- **Study documents.** A general primer for the team and a personal document per member, with their part of the project, a minute-by-minute script keyed to the final slide numbers, a demo runbook tested step by step, a printable cheat sheet, and likely questions with answers.
- **Real numbers only.** The code is read and checked before anything is written, a document that disagrees with the results loses, and every number traces to a result file, a log or a run. Missing results come from running the project. Runs that cost money or use your credentials need your approval first, and files the run rewrites are saved aside and restored.
- **One research round at most.** When the project's own literature is not enough, one workflow searches the web with a reviewer behind each searcher and a collector that writes one folder with BibTeX. When the sources are enough, it is skipped.
- **Written in the authors' voice.** The report and the deck never mention how they were produced. They carry no AI-use statement unless you explicitly ask for one, so if your course or venue requires one, ask for it.
- **Story mode, on request.** At the end of the first run it offers once to restructure every deliverable around one storyline: the big picture, two to four categories, and for each what was aimed for, achieved and not achieved, with the evidence from simple to detailed. Facts and numbers never change; the text is reordered and regrouped, not rewritten. Turn it on or off at any time ("make it a story", "drop the story mode"), or set it in `settings.md`.
- **Full pages.** Every page is rendered and inspected. Gaps are fixed through content and float placement, never by changing margins, fonts or spacing.

## Language

Any deliverable can be in any language you ask for. Without an instruction, the report and the deck are in English, and the study documents are in Turkish with the English term in parentheses after each technical term. These defaults, the research team's models and the file names live in plain words in `settings.md`, so edit that file to change them.

## Requirements

- A LaTeX distribution with `pdflatex` and `bibtex`. The template loads `minted`, so a local build needs Python's Pygments and `-shell-escape`.
- [`olcli`](https://www.npmjs.com/package/@aloth/olcli) in a version whose `push` keeps nested folders, and your `overleaf_session2` cookie. Without Overleaf, the skill delivers the folder and a zip you can upload.
- `pdftoppm` (Poppler), to render and inspect the pages.
- Claude Code. The skill is written for it: the research round uses its Workflow tool, and the plugin install below is what brings `scientific-figure-making` along.
- For the deck, the `slides` skill if you have it. It does not come with Claude Code; without it the deck is built with Anthropic's `pptx` skill, when your Claude account offers it, or with PptxGenJS directly. LibreOffice exports the PDF.
- Chrome or Chromium, optional, for converting SVG diagrams and rendering study documents.
- For data figures: Python with matplotlib, and the `scientific-figure-making` skill from [ChenLiu-1996/figures4papers](https://github.com/ChenLiu-1996/figures4papers). The plugin installs it for you (see "Install"). Without it, data figures are drawn in a consistent style of the skill's own. It is third-party work under its own license, CC BY-NC 4.0, and is fetched from its repository, not copied into this one.
- Whatever your own project needs to run.

The research round uses Claude Code's Workflow tool. The Overleaf cookie stays in the report folder's git-ignored `.olauth` and is never printed.

## Status

The report path has been used end to end on a real project, from the questions to the Overleaf compile, and once more with the figure policy and `scientific-figure-making`. The deck, the study documents and the research workflow have not been run on a real project yet. The plugin install, with `scientific-figure-making` arriving as a dependency and moving to a new upstream commit on update, was tested in a clean Claude Code home.

## Install

Install it as a Claude Code plugin. Claude Code then installs `scientific-figure-making` with it as a plugin dependency, straight from its upstream repository:

```text
/plugin install project-report-and-slide-creation --marketplace arda-tuz/public-skills
```

To keep both up to date without doing anything, turn on auto-update once: `/plugin` → **Marketplaces** → `arda-tuz-skills` → **Enable auto-update**. `scientific-figure-making` has no version of its own, so every new commit in its repository counts as an update, and so does every new release of this skill. Without auto-update, run `claude plugin marketplace update arda-tuz-skills`, then `claude plugin update scientific-figure-making@arda-tuz-skills` and `claude plugin update project-report-and-slide-creation@arda-tuz-skills`.

The other methods in the repository's [installation guide](../../README.md#install), such as `npx skills add`, copy only this skill's folder. With them, install `scientific-figure-making` yourself, as its README describes. If it is already in your skills folder, do not also install the plugin, or it loads twice.

## Use

Open the agent in the project's folder and say what you need:

```text
/project-report-and-slide-creation:project-report-and-slide-creation Write the final report (8-10 pages) covering objectives, approach, outcomes and lessons learned.
```

As a plugin it is called `/project-report-and-slide-creation:project-report-and-slide-creation`; Claude Code also picks it up on its own when you ask for a report or a deck. The agent surveys the project first and asks only what it cannot find out: names, the Overleaf project, scope, and who presents what. Results land in `deliverables/` at the project root. On a later run it reads its earlier notes, so a final report stays consistent with the interim one.

## License

MIT, see [LICENSE](LICENSE).
