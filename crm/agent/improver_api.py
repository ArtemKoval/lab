"""The CRM backend's API for the improver and for the service's work on a
round: one function for each operation under /api/rounds, and the round's
evaluations. The case agent's tools never use it."""

from typing import Any, Literal

from agent.connection import get, post

RoundStatus = Literal["open", "finished", "stopped"]
OPEN: RoundStatus = "open"
Review = Literal["approved", "rejected"]
APPROVED: Review = "approved"
REJECTED: Review = "rejected"


def create_round(worker_id: str) -> dict[str, Any]:
    return post("/rounds", **{"worker_id": worker_id})


def get_round(round_id: str) -> dict[str, Any]:
    return get(f"/rounds/{round_id}")


def get_improver_view(round_id: str) -> dict[str, Any]:
    return get(f"/rounds/{round_id}/results")


def record_change_proposal(
    round_id: str, instructions: str, model: str, reasoning_effort: str, reason: str
) -> dict[str, Any]:
    body = {
        "instructions": instructions,
        "model": model,
        "reasoning_effort": reasoning_effort,
        "reason": reason,
    }
    return post(f"/rounds/{round_id}/proposals/change", **body)


def record_recipe_proposal(round_id: str, recipe: str, reason: str) -> dict[str, Any]:
    body = {"recipe": recipe, "reason": reason}
    return post(f"/rounds/{round_id}/proposals/recipe", **body)


def record_review(
    round_id: str, proposal_id: str, review: Review, worker_id: str, reason: str
) -> dict[str, Any]:
    body = {"review": review, "worker_id": worker_id, "reason": reason}
    return post(f"/rounds/{round_id}/proposals/{proposal_id}/review", **body)


def create_version(round_id: str) -> dict[str, Any]:
    return post(f"/rounds/{round_id}/version")


def create_recipe(round_id: str) -> dict[str, Any]:
    return post(f"/rounds/{round_id}/recipe")


def create_round_evaluation(round_id: str) -> dict[str, Any]:
    return post(f"/runs/rounds/{round_id}/evaluations")


def record_verdict(round_id: str) -> dict[str, Any]:
    return post(f"/rounds/{round_id}/verdict")


def record_improver_call(
    round_id: str, input_tokens: int, output_tokens: int, cost: float
) -> dict[str, Any]:
    body = {"input_tokens": input_tokens, "output_tokens": output_tokens, "cost": cost}
    return post(f"/rounds/{round_id}/model-calls", **body)


def finish_round(round_id: str) -> dict[str, Any]:
    return post(f"/rounds/{round_id}/finish")


def stop_rounds(reason: str) -> list[str]:
    return post("/rounds/stop", **{"reason": reason})
