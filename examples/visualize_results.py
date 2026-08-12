"""Exploratory visualization scenario.

This example runs a small baseline simulation and exports the standard plots so
you can inspect the model dynamics from multiple angles.
"""

from pathlib import Path
from _bootstrap import bootstrap_project_root

import matplotlib.pyplot as plt
import networkx as nx

bootstrap_project_root()

from challengeabm import ChallengeABM
from challengeabm.viz import (
    create_dashboard,
    plot_agent_state_matrix,
    plot_network_snapshot,
    plot_state_density_matrix,
    plot_state_trends,
)


def main() -> None:
    output_dir = Path(__file__).resolve().parents[1] / "artifacts"
    output_dir.mkdir(exist_ok=True)

    graph = nx.watts_strogatz_graph(n=80, k=8, p=0.1, seed=42)
    model = ChallengeABM(peer_network=graph)
    result = model.run(steps=50)

    plot_state_trends(result).savefig(output_dir / "state_trends.png", dpi=180, bbox_inches="tight")
    plot_state_density_matrix(result).savefig(output_dir / "state_density_matrix.png", dpi=180, bbox_inches="tight")
    plot_agent_state_matrix(model).savefig(output_dir / "agent_state_matrix.png", dpi=180, bbox_inches="tight")
    plot_network_snapshot(model).savefig(output_dir / "network_snapshot.png", dpi=180, bbox_inches="tight")
    create_dashboard(model, result).savefig(output_dir / "dashboard.png", dpi=180, bbox_inches="tight")

    plt.close("all")


if __name__ == "__main__":
    main()
