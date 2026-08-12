"""High-visibility cascade scenario.

This example models a challenge that is attractive, socially visible, and
easy to adopt. It uses stronger participation and amplification pressures to
illustrate a faster cascade.
"""

from pathlib import Path
from _bootstrap import bootstrap_project_root

import networkx as nx

bootstrap_project_root()

from challengeabm import Challenge, ChallengeABM
from challengeabm.config import SimulationConfig, TransitionParameters


def main() -> None:
    graph = nx.barabasi_albert_graph(n=160, m=4, seed=7)
    config = SimulationConfig(
        steps=70,
        seed_count=6,
        random_seed=7,
        transition=TransitionParameters(
            awareness_lambda=3.0,
            participation_intercept=-1.2,
            participation_appeal=1.7,
            participation_susceptibility=3.8,
            participation_conformity=2.8,
            participation_risk=1.8,
            amplification_intercept=-1.0,
            amplification_share=2.6,
            amplification_exposure=2.0,
            amplification_conformity=1.4,
            dropout_intercept=-1.8,
            spontaneous_dropout=0.01,
        ),
    )
    model = ChallengeABM(
        peer_network=graph,
        config=config,
        challenge=Challenge(appeal=0.85, severity=0.35),
    )
    result = model.run()

    print("High-visibility cascade scenario")
    print(f"final_reach={result.final_reach:.3f}")
    print(f"peak_participants={result.peak_participants}")
    print(f"time_of_peak_participation={result.time_of_peak_participation}")

    output_dir = Path("artifacts")
    output_dir.mkdir(exist_ok=True)
    (output_dir / "high_visibility_cascade.txt").write_text(
        "\n".join(
            [
                "High-visibility cascade scenario",
                f"final_reach={result.final_reach:.3f}",
                f"peak_participants={result.peak_participants}",
                f"time_of_peak_participation={result.time_of_peak_participation}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
