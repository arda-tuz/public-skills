#!/usr/bin/env bash
# End-to-end test of tca.py (run: scripts/e2e_test.sh).
# Local bare repositories stand in for GitHub. Every routine run uses fresh,
# shallow, side-by-side clones with a claude/* branch checked out and a dirty
# working tree, the way a cloud routine session looks. Dates are relative to
# today, so the test never expires.
set -euo pipefail

SKILL="$(cd "$(dirname "$0")/.." && pwd)"
ENGINE="$SKILL/scripts/tca.py"
FOLDER="timed-commit-automation-skill"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

export GIT_CONFIG_GLOBAL="$WORK/gitconfig" GIT_CONFIG_NOSYSTEM=1
git config --global init.defaultBranch main
git config --global user.name "Local Dev"
git config --global user.email "local@example.com"
unset CLAUDE_CODE_REMOTE TCA_TARGET
# A gh that always fails keeps the test offline and away from any real GitHub account.
mkdir -p "$WORK/bin"
printf '#!/bin/sh\nexit 1\n' > "$WORK/bin/gh" && chmod +x "$WORK/bin/gh"
export PATH="$WORK/bin:$PATH"

pass() { echo "PASS: $*"; }
fail() {
  echo "FAIL: $*" >&2
  if [ -s "$WORK/stderr" ]; then sed 's/^/  stderr: /' "$WORK/stderr" >&2; fi
  exit 1
}
check() {  # check "description" command...: fail unless the command succeeds
  local what="$1"; shift
  "$@" || fail "$what"
}
day() {
  python3 -c 'import datetime, sys, zoneinfo
t = datetime.datetime.now(zoneinfo.ZoneInfo("Europe/Istanbul")).date()
print(t + datetime.timedelta(days=int(sys.argv[1])))' "$1"
}
weekday() {
  python3 -c 'import datetime, sys
print(("mon","tue","wed","thu","fri","sat","sun")[datetime.date.fromisoformat(sys.argv[1]).weekday()])' "$1"
}
for n in 0 2 4 6 8 9 10 12 13 17 20 21 22; do eval "D$n=$(day "$n")"; done
D14="$(day 14)"; D15="$(day 15)"; D16="$(day 16)"

# run_with ENGINE_PATH ARGS...: sets OUT (stdout), RC and LAST (the JSON line)
run_with() {
  local engine="$1"; shift
  set +e
  OUT="$(python3 -I "$engine" "$@" 2>"$WORK/stderr")"
  RC=$?
  set -e
  LAST="$(printf '%s\n' "$OUT" | tail -n 1)"
}
run() { run_with "$ENGINE" "$@"; }
field() {  # evaluate a Python expression on the last JSON result
  python3 -c 'import json, sys
d = json.loads(sys.argv[2])
print(eval(sys.argv[1], {}, {"d": d}))' "$1" "$LAST"
}
has() {  # has EXPR TEXT: the field's text contains TEXT
  field "$1" | grep -q -- "$2"
}
is() {  # is EXPR VALUE: the field equals VALUE
  [ "$(field "$1")" = "$2" ]
}
state() {  # evaluate a Python expression on the calendar state stored in the source repo
  git -C "$WORK/acme/source.git" show "main:$FOLDER/calendar.md" > "$WORK/cal.md"
  python3 - "$1" "$WORK/cal.md" <<'PY'
import json, sys
text = open(sys.argv[2], encoding="utf-8").read()
block = text.split("<!-- tca:state:begin -->")[1].split("<!-- tca:state:end -->")[0].strip()
d = json.loads(block.removeprefix("```json").removesuffix("```"))
print(eval(sys.argv[1], {}, {"d": d}))
PY
}
fresh_clones() {  # $1 = folder; clones both repositories for local (planning) use
  git clone --quiet "$WORK/acme/source.git" "$1/source" 2>/dev/null
  git clone --quiet "$WORK/acme/target.git" "$1/target" 2>/dev/null
}
routine() {  # one cloud-like run on simulated day $1
  local s="$WORK/session-$RANDOM$RANDOM"
  mkdir -p "$s"
  git clone --quiet --depth 1 "file://$WORK/acme/source.git" "$s/source" 2>/dev/null
  git clone --quiet --depth 1 "file://$WORK/acme/target.git" "$s/target" 2>/dev/null
  git -C "$s/source" checkout --quiet -b claude/routine-run
  echo "scratch" > "$s/source/backend/app.py"
  set +e
  OUT="$(cd "$s" && python3 -I "$s/source/$FOLDER/tca.py" run --today "$1" 2>"$WORK/stderr")"
  RC=$?
  set -e
  LAST="$(printf '%s\n' "$OUT" | tail -n 1)"
  echo "  routine $1: rc=$RC $(printf '%s' "$LAST" | cut -c1-150)"
}
cloud_routine() {  # a routine run as in a cloud session: issue reporting on, gh stand-in on PATH
  local saved="$PATH"
  export PATH="$WORK/ghstub:$PATH" CLAUDE_CODE_REMOTE=1
  routine "$1"
  export PATH="$saved"
  unset CLAUDE_CODE_REMOTE
}
src_head() { git -C "$WORK/acme/source.git" rev-parse main; }
tgt_count() { git -C "$WORK/acme/target.git" rev-list --count main 2>/dev/null || echo 0; }
pushed_now() { field '[p["number"] for p in d.get("pushed_now", d.get("pushed", []))]'; }
edit_json() {  # $1 = file, $2 = Python statements operating on d
  python3 - "$1" "$2" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
exec(sys.argv[2])
json.dump(d, open(sys.argv[1], "w"), indent=2)
PY
}

