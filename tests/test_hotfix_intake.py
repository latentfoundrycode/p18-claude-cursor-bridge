"""Hotfix 2026.11.09a (HOTFIX-003): the software's features and behaviour are asked as a conversation, never as
guessed options; a project's parameters and the gates keep the question form (the owner's rule of 2026-11-08;
docs/INVENTORY.md, Decisions, row of 2026-11-08; docs/DESIGN.md, "Change: the intake hotfix").

enforces: docs/DESIGN.md, Change: the intake hotfix, "What changes - the text by home" (one test per row, each pinning
its sentence in its home) and "Non-goals" (the places that keep the form, pinned as invariants, one assert per place).

KP-052: the one non-ASCII character these pins need, the em dash, is built with chr(), never typed."""
import os

from phase_modules import flat, read, rule, section

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIDGE = os.path.join(ROOT, "bridge")
CORE = os.path.join(BRIDGE, "commands", "supervisor.md")
EVALUATE = os.path.join(BRIDGE, "commands", "evaluate-reports.md")
SKILL = os.path.join(BRIDGE, "skills", "explain-for-decision", "SKILL.md")
PHASES = os.path.join(BRIDGE, "cursor-bridge", "workflow", "phases")
INTAKE = os.path.join(PHASES, "intake.md")
MOCKUPS = os.path.join(PHASES, "interface", "mockups.md")
CHANGE_CYCLE = os.path.join(PHASES, "change-cycle.md")
DESIGN = os.path.join(PHASES, "design.md")
INTERFACE = os.path.join(PHASES, "interface.md")
RUN_PARAMETERS = os.path.join(PHASES, "run-parameters.md")
CONFIGURATION = os.path.join(PHASES, "configuration.md")
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
    assert ("**A question about the project's parameters** " + DASH + " a fact the bridge's own procedures consume in "
            "a fixed form, one of this closed list: the kind (`private` or `commercial`), the platform and runtime "
            "context, the delivery kind, the confirmation of a part's product type or sub-type as you classified it "
            "from their answers (each definition in one line), the figure of a budget or a limit " + DASH + " may be "
            "asked in the question form (`AskUserQuestion`, the default or the recommended answer first), so that "
            "answering it is one choice.") in procedure


def test_hotfix003_intake_a_question_about_the_software_is_a_conversation():
    procedure = flat(section(read(INTAKE), "The procedure", 3))
    assert ("**A question about the software itself** " + DASH + " what it does, which features it has and how each "
            "behaves, who uses it and how, what happens in a case the description leaves open; the gaps, contradictions "
            "and better options above " + DASH + " is a conversation: numbered questions in prose, batched, each "
            "answered in the owner's own words, your follow-ups building on their answers; never a list of answers you "
            "guessed for the owner to tick (the owner's rule of 2026-11-08, who found such options too rigid when a "
            "supervisor offered them at intake).") in procedure


def test_hotfix003_intake_a_question_that_is_both_is_a_conversation():
    """The tie-break (round 1, plan-critic S1 and Review B's first Blocking): a fact about the software that fixes a
    parameter is a conversation, and a short answer never makes a question a parameter."""
    procedure = flat(section(read(INTAKE), "The procedure", 3))
    assert ("**A question that is both** " + DASH + " a fact about the software that fixes a parameter, the open list's "
            "deciding questions among them (does it keep data for its users; does its user meet it in a browser) " + DASH
            + " is asked as a conversation: a conversation carries a parameter's answer, the form cannot carry a "
            "description. That a feature's answer could be written in a fixed form never makes it a parameter: a "
            "parameter is one the list above names, not a question whose answers are short.") in procedure


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
            "(`interface.md`, \"The gate\") and for a parameter in a fixed form that a screen turns on (one of "
            "intake.md's closed list: the smallest screen width the design must fit, a figure); how a screen should "
            "behave is never such a parameter, however short its answer.") in procedure
    assert "for discrete choices" not in procedure


# --- change-cycle.md, item 1: the change's intake in the same form

def test_hotfix003_a_change_is_interrogated_in_the_same_form():
    text = read(CHANGE_CYCLE)
    assert ("Interrogate the request the same way as a new project's description " + DASH + " gaps, contradictions, "
            "better options, and in the same form (intake.md's sorting of questions: the change's features and "
            "behaviour as a conversation in the owner's own words, a parameter in the question form) " + DASH + " but "
            "only about the delta") in item(text, 1, "Intake of the change")


# --- design.md, "The gate": a question before the gate

def test_hotfix003_a_question_before_the_design_gate_is_a_conversation():
    gate = flat(section(read(DESIGN), "The gate", 3))
    assert ("A question the design must put to the owner before the gate about what the software does or how a "
            "feature behaves " + DASH + " a case the description left open that the design has to settle, an open "
            "question the critique raised " + DASH + " is asked as intake.md's sorting of questions says: a "
            "conversation in their own words, never options you guessed. The gate's decisions above keep the question "
            "form, since each approves something the design has already written down.") in gate


# --- the core: the escalation passage, its skill summary, the reporting rule and rule 12's bound

def test_hotfix003_an_escalation_about_behaviour_is_a_conversation():
    passage = flat(section(read(CORE), "Escalate to the user when", 2))
    assert ("When you do escalate, lead with the decision, recommend one where there are answers to choose between, "
            "then wait. The options are put only where the decision is one between answers that exist before the owner "
            "speaks (rule 12's bound, among them scope, a consequence they bear, an item that costs money, an "
            "irreversible step, a reading of an approved requirement, a change to what \"correct\" means); a decision "
            "about what the software should do or how a feature behaves, which the owner has not yet described, is "
            "asked as a conversation in the owner's own words, never as options you guessed and with no recommendation "
            "before their answer, mid-build as at intake (intake.md's sorting of questions): your own view of it, where "
            "you have one, follows their answer as a follow-up, as intake's better-options bucket does.") in passage
    assert "lead with the decision and the options" not in passage


