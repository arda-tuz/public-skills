# Public skills

Agent skills I build and want to share with other people. Instead of a separate repository per skill, every skill I publish lives here, each in its own folder under [`skills/`](skills). They follow the open [Agent Skills](https://agentskills.io) format (a folder with a `SKILL.md`), so they work in Claude Code, Codex and the other agents that support skills, unless a skill says otherwise.

## Skills

| Skill | What it does | Works in |
|---|---|---|
| [`create-uml-seq-diagram`](skills/create-uml-seq-diagram) | Exam-ready UML class and sequence diagrams | Any agent with Python 3.10+ |
| [`timed-commit-automation`](skills/timed-commit-automation) | Gradual, scheduled migration of a project between GitHub repositories | Claude Code only |

### create-uml-seq-diagram

Draws UML class diagrams and UML sequence diagrams in standard OMG UML 2.5.1 notation, at the level a strict examiner would give full marks: every symbol is standard and nothing optional is added. The agent models the diagram in text and lays it out with a small Python library that fixes the notation, and a checker rejects non-standard input and uses headless Chrome to catch overlapping labels. The result is a self-contained HTML page with inline SVG; SVG or PNG export is available on request. [More, with example images](skills/create-uml-seq-diagram/README.md).

### timed-commit-automation

Moves a finished project from one GitHub repository to another as a calendar of meaningful commits. You give the deadlines in plain language ("backend and frontend by 19 November, everything by 1 December"), review the commit calendar it proposes, and a Claude Code cloud routine then creates and pushes each commit on its planned day, authored by your own GitHub account and never backdated. The calendar and progress reports stay in the source repository; the destination receives only the project's files. It needs Claude Code cloud routines. [More](skills/timed-commit-automation/README.md).

## Install

Each skill can be installed at two levels:

- **User level:** available to you in every project on your machine.
- **Project level:** stored inside one repository, so everyone who works on it gets the skill too. Commit the installed folder.

Pick one of the methods below and replace `SKILL` with a name from the table above. After installing, the agent uses a skill on its own when your request matches it, or you can call it by name (`/SKILL` in Claude Code, `$SKILL` in Codex). If a new skill does not show up, restart the agent.

### Any agent: the `skills` CLI

[`skills`](https://github.com/vercel-labs/skills) installs a skill for one or more agents. It needs Node.js.

```bash
# Project level: run in the repository's root folder
npx skills add arda-tuz/public-skills --skill SKILL --agent claude-code

# User level
npx skills add arda-tuz/public-skills --skill SKILL --agent claude-code --global
```

- `--agent` takes one or more ids: `claude-code`, `codex`, `cursor`, `gemini-cli`, `github-copilot`, `opencode` (or `'*'` for every supported agent).
- For Claude Code the skill goes to `.claude/skills/` (`~/.claude/skills/` at user level). Codex, Cursor, Gemini CLI, GitHub Copilot and OpenCode share one copy in `.agents/skills/` (`~/.agents/skills/`). When you install for Claude Code and another agent together, the Claude Code folder is a symbolic link to that shared copy; add `--copy` to get real copies instead.
- `npx skills add arda-tuz/public-skills --list` lists the skills in this repository, `npx skills update` updates installed skills, and `npx skills remove SKILL` removes one.

### Claude Code: plugin marketplace

This repository is also a Claude Code plugin marketplace with one plugin per skill. Inside Claude Code:

```text
/plugin marketplace add arda-tuz/public-skills
/plugin install SKILL@arda-tuz-skills
```

The install dialog asks for the scope: user, project (shared through the repository's `.claude/settings.json`) or local (this repository, only for you). The same from a terminal:

```bash
# User level
claude plugin marketplace add arda-tuz/public-skills
claude plugin install SKILL@arda-tuz-skills --scope user

# Project level: run in the repository, then commit .claude/settings.json
claude plugin marketplace add arda-tuz/public-skills --scope project
claude plugin install SKILL@arda-tuz-skills --scope project
```

At project level both the marketplace and the plugin are recorded in `.claude/settings.json`, so Claude Code offers the plugin to everyone who opens the repository.

Plugin skills are namespaced: call them as `/SKILL:SKILL`, for example `/timed-commit-automation:timed-commit-automation`. Update with `claude plugin marketplace update arda-tuz-skills` and `claude plugin update SKILL@arda-tuz-skills`. A plugin installed from a terminal loads in the next session, or after `/reload-plugins`.

### Manual copy

Copy the skill's folder into the agent's skills folder. With no installer involved, this works for every agent:

```bash
src="$(mktemp -d)"
git clone --depth 1 https://github.com/arda-tuz/public-skills.git "$src"

# User level for Claude Code; use a folder from the table below for other agents or levels
mkdir -p ~/.claude/skills
cp -R "$src/skills/SKILL" ~/.claude/skills/
rm -rf "$src"
```

| Agent | User level | Project level |
|---|---|---|
| Claude Code | `~/.claude/skills/` | `.claude/skills/` |
| Codex | `~/.agents/skills/` | `.agents/skills/` |
| Gemini CLI | `~/.gemini/skills/` or `~/.agents/skills/` | `.gemini/skills/` or `.agents/skills/` |
| GitHub Copilot | `~/.copilot/skills/` or `~/.agents/skills/` | `.github/skills/` or `.agents/skills/` |
| Cursor | `~/.cursor/skills/` or `~/.agents/skills/` | `.cursor/skills/` or `.agents/skills/` |
| OpenCode | `~/.config/opencode/skills/` or `~/.agents/skills/` | `.opencode/skills/` or `.agents/skills/` |

`.agents/skills/` is the shared location of the Agent Skills format, so one copy there serves every agent in the table except Claude Code. The folder name must stay equal to the skill name. To update, copy the folder again.

### Agent-specific installers

These also work, if you already use the tool:

```bash
# GitHub CLI 2.90 or newer (skills are a preview feature); --scope user or project
gh skill install arda-tuz/public-skills skills/SKILL --agent claude-code --scope user

# Gemini CLI; --scope user or workspace
gemini skills install https://github.com/arda-tuz/public-skills.git --path skills/SKILL --scope user
```

## Repository layout

```text
skills/<name>/              one folder per skill
  SKILL.md                  instructions the agent loads
  README.md                 description for people
  LICENSE
  agents/openai.yaml        Codex display metadata
  scripts/ references/ assets/
.claude-plugin/marketplace.json   Claude Code marketplace, one plugin per skill
```

## License

MIT, see [LICENSE](LICENSE). Each skill folder carries its own license file; `create-uml-seq-diagram` also keeps the notice of the project it is forked from.
