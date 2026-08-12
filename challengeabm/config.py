"""Configuration objects and defaults."""

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class DistributionSpec:
    """Description of a one-dimensional random distribution."""

    kind: str = "beta"
    parameters: Tuple[float, ...] = (2.0, 2.0)
    clip: bool = True


@dataclass(frozen=True)
class AgentTraitDistributions:
    """Random distributions used to generate stable agent traits."""

    susceptibility: DistributionSpec = DistributionSpec(kind="beta", parameters=(2.0, 2.0))
    conformity: DistributionSpec = DistributionSpec(kind="beta", parameters=(2.0, 2.0))
    risk_aversion: DistributionSpec = DistributionSpec(kind="beta", parameters=(3.0, 2.0))
    share_tendency: DistributionSpec = DistributionSpec(kind="beta", parameters=(2.0, 3.0))


@dataclass(frozen=True)
class TransitionParameters:
    awareness_lambda: float = 2.0
    participation_intercept: float = -2.0
    participation_appeal: float = 1.0
    participation_susceptibility: float = 3.0
    participation_conformity: float = 2.0
    participation_risk: float = 2.5
    amplification_intercept: float = -1.5
    amplification_share: float = 2.0
    amplification_exposure: float = 1.5
    amplification_conformity: float = 1.0
    counter_intercept: float = -1.0
    counter_risk: float = 2.0
    counter_exposure: float = 2.0
    counter_effectiveness: float = 0.5
    dropout_intercept: float = -1.2
    dropout_risk: float = 2.0
    dropout_exposure: float = 2.0
    spontaneous_dropout: float = 0.02


@dataclass(frozen=True)
class SimulationConfig:
    steps: int = 100
    seed_count: int = 3
    large_cascade_threshold: float = 0.10
    random_seed: Optional[int] = None
    transition: TransitionParameters = TransitionParameters()
    trait_distributions: AgentTraitDistributions = AgentTraitDistributions()
