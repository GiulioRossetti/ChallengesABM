"""ChallengeABM package."""

from .agent import Agent
from .challenge import Challenge
from .config import AgentTraitDistributions, DistributionSpec, SimulationConfig, TransitionParameters
from .model import ChallengeABM, SimulationResult
from .states import State
from .viz import (
    create_dashboard,
    plot_agent_state_matrix,
    plot_network_snapshot,
    plot_state_density_matrix,
    plot_state_trends,
)

__all__ = [
    "Agent",
    "Challenge",
    "ChallengeABM",
    "AgentTraitDistributions",
    "create_dashboard",
    "DistributionSpec",
    "plot_agent_state_matrix",
    "plot_network_snapshot",
    "plot_state_density_matrix",
    "plot_state_trends",
    "SimulationConfig",
    "SimulationResult",
    "TransitionParameters",
    "State",
]
