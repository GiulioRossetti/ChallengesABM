"""Defensive counteraction scenario.

This example models a risky challenge in a network where observers are more
likely to resist or denounce the challenge than to adopt it.
"""

from pathlib import Path
from _bootstrap import bootstrap_project_root

import networkx as nx

bootstrap_project_root()

from challengeabm import Challenge, ChallengeABM
from challengeabm.config import SimulationConfig, TransitionParameters


def main() -> None:
    graph = nx.watts_strogatz_graph(n=140, k=10, p=0.05, seed=21)
    config = SimulationConfig(
        steps=70,
        seed_count=5,
        random_seed=21,
        transition=TransitionParameters(
            awareness_lambda=1.8,
            participation_intercept=-3.0,
            participation_appeal=0.8,
            participation_susceptibility=2.0,
            participation_conformity=1.5,
            participation_risk=4.0,
            counter_intercept=-0.2,
            counter_risk=3.5,
            counter_exposure=2.8,
            counter_effectiveness=0.9,
            dropout_intercept=-0.8,
            dropout_risk=3.0,
            dropout_exposure=1.0,
            spontaneous_dropout=0.04,
        ),
    )
    model = ChallengeABM(
        peer_network=graph,
        config=config,
        challenge=Challenge(appeal=0.45, severity=0.85),
    )
    result = model.run()

    print("Defensive counteraction scenario")
    print(f"final_reach={result.final_reach:.3f}")
    print(f"ever_counteracted={result.ever_counteracted}")
    print(f"ever_participated={result.ever_participated}")

    output_dir = Path("artifacts")
    output_dir.mkdir(exist_ok=True)
    (output_dir / "defensive_counteraction.txt").write_text(
        "\n".join(
            [
                "Defensive counteraction scenario",
                f"final_reach={result.final_reach:.3f}",
                f"ever_counteracted={result.ever_counteracted}",
                f"ever_participated={result.ever_participated}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
