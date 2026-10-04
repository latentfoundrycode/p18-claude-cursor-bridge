"""Claude Code's documented Bash permission matching, for the bridge's tests.

Rules (code.claude.com/docs/en/permissions, checked 2026-10-04):
- `Bash(pattern)`; a `*` matches any text, including spaces, anywhere in the pattern;
- `:*` at the end of a pattern is the same as a trailing ` *`;
- a pattern with no `*` matches one exact command;
- a compound command (`a && b`, `a; b`, `a | b`) is matched part by part;
- deny rules are evaluated before allow rules, in every permission mode.
A wrapper changes what is matched: `timeout 5 git push` does not match `Bash(git push *)`.
"""
import re


def pattern_to_regex(pattern):
    tail = ""
    if pattern.endswith(":*") or pattern.endswith(" *"):
        pattern, tail = pattern[:-2], "( .*)?"       # the prefix form also matches the bare command
    parts = pattern.split("*")
    return "^" + ".*".join(re.escape(p) for p in parts) + tail + "$"


def rule_matches(rule, command):
    if not rule.startswith("Bash(") or not rule.endswith(")"):
        return False
    pattern = rule[len("Bash("):-1]
    return re.match(pattern_to_regex(pattern), command.strip(), re.S) is not None


def split_compound(command):
    """Split on &&, ||, ;, | outside quotes. Good enough for the bridge's own commands."""
    parts, buf, quote, i = [], "", None, 0
    while i < len(command):
        c = command[i]
        if quote:
            buf += c
            if c == quote:
                quote = None
        elif c in ("'", '"'):
            quote = c
            buf += c
        elif command.startswith("&&", i) or command.startswith("||", i):
            parts.append(buf); buf = ""; i += 1
        elif c in (";", "|"):
            parts.append(buf); buf = ""
        else:
            buf += c
        i += 1
    parts.append(buf)
    return [p.strip() for p in parts if p.strip()]


def decide(command, allow, deny):
    """Return ('deny'|'allow'|'ask', part) for a command under the given rule lists."""
    for part in split_compound(command):
        if any(rule_matches(r, part) for r in deny):
            return "deny", part
    for part in split_compound(command):
        if not any(rule_matches(r, part) for r in allow):
            return "ask", part
    return "allow", command
