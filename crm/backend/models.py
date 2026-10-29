"""The shapes of the backend's requests and responses."""

from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import BaseModel, Field, model_validator


class Status(StrEnum):
    """Where a case stands."""

    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    WAITING_FOR_SIGN_OFF = "waiting_for_sign_off"
    DECIDED = "decided"
    LEFT_FOR_WORKER = "left_for_worker"


class DecisionKind(StrEnum):
    APPROVE = "approve"
    DECLINE = "decline"
    REFER = "refer"


class RunKind(StrEnum):
    DISPATCH = "dispatch"
    EVALUATION = "evaluation"


class RunStatus(StrEnum):
    RUNNING = "running"
    FINISHED = "finished"
    STOPPED = "stopped"


class EvaluationSet(StrEnum):
    """The labeled sets of cases an evaluation can work."""

    EVALUATION = "evaluation"
    HELD_OUT = "held_out"


StepKind = Literal["tool_call", "tool_result", "message", "reading", "error"]
MOST_AGENTS = 25
Agents = Annotated[
    int, Field(ge=1, le=MOST_AGENTS, description="How many case agents work at once")
]
DocumentName = Literal["wording", "manual"]
Benefit = Literal[
    "trip_cancellation",
    "trip_interruption",
    "trip_delay",
    "baggage_delay",
    "baggage",
    "passport",
    "emergency_medical",
]
LineKind = Literal[
    "item", "electronics", "cash", "expense", "hotel", "meals_without_receipts"
]


class Item(BaseModel):
    description: str
    category: str
    amount: float


class Document(BaseModel):
    name: str
    type: str
    content: str


class Decision(BaseModel):
    decision: DecisionKind
    award: float
    section: str
    reason: str
    decided_at: str
    signed_off_by: str | None
    signed_off_at: str | None


class Payment(BaseModel):
    amount: float
    paid_at: str
    signed_off_by: str | None
    signed_off_at: str | None


class CaseSummary(BaseModel):
    case_id: str
    customer_name: str
    case_type: str
    summary: str
    amount_claimed: float
    submitted_on: str
    status: Status
    decision: DecisionKind | None
    award: float | None


class Case(BaseModel):
    case_id: str
    contract_id: str
    customer_id: str
    customer_name: str
    case_type: str
    submitted_on: str
    incident_date: str
    incident_location: str
    summary: str
    story: str
    items: list[Item]
    amount_claimed: float
    documents: list[Document]
    status: Status
    thread_id: str | None
    attempts: int
    evaluation_id: str | None
    copy_of: str | None
    decision: Decision | None
    payment: Payment | None


class Trip(BaseModel):
    destination: str
    departs_on: str
    returns_on: str
    trip_cost: float


class Contract(BaseModel):
    contract_id: str
    customer_id: str
    plan: str
    add_ons: list[str]
    purchased_on: str
    sold_through: str
    trip: Trip
    travelers: list[str]
    status: str


class PreviousCase(BaseModel):
    case_id: str
    filed_on: str
    incident_date: str
    case_type: str
    summary: str
    outcome: str
    amount_paid: float


class Worker(BaseModel):
    worker_id: str
    name: str
    role: str
    can_approve_over_limit: bool


class Step(BaseModel):
    step_id: int
    thread_id: str
    kind: StepKind
    content: str
    created_at: str


class Instructions(BaseModel):
    case: str


class Section(BaseModel):
    document: DocumentName
    document_title: str
    number: int
    title: str
    text: str


class SectionMatch(BaseModel):
    document: DocumentName
    number: int
    title: str
    excerpts: list[str]


class StartRequest(BaseModel):
    thread_id: str = Field(min_length=1)


class StepRequest(BaseModel):
    kind: StepKind
    content: str = Field(min_length=1)


class DecisionRequest(BaseModel):
    decision: DecisionKind
    award: float = Field(ge=0, description="In US dollars, 0 for a decline or referral")
    section: str = Field(
        min_length=1, description="The sections of the wording and the manual relied on"
    )
    reason: str = Field(
        min_length=1, description="Two or three sentences explaining the decision"
    )

    @model_validator(mode="after")
    def check_award(self) -> Self:
        """An approval pays something, and a decline or referral pays nothing."""
        if self.decision == DecisionKind.APPROVE and self.award == 0:
            raise ValueError("An approval needs a award above zero")
        if self.decision != DecisionKind.APPROVE and self.award != 0:
            raise ValueError("A decline or a referral has a award of zero")
        return self


