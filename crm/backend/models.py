"""The shapes of the backend's requests and responses."""

from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator

Status = Literal[
    "waiting", "in_progress", "waiting_for_sign_off", "decided", "left_for_worker"
]
DecisionKind = Literal["approve", "decline", "refer"]
StepKind = Literal["tool_call", "tool_result", "message", "reading", "error"]
TodoStatus = Literal["to_do", "in_progress", "done", "left_for_worker"]
DocumentName = Literal["wording", "manual"]


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


class Payment(BaseModel):
    amount: float
    paid_at: str
    signed_off_by: str | None


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
    queue: str
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
        if self.decision == "approve" and self.award == 0:
            raise ValueError("An approval needs an award above zero")
        if self.decision != "approve" and self.award != 0:
            raise ValueError("A decline or a referral has an award of zero")
        return self


class PaymentRequest(BaseModel):
    amount: float = Field(gt=0, description="The approved award in US dollars")


class SignOffRequest(BaseModel):
    worker_id: str


class FailureRequest(BaseModel):
    reason: str = Field(min_length=1, description="What went wrong")


class Todo(BaseModel):
    content: str = Field(min_length=1)
    status: TodoStatus


class Run(BaseModel):
    run_id: str
    cap: int
    status: Literal["running", "finished"]
    started_at: str
    finished_at: str | None
    summary: str | None
    todos: list[Todo]


class RunRequest(BaseModel):
    cap: int = Field(ge=1, description="The most cases the run can work")


class TodosRequest(BaseModel):
    todos: list[Todo]


class FinishRequest(BaseModel):
    summary: str = Field(min_length=1, description="The summary for the workers")
