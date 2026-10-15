#!/usr/bin/env python3
"""Engine of the timed-commit-automation skill.

Moves a finished project from a source repository to a destination repository
as a calendar of commits. Every destination commit is created at the moment it
is pushed (never backdated), is authored and committed by the configured user,
and contains files byte-identical to the source. The calendar, the progress
reports and a copy of this engine live only in the source repository, under
timed-commit-automation-skill/, and that folder never reaches the destination.

Progress is derived from the destination itself: its history is matched against
the planned trees, so a run that pushed but crashed before recording progress is
repaired by the next run. The approved calendar is a contract: runs never
reschedule, they only push what is due (catching up if earlier runs failed).

Commands (each has --help):
  inspect  facts about both clones, for planning
  plan     validate and schedule a draft calendar, write a preview for review
  install  save the calendar and this engine in the source repo, push due commits
  run      push due commits and record progress (what the cloud routine runs)
  status   read-only progress summary
  export   write the installed calendar to a file, as an editable draft
  routine  print the cloud routine configuration

The last line on stdout is always one JSON object; logs go to stderr.
Exit status: 0 success, 1 failure.
"""

from __future__ import annotations

import argparse
import bisect
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

try:
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
except ImportError:  # Python < 3.9
    print(json.dumps({"status": "error", "message": "tca.py needs Python 3.9 or newer"}))
    sys.exit(1)

SKILL_DIR = "timed-commit-automation-skill"
CALENDAR_FILE = f"{SKILL_DIR}/calendar.md"
REPORT_DIR = f"{SKILL_DIR}/progress-report"
ENGINE_FILE = f"{SKILL_DIR}/tca.py"
STATE_BEGIN = "<!-- tca:state:begin -->"
STATE_END = "<!-- tca:state:end -->"
SCHEMA_VERSION = 1
TRACKING_REF = "refs/tca/target"  # destination history, fetched into the source clone
OUTGOING_REF = "refs/tca/out"  # new destination commits, handed to the destination clone

WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
DAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
ONE_DAY = dt.timedelta(days=1)
UTC = dt.timezone.utc  # noqa: UP017 - datetime.UTC needs Python 3.11; the engine supports 3.9

# Two runs a day: the evening run retries a failed morning run on the same day.
# Minutes past the hour, because routines scheduled exactly on the hour can start late.
DEFAULT_RUN_TIMES = ["10:07", "20:07"]
# Every deadline is planned one day early, so a whole day of failed runs is recoverable.
DEFAULT_MARGIN_DAYS = 1
# GitHub rejects pushes containing files over 100 MB and warns above 50 MB.
GITHUB_FILE_LIMIT = 100 * 1024 * 1024
GITHUB_FILE_WARNING = 50 * 1024 * 1024
# A Git LFS pointer is a small text file starting with this line (the spec caps it at 1024 bytes).
LFS_POINTER = b"version https://git-lfs.github.com/spec/v1"
LFS_POINTER_MAX = 1024
# CI configuration arrives with the last commit, so no CI run ever sees an unfinished project.
CI_PATTERNS = (".github/workflows/", ".circleci/", ".buildkite/", ".travis.yml", ".drone.yml",
               "appveyor.yml", ".appveyor.yml", "azure-pipelines.yml")
# Transient network errors usually clear on a retry; a rejected push never does.
PUSH_ATTEMPTS = 3
ISSUE_TITLE = "timed-commit-automation: scheduled run failed"
ROUTINE_MODEL = "claude-sonnet-5-5"
ROUTINE_TOOLS = ["Bash", "Read", "Glob", "Grep"]
AI_TOOL_NAMES = {"CLAUDE.md", "CLAUDE.local.md", "AGENTS.md", "GEMINI.md", ".cursorrules", ".windsurfrules"}
AI_TOOL_DIRS = {".claude", ".cursor", ".windsurf", ".aider"}
# Destination commit messages must not reveal the tooling behind them.
FORBIDDEN_IN_MESSAGES = (
    re.compile(r"co-authored-by\s*:", re.IGNORECASE),
    re.compile(r"claude-session\s*:", re.IGNORECASE),
    re.compile(r"generated with \[?claude", re.IGNORECASE),
    re.compile(r"noreply@anthropic\.com", re.IGNORECASE),
    re.compile(r"timed-commit-automation", re.IGNORECASE),
)
REPO_RX = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
SLUG_RX = re.compile(r"[a-z0-9][a-z0-9-]{0,62}")
EMAIL_RX = re.compile(r"[^@\s<>]+@[^@\s<>]+\.[^@\s<>]+")
TIME_RX = re.compile(r"([01]\d|2[0-3]):[0-5]\d")
DEADLINE_RX = re.compile(r"(\d{4}-\d{2}-\d{2})(?:[T ](\d{2}):(\d{2}))?")

ROUTINE_PROMPT = """\
Run one step of the scheduled migration from {source} to {target}. A script does all of the git work; you only run it and report.

1. Find the script, starting from the working directory:
   find . "$HOME" -maxdepth 6 -path '*/{skill_dir}/tca.py' 2>/dev/null | head -n 1
2. Run it exactly once: python3 <path found in step 1> run
3. Reply with one or two sentences summarizing the JSON object on the last line of its output: status, commits pushed, next planned commit. If the command fails or prints no JSON, quote its last 20 lines.

Do not edit, create, commit or push anything, do not create branches or pull requests, and do not retry or work around a failure yourself. The script reports failures as an issue in {source}, and the next scheduled run retries.
"""


class Fail(Exception):
    """An expected failure; the message is written for the user."""


class Rejected(Fail):
    """A push was rejected because the remote branch moved."""


def log(message):
    print(message, file=sys.stderr)


def emit(status, **fields):
    """Print the JSON result line (always the last line on stdout)."""
    print(json.dumps({"status": status, **fields}, ensure_ascii=False))


# --------------------------------------------------------------------------- git


class Repo:
    """A local clone, driven through plumbing so its working tree is never touched."""

    def __init__(self, path):
        self.path = str(Path(path).expanduser().resolve())
        top = self.git("rev-parse", "--show-toplevel", check=False)
        if top.returncode != 0 or Path(top.stdout.strip()).resolve() != Path(self.path):
            raise Fail(f"{self.path} is not the top folder of a git clone")

    def git(self, *args, input=None, env=None, check=True, binary=False):
        run_env = dict(os.environ if env is None else env)
        run_env["GIT_TERMINAL_PROMPT"] = "0"  # fail fast instead of waiting for a password
        text = {} if binary else {"text": True, "encoding": "utf-8", "errors": "surrogateescape"}
        result = subprocess.run(
            ["git", "-C", self.path, *args],
            input=input, capture_output=True, env=run_env, check=False, **text,
        )
        if check and result.returncode != 0:
            err = result.stderr.decode("utf-8", "replace") if binary else result.stderr
            raise Fail(f"git {' '.join(args[:2])} failed in {self.path}: {err.strip()}")
        return result

    def out(self, *args, **kwargs):
        return self.git(*args, **kwargs).stdout.strip()

    def ok(self, *args):
        return self.git(*args, check=False).returncode == 0

    def commit_of(self, ref):
        result = self.git("rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}", check=False)
        return result.stdout.strip() or None

    def has_commit(self, sha):
        return self.ok("cat-file", "-e", f"{sha}^{{commit}}")

    def remote(self):
        names = self.out("remote").split()
        if "origin" in names:
            return "origin"
        if len(names) == 1:
            return names[0]
        raise Fail(f"{self.path}: cannot tell which git remote to use ({', '.join(names) or 'none'})")

    def slug(self):
        return repo_slug(self.out("remote", "get-url", self.remote()))


def repo_slug(text):
    """'owner/name' from a slug, an https or ssh URL, or a proxy URL; None if unrecognised."""
    if not isinstance(text, str) or not text.strip():
        return None
    value = text.strip().rstrip("/").removesuffix(".git")
    parts = [part for part in re.split(r"[/:]", value) if part]
    if len(parts) < 2:
        return None
    slug = f"{parts[-2]}/{parts[-1]}"
    return slug if REPO_RX.fullmatch(slug) else None


def same_repo(a, b):
    return bool(a and b and a.lower() == b.lower())


def ls_tree(repo, rev):
    """path -> (mode, object id) for every file in rev."""
    entries = {}
    for record in repo.git("ls-tree", "-r", "-z", "--full-tree", rev).stdout.split("\0"):
        if record:
            meta, path = record.split("\t", 1)
            mode, _kind, sha = meta.split(" ")
            entries[path] = (mode, sha)
    return entries


def default_branch(repo, fallback="main"):
    remote = repo.remote()
    head = repo.git("symbolic-ref", "--quiet", "--short", f"refs/remotes/{remote}/HEAD", check=False)
    if head.returncode == 0 and "/" in head.stdout:
        return head.stdout.strip().split("/", 1)[1]
    symref = repo.git("ls-remote", "--symref", remote, "HEAD", check=False)
    found = re.search(r"ref: refs/heads/(\S+)\s+HEAD", symref.stdout or "")
    return found.group(1) if found else fallback


def sync_branch(repo, branch):
    """Fetch the remote branch with full history; return its head, or None if it does not exist."""
    remote = repo.remote()
    ref = f"refs/remotes/{remote}/{branch}"
    spec = f"+refs/heads/{branch}:{ref}"
    result = repo.git("fetch", "--quiet", "--no-tags", remote, spec, check=False)
    if result.returncode != 0:
        if "couldn't find remote ref" in result.stderr.lower():
            return None
        raise Fail(f"cannot fetch {branch} into {repo.path}: {result.stderr.strip()}")
    if repo.out("rev-parse", "--is-shallow-repository") == "true":
        repo.git("fetch", "--quiet", "--no-tags", "--unshallow", remote, spec)
    return repo.commit_of(ref)


def ensure_commit(repo, sha):
    if repo.has_commit(sha):
        return
    repo.git("fetch", "--quiet", "--no-tags", repo.remote(), sha, check=False)
    if not repo.has_commit(sha):
        raise Fail(
            f"source snapshot {sha[:7]} is not in {repo.path}; if the source history was "
            "rewritten, re-plan with --repin"
        )


PERMANENT_PUSH_ERRORS = ("remote rejected", "denied", "403", "not found", "protected branch", "workflow")


def push(repo, sha, branch):
    remote = repo.remote()
    for attempt in range(1, PUSH_ATTEMPTS + 1):
        result = repo.git("push", "--no-verify", remote, f"{sha}:refs/heads/{branch}", check=False)
        if result.returncode == 0:
            return
        err = result.stderr.strip()
        lowered = err.lower()
        if any(word in lowered for word in PERMANENT_PUSH_ERRORS):
            raise Fail(f"{remote} refused the push to {branch}: {err}")
        if "non-fast-forward" in lowered or "fetch first" in lowered:
            raise Rejected(f"{remote}/{branch} moved during the push: {err}")
        if attempt == PUSH_ATTEMPTS:
            raise Fail(f"push to {remote}/{branch} failed: {err}")
        log(f"push failed (attempt {attempt}), retrying: {err}")
        time.sleep(2 * attempt)


