# Study documents

A reader who knows nothing about the project should be able to learn it from these documents alone. That means
they can:
- understand what was built and why;
- present their part with confidence;
- run the demo from start to finish;
- answer the instructor's questions.

These documents are private preparation material, so the voice rule does not apply. Point at files, functions,
commands and logs whenever that helps the reader.

When story mode is on, every document uses the categories of `notes/story.md`, in the deck's order, and groups the likely questions by category.

## The general primer, shared by the whole team

It covers the entire project, independent of who did what, so every member also understands the parts they did
not build. Detail belongs in the personal documents; this one gives the full picture clearly.

- **The big picture first.** What problem, for whom, what the system does, and the one-paragraph story of the
  project.
- **Then the parts, grouped.** Sort the methods and main ideas into a few families, such as data, models,
  evaluation and serving, or whatever fits. For each family explain what it does, why it was chosen, how it
  works in plain words, and where it lives in the code.
- **Pictures.** An architecture diagram, a data or request flow, and small diagrams for any idea that is easier
  seen than read.
- **Results and how to read them.** The key numbers to remember, what they mean and what they do not mean, and
  the limitations.
- **A map of the deliverables.** Which report section and which slides cover which part.
- **A glossary of the project's terms,** each with its English original. The handed-in report and deck usually
  use the English terms, so the reader must know both.

## A personal document per member

Each member gets the sections the user chose for them, and members can differ. One may get the demo runbook and
another not.

- **Study of their own part.** Deeper than the primer, but still in plain language:
  - the design decisions, the alternatives and why they were rejected;
  - how the part connects to the rest of the system;
  - where it lives in the code;
  - the numbers to know by heart.
- **Presentation script.** The talk minute by minute, keyed to the final deck's slide numbers and titles. For
  each slide:
  - what to say, as natural sentences they can adapt;
  - what to point at;
  - the transition to the next slide and the running time;
  - for a team talk, the hand-overs between presenters.
- **Demo runbook**, for whoever runs the demo:
  - prerequisites, setup and start commands, URLs and ports;
  - the click-by-click path, with what to show and say at each step, and screenshots of the expected screens;
  - what to do when a step fails, and how to reset for another run.
- **Demo cheat sheet.** One or two printable pages: only the commands, URLs and steps, in order, for use during
  the demo itself.
- **Likely questions with answers.** The questions an instructor would ask about this part and about the project
  as a whole: design choices, alternatives, evaluation validity, numbers, limitations, "what if" questions. Each
  answer is short, accurate and consistent with the report.

## Test the demo before writing about it

Run the demo yourself from a clean state, following the runbook word for word. Use a browser automation tool for a
web interface, and capture the screenshots for the runbook as you go. Fix every step that does not work as
written. A runbook that fails on stage is worse than none.

## Format

- **Language.** Use the language agreed at intake. Without an instruction it is Turkish, with the term rule from
  `settings.md`: the original English term in parentheses right after every technical term, and the English form
  of borrowed jargon.
- **Output.** A polished PDF per document.
- **Toolchain.** A LaTeX article, or HTML with print CSS rendered by headless Chrome, both work well. Pick one and
  use it for every study document, so they look like a set.
- **Visuals and pages.** Diagrams are vector graphics. Check every page visually, with the same "no wasted space"
  standard as the report.
- **Order of work.** Write these documents last, so the script matches the final slides and the numbers match the
  final report.
