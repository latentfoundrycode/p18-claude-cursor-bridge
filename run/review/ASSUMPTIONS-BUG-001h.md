# ASSUMPTIONS-BUG-001h

No builder run on this branch: the diff is the supervisor's test and records, so there is no `Assumed, not verified` list.

The supervisor's own assumption, as an extra place to look:
- GitHub runs workflows only from files directly under `.github/workflows/` (not from subfolders), so requiring that folder's entries to be exactly `tests.yml` covers every workflow the repository can run → test (the new test lists every entry, files and folders alike, so a subfolder also fails it).
