# Usage

## Create a Model

```python
import networkx as nx

from challengeabm import ChallengeABM
from challengeabm.config import SimulationConfig

graph = nx.barabasi_albert_graph(n=200, m=4, seed=7)

model = ChallengeABM(
    peer_network=graph,
    config=SimulationConfig(seed_count=4, steps=50, random_seed=7),
)
```

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

Use this when you want the initial population to reflect a different prior than the default Beta draws.

## Choose Initial Infected Nodes

```python
graph = nx.path_graph(["a", "b", "c", "d", "e"])

model = ChallengeABM(
    peer_network=graph,
    infected_nodes=["b", "d"],
    config=SimulationConfig(steps=25),
)
```

When `infected_nodes` is provided:

- the listed nodes start in the observing state;
- `seed_count` is ignored for initial seeding;
- the node labels should match the original labels from your graph.

## Run the Simulation

```python
result = model.run()
print(result.final_reach)
print(result.peak_participants)
```

## Inspect the Result

```python
print(result.state_counts[-1])
print(result.large_cascade)
print(result.largest_participating_cluster)
```

## Use a Custom Challenge

```python
from challengeabm import Challenge

model = ChallengeABM(
    peer_network=graph,
    challenge=Challenge(appeal=0.7, severity=0.4),
)
```

## Visualize the Run

```python
from challengeabm.viz import create_dashboard, plot_state_trends

plot_state_trends(result).savefig("state_trends.png", dpi=180, bbox_inches="tight")
create_dashboard(model, result).savefig("dashboard.png", dpi=180, bbox_inches="tight")
```

## Reproducibility

Set `random_seed` in `SimulationConfig` to reproduce the same random draws for:

- agent trait generation;
- seed selection;
- explicit infected-node selection when used;
- stochastic transitions.

See the scripts under `examples/` for runnable presets that combine these options in small scenarios.

If you want to explore the model interactively, launch the local dashboard from `python -m challengeabm.dashboard.server` and use the browser controls to configure the run and replay the stored timeline.
