#!/usr/bin/env python3
"""completion-check: is every specified requirement planned, built and tested - or deferred by
the owner - and does the shipped code contain no stand-ins presented as features?

  python completion-check.py [--mode plan|done] [--requirements docs/REQUIREMENTS.md] [--only R-001,R-002]

Run from the Workspace root. Deterministic; reads only. ASCII output.

docs/REQUIREMENTS.md holds one table (see supervisor.md, "The requirements register"):
  | ID | Requirement | Source | Status | Evidence |
  ID      R-001, R-002, ...                 (never reused, never renumbered)
  Status  planned | built | deferred - owner YYYY-MM-DD | dropped - owner YYYY-MM-DD

--mode plan  (plan gate, every stage close)
  REGISTER    the register exists, rows are well-formed, IDs unique.
  UNPLANNED   a `planned` requirement that no increment's `Satisfies:` field names (a mention
              in prose is not a plan; release A4). A `built` row needs evidence, not a plan
              increment: the plan that built it may be gone (the video factory's older plans).
  UNAPPROVED  a deferred/dropped row without "owner" and a date.
  NO EVIDENCE a `built` requirement whose Evidence cell names no test file (release A4: a
              release was declared complete while features returned empty data). A requirement
              an instruction text satisfies may name the text instead (release S), each entry
              `text: <file>.md :: <heading> (#<pull request>)`: the file must exist, hold that
              heading, and the pull request's squash stand on origin/main (a note on a branch
              of unmerged work and in a shallow clone, a failure on merged work). Never for a
              row whose sentence names a program (`name.py`): a test proves what a program does.
  stand-ins are listed as notes (mid-build a later stage may legitimately be pending).
--mode done  (project end, and the start of every change cycle) - everything above, plus:
  NOT BUILT   a requirement still `planned`.
  NO EVIDENCE also a `built` requirement whose ID appears in no tracked test file. Tests carry
              the requirement ID (a comment, docstring, or test name) - that is the trace. A row
              whose text entries all hold needs no test that names it.
--only R-001,R-002  limits every check to those IDs (an older project brought under the
              register part by part, or one stage's requirements; release A4).
  STAND-IN    shipped (non-test) code shows a user-visible stand-in, in any of these forms:
              arrive or arrives, then in a later stage, version, release or update; the word
              coming directly followed by soon; not and yet before implemented, available,
              built or supported; not, implemented and yet in a row; to be and implemented
              in a row; under and construction in a row; an identifier ending in Placeholder
              plus one of View, Page, Screen, Tab, Panel or Section; a call of the todo or
              unimplemented macro (Rust), with or without arguments.
              Allowed only on a line that names the ID of an owner-deferred requirement.
Notes never fail: TODO/FIXME counts and NotImplementedError sites (often legitimate
abstract methods) in shipped code.
Exit 0 = OK, 1 = at least one failure.
"""
import argparse
import glob
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bridge_env

NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

ID_RX = re.compile(r"\bR-\d{3,}\b")
STATUS_OK = re.compile(r"^(planned|built|(deferred|dropped)\b.*)$", re.I)
OWNER_DATED = re.compile(r"\bowner\b.*\d{4}-\d{2}-\d{2}", re.I)
STANDIN_RX = re.compile(
    r"arrives?\s+in\s+a\s+later\s+(stage|version|release|update)"
    r"|coming\s+soon"
    r"|not\s+yet\s+(implemented|available|built|supported)"
    r"|\bnot\s+implemented\s+yet\b"
    r"|under\s+construction"
    r"|to\s+be\s+implemented"
    r"|\b\w*Placeholder(View|Page|Screen|Tab|Panel|Section)\b"
    r"|\btodo!\s*\(|\bunimplemented!\s*\(", re.I)
NOTE_RX = re.compile(r"\b(TODO|FIXME|XXX|HACK)\b|NotImplementedError")
CODE_EXT = {".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".vue", ".svelte", ".html",
            ".htm", ".css", ".scss", ".cs", ".rs", ".go", ".java", ".kt", ".swift", ".dart",
            ".rb", ".php", ".ps1", ".xaml", ".qml"}
TEST_PATH = re.compile(r"(^|/)(tests?|__tests__|spec|specs|e2e|testing|fixtures)(/|$)"
                       r"|(^|/)test_[^/]*$|_test\.[a-z]+$|\.(test|spec)\.[a-z]+$", re.I)