class PaymentRequest(BaseModel):
    amount: float = Field(gt=0, description="The approved award in US dollars")


class SignOffRequest(BaseModel):
    worker_id: str


class Plan(BaseModel):
    plan: str
    name: str
    trip_cancellation_max: float
    trip_delay_waiting_hours: int
    trip_delay_max: float
    baggage_delay_waiting_hours: int
    baggage_delay_max: float
    baggage_max: float
    per_item_limit: float
    passport_max: float
    emergency_medical_max: float
    deductible: float


class AddOn(BaseModel):
    add_on: str
    name: str
    effect: str
    electronics_per_item_limit: float | None = None


class Plans(BaseModel):
    plans: list[Plan]
    deductible_applies_to: list[Benefit]
    add_ons: list[AddOn]


class Line(BaseModel):
    description: str = Field(min_length=1)
    amount: float = Field(ge=0, description="The total claimed, before limits")
    quantity: int = Field(ge=1, description="How many separate items")
    kind: LineKind
    nights: int = Field(ge=0, description="For a hotel, and 0 otherwise")
    hours: float = Field(
        ge=0, description="For meals without receipts, and 0 otherwise"
    )


class AwardRequest(BaseModel):
    benefit: Benefit
    lines: list[Line] = Field(
        description="The covered lines, with any excluded left out"
    )
    paid_by_others: float = Field(ge=0, description="Paid or refunded by others")


class CalculationStep(BaseModel):
    step: str
    amount: float


class Award(BaseModel):
    calculation: list[CalculationStep]
    award: float
    needs_sign_off: bool


class FailureRequest(BaseModel):
    reason: str = Field(min_length=1, description="What went wrong")


class ModelCallRequest(BaseModel):
    run_id: str | None = Field(description="The run the call was made in, or null")
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    cost: float = Field(ge=0, description="In US dollars, as OpenRouter reports it")


class ModelCall(BaseModel):
    case_id: str
    thread_id: str
    run_id: str | None
    input_tokens: int
    output_tokens: int
    cost: float
    created_at: str


class WorkTimeRequest(BaseModel):
    run_id: str | None = Field(description="The run the work was done in, or null")
    seconds: float = Field(ge=0, description="How long the agent worked on the case")


class WorkTime(BaseModel):
    case_id: str
    thread_id: str
    run_id: str | None
    started_at: str
    seconds: float


class StartDispatchRequest(BaseModel):
    agents: Agents


class CreateDispatchRequest(StartDispatchRequest):
    model: str = Field(min_length=1)
    reasoning_effort: str = Field(min_length=1, description="Or none")


class RunCasesRequest(BaseModel):
    case_ids: list[str] = Field(description="The cases a dispatch works, in order")


class HeldAward(BaseModel):
    case_id: str
    award: float


class DispatchSummary(BaseModel):
    approved: int
    declined: int
    referred: int
    waiting_for_sign_off: list[HeldAward]
    left_for_worker: list[str]
    unfinished: list[str]


class RunCase(CaseSummary):
    started_at: str | None
    seconds: float
    model_cost: float


class RunDetails(BaseModel):
    run_id: str
    number: int
    kind: RunKind
    agents: int
    model: str
    reasoning_effort: str
    status: RunStatus
    started_at: str
    finished_at: str | None
    seconds: float | None
    model_cost: float


class Run(RunDetails):
    evaluation_set: EvaluationSet | None
    tiny: bool | None
    summary: DispatchSummary | None
    cases: list[RunCase]


class StartEvaluationRequest(StartDispatchRequest):
    evaluation_set: EvaluationSet
    tiny: bool = Field(description="Only the set's five tiny cases")


class CreateEvaluationRequest(StartEvaluationRequest, CreateDispatchRequest):
    pass


class Measures(BaseModel):
    decision_accuracy: float
    accuracy: float
    cost_of_mistakes: float
    straight_through: float
    model_cost_per_case: float
    seconds_per_case: float
    run_seconds: float | None


class ScoredCase(RunCase):
    copy_of: str
    reason: str | None
    worker_decision: DecisionKind
    worker_award: float
    right: bool
    mistake_cost: float


class Evaluation(RunDetails):
    evaluation_set: EvaluationSet
    tiny: bool
    size: int
    measures: Measures


class ScoredEvaluation(Evaluation):
    cases: list[ScoredCase]


class Accepted(BaseModel):
    status: Literal["accepted"] = "accepted"
