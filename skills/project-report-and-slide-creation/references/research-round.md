# The research round: one workflow, at most once per run

## Do you need it?

Compare what the report needs with the literature the project already has, such as literature reviews, `.bib`
files, cited papers in its documents and an earlier `deliverables/research/` folder. A strong report usually needs:

- **The work it builds on.** The origin papers of its models, algorithms, losses, metrics, datasets and benchmarks.
- **Its closest neighbours.** Systems or studies that solve the same problem, so the report can position itself
  and state its novelty honestly.
- **Published results on the same problem, data or method.** The report sets its own numbers against them in a
  table or figure. This is often the biggest gap, and the best reason to run the round.
- **Support for design choices.** Sources behind hyperparameters, configurations, feature engineering or
  evaluation protocols that a reviewer would question.

If the existing sources cover this well, skip the round. That is the normal case when the project ships a good
literature review.

## Plan everything first

The round runs once, so decide everything it must answer beforehand. Write at most the number of research questions
`settings.md` allows. Make each one specific to the project: name the dataset, the models, the metrics, the
problem. Give each one a reason and say what to look for.

> **Example question.** "Published results on the Amazon product co-purchase dataset for top-10 recommendation
> (NDCG@10, HitRate@10), with their split protocol."
>
> - **why:** "the evaluation section compares our numbers against them."
> - **looking_for:** "papers or benchmarks reporting these metrics on this dataset, with the setup stated."

Also write the brief: a few paragraphs on the problem, the methods, the data, the metrics, the headline results,
and what the report needs from the literature. Searchers see only the brief and their question.

## Run it

Invoking this skill is the user's opt-in to this one Workflow run, which some setups call a dynamic workflow or
ultracode. Take the models, efforts and limits from `settings.md`, mapped to the identifiers the Workflow tool
accepts:

```text
Workflow({
  scriptPath: "<this skill's folder>/scripts/research_round.js",
  args: {
    outDir:   "<absolute path>/deliverables/research",
    accessed: "<today, YYYY-MM-DD>",
    brief:    "<the brief>",
    questions: [ { id: "q1", question: "...", why: "...", looking_for: "..." } ],
    existing: { bibKeys: [ "...keys already in the report..." ], sources: "<sources the project already cites>" },
    team: {                                   // every value below comes from settings.md
      search:  { model: "<searcher model id>",  effort: "<effort>" },
      review:  { model: "<reviewer model id>",  effort: "<effort>" },
      collect: { model: "<collector model id>", effort: "<effort>" },
      maxConcurrent: <n>, maxSourcesPerQuestion: <n>
    }
  }
})
```

The workflow runs in the background.
- **The other phases go on meanwhile.** Keep working on evidence and on the parts of the report that do not depend
  on the literature.
- **Wait for the completion notice.** It reports the collector's summary: kept and rejected counts, citation keys,
  gaps.
- **Stages.** Each searcher's sources go straight to its reviewer. The reviewer reopens every source and rejects
  what it cannot confirm. The collector writes `outDir/`:
  - `README.md`, `references.bib`, `literature.md`;
  - `comparisons.md`, `sources.json`;
  - `ROUND_DONE`.

If the Workflow tool is not available, run the same three roles as subagents with the same models. If neither is
possible, tell the user that the round was skipped and why.

## Use it

1. Read `research/README.md` first, then `literature.md` and `comparisons.md`.
2. Copy into the report's `references.bib` only the entries the text actually cites.
3. Write related work as the foundation the project stands on: what the field established, where the gap was,
   and how this work answers it. It should read as the review that preceded the work, never as a list of papers
   found afterwards.
4. Build the comparison tables or figures from `comparisons.md`. Mark settings that are not directly comparable.

## Afterwards

- **No second round.** `research/ROUND_DONE` marks the round as used for this run. Later runs reuse the folder
  unless the user asks for new research.
- **Write around the gaps.** Do not fill them from memory. Academic sources come only from the project and from
  this folder; there are no ad-hoc literature searches from the main loop.