# ---------------------------------------------------------------- the project
mkdir -p "$WORK/acme"
git init --quiet --bare "$WORK/acme/source.git"
git init --quiet --bare "$WORK/acme/target.git"
git clone --quiet "$WORK/acme/source.git" "$WORK/dev" 2>/dev/null
cd "$WORK/dev"
mkdir -p backend/api backend/models backend/db frontend/src/components frontend/src/pages \
  ai/vision/local ai/vision/cloud ai/llm ai/common tests docs scripts .github/workflows
printf 'node_modules/\n*.log\n' > .gitignore
echo '{"name": "demo"}' > package.json
printf '#!/bin/sh\necho run\n' > scripts/run.sh && chmod +x scripts/run.sh
echo "print('app')" > backend/app.py
echo "routes = []" > backend/api/routes.py
echo "def login(): pass" > backend/api/auth.py
echo "class User: pass" > backend/models/user.py
echo "CREATE TABLE users (id int);" > backend/db/schema.sql
echo "<html></html>" > frontend/index.html
echo "app()" > frontend/src/app.js
echo "button()" > frontend/src/components/button.js
echo "home()" > frontend/src/pages/home.js
echo "def infer(): pass" > ai/vision/local/infer.py
head -c 4096 /dev/urandom > ai/vision/local/model.onnx
echo "def call(): pass" > ai/vision/cloud/api.py
echo "def chat(): pass" > ai/llm/chat.py
echo "def norm(): pass" > ai/common/utils.py
echo "def test_backend(): pass" > tests/test_backend.py
echo "def test_ai(): pass" > tests/test_ai.py
echo "# Guide" > docs/guide.md
echo "# Old notes" > docs/old.md
echo "# Demo" > README.md
echo "Use the tools" > CLAUDE.md
printf 'name: ci\non: push\n' > .github/workflows/ci.yml
echo "debug" > keep.log && git add -f keep.log
git add -A && git commit --quiet -m "wip" && git push --quiet origin main
cd "$WORK"

write_draft() {  # $1 = path, $2 = weekday stated for the first milestone
  python3 - "$1" "$2" "$D0" "$D12" "$D20" <<'PY'
import json, sys
path, weekday, d0, d12, d20 = sys.argv[1:]
draft = {
    "source": {"repo": "acme/source"},
    "target": {"repo": "https://github.com/acme/target.git"},
    "author": {"name": "Test User", "email": "123+test@users.noreply.github.com"},
    "timezone": "Europe/Istanbul",
    "schedule": {"start": d0},
    "exclude": ["CLAUDE.md"],
    "milestones": [
        {"id": "core", "title": "Backend, frontend and local vision", "deadline": d12, "weekday": weekday,
         "request": "backend, frontend and the vision parts that use local models",
         "scope": ["backend/", "frontend/", "ai/vision/local/", "ai/common/"]},
        {"id": "everything", "title": "Whole project", "request": "the whole project",
         "deadline": d20, "scope": ["**"]},
    ],
    "commits": [
        {"message": "chore: initialize project tooling", "paths": [".gitignore", "package.json", "scripts/", ".github/"]},
        {"message": "feat(db): add schema and user model", "paths": ["backend/db/", "backend/models/"]},
        {"message": "feat(api): add API routes and auth\n\nAdds the REST endpoints.\n#42 tracks rate limiting.",
         "paths": ["backend/api/", "backend/app.py"]},
        {"message": "feat(frontend): add app shell and components", "paths": ["frontend/"]},
        {"message": "feat(vision): add local model inference", "paths": ["ai/common/", "ai/vision/local/"]},
        {"message": "feat(ai): add cloud vision and chat", "paths": ["ai/"]},
        {"message": "test: add test suites", "paths": ["tests/"]},
        {"message": "docs: add readme, guide and ci", "paths": ["**"]},
    ],
}
json.dump(draft, open(path, "w"), indent=2)
PY
}

# ---------------------------------------------------------------- planning
mkdir -p "$WORK/local"
fresh_clones "$WORK/local"
L="$WORK/local"

