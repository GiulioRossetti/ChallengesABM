"""Tests for the interactive dashboard backend."""

from __future__ import annotations

import unittest

from challengeabm.dashboard.server import create_network, default_dashboard_config, simulate_dashboard


class DashboardTests(unittest.TestCase):
    def test_dashboard_two_step_flow_returns_network_and_timeline(self) -> None:
        payload = default_dashboard_config()
        payload["topology"]["kind"] = "watts_strogatz"
        payload["topology"]["watts_strogatz"]["n"] = 20
        payload["topology"]["watts_strogatz"]["k"] = 4
        payload["topology"]["watts_strogatz"]["p"] = 0.1
        payload["simulation"]["steps"] = 5
        payload["simulation"]["seed_count"] = 2
        payload["simulation"]["random_seed"] = 7

        network_response = create_network(payload)
        self.assertIn("network", network_response)
        self.assertEqual(len(network_response["network"]["nodes"]), 20)

        payload["network"] = network_response["network"]
        payload["simulation"]["infected_nodes"] = [network_response["network"]["nodes"][0]["id"]]
        response = simulate_dashboard(payload)

        self.assertIn("network", response)
        self.assertIn("timeline", response)
        self.assertIn("ui", response)
        self.assertEqual(len(response["network"]["nodes"]), 20)
        self.assertEqual(len(response["timeline"]["node_histories"]), 20)
        self.assertEqual(len(response["timeline"]["state_counts"]), 6)
        self.assertEqual(response["ui"]["time_steps"], 5)

    def test_dashboard_supports_sbm_topology(self) -> None:
        payload = default_dashboard_config()
        payload["topology"] = {
            "kind": "sbm",
            "layout": "spring",
            "sizes": [8, 12],
            "probabilities": [[0.5, 0.05], [0.05, 0.4]],
        }
        payload["simulation"]["steps"] = 4
        payload["simulation"]["seed_count"] = 1
        payload["simulation"]["random_seed"] = 11

        network_response = create_network(payload)
        self.assertIn("network", network_response)
        self.assertEqual(len(network_response["network"]["nodes"]), 20)

        payload["network"] = network_response["network"]
        payload["simulation"]["infected_nodes"] = [network_response["network"]["nodes"][0]["id"]]
        response = simulate_dashboard(payload)

        self.assertIn("timeline", response)
        self.assertEqual(len(response["network"]["nodes"]), 20)
        self.assertEqual(len(response["timeline"]["node_histories"]), 20)


if __name__ == "__main__":
    unittest.main()
