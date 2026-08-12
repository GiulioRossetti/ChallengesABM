"""Baseline scenario.

This example uses the default Beta priors, a modest seed count, and a small
rewired network to show the model with its standard configuration.
"""

from pathlib import Path
from _bootstrap import bootstrap_project_root

import networkx as nx

bootstrap_project_root()

from challengeabm import ChallengeABM
from challengeabm.config import SimulationConfig


def main() -> None:
    graph = nx.watts_strogatz_graph(n=120, k=8, p=0.08, seed=42)
    model = ChallengeABM(
        peer_network=graph,
        config=SimulationConfig(steps=60, seed_count=4, random_seed=42),
    )
    result = model.run()

    print("Baseline scenario")
    print(f"final_reach={result.final_reach:.3f}")
    print(f"peak_participants={result.peak_participants}")
    print(f"large_cascade={result.large_cascade}")

    output_dir = Path("artifacts")
    output_dir.mkdir(exist_ok=True)
    model_path = output_dir / "baseline_default_summary.txt"
    model_path.write_text(
        "\n".join(
            [
                "Baseline scenario",
                f"final_reach={result.final_reach:.3f}",
                f"peak_participants={result.peak_participants}",
                f"large_cascade={result.large_cascade}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
