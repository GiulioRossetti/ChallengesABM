# API Reference

This page summarizes the public API and the configuration parameters that affect simulation behavior.

## Package Exports

```python
from challengeabm import (
    AgentTraitDistributions,
    Agent,
    Challenge,
    ChallengeABM,
    DistributionSpec,
    SimulationConfig,
    SimulationResult,
    State,
    TransitionParameters,
)
```

Visualization helpers are available from `challengeabm.viz`.

## `ChallengeABM`

Constructor:

```python
ChallengeABM(
    peer_network: nx.Graph,
    infected_nodes: Optional[Sequence[Hashable]] = None,
    config: SimulationConfig = SimulationConfig(...),
    challenge: Challenge = Challenge(appeal=0.55, severity=0.65),
)
```

### Parameters

| Parameter | Type | Recommended range | Effect | Interpretation |
|---|---|---:|---|---|
| `peer_network` | `networkx.Graph` | any simple graph | Defines who can influence whom. | The social network through which challenge exposure propagates. |
| `infected_nodes` | `Sequence[Hashable] \| None` | subset of graph node labels | Overrides random seeding and starts these nodes in `O` (observing). | Use when you want deterministic initial spreaders or externally chosen seed nodes. |
| `config` | `SimulationConfig` | see below | Controls simulation length, seeding fallback, and cascade threshold. | Global run settings. |
| `challenge` | `Challenge` | see below | Sets the challenge appeal and severity used in transition rules. | Abstract description of the challenge being studied. |

### Behavior

- If `infected_nodes` is provided, those nodes are initialized as observing agents.
- If `infected_nodes` is omitted, the model selects `seed_count` nodes at random.
- The input graph is copied and its original node labels are preserved.
- Missing edge weights default to `1.0`.

### Main Methods

- `run(steps: Optional[int] = None) -> SimulationResult`
- `step(time_index: int) -> None`
- `participation_probability(agent, effective_exposure) -> float`
- `counter_probability(agent, effective_exposure) -> float`
- `amplification_probability(agent, effective_exposure) -> float`
- `dropout_probability(agent, effective_exposure) -> float`

### Attributes

- `graph`: copy of the user-provided peer network with original node labels preserved.
- `agents`: list of `Agent` objects.
- `rng`: model random-number generator.

## `SimulationConfig`

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

### Parameters

| Parameter | Type | Recommended range | Effect | Interpretation |
|---|---|---:|---|---|
| `steps` | `int` | `1..` | Number of synchronous updates to run when `steps` is not passed to `run()`. | Simulation horizon. Larger values let slow cascades unfold. |
| `seed_count` | `int` | `0..N` | Number of randomly chosen initial observing agents when `infected_nodes` is not supplied. | Random seeding intensity. Higher values increase the chance of early diffusion. |
| `large_cascade_threshold` | `float` | `0..1` | Threshold used to set `large_cascade`. | Definition of what counts as a large cascade in terms of final reach. |
| `random_seed` | `int \| None` | any integer or `None` | Controls reproducibility of network-independent random draws. | Use to reproduce trait draws, random seed selection, and stochastic transitions. |
| `transition` | `TransitionParameters` | see below | Parameter bundle for behavioral transitions. | The behavioral “ruleset” of the model. |
| `trait_distributions` | `AgentTraitDistributions` | see below | Selects the random distributions used to generate agent traits. | How susceptibility, conformity, risk aversion, and sharing tendencies are initialized. |

## `Challenge`

```python
Challenge(
    appeal: float = 0.55,
    severity: float = 0.65,
)
```

### Parameters

| Parameter | Type | Recommended range | Effect | Interpretation |
|---|---|---:|---|---|
| `appeal` | `float` | `0..1` | Raises participation and amplification probabilities. | How attractive the challenge appears socially. |
| `severity` | `float` | `0..1` | Lowers participation and raises counteraction/dropout pressures. | How risky or harmful the challenge appears. |

### Notes

- Higher `appeal` makes adoption easier.
- Higher `severity` suppresses participation but increases protective responses and dropout.

