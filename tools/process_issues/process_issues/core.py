"""Pure classification for the process-issues loop. No I/O lives here."""

import re

LABEL_HANDOVER = "handover"
LABEL_BLOCKED = "blocked"
LABEL_ANSWERED = "answered"
LABEL_HUMAN_APPROVED = "human-approved"
LABEL_WAITING = "waiting-human-approval"

STATE_SKIP = "skip"
STATE_BLOCKED = "blocked"
STATE_ANSWERED = "answered"
STATE_WAIT_APPROVAL = "wait-approval"
STATE_APPLY = "apply"
STATE_PROPOSE = "propose"

ACTION_NONE = "none"
ACTION_BLOCKED = "blocked"
ACTION_WAIT = "wait"
ACTION_APPLY = "apply"
ACTION_START = "start"
ACTION_RESUME = "resume"
ACTION_REPAIR = "repair"
ACTION_PROPOSE_THEN_APPLY = "propose-then-apply"

# The pure label states, highest precedence first. The human-approved
# and waiting-human-approval branches stay below the table, because
# they read artifacts and the existing order puts approval above
# waiting.
LABEL_PRECEDENCE = (
    (LABEL_HANDOVER, STATE_SKIP, ACTION_NONE),
    (LABEL_BLOCKED, STATE_BLOCKED, ACTION_BLOCKED),
    (LABEL_ANSWERED, STATE_ANSWERED, ACTION_NONE),
)


def classify(labels, prs, has_artifacts):
    """Map one issue's labels, linked PRs, and artifact flag to its state."""
    labels = set(labels)
    for label, state, action in LABEL_PRECEDENCE:
        if label in labels:
            return {"state": state, "action": action}
    if LABEL_HUMAN_APPROVED in labels:
        if has_artifacts:
            return {"state": STATE_APPLY, "action": ACTION_APPLY}
        return {"state": STATE_PROPOSE, "action": ACTION_PROPOSE_THEN_APPLY}
    if LABEL_WAITING in labels:
        return {"state": STATE_WAIT_APPROVAL, "action": ACTION_WAIT}
    pr_states = {pr.get("state") for pr in prs}
    if "merged" in pr_states:
        return {"state": STATE_PROPOSE, "action": ACTION_REPAIR}
    if "open" in pr_states:
        return {"state": STATE_PROPOSE, "action": ACTION_RESUME}
    if has_artifacts:
        return {"state": STATE_PROPOSE, "action": ACTION_RESUME}
    return {"state": STATE_PROPOSE, "action": ACTION_START}


def linked_prs(prs, number):
    """Return the raw PRs whose body carries a Refs line for this issue."""
    pattern = re.compile(rf"Refs #{number}\b")
    return [pr for pr in prs if pattern.search(pr.get("body") or "")]


def sorted_issues(issues):
    """Order issues oldest first by creation time, then by number."""
    return sorted(
        issues,
        key=lambda issue: (issue.get("createdAt") or "", issue.get("number") or 0),
    )


def linked_change_dir(prs, active_dirs):
    """Name the change dir a linked PR branch carries, merged PRs first.

    The branch must carry the change id as its last path segment, with an
    optional `archive-` prefix. A partial match links a foreign change.
    """
    ordered = sorted(prs, key=lambda pr: pr.get("state") != "merged")
    for pr in ordered:
        segment = (pr.get("headRefName") or "").rsplit("/", 1)[-1]
        if segment.startswith("archive-"):
            segment = segment[len("archive-"):]
        if segment in active_dirs:
            return segment
    return None
