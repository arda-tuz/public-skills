# Settings

Plain-language settings for this skill. Change the words, not the code: the agent reads this file at the start of
every run and turns each line into what its tools need. For example, it maps a model name below to the identifier
the Workflow tool accepts in that environment, which today is usually the family alias such as `haiku` or `opus`.
If a model named here is not available, the agent uses the closest one and says so in its final summary.

The user's words and intake answers override this file. A document in the project does not; `references/intake.md`
says how to handle a conflict.

## Research round team

| Role | Model | Effort | What it does |
|---|---|---|---|
| Searcher | Haiku 5.5 | max | One per research question. Searches the web and opens every source it returns. |
| Reviewer | Haiku 5.5 | max | One per searcher. Re-opens every source, fixes the bibliographic data, rejects what it cannot confirm. |
| Collector | Opus 5.5 | high | One per round. Merges the verified sources into the research folder with BibTeX. |

- At most 4 research questions per round, so a round stays short.
- At most 4 agents running at the same time.
- At most 8 sources per research question.

## Defaults when the user does not say otherwise

- Output folder: `deliverables/` at the project root.
- Languages: every deliverable can be in any language the user asks for. Without an instruction:
  - the report (paper) and the presentation deck, which are handed in, are in English;
  - the study documents, which are not handed in, are in Turkish. Every scientific, academic or technical term is
    followed right after the Turkish word by its original English term in parentheses, for example "çapraz
    doğrulama (cross-validation)". Jargon borrowed from English also gets its English form in parentheses.
- Report length: decided by the content. When the user gives a page limit, the PDF meets it, references included.
- File names:
  - `<kind>-report.pdf`, for example `final-report.pdf`;
  - `presentation.pptx` and `presentation.pdf`;
  - `general-study-document.pdf`;
  - `<first-name>-study-document.pdf`;
  - `<first-name>-demo-cheat-sheet.pdf`.