run inspect --source "$L/source" --target "$L/target"
check "inspect failed: $LAST" [ "$RC" = 0 ]
check "inspect missed CLAUDE.md" is 'd["source"]["ai_tool_files"]' "['CLAUDE.md']"
check "inspect: target should be empty" is 'd["target"]["empty"]' True
check "inspect: wrong file count" is 'd["source"]["files"]' 25
check "inspect: CI files not reported" is 'd["source"]["ci_files"]' "['.github/workflows/ci.yml']"
pass "inspect reports structure, AI tool files, workflows and the empty destination"

write_draft "$WORK/draft.json" "$(weekday "$D13")"
run plan --draft "$WORK/draft.json" --source "$L/source" --target "$L/target" --out "$WORK/preview" --today "$D0"
check "a weekday mismatch must hold the plan back: $LAST" [ "$RC" = 1 ]
check "a weekday mismatch must be a question for the user: $LAST" is 'd["status"]' questions
check "weekday question not asked" has 'd["questions"]' "Which date is meant?"
check "the review must still show dates while a question is open" grep -q "^| 1 | " "$WORK/preview/review.md"
check "the review must show what the request said" grep -q "(request says" "$WORK/preview/review.md"
pass "a stated weekday that contradicts the date becomes a question, with a dated review"

write_draft "$WORK/draft.json" "$(weekday "$D12")"
BEFORE="$(src_head)"
run plan --draft "$WORK/draft.json" --source "$L/source" --target "$L/target" --out "$WORK/preview" --today "$D0"
check "valid plan rejected: $LAST" [ "$RC" = 0 ]
python3 - "$WORK/preview/calendar.md" "$D0 $D2 $D4 $D6 $D8 $D12 $D14 $D16" <<'PY' || fail "unexpected schedule"
import json, sys
text = open(sys.argv[1]).read()
block = text.split("<!-- tca:state:begin -->")[1].split("<!-- tca:state:end -->")[0].strip()
d = json.loads(block.removeprefix("```json").removesuffix("```"))
got = " ".join(c["date"] for c in d["commits"])
print("  schedule:", got)
sys.exit(got != sys.argv[2])
PY
check "review lacks the commit count" grep -q "8 commits" "$WORK/preview/review.md"
check "review does not say commit 1 is due today" grep -q "Commit #1 is due today" "$WORK/preview/review.md"
check "review does not show milestone scopes" grep -qF 'ai/vision/local/' "$WORK/preview/review.md"
check "review does not explain where CI configuration goes" grep -q "CI configuration (.github/workflows/ci.yml) arrives with commit #8" "$WORK/preview/review.md"
check "core report missing" test -f "$WORK/preview/progress-report/$D12-core.md"
check "whole-project report missing" test -f "$WORK/preview/progress-report/$D20-everything.md"
check "core report must list its last commit" grep -q "^| 5 |" "$WORK/preview/progress-report/$D12-core.md"
if grep -q "^| 6 |" "$WORK/preview/progress-report/$D12-core.md"; then fail "a later commit lands before the core deadline"; fi
check "plan changed the source repository" [ "$(src_head)" = "$BEFORE" ]
check "plan changed the destination repository" [ "$(tgt_count)" = 0 ]
pass "plan spreads 1 commit/day per milestone window, later commits wait for the deadline, nothing changes"

