# study-buddy

A study partner skill for a course and its exams (quiz, midterm, final). Point it at the folder that holds your course material: slides, lecture notes, books, past exams, answer keys. It turns that folder into a study system that keeps itself up to date, explains topics from the big picture down to the details, and builds study material aimed at what is likely to be asked.

- **A folder that remembers.** At setup the agent writes an `AGENTS.md` and a `kb/` folder of Markdown files: course settings and exam dates, a map of every file, learned preferences, an exam analysis, a question bank, progress and decisions. Every later session, in any agent, reads them first and continues where the last one stopped.
- **Your sources stay untouched.** Original files are read only. A small script (`tools/buddy.py`, written into the folder at setup) extracts their text page by page into `kb/text/` and notices new, changed or removed files, so new slides or a newly published exam are folded in automatically.
- **Past questions drive the plan.** Every past question is normalized into one bank with its answer, its source location and why the answer is right. The analysis records the instructor's question style, distractor patterns and how often each unit and page was asked, and turns that into study priorities.
- **Grounded explanations.** Every claim carries its location (`L3 s.15`). You choose how far the agent may go beyond your sources, from "only the slides" to "teach freely"; anything from outside is labeled.
- **Study material.** Practice exams in the real exam's format with a separate answer key, annotated slides that mark each page as memorize, know, skim or skip, a standalone reading guide, cheat sheets and flashcards. Interactive pages also come as portrait and landscape PDFs for annotating on a tablet.
- **It learns from you.** A preference, correction or piece of exam information you give is applied at once and written into the folder, so you never have to repeat it. Preferences that hold for every course can be promoted into the skill's own defaults.

## Language

The defaults come from a Turkish-speaking student: explanations are written in Turkish with the English technical term in parentheses, and the file templates and PDF labels default to Turkish (the PDF labels also exist in English). Practice questions follow the exam's own language. Tell the agent your language at setup and it records that as a course preference.

## Requirements

- Python 3.8 or newer.
- [PyMuPDF](https://pymupdf.readthedocs.io) 1.25 or newer for PDF text extraction and PDF output: `pip install -U pymupdf`.
- `python-pptx` and `python-docx` only if the course has PowerPoint or Word files.
- Optional: `mmdc` ([Mermaid CLI](https://github.com/mermaid-js/mermaid-cli)) for diagrams in annotated slides; without it the diagrams are skipped with a warning.

The skill writes its scripts into the course folder when it needs them, so there is nothing else to install.

## Install

Follow the repository's [installation guide](../../README.md#install) using the skill name `study-buddy`. For example:

```bash
npx skills add arda-tuz/public-skills --skill study-buddy --agent claude-code --global
```

## Use

Open the agent in your course folder and say what you are preparing for:

```text
/study-buddy Set up this folder for my midterm on 12 November and map the past exam questions.
```

In Codex use `$study-buddy`; as a Claude Code plugin, `/study-buddy:study-buddy`. The agent reads the folder, shows how it understood each file and asks the remaining questions (exam format and scope, how far beyond the sources to go, what you already know) in one numbered list, so you can answer everything in a single reply. After setup you can simply ask: "explain chapter 4", "what should I study today?", "make a practice exam", "annotate the week 3 slides".

## License

MIT, see [LICENSE](LICENSE).
