"""The Copilot's turn traced in Langfuse: one root run per turn, in the
conversation's session, under the turn's trace name. The traces fixture
stands in for Langfuse and keeps the metadata of each root run."""

from agent.tests.copilot_driver import Copilot

WHY = "Why does CLM-1003 need me?"


def test_a_turn_is_traced_in_the_session_of_its_conversation(
    client, copilot: Copilot, traces
):
    conversation = copilot.ask(WHY)
    assert [(t["langfuse_session_id"], t["langfuse_trace_name"]) for t in traces] == [
        (conversation["conversation_id"], "Copilot turn")
    ]