# Text evidence (release S): a requirement an instruction text satisfies names where the text
# stands and the pull request that merged it, `text: <file>.md :: <heading> (#<n>)`.
TEXT_EVIDENCE = re.compile(r"\btext:\s*`?([^\s`|;]+\.md)`?\s*::\s*(.+?)\s*\(#(\d+)\)")
PROGRAM_NAME = re.compile(r"(?<![\w/.-])[\w-]+\.(?:py|ps1|sh|js|mjs|cjs|ts|tsx|jsx|cs|rs|go|java|kt|swift|rb|php)\b")
HEADING_RX = re.compile(r"^#{1,6}[ \t]+(.*?)[ \t]*#*[ \t]*$")
SKIP_PATH = re.compile(r"(^|/)(docs|\.claude|\.cursor|\.github|node_modules|vendor|third_party|"
                       r"dist|build|bench|benchmarks|scripts/dev)(/|$)", re.I)


def read(path):
    return bridge_env.read_record_text(path)


def tracked():
    p = subprocess.run(["git", "ls-files", "-z"], capture_output=True, creationflags=NO_WINDOW)
    if p.returncode != 0:
        return None
    return [f for f in p.stdout.decode("utf-8", "replace").split("\0") if f]


def parse_register(text):
    return bridge_env.parse_register(text)


