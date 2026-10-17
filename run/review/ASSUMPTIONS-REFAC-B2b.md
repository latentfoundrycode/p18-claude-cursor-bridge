# ASSUMPTIONS-REFAC-B2b

No builder ran on this branch: no `Assumed, not verified` list exists. The supervisor's own assumption: importing a test module from another (`from test_open_list import table`) is how the suite already shares helpers (test_workflows_line_check.py imports from test_conformance_check.py), and pytest collects no test function through such an import (checked: the collected set is identical).
