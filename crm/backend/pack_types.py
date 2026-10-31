"""The pack-shaped types the engine carries: the plan and award family.

The active pack declares their meaning; the engine carries them as plain
pydantic containers so the routes and the tools have one import source.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Benefit = str
LineKind = Literal[
    "item", "electronics", "cash", "expense", "hotel", "meals_without_receipts"
]


class Plan(BaseModel):
    """A plan of the active pack. The benefit maxima are the insurance pack's;
    another pack declares its own fields, which its rules module reads."""

    model_config = ConfigDict(extra="allow")

    plan: str
    name: str
    per_item_limit: float = 0.0
    deductible: float = 0.0


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
