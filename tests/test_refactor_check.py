"""refactor-check.py (release A4, R17): the test files of Go, Java and C# count as tests, so an edit to
one is not a pure refactoring. Scratch repository."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "refactor-check.py")
ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid")


def git(repo, *args):
    p = subprocess.run(["git"] + list(args), cwd=str(repo), capture_output=True, text=True, env=ENV)
    assert p.returncode == 0, p.stderr


def test_go_java_and_csharp_test_files_count_as_tests(tmp_path):
    r = tmp_path / "ws"
    (r / "pkg").mkdir(parents=True)
    files = {"pkg/x_test.go": "package pkg\n", "pkg/FooTest.java": "class FooTest {}\n", "pkg/BarTests.cs": "class BarTests {}\n", "pkg/main.go": "package pkg\n"}
    for f, t in files.items():
        (r / f).write_text(t, encoding="utf-8")
    git(r, "init", "-q", "-b", "main")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "base")
    for f in files:
        (r / f).write_text(files[f] + "// changed\n", encoding="utf-8")
    p = subprocess.run([sys.executable, PROG, "HEAD"], cwd=str(r), capture_output=True, text=True, env=ENV)
    out = p.stdout
    assert p.returncode == 1 and "IMPURE" in out, out
    for f in ("pkg/x_test.go", "pkg/FooTest.java", "pkg/BarTests.cs"):
        assert f in out.split("test file(s) changed:")[1].split("\n")[0], "%s passed as a pure refactoring (R17): %s" % (f, out)
    assert "pkg/main.go" not in out.split("test file(s) changed:")[1].split("\n")[0]
