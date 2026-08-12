"""Challenge parameters."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Challenge:
    """Abstract representation of a risky online challenge."""

    appeal: float
    severity: float