## `TransitionParameters`

```python
TransitionParameters(
    awareness_lambda: float = 2.0,
    participation_intercept: float = -2.0,
    participation_appeal: float = 1.0,
    participation_susceptibility: float = 3.0,
    participation_conformity: float = 2.0,
    participation_risk: float = 2.5,
    amplification_intercept: float = -1.5,
    amplification_share: float = 2.0,
    amplification_exposure: float = 1.5,
    amplification_conformity: float = 1.0,
    counter_intercept: float = -1.0,
    counter_risk: float = 2.0,
    counter_exposure: float = 2.0,
    counter_effectiveness: float = 0.5,
    dropout_intercept: float = -1.2,
    dropout_risk: float = 2.0,
    dropout_exposure: float = 2.0,
    spontaneous_dropout: float = 0.02,
)
```

The model uses logistic-style transition rules. Intercepts shift the baseline probability; the other coefficients scale how strongly a trait or exposure term contributes.

For the exact transition equations, the corresponding probability expressions, and the order in which competing transitions are sampled, see [Model Notes](model.md#transition-equations).

### Parameters

| Parameter | Type | Recommended range | Effect | Interpretation |
|---|---|---:|---|---|
| `awareness_lambda` | `float` | `0..10` | Controls how quickly observing spreads from participating/amplifying neighbors. | Social visibility or attention sensitivity. |
| `participation_intercept` | `float` | roughly `-6..2` | Baseline offset for `O -> P`. More negative values suppress participation. | Baseline willingness to adopt absent strong exposure. |
| `participation_appeal` | `float` | `0..5` | Scales the effect of challenge appeal on participation. | How strongly the challenge’s attractiveness pushes observing agents toward adoption. |
| `participation_susceptibility` | `float` | `0..5` | Scales susceptibility times exposure. | Sensitivity to peer influence when exposed. |
| `participation_conformity` | `float` | `0..5` | Scales conformity times exposure. | Tendency to align with what peers are doing. |
| `participation_risk` | `float` | `0..5` | Scales risk aversion times challenge severity and subtracts from participation. | How much danger perception suppresses adoption. |
| `amplification_intercept` | `float` | roughly `-6..2` | Baseline offset for `P -> A`. More negative values reduce amplification. | Baseline tendency to share challenge-related content. |
| `amplification_share` | `float` | `0..5` | Scales share tendency. | Personal inclination to publicly spread content. |
| `amplification_exposure` | `float` | `0..5` | Scales exposure-driven amplification. | How much peer activity encourages public promotion. |
| `amplification_conformity` | `float` | `0..5` | Scales conformity in amplification. | Tendency to mirror peers by resharing or promoting. |
| `counter_intercept` | `float` | roughly `-6..2` | Baseline offset for `O -> C`. More negative values reduce counteraction. | Baseline willingness to discourage the challenge. |
| `counter_risk` | `float` | `0..5` | Scales risk aversion times severity in counteraction. | How strongly danger perception triggers resistance. |
| `counter_exposure` | `float` | `0..5` | Scales exposure-driven counteraction. | Visibility of the challenge as a trigger for corrective response. |
| `counter_effectiveness` | `float` | `0..1` typical, can exceed `1` | Reduces effective exposure when neighbors are counteracting. | How much counter-speech dampens local diffusion. |
| `dropout_intercept` | `float` | roughly `-6..2` | Baseline offset for `P -> D`. More negative values reduce dropout. | Baseline tendency to stop participating. |
| `dropout_risk` | `float` | `0..5` | Scales risk aversion times severity in dropout. | How strongly perceived danger makes participants disengage. |
| `dropout_exposure` | `float` | `0..5` | Scales exposure-driven retention. | How strongly peer reinforcement keeps participants engaged. |
| `spontaneous_dropout` | `float` | `0..1` | Added baseline dropout probability. | Small spontaneous exit rate even without strong risk cues. |

### Practical Tuning Guidance

- Increase `participation_*` terms to make cascades easier.
- Increase `counter_*` terms to make protective responses more common.
- Increase `dropout_*` risk sensitivity to make participation less persistent.
- Keep `counter_effectiveness` modest unless you want counteraction to strongly suppress exposure.
- Use negative intercepts to make transitions selective instead of near-automatic.

## `AgentTraitDistributions`

```python
AgentTraitDistributions(
    susceptibility: DistributionSpec = DistributionSpec(kind="beta", parameters=(2.0, 2.0)),
    conformity: DistributionSpec = DistributionSpec(kind="beta", parameters=(2.0, 2.0)),
    risk_aversion: DistributionSpec = DistributionSpec(kind="beta", parameters=(3.0, 2.0)),
    share_tendency: DistributionSpec = DistributionSpec(kind="beta", parameters=(2.0, 3.0)),
)
```

### Parameters

| Parameter | Type | Recommended range | Effect | Interpretation |
|---|---|---:|---|---|
| `susceptibility` | `DistributionSpec` | any supported distribution | Generates the susceptibility trait for each agent. | How easily the agent is influenced by exposed peers. |
| `conformity` | `DistributionSpec` | any supported distribution | Generates the conformity trait for each agent. | How much the agent tends to align with peer behavior. |
| `risk_aversion` | `DistributionSpec` | any supported distribution | Generates the risk-aversion trait for each agent. | How strongly the agent avoids risky behavior. |
| `share_tendency` | `DistributionSpec` | any supported distribution | Generates the sharing/amplification trait for each agent. | How willing the agent is to publicly spread the challenge. |

### Default

All four traits default to Beta distributions, which keep values in `[0, 1]` and fit the model’s normalized-trait assumption.

## `DistributionSpec`

```python
DistributionSpec(
    kind: str = "beta",
    parameters: Tuple[float, ...] = (2.0, 2.0),
    clip: bool = True,
)
```

### Parameters

| Parameter | Type | Recommended range | Effect | Interpretation |
|---|---|---:|---|---|
| `kind` | `str` | `beta`, `uniform`, `triangular`, `normal`, `gamma`, `lognormal` | Selects the sampler used for a trait. | The shape of the initial trait distribution. |
| `parameters` | `Tuple[float, ...]` | depends on `kind` | Passed to the corresponding random sampler. | Distribution parameters such as alpha/beta, mean/sigma, or bounds. |
| `clip` | `bool` | `True` or `False` | Clips sampled values to `[0, 1]` when enabled. | Keeps the normalized-trait assumption intact. |

### Supported `kind` values

- `beta(alpha, beta)`: default, bounded in `[0, 1]`.
- `uniform(low, high)`: flat distribution between two bounds.
- `triangular(low, high[, mode])`: peaked distribution on an interval.
- `normal(mu, sigma)`: bell-shaped distribution; typically use `clip=True`.
- `gamma(alpha, beta)`: positively skewed distribution; typically use `clip=True`.
- `lognormal(mu, sigma)`: heavy-tailed positive distribution; typically use `clip=True`.

### Trait-Configuration Guidance

- Use `beta` when you want a direct normalized trait prior.
- Use `uniform` when you want broad heterogeneity with no central tendency.
- Use `triangular` when you want a plausible middle value but still bounded support.
- Use `normal`, `gamma`, or `lognormal` when you want to model a latent continuous process and then clip it back to `[0, 1]`.

## `SimulationResult`

Returned by `ChallengeABM.run()`.

Fields:

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

## `State`

Behavioral states:

- `U` unaware
- `O` observing
- `P` participating
- `A` amplifying
- `C` counteracting
- `D` dropped out

## Visualization Helpers

Available from `challengeabm.viz`:

- `plot_state_trends(result, ax=None, normalize=False)`
- `plot_state_density_matrix(result, ax=None, normalize=True)`
- `plot_agent_state_matrix(model, ax=None)`
- `plot_network_snapshot(model, ax=None, layout="spring", with_labels=False)`
- `create_dashboard(model, result=None, layout="spring")`
