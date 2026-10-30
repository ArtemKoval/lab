"""Rounds of the improver the tests work through the agent's service: a stub
improver that follows a script of tool calls, and stub case agents that decide
better once their instructions hold the improver's rule."""

from agent.tests.stubs import StubModel, calculate, call, stub
from backend.tests.round_requests import worker_answers
from domains import loader

# What the improver adds to the case agent's instructions in the tests, and what
# makes the stub case agents decide as the workers did.
RULE = "\nA general rule: decide each case as a careful worker would.\n"
VERSION_1 = loader.pack().instruction("case")
LUNA = {"model": "openai/gpt-6-luna", "reasoning_effort": "low"}


class RuleFollowingModel(StubModel):
    """A stub case agent that reads its case, then refers it, or once its
    instructions hold the rule, decides it as the worker did, working out an
    approval's award first."""

    answers: dict[str, tuple[str, float]] = {}

    def next_reply(self, messages):
        if len(messages) == 2:
            return call("get_case")
        copy_id = messages[1].content.removeprefix("Case ")
        decision, award = ("refer", 0)
        if RULE.strip() in messages[0].content:
            decision, award = self.answers[copy_id.rsplit("-E", 1)[0]]
        if decision == "approve" and messages[-1].name != "calculate_award":
            return calculate(copy_id, award)
        return call(
            "record_decision",
            decision=decision,
            award=award,
            section="Section 3",
            reason="The reason.",
        )


def case_agents_model():
    answers = worker_answers("evaluation") | worker_answers("held_out")
    return RuleFollowingModel(messages=iter(()), answers=answers)


def propose(instructions=VERSION_1 + RULE, **model):
    return call(
        "propose_change",
        instructions=instructions,
        reason="It approved cases the workers declined.",
        **(LUNA | model),
    )


def improver(*replies):
    """A stub improver with a script of replies, across its stretches."""
    return stub(*replies)


def whole_round():
    """The improver's replies in a round with one rejection: it reads the results,
    proposes a change, proposes another after the rejection, runs the evaluation,
    proposes a recipe and ends."""
    return improver(
        call("read_results"),
        propose(VERSION_1 + "\nA rule for CLM-1003.\n"),
        propose(),
        call("run_evaluation"),
        call("propose_recipe", recipe="1. Read the results.\n", reason="Shorter"),
        "The round is done.",
    )
