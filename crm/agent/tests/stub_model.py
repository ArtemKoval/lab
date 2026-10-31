"""A stub model, so that tests never call a real model, and replies to script it."""

import itertools

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult


class StubModel(GenericFakeChatModel):
    """A chat model that gives scripted replies, or raises a scripted error,
    and keeps the prompts it was sent."""

    prompts: list[list[BaseMessage]] = []

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        self.prompts.append(messages)
        reply = next(self.messages)
        if isinstance(reply, Exception):
            raise reply
        message = AIMessage(content=reply) if isinstance(reply, str) else reply
        return ChatResult(generations=[ChatGeneration(message=message)])


CALL_IDS = itertools.count()


def stub(*replies):
    return StubModel(messages=iter(replies))


def call(name, text="", **args):
    """A reply that calls one tool, with an id of its own as a real model gives."""
    tool_call = {"name": name, "args": args, "id": f"call-{next(CALL_IDS)}"}
    return AIMessage(content=text, tool_calls=[tool_call])


def record(decision):
    return call(
        "record_decision",
        decision=decision,
        section="Section 3, Trip Delay",
        reason="The delay was covered.",
    )


def pay(amount, text=""):
    return call("pay_case", text=text, amount=amount)


def decide(decision, award, *extra):
    """The replies of a case agent that reads its case and decides it."""
    return [
        call("get_case"),
        record(decision),
        *extra,
        AIMessage(content=f"Decision: {decision}."),
    ]
