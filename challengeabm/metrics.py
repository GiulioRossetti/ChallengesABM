"""Metrics and summaries for ChallengeABM runs."""

from __future__ import annotations

from dataclasses import dataclass, field

import networkx as nx

from .states import State


@dataclass
class SimulationResult:
    """Aggregate results produced by a simulation run."""

    time_steps: int
    state_counts: list[dict[str, int]] = field(default_factory=list)
    ever_exposed: int = 0
    ever_participated: int = 0
    ever_amplified: int = 0
    ever_counteracted: int = 0
    ever_dropped_out: int = 0
    peak_participants: int = 0
    time_of_peak_participation: int = 0
    cascade_duration: int = 0
    largest_participating_cluster: int = 0
    final_reach: float = 0.0
    large_cascade: bool = False


def count_states(states: list[State]) -> dict[str, int]:
    counts = {state.value: 0 for state in State}
    for state in states:
        counts[state.value] += 1
    return counts


def participating_cluster_size(graph: nx.Graph, states: list[State]) -> int:
    participating_nodes = {idx for idx, state in enumerate(states) if state in {State.PARTICIPATING, State.AMPLIFYING}}
    if not participating_nodes:
        return 0

    subgraph = graph.subgraph(participating_nodes)
    return max((len(component) for component in nx.connected_components(subgraph)), default=0)
