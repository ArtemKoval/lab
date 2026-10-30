"""The shapes of the backend's requests and responses."""

from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import BaseModel, Field, StringConstraints, model_validator


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


class Verdict(StrEnum):
    """Whether the business's rule kept a version of the case agent."""

    KEPT = "kept"
    ROLLED_BACK = "rolled_back"


class VersionStatus(StrEnum):
    """Where a version of the case agent stands."""

    CURRENT = "current"
    KEPT = "kept"
    ROLLED_BACK = "rolled_back"
    UNDER_TEST = "under_test"


class Letter(StrEnum):
    """The judge's levels, from different grounds to better expressed."""

    F = "F"
    C = "C"
    B = "B"
    A = "A"


class RoundStatus(StrEnum):
    OPEN = "open"
    FINISHED = "finished"
    STOPPED = "stopped"


class RoundStage(StrEnum):
    """Where an open round has got to, which the backend works out from its
    records."""

    FIRST_EVALUATIONS = "first_evaluations"
    IMPROVING = "improving"
    CHANGE_WAITING = "change_waiting"
    EVALUATING = "evaluating"
    VERDICT = "verdict"
    RECIPE_WAITING = "recipe_waiting"


class ProposalKind(StrEnum):
    CHANGE = "change"
    RECIPE = "recipe"


class Review(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"


class DiffLineKind(StrEnum):
    CONTEXT = "context"
    ADDED = "added"
    REMOVED = "removed"


# A model at its own default, with no reasoning effort sent. OpenAI's "none" is a
# real level of its own.
NO_REASONING_EFFORT = "default"


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
    email: str
    can_approve_over_limit: bool


class Step(BaseModel):
    step_id: int
    thread_id: str
    kind: StepKind
    content: str
    created_at: str


class MeasureSettings(BaseModel):
    """A setting for each measure the rule compares: accuracy and the grade as
    differences, cost and time per case as fractions of the old value."""

    accuracy: float = Field(ge=0)
    grade: float = Field(ge=0)
    cost_per_case: float = Field(ge=0)
    seconds_per_case: float = Field(ge=0)


class Objectives(BaseModel):
    """The floors a new version must meet on the held-out set."""

    accuracy: float = Field(ge=0, le=1)
    grade: float = Field(ge=0, le=3)


class SettingsValues(BaseModel):
    approval_limit: float = Field(gt=0, description="In US dollars")
    objectives: Objectives
    noise: MeasureSettings
    tolerance: MeasureSettings
    spending_limit: float = Field(gt=0, description="For each round, in US dollars")
    agents: Agents


class Settings(SettingsValues):
    number: int
    changed_by: str | None
    changed_at: str


class ModelAllowed(BaseModel):
    model: str
    reasoning_efforts: list[str]
    input_price: float = Field(description="US dollars per million input tokens")
    output_price: float = Field(description="US dollars per million output tokens")


class SettingsPage(BaseModel):
    current: Settings
    changes: list[Settings]
    models_allowed: list[ModelAllowed]


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
    version: int
    round_id: str | None
    round_number: int | None = Field(description="The round that ran it, if any")
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


class Measures(BaseModel):
    decision_accuracy: float
    accuracy: float
    cost_of_mistakes: float
    straight_through: float
    grade: float | None = Field(description="From 0 to 3, or null with none graded")
    model_cost_per_case: float
    seconds_per_case: float
    run_seconds: float | None


class CaseGrade(BaseModel):
    """The judge's grade of an explanation: its score from 0 to 3, the likeliest
    level, and the chances of the same grounds and the same section as the
    worker's."""

    score: float
    letter: Letter
    same_grounds: float
    same_section: float
    cost: float


class ScoredCase(RunCase):
    copy_of: str
    reason: str | None
    section: str | None
    grade: CaseGrade | None
    worker_decision: DecisionKind
    worker_award: float
    right: bool
    mistake_cost: float


class Evaluation(RunDetails):
    evaluation_set: EvaluationSet
    tiny: bool
    size: int
    judge_cost: float
    measures: Measures


class ScoredEvaluation(Evaluation):
    cases: list[ScoredCase]


class Accepted(BaseModel):
    status: Literal["accepted"] = "accepted"


class CaseAgentVersion(BaseModel):
    """A version as the case agent reads it, with no scores."""

    number: int
    instructions: str
    model: str
    reasoning_effort: str


class DiffLine(BaseModel):
    kind: DiffLineKind
    text: str


class Diff(BaseModel):
    added: int
    removed: int
    hunks: list[list[DiffLine]]


class VersionScores(BaseModel):
    """A version's scores on each set, from the evaluations rounds ran on it."""

    evaluation: Measures | None
    held_out: Measures | None


class VersionSummary(BaseModel):
    number: int
    status: VersionStatus
    model: str
    reasoning_effort: str
    based_on: int | None
    model_before: str | None
    reasoning_effort_before: str | None
    lines_added: int
    lines_removed: int
    reason: str
    proposed_by: str
    round_id: str | None
    approved_by: str | None
    approved_at: str | None
    created_at: str
    verdict: Verdict | None
    verdict_reason: str | None
    scores: VersionScores


class VersionDetails(VersionSummary):
    instructions: str
    diff: Diff | None


class Configuration(BaseModel):
    current: int
    versions: list[VersionSummary]


class NewNumber(BaseModel):
    """The number of a version or a recipe the improver's round made."""

    number: int


class CreateRoundRequest(BaseModel):
    worker_id: str = Field(description="The worker who started the round")


class RoundForService(BaseModel):
    """A round as the agent's service needs it to work."""

    round_id: str
    number: int
    status: RoundStatus
    thread_id: str
    improver_model: str
    improver_reasoning_effort: str
    instructions: str = Field(description="The improver's, around the recipe")
    models_allowed: list[ModelAllowed]
    first_evaluations: list[EvaluationSet] = Field(
        description="The first evaluations the round needed as it started, in order"
    )
    version_evaluations: list[EvaluationSet] = Field(
        description="The evaluations a version under test gets, in order"
    )


class ChangeProposalRequest(BaseModel):
    instructions: str = Field(min_length=1)
    model: str = Field(min_length=1)
    reasoning_effort: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class RecipeProposalRequest(BaseModel):
    recipe: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class Proposal(BaseModel):
    proposal_id: str
    round_id: str
    kind: ProposalKind
    reason: str
    instructions: str | None
    model: str | None
    reasoning_effort: str | None
    recipe: str | None
    proposed_at: str
    review: Review | None
    reviewed_by: str | None
    reviewed_at: str | None
    rejection_reason: str | None


class ReviewRequest(BaseModel):
    review: Review
    worker_id: str
    reason: str = Field(description="Why a proposal was rejected, or empty")

    @model_validator(mode="after")
    def check_reason(self) -> Self:
        """A rejection says why, so the improver can take it into account."""
        if self.review == Review.REJECTED and not self.reason.strip():
            raise ValueError("A rejection needs a reason")
        return self


class RejectionRequest(BaseModel):
    reason: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)] = (
        Field(description="Why, for the improver to read")
    )