cp "$WORK/draft.json" "$WORK/bad.json"
edit_json "$WORK/bad.json" "d['schedule']['start'] = '$D8'"
run plan --draft "$WORK/bad.json" --source "$L/source" --target "$L/target" --out "$WORK/bad" --today "$D0"
check "infeasible schedule not reported: $LAST" has 'd["problems"]' "must be in the destination by"
cp "$WORK/draft.json" "$WORK/bad.json"
edit_json "$WORK/bad.json" "d['commits'][2]['paths'] = ['backend/apis/', 'backend/app.py']"
run plan --draft "$WORK/bad.json" --source "$L/source" --target "$L/target" --out "$WORK/bad" --today "$D0"
check "pattern typo not reported: $LAST" has 'd["problems"]' "matches no file"
cp "$WORK/draft.json" "$WORK/bad.json"
edit_json "$WORK/bad.json" "d['commits'].pop()"
run plan --draft "$WORK/bad.json" --source "$L/source" --target "$L/target" --out "$WORK/bad" --today "$D0"
check "unmigrated files not reported: $LAST" has 'd["problems"]' "never reach the destination"
cp "$WORK/draft.json" "$WORK/bad.json"
edit_json "$WORK/bad.json" "d['commits'][0]['message'] += '\n\nCo-Authored-By: Claude <noreply@anthropic.com>'"
run plan --draft "$WORK/bad.json" --source "$L/source" --target "$L/target" --out "$WORK/bad" --today "$D0"
check "trailer in a message not rejected: $LAST" has 'd["problems"]' "must not mention"
cp "$WORK/draft.json" "$WORK/ci.json"
edit_json "$WORK/ci.json" "d['commits'].insert(1, {'message': 'ci: add pipeline', 'paths': ['.github/']})"
run plan --draft "$WORK/ci.json" --source "$L/source" --target "$L/target" --out "$WORK/bad" --today "$D0"
check "a CI-only commit before the last one must be refused: $LAST" has 'd["problems"]' "CI configuration always arrives with the last commit"
run plan --draft "$WORK/bad.json" --source "$L/source" --target "$L/target" --out "$WORK/preview" --today "$D0"
check "an invalid plan must not leave an earlier preview calendar behind" test ! -e "$WORK/preview/calendar.md"
check "an invalid plan must not leave earlier progress reports behind" test ! -e "$WORK/preview/progress-report"
cp "$WORK/draft.json" "$WORK/narrow.json"
edit_json "$WORK/narrow.json" "d['milestones'][0]['scope'] = ['backend/', '!backend/api/', 'frontend/', 'ai/vision/local/', 'ai/common/']"
run plan --draft "$WORK/narrow.json" --source "$L/source" --target "$L/target" --out "$WORK/bad" --today "$D0"
check "a scope with a left-out path must stay valid: $LAST" is 'd["status"]' valid
check "a left-out path must leave the milestone scope" grep -q "(10 files)" "$WORK/bad/review.md"
check "the review must list the files of each commit" grep -qF "#3: \`backend/api/auth.py" "$WORK/bad/review.md"
cp "$WORK/draft.json" "$WORK/asked.json"
edit_json "$WORK/asked.json" "d['questions'] = ['Should CLAUDE.md stay out of the destination?']"
run plan --draft "$WORK/asked.json" --source "$L/source" --target "$L/target" --out "$WORK/bad" --today "$D0"
check "an open question must hold the plan back: $LAST" is 'd["status"]' questions
check "the review must list the open question" grep -q "Should CLAUDE.md stay out" "$WORK/bad/review.md"
run install --draft "$WORK/asked.json" --source "$L/source" --target "$L/target" --today "$D0"
check "install must refuse while a question is open: $LAST" [ "$RC" = 1 ]
check "nothing may be pushed while a question is open" [ "$(tgt_count)" = 0 ]
pass "plan rejects impossible deadlines, pattern typos, missing files and tool trailers; open questions block install"

# ---------------------------------------------------------------- install and routine runs
S="$WORK/acme/source.git"
T="$WORK/acme/target.git"
run install --draft "$WORK/draft.json" --source "$L/source" --target "$L/target" --today "$D0"
check "install failed: $LAST" is 'd["status"]' installed
check "install should push commit 1" [ "$(pushed_now)" = "[1]" ]
git -C "$S" ls-tree -r main --name-only -- "$FOLDER" | sort > "$WORK/folder.txt"
diff <(printf '%s\n' "$FOLDER/calendar.md" "$FOLDER/progress-report/$D12-core.md" \
  "$FOLDER/progress-report/$D20-everything.md" "$FOLDER/tca.py" | sort) "$WORK/folder.txt" \
  || fail "skill folder content in the source repository is wrong"
check "engine copy is not executable" [ "$(git -C "$S" ls-tree main "$FOLDER/tca.py" | cut -d' ' -f1)" = 100755 ]
check "first destination commit has the wrong identity or message" [ \
  "$(git -C "$T" log -1 --format='%an <%ae>|%cn <%ce>|%s' main)" = \
  "Test User <123+test@users.noreply.github.com>|Test User <123+test@users.noreply.github.com>|chore: initialize project tooling" ]
check "first destination commit has the wrong files" [ \
  "$(git -C "$T" ls-tree -r --name-only main | paste -sd ' ')" = ".gitignore package.json scripts/run.sh" ]
check "executable bit lost" [ "$(git -C "$T" ls-tree main scripts/run.sh | cut -d' ' -f1)" = 100755 ]
pass "install saves calendar, reports and engine in the source and pushes commit #1 as the user, CI held back"

INSTALLED="$(src_head)"
routine "$D0"
check "same-day run should be a no-op: $LAST" is 'd["status"]' up_to_date
check "a no-op run must not commit to the source" [ "$(src_head)" = "$INSTALLED" ]
pass "a routine run with nothing due changes nothing, not even the calendar"

