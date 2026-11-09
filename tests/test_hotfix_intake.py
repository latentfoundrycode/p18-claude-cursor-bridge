"""Hotfix 2026.11.09a (HOTFIX-003): the software's features and behaviour are asked as a conversation, never as
guessed options; a project's parameters and the gates keep the question form (the owner's rule of 2026-11-08;
docs/INVENTORY.md, Decisions, row of 2026-11-08; docs/DESIGN.md, "Change: the intake hotfix").

enforces: docs/DESIGN.md, Change: the intake hotfix, "What changes - the text by home" (one test per row, each pinning
its sentence in its home) and "Non-goals" (the places that keep the form, pinned as invariants).

KP-052: the one non-ASCII character these pins need, the em dash, is built with chr(), never typed."""
import os

from phase_modules import flat, read, rule, section

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIDGE = os.path.join(ROOT, "bridge")
CORE = os.path.join(BRIDGE, "commands", "supervisor.md")
PHASES = os.path.join(BRIDGE, "cursor-bridge", "workflow", "phases")
INTAKE = os.path.join(PHASES, "intake.md")
MOCKUPS = os.path.join(PHASES, "interface", "mockups.md")
CHANGE_CYCLE = os.path.join(PHASES, "change-cycle.md")
DESIGN = os.path.join(PHASES, "design.md")
INTERFACE = os.path.join(PHASES, "interface.md")
RUN_PARAMETERS = os.path.join(PHASES, "run-parameters.md")
PITFALLS = os.path.join(BRIDGE, "cursor-bridge", "Known-Pitfalls.md")
DASH = chr(0x2014)


def item(text, number, label):
    """A numbered item of a procedure list, from `<number>. **<label>**` to the next item."""
    start = text.index("\n%d. **%s**" % (number, label))
    end = text.index("\n%d. **" % (number + 1), start)
    return flat(text[start:end])


# --- intake.md, "The procedure": the sorting of questions

def test_hotfix003_intake_sorts_a_question_by_what_it_asks():
    procedure = flat(section(read(INTAKE), "The procedure", 3))
    assert ("Ask in batches, not one at a time, and sort each question by what it asks, never by whether you could "
            "guess its answers.") in procedure


def test_hotfix003_intake_a_parameter_question_may_take_the_question_form():
    procedure = flat(section(read(INTAKE), "The procedure", 3))
    assert ("**A question about the project's parameters** " + DASH + " a fact the bridge needs in a fixed form: the "
            "kind (`private` or `commercial`), the platform and runtime context, the delivery kind, a part's product "
            "type or sub-type where the owner must choose between the open list's definitions, the figure of a budget "
            "or a limit " + DASH + " may be asked in the question form (`AskUserQuestion`, the default or the "
            "recommended answer first), so that answering it is one choice.") in procedure


def test_hotfix003_intake_a_question_about_the_software_is_a_conversation():
    procedure = flat(section(read(INTAKE), "The procedure", 3))
    assert ("**A question about the software itself** " + DASH + " what it does, which features it has and how each "
            "behaves, who uses it and how, what happens in a case the description leaves open; the gaps, contradictions "
            "and better options above " + DASH + " is a conversation: numbered questions in prose, batched, each "
            "answered in the owner's own words, your follow-ups building on their answers; never a list of answers you "
            "guessed for the owner to tick, since a guessed option frames the feature before the owner has described "
            "it, and their answer then measures your guess, not their intent (the owner's rule of 2026-11-08, after a "
            "supervisor offered guessed feature options at intake).") in procedure


def test_hotfix003_intake_the_stop_rule_stays_and_the_old_sort_is_gone():
    procedure = flat(section(read(INTAKE), "The procedure", 3))
    assert ("Stop asking when the remaining unknowns are ones a competent implementer could decide without you.") in procedure
    assert "where the answer is a choice among options" not in procedure
    assert "use plain prose where it is open-ended" not in procedure


# --- mockups.md, "The procedure": the iteration

def test_hotfix003_the_mockup_iteration_is_a_conversation():
    procedure = flat(section(read(MOCKUPS), "The procedure", 3))
    assert ("Iterate with the user until they are satisfied " + DASH + " expect change requests; this is where UI "
            "decisions are cheap to make. The iteration is a conversation, as intake's questions about the software "
            "are (`intake.md`, the sorting of questions): ask what they would change and why, numbered where several "
            "points are open, answered in their own words, your follow-ups building on the answers; variants of a "
            "screen you guessed are never put as options to tick. The question form is kept for the gate's approval "
            "(`interface.md`, \"The gate\") and for a parameter in a fixed form that a screen turns on (the target "
            "platform, say).") in procedure
    assert "for discrete choices" not in procedure


# --- change-cycle.md, item 1: the change's intake in the same form

def test_hotfix003_a_change_is_interrogated_in_the_same_form():
    text = read(CHANGE_CYCLE)
    assert ("Interrogate the request the same way as a new project's description " + DASH + " gaps, contradictions, "
            "better options, and in the same form (intake.md's sorting of questions: the change's features and "
            "behaviour as a conversation in the owner's own words, a parameter in the question form) " + DASH + " but "
            "only about the delta") in item(text, 1, "Intake of the change")


# --- the core's rule 12: the form's bound

def test_hotfix003_rule_12_bounds_the_question_form():
    text = rule(12)
    assert ("A decision the owner owns is asked in the question form (the `AskUserQuestion` tool, the recommended "
            "option first), so that answering it is one choice.") in text
    assert ("The form is for a decision between answers that exist before the owner speaks " + DASH + " a gate, a run "
            "parameter, a project parameter at intake, an item that costs money, a reading of an approved requirement; "
            "what the software should do and how its features behave is asked as a conversation in the owner's own "
            "words, never as options you guessed (intake.md's sorting of questions; the owner's rule of 2026-11-08).") in text


# --- Known-Pitfalls: KP-075

def test_hotfix003_kp075_names_the_pitfall_and_its_sign():
    text = read(PITFALLS)
    assert "### KP-075 " + DASH + " A question's sort left to the supervisor licensed guessed feature options at intake" in text
    entry = text[text.index("### KP-075"):]
    assert "**Correction (2026.11.09a):**" in entry
    assert "The sign:" in entry


# --- the places that keep the form (invariants of the hotfix's non-goals)

def test_hotfix003_the_kind_the_gates_and_the_run_parameters_keep_the_form():
    assert ("it the owner is asked is the kind, as its own question in the question form, `private` named") in read(INTAKE)
    assert ("each asked as a question of its own in the app's question form") in flat(read(DESIGN))
    assert ("each part's traits are a decision of their own, asked in the question form") in flat(read(DESIGN))
    assert "question form" in flat(section(read(INTERFACE), "The gate", 3))
    assert ("each as a question of its own in the app's question form** (`AskUserQuestion`,") in flat(read(RUN_PARAMETERS))
