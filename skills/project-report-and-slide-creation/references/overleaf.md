# Keeping the report in sync with Overleaf

Use the `overleaf` skill's CLI, `olcli`. One olcli feature is essential: `push` must keep nested folders. Check the
version on PATH: `olcli push --help` or its README should mention nested folders, and `olcli pdf --help` should
offer `-r`.
- Old releases flatten `sections/x.tex` into the project root, which breaks the layout.
- If the CLI on PATH is old, put a current `@aloth/olcli` in front of it before doing anything else.

## Credentials without touching the user's global login

- **Where the cookie goes.** Write the `overleaf_session2` cookie value into `deliverables/report-<kind>/.olauth`
  and `chmod 600` it, in the order given under "Project setup". `olcli` reads `.olauth` from the folder it runs in.
- **Why not a global login.** Do not use `olcli auth`: it would overwrite whatever account the user's global
  config holds.
- **Keeping it private.**
  - The ignore rule comes first. A cookie file that exists before its rule can enter the project's git history
    through any `git add -A`.
  - The template's `.gitignore` already lists `.olauth`.
  - `olcli` never uploads dotfiles, and the template's `.olignore` lists `.olauth` again as a second guard.
  - The `push --dry-run --show-ignored` step below confirms that the file stays local.
  - Never print the cookie, and never write it to notes, logs or any other file.
- **Checking it works.** From the report folder, run `olcli auth status` (called `olcli whoami` before 0.16) and
  `olcli list`. If the cookie is rejected or
  shows no projects, stop and ask for a fresh one. This is one of the few blockers worth a question.

## Project setup

Do this before copying the rest of the template, so the pull cannot clash with it. Every command runs from the
report folder, because that is where `.olauth` and the `.olcli.json` written by the pull live.

1. Create `deliverables/report-<kind>/` and `cd` into it.
2. Copy the template's `.gitignore` and `.olignore` into it. If an installer dropped them, write a `.gitignore`
   that lists `.olauth`. Inside a git repository, `git check-ignore -q .olauth` must now succeed.
3. Only then write `.olauth` and `chmod 600` it.
4. If no project has the name, create one with `olcli project create "<name>"` (blank).
5. Run `olcli pull "<name>" .`.
6. If the pulled content is anything more than an empty template, back it up before replacing anything:
   `olcli zip "<name>" -o ../notes/overleaf-backup-before-<kind>.zip`. Without `-o` the zip lands in the report
   folder and goes up with the next push.
7. Copy `assets/ieee-report/.` over it.
- **Main document.** Keep the root document as `main.tex`, which is Overleaf's default.
  - If an existing project has a different main document, compile with `-r main.tex`.
  - Tell the user in the summary that they can set *Menu → Main document* to `main.tex`. Alternatively, delete the
    stale root file after the backup, if it is clearly superseded.

## Push, compile, verify

```bash
olcli push --dry-run --show-ignored   # see what will go up; local PDFs and build files stay local
olcli push --all                      # first upload; later pushes upload only changed files
olcli pdf -r main.tex -o ../<kind>-report.pdf
olcli output log -r main.tex -o ../notes/overleaf-<kind>.log
olcli diff --name-only                # empty when the remote matches the local folder
```

- **Read the Overleaf log as closely as the local one.** Overleaf runs a newer TeX Live, so a clean local build
  is not proof.
- **The delivered PDF is the Overleaf one.** Its page count must match the local build.
- **Deletions are opt-in.** Use `push --delete` only for files this run created or replaced, after the backup.

## Local only

When the user has no Overleaf project, compile locally, deliver the folder, and also deliver a zip of it. The zip
is ready to upload as a new Overleaf project. The structure is the same, so it compiles there unchanged.