def make_commit(repo, tree, parent, message, author, tz):
    """Create a commit stamped with the current time, as the user, unsigned, without trailers."""
    now = dt.datetime.now(tz).replace(microsecond=0)
    offset = now.utcoffset() or dt.timedelta(0)
    minutes = int(offset.total_seconds() // 60)
    stamp = f"{int(now.timestamp())} {'+' if minutes >= 0 else '-'}{abs(minutes) // 60:02d}{abs(minutes) % 60:02d}"
    env = {k: v for k, v in os.environ.items() if not k.startswith(("GIT_AUTHOR_", "GIT_COMMITTER_"))}
    env.update(
        GIT_AUTHOR_NAME=author["name"], GIT_AUTHOR_EMAIL=author["email"], GIT_AUTHOR_DATE=stamp,
        GIT_COMMITTER_NAME=author["name"], GIT_COMMITTER_EMAIL=author["email"], GIT_COMMITTER_DATE=stamp,
    )
    args = ["commit-tree", tree, "--no-gpg-sign"] + (["-p", parent] if parent else [])
    sha = repo.out(*args, input=message.rstrip() + "\n", env=env)
    return sha, now


class ScratchIndex:
    """A temporary index file, so trees are built without touching the clone's own index."""

    def __init__(self, repo):
        fd, self.path = tempfile.mkstemp(prefix="tca-index-")
        os.close(fd)
        os.unlink(self.path)
        self.repo = repo
        self.env = dict(os.environ, GIT_INDEX_FILE=self.path)

    def git(self, *args, **kwargs):
        return self.repo.git(*args, env=self.env, **kwargs)

    def close(self):
        for path in (self.path, self.path + ".lock"):
            if os.path.exists(path):
                os.unlink(path)


class TreeBuilder:
    """Applies planned commits one after another and records the tree after each."""

    def __init__(self, repo, base_commit, base_entries):
        self.index = ScratchIndex(repo)
        self.empty_tree = repo.out("mktree", input="")
        self.zero = "0" * len(self.empty_tree)
        self.state = dict(base_entries)
        self.dirs = Counter()
        for path in self.state:
            self._count(path, 1)
        if base_commit:
            self.index.git("read-tree", base_commit)
            self.tree = repo.out("rev-parse", f"{base_commit}^{{tree}}")
        else:
            self.index.git("read-tree", "--empty")
            self.tree = self.empty_tree

    def _count(self, path, delta):
        cut = path.find("/")
        while cut != -1:
            self.dirs[path[:cut]] += delta
            cut = path.find("/", cut + 1)

    def _drop(self, path, records):
        del self.state[path]
        self._count(path, -1)
        records.append(f"0 {self.zero}\t{path}")

    def apply(self, sets, removes):
        records = []
        for path in removes:
            if path in self.state:
                self._drop(path, records)
        for path, (mode, sha) in sets.items():
            cut = path.find("/")
            while cut != -1:  # a file stands where this path needs a directory
                if path[:cut] in self.state:
                    self._drop(path[:cut], records)
                cut = path.find("/", cut + 1)
            if self.dirs.get(path):  # a directory stands where this file goes
                for other in [p for p in self.state if p.startswith(path + "/")]:
                    self._drop(other, records)
            if path not in self.state:
                self._count(path, 1)
            self.state[path] = (mode, sha)
            records.append(f"{mode} {sha}\t{path}")
        if records:
            self.index.git("update-index", "-z", "--index-info", input="\0".join(records) + "\0")
            self.tree = self.index.repo.out("write-tree", env=self.index.env)
        return self.tree

    def close(self):
        self.index.close()


# ---------------------------------------------------------------------- patterns


class Pattern:
    """A path pattern anchored at the repository root.

    "dir" or "dir/" selects everything under dir; "*" and "?" stay inside one path
    segment; "**" crosses segments; a pattern matching a directory selects its files.
    """

    def __init__(self, text):
        value = text.strip().removeprefix("!")
        while value.startswith("./"):
            value = value[2:]
        value = value.strip("/")
        if not value:
            raise ValueError("empty pattern")
        self.text = text
        self.literal = None if set(value) & set("*?[") else value
        self.rx = None if self.literal is not None else re.compile(glob_regex(value))

    def matches(self, path):
        if self.literal is not None:
            return path == self.literal or path.startswith(self.literal + "/")
        if self.rx.fullmatch(path):
            return True
        cut = path.find("/")
        while cut != -1:
            if self.rx.fullmatch(path[:cut]):
                return True
            cut = path.find("/", cut + 1)
        return False

    def select(self, sorted_paths):
        if self.literal is None:
            return [path for path in sorted_paths if self.matches(path)]
        hits = []
        exact = bisect.bisect_left(sorted_paths, self.literal)
        if exact < len(sorted_paths) and sorted_paths[exact] == self.literal:
            hits.append(self.literal)
        # Paths under "lit/" sort between "lit/" and "lit0" ("0" follows "/").
        low = bisect.bisect_left(sorted_paths, self.literal + "/")
        high = bisect.bisect_left(sorted_paths, self.literal + "0")
        return hits + sorted_paths[low:high]


def glob_regex(pattern):
    out, i = [], 0
    while i < len(pattern):
        char = pattern[i]
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif char == "*":
            out.append("[^/]*")
            i += 1
        elif char == "?":
            out.append("[^/]")
            i += 1
        elif char == "[" and "]" in pattern[i + 2:]:
            end = pattern.index("]", i + 2)
            body = pattern[i + 1:end]
            out.append("[" + ("^" + body[1:] if body.startswith("!") else body).replace("\\", "\\\\") + "]")
            i = end + 1
        else:
            out.append(re.escape(char))
            i += 1
    return "".join(out)


def valid_patterns(value, where, problems, negation=False):
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        problems.append(f"{where} must be a list of path patterns")
        return []
    good = []
    for item in value:
        if item.strip().startswith("!") and not negation:
            problems.append(f"{where}: {item!r}: a leading \"!\" (leave out) is allowed only in milestone scopes")
            continue
        try:
            Pattern(item)
            good.append(item)
        except ValueError:
            problems.append(f"{where} contains an empty pattern")
    return good


# ------------------------------------------------------------------- time rules


def zone(name, fallback=None):
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError, OSError):  # unknown name or no tz database
        if fallback:
            log(f"warning: no timezone data for {name!r}; using the fixed offset {fallback}")
            return fixed_offset(fallback)
        raise Fail(f"unknown timezone {name!r}; use an IANA name such as Europe/Istanbul") from None


def fixed_offset(text):
    found = re.fullmatch(r"([+-])(\d{2}):(\d{2})", text or "")
    if not found:
        raise Fail(f"bad UTC offset {text!r}")
    delta = dt.timedelta(hours=int(found.group(2)), minutes=int(found.group(3)))
    return dt.timezone(delta if found.group(1) == "+" else -delta)