routine "$D2"
check "commit #2 not pushed: $LAST" [ "$(pushed_now)" = "[2]" ]
check "calendar does not record commit #2" [ -n "$(state 'd["commits"][1].get("target_sha", "")')" ]
BEFORE="$(src_head)"
run run --source "$L/source" --target "$L/target" --today "$D4" --dry-run
check "dry run failed: $LAST" is 'd["status"]' dry_run
check "dry run should list commit 3" is '[c["number"] for c in d["would_push"]]' "[3]"
check "dry run changed a repository" [ "$(src_head)" = "$BEFORE" ]
check "dry run pushed to the destination" [ "$(tgt_count)" = 2 ]
routine "$D9"
check "missed days not caught up in order: $LAST" [ "$(pushed_now)" = "[3, 4, 5]" ]
check "milestone core not marked reached" [ "$(state 'bool(d["milestones"][0].get("reached_at"))')" = True ]
git -C "$S" show "main:$FOLDER/progress-report/$D12-core.md" | grep -q "| Status | reached" || fail "core report not updated"
AFTER_D9="$(src_head)"
routine "$D9"
check "repeated run not idempotent: $LAST" is 'd["status"]' up_to_date
check "repeated run committed to the source" [ "$(src_head)" = "$AFTER_D9" ]
pass "routine runs push due commits, catch up missed days in order, and record progress idempotently"

# ---------------------------------------------------------------- change the plan
mkdir -p "$WORK/replan"
fresh_clones "$WORK/replan"
R="$WORK/replan"
run export --source "$R/source" --out "$WORK/exported.json"
check "export failed: $LAST" is 'd["pushed"]' 5
cp "$WORK/exported.json" "$WORK/locked.json"
edit_json "$WORK/locked.json" "d['commits'][1]['paths'] = ['backend/db/']"
run plan --draft "$WORK/locked.json" --source "$R/source" --target "$R/target" --out "$WORK/bad" --today "$D9"
check "changing a pushed commit must fail" [ "$RC" = 1 ]
check "locked-commit refusal not explained: $LAST" grep -q "already in the destination" <<<"$LAST"
edit_json "$WORK/exported.json" \
  "d['commits'].insert(7, {'message': 'docs: add user guide', 'paths': ['docs/']}); d['commits'][8].update(date='$D17', pin=True)"
run plan --draft "$WORK/exported.json" --source "$R/source" --target "$R/target" --out "$WORK/replan-preview" --today "$D9"
check "the re-plan review must show a moved date: $LAST" grep -q "(was " "$WORK/replan-preview/review.md"
run install --draft "$WORK/exported.json" --source "$R/source" --target "$R/target" --today "$D9"
check "re-plan install failed: $LAST" [ "$RC" = 0 ]
check "re-plan dates wrong: $(state '" ".join(c["date"] for c in d["commits"][5:])')" \
  [ "$(state '" ".join(c["date"] for c in d["commits"][5:])')" = "$D12 $D13 $D15 $D17" ]
check "nothing is due before the core deadline has passed" [ "$(pushed_now)" = "[]" ]
check "re-plan must not push" [ "$(tgt_count)" = 5 ]
pass "re-planning keeps pushed commits locked, honours a pinned date, and reschedules the rest"

# ---------------------------------------------------------------- the source changes
cd "$WORK/dev"
git pull --quiet --rebase origin main
echo "routes = ['/health']" > backend/api/routes.py
echo "You are helpful." > ai/llm/prompts.txt
git rm --quiet frontend/src/pages/home.js
git add -A && git commit --quiet -m "late fixes" && git push --quiet origin main
cd "$WORK"
routine "$D10"
check "nothing should be due on day 10: $LAST" is 'd["status"]' up_to_date
check "source change not flagged: $LAST" has 'd["warnings"]' "source branch changed"
mkdir -p "$WORK/repin"
fresh_clones "$WORK/repin"
P="$WORK/repin"
run export --source "$P/source" --out "$WORK/repin.json"
run plan --draft "$WORK/repin.json" --source "$P/source" --target "$P/target" --out "$WORK/bad" --today "$D10" --repin
check "deleted source file not reported: $LAST" has 'd["problems"]' "no longer in the"
edit_json "$WORK/repin.json" "d['commits'][-1]['remove'] = ['frontend/src/pages/home.js']"
REPIN_HEAD="$(src_head)"
run install --draft "$WORK/repin.json" --source "$P/source" --target "$P/target" --today "$D10" --repin
check "repin install failed: $LAST" [ "$RC" = 0 ]
check "repin must not push anything before its date: $LAST" [ "$(pushed_now)" = "[]" ]
check "source snapshot not moved" [ "$(state 'd["source"]["commit"]')" = "$REPIN_HEAD" ]
check "pushed commits not frozen to the old snapshot" [ "$(state 'all(c.get("source_commit") for c in d["commits"][:5])')" = True ]
pass "a changed source is flagged, and --repin migrates edits, new files and deletions"

# ---------------------------------------------------------------- drift, with cloud issue reporting
# A gh stand-in that records its calls; it reports one open failure issue once "$WORK/issue-open" exists.
mkdir -p "$WORK/ghstub"
cat > "$WORK/ghstub/gh" <<STUB
#!/bin/sh
echo "\$*" >> "$WORK/gh.log"
case "\$*" in
  *"issues?state=open"*) if [ -e "$WORK/issue-open" ]; then
      echo '[{"number": 7, "title": "timed-commit-automation: scheduled run failed"}]'; else echo '[]'; fi ;;
  *) echo '{}' ;;