class ImproverCallRequest(BaseModel):
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    cost: float = Field(ge=0, description="In US dollars, as OpenRouter reports it")


class StopRoundsRequest(BaseModel):
    reason: str = Field(min_length=1)


class VerdictScores(BaseModel):
    held_out_before: Measures | None
    held_out_after: Measures | None
    evaluation_after: Measures | None


class VerdictResult(BaseModel):
    version: int
    verdict: Verdict
    reason: str
    current_version: int
    summary: str = Field(description="The verdict in a sentence, for the improver")
    scores: VerdictScores


# What the improver reads.


class AgentAnswer(BaseModel):
    decision: DecisionKind | None
    award: float | None
    reason: str | None
    section: str | None


class WorkerAnswer(BaseModel):
    decision: DecisionKind
    award: float
    reason: str
    reference: str


class JudgeAnswer(BaseModel):
    grade: float
    letter: Letter
    same_grounds: Literal["yes", "no"]
    same_section: Literal["yes", "no"]


class CaseBesideWorker(BaseModel):
    """A case of the evaluation set, with the agent's answer beside the
    worker's and the judge's grade."""

    case_id: str
    summary: str
    agent: AgentAnswer
    worker: WorkerAnswer
    judge: JudgeAnswer | None


class EvaluationSetResults(BaseModel):
    wrong: list[CaseBesideWorker]
    explained_least_well: list[CaseBesideWorker]


class EarlierRound(BaseModel):
    round: int
    recipe_version: int
    version: int | None
    model: str | None
    reasoning_effort: str | None
    reason: str | None
    held_out_before: Measures | None
    held_out_after: Measures | None
    verdict: Verdict | None
    why: str | None


class Spending(BaseModel):
    limit: float
    spent: float
    left: float


class ImproverView(BaseModel):
    current_version: CaseAgentVersion = Field(
        description="Without the contents of the documents, which never change"
    )
    scores: VersionScores
    evaluation_set: EvaluationSetResults
    earlier_rounds: list[EarlierRound]
    objectives_on_the_held_out_set: Objectives
    noise: MeasureSettings
    tolerance: MeasureSettings
    rule: str
    spending: Spending
    models_allowed: list[ModelAllowed]


# What the Improvement page shows.


class RoundReviewView(BaseModel):
    """Who approved or rejected one of the improver's proposals, and when."""

    kind: ProposalKind
    review: Review
    reviewed_by: str
    reviewed_at: str
    rejection_reason: str | None


class WaitingProposal(BaseModel):
    proposal_id: str
    kind: ProposalKind
    reason: str
    proposed_at: str
    diff: Diff
    model_before: str | None
    reasoning_effort_before: str | None
    model_after: str | None
    reasoning_effort_after: str | None


class RoundSummary(BaseModel):
    round_id: str
    number: int
    status: RoundStatus
    stage: RoundStage | None
    progress: str | None = Field(description="Such as 2 of 3, or null")
    started_by: str
    started_at: str
    finished_at: str | None
    stopped_by: str | None
    stopped_because: str | None
    recipe: int
    settings: int
    spending_limit: float
    cost: float
    version: int | None
    model: str | None
    reasoning_effort: str | None
    reason: str | None
    verdict: Verdict | None
    verdict_reason: str | None
    held_out_before: Measures | None
    held_out_after: Measures | None
    reviews: list[RoundReviewView]


class RoundView(RoundSummary):
    waiting: WaitingProposal | None
    evaluations: list[Evaluation]


class VersionPoint(BaseModel):
    """A version's held-out accuracy and grade, for the chart."""

    number: int
    verdict: Verdict | None
    accuracy: float | None
    grade: float | None


class RecipeSummary(BaseModel):
    number: int
    current: bool
    reason: str
    proposed_by: str
    round_id: str | None
    approved_by: str | None
    approved_at: str | None
    created_at: str
    lines_added: int
    lines_removed: int


class RecipeDetails(RecipeSummary):
    recipe: str
    diff: Diff | None


class Improvement(BaseModel):
    round: RoundView | None = Field(description="The open round, or the newest")
    rounds: list[RoundSummary]
    first_version: VersionPoint
    versions_tried: list[VersionPoint]
    recipes: list[RecipeSummary]
