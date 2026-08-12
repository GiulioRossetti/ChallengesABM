# Dashboard

ChallengeABM ships with a local browser dashboard for interactive exploration of the model.

The dashboard follows a three-step workflow:

1. Create the network.
2. Configure the model and choose seed nodes by clicking the graph.
3. Run the simulation and replay the resulting dynamics in JavaScript.

## Launch

From the repository root:

```bash
python -m challengeabm.dashboard.server
```

If the project is installed, you can also use the console script:

```bash
challengeabm-dashboard
```

## Layout

The dashboard uses three main columns:

- left: network creation, model configuration, and simulation execution;
- center: playable network visualization plus time slider and trend/density plots;
- right: summary metrics and current state counts.

The advanced configuration area is collapsed by default and contains structured form controls for the transition parameters and trait-distribution settings.

## Interaction

The playback controls let you:

- create the graph before running the model;
- select seeds by clicking nodes in the network preview;
- run a new simulation with the current configuration;
- move backward or forward one step at a time;
- drag the slider to inspect any recorded timestep;
- play or pause the animation;
- change playback speed without recomputing the run.

Result plots stay hidden until a simulation has been executed. The network preview appears after the graph is created, and the current counts are color-coded with the same palette used in the graph view.

## Configuration

The dashboard accepts the same model objects as the Python API:

- `SimulationConfig`
- `Challenge`
- `TransitionParameters`
- `AgentTraitDistributions`
- explicit `infected_nodes` via clicked seed selection

For convenience, the dashboard exposes structured form groups for the transition and trait-distribution objects, so advanced settings can be edited safely without relying on raw JSON input.

## Network Presets

The current dashboard includes built-in topology presets for:

- Watts-Strogatz
- Erdos-Renyi
- Barabasi-Albert
- Newman-Watts-Strogatz
- path graph

The model itself still accepts any `networkx.Graph`, so the dashboard presets are only a convenience layer for interactive exploration.