esac
STUB
chmod +x "$WORK/ghstub/gh"
git clone --quiet "$T" "$WORK/manual" 2>/dev/null
echo "hotfix" > "$WORK/manual/hotfix.txt"
git -C "$WORK/manual" add -A && git -C "$WORK/manual" commit --quiet -m "manual hotfix"
git -C "$WORK/manual" push --quiet origin main
cloud_routine "$D13"
check "manual destination commit not detected" [ "$RC" = 1 ]
check "drift not explained: $LAST" grep -q "not in the calendar" <<<"$LAST"
check "nothing may be pushed while the destination has drifted" [ "$(tgt_count)" = 6 ]
check "a failed cloud run did not open an issue in the source repository" \
  grep -q "repos/acme/source/issues -f title=timed-commit-automation: scheduled run failed" "$WORK/gh.log"
git -C "$WORK/manual" revert --no-edit HEAD >/dev/null && git -C "$WORK/manual" push --quiet origin main
touch "$WORK/issue-open"
cloud_routine "$D13"
check "run did not resume after the revert: $LAST" [ "$(pushed_now)" = "[6, 7]" ]
check "cancelled-out commits not reported" has 'd["warnings"]' "cancel out"
check "a recovered cloud run did not close the failure issue" grep -q "repos/acme/source/issues/7 -X PATCH -f state=closed" "$WORK/gh.log"
pass "a manual destination commit stops the routine and opens an issue; reverting it resumes and closes it"

cat > "$T/hooks/pre-receive" <<'HOOK'
#!/bin/sh
echo "GH006: Protected branch update failed for refs/heads/main." >&2
exit 1
HOOK
chmod +x "$T/hooks/pre-receive"
routine "$D20"
check "a refused push must fail the run" [ "$RC" = 1 ]
check "a refused push must be reported as refused, with the server's reason: $LAST" grep -q "refused the push.*Protected branch" <<<"$LAST"
rm "$T/hooks/pre-receive"
mkdir -p "$WORK/lonely"
git clone --quiet --depth 1 "file://$S" "$WORK/lonely/source" 2>/dev/null
COMMENTS="$(grep -c "repos/acme/source/issues/7/comments" "$WORK/gh.log")"
set +e
OUT="$(cd "$WORK/lonely" && export PATH="$WORK/ghstub:$PATH" CLAUDE_CODE_REMOTE=1 \
  && python3 -I "$WORK/lonely/source/$FOLDER/tca.py" run 2>"$WORK/stderr")"
RC=$?
set -e
LAST="$(printf '%s\n' "$OUT" | tail -n 1)"
check "a missing destination clone must fail the run" [ "$RC" = 1 ]
check "a missing destination clone must be explained: $LAST" grep -q "no clone of the destination acme/target" <<<"$LAST"
check "a run that cannot even load must still report an issue" \
  [ "$(grep -c "repos/acme/source/issues/7/comments" "$WORK/gh.log")" -gt "$COMMENTS" ]
pass "refused pushes and a missing destination clone fail clearly and are reported"

# ---------------------------------------------------------------- finish
routine "$D20"
check "last commits not pushed: $LAST" [ "$(pushed_now)" = "[8, 9]" ]
routine "$D21"
check "status should be complete: $LAST" is 'd["status"]' complete

git -C "$WORK/dev" pull --quiet --rebase origin main
git -C "$WORK/dev" ls-tree -r HEAD | grep -v -e "	$FOLDER/" -e "	CLAUDE.md$" > "$WORK/expected.txt"
git -C "$T" ls-tree -r main > "$WORK/actual.txt"
diff "$WORK/expected.txt" "$WORK/actual.txt" || fail "final destination differs from the source"
pass "the destination ends byte-identical to the source minus the skill folder and excluded files"

git -C "$T" log --format='%s' main | grep -v -e "^manual hotfix$" -e '^Revert "manual hotfix"$' | tac > "$WORK/subjects.txt"
diff <(printf '%s\n' "chore: initialize project tooling" "feat(db): add schema and user model" \
  "feat(api): add API routes and auth" "feat(frontend): add app shell and components" \
  "feat(vision): add local model inference" "feat(ai): add cloud vision and chat" \
  "test: add test suites" "docs: add user guide" "docs: add readme, guide and ci") "$WORK/subjects.txt" \
  || fail "destination commit subjects differ from the calendar"