def offset_text(moment):
    minutes = int((moment.utcoffset() or dt.timedelta(0)).total_seconds() // 60)
    return f"{'+' if minutes >= 0 else '-'}{abs(minutes) // 60:02d}:{abs(minutes) % 60:02d}"


def detect_timezone():
    name = os.environ.get("TZ", "").lstrip(":")
    if "/" in name:
        return name
    real = os.path.realpath("/etc/localtime")
    if "zoneinfo/" in real:
        return real.split("zoneinfo/", 1)[1]
    if shutil.which("timedatectl"):
        result = subprocess.run(["timedatectl", "show", "-p", "Timezone", "--value"],
                                capture_output=True, text=True, check=False)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    return "UTC"


def parse_time(text):
    hours, minutes = text.split(":")
    return dt.time(int(hours), int(minutes))


def parse_deadline(text, tz):
    """(stated day, due moment, date_only).

    A bare date means the work must be in the destination before that day starts,
    so "2026-12-12" is due at 2026-12-11 23:59.
    """
    found = DEADLINE_RX.fullmatch(text.strip())
    if not found:
        raise ValueError(text)
    day = dt.date.fromisoformat(found.group(1))
    if found.group(2) is None:
        return day, dt.datetime.combine(day - ONE_DAY, dt.time(23, 59), tz), True
    return day, dt.datetime.combine(day, dt.time(int(found.group(2)), int(found.group(3))), tz), False


def push_cutoff(due, first_run):
    """Last day whose first routine run happens before the deadline."""
    return due.date() if due.time() >= first_run else due.date() - ONE_DAY


def day_text(day):
    return f"{DAY_NAMES[day.weekday()]} {day.isoformat()}"


def moment_text(moment, tz):
    return moment.astimezone(tz).strftime("%Y-%m-%d %H:%M")


def cron_utc(run_times, tz, day):
    hours, minutes = set(), set()
    for text in run_times:
        utc = dt.datetime.combine(day, parse_time(text), tz).astimezone(UTC)
        hours.add(utc.hour)
        minutes.add(utc.minute)
    if len(minutes) != 1:
        raise Fail("all run_times must share the same minute, so that one cron expression covers them")
    return f"{minutes.pop()} {','.join(str(hour) for hour in sorted(hours))} * * *"


# ----------------------------------------------------------------- the calendar


def parse_calendar_text(text):
    start, end = text.find(STATE_BEGIN), text.find(STATE_END)
    if start == -1 or end < start:
        raise Fail("calendar.md has no machine-readable state block")
    block = text[start + len(STATE_BEGIN):end].strip()
    block = re.sub(r"^```(?:json)?\s*", "", block)
    block = re.sub(r"\s*```$", "", block)
    try:
        return json.loads(block)
    except json.JSONDecodeError as err:
        raise Fail(f"calendar.md holds invalid JSON: {err}") from None


def load_draft(path):
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as err:
        raise Fail(f"cannot read {path}: {err}") from None
    if STATE_BEGIN in text:
        return parse_calendar_text(text)
    try:
        return json.loads(text)
    except json.JSONDecodeError as err:
        raise Fail(f"{path} is not valid JSON: {err}") from None


def read_installed(src, branch):
    """(raw calendar, source head) from the remote branch; raw is None when nothing is installed."""
    head = sync_branch(src, branch)
    if not head:
        raise Fail(f"the source repository has no branch {branch!r}")
    shown = src.git("show", f"{head}:{CALENDAR_FILE}", check=False)
    if shown.returncode != 0:
        return None, head
    return parse_calendar_text(shown.stdout), head


def normalize(raw, problems, warnings):
    """Validate a draft or stored calendar and fill in defaults."""
    if not isinstance(raw, dict):
        raise Fail("the calendar must be a JSON object")

    def block(name):
        value = raw.get(name)
        return value if isinstance(value, dict) else {}

    if raw.get("version", SCHEMA_VERSION) != SCHEMA_VERSION:
        problems.append(f"unsupported calendar version {raw.get('version')!r}")
    source, target, author, schedule = block("source"), block("target"), block("author"), block("schedule")
    cal = {
        "version": SCHEMA_VERSION,
        "source": {"repo": repo_slug(source.get("repo")), "branch": source.get("branch") or None,
                   "commit": source.get("commit") or None},
        "target": {"repo": repo_slug(target.get("repo")), "branch": target.get("branch") or None},
    }
    if "base_commit" in target:
        cal["target"]["base_commit"] = target["base_commit"] or None
    for side in ("source", "target"):
        if not cal[side]["repo"]:
            problems.append(f"{side}.repo must be a GitHub repository written as owner/name")
    if same_repo(cal["source"]["repo"], cal["target"]["repo"]):
        problems.append("source and target must be different repositories")

    name, email = str(author.get("name") or "").strip(), str(author.get("email") or "").strip()
    if not name:
        problems.append("author.name is required: the user's name as GitHub shows it")
    if not EMAIL_RX.fullmatch(email):
        problems.append("author.email must be an address linked to the user's GitHub account, "
                        "such as 12345+login@users.noreply.github.com")
    cal["author"] = {"name": name, "email": email}

    cal["timezone"] = str(raw.get("timezone") or "")
    if raw.get("utc_offset"):
        cal["utc_offset"] = raw["utc_offset"]
    try:
        zone(cal["timezone"], cal.get("utc_offset"))
    except Fail as err:
        problems.append(str(err))

    cal["schedule"] = normalize_schedule(schedule, problems)
    cal["exclude"] = valid_patterns(raw.get("exclude", []), "exclude", problems)
    for key in ("notes", "questions"):
        value = raw.get(key, [])
        if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
            problems.append(f"{key} must be a list of sentences")
            value = []
        cal[key] = [item.strip() for item in value]
    cal["milestones"] = normalize_milestones(raw.get("milestones"), problems)
    cal["commits"] = normalize_commits(raw.get("commits"), problems, warnings)
    ci_from = raw.get("ci_from")
    valid = isinstance(ci_from, int) and not isinstance(ci_from, bool) and 1 <= ci_from <= len(cal["commits"])
    cal["ci_from"] = ci_from if valid else None
    return cal


def normalize_schedule(raw, problems):
    out = {"start": None}
    if raw.get("start"):
        try:
            out["start"] = dt.date.fromisoformat(str(raw["start"])).isoformat()
        except ValueError:
            problems.append(f"schedule.start {raw['start']!r} is not a YYYY-MM-DD date")
    per_day = raw.get("per_day", 1)
    if isinstance(per_day, bool) or not isinstance(per_day, int) or not 1 <= per_day <= 24:
        problems.append("schedule.per_day must be a whole number from 1 to 24")
        per_day = 1
    out["per_day"] = per_day
    weekdays = raw.get("weekdays", list(WEEKDAYS))
    picked = {str(day).lower()[:3] for day in weekdays} if isinstance(weekdays, list) else set()
    if not picked or not picked <= set(WEEKDAYS):
        problems.append("schedule.weekdays must list days such as \"mon\", \"tue\" ... \"sun\"")
        picked = set(WEEKDAYS)
    out["weekdays"] = [day for day in WEEKDAYS if day in picked]
    out["skip"] = []
    for day in raw.get("skip", []) if isinstance(raw.get("skip", []), list) else [None]:
        try:
            out["skip"].append(dt.date.fromisoformat(str(day)).isoformat())
        except ValueError:
            problems.append(f"schedule.skip contains {day!r}, which is not a YYYY-MM-DD date")
    margin = raw.get("margin_days", DEFAULT_MARGIN_DAYS)
    if isinstance(margin, bool) or not isinstance(margin, int) or not 0 <= margin <= 14:
        problems.append("schedule.margin_days must be a whole number from 0 to 14")
        margin = DEFAULT_MARGIN_DAYS
    out["margin_days"] = margin
    run_times = raw.get("run_times", DEFAULT_RUN_TIMES)
    if (not isinstance(run_times, list) or not run_times
            or not all(isinstance(t, str) and TIME_RX.fullmatch(t) for t in run_times)):
        problems.append("schedule.run_times must be a list of HH:MM times")
        run_times = list(DEFAULT_RUN_TIMES)
    elif len({t[3:] for t in run_times}) != 1:
        problems.append("schedule.run_times must share the same minute (one cron expression runs them)")
    out["run_times"] = sorted(set(run_times))
    return out


def normalize_milestones(raw, problems):
    if not isinstance(raw, list) or not raw:
        problems.append("at least one milestone is required; the last one is usually the whole "
                        "project, with scope [\"**\"]")
        return []
    out, seen = [], set()
    for number, item in enumerate(raw, 1):
        if not isinstance(item, dict):
            problems.append(f"milestone {number} must be an object")
            continue
        mid = str(item.get("id") or "")
        where = f"milestone {mid or number}"
        if not SLUG_RX.fullmatch(mid):
            problems.append(f"{where}: id must use lowercase letters, digits and dashes")
        elif mid in seen:
            problems.append(f"{where}: id is used twice")
        seen.add(mid)
        entry = {
            "id": mid,
            "title": str(item.get("title") or "").strip() or mid,
            "request": str(item.get("request") or "").strip(),
            "deadline": str(item.get("deadline") or "").strip(),
            "scope": valid_patterns(item.get("scope"), f"{where}: scope", problems, negation=True),
        }
        if not DEADLINE_RX.fullmatch(entry["deadline"]):
            problems.append(f"{where}: deadline must be YYYY-MM-DD or YYYY-MM-DDTHH:MM")
        else:
            try:
                parse_deadline(entry["deadline"], UTC)
            except ValueError:
                problems.append(f"{where}: deadline {entry['deadline']!r} is not a real date")
        if not entry["scope"]:
            problems.append(f"{where}: scope must name at least one path pattern")
        if item.get("weekday"):
            weekday = str(item["weekday"]).lower()[:3]
            if weekday not in WEEKDAYS:
                problems.append(f"{where}: weekday must be one of {', '.join(WEEKDAYS)}")
            entry["weekday"] = weekday
        if item.get("reached_at"):
            entry["reached_at"] = item["reached_at"]
            if isinstance(item.get("reached_by"), int) and not isinstance(item["reached_by"], bool):
                entry["reached_by"] = item["reached_by"]
        out.append(entry)
    return out


def normalize_commits(raw, problems, warnings):
    if not isinstance(raw, list) or not raw:
        problems.append("the calendar needs at least one commit")
        return []
    out = []
    for number, item in enumerate(raw, 1):
        where = f"commit #{number}"
        if not isinstance(item, dict):
            problems.append(f"{where} must be an object")
            continue
        message = str(item.get("message") or "").strip()
        if not message:
            problems.append(f"{where}: message is required")
        else:
            first = message.splitlines()[0].strip()
            if not first:
                problems.append(f"{where}: the first line of the message must not be empty")
            elif len(first) > 72:
                warnings.append(f"{where}: subject has {len(first)} characters; 72 or fewer reads better")
            for rule in FORBIDDEN_IN_MESSAGES:
                if rule.search(message):
                    problems.append(f"{where}: message must not mention {rule.pattern!r}")
        entry = {
            "message": message,
            "paths": valid_patterns(item.get("paths", []), f"{where}: paths", problems),
        }
        remove = valid_patterns(item.get("remove", []), f"{where}: remove", problems)
        if remove:
            entry["remove"] = remove
        if not entry["paths"] and not remove:
            problems.append(f"{where}: paths must name at least one path pattern")
        if item.get("source_commit"):
            entry["source_commit"] = str(item["source_commit"])
        if item.get("date"):
            try:
                entry["date"] = dt.date.fromisoformat(str(item["date"])).isoformat()
            except ValueError:
                problems.append(f"{where}: date {item['date']!r} is not a YYYY-MM-DD date")
        if item.get("pin"):
            entry["pin"] = True
            if "date" not in entry:
                problems.append(f"{where}: a pinned commit needs a date")
        for key in ("pushed_at", "target_sha"):
            if item.get(key):
                entry[key] = item[key]
        out.append(entry)
    return out


# ---------------------------------------------------------------------- the plan


class Plan:
    """Concrete file changes and trees for every planned commit."""

    def __init__(self):
        self.trees = []  # trees[0] is the destination's starting tree, trees[k] the tree after #k
        self.changes = []  # per commit: {"set": [...], "removed": [...]}
        self.milestones = []  # per milestone: {"files": n, "completed_by": k, ...}
        self.latest = {}
        self.base = {}
        self.final = {}
        self.ci_files = []


def migratable(entries, excludes):
    return {
        path: value for path, value in entries.items()
        if not path.startswith(SKILL_DIR + "/") and not any(rule.matches(path) for rule in excludes)
    }


def plural(count, word):
    return f"{count} {word}" + ("" if count == 1 else "s")


def preview(items, limit=5):
    items = list(items)
    shown = ", ".join(items[:limit])
    return shown + (f" and {len(items) - limit} more" if len(items) > limit else "")


def build_plan(cal, src, problems, warnings, planning):
    plan = Plan()
    excludes = [Pattern(text) for text in cal["exclude"]]
    snapshots = {}

    def snapshot(sha):
        if sha not in snapshots:
            entries = migratable(ls_tree(src, sha), excludes)
            snapshots[sha] = (entries, sorted(entries))
        return snapshots[sha]

    ci_rules = [Pattern(text) for text in CI_PATTERNS]

    def is_ci(path):
        return any(rule.matches(path) for rule in ci_rules)

    ci_from = cal.get("ci_from") or len(cal["commits"])
    default_source = cal["source"]["commit"]
    plan.latest, latest_sorted = snapshot(default_source)
    plan.ci_files = [path for path in latest_sorted if is_ci(path)]
    base_commit = cal["target"].get("base_commit")
    plan.base = ls_tree(src, base_commit) if base_commit else {}
    builder = TreeBuilder(src, base_commit, plan.base)
    last_set = dict.fromkeys(plan.base, 0)
    try:
        plan.trees.append(builder.tree)
        for number, commit in enumerate(cal["commits"], 1):
            entries, sorted_paths = snapshot(commit.get("source_commit") or default_source)
            sets, held_back = {}, False
            for text in commit["paths"]:
                hits = Pattern(text).select(sorted_paths)
                if not hits:
                    problems.append(f"commit #{number}: {text!r} matches no file in the source")
                for path in hits:
                    if number < ci_from and is_ci(path):
                        held_back = True
                    elif builder.state.get(path) != entries[path]:
                        sets[path] = entries[path]
            if number == ci_from:
                sets.update((path, entries[path]) for path in sorted_paths
                            if is_ci(path) and builder.state.get(path) != entries[path])
            removes = []
            for text in commit.get("remove", []):
                rule = Pattern(text)
                hits = [path for path in builder.state if rule.matches(path) and path not in sets]
                if not hits:
                    problems.append(f"commit #{number}: remove {text!r} matches nothing in the destination")
                removes.extend(hits)
            if not sets and not removes:
                problems.append(f"commit #{number} ({subject(commit['message'])!r}) changes nothing: "
                                + (f"CI configuration always arrives with the last commit (#{ci_from}); "
                                   "merge this commit into another one" if held_back else
                                   "every file it names already arrived in an earlier commit"))
            plan.trees.append(builder.apply(sets, removes))
            for path in sets:
                last_set[path] = number
            for path in removes:
                last_set.pop(path, None)
            plan.changes.append({"set": sorted(sets), "removed": sorted(removes)})
        plan.final = dict(builder.state)
    finally:
        builder.close()

    missing = [path for path in latest_sorted if plan.final.get(path) != plan.latest[path]]
    if missing:
        problems.append(f"{len(missing)} source file(s) never reach the destination, e.g. {preview(missing)}. "
                        "Add them to a commit (a last commit with \"**\" picks up everything left).")
    extra = sorted(p for p in plan.final if p not in plan.latest and plan.base.get(p) != plan.final[p])
    if extra:
        problems.append(f"{len(extra)} file(s) would stay in the destination but are no longer in the "
                        f"source: {preview(extra)}. Add them to a commit's \"remove\" list.")
    kept = sorted(p for p in plan.final if p not in plan.latest and plan.base.get(p) == plan.final[p])
    if kept and planning:
        warnings.append(f"files already in the destination stay as they are: {preview(kept)}")
    first_seen = {}
    for number, tree in enumerate(plan.trees):
        if tree in first_seen and number:
            earlier = first_seen[tree]
            problems.append(f"commit #{number} returns the destination to the same files as "
                            f"{'its start' if earlier == 0 else f'commit #{earlier}'}")
        first_seen.setdefault(tree, number)

    covered = set()
    for milestone in cal["milestones"]:
        scope = set()
        for text in sorted(milestone["scope"], key=lambda t: t.strip().startswith("!")):
            hits = Pattern(text).select(latest_sorted)
            if not hits:
                problems.append(f"milestone {milestone['id']}: scope {text!r} matches no file in the source")
            if text.strip().startswith("!"):
                scope.difference_update(hits)
            else:
                scope.update(hits)
        covered |= scope
        plan.milestones.append({
            "files": len(scope),
            "completed_by": max((last_set.get(path, 0) for path in scope), default=0),
        })
    uncovered = [path for path in latest_sorted if path not in covered]
    if uncovered:
        problems.append(f"{len(uncovered)} file(s) fall under no milestone, so nothing says when they are "
                        f"due (e.g. {preview(uncovered)}). Add a whole-project milestone with scope [\"**\"].")
    if planning:
        check_content(src, plan.latest, problems, warnings)
    return plan


def subject(message):
    return message.strip().splitlines()[0].strip() if message.strip() else ""


def check_content(src, entries, problems, warnings):
    """Problems GitHub or the migration would hit: huge files, LFS pointers; notable files."""
    blobs = sorted({sha for mode, sha in entries.values() if mode != "160000"})
    sizes = {}
    if blobs:
        checked = src.git("cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize)",
                          input="\n".join(blobs) + "\n").stdout
        for line in checked.splitlines():
            parts = line.split()
            if len(parts) == 3 and parts[1] == "blob":
                sizes[parts[0]] = int(parts[2])
    huge = sorted(p for p, (_m, sha) in entries.items() if sizes.get(sha, 0) > GITHUB_FILE_LIMIT)
    if huge:
        problems.append(f"GitHub rejects files over 100 MB: {preview(huge)}. Exclude them.")
    big = sorted(p for p, (_m, sha) in entries.items() if GITHUB_FILE_WARNING < sizes.get(sha, 0) <= GITHUB_FILE_LIMIT)
    if big:
        warnings.append(f"GitHub warns about files over 50 MB: {preview(big)}")
    pointers = lfs_pointers(src, entries, sizes)
    if pointers:
        problems.append(f"{len(pointers)} file(s) are Git LFS pointers ({preview(pointers)}); their content "
                        "lives on the LFS server and would not reach the destination. Exclude them, or "
                        "migrate LFS separately.")
    links = sorted(p for p, (mode, _s) in entries.items() if mode == "160000")
    if links:
        warnings.append(f"submodules are copied as links to their own repositories: {preview(links)}")


def lfs_pointers(src, entries, sizes):
    small = sorted({sha for sha, size in sizes.items() if size < LFS_POINTER_MAX})
    if not small:
        return []
    raw = src.git("cat-file", "--batch", input=("\n".join(small) + "\n").encode(), binary=True).stdout
    found, pos = set(), 0
    while pos < len(raw):
        newline = raw.index(b"\n", pos)
        header = raw[pos:newline].split()
        size = int(header[2])
        if raw[newline + 1:newline + 1 + size].startswith(LFS_POINTER):
            found.add(header[0].decode())
        pos = newline + 1 + size + 1
    return sorted(path for path, (_mode, sha) in entries.items() if sha in found)


def ai_tool_files(paths):
    hits = set()
    for path in paths:
        parts = path.split("/")
        for depth, part in enumerate(parts):
            if part in AI_TOOL_DIRS and depth < len(parts) - 1:
                hits.add("/".join(parts[:depth + 1]) + "/")
                break
        else:
            if parts[-1] in AI_TOOL_NAMES or path == ".github/copilot-instructions.md":
                hits.add(path)
    return sorted(hits)


# ---------------------------------------------------------------- the session


class Session:
    """Everything one command knows: calendar, clones, plan and destination progress."""

    def __init__(self, cal, src, tgt, today):
        self.cal, self.src, self.tgt = cal, src, tgt
        self.problems, self.warnings = [], []
        self.questions = list(cal.get("questions", []))
        self.tz = zone(cal["timezone"], cal.get("utc_offset"))
        self.now = dt.datetime.now(self.tz)
        self.today = today or self.now.date()
        self.first_run = parse_time(cal["schedule"]["run_times"][0])
        self.plan = None
        self.target_head = None
        self.source_head = None
        self.done = 0
        self.pushed = {}  # commit number -> (destination sha, aware datetime)

    @property
    def commits(self):
        return self.cal["commits"]

    def load(self, planning, previous=None):
        """Fetch both repositories, build the plan and derive progress from the destination."""
        cal, src, tgt = self.cal, self.src, self.tgt
        for clone, side in ((src, "source"), (tgt, "target")):
            if not same_repo(clone.slug(), cal[side]["repo"]):
                raise Fail(f"{clone.path} is a clone of {clone.slug()}, not of the {side} {cal[side]['repo']}")
        cal["source"]["branch"] = cal["source"]["branch"] or default_branch(src)
        cal["target"]["branch"] = cal["target"]["branch"] or default_branch(tgt)
        if planning:  # a fallback for hosts without timezone data; refreshed only when planning
            cal["utc_offset"] = offset_text(self.now)
        self.source_head = sync_branch(src, cal["source"]["branch"])
        if not self.source_head:
            raise Fail(f"the source repository has no branch {cal['source']['branch']!r}")
        self.target_head = sync_branch(tgt, cal["target"]["branch"])
        if self.target_head:
            src.git("fetch", "--quiet", "--no-tags", tgt.path,
                    f"+refs/remotes/{tgt.remote()}/{cal['target']['branch']}:{TRACKING_REF}")
        cal["source"]["commit"] = cal["source"]["commit"] or self.source_head
        for sha in {cal["source"]["commit"]} | {c["source_commit"] for c in self.commits if "source_commit" in c}:
            ensure_commit(src, sha)
        if "base_commit" not in cal["target"]:
            if previous is not None and "base_commit" in previous.get("target", {}):
                cal["target"]["base_commit"] = previous["target"]["base_commit"]
            elif planning:
                cal["target"]["base_commit"] = self.target_head
            else:
                raise Fail("the calendar does not record the destination's starting commit")
        base = cal["target"]["base_commit"]
        if base and not src.has_commit(base):
            raise Fail(f"the destination no longer contains its starting commit {base[:7]}; "
                       "its history was rewritten")
        self.plan = build_plan(cal, src, self.problems, self.warnings, planning)
        self.derive_progress(previous)
        self.check_source_drift()

    def derive_progress(self, previous):
        """Match destination history to the planned trees (the destination is the truth)."""
        base, head, trees = self.cal["target"].get("base_commit"), self.target_head, self.plan.trees
        total = len(self.commits)
        if head is None:
            if base:
                raise Fail(f"the destination branch {self.cal['target']['branch']} is gone, but the "
                           f"calendar expects it to start at {base[:7]}")
            return
        if base and not self.src.ok("merge-base", "--is-ancestor", base, TRACKING_REF):
            raise Fail("the destination history was rewritten: its starting commit is no longer in it")
        span = [TRACKING_REF] + ([f"^{base}"] if base else [])
        extras = []
        for line in self.src.out("log", "--first-parent", "--reverse", "--format=%H %T %ct", *span).splitlines():
            sha, tree, stamp = line.split()
            if self.done < total and tree == trees[self.done + 1]:
                self.done += 1
                self.pushed[self.done] = (sha, dt.datetime.fromtimestamp(int(stamp), self.tz))
            else:
                extras.append(sha)
        if not extras or self.done == total:
            return
        head_tree = self.src.out("rev-parse", f"{TRACKING_REF}^{{tree}}")
        if head_tree == trees[self.done]:
            self.warnings.append(f"the destination has extra commits that cancel out ({preview([s[:7] for s in extras])})")
            return
        recorded = {c.get("target_sha"): n for n, c in enumerate(self.commits, 1) if c.get("target_sha")}
        if previous:
            recorded.update({c.get("target_sha"): n for n, c in enumerate(previous.get("commits", []), 1)
                             if c.get("target_sha")})
        locked = sorted({recorded[sha] for sha in extras if sha in recorded})
        if locked:
            raise Fail(f"commit(s) {', '.join(f'#{n}' for n in locked)} are already in the destination, but the "
                       f"plan changes them. Keep already-pushed commits exactly as they are and change only "
                       f"later ones (use `export` to start from the installed calendar).")
        raise Fail(f"the destination has commits that are not in the calendar after commit #{self.done}: "
                   f"{preview([s[:7] for s in extras])}. Revert them so its files match commit #{self.done} "
                   f"again, or put those changes into the source repository and re-plan.")

    def check_source_drift(self):
        excludes = [Pattern(text) for text in self.cal["exclude"]]
        if self.source_head != self.cal["source"]["commit"]:
            now = migratable(ls_tree(self.src, self.source_head), excludes)
            if now != self.plan.latest:
                self.warnings.append("the source branch changed after this calendar was planned; those "
                                     "changes are not migrated unless you re-plan with --repin")

    # ------------------------------------------------------------- scheduling

    def milestone_facts(self):
        """Per milestone: stated day, due moment, push cutoff, last planned day, completed_by."""
        facts = []
        margin = self.cal["schedule"]["margin_days"]
        for milestone, computed in zip(self.cal["milestones"], self.plan.milestones):
            stated, due, date_only = parse_deadline(milestone["deadline"], self.tz)
            cutoff = push_cutoff(due, self.first_run)
            fact = {"stated": stated, "due": due, "date_only": date_only, "cutoff": cutoff,
                    "last_day": cutoff - margin * ONE_DAY, **computed}
            if "reached_by" in milestone:  # a reached checkpoint stays where it was reached
                fact["completed_by"] = milestone["reached_by"]
            facts.append(fact)
        return facts

    def check_deadlines(self):
        """Planning-time checks of the requested deadlines (never run against an installed calendar)."""
        for milestone, fact in zip(self.cal["milestones"], self.milestone_facts()):
            stated = fact["stated"]
            if milestone.get("weekday") and WEEKDAYS[stated.weekday()] != milestone["weekday"]:
                self.questions.append(
                    f"Milestone \"{milestone['title']}\": {stated.isoformat()} is a {DAY_NAMES[stated.weekday()]}, "
                    f"but the request says {DAY_NAMES[WEEKDAYS.index(milestone['weekday'])]}. Which date is meant?")
            if milestone.get("reached_at") or fact["due"] > self.now or fact["completed_by"] <= self.done:
                continue
            if self.done == 0:
                self.problems.append(f"milestone {milestone['id']}: its deadline "
                                     f"{moment_text(fact['due'], self.tz)} has already passed")
            else:
                self.warnings.append(f"milestone {milestone['id']} missed its deadline; its remaining "
                                     "commits are scheduled under the later milestones")

    def schedule(self):
        """Date every commit that is not in the destination yet; pins are kept.

        Each milestone is a checkpoint: its commits fit before its deadline (minus the
        margin) and every later commit comes after the deadline, so at the deadline the
        destination holds exactly the commits up to the milestone's last one. Inside each
        window the commits are spread evenly.
        """
        rules = self.cal["schedule"]
        unlocked = list(range(self.done + 1, len(self.commits) + 1))
        if not unlocked:
            return
        upper, lower, reason = {}, {}, {}  # commit -> last day, first day, milestone behind it
        for milestone, fact in zip(self.cal["milestones"], self.milestone_facts()):
            if fact["due"] <= self.now:
                continue
            for number in unlocked:
                if number <= fact["completed_by"]:
                    if not milestone.get("reached_at") and fact["last_day"] < upper.get(number, dt.date.max):
                        upper[number] = fact["last_day"]
                        reason[number] = milestone["id"]
                elif fact["cutoff"] + ONE_DAY > lower.get(number, dt.date.min):
                    lower[number] = fact["cutoff"] + ONE_DAY
        used = Counter(at.date() for _sha, at in self.pushed.values())
        start = dt.date.fromisoformat(rules["start"]) if rules["start"] else self.today
        low = max(start, self.today, max(used) if used else self.today)
        pins = {n: dt.date.fromisoformat(self.commits[n - 1]["date"])
                for n in unlocked if self.commits[n - 1].get("pin")}
        for number, day in pins.items():
            first = max(low, lower.get(number, low))
            if day < first:
                self.problems.append(f"commit #{number} is pinned to {day_text(day)}, but its first possible "
                                     f"day is {day_text(first)}")
            if number in upper and day > upper[number]:
                self.problems.append(f"commit #{number} is pinned to {day_text(day)}, after milestone "
                                     f"{reason[number]} allows ({day_text(upper[number])})")
        ordered = [pins[n] for n in sorted(pins)]
        if ordered != sorted(ordered):
            self.problems.append("pinned dates must follow the commit order")
        if self.problems:
            return

        allowed = {WEEKDAYS.index(day) for day in rules["weekdays"]}
        skip = {dt.date.fromisoformat(day) for day in rules["skip"]}
        per_day, slots, cursor = rules["per_day"], [], [low]

        def grow(until_day=None, until_count=0):
            """Add the free commit slots of each following day until both targets are met."""
            while (until_day and cursor[0] <= until_day) or len(slots) < until_count:
                day = cursor[0]
                if day > low + 3660 * ONE_DAY:
                    raise Fail("no free day within ten years; check schedule.weekdays and schedule.skip")
                if day in pins.values() or (day.weekday() in allowed and day not in skip):
                    slots.extend([day] * max(per_day - used.get(day, 0), 0))
                cursor[0] = day + ONE_DAY

        grow(max([low] + list(upper.values()) + list(lower.values()) + list(pins.values())))
        for limit in sorted(set(upper.values())):
            need = sum(1 for n in unlocked if upper.get(n, dt.date.max) <= limit)
            have = bisect.bisect_right(slots, limit)
            if need > have:
                names = sorted({reason[n] for n in unlocked if upper.get(n) == limit})
                self.problems.append(
                    f"{plural(need, 'commit')} must be in the destination by {day_text(limit)} (milestone "
                    f"{', '.join(names)}), but only {plural(have, 'commit slot')} exist from {day_text(low)} at "
                    f"{per_day} per day on the allowed days. Use fewer commits before it, allow more per day, "
                    "or start earlier.")
        if self.problems:
            return

        earliest, previous = [], -1  # forward pass: earliest slot each commit can take
        for number in unlocked:
            floor = pins.get(number) or lower.get(number)
            index = previous + 1
            if floor:
                index = max(index, bisect.bisect_left(slots, floor))
            grow(until_count=index + 1)
            earliest.append(index)
            previous = index
        latest, limit = [0] * len(unlocked), len(slots)  # backward pass: latest slot each can take
        for i in range(len(unlocked) - 1, -1, -1):
            number = unlocked[i]
            cap = pins.get(number) or upper.get(number)
            j = limit - 1 if cap is None else min(limit - 1, bisect.bisect_right(slots, cap) - 1)
            if number in pins and (j < earliest[i] or slots[j] != pins[number]):
                self.problems.append(f"commit #{number} cannot keep its pinned day {day_text(pins[number])}: "
                                     "the commits around it need that slot")
                return
            if j < earliest[i]:
                self.problems.append(
                    f"commit #{number} must come after the deadline of the milestone before it and by "
                    f"{day_text(cap) if cap else 'the end'}{f' (milestone {reason[number]})' if number in reason else ''}, "
                    "but the commits around it already fill those days. Use fewer commits in that part of the "
                    "calendar, allow more commits per day, or move a deadline.")
                return
            latest[i] = limit = j

        ideal, i, floor_index = [0] * len(unlocked), 0, 0  # even spread inside each window
        while i < len(unlocked):
            key = (lower.get(unlocked[i]), upper.get(unlocked[i]))
            j = i
            while j < len(unlocked) and (lower.get(unlocked[j]), upper.get(unlocked[j])) == key:
                j += 1
            count = j - i
            first = max(floor_index, bisect.bisect_left(slots, key[0]) if key[0] else floor_index)
            last = bisect.bisect_right(slots, key[1]) - 1 if key[1] else first + count - 1
            span = max(last - first + 1, 1)
            for t in range(count):
                ideal[i + t] = first + (t * span) // count
            floor_index, i = max(last + 1, floor_index), j

        previous = -1
        for i, number in enumerate(unlocked):
            if number in pins:
                index = max(bisect.bisect_left(slots, pins[number]), previous + 1)
            else:
                index = min(max(ideal[i], previous + 1, earliest[i]), latest[i])
            self.commits[number - 1]["date"] = slots[index].isoformat()
            previous = index

    # --------------------------------------------------------------- execution

    def check_dates(self):
        for number in range(self.done + 1, len(self.commits) + 1):
            if not self.commits[number - 1].get("date"):
                raise Fail(f"commit #{number} has no date; install the calendar again")

    def due(self):
        return [n for n in range(self.done + 1, len(self.commits) + 1)
                if dt.date.fromisoformat(self.commits[n - 1]["date"]) <= self.today]

    def push_due(self):
        """Create every due commit now, as the user, and push them to the destination."""
        due = self.due()
        if not due:
            return []
        for number in due:
            leaked = self.src.out("ls-tree", "-r", "--name-only", self.plan.trees[number], "--", SKILL_DIR)
            if leaked:
                raise Fail(f"refusing to push: commit #{number} would contain {SKILL_DIR}/")
        parent, made = self.target_head, []
        for number in due:
            sha, when = make_commit(self.src, self.plan.trees[number], parent,
                                    self.commits[number - 1]["message"], self.cal["author"], self.tz)
            made.append((number, sha, when))
            parent = sha
        self.src.git("update-ref", OUTGOING_REF, parent)
        self.tgt.git("fetch", "--quiet", "--no-tags", self.src.path, f"+{OUTGOING_REF}:{OUTGOING_REF}")
        try:
            push(self.tgt, parent, self.cal["target"]["branch"])
        except Rejected as err:
            raise Fail(f"the destination changed while this run was pushing; the next run checks again ({err})") from None
        for number, sha, when in made:
            self.pushed[number] = (sha, when)
        self.done, self.target_head = due[-1], parent
        return made

    def record(self):
        """Write destination facts into the calendar: push times, shas, reached milestones."""
        for number, commit in enumerate(self.commits, 1):
            if number in self.pushed:
                sha, when = self.pushed[number]
                commit["pushed_at"] = when.isoformat(timespec="seconds")
                commit["target_sha"] = sha
            else:
                commit.pop("pushed_at", None)
                commit.pop("target_sha", None)
        for milestone, fact in zip(self.cal["milestones"], self.milestone_facts()):
            needed = fact["completed_by"]
            if "reached_at" not in milestone and needed and needed <= self.done:
                milestone["reached_at"] = max(self.pushed[n][1] for n in range(1, needed + 1)).isoformat(timespec="seconds")
                milestone["reached_by"] = needed

    def publish(self, include_engine, message):
        """Commit the calendar, reports (and engine) to the source branch; retry if it moved."""
        branch = self.cal["source"]["branch"]
        for _attempt in range(PUSH_ATTEMPTS):
            base = sync_branch(self.src, branch)
            if not base:
                raise Fail(f"the source repository has no branch {branch!r}")
            files = {CALENDAR_FILE: render_calendar(self).encode()}
            for name, text in render_reports(self).items():
                files[f"{REPORT_DIR}/{name}"] = text.encode()
            if include_engine:
                files[ENGINE_FILE] = Path(__file__).read_bytes()
            index = ScratchIndex(self.src)
            try:
                index.git("read-tree", base)
                zero = "0" * len(base)
                stale = [p for p in ls_tree(self.src, base) if p.startswith(REPORT_DIR + "/") and p not in files]
                records = [f"0 {zero}\t{path}" for path in stale]
                for path, data in files.items():
                    sha = self.src.git("hash-object", "-w", "--stdin", input=data, binary=True).stdout.decode().strip()
                    records.append(f"{'100755' if path == ENGINE_FILE else '100644'} {sha}\t{path}")
                index.git("update-index", "-z", "--index-info", input="\0".join(records) + "\0")
                tree = self.src.out("write-tree", env=index.env)
            finally:
                index.close()
            if tree == self.src.out("rev-parse", f"{base}^{{tree}}"):
                return None
            sha, _when = make_commit(self.src, tree, base, message, self.cal["author"], self.tz)
            try:
                push(self.src, sha, branch)
                return sha
            except Rejected:
                log("the source branch moved during publishing; retrying on top of it")
        raise Fail("could not save the calendar: the source branch kept changing")

    def next_commit(self):
        if self.done >= len(self.commits):
            return None
        commit = self.commits[self.done]
        return {"number": self.done + 1, "date": commit.get("date"), "message": subject(commit["message"])}

    def summary(self):
        facts = self.milestone_facts()
        return {
            "pushed": self.done,
            "total": len(self.commits),
            "next": self.next_commit(),
            "milestones": [{"id": m["id"], "status": milestone_status(self, m, f)}
                           for m, f in zip(self.cal["milestones"], facts)],
            "warnings": self.warnings,
        }


# ------------------------------------------------------------------- rendering


def cell(text):
    return str(text).replace("|", "\\|").replace("\n", " ")


def commit_status(session, number):
    commit = session.commits[number - 1]
    if number in session.pushed:
        sha, when = session.pushed[number]
        return f"pushed {moment_text(when, session.tz)} (`{sha[:7]}`)"
    if commit.get("date") and dt.date.fromisoformat(commit["date"]) < session.today:
        return "overdue"
    return "planned"


def milestone_status(session, milestone, fact):
    if milestone.get("reached_at"):
        at = dt.datetime.fromisoformat(milestone["reached_at"])
        return f"reached {moment_text(at, session.tz)}" + ("" if at <= fact["due"] else " (late)")
    needed = fact["completed_by"]
    if needed == 0:
        return "already in the destination"
    if session.now > fact["due"]:
        return "missed"
    behind = any(n not in session.pushed and session.commits[n - 1].get("date")
                 and dt.date.fromisoformat(session.commits[n - 1]["date"]) < session.today
                 for n in range(1, needed + 1))
    return "behind schedule" if behind else "on track"


def deadline_text(fact, tz_name, said=None):
    stated = day_text(fact["stated"])
    if said and WEEKDAYS[fact["stated"].weekday()] != said:
        stated += f" (request says {DAY_NAMES[WEEKDAYS.index(said)]})"
    if fact["date_only"]:
        return stated, f"{day_text(fact['due'].date())} 23:59"
    return f"{stated} {fact['due'].strftime('%H:%M')}", f"{day_text(fact['due'].date())} {fact['due'].strftime('%H:%M')}"


def change_summary(change):
    groups = Counter(path.split("/", 1)[0] + "/" if "/" in path else "(root)" for path in change["set"])
    parts = [f"{name} {count}" for name, count in groups.most_common(4 if len(groups) <= 4 else 3)]
    if len(groups) > 4:
        parts.append(f"{len(groups) - 3} more folders")
    text = str(len(change["set"])) + (f" ({', '.join(parts)})" if parts else "")
    if change["removed"]:
        text += f", {len(change['removed'])} removed"
    return text


def scope_text(milestone, fact):
    return f"{', '.join(f'`{s}`' for s in milestone['scope'])} ({plural(fact['files'], 'file')})"


def effective_day(session, number):
    if number in session.pushed:
        return session.pushed[number][1].date()
    date = session.commits[number - 1].get("date")
    return dt.date.fromisoformat(date) if date else None


KEY_ORDER = {
    "top": ("version", "source", "target", "author", "timezone", "utc_offset", "schedule", "exclude",
            "notes", "questions", "ci_from", "milestones", "commits"),
    "source": ("repo", "branch", "commit"),
    "target": ("repo", "branch", "base_commit"),
    "milestone": ("id", "title", "request", "deadline", "weekday", "scope", "reached_at", "reached_by"),
    "commit": ("message", "paths", "remove", "source_commit", "date", "pin", "pushed_at", "target_sha"),
}


def ordered(mapping, keys):
    """Known keys in a fixed order, then any others: identical state always renders identically."""
    out = {key: mapping[key] for key in keys if key in mapping}
    out.update((key, value) for key, value in mapping.items() if key not in out)
    return out


def state_json(cal):
    state = ordered(cal, KEY_ORDER["top"])
    for side in ("source", "target"):
        if isinstance(state.get(side), dict):
            state[side] = ordered(state[side], KEY_ORDER[side])
    state["milestones"] = [ordered(m, KEY_ORDER["milestone"]) for m in state.get("milestones", [])]
    state["commits"] = [ordered(c, KEY_ORDER["commit"]) for c in state.get("commits", [])]
    return json.dumps(state, indent=2, ensure_ascii=False)


def render_calendar(session):
    cal = session.cal
    total = len(session.commits)
    lines = [
        "# Commit calendar",
        "",
        ("> Managed by the timed-commit-automation skill. Ask the skill to change the plan instead of "
         "editing this file; the JSON block at the end is the source of truth."),
        "",
        "| | |",
        "|---|---|",
        f"| Source | `{cal['source']['repo']}` (`{cal['source']['branch']}`), snapshot `{cal['source']['commit'][:7]}` |",
        f"| Destination | `{cal['target']['repo']}` (`{cal['target']['branch']}`) |",
        f"| Commit author | `{cal['author']['name']} <{cal['author']['email']}>` |",
        f"| Timezone | {cal['timezone']} |",
        f"| Routine runs | {', '.join(cal['schedule']['run_times'])} every day |",
        "",
        "## Progress",
        "",
    ]
    nxt = session.next_commit()
    if nxt:
        lines.append(f"**{session.done} / {total}** commits are in the destination. Next: #{nxt['number']} "
                     f"`{cell(nxt['message'])}` on {day_text(dt.date.fromisoformat(nxt['date']))}.")
    else:
        lines.append(f"**All {total} commits are in the destination.**")
    for warning in session.warnings:
        if "source branch changed" in warning:
            lines += ["", f"> Note: {warning}."]
    if cal.get("notes"):
        lines += ["", "## Notes", ""] + [f"- {note}" for note in cal["notes"]]
    lines += ["", "## Milestones", "",
              "| Milestone | Requested deadline | Must be in the destination by | Completed by | Status |",
              "|---|---|---|---|---|"]
    for milestone, fact in zip(cal["milestones"], session.milestone_facts()):
        stated, due = deadline_text(fact, cal["timezone"])
        number = fact["completed_by"]
        done_day = effective_day(session, number) if number else None
        completed = f"#{number} on {day_text(done_day)}" if done_day else "-"
        lines.append(f"| {cell(milestone['title'])} | {stated} | {due} | {completed} | "
                     f"{milestone_status(session, milestone, fact)} |")
    lines += ["", "## Commits", "", "| # | Date | Message | Files | Status |", "|---|---|---|---|---|"]
    for number, commit in enumerate(session.commits, 1):
        date = commit.get("date")
        shown = (day_text(dt.date.fromisoformat(date)) if date else "-") + (" (pinned)" if commit.get("pin") else "")
        lines.append(f"| {number} | {shown} | {cell(subject(commit['message']))} | "
                     f"{change_summary(session.plan.changes[number - 1])} | {commit_status(session, number)} |")
    lines += ["", "<details>", "<summary>Machine-readable state</summary>", "", STATE_BEGIN, "```json",
              state_json(cal), "```", STATE_END, "", "</details>", ""]
    return "\n".join(lines)


def render_reports(session):
    """One report per milestone: only the commits up to its deadline, and the files they leave."""
    reports = {}
    cal = session.cal
    for milestone, fact in zip(cal["milestones"], session.milestone_facts()):
        included = [n for n in range(1, len(session.commits) + 1)
                    if effective_day(session, n) and effective_day(session, n) <= fact["cutoff"]]
        stated, due = deadline_text(fact, cal["timezone"])
        rule = (" (a date without a time means everything is in the destination before that day starts)"
                if fact["date_only"] else "")
        number = fact["completed_by"]
        done_day = effective_day(session, number) if number else None
        lines = [
            f"# Progress report: {milestone['title']}",
            "",
            "> Generated by the timed-commit-automation skill from ../calendar.md.",
            "",
            "| | |",
            "|---|---|",
            f"| Request | {cell(milestone['request'] or milestone['title'])} |",
            f"| Deadline | {stated}; everything must be in the destination by {due} {cal['timezone']}{rule} |",
            f"| Scope | {cell(', '.join(f'`{s}`' for s in milestone['scope']))} ({fact['files']} files) |",
            f"| Completed by | {f'#{number} on {day_text(done_day)}' if done_day else '-'} |",
            f"| Status | {milestone_status(session, milestone, fact)} |",
            "",
            f"## Commits up to {day_text(fact['cutoff'])} ({len(included)})",
            "",
            "| # | Date | Message | Status |",
            "|---|---|---|---|",
        ]
        for n in included:
            date = session.commits[n - 1].get("date")
            lines.append(f"| {n} | {day_text(dt.date.fromisoformat(date)) if date else '-'} | "
                         f"{cell(subject(session.commits[n - 1]['message']))} | {commit_status(session, n)} |")
        tree = session.plan.trees[included[-1]] if included else session.plan.trees[0]
        files = session.src.git("ls-tree", "-r", "-z", "--name-only", tree).stdout.split("\0")
        files = [f for f in files if f]
        groups = Counter(f.split("/", 1)[0] + "/" if "/" in f else "(root)" for f in files)
        lines += ["", f"## Project state after these commits ({len(files)} files)", "",
                  "| Folder | Files |", "|---|---|"]
        lines += [f"| {cell(name)} | {count} |" for name, count in sorted(groups.items())]
        lines += ["", "<details>", "<summary>All files</summary>", ""]
        lines += [f"- `{f}`" for f in files[:2000]]
        if len(files) > 2000:
            lines.append(f"- ... and {len(files) - 2000} more")
        lines += ["", "</details>", ""]
        reports[f"{fact['stated'].isoformat()}-{milestone['id']}.md"] = "\n".join(lines)
    return reports


def render_review(session, excluded):
    """What the user approves: questions first, then milestones, commits and assumptions."""
    cal, rules = session.cal, session.cal["schedule"]
    total = len(session.commits)
    unlocked = range(session.done + 1, total + 1)
    dates = [dt.date.fromisoformat(session.commits[n - 1]["date"]) for n in unlocked
             if session.commits[n - 1].get("date")]
    lines = ["# Commit calendar draft", ""]
    head = f"**{plural(total, 'commit')}**" + (f" ({session.done} already in the destination)" if session.done else "")
    if dates:
        head += (f", planned from {day_text(min(dates))} to {day_text(max(dates))}, at most "
                 f"{plural(rules['per_day'], 'commit')} per day.")
    lines.append(head + ("" if dates else ", not scheduled yet (see the problems below)."))
    if session.questions:
        lines += ["", "## Questions for the user", ""] + [f"- {q}" for q in session.questions]
    if session.problems:
        lines += ["", "## Problems to fix before installing", ""] + [f"- {p}" for p in session.problems]
    lines += ["", "## Milestones", "",
              "| Milestone | Requested | Must be in the destination by | Completed by | Spare days | Scope |",
              "|---|---|---|---|---|---|"]
    for milestone, fact in zip(cal["milestones"], session.milestone_facts()):
        stated, due = deadline_text(fact, cal["timezone"], milestone.get("weekday"))
        number = fact["completed_by"]
        day = effective_day(session, number) if number else None
        spare = (fact["cutoff"] - day).days if day else "-"
        lines.append(f"| {cell(milestone['title'])} | {stated} | {due} | "
                     f"{f'#{number} on {day_text(day)}' if day else '-'} | {spare} | {cell(scope_text(milestone, fact))} |")
    lines += ["", "## Commits", "", "| # | Date | Message | Files |", "|---|---|---|---|"]
    before = {subject(c.get("message", "")): c.get("date") for c in
              (getattr(session, "previous", None) or {}).get("commits", []) if not c.get("target_sha")}
    for number, commit in enumerate(session.commits, 1):
        date = commit.get("date")
        shown = day_text(dt.date.fromisoformat(date)) if date else "unscheduled"
        if number <= session.done:
            shown += " (pushed)"
        elif commit.get("pin"):
            shown += " (pinned)"
        was = before.get(subject(commit["message"]))
        if number > session.done and was and date and was != date:
            shown += f" (was {day_text(dt.date.fromisoformat(was))})"
        lines.append(f"| {number} | {shown} | {cell(subject(commit['message']))} | "
                     f"{change_summary(session.plan.changes[number - 1])} |")
    lines += ["", "<details>", "<summary>Files per commit</summary>", ""]
    for number, change in enumerate(session.plan.changes, 1):
        files = change["set"] + [f"{path} (removed)" for path in change["removed"]]
        lines.append(f"- #{number}: " + (", ".join(f"`{f}`" for f in files[:60])
                                         + (f" and {len(files) - 60} more" if len(files) > 60 else "")))
    lines += ["", "</details>"]
    margin = rules["margin_days"]
    lines += [
        "", "## Assumptions", "",
        (f"- Every destination commit is authored and committed by `{cal['author']['name']} "
         f"<{cal['author']['email']}>`, at the real time it is pushed, with no co-author or tool trailers."),
        (f"- Timezone {cal['timezone']}. The routine runs every day at {' and '.join(rules['run_times'])}; "
         "a commit planned for a day is pushed by that day's first run, and later runs retry."),
        ("- A deadline without a time means everything is in the destination before that day starts "
         f"(23:59 the day before); each milestone's commits are planned {plural(margin, 'day')} earlier as a margin."),
        ("- Each milestone is a checkpoint: at its deadline the destination holds exactly the commits up to "
         "the milestone's last commit; later commits start on the day the user named, or after it."),
        (f"- Never copied to the destination: `{SKILL_DIR}/` (always)"
         + (f", and by `exclude`: {preview(excluded)}" if excluded else "") + "."),
    ]
    if session.plan.base:
        replaced = sorted(p for p in session.plan.base if p in session.plan.latest)
        kept = sorted(p for p in session.plan.base if p not in session.plan.latest)
        lines.append(f"- The destination already has files. Replaced by the source version: "
                     f"{preview(replaced) or 'none'}; kept as they are: {preview(kept) or 'none'}.")
    elif not session.target_head:
        lines.append("- The destination is empty.")
    if session.plan.ci_files:
        lines.append(f"- CI configuration ({preview(session.plan.ci_files)}) arrives with commit "
                     f"#{cal['ci_from']}, the last one, so CI never runs on an unfinished project.")
    if dates:
        due_now = session.due()
        if len(due_now) == 1:
            lines.append(f"- Commit #{due_now[0]} is due today, so installing pushes it immediately.")
        elif due_now:
            lines.append(f"- Commits {', '.join(f'#{n}' for n in due_now)} are due today, so installing pushes "
                         "them immediately.")
    lines += [f"- {note}" for note in cal.get("notes", [])]
    if session.warnings:
        lines += ["", "## Warnings", ""] + [f"- {w}" for w in session.warnings]
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------- GitHub issues


def gh_api(*args):
    if not shutil.which("gh"):
        return None
    try:
        result = subprocess.run(["gh", "api", *args], capture_output=True, text=True, timeout=60, check=False)
    except subprocess.TimeoutExpired:
        log(f"warning: gh api {args[0]} timed out")
        return None
    if result.returncode != 0:
        log(f"warning: gh api {args[0]} failed: {result.stderr.strip()}")
        return None
    return json.loads(result.stdout) if result.stdout.strip() else {}


def open_issue(repo):
    for issue in gh_api(f"repos/{repo}/issues?state=open&per_page=100") or []:
        if issue.get("title") == ISSUE_TITLE and "pull_request" not in issue:
            return issue["number"]
    return None


def report_failure(repo, message):
    body = (f"The scheduled run at {dt.datetime.now().astimezone().isoformat(timespec='minutes')} failed:\n\n"
            f"```\n{message}\n```\n\nNothing was pushed by the failing step; the next run retries. "
            "If this repeats, run the timed-commit-automation skill and ask it to check the migration.")
    number = open_issue(repo)
    if number:
        gh_api(f"repos/{repo}/issues/{number}/comments", "-f", f"body={body}")
    else:
        gh_api(f"repos/{repo}/issues", "-f", f"title={ISSUE_TITLE}", "-f", f"body={body}")


def resolve_failure(repo, summary):
    number = open_issue(repo)
    if number:
        gh_api(f"repos/{repo}/issues/{number}/comments", "-f", f"body=Runs work again: {summary}")
        gh_api(f"repos/{repo}/issues/{number}", "-X", "PATCH", "-f", "state=closed")


# --------------------------------------------------------------------- commands


def parse_today(text):
    if not text:
        return None
    try:
        return dt.date.fromisoformat(text)
    except ValueError:
        raise Fail(f"--today {text!r} is not a YYYY-MM-DD date") from None


def find_target(src, slug):
    """The destination clone next to the source clone (cloud routines clone side by side)."""
    candidates = [Path(os.environ["TCA_TARGET"])] if os.environ.get("TCA_TARGET") else []
    for root in (Path(src.path).parent, Path.cwd()):
        try:
            candidates += sorted(path for path in root.iterdir() if path.is_dir())
        except OSError:
            continue
    seen = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen or str(candidate) == src.path or not (candidate / ".git").exists():
            continue
        seen.add(candidate)
        try:
            clone = Repo(candidate)
            if same_repo(clone.slug(), slug):
                return clone
        except Fail:
            continue
    raise Fail(f"no clone of the destination {slug} was found next to {src.path}; add {slug} to the "
               "routine's repositories (or pass --target)")


def prepare_draft(args):
    """Shared by plan and install: draft + clones -> (scheduled session or None, problems, warnings)."""
    problems, warnings = [], []
    raw = load_draft(args.draft)
    cal = normalize(raw, problems, warnings)
    src, tgt = Repo(args.source), Repo(args.target)
    branch = cal["source"]["branch"] or default_branch(src)
    previous, _head = read_installed(src, branch)
    if previous is not None:
        old = (repo_slug(previous.get("target", {}).get("repo")) or "")
        if cal["target"]["repo"] and not same_repo(old, cal["target"]["repo"]):
            raise Fail(f"this source repository already has a calendar for {old}; finish or remove it first")
        reached = {m.get("id"): m for m in previous.get("milestones", []) if m.get("reached_at")}
        for milestone in cal["milestones"]:
            if milestone["id"] in reached and "reached_at" not in milestone:
                for key in ("reached_at", "reached_by"):
                    if key in reached[milestone["id"]]:
                        milestone[key] = reached[milestone["id"]][key]
    if problems:
        return None, problems, warnings
    keep = cal["ci_from"]
    if not (keep and cal["commits"][keep - 1].get("target_sha")):
        cal["ci_from"] = len(cal["commits"])
    session = Session(cal, src, tgt, parse_today(args.today))
    session.problems, session.warnings, session.previous = problems, warnings, previous
    if args.repin:
        head = sync_branch(src, branch)
        old_commit = cal["source"]["commit"]
        if old_commit and head != old_commit:
            for commit in cal["commits"]:
                if commit.get("target_sha") and "source_commit" not in commit:
                    commit["source_commit"] = old_commit
        cal["source"]["commit"] = head
    session.load(planning=True, previous=previous)
    session.check_deadlines()
    if not problems:
        session.schedule()
    return session, problems, warnings


def excluded_files(session):
    rules = [Pattern(text) for text in session.cal["exclude"]]
    return sorted(p for p in ls_tree(session.src, session.cal["source"]["commit"])
                  if not p.startswith(SKILL_DIR + "/") and any(rule.matches(p) for rule in rules))


def cmd_plan(args):
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    reports = out / "progress-report"
    for stale in (out / "review.md", out / "calendar.md"):  # never show an earlier preview
        stale.unlink(missing_ok=True)
    shutil.rmtree(reports, ignore_errors=True)
    session, problems, warnings = prepare_draft(args)
    if session is None:
        emit("invalid", problems=problems, warnings=warnings)
        return 1
    status = "invalid" if problems else ("questions" if session.questions else "valid")
    (out / "review.md").write_text(render_review(session, excluded_files(session)), encoding="utf-8")
    scheduled = all(c.get("date") for c in session.commits)
    if scheduled:
        (out / "calendar.md").write_text(render_calendar(session), encoding="utf-8")
        reports.mkdir()
        for name, text in render_reports(session).items():
            (reports / name).write_text(text, encoding="utf-8")
    facts = session.milestone_facts()
    emit(status, commits=len(session.commits), already_pushed=session.done,
         first=session.commits[session.done]["date"] if scheduled and session.done < len(session.commits) else None,
         last=session.commits[-1].get("date"),
         milestones=[{"id": m["id"], "completed_by": f["completed_by"],
                      "must_be_in_by": f["due"].isoformat(timespec="minutes")}
                     for m, f in zip(session.cal["milestones"], facts)],
         review=str(out / "review.md"), problems=problems, questions=session.questions, warnings=warnings)
    return 0 if status == "valid" else 1


def cmd_install(args):
    session, problems, warnings = prepare_draft(args)
    if session is None or problems or session.questions:
        emit("invalid", problems=problems, questions=session.questions if session else [], warnings=warnings,
             message="fix every problem, and answer every question and remove it from the draft, before installing")
        return 1
    made = [] if args.no_run else session.push_due()
    session.record()
    sha = session.publish(include_engine=True, message="chore: update commit calendar"
                          if session.previous is not None else "chore: add commit calendar")
    emit("installed", calendar_commit=sha, pushed_now=pushed_list(made), **session.summary())
    return 0


def source_clone(args):
    """--source, or the clone this engine copy lives in (how the routine runs it)."""
    return Repo(args.source) if args.source else Repo(Path(__file__).resolve().parent.parent)


def load_installed_session(args, src):
    local = Path(src.path, CALENDAR_FILE)
    branch = None
    if local.exists():
        try:
            branch = (parse_calendar_text(local.read_text(encoding="utf-8")).get("source") or {}).get("branch")
        except Fail:
            branch = None
    raw, _head = read_installed(src, branch or default_branch(src))
    if raw is None:
        raise Fail(f"no calendar is installed in {src.slug()}")
    problems, warnings = [], []
    cal = normalize(raw, problems, warnings)
    if problems:
        raise Fail("the installed calendar is invalid: " + "; ".join(problems))
    tgt = Repo(args.target) if args.target else find_target(src, cal["target"]["repo"])
    session = Session(cal, src, tgt, parse_today(args.today))
    session.warnings = warnings
    session.load(planning=False)
    if session.problems:
        raise Fail("the installed calendar no longer matches the repositories: " + "; ".join(session.problems))
    session.check_dates()
    return session


def cmd_run(args):
    report = args.report or bool(os.environ.get("CLAUDE_CODE_REMOTE"))
    repo = None
    try:
        src = source_clone(args)
        repo = src.slug()
        session = load_installed_session(args, src)
        if args.dry_run:
            emit("dry_run", would_push=[{"number": n, "message": subject(session.commits[n - 1]["message"])}
                                        for n in session.due()], **session.summary())
            return 0
        made = session.push_due()
        session.record()
        pushed = session.done
        session.publish(include_engine=False,
                        message=f"chore: record commit calendar progress ({pushed}/{len(session.commits)})")
        status = "pushed" if made else ("complete" if pushed == len(session.commits) else "up_to_date")
        if report:
            resolve_failure(repo, f"{pushed}/{len(session.commits)} commits are in the destination")
        extra = {"next_step": "the calendar is complete; delete this routine at claude.ai/code/routines"} \
            if pushed == len(session.commits) else {}
        emit(status, pushed_now=pushed_list(made), **session.summary(), **extra)
        return 0
    except Exception as err:  # noqa: BLE001 - the routine must always get a JSON line and an issue
        message = str(err) if isinstance(err, Fail) else internal_error(err)
        if report and repo:
            report_failure(repo, message)
        emit("error", message=message)
        return 1


def pushed_list(made):
    return [{"number": n, "sha": sha, "at": when.isoformat(timespec="seconds")} for n, sha, when in made]


def internal_error(err):
    import traceback
    traceback.print_exc()
    return f"internal error ({type(err).__name__}: {err}); the traceback is in the run log"


def cmd_status(args):
    session = load_installed_session(args, source_clone(args))
    emit("ok", due_now=session.due(), **session.summary())
    return 0


def cmd_export(args):
    src = Repo(args.source)
    raw, _head = read_installed(src, default_branch(src))
    if raw is None:
        raise Fail(f"no calendar is installed in {src.slug()}")
    Path(args.out).write_text(state_json(raw) + "\n", encoding="utf-8")
    emit("ok", path=str(Path(args.out).resolve()), commits=len(raw.get("commits", [])),
         pushed=sum(1 for c in raw.get("commits", []) if c.get("target_sha")))
    return 0


def cmd_routine(args):
    src = Repo(args.source)
    raw, _head = read_installed(src, default_branch(src))
    if raw is None:
        raise Fail(f"no calendar is installed in {src.slug()}; install it first")
    problems, warnings = [], []
    cal = normalize(raw, problems, warnings)
    tz = zone(cal["timezone"], cal.get("utc_offset"))
    today = dt.datetime.now(tz).date()
    dates = [dt.date.fromisoformat(c["date"]) for c in cal["commits"] if c.get("date")]
    end = max(dates + [today])
    notes = []
    if offset_text(dt.datetime.combine(today, dt.time(12), tz)) != offset_text(dt.datetime.combine(end, dt.time(12), tz)):
        notes.append("daylight saving time changes during the calendar, so runs shift by one hour "
                     "afterwards; dates, not hours, decide what is pushed, so nothing is affected")
    emit("ok",
         name=f"Timed commits: {cal['source']['repo']} -> {cal['target']['repo']}",
         repositories=[f"https://github.com/{cal['source']['repo']}", f"https://github.com/{cal['target']['repo']}"],
         cron_utc=cron_utc(cal["schedule"]["run_times"], tz, today),
         local_run_times=cal["schedule"]["run_times"], timezone=cal["timezone"],
         model=ROUTINE_MODEL, allowed_tools=ROUTINE_TOOLS, connectors="none",
         prompt=ROUTINE_PROMPT.format(source=cal["source"]["repo"], target=cal["target"]["repo"], skill_dir=SKILL_DIR),
         notes=notes)
    return 0


def guess_author(src):
    if shutil.which("gh"):
        try:
            result = subprocess.run(["gh", "api", "user"], capture_output=True, text=True, timeout=30, check=False)
            if result.returncode == 0:
                user = json.loads(result.stdout)
                return {"name": user.get("name") or user["login"], "login": user["login"],
                        "email": f"{user['id']}+{user['login']}@users.noreply.github.com", "from": "gh api user"}
        except (subprocess.TimeoutExpired, ValueError, KeyError):
            pass
    rows = src.out("log", "-n", "300", "--format=%an%x09%ae", check=False).splitlines()
    if rows:
        name, email = Counter(rows).most_common(1)[0][0].split("\t", 1)
        return {"name": name, "email": email, "from": "most frequent author in the source history"}
    return None


def cmd_inspect(args):
    src, tgt = Repo(args.source), Repo(args.target)
    branch = default_branch(src)
    head = sync_branch(src, branch)
    if not head:
        raise Fail(f"the source repository has no commits on {branch!r}")
    target_branch = default_branch(tgt)
    target_head = sync_branch(tgt, target_branch)
    all_entries = ls_tree(src, head)
    entries = {p: v for p, v in all_entries.items() if not p.startswith(SKILL_DIR + "/")}
    problems, warnings = [], []
    check_content(src, entries, problems, warnings)
    top = Counter(p.split("/", 1)[0] for p in entries if "/" in p)
    second = Counter("/".join(p.split("/")[:2]) for p in entries if p.count("/") >= 2)
    folders = [{"path": name + "/", "files": count,
                "subfolders": [{"path": sub + "/", "files": n} for sub, n in sorted(second.items())
                               if sub.startswith(name + "/")][:25]}
               for name, count in sorted(top.items())]
    target_files = sorted(ls_tree(tgt, target_head)) if target_head else []
    tz_name = detect_timezone()
    emit("ok",
         today=dt.datetime.now(zone(tz_name, "+00:00")).date().isoformat(), timezone=tz_name,
         author=guess_author(src),
         source={"repo": src.slug(), "branch": branch, "head": head, "files": len(entries),
                 "folders": folders, "root_files": sorted(p for p in entries if "/" not in p),
                 "ai_tool_files": ai_tool_files(entries),
                 "ci_files": sorted(p for p in entries if any(Pattern(c).matches(p) for c in CI_PATTERNS)),
                 "calendar_installed": CALENDAR_FILE in all_entries},
         target={"repo": tgt.slug(), "branch": target_branch, "head": target_head, "empty": not target_head,
                 "files": target_files[:100], "file_count": len(target_files)},
         problems=problems, warnings=warnings)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    def clones(p, optional=False):
        p.add_argument("--source", required=not optional, help="clone of the source repository")
        p.add_argument("--target", required=not optional, help="clone of the destination repository")

    p = sub.add_parser("inspect", help="facts about both clones, for planning")
    clones(p)
    for name, text in (("plan", "validate and schedule a draft, write a preview"),
                       ("install", "save the calendar in the source repo and push due commits")):
        p = sub.add_parser(name, help=text)
        p.add_argument("--draft", required=True, help="draft calendar (JSON, or an exported calendar)")
        clones(p)
        p.add_argument("--repin", action="store_true",
                       help="take file contents from the current source branch head")
        p.add_argument("--today", help=argparse.SUPPRESS)
        if name == "plan":
            p.add_argument("--out", required=True, help="folder for review.md and the preview files")
        else:
            p.add_argument("--no-run", action="store_true", help="do not push due commits now")
    p = sub.add_parser("run", help="push due commits and record progress")
    clones(p, optional=True)
    p.add_argument("--dry-run", action="store_true", help="show what is due without changing anything")
    p.add_argument("--report", action="store_true",
                   help="open/close a GitHub issue on failure/recovery (default in cloud sessions)")
    p.add_argument("--today", help=argparse.SUPPRESS)
    p = sub.add_parser("status", help="read-only progress summary")
    clones(p, optional=True)
    p.add_argument("--today", help=argparse.SUPPRESS)
    p = sub.add_parser("export", help="write the installed calendar to a file as a draft")
    p.add_argument("--source", required=True, help="clone of the source repository")
    p.add_argument("--out", required=True, help="file to write")
    p = sub.add_parser("routine", help="print the cloud routine configuration")
    p.add_argument("--source", required=True, help="clone of the source repository")

    args = parser.parse_args(argv)
    handlers = {"inspect": cmd_inspect, "plan": cmd_plan, "install": cmd_install, "run": cmd_run,
                "status": cmd_status, "export": cmd_export, "routine": cmd_routine}
    try:
        return handlers[args.command](args)
    except Fail as err:
        emit("error", message=str(err))
    except Exception as err:  # noqa: BLE001 - the last stdout line must always be a JSON result
        emit("error", message=internal_error(err))
    return 1


if __name__ == "__main__":
    sys.exit(main())
