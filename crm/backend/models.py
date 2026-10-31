"""The shapes of the backend's requests and responses."""

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    Field,
    StringConstraints,
)

from backend.pack_types import (  # noqa: F401 — the pack-shaped types re-exported
    AddOn,
    Award,
    AwardRequest,
    Benefit,
    CalculationStep,
    Line,
    LineKind,
    Plan,
    Plans,
)


class Status(StrEnum):
    """Where a case stands."""

    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    WAITING_FOR_SIGN_OFF = "waiting_for_sign_off"
    SENT_BACK = "sent_back"
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


def to_the_cent(amount: float) -> float:
    """Round an amount in US dollars to the cent."""
    return round(amount, 2)


# A model at its own default, with no reasoning effort sent. OpenAI's "none" is a
# real level of its own.
NO_REASONING_EFFORT = "default"


# The kinds of step recorded through record_step.
RecordedStepKind = Literal[
    "screening",
    "tool_call",
    "tool_result",
    "message",
    "lookup",
    "memory_search",
    "memory_save",
    "refusal",
    "error",
]
# A worker's note on a decision sent back, which only the app records.
StepKind = RecordedStepKind | Literal["sent_back"]
MOST_AGENTS = 25
NOTE_LENGTH = 1000
Agents = Annotated[
    int, Field(ge=1, le=MOST_AGENTS, description="How many case agents work at once")
]



class Item(BaseModel):
    description: str
    category: str
    amount: float


class Document(BaseModel):
    name: str
    type: str
    content: str


class Calculation(BaseModel):
    lines: list[CalculationStep]
    award: float


class DecisionRecord(BaseModel):
    """A decision as cases manual section 14 records it."""

    decision: DecisionKind
    section: str
    reason: str
    decided_by: str
    decided_at: str
    manual_version: str
    gateway_refusal: str | None
    # The outcome kind the pack resolved, and its opaque payload, on an
    # approval, and nothing on a decline or a referral.
    outcome: str | None = None
    payload: dict | None = None


class Decision(DecisionRecord):
    signed_off_by: str | None
    signed_off_at: str | None


class EffectRun(BaseModel):
    """One executed effect on a case, with the record the pack's execute gave,
    and its summary of the outcome."""

    case_id: str
    effect: str
    result: dict
    summary: str
    ran_at: str


class PackView(BaseModel):
    """The active pack's declarations, which the tools and the dashboard render."""

    name: str
    display_name: str
    resolutions: list[str]
    outcomes: dict[str, str]
    config: dict[str, str]
    effects: dict[str, dict]


class SentBackDecision(DecisionRecord):
    """A decision a senior worker sent back to the agent, with their note."""

    note: str
    sent_back_by: str
    sent_back_at: str


class CaseSummary(BaseModel):
    case_id: str
    customer_name: str
    case_type: str
    summary: str
    amount_claimed: float
    submitted_on: str
    status: Status
    decision: DecisionKind | None
    outcome: str | None = Field(
        default=None,
        description="The pack's own line on the outcome it resolved, if it did",
    )
    resuming: bool = Field(description="A resume is working on the case")


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
    effect: EffectRun | None = None
    sent_back_decisions: list[SentBackDecision] = Field(
        description="The decisions workers sent back, oldest first"
    )


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


class Source(BaseModel):
    """A context file a lookup's answer came from, and that file's source."""

    file: str
    system: str
    owner: str
    reviewed: str


class Step(BaseModel):
    step_id: int
    thread_id: str
    kind: StepKind
    content: str
    sources: list[Source]
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


class StartRequest(BaseModel):
    thread_id: str = Field(min_length=1)


class StepRequest(BaseModel):
    kind: RecordedStepKind
    content: str = Field(min_length=1)
    sources: list[Source] = Field(
        description="The context files a lookup came from, and none for other steps"
    )


class NewStep(BaseModel):
    """A step the app adds to a case, recorded by the agent or the app itself."""

    kind: StepKind
    content: str
    sources: list[Source]


class SendBackRequest(BaseModel):
    note: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=NOTE_LENGTH),
    ] = Field(description="What the agent should look at again")


class TakeRequest(BaseModel):
    run_id: str | None = Field(
        description="The dispatch taking the case, or null for a resume"
    )


class DecisionRequest(BaseModel):
    """A decision to record, which cases manual section 14 checks."""

    decision: DecisionKind
    section: str = Field(
        description="The sections of the wording and the manual relied on"
    )
    reason: str = Field(description="Two or three sentences explaining the decision")
    decided_by: str = Field(
        description="Who or what made the decision, such as the CRM Agent "
        "with the version of its configuration"
    )


class HoldRequest(BaseModel):
    reason: str = Field(min_length=1, description="Why the Gateway refused to pay")


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
    outcome: str


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
    stopped_because: str | None
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
    # The number the pack's metric reads from the outcome payload, which
    # scoring compares with the worker's label.
    award: float
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


