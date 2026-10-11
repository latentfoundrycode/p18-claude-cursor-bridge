"""conformance-check.py (release A4, the A1b third pass T1 and the A2 field): the adapters floor counts
a source file as an adapter of a listed provider only when the provider's word is in a host or URL
string or in an upper-case key name, never in any string of code (reAngle's health and weights
modules only mentioned modal in a log string)."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_conformance_check import make_workspace, run, verdict  # noqa: E402


def test_a_provider_word_counts_only_in_a_host_or_a_key_name(tmp_path):
    make_workspace(tmp_path)
    inv = (tmp_path / "docs" / "INVENTORY.md").read_text(encoding="utf-8")
    (tmp_path / "docs" / "INVENTORY.md").write_text(inv.replace("| CI | 2026-09-01 |\n", "| CI | 2026-09-01 |\n"
                                                     + "| MODAL_TOKEN_ID / MODAL_TOKEN_SECRET | secret | key file; limit $50/month, set 2026-09-20 | app | 2026-09-20 |\n"), encoding="utf-8")
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "health.py").write_text('import httpx2\n\nSTATUS = "modal worker alive"   # a word in a string, not an adapter\n\ndef ping():\n    return httpx2.get("http://127.0.0.1:8000/health")\n', encoding="utf-8")
    (tmp_path / "app" / "weights.py").write_text('import os\nimport httpx2\n\nTOKEN = os.environ["MODAL_TOKEN_ID"]\n\ndef fetch(u):\n    return httpx2.get(u)\n', encoding="utf-8")
    (tmp_path / "app" / "run.py").write_text('import httpx2\n\nURL = "https://api.modal.com/v1/apps"\n\ndef start():\n    return httpx2.post(URL)\n', encoding="utf-8")
    rc, out = run(tmp_path)
    kind, detail = verdict(out, "Adapters tested against recorded replies")
    assert kind == "MISSING" and "weights" in detail and "run" in detail and "health" not in detail, "a provider word in a plain string is not an adapter; a host or a key name is: " + out
