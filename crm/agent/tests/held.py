"""Cases the tests hold for a worker's sign-off, paused or stopped short of the
pause, and resume through the agent's AgentCore app."""

from langgraph.checkpoint.memory import InMemorySaver

from agent import harness
from agent.tests import invoking
from agent.tests.records import case_of
from agent.tests.stubs import agent_on, approve, stub

# The channel LangGraph saves an interrupt on, which the case graph's pause writes.
INTERRUPT = "__interrupt__"


def state_of(agent, client, case_id):
    """The case graph's saved state on the case's thread."""
    return agent.graph.get_state(harness.thread_of(case_of(client, case_id)))


def hold(case_id="CLM-1003", award=3750.0, saver=None, **given):
    """Work a case to an approval over the limit, held for sign-off, and return its
    case agent."""
    agent = agent_on(stub(*approve(case_id, award)), saver, **given)
    harness.work_case(case_id, None, agent)
    return agent


class StopAtThePause(InMemorySaver):
    """Stops as the pause's interrupt is saved, once: the decision and the step that
    recorded it are saved, and the pause never ran, as when the process stops in
    between."""

    stopped = False

    def put_writes(self, config, writes, task_id, task_path=""):
        if not self.stopped and any(channel == INTERRUPT for channel, _ in writes):
            self.stopped = True
            raise KeyboardInterrupt
        super().put_writes(config, writes, task_id, task_path)


def resume_case(agent, case_id):
    """Ask the agent to resume a case, as the app does, and wait for the resume."""
    return agent.invoke(invoking.resume_case(case_id))