class ScreeningModel(BaseModel):
    """The model the check for hidden instructions runs on, outside the versions."""

    model: str
    reasoning_effort: str


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


class RoundForTheAgent(BaseModel):
    """A round as the agent needs it to work."""

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


class RejectionRequest(BaseModel):
    reason: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)] = (
        Field(description="Why, for the improver to read")
    )


class ImproverCallRequest(BaseModel):
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    cost: float = Field(ge=0, description="In US dollars, as OpenRouter reports it")


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


# The Copilot's conversations and what the Copilot records of them.

MESSAGE_LENGTH = 4000
Message = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=MESSAGE_LENGTH),
]


class TurnStatus(StrEnum):
    """Where one of the Copilot's turns stands. A turn reads as stopped when it has
    been working too long; it is never recorded as stopped."""

    WORKING = "working"
    WAITING_FOR_CONFIRMATION = "waiting_for_confirmation"
    DONE = "done"
    FAILED = "failed"
    STOPPED = "stopped"


class CardKind(StrEnum):
    """What a card's tool does: looks up cases, customers and contracts or the
    context layer, works with the agent's work or the memory, or acts."""

    CASES = "cases"
    CUSTOMERS = "customers"
    CONTEXT = "context"
    WORK = "work"
    MEMORY = "memory"
    ACTION = "action"


class CardStatus(StrEnum):
    WORKING = "working"
    DONE = "done"
    REFUSED = "refused"
    FAILED = "failed"


class ConfirmationAnswer(StrEnum):
    SIGN_OFF = "sign_off"
    CANCEL = "cancel"


class MessageRequest(BaseModel):
    message: Message = Field(description="The worker's message to the Copilot")


class ConfirmationRequest(BaseModel):
    turn_id: str = Field(description="The turn whose confirmation card was shown")
    answer: ConfirmationAnswer


class Confirmation(BaseModel):
    """A sign-off waiting for the worker's confirmation, from the app's records."""

    case_id: str
    customer_name: str
    outcome: str
    reason: str


class CopilotStep(BaseModel):
    """A card: one tool the Copilot called, what was asked and what came back."""

    step_id: int
    tool: str
    kind: CardKind
    input: str = Field(description="The tool's main input, such as CLM-1012")
    asked: str
    status: CardStatus
    answer: str | None
    reason: str | None
    sources: list[Source]
    started_at: str
    finished_at: str | None
    seconds: float = Field(description="So far, while it works")


class CopilotTurn(BaseModel):
    turn_id: str
    number: int
    message: str
    status: TurnStatus
    started_at: str
    paused_at: str | None
    answered_at: str | None
    finished_at: str | None
    seconds: float | None = Field(
        description="Once it has finished, leaving out the wait for the worker"
    )
    answer: str | None
    model_calls: int | None
    cost: float | None
    failure: str | None
    confirmation: Confirmation | None
    confirmation_answer: ConfirmationAnswer | None
    canceled_because: str | None
    steps: list[CopilotStep]


class ConversationSummary(BaseModel):
    conversation_id: str
    title: str = Field(description="The first message")
    created_at: str


class Conversation(ConversationSummary):
    turns: list[CopilotTurn]


class CopilotModel(BaseModel):
    """The model the Copilot runs on."""

    model: str
    reasoning_effort: str


class CopilotStepRequest(BaseModel):
    tool: str = Field(min_length=1)
    kind: CardKind
    input: str = Field(description="The tool's main input, or nothing")
    asked: str = Field(description="What the tool was asked")


class CopilotStepResult(BaseModel):
    status: Literal[CardStatus.DONE, CardStatus.REFUSED, CardStatus.FAILED]
    answer: str | None = Field(description="What came back, or null")
    reason: str | None = Field(description="Why it was refused or failed, or null")
    sources: list[Source] = Field(
        description="The context files an answer came from, and none otherwise"
    )


class TurnFinishRequest(BaseModel):
    answer: str = Field(min_length=1)
    model_calls: int = Field(ge=0)
    cost: float = Field(ge=0, description="In US dollars, as OpenRouter reports it")


class PauseRequest(BaseModel):
    case_id: str = Field(description="The case the sign-off waits on")


class TurnFailureRequest(BaseModel):
    reason: str = Field(min_length=1, description="What went wrong")


# Customers, as the Copilot finds them.


class CustomerMatch(BaseModel):
    customer_id: str
    name: str


class Customer(CustomerMatch):
    """Who a customer is, without their contact details or date of birth, their
    contracts, their earlier cases and their cases in our queue."""

    customer_since: str
    contracts: list[Contract]
    earlier_cases: list[PreviousCase]
    cases_in_the_queue: list[CaseSummary]


class SignOffs(BaseModel):
    """The queue's approvals a Gateway held, and how many a worker signed off."""

    held: int
    signed_off: int


class RunStarted(Accepted):
    """A dispatch or an evaluation a worker started, which the agent works."""

    run_id: str
    number: int