check "message body line starting with # lost" grep -q "^#42 tracks rate limiting.$" <(git -C "$T" log --format='%B' main)
IDS="$(git -C "$T" log --format='%an <%ae>|%cn <%ce>|%s' main \
  | grep -v -e '|manual hotfix$' -e '|Revert "manual hotfix"$' | cut -d'|' -f1,2 | sort -u)"
check "unexpected author or committer: $IDS" [ \
  "$IDS" = "Test User <123+test@users.noreply.github.com>|Test User <123+test@users.noreply.github.com>" ]
if git -C "$T" log --all --format='%B' | grep -qi -e "co-authored-by" -e "claude" -e "timed-commit-automation"; then
  fail "a destination commit message mentions the tooling"
fi
if git -C "$T" log --all --name-only --format= | grep -q "$FOLDER"; then fail "the skill folder reached the destination"; fi
YEAR="$(date +%Y)"
if git -C "$T" log --format='%ad %cd' --date=format:%Y main | grep -qv "^$YEAR $YEAR$"; then fail "backdated commit"; fi
pass "every calendar commit is the user's, at real time, with exact messages and no trace of the tooling"

git clone --quiet "$T" "$WORK/later" 2>/dev/null
echo "next feature" > "$WORK/later/feature.txt"
git -C "$WORK/later" add -A && git -C "$WORK/later" commit --quiet -m "feat: next feature"
git -C "$WORK/later" push --quiet origin main
routine "$D22"
check "work after completion must not be treated as drift: $LAST" is 'd["status"]' complete
pass "development after the migration is complete is left alone"

run status --source "$R/source" --target "$R/target" --today "$D22"
check "status failed: $LAST" is 'd["pushed"]' 9
run routine --source "$R/source"
check "routine cron wrong: $LAST" is 'd["cron_utc"]' "7 7,17 * * *"
check "routine prompt wrong" has 'd["prompt"]' "acme/source"
pass "status and routine report correctly (10:07 and 20:07 Istanbul = cron 7 7,17 UTC)"

# ---------------------------------------------------------------- a destination that already has files
mkdir -p "$WORK/b"
git init --quiet --bare "$WORK/b/source.git"
git init --quiet --bare "$WORK/b/target.git"
git clone --quiet "$WORK/b/target.git" "$WORK/b/t0" 2>/dev/null
echo "# placeholder" > "$WORK/b/t0/README.md" && echo "MIT" > "$WORK/b/t0/LICENSE"
git -C "$WORK/b/t0" add -A && git -C "$WORK/b/t0" commit --quiet -m "Initial commit"
git -C "$WORK/b/t0" push --quiet origin main
git clone --quiet "$WORK/b/source.git" "$WORK/b/s0" 2>/dev/null
mkdir -p "$WORK/b/s0/src" && echo "main()" > "$WORK/b/s0/src/main.py" && echo "# Real readme" > "$WORK/b/s0/README.md"
git -C "$WORK/b/s0" add -A && git -C "$WORK/b/s0" commit --quiet -m "wip" && git -C "$WORK/b/s0" push --quiet origin main
git clone --quiet "$WORK/b/source.git" "$WORK/b/source" 2>/dev/null
git clone --quiet "$WORK/b/target.git" "$WORK/b/target" 2>/dev/null
cat > "$WORK/b/draft.json" <<JSON
{"source": {"repo": "b/source"}, "target": {"repo": "b/target"},
 "author": {"name": "Test User", "email": "123+test@users.noreply.github.com"},
 "timezone": "Europe/Istanbul",
 "milestones": [{"id": "all", "title": "Everything", "deadline": "$D6", "scope": ["**"]}],
 "commits": [{"message": "feat: add entry point", "paths": ["src/"]},
             {"message": "docs: add readme", "paths": ["**"]}]}
JSON
run plan --draft "$WORK/b/draft.json" --source "$WORK/b/source" --target "$WORK/b/target" --out "$WORK/b/preview" --today "$D0"
check "plan with an existing destination failed: $LAST" [ "$RC" = 0 ]
check "kept destination file not reported" has 'd["warnings"]' LICENSE
check "review does not mention the replaced README" grep -q "Replaced by the source version: README.md" "$WORK/b/preview/review.md"
run install --draft "$WORK/b/draft.json" --source "$WORK/b/source" --target "$WORK/b/target" --today "$D0"
check "install with an existing destination failed: $LAST" [ "$(pushed_now)" = "[1]" ]
run run --source "$WORK/b/source" --target "$WORK/b/target" --today "$D2"
check "run with an existing destination failed: $LAST" [ "$(pushed_now)" = "[2]" ]
check "existing destination files not kept or replaced correctly" [ \
  "$(git -C "$WORK/b/target.git" ls-tree -r --name-only main | paste -sd ' ')" = "LICENSE README.md src/main.py" ]
check "README not replaced" [ "$(git -C "$WORK/b/target.git" show main:README.md)" = "# Real readme" ]
pass "a destination that already has files keeps its own (LICENSE) and gets the source's (README.md)"

