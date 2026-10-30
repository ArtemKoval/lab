"""Who may call each of the backend's operations: anyone, the agent with its key, a
signed-in worker or the agent, or a signed-in worker alone."""

from backend.tests.settings_requests import STARTING

ROUND = "/api/improvement/rounds/round-1"
PROPOSAL = f"{ROUND}/proposals/proposal-1"

OPEN = {"health"}

# Every operation only the agent's side calls.
AGENT_OPERATIONS = {
    "start_case",
    "record_step",
    "record_model_call",
    "record_work_time",
    "record_decision",
    "calculate_award",
    "pay_case",
    "hold_payment",
    "fail_case",
    "get_version",
    "get_current_version",
    "get_screening",
    "create_dispatch",
    "create_evaluation",
    "create_round_evaluation",
    "record_run_cases",
    "finish_run",
    "stop_runs",
    "create_round",
    "stop_rounds",
    "get_round",
    "get_improver_view",
    "record_change_proposal",
    "record_recipe_proposal",
    "record_review",
    "create_version",
    "create_recipe",
    "record_verdict",
    "record_improver_call",
    "finish_round",
}

# The reads both the dashboard and the agent use, with a path each answers.
SHARED_READS = {
    "list_cases": "/api/cases",
    "get_case": "/api/cases/CLM-1001",
    "get_contract": "/api/contracts/POL-2001",
    "get_case_history": "/api/customers/CUS-3001/cases",
    "get_agent_api": "/api/agent/openapi.json",
}

# Every operation only a signed-in worker may use, with a body it would accept.
WORKER_OPERATIONS = {
    "get_signed_in_worker": ("GET", "/api/me", None),
    "list_steps": ("GET", "/api/cases/CLM-1002/steps", None),
    "get_configuration": ("GET", "/api/configuration", None),
    "get_version_details": ("GET", "/api/configuration/versions/1", None),
    "get_settings": ("GET", "/api/settings", None),
    "change_settings": ("PUT", "/api/settings", STARTING),
    "get_latest_dispatch": ("GET", "/api/dispatches/latest", None),
    "start_dispatch": ("POST", "/api/dispatches", {"agents": 3}),
    "list_evaluations": ("GET", "/api/evaluations", None),
    "get_evaluation": ("GET", "/api/evaluations/run-1", None),
    "start_evaluation": (
        "POST",
        "/api/evaluations",
        {"evaluation_set": "held_out", "tiny": True, "agents": 5},
    ),
    "sign_off_case": ("POST", "/api/cases/CLM-1002/sign-off", None),
    "get_improvement": ("GET", "/api/improvement", None),
    "get_recipe": ("GET", "/api/improvement/recipes/1", None),
    "start_round": ("POST", "/api/improvement/rounds", None),
    "stop_round": ("POST", f"{ROUND}/stop", None),
    "approve_proposal": ("POST", f"{PROPOSAL}/approval", None),
    "reject_proposal": ("POST", f"{PROPOSAL}/rejection", {"reason": "Too broad"}),
}
