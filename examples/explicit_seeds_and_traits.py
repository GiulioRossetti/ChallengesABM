"""Explicit seeds and custom trait priors scenario.

This example shows how to start the simulation from user-chosen seed nodes and
how to replace the default Beta priors with a different trait configuration.
"""

from pathlib import Path
from _bootstrap import bootstrap_project_root

import networkx as nx

bootstrap_project_root()

from challengeabm import AgentTraitDistributions, ChallengeABM, DistributionSpec
from challengeabm.config import SimulationConfig


def main() -> None:
    graph = nx.path_graph(["a", "b", "c", "d", "e", "f", "g", "h"])
    trait_distributions = AgentTraitDistributions(
        susceptibility=DistributionSpec(kind="uniform", parameters=(0.3, 0.8)),
        conformity=DistributionSpec(kind="triangular", parameters=(0.2, 0.9, 0.65)),
        risk_aversion=DistributionSpec(kind="beta", parameters=(4.0, 2.5)),
        share_tendency=DistributionSpec(kind="normal", parameters=(0.55, 0.1), clip=True),
    )
    model = ChallengeABM(
        peer_network=graph,
        infected_nodes=["b", "f"],
        config=SimulationConfig(steps=40, random_seed=11, trait_distributions=trait_distributions),
    )
    result = model.run()

    print("Explicit seeds and custom trait priors scenario")
    print(f"initial_seed_nodes=['b', 'f']")
    print(f"final_reach={result.final_reach:.3f}")
    print(f"largest_participating_cluster={result.largest_participating_cluster}")

    output_dir = Path("artifacts")
    output_dir.mkdir(exist_ok=True)
    (output_dir / "explicit_seeds_and_traits.txt").write_text(
        "\n".join(
            [
                "Explicit seeds and custom trait priors scenario",
                "initial_seed_nodes=['b', 'f']",
                f"final_reach={result.final_reach:.3f}",
                f"largest_participating_cluster={result.largest_participating_cluster}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
