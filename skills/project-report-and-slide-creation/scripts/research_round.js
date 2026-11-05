export const meta = {
  name: 'project-report-research-round',
  description: 'One literature research round for a project report: search, verify, collect into one folder',
  whenToUse: 'Started by the project-report-and-slide-creation skill, at most once per run',
  phases: [
    { title: 'Search', detail: 'one web search agent per research question' },
    { title: 'Verify', detail: 'one reviewer per question re-checks every source' },
    { title: 'Collect', detail: 'one agent writes the research folder and BibTeX' },
  ],
}

// Everything that can change over time (models, efforts, limits) arrives in `args`, read by the main agent from
// the skill's settings.md. Nothing about the team is fixed here.
//
// args = {
//   outDir:   absolute path of the research folder to create,
//   accessed: today's date (scripts cannot read the clock),
//   brief:    the project in a few paragraphs: problem, methods, data, metrics, results, and what the report
//             needs from the literature,
//   questions: [{ id, question, why, looking_for }],
//   existing: { bibKeys: [...], sources: 'sources the report already has, one per line' },
//   team: { search: {model, effort}, review: {model, effort}, collect: {model, effort},
//           maxConcurrent, maxSourcesPerQuestion },
// }

const a = args || {}
const missing = ['outDir', 'accessed', 'brief', 'questions', 'team'].filter(k => !a[k])
if (missing.length) throw new Error(`research_round: missing args ${missing.join(', ')} (see the skill's references/research-round.md)`)
for (const role of ['search', 'review', 'collect']) {
  if (!a.team[role]) throw new Error(`research_round: team.${role} is missing (read it from settings.md)`)
}
const team = a.team
const maxConcurrent = Math.max(1, team.maxConcurrent || 4)
const maxSources = team.maxSourcesPerQuestion || 8
const existingKeys = (a.existing && a.existing.bibKeys) || []
const existingSources = (a.existing && a.existing.sources) || 'none'

const RESULT = {
  type: 'object',
  properties: {
    metric: { type: 'string' }, value: { type: 'string' }, dataset: { type: 'string' },
    setting: { type: 'string' }, location: { type: 'string' },
  },
  required: ['metric', 'value'],
}
const SOURCE = {
  type: 'object',
  properties: {
    title: { type: 'string' },
    authors: { type: 'array', items: { type: 'string' } },
    year: { type: 'string' },
    venue: { type: 'string' },
    kind: { type: 'string', enum: ['journal', 'conference', 'preprint', 'book', 'thesis', 'dataset', 'software', 'web', 'other'] },
    doi: { type: 'string' },
    url: { type: 'string', description: 'the page that was actually opened' },
    bibtex: { type: 'string', description: 'built from the source page, not from memory' },
    relevance: { type: 'string', description: 'how it relates to the project and to the question' },
    key_points: { type: 'array', items: { type: 'string' }, description: 'usable statements, each with where it appears' },
    reported_results: { type: 'array', items: RESULT },
  },
  required: ['title', 'authors', 'year', 'url', 'bibtex', 'relevance'],
}
const SEARCH = {
  type: 'object',
  properties: {
    question_id: { type: 'string' },
    sources: { type: 'array', items: SOURCE },
    notes: { type: 'string', description: 'dead ends, paywalls, what could not be found' },
  },
  required: ['question_id', 'sources'],
}
const REVIEW = {
  type: 'object',
  properties: {
    question_id: { type: 'string' },
    reviewed: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          ...SOURCE.properties,
          status: { type: 'string', enum: ['verified', 'corrected', 'rejected'] },
          reason: { type: 'string', description: 'what was checked, what was fixed, or why it was rejected' },
        },
        required: ['title', 'status', 'reason'],
      },
    },
    still_missing: { type: 'string' },
  },
  required: ['question_id', 'reviewed'],
}
const COLLECT = {
  type: 'object',
  properties: {
    folder: { type: 'string' },
    files: { type: 'array', items: { type: 'string' } },
    kept: { type: 'integer' },
    rejected: { type: 'integer' },
    keys: { type: 'array', items: { type: 'string' }, description: 'citation keys written to references.bib' },
    gaps: { type: 'array', items: { type: 'string' } },
    summary: { type: 'string', description: 'a short paragraph the main agent reads first' },
  },
  required: ['folder', 'files', 'kept', 'rejected', 'keys', 'summary'],
}

