import unittest

import networkx as nx

from challengeabm.network import prepare_custom_network


class CustomNetworkTests(unittest.TestCase):
    def test_prepare_custom_network_relables_nodes_and_fills_weights(self) -> None:
        graph = nx.Graph()
        graph.add_edge("alice", "bob", weight=0.7)
        graph.add_edge("bob", "carol")
        graph.add_edge("carol", "diana", weight=0.4)

        prepared = prepare_custom_network(graph)

        self.assertEqual(prepared.number_of_nodes(), 4)
        self.assertEqual(set(prepared.nodes()), {0, 1, 2, 3})
        self.assertEqual(prepared[0][1]["weight"], 0.7)
        self.assertEqual(prepared[1][2]["weight"], 1.0)
        self.assertEqual(prepared[2][3]["weight"], 0.4)


if __name__ == "__main__":
    unittest.main()
