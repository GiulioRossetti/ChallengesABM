"""Agent definition for the ChallengeABM model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .states import State


@dataclass
class Agent:
    """An adolescent agent with stable behavioral traits."""

    agent_id: int
    susceptibility: float
    conformity: float
    risk_aversion: float
    share_tendency: float
    state: State = State.UNAWARE
    ever_exposed: bool = False
    ever_participated: bool = False
    ever_amplified: bool = False
    ever_counteracted: bool = False
    ever_dropped_out: bool = False
    time_of_entry: Optional[int] = None
    time_of_exit: Optional[int] = None
    history: list[State] = field(default_factory=list)

    def record_state(self) -> None:
        self.history.append(self.state)