def test_hotfix003_the_recommendation_comes_only_where_answers_exist():
    """Round 2 (plan-critic S2, Review B's first Should fix): the skill summary in the escalation section and the
    reporting rule's first bullet bound the recommendation as the passage and the brief do."""
    passage = flat(section(read(CORE), "Escalate to the user when", 2))
    assert ("the options in the user's currency and your recommendation, where the answers exist before they speak; "
            "what you decide regardless") in passage
    reporting = flat(section(read(CORE), "Reporting to the user", 2))
    assert ("a product-behaviour or scope call " + DASH + " stated as one question, with your recommendation where the "
            "answers exist before they speak (a behaviour they have not yet described is asked in prose, rule 12's "
            "bound); or, if nothing is needed,") in reporting


def test_hotfix003_rule_12_bounds_the_question_form():
    text = rule(12)
    assert ("A decision the owner owns is asked in the question form (the `AskUserQuestion` tool, the recommended "
            "option first), so that answering it is one choice.") in text
    assert ("The form is for a decision between answers that exist before the owner speaks, or a fact the bridge needs "
            "in a fixed form " + DASH + " a gate, a run parameter, a project parameter, a figure the owner names, a scope "
            "question (deferring or dropping a requirement), a consequence they bear (rule 56), an item that costs "
            "money, an irreversible step, a reading of an approved requirement, a change to what \"correct\" means; a "
            "decision about what the software should do or how a feature behaves is the owner's too, but its answer is "
            "theirs to describe, so it is asked as a conversation in their own words, never as options you guessed, "
            "wherever it arises " + DASH + " intake, a change's intake, the mockup iteration, a question before the "
            "design gate, an escalation mid-build (intake.md's sorting of questions; the owner's rule of 2026-11-08).") in text


# --- the explain-for-decision brief, parts 1, 4 and 5

def test_hotfix003_the_decision_brief_puts_options_only_where_answers_exist():
    brief = flat(section(read(SKILL), "The decision brief " + DASH + " when a decision is put to the user", 2))
    assert ("1. **The decision** " + DASH + " one sentence: what you are choosing between, or, for a behaviour the user "
            "has not yet described, the case the software must settle.") in brief
    assert ("Options are for a decision between answers that exist before the user speaks (a gate's approval of what "
            "the design or the mockup already writes down, scope, a consequence they bear, money, an irreversible step, "
            "a reading of an approved requirement, a change to what \"correct\" means); when the decision is what the "
            "software should do or how a feature behaves and the user has not yet described it, this part is the "
            "question itself, in prose, answered in the user's own words " + DASH + " never options you guessed for them "
            "to tick (`intake.md`, the sorting of questions; the owner's rule of 2026-11-08) " + DASH + " and part 5 "
            "waits for their answer: your view comes as a follow-up building on it, as intake's better-options bucket "
            "does.") in brief
    assert ("5. **Recommendation** " + DASH + " which one, and the reason in the user's currency; withheld for a "
            "behaviour the user has not yet described (part 4).") in brief


# --- Known-Pitfalls: KP-075

def test_hotfix003_kp075_names_the_pitfall_its_places_and_its_sign():
    text = read(PITFALLS)
    assert "### KP-075 " + DASH + " A question's sort left to the supervisor licensed guessed feature options at intake" in text
    entry = text[text.index("### KP-075"):]
    assert "**Correction (2026.11.09a):**" in entry
    assert ("(one of intake.md's closed list of facts the bridge's own procedures consume in a fixed form: the kind, the "
            "platform and runtime context, the delivery kind, the confirmation of a classification, a figure) may take "
            "the question form, the default or recommended answer first, and a short answer never makes a question a "
            "parameter") in entry
    assert ("(intake.md, change-cycle.md item 1, interface/mockups.md, design.md \"The gate\", the core's \"Escalate to "
            "the user when\", the explain-for-decision brief's part 4)") in entry
    assert ("**Applies:** every intake, every question before the design gate, every mockup iteration, every change "
            "cycle's intake, every escalation about product behaviour.") in entry
    assert ("The sign: a message to the owner offering options for a feature they have not yet described, or an intake "
            "batch whose feature questions carry answer lists.") in entry


# --- the places that keep the form (invariants of the hotfix's non-goals, one assert per place)

def test_hotfix003_the_kind_the_gates_the_run_parameters_the_figure_and_the_sign_off_keep_the_form():
    assert ("it the owner is asked is the kind, as its own question in the question form, `private` named") in read(INTAKE)
    assert ("each asked as a question of its own in the app's question form") in flat(read(DESIGN))
    assert ("each part's traits are a decision of their own, asked in the question form") in flat(read(DESIGN))
    assert ("each variant's approval asked as a question of its own in the app's question form") in flat(section(read(INTERFACE), "The gate", 3))
    assert ("each as a question of its own in the app's question form** (`AskUserQuestion`,") in flat(read(RUN_PARAMETERS))
    assert ("A limit the owner names is theirs: ask for the figure in the question form.") in flat(read(CONFIGURATION))
    assert ("each as a question of its own in the app's question form; nothing of that kind changes before they do") in flat(read(EVALUATE))
