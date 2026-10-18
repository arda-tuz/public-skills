# web-course-complete

A model-agnostic skill for working through a web course from its current progress to verified completion, including local practice and the course completion document when one is offered.

- **One primary agent by default.** The same user-selected model operates the browser and computer, solves questions, writes code and performs required local setup. A separate installation subagent is optional and is created only when the user chooses it.
- **Resume the existing environment.** Reuse the signed-in account, open course tab, installed tools, virtual machines and verified answers. Repair or install only what is actually needed.
- **Small continuation state.** Keep the current location and next action in one `state.md`, alongside necessary coursework and the final completion document. Skipped sections, when allowed, use a short `skipped.md` containing only their numbers and titles.
- **Verify the real result.** Check platform feedback, exam results and the downloaded document. Keep platform completion separate from local practice that was actually performed.

## Requirements

An agent harness with browser and computer-use tools, plus terminal and file access when the course requires local setup or coding. Select a model supported by that harness. This skill supplies instructions, not model binaries or a provider-routing service.

The skill instructions and the required opening prompt are in Turkish. The opening prompt preserves the original Cisco course benchmark context; the course workflow applies to other web courses as well.

## Install

Follow the repository's [installation guide](../../README.md#install) using the skill name `web-course-complete`. For example:

```bash
npx skills add arda-tuz/public-skills --skill web-course-complete --agent codex --global
```

Choose `claude-code` instead of `codex` for Claude Code, or use another supported agent id.

## Use

In Codex:

```text
$web-course-complete Complete the course at <course URL>, starting from my existing progress.
```

In Claude Code, use `/web-course-complete`; as a plugin, use `/web-course-complete:web-course-complete`.

At startup the skill asks which primary model to use and whether the same agent should perform installations. Choices already given in the conversation are retained. The required benchmark opening prompt precedes the selected model's course task; course-specific context follows it.

Course state, credentials, downloads and completion documents belong in the course workspace, outside this skill repository.