# ---------------------------------------------------------------- weekdays only, a day off, two a day
mkdir -p "$WORK/d"
git init --quiet --bare "$WORK/d/source.git"
git init --quiet --bare "$WORK/d/target.git"
git clone --quiet "$WORK/d/source.git" "$WORK/d/s0" 2>/dev/null
for i in 1 2 3 4 5 6 7 8; do mkdir -p "$WORK/d/s0/m$i" && echo "part $i" > "$WORK/d/s0/m$i/main.py"; done
git -C "$WORK/d/s0" add -A && git -C "$WORK/d/s0" commit --quiet -m "wip" && git -C "$WORK/d/s0" push --quiet origin main
git clone --quiet "$WORK/d/source.git" "$WORK/d/source" 2>/dev/null
git clone --quiet "$WORK/d/target.git" "$WORK/d/target" 2>/dev/null
FIRST_WEEKDAY="$(python3 -c 'import datetime, sys
d = datetime.date.fromisoformat(sys.argv[1])
while d.weekday() > 4:
    d += datetime.timedelta(days=1)
print(d + datetime.timedelta(days=1 if d.weekday() < 4 else 3))' "$D0")"
python3 - "$WORK/d/draft.json" "$D0" "$D10" "$FIRST_WEEKDAY" <<'PY'
import json, sys
path, d0, d10, day_off = sys.argv[1:]
json.dump({
    "source": {"repo": "d/source"}, "target": {"repo": "d/target"},
    "author": {"name": "Test User", "email": "123+test@users.noreply.github.com"},
    "timezone": "Europe/Istanbul",
    "schedule": {"start": d0, "weekdays": ["mon", "tue", "wed", "thu", "fri"], "skip": [day_off], "per_day": 2},
    "milestones": [{"id": "all", "title": "Everything", "deadline": d10, "scope": ["**"]}],
    "commits": [{"message": f"feat: add part {i}", "paths": [f"m{i}/"]} for i in range(1, 9)],
}, open(path, "w"), indent=2)
PY
run plan --draft "$WORK/d/draft.json" --source "$WORK/d/source" --target "$WORK/d/target" --out "$WORK/d/preview" --today "$D0"
check "plan with weekday rules failed: $LAST" [ "$RC" = 0 ]
python3 - "$WORK/d/preview/calendar.md" "$FIRST_WEEKDAY" "$D10" <<'PY' || fail "weekday, day-off or per-day rule broken"
import collections, datetime, json, sys
text = open(sys.argv[1]).read()
block = text.split("<!-- tca:state:begin -->")[1].split("<!-- tca:state:end -->")[0].strip()
dates = [datetime.date.fromisoformat(c["date"]) for c in json.loads(block.removeprefix("```json").removesuffix("```"))["commits"]]
day_off, deadline = (datetime.date.fromisoformat(x) for x in sys.argv[2:])
print("  weekday schedule:", " ".join(d.isoformat() for d in dates))
assert dates == sorted(dates), "dates out of order"
assert all(d.weekday() < 5 for d in dates), "weekend date"
assert day_off not in dates, "skipped day used"
assert max(collections.Counter(dates).values()) <= 2, "more than 2 commits on a day"
assert max(dates) <= deadline - datetime.timedelta(days=2), "deadline margin not kept"
PY
pass "weekdays-only, a skipped day and two commits a day are respected within the deadline margin"

# ---------------------------------------------------------------- Git LFS pointers
mkdir -p "$WORK/c"
git init --quiet --bare "$WORK/c/source.git"
git init --quiet --bare "$WORK/c/target.git"
git clone --quiet "$WORK/c/source.git" "$WORK/c/s0" 2>/dev/null
printf 'version https://git-lfs.github.com/spec/v1\noid sha256:%064d\nsize 12345\n' 0 > "$WORK/c/s0/weights.bin"
git -C "$WORK/c/s0" add -A && git -C "$WORK/c/s0" commit --quiet -m "wip" && git -C "$WORK/c/s0" push --quiet origin main
git clone --quiet "$WORK/c/source.git" "$WORK/c/source" 2>/dev/null
git clone --quiet "$WORK/c/target.git" "$WORK/c/target" 2>/dev/null
sed -e 's#b/source#c/source#; s#b/target#c/target#' "$WORK/b/draft.json" > "$WORK/c/draft.json"
edit_json "$WORK/c/draft.json" "d['commits'] = [{'message': 'feat: add weights', 'paths': ['**']}]"
run plan --draft "$WORK/c/draft.json" --source "$WORK/c/source" --target "$WORK/c/target" --out "$WORK/c/preview" --today "$D0"
check "LFS pointer not reported: $LAST" has 'd["problems"]' "Git LFS pointers"
pass "Git LFS pointer files are refused with an explanation"

echo "ALL E2E CHECKS PASSED"
