# Visualization

ChallengeABM includes plotting helpers that summarize different scales of the simulation.

## Available Plots

- `plot_state_trends(result)`: state counts over time as line plots.
- `plot_state_density_matrix(result)`: state-by-time heatmap.
- `plot_agent_state_matrix(model)`: agent-by-time trajectory heatmap.
- `plot_network_snapshot(model)`: current peer network colored by agent state.
- `create_dashboard(model, result)`: combined summary figure.

## Example

```python
import networkx as nx

from challengeabm import ChallengeABM
from challengeabm.viz import (
    create_dashboard,
    plot_agent_state_matrix,
    plot_network_snapshot,
    plot_state_density_matrix,
    plot_state_trends,
)

graph = nx.watts_strogatz_graph(n=120, k=8, p=0.12, seed=42)
model = ChallengeABM(peer_network=graph)
result = model.run(steps=50)

plot_state_trends(result).savefig("state_trends.png", dpi=180, bbox_inches="tight")
plot_state_density_matrix(result).savefig("state_density_matrix.png", dpi=180, bbox_inches="tight")
plot_agent_state_matrix(model).savefig("agent_state_matrix.png", dpi=180, bbox_inches="tight")
plot_network_snapshot(model).savefig("network_snapshot.png", dpi=180, bbox_inches="tight")
create_dashboard(model, result).savefig("dashboard.png", dpi=180, bbox_inches="tight")
```

## Interpreting the Figures

- Trends show whether the challenge stayed local or grew into a cascade.
- Density matrices make phase shifts easier to spot across time.
- Agent-state matrices show whether a few agents drive the cascade or whether it spreads broadly.
- Network snapshots show where the active states sit in the peer structure.

For large simulations, the network snapshot and dashboard are usually the fastest first pass.
