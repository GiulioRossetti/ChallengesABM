"""Visualization presets for contrasting network structures.

This example compares the same simulation settings on two different network
topologies: a highly clustered small-world graph and a sparse random graph.
It saves the standard dashboard for each case so you can inspect how network
structure changes the diffusion pattern.
"""

from pathlib import Path

from _bootstrap import bootstrap_project_root

import matplotlib.pyplot as plt
import networkx as nx

bootstrap_project_root()

from challengeabm import ChallengeABM
from challengeabm.config import SimulationConfig
from challengeabm.viz import create_dashboard


def run_case(name: str, graph: nx.Graph, output_dir: Path) -> None:
    model = ChallengeABM(
        peer_network=graph,
        config=SimulationConfig(steps=60, seed_count=4, random_seed=123),
    )
    result = model.run()
    figure = create_dashboard(model, result)
    figure.suptitle(f"{name}: ChallengeABM simulation dashboard", fontsize=16, fontweight="bold")
    figure.savefig(output_dir / f"{name}_dashboard.png", dpi=180, bbox_inches="tight")
    plt.close(figure)

    print(f"{name}")
    print(f"final_reach={result.final_reach:.3f}")
    print(f"peak_participants={result.peak_participants}")


def main() -> None:
    output_dir = Path("artifacts")
    output_dir.mkdir(exist_ok=True)

    clustered_graph = nx.watts_strogatz_graph(n=140, k=12, p=0.04, seed=123)
    sparse_graph = nx.erdos_renyi_graph(n=140, p=0.035, seed=123)

    run_case("clustered_network", clustered_graph, output_dir)
    run_case("sparse_random_graph", sparse_graph, output_dir)


if __name__ == "__main__":
    main()