def git_out(*args):
    try:
        p = subprocess.run(("git",) + args, capture_output=True, creationflags=NO_WINDOW, timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return None, ""
    return p.returncode, p.stdout.decode("utf-8", "replace")


class Merged(object):
    """Which pull requests' squash commits stand on origin/main, asked of git once. `state` is
    "strict" where HEAD is merged work (a missing squash is a failure), "ahead" where HEAD holds
    commits origin/main lacks (the cell may name its own pull request: a note), or the reason the
    question cannot be answered here (a note)."""

    def __init__(self):
        self.numbers, self.state = None, None

    def load(self):
        if self.state is not None:
            return
        code, out = git_out("rev-parse", "--is-shallow-repository")
        if code != 0:
            self.state = "not a git repository"
        elif out.strip() == "true":
            self.state = "a shallow clone holds no history"
        else:
            code, out = git_out("log", "origin/main", "--format=%s")
            if code != 0:
                self.state = "origin/main is not known here"
            else:
                self.numbers = set(re.findall(r"\(#(\d+)\)[ \t]*$", out, re.M))
                self.state = "strict" if git_out("merge-base", "--is-ancestor", "HEAD", "origin/main")[0] == 0 else "ahead"


def text_evidence(rid, requirement, cell, merged):
    """(valid entries, failures, notes) of a row's `text:` entries. An entry is valid when its
    file exists under the Workspace, holds the heading, and its pull request's squash is on
    origin/main; never for a row whose sentence names a program, which a test proves."""
    entries = TEXT_EVIDENCE.findall(cell or "")
    fails, notes, valid = [], [], 0
    if not entries:
        return 0, fails, notes
    program = PROGRAM_NAME.search(requirement or "")
    if program:
        fails.append("NO EVIDENCE: %s names a program (%s): a text entry is no evidence of what a program does, name its test" % (rid, program.group(0)))
        return 0, fails, notes
    for path, heading, number in entries:
        shown = path.replace("\\", "/")
        if os.path.isabs(path) or ".." in shown.split("/") or not os.path.isfile(path):
            fails.append("NO EVIDENCE: %s names the text %s, which is no file of this Workspace" % (rid, shown))
            continue
        try:
            lines = read(path).splitlines()
        except OSError:
            lines = []
        if not any(m and m.group(1) == heading for m in (HEADING_RX.match(line) for line in lines)):
            fails.append("NO EVIDENCE: %s names the heading '%s', which %s does not hold" % (rid, heading[:80], shown))
            continue
        merged.load()
        if merged.numbers is None:
            notes.append("%s: pull request #%s not looked up (%s)" % (rid, number, merged.state))
        elif number not in merged.numbers:
            if merged.state == "strict":
                fails.append("NO EVIDENCE: %s names pull request #%s, whose squash is not on origin/main" % (rid, number))
                continue
            notes.append("%s: pull request #%s is not on origin/main yet (this branch is unmerged work; checked again once it is merged)" % (rid, number))
        valid += 1
    return valid, fails, notes


def build_parser():
    ap = argparse.ArgumentParser(description="Check requirements coverage and shipped stand-ins.")
    ap.add_argument("--mode", choices=("plan", "done"), default="done")
    ap.add_argument("--requirements", default="docs/REQUIREMENTS.md")
    ap.add_argument("--only", default="", help="comma-separated requirement IDs; the run is limited to them")
    return ap


def main():
    a = build_parser().parse_args()
    only = set(ID_RX.findall(a.only))
    fails, notes = [], []
    done = a.mode == "done"

    reqs, evidence = {}, {}
    if not os.path.exists(a.requirements):
        fails.append("REGISTER: %s does not exist" % a.requirements)
    else:
        reg_text = read(a.requirements)
        shown_reg = a.requirements.replace("\\", "/")
        reg_header = None
        reg_body = reg_text
        try:
            reg_header, reg_body = bridge_env.read_header(reg_text)
        except bridge_env.HeaderError as err:
            print("HEADER MALFORMED: %s:%d %s" % (shown_reg, err.line, str(err)))
            print("RESULT: not checked")
            return 2
        if reg_header is not None:
            findings = bridge_env.check_header("requirements", reg_header)
            if findings:
                print("HEADER MALFORMED: %s:1 %s" % (shown_reg, "; ".join(findings)))
                print("RESULT: not checked")
                return 2
            fallback = bridge_env.register_fallback(reg_body or "")
            for key in bridge_env.header_agrees("requirements", reg_header, fallback):
                fails.append("HEADER DISAGREES: %s" % key)
            columns = list(reg_header.get("columns") or [])
            roles = reg_header.get("roles") or {}
            role_cols = set(roles.values())
            evidence_col = roles.get("evidence")
            _hl, rows = parse_register(reg_body or "")
            for r in rows:
                if len(r) < len(columns):
                    fails.append("REGISTER: malformed row: %s" % " | ".join(r)[:120])
                    continue
                if any(
                        not r[i]
                        for i, col in enumerate(columns)
                        if col != evidence_col
                ):
                    fails.append("REGISTER: malformed row: %s" % " | ".join(r)[:120])
                    continue
                rid = bridge_env.register_row_role(r, columns, roles, "id").strip("`* ")
                if not re.fullmatch(r"R-\d{3,}", rid):
                    fails.append("REGISTER: bad ID '%s' (use R-001 ...)" % rid)
                    continue
                if rid in reqs:
                    fails.append("REGISTER: duplicate ID %s" % rid)
                    continue
                status = bridge_env.register_row_role(r, columns, roles, "status").strip("`* ")
                if not STATUS_OK.match(status):
                    fails.append("REGISTER: %s has status '%s' (planned | built | deferred - owner <date> | dropped - owner <date>)" % (rid, status[:40]))
                    continue
                kind = status.split()[0].lower()
                if kind in ("deferred", "dropped") and not OWNER_DATED.search(status):
                    fails.append("UNAPPROVED: %s is %s without the owner's approval and a date (%s)" % (rid, kind, status[:60]))
                req_text = ""
                for col in columns:
                    if col not in role_cols:
                        idx = columns.index(col)
                        req_text = r[idx] if idx < len(r) else ""
                        break
                reqs[rid] = (kind, req_text)
                evidence[rid] = bridge_env.register_row_role(r, columns, roles, "evidence")
        else:
            header, rows = parse_register(reg_text)
            want = ["id", "requirement", "source", "status", "evidence"]
            if header is None or [h.split()[0] if h else "" for h in header][:5] != want:
                fails.append("REGISTER: header must be | ID | Requirement | Source | Status | Evidence |")
            for r in rows:
                if len(r) < 5 or not all(r[:4]):
                    fails.append("REGISTER: malformed row: %s" % " | ".join(r)[:120])
                    continue
                rid = r[0].strip("`* ")
                if not re.fullmatch(r"R-\d{3,}", rid):
                    fails.append("REGISTER: bad ID '%s' (use R-001 ...)" % rid)
                    continue
                if rid in reqs:
                    fails.append("REGISTER: duplicate ID %s" % rid)
                    continue
                status = r[3].strip("`* ")
                if not STATUS_OK.match(status):
                    fails.append("REGISTER: %s has status '%s' (planned | built | deferred - owner <date> | dropped - owner <date>)" % (rid, status[:40]))
                    continue
                kind = status.split()[0].lower()
                if kind in ("deferred", "dropped") and not OWNER_DATED.search(status):
                    fails.append("UNAPPROVED: %s is %s without the owner's approval and a date (%s)" % (rid, kind, status[:60]))
                reqs[rid] = (kind, r[1])
                evidence[rid] = r[4] if len(r) > 4 else ""
        if not reqs and not any(f.startswith("REGISTER") for f in fails):
            fails.append("REGISTER: %s has no requirement rows" % a.requirements)
        if only:
            total = len(reqs)
            reqs = {k: v for k, v in reqs.items() if k in only}
            notes.append("limited to %d of %d requirements (--only %s)" % (len(reqs), total, ", ".join(sorted(only))))

    plans = sorted(glob.glob("docs/BUILD_PLAN*.md"))
    if not plans:
        notes.append("no docs/BUILD_PLAN*.md found - plan coverage not checked")
    else:
        satisfied = set()
        header_union = set()
        has_build_plan_header = False
        headed_texts = []
        for p in plans:
            text = read(p)
            fatal, _, hdr = bridge_env.plan_header_findings(p, text, None)
            if fatal:
                print(fatal[0])
                return 2
            if hdr is not None:
                has_build_plan_header = True
                headed_texts.append(text)
                for st in hdr.get("stages") or []:
                    for inc in st.get("increments") or []:
                        for rid in inc.get("satisfies") or []:
                            satisfied.add(rid)
                            header_union.add(rid)
            else:
                body = bridge_env.plan_body(text)
                satisfied.update(bridge_env.plan_collect_satisfies_ids(body))
        if has_build_plan_header:
            disagree = False
            for text in headed_texts:
                for rid in bridge_env.plan_r_ids_outside_headers(text):
                    if rid not in header_union:
                        disagree = True
                        break
                if disagree:
                    break
            if disagree:
                fails.append("HEADER DISAGREES: satisfies")
        for rid, (kind, text) in sorted(reqs.items()):
            if kind == "planned" and rid not in satisfied:
                fails.append("UNPLANNED: %s (%s) is in no increment's Satisfies: field" % (rid, text[:70]))
    merged, by_text = Merged(), set()
    for rid, (kind, text) in sorted(reqs.items()):
        if kind != "built":
            continue
        valid, text_fails, text_notes = text_evidence(rid, text, evidence.get(rid, ""), merged)
        fails.extend(text_fails)
        notes.extend(text_notes)
        if valid and not text_fails:
            by_text.add(rid)
        cell = TEXT_EVIDENCE.sub(" ", evidence.get(rid, ""))    # a text's own path is no test file, whatever folder holds it
        if not valid and not text_fails and not any(TEST_PATH.search(tok.strip("`*, ").replace("\\", "/")) for tok in cell.split()):
            fails.append("NO EVIDENCE: %s (%s) is marked built but its Evidence names no test file" % (rid, text[:60]))

    files = tracked()
    if files is None:
        notes.append("not a git repository - evidence and stand-ins not checked")
        files = []
    tests = [f for f in files if TEST_PATH.search(f.replace("\\", "/"))]
    shipped = [f for f in files if os.path.splitext(f)[1].lower() in CODE_EXT
               and not TEST_PATH.search(f.replace("\\", "/")) and not SKIP_PATH.search(f.replace("\\", "/"))]

    # completion
    if done:
        test_ids = set()
        for f in tests:
            try:
                test_ids.update(ID_RX.findall(read(f)))
            except OSError:
                pass
        for rid, (kind, text) in sorted(reqs.items()):
            if kind == "planned":
                fails.append("NOT BUILT: %s (%s) is still planned" % (rid, text[:70]))
            elif kind == "built" and rid not in test_ids and rid not in by_text:
                fails.append("NO EVIDENCE: %s (%s) is marked built but no tracked test names it" % (rid, text[:60]))

    # stand-ins
    deferred_ids = {rid for rid, (kind, _) in reqs.items() if kind in ("deferred", "dropped")}
    standins, note_count, nie = [], 0, 0
    for f in shipped:
        try:
            text = read(f)
        except OSError:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            if STANDIN_RX.search(line):
                if set(ID_RX.findall(line)) & deferred_ids:
                    continue
                standins.append("%s:%d: %s" % (f.replace("\\", "/"), n, line.strip()[:100]))
            elif NOTE_RX.search(line):
                if "NotImplementedError" in line:
                    nie += 1
                else:
                    note_count += 1
    for s in standins[:40]:
        (fails if done else notes).append(("STAND-IN: " if done else "stand-in (fails at done): ") + s)
    if len(standins) > 40:
        (fails if done else notes).append("... and %d more stand-ins" % (len(standins) - 40))
    if note_count or nie:
        notes.append("shipped code: %d TODO/FIXME/XXX/HACK markers, %d NotImplementedError sites (review, not a failure)" % (note_count, nie))

    counts = {}
    for kind, _ in reqs.values():
        counts[kind] = counts.get(kind, 0) + 1
    notes.insert(0, "mode %s; requirements: %s" % (a.mode, ", ".join("%d %s" % (v, k) for k, v in sorted(counts.items())) or "none"))
    for n in notes:
        print("note: " + n)
    for f in fails:
        print(f)
    print("RESULT: %s" % ("OK" if not fails else "%d problem(s)" % len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):      # never crash on a character the console lacks
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(errors="backslashreplace")
    sys.exit(main())