const searchPrompt = q => `You are one search agent in a literature research round for an academic report about a finished project.

Project brief:
${a.brief}

Your research question (${q.id}): ${q.question}
Why the report needs it: ${q.why || 'see the brief'}
Looking for: ${q.looking_for || 'the strongest citable sources that answer the question'}

Sources the report already has (do not return these again):
${existingSources}

Search the web; load the WebSearch and WebFetch tools with ToolSearch if they are not loaded yet. Prefer primary,
citable sources: peer-reviewed papers, arXiv preprints, theses, official dataset and software documentation. Open
every source before you return it and take its bibliographic data from the page you opened. Return at most
${maxSources} sources, strongest first. For each give the BibTeX entry, the points the report could use (with where
they appear in the source), and every reported number with its metric, dataset and setting, so it can be compared
with the project's own results. Put dead ends and anything you could not reach in notes.`

const reviewPrompt = (found, q) => `You verify one search agent's sources for an academic report. Nothing unverified may reach the report.

Research question (${q.id}): ${q.question}

Sources to check:
${JSON.stringify(found.sources, null, 1)}

Search agent notes: ${found.notes || 'none'}

Open each source's DOI, arXiv or publisher page yourself (WebFetch, WebSearch; load them with ToolSearch if needed).
Mark it verified when it exists, its bibliographic data and BibTeX match the page, and every key point and number is
stated in the source as reported. Mark it corrected when it exists but something was wrong; fix the fields and say
what changed. Mark it rejected when it cannot be found, does not say what was claimed, or does not help with the
question. When you cannot confirm a source, reject it. Return every source with its status and reason, and say what
the question still lacks.`

const collectPrompt = reviewed => `You assemble the research folder for an academic report. Write files only inside ${a.outDir} (create it).

Project brief:
${a.brief}

Access date for web sources: ${a.accessed}
Citation keys the report already uses (do not reuse them): ${existingKeys.join(', ') || 'none'}

Reviewed sources, by research question:
${JSON.stringify(reviewed, null, 1)}

Keep only sources whose status is verified or corrected. Merge duplicates across questions. Give each kept source a
unique, readable citation key (first author's surname, year, first title word, lowercase).

Write these files:
- references.bib: one entry per kept source, with the fields IEEEtran.bst uses (author, title, journal or booktitle,
  year, volume, number, pages, publisher, doi, url). Web pages and software get url and a note with the access date.
- literature.md: for each research question, what the literature establishes and how the project relates to it
  (builds on, differs from, compares with), every statement backed by citation keys. Write it so that a related-work
  section can be drafted from it directly.
- comparisons.md: a table of published results that can be set against the project's own metrics: key, metric,
  value, dataset, setting, and how comparable it is to the project's setup (same data and protocol, or not).
- sources.json: every reviewed source with its status and reason, rejected ones included.
- README.md: what each file holds, the counts (kept, rejected), and the gaps that remain.
- ROUND_DONE: one line with the access date and the counts. Its presence records that the research round has run.

Then return the summary.`

const reviewed = []
for (let i = 0; i < a.questions.length; i += maxConcurrent) {
  const chunk = a.questions.slice(i, i + maxConcurrent)
  const done = await pipeline(
    chunk,
    q => agent(searchPrompt(q), {
      label: `search:${q.id}`, phase: 'Search', schema: SEARCH, model: team.search.model, effort: team.search.effort,
    }),
    (found, q) => found && agent(reviewPrompt(found, q), {
      label: `verify:${q.id}`, phase: 'Verify', schema: REVIEW, model: team.review.model, effort: team.review.effort,
    }),
  )
  done.forEach((r, j) => {
    if (r) reviewed.push(r)
    else log(`${chunk[j].id}: no reviewed result (search or review failed); the collector lists it as a gap`)
  })
}

phase('Collect')
const lost = a.questions.filter(q => !reviewed.some(r => r.question_id === q.id)).map(q => q.id)
const summary = await agent(collectPrompt({ reviewed, questions_without_result: lost }), {
  label: 'collect', phase: 'Collect', schema: COLLECT, model: team.collect.model, effort: team.collect.effort,
})
if (!summary) throw new Error('research_round: the collector did not finish; the reviewed sources are in this run\'s journal')
return { ...summary, questions: a.questions.length, questions_without_result: lost }
