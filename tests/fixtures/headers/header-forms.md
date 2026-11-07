---
record: build-plan
header: 1
nothing:
quoted: "PR #135"
blank: ""
escapes: "say \"hi\" c:\\x"
number: 42
zero: 0
quoted_word: "yes"
quoted_date: "2026-11-04"
quoted_path: "bridge/cursor-bridge/bridge_env.py"
on_true: true
on_false: false
on_null: null
word: v1.2_x-y
upper: TASK-046
flow: [a, "b c", 3, true, null, ""]
flow_empty: []
block:
  - one
  - "two words"
  - 7
nested:
  inner:
    deep: x
  other: [p, q]
# a comment line

items:
  - id: TASK-001
    scope: [a, b]
    inner:
      - k: 1
      - k: 2
  - id: TASK-002
    scope: []
after: word # a trailing comment
last: "text" # another
---
# forms fixture
