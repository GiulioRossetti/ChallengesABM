import unittest

import matplotlib
import networkx as nx

matplotlib.use("Agg")

from challengeabm import ChallengeABM
from challengeabm.viz import (
    create_dashboard,
    plot_agent_state_matrix,
    plot_network_snapshot,
    plot_state_density_matrix,
    plot_state_trends,
)


class VizTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model = ChallengeABM(peer_network=nx.path_graph(30))
        self.result = self.model.run(steps=5)

    def test_state_trends(self) -> None:
        fig = plot_state_trends(self.result)
        self.assertIsNotNone(fig)
        self.assertGreaterEqual(len(fig.axes), 1)

    def test_state_density_matrix(self) -> None:
        fig = plot_state_density_matrix(self.result)
        self.assertIsNotNone(fig)
        self.assertGreaterEqual(len(fig.axes), 2)

    def test_agent_state_matrix(self) -> None:
        fig = plot_agent_state_matrix(self.model)
        self.assertIsNotNone(fig)
        self.assertGreaterEqual(len(fig.axes), 2)

    def test_network_snapshot(self) -> None:
        fig = plot_network_snapshot(self.model)
        self.assertIsNotNone(fig)
        self.assertGreaterEqual(len(fig.axes), 1)

    def test_dashboard(self) -> None:
        fig = create_dashboard(self.model, self.result)
        self.assertIsNotNone(fig)
        self.assertGreaterEqual(len(fig.axes), 6)


if __name__ == "__main__":
    unittest.main()
