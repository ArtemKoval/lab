"""Behavior tests for the pure classification in process_issues.core."""

from process_issues import core


def test_handover_label_wins_over_everything():
    result = core.classify({"handover", "human-approved"}, [], False)
    assert result == {"state": core.STATE_SKIP, "action": core.ACTION_NONE}


def test_answered_label_wins_over_approval():
    result = core.classify({"answered", "human-approved"}, [], True)
    assert result == {"state": core.STATE_ANSWERED, "action": core.ACTION_NONE}


def test_waiting_label_waits():
    result = core.classify({"waiting-human-approval"}, [], True)
    assert result == {"state": core.STATE_WAIT_APPROVAL, "action": core.ACTION_WAIT}


def test_plain_issue_proposes():
    result = core.classify(set(), [], False)
    assert result == {"state": core.STATE_PROPOSE, "action": core.ACTION_START}


def test_approved_with_artifacts_applies():
    result = core.classify({"human-approved"}, [], True)
    assert result == {"state": core.STATE_APPLY, "action": core.ACTION_APPLY}


def test_approved_without_artifacts_proposes_then_applies():
    result = core.classify({"human-approved"}, [], False)
    assert result == {
        "state": core.STATE_PROPOSE,
        "action": core.ACTION_PROPOSE_THEN_APPLY,
    }


def test_merged_linked_pr_repairs():
    prs = [{"number": 90, "state": "merged", "headRefName": "feat/add-x"}]
    result = core.classify(set(), prs, True)
    assert result == {"state": core.STATE_PROPOSE, "action": core.ACTION_REPAIR}


def test_open_linked_pr_resumes():
    prs = [{"number": 90, "state": "open", "headRefName": "feat/add-x"}]
    result = core.classify(set(), prs, False)
    assert result == {"state": core.STATE_PROPOSE, "action": core.ACTION_RESUME}


def test_artifacts_without_pr_resume():
    result = core.classify(set(), [], True)
    assert result == {"state": core.STATE_PROPOSE, "action": core.ACTION_RESUME}


def test_oldest_first_order_by_created_then_number():
    issues = [
        {"number": 20, "createdAt": "2026-11-04T10:00:00Z"},
        {"number": 9, "createdAt": "2026-11-04T09:00:00Z"},
        {"number": 15, "createdAt": "2026-11-04T10:00:00Z"},
    ]
    order = [i["number"] for i in core.sorted_issues(issues)]
    assert order == [9, 15, 20]


def test_sorted_issues_treats_missing_fields_as_oldest():
    issues = [
        {"number": 2, "createdAt": "2026-11-04T10:00:00Z"},
        {"number": 3},
        {"number": 1},
    ]
    order = [i["number"] for i in core.sorted_issues(issues)]
    assert order == [1, 3, 2]


def test_sorted_issues_sorts_a_missing_number_before_present_numbers():
    issues = [
        {"number": 1, "createdAt": "x"},
        {"createdAt": "x"},
    ]
    order = [i.get("number") for i in core.sorted_issues(issues)]
    assert order == [None, 1]


def test_linked_change_dir_prefers_merged_branch():
    prs = [
        {"number": 91, "state": "open", "headRefName": "chore/archive-add-sec-scan"},
        {"number": 90, "state": "merged", "headRefName": "feat/add-process-issues"},
    ]
    dirs = ["add-sec-scan", "add-process-issues"]
    assert core.linked_change_dir(prs, dirs) == "add-process-issues"


def test_linked_change_dir_returns_none_without_match():
    prs = [{"number": 90, "state": "merged", "headRefName": "feat/unrelated"}]
    assert core.linked_change_dir(prs, ["add-sec-scan"]) is None


def test_linked_change_dir_skips_a_pr_without_a_branch():
    prs = [
        {"number": 92, "state": "open"},
        {"number": 93, "state": "open", "headRefName": "feat/add-x"},
    ]
    assert core.linked_change_dir(prs, ["add-x"]) == "add-x"


def test_linked_change_dir_rejects_a_branch_that_extends_the_change_id():
    prs = [{"number": 90, "state": "merged", "headRefName": "feat/add-x-other"}]
    assert core.linked_change_dir(prs, ["add-x"]) is None


def test_linked_prs_respects_number_boundary():
    prs = [{"number": 86, "state": "open", "headRefName": "b", "body": "Refs #86"}]
    assert core.linked_prs(prs, 8) == []
    assert core.linked_prs(prs, 86) == prs


def test_linked_prs_skips_bodies_without_refs_line():
    prs = [{"number": 86, "state": "open", "headRefName": "b", "body": "closes 86"}]
    assert core.linked_prs(prs, 86) == []
