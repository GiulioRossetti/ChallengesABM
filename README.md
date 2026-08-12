# ChallengeABM

ChallengeABM is an agent-based model for studying how a risky online challenge may diffuse through an adolescent peer network.

The interface is intentionally simple:

- build or provide a `networkx.Graph`;
- pass it to `ChallengeABM`;
- run the simulation;
- inspect outputs with the built-in metrics and visualization helpers.

## Installation

```bash
python -m pip install -e .
```

The package depends on `networkx`, `numpy`, and `matplotlib`.

## Compartmental Diagram

![ChallengeABM compartmental model](docs/assets/compartmental_model.png)

The figure summarizes the states and the main transition rules in one place. Read the arrows as one-step probabilistic updates evaluated synchronously from the previous state snapshot.

### Transition Legend

- `U -> O`: awareness. An unaware agent becomes observing when nearby `P` or `A` neighbors create enough exposure.
- `O -> P`: participation. An observing agent joins the challenge when challenge appeal, susceptibility, conformity, and local exposure outweigh risk aversion.
- `O -> C`: counteraction. An observing agent starts opposing the challenge when perceived risk and exposure make resistance more likely.
- `P -> A`: amplification. A participant becomes an amplifier when sharing tendency, conformity, and exposure favor public promotion.
- `P -> D`: dropout. A participant leaves the challenge when risk aversion, challenge severity, and low retention pressure push exit probability up.
- `A -> D`: dropout from amplification. Amplifiers can also leave the cascade under the same dropout logic used for participants.
- `C -> C`: counteracting is absorbing in the current implementation. Once an agent starts counteracting, it remains in that state.
- `D -> D`: dropped out is absorbing. Once an agent exits, it does not re-enter the cascade.

## Core API

### `ChallengeABM`

```python
ChallengeABM(
    peer_network: networkx.Graph,
    infected_nodes: Optional[Sequence[Hashable]] = None,
    config: SimulationConfig = SimulationConfig(...),
    challenge: Challenge = Challenge(appeal=0.55, severity=0.65),
)
```

`peer_network` is required. The graph is copied, relabeled internally to consecutive integer node ids, and used as the social network for the simulation.
`infected_nodes`, when provided, overrides random seeding and marks the listed nodes as the initial observing agents.

### `SimulationConfig`

```python
SimulationConfig(
    steps: int = 100,
    seed_count: int = 3,
    large_cascade_threshold: float = 0.10,
    random_seed: Optional[int] = None,
    transition: TransitionParameters = TransitionParameters(...),
    trait_distributions: AgentTraitDistributions = AgentTraitDistributions(...),
)
```

Use `trait_distributions` to replace the default Beta priors for each agent trait.

### `TransitionParameters`

The transition layer controls how the model reacts to local exposure:

- `awareness_lambda`
- `participation_intercept`
- `participation_appeal`
- `participation_susceptibility`
- `participation_conformity`
- `participation_risk`
- `amplification_intercept`
- `amplification_share`
- `amplification_exposure`
- `amplification_conformity`
- `counter_intercept`
- `counter_risk`
- `counter_exposure`
- `counter_effectiveness`
- `dropout_intercept`
- `dropout_risk`
- `dropout_exposure`
- `spontaneous_dropout`

## Quick Start

```python
import networkx as nx

from challengeabm import ChallengeABM
from challengeabm.config import SimulationConfig

graph = nx.watts_strogatz_graph(n=200, k=12, p=0.08, seed=42)

model = ChallengeABM(
    peer_network=graph,
    config=SimulationConfig(seed_count=3, steps=100, random_seed=42),
)

result = model.run()
print(result.final_reach)
print(result.peak_participants)
print(result.large_cascade)
```

For more complete examples, see the scripts under [examples/](/Users/rossetti/PycharmProjects/ChallengesABM/examples) and the short scenario descriptions in [examples/README.md](/Users/rossetti/PycharmProjects/ChallengesABM/examples/README.md).

## Working With Your Graph

If you already have a NetworkX graph, pass it directly to `ChallengeABM`.

```python
import networkx as nx

from challengeabm import ChallengeABM

graph = nx.barabasi_albert_graph(n=150, m=4, seed=7)
model = ChallengeABM(peer_network=graph, infected_nodes=[0, 4, 7])
```

The model will:

- normalize node labels to `0..N-1`;
- preserve edge weights when present;
- default missing edge weights to `1.0`;
- convert the graph to a simple undirected graph for the diffusion rules.

If `infected_nodes` is omitted, the model falls back to randomly selecting `seed_count` initial observing agents.

## Custom Trait Distributions

```python
from challengeabm import AgentTraitDistributions, ChallengeABM, DistributionSpec
from challengeabm.config import SimulationConfig

trait_distributions = AgentTraitDistributions(
    susceptibility=DistributionSpec(kind="uniform", parameters=(0.2, 0.9)),
    conformity=DistributionSpec(kind="triangular", parameters=(0.1, 0.8, 0.6)),
    risk_aversion=DistributionSpec(kind="beta", parameters=(3.0, 2.0)),
    share_tendency=DistributionSpec(kind="normal", parameters=(0.55, 0.12), clip=True),
)

model = ChallengeABM(
    peer_network=graph,
    config=SimulationConfig(trait_distributions=trait_distributions),
)
```

## Visualization

The package includes helpers to inspect simulation results:

- `plot_state_trends(result)`
- `plot_state_density_matrix(result)`
- `plot_agent_state_matrix(model)`
- `plot_network_snapshot(model)`
- `create_dashboard(model, result)`

```python
from challengeabm import ChallengeABM
from challengeabm.viz import create_dashboard, plot_state_trends

model = ChallengeABM(peer_network=graph)
result = model.run(steps=50)

plot_state_trends(result).savefig("state_trends.png", dpi=180, bbox_inches="tight")
create_dashboard(model, result).savefig("dashboard.png", dpi=180, bbox_inches="tight")
```

## Simulation Output

`ChallengeABM.run()` returns a `SimulationResult` with:

- `time_steps`
- `state_counts`
- `ever_exposed`
- `ever_participated`
- `ever_amplified`
- `ever_counteracted`
- `ever_dropped_out`
- `peak_participants`
- `time_of_peak_participation`
- `cascade_duration`
- `largest_participating_cluster`
- `final_reach`
- `large_cascade`

## Documentation

- [Usage guide](docs/usage.md)
- [API reference](docs/api.md)
- [Model notes](docs/model.md)
- [Visualization guide](docs/visualization.md)
