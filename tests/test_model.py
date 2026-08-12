import unittest

import networkx as nx

from challengeabm import AgentTraitDistributions, Challenge, ChallengeABM, DistributionSpec, State
from challengeabm.config import SimulationConfig, TransitionParameters


class ChallengeABMTests(unittest.TestCase):
    def test_model_initializes_with_seeds(self) -> None:
        graph = nx.path_graph(20)
        config = SimulationConfig(seed_count=4, steps=0, random_seed=7)
        model = ChallengeABM(peer_network=graph, config=config, challenge=Challenge(appeal=0.55, severity=0.65))

        observed = sum(agent.state == State.OBSERVING for agent in model.agents)
        self.assertEqual(observed, 4)

    def test_probabilities_are_bounded(self) -> None:
        config = SimulationConfig(seed_count=2, steps=0, random_seed=2)
        model = ChallengeABM(peer_network=nx.path_graph(12), config=config)
        agent = model.agents[0]
        p1 = model.participation_probability(agent, 0.7)
        p2 = model.counter_probability(agent, 0.7)
        p3 = model.amplification_probability(agent, 0.7)
        p4 = model.dropout_probability(agent, 0.7)
        for probability in (p1, p2, p3, p4):
            self.assertGreaterEqual(probability, 0.0)
            self.assertLessEqual(probability, 1.0)

    def test_run_returns_result(self) -> None:
        config = SimulationConfig(seed_count=3, steps=6, random_seed=11)
        model = ChallengeABM(peer_network=nx.watts_strogatz_graph(40, 4, 0.1, seed=11), config=config)
        result = model.run()

        self.assertEqual(result.time_steps, 6)
        self.assertGreaterEqual(result.final_reach, 0.0)
        self.assertLessEqual(result.final_reach, 1.0)
        self.assertIn("U", result.state_counts[0])

    def test_model_accepts_custom_networkx_graph(self) -> None:
        custom_graph = nx.Graph()
        custom_graph.add_edge("alice", "bob", weight=0.8)
        custom_graph.add_edge("bob", "carol")
        custom_graph.add_edge("carol", "diana", weight=0.4)

        config = SimulationConfig(seed_count=2, steps=1, random_seed=21)
        model = ChallengeABM(config=config, peer_network=custom_graph)

        self.assertEqual(model.graph.number_of_nodes(), 4)
        self.assertEqual(set(model.graph.nodes()), {0, 1, 2, 3})
        self.assertEqual(model.n_agents, 4)
        self.assertEqual(model.graph[0][1]["weight"], 0.8)
        self.assertEqual(model.graph[1][2]["weight"], 1.0)
        self.assertEqual(model.graph[2][3]["weight"], 0.4)

        result = model.run()
        self.assertEqual(result.time_steps, 1)
        self.assertLessEqual(result.final_reach, 1.0)

    def test_model_accepts_explicit_infected_nodes(self) -> None:
        graph = nx.path_graph(["a", "b", "c", "d", "e"])
        config = SimulationConfig(seed_count=1, steps=0, random_seed=5)
        model = ChallengeABM(peer_network=graph, infected_nodes=["b", "d"], config=config)

        observed = [agent.agent_id for agent in model.agents if agent.state == State.OBSERVING]
        self.assertEqual(len(observed), 2)
        self.assertEqual(sum(agent.ever_exposed for agent in model.agents), 2)

        original_labels = {data["original_label"] for _, data in model.graph.nodes(data=True)}
        self.assertEqual(original_labels, {"a", "b", "c", "d", "e"})

    def test_model_uses_custom_trait_distributions(self) -> None:
        graph = nx.path_graph(8)
        trait_distributions = AgentTraitDistributions(
            susceptibility=DistributionSpec(kind="uniform", parameters=(0.8, 0.8)),
            conformity=DistributionSpec(kind="triangular", parameters=(0.6, 0.6), clip=True),
            risk_aversion=DistributionSpec(kind="beta", parameters=(1.0, 1.0)),
            share_tendency=DistributionSpec(kind="normal", parameters=(0.4, 0.0), clip=True),
        )
        config = SimulationConfig(seed_count=1, steps=0, random_seed=3, trait_distributions=trait_distributions)
        model = ChallengeABM(peer_network=graph, config=config)

        for agent in model.agents:
            self.assertEqual(agent.susceptibility, 0.8)
            self.assertEqual(agent.conformity, 0.6)
            self.assertEqual(agent.share_tendency, 0.4)
            self.assertGreaterEqual(agent.risk_aversion, 0.0)
            self.assertLessEqual(agent.risk_aversion, 1.0)

    def test_counteraction_and_dropout_states_are_reachable(self) -> None:
        transition = TransitionParameters(
            awareness_lambda=5.0,
            participation_intercept=4.0,
            counter_intercept=-3.0,
            dropout_intercept=-3.0,
        )
        config = SimulationConfig(
            seed_count=5,
            steps=5,
            random_seed=13,
            transition=transition,
        )
        model = ChallengeABM(peer_network=nx.cycle_graph(30), config=config)
        model.run()

        states = {agent.state for agent in model.agents}
        self.assertTrue(State.PARTICIPATING in states or State.AMPLIFYING in states)


if __name__ == "__main__":
    unittest.main()
