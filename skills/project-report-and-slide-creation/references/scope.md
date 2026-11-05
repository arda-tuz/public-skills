# Understanding the project and scoping each deliverable

## Read the project for real

The documentation tells you where to look; the code tells you what is true. Read the source of every component
the deliverables will describe:
- its data flow, algorithms, parameters and defaults;
- its evaluation protocol and the edge cases it handles.

When a document and the code disagree, the code wins. Run a quick check if you are unsure how something behaves.
Read the existing results and logs alongside the code that produced them, so you know what each number means.

## The fact sheet: `deliverables/notes/facts.md`

This is the one source every deliverable is written from. It is the reason the report, the deck and the study
documents never contradict each other. Shape it as you like, but it should hold:
- what the system is, and its components with the names you will use everywhere (one name per concept);
- the data, the methods and the evaluation setup;
- every number that may appear, with its value, unit and source (file, command or run), and where it is used;
- the contributions, the limitations, and the honest negative results;
- the people and their parts;
- the scope of each report kind (below).

When a number changes, change it here first, then in every deliverable that uses it.

## Report kinds

Write each kind as what it is, whatever state the project is in today.

- **Proposal.** The plan: problem and motivation, related work, the intended approach, the planned evaluation,
  the work plan and timeline, the expected outcomes and the risks.
- **Interim or status report.** What is done up to the milestone, with its evidence. What remains and how it
  will be done. Deviations from the proposal, and risks.
- **Final report.** The complete work: full evaluation, discussion, limitations and conclusion.
- **Course-specific kinds.** Follow the user's or the course's definition. When it is vague, the kinds above are
  the default reading.

## Splitting by milestone

When a report covers only part of a finished project, decide what counts as done for it. In order of authority,
use:
1. the user's own description;
2. a written plan;
3. GitHub milestones, or issues closed before the cut-off;
4. git tags and commit dates.

Work after the cut-off appears only as planned work, described as the design that was later built. When the report
needs evidence from that earlier state, check out the milestone commit in a separate git worktree
(`git worktree add ../<name>-<milestone> <commit>`) and run it there. Never move the main checkout. Interim and
final reports differ in coverage, never in facts or in names.

## Splitting by person

Sources, in order of authority:
1. the user's words;
2. a split written in the repository;
3. issue and pull request assignees;
4. git authorship.

Map each component to its owner, and from there to its report sections, its slides and its owner's study
document.

- **Shared deliverables cover everyone's work evenly.** These are the report and the deck. The deck is grouped
  in talk order by presenter.
- **A contributions statement only when wanted.** Add it to the report when the user or the course asks for one.
- **Study documents are personal.** Each one goes deep on its owner's part and stays general about the rest.

## Unfinished parts

Describe what exists, and present what is missing as future work. Never describe a feature the code does not have.
When a requirement asks for something the project lacks, say so in the final summary rather than covering it up.
