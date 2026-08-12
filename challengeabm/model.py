"""Main ChallengeABM simulation engine."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from collections.abc import Hashable, Sequence
from typing import Optional

import networkx as nx

from .agent import Agent
from .challenge import Challenge
from .config import DistributionSpec, SimulationConfig, TransitionParameters
from .metrics import SimulationResult, count_states, participating_cluster_size
from .network import prepare_custom_network
from .states import State


def sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-value))


def clamp_probability(value: float) -> float:
    return max(0.0, min(1.0, value))


@dataclass
class ChallengeABM:
    """Synchronous agent-based model of challenge diffusion."""

    peer_network: nx.Graph
    infected_nodes: Optional[Sequence[Hashable]] = None
    config: SimulationConfig = SimulationConfig()
    challenge: Challenge = Challenge(appeal=0.55, severity=0.65)

    def __post_init__(self) -> None:
        self.rng = random.Random(self.config.random_seed)
        self._state_counts_history: list[dict[str, int]] = []
        self.graph = prepare_custom_network(self.peer_network)
        self.node_labels = list(self.graph.nodes())
        self.node_to_agent_index = {node_label: index for index, node_label in enumerate(self.node_labels)}
        self.n_agents = len(self.node_labels)
        self.agents = self._build_agents()
        self.seed_nodes = self._initial_seed_nodes()
        self._seed_initial_observers(self.seed_nodes)
        self._record_current_states()

    def _build_agents(self) -> list[Agent]:
        agents: list[Agent] = []
        for agent_id in range(self.n_agents):
            agents.append(
                Agent(
                    agent_id=agent_id,
                    susceptibility=self._sample_distribution(self.config.trait_distributions.susceptibility),
                    conformity=self._sample_distribution(self.config.trait_distributions.conformity),
                    risk_aversion=self._sample_distribution(self.config.trait_distributions.risk_aversion),
                    share_tendency=self._sample_distribution(self.config.trait_distributions.share_tendency),
                )
            )
        return agents

    def _sample_distribution(self, spec: DistributionSpec) -> float:
        kind = spec.kind.lower().strip()
        params = spec.parameters
        if kind == "beta":
            if len(params) != 2:
                raise ValueError("beta distribution requires exactly 2 parameters: alpha, beta")
            value = self.rng.betavariate(params[0], params[1])
        elif kind == "uniform":
            if len(params) != 2:
                raise ValueError("uniform distribution requires exactly 2 parameters: low, high")
            value = self.rng.uniform(params[0], params[1])
        elif kind == "triangular":
            if len(params) == 2:
                low, high = params
                mode = (low + high) / 2.0
            elif len(params) == 3:
                low, high, mode = params
            else:
                raise ValueError("triangular distribution requires 2 or 3 parameters: low, high[, mode]")
            value = self.rng.triangular(low, high, mode)
        elif kind == "normal":
            if len(params) != 2:
                raise ValueError("normal distribution requires exactly 2 parameters: mu, sigma")
            value = self.rng.normalvariate(params[0], params[1])
        elif kind == "gamma":
            if len(params) != 2:
                raise ValueError("gamma distribution requires exactly 2 parameters: alpha, beta")
            value = self.rng.gammavariate(params[0], params[1])
        elif kind == "lognormal":
            if len(params) != 2:
                raise ValueError("lognormal distribution requires exactly 2 parameters: mu, sigma")
            value = self.rng.lognormvariate(params[0], params[1])
        else:
            raise ValueError(f"Unsupported trait distribution kind: {spec.kind!r}")

        if spec.clip:
            value = max(0.0, min(1.0, value))
        return value

    def _seed_initial_observers(self, seed_nodes: Sequence[Hashable]) -> None:
        for node_label in seed_nodes:
            agent = self.agents[self.node_to_agent_index[node_label]]
            agent.state = State.OBSERVING
            agent.ever_exposed = True
            agent.time_of_entry = 0

    def _initial_seed_nodes(self) -> list[Hashable]:
        if self.infected_nodes is not None:
            return self._normalize_infected_nodes(self.infected_nodes)
        seed_count = min(self.config.seed_count, self.n_agents)
        return self.rng.sample(self.node_labels, seed_count)

    def _normalize_infected_nodes(self, infected_nodes: Sequence[Hashable]) -> list[Hashable]:
        normalized: list[Hashable] = []
        seen: set[Hashable] = set()
        for node in infected_nodes:
            if node not in self.node_to_agent_index:
                raise ValueError(f"infected node {node!r} is not present in the provided graph")
            if node not in seen:
                normalized.append(node)
                seen.add(node)
        return normalized

    def _neighbor_weights(self, node_label: Hashable) -> float:
        total = 0.0
        for neighbor in self.graph.neighbors(node_label):
            total += self.graph[node_label][neighbor]["weight"]
        return total

    def _weighted_fraction(self, node_label: Hashable, target_states: set[State]) -> float:
        total_weight = self._neighbor_weights(node_label)
        if total_weight == 0:
            return 0.0
        numerator = 0.0
        for neighbor in self.graph.neighbors(node_label):
            neighbor_index = self.node_to_agent_index[neighbor]
            if self.agents[neighbor_index].state in target_states:
                numerator += self.graph[node_label][neighbor]["weight"]
        return numerator / total_weight

    def _exposure(self, node_label: Hashable) -> tuple[float, float, float]:
        exposure_participating = self._weighted_fraction(node_label, {State.PARTICIPATING})
        exposure_amplifying = self._weighted_fraction(node_label, {State.AMPLIFYING})
        exposure_counteracting = self._weighted_fraction(node_label, {State.COUNTERACTING})
        return exposure_participating, exposure_amplifying, exposure_counteracting

    def awareness_probability(self, exposure_participating: float, exposure_amplifying: float) -> float:
        params = self.config.transition
        return clamp_probability(1.0 - math.exp(-params.awareness_lambda * (exposure_participating + exposure_amplifying)))

    def effective_exposure(self, exposure_participating: float, exposure_amplifying: float, exposure_counteracting: float) -> float:
        raw_exposure = exposure_participating + exposure_amplifying
        return max(0.0, raw_exposure - self.config.transition.counter_effectiveness * exposure_counteracting)

    def participation_probability(self, agent: Agent, effective_exposure: float) -> float:
        params = self.config.transition
        score = (
            params.participation_intercept
            + params.participation_appeal * self.challenge.appeal
            + params.participation_susceptibility * agent.susceptibility * effective_exposure
            + params.participation_conformity * agent.conformity * effective_exposure
            - params.participation_risk * agent.risk_aversion * self.challenge.severity
        )
        return sigmoid(score)

    def counter_probability(self, agent: Agent, effective_exposure: float) -> float:
        params = self.config.transition
        score = (
            params.counter_intercept
            + params.counter_risk * agent.risk_aversion * self.challenge.severity
            + params.counter_exposure * effective_exposure
        )
        return sigmoid(score)

    def amplification_probability(self, agent: Agent, effective_exposure: float) -> float:
        params = self.config.transition
        score = (
            params.amplification_intercept
            + params.amplification_share * agent.share_tendency
            + params.amplification_exposure * effective_exposure
            + params.amplification_conformity * agent.conformity
        )
        return sigmoid(score)

    def dropout_probability(self, agent: Agent, effective_exposure: float) -> float:
        params = self.config.transition
        score = (
            params.dropout_intercept
            + params.dropout_risk * agent.risk_aversion * self.challenge.severity
            - params.dropout_exposure * effective_exposure
        )
        return clamp_probability(params.spontaneous_dropout + sigmoid(score))

    def _sample_observer_transition(self, agent: Agent, effective_exposure: float) -> State:
        p_counter = self.counter_probability(agent, effective_exposure)
        p_participate = self.participation_probability(agent, effective_exposure)
        roll = self.rng.random()
        if roll < p_counter:
            return State.COUNTERACTING
        if roll < p_counter + p_participate:
            return State.PARTICIPATING
        return State.OBSERVING

    def _sample_participant_transition(self, agent: Agent, effective_exposure: float) -> State:
        p_dropout = self.dropout_probability(agent, effective_exposure)
        p_amplify = self.amplification_probability(agent, effective_exposure)
        roll = self.rng.random()
        if roll < p_dropout:
            return State.DROPPED_OUT
        if roll < p_dropout + p_amplify:
            return State.AMPLIFYING
        return State.PARTICIPATING

    def _sample_amplifying_transition(self, agent: Agent, effective_exposure: float) -> State:
        p_dropout = self.dropout_probability(agent, effective_exposure)
        if self.rng.random() < p_dropout:
            return State.DROPPED_OUT
        return State.AMPLIFYING

    def _sample_counteracting_transition(self, agent: Agent) -> State:
        return State.COUNTERACTING

    def _record_current_states(self) -> None:
        for agent in self.agents:
            agent.record_state()
        self._state_counts_history.append(count_states([agent.state for agent in self.agents]))

    def step(self, time_index: int) -> None:
        next_states: list[State] = [agent.state for agent in self.agents]

        for agent in self.agents:
            node_label = self.node_labels[agent.agent_id]
            exposure_participating, exposure_amplifying, exposure_counteracting = self._exposure(node_label)
            effective_exposure = self.effective_exposure(
                exposure_participating,
                exposure_amplifying,
                exposure_counteracting,
            )

            if agent.state == State.UNAWARE:
                if exposure_amplifying > 0.0:
                    next_states[agent.agent_id] = State.OBSERVING
                    agent.ever_exposed = True
                else:
                    awareness = self.awareness_probability(exposure_participating, exposure_amplifying)
                    if self.rng.random() < awareness:
                        next_states[agent.agent_id] = State.OBSERVING
                        agent.ever_exposed = True

            elif agent.state == State.OBSERVING:
                next_states[agent.agent_id] = self._sample_observer_transition(agent, effective_exposure)

            elif agent.state == State.PARTICIPATING:
                next_states[agent.agent_id] = self._sample_participant_transition(agent, effective_exposure)

            elif agent.state == State.AMPLIFYING:
                next_states[agent.agent_id] = self._sample_amplifying_transition(agent, effective_exposure)

            elif agent.state == State.COUNTERACTING:
                next_states[agent.agent_id] = self._sample_counteracting_transition(agent)

        for agent, new_state in zip(self.agents, next_states):
            if new_state != agent.state:
                if new_state == State.PARTICIPATING and not agent.ever_participated:
                    agent.ever_participated = True
                    agent.time_of_entry = time_index + 1 if agent.time_of_entry is None else agent.time_of_entry
                if new_state == State.AMPLIFYING:
                    agent.ever_amplified = True
                    if agent.time_of_entry is None:
                        agent.time_of_entry = time_index + 1
                if new_state == State.COUNTERACTING:
                    agent.ever_counteracted = True
                    if agent.time_of_entry is None:
                        agent.time_of_entry = time_index + 1
                if new_state == State.DROPPED_OUT:
                    agent.ever_dropped_out = True
                    agent.time_of_exit = time_index + 1
            agent.state = new_state
            agent.record_state()

        self._state_counts_history.append(count_states([agent.state for agent in self.agents]))

    def run(self, steps: Optional[int] = None) -> SimulationResult:
        total_steps = self.config.steps if steps is None else steps
        for time_index in range(total_steps):
            self.step(time_index)

        return self._build_result(total_steps)

    def _build_result(self, time_steps: int) -> SimulationResult:
        states = [agent.state for agent in self.agents]
        ever_participated = sum(agent.ever_participated or agent.ever_amplified for agent in self.agents)
        ever_amplified = sum(agent.ever_amplified for agent in self.agents)
        ever_counteracted = sum(agent.ever_counteracted for agent in self.agents)
        ever_dropped_out = sum(agent.ever_dropped_out for agent in self.agents)
        ever_exposed = sum(agent.ever_exposed for agent in self.agents)

        participant_counts = [
            snapshot.get(State.PARTICIPATING.value, 0) + snapshot.get(State.AMPLIFYING.value, 0)
            for snapshot in self._state_counts_history
        ]
        if participant_counts:
            peak_participants = max(participant_counts)
            time_of_peak = participant_counts.index(peak_participants)
            cascade_duration = sum(1 for value in participant_counts if value > 0)
        else:
            peak_participants = 0
            time_of_peak = 0
            cascade_duration = 0

        final_reach = ever_participated / self.n_agents if self.n_agents else 0.0
        large_cascade = final_reach > self.config.large_cascade_threshold
        largest_cluster = participating_cluster_size(self.graph, states, self.node_labels)

        return SimulationResult(
            time_steps=time_steps,
            state_counts=list(self._state_counts_history),
            ever_exposed=ever_exposed,
            ever_participated=ever_participated,
            ever_amplified=ever_amplified,
            ever_counteracted=ever_counteracted,
            ever_dropped_out=ever_dropped_out,
            peak_participants=peak_participants,
            time_of_peak_participation=time_of_peak,
            cascade_duration=cascade_duration,
            largest_participating_cluster=largest_cluster,
            final_reach=final_reach,
            large_cascade=large_cascade,
        )
