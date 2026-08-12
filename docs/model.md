# Model Notes

ChallengeABM is intentionally minimal:

- the network is provided by the caller as a NetworkX graph;
- agents have four stable traits: susceptibility, conformity, risk aversion, and share tendency;
- the challenge has two abstract parameters: appeal and severity;
- behavior evolves through synchronous probabilistic state transitions.
- initial seeds can be selected randomly or passed explicitly as `infected_nodes`.
- stable agent traits are drawn from configurable distributions, with Beta as the default prior.

## Compartmental Diagram

![ChallengeABM compartmental model](assets/compartmental_model.png)

The diagram is a compact summary of the synchronous transition rules. Each arrow is a one-step stochastic transition evaluated from the previous state snapshot.

### Transition Legend

- `U -> O`: [awareness probability](#awareness-probability). An unaware agent becomes observing when local `P` or `A` exposure is high enough.
- `O -> P`: [participation probability](#participation-probability). Observing agents join the challenge when appeal, susceptibility, conformity, and exposure overcome resistance from risk aversion.
- `O -> C`: [counteraction probability](#counteraction-probability). Observing agents move into an opposing stance when risk aversion and local exposure favor resistance.
- `P -> A`: [amplification probability](#amplification-probability). Participants start amplifying when sharing tendency, conformity, and exposure favor public promotion.
- `P -> D`: [dropout probability](#dropout-probability). Participants leave the challenge when risk aversion and challenge severity outweigh retention.
- `A -> D`: [dropout probability](#dropout-probability). Amplifiers can also exit using the same dropout logic applied to participants.
- `C -> C`: counteracting is absorbing in the current implementation.
- `D -> D`: dropped out is absorbing in the current implementation.

### Transition Equations

The model uses the following quantities for each agent at each time step:

- `e_P`: weighted fraction of neighbors in `P`
- `e_A`: weighted fraction of neighbors in `A`
- `e_C`: weighted fraction of neighbors in `C`
- `s`: agent susceptibility
- `c`: agent conformity
- `r`: agent risk aversion
- `t`: agent share tendency
- `appeal`: challenge appeal
- `severity`: challenge severity

The helper quantities are:

```text
sigma(x) = 1 / (1 + exp(-x))                                          # Logistic link used by most transition rules
effective_exposure = max(0, e_P + e_A - counter_effectiveness * e_C)  # Counteracting neighbors reduce local exposure
```

### Awareness Probability

```text
p_awareness = 1 - exp(-awareness_lambda * (e_P + e_A))                # U -> O: observing becomes more likely as participating/amplifying exposure grows
```

### Participation Probability

```text

p_participation = sigma(
    participation_intercept
    + participation_appeal * appeal
    + participation_susceptibility * s * effective_exposure
    + participation_conformity * c * effective_exposure
    - participation_risk * r * severity
)                                                                     # O -> P: participation increases with appeal, susceptibility, conformity, and exposure, and decreases with perceived risk
```

### Counteraction Probability

```text

p_counteraction = sigma(
    counter_intercept
    + counter_risk * r * severity
    + counter_exposure * effective_exposure
)                                                                     # O -> C: counteraction increases with risk aversion, severity, and exposure to the challenge
```

### Amplification Probability

```text

p_amplification = sigma(
    amplification_intercept
    + amplification_share * t
    + amplification_exposure * effective_exposure
    + amplification_conformity * c
)                                                                     # P -> A: amplification increases with sharing tendency, exposure, and conformity
```

### Dropout Probability

```text

p_dropout = clamp(
    spontaneous_dropout
    + sigma(
        dropout_intercept
        + dropout_risk * r * severity
        - dropout_exposure * effective_exposure
    ),
    0, 1
)                                                                     # P -> D and A -> D: dropout increases with risk and decreases with reinforcing exposure
```

The implementation evaluates these rules with a single uniform random draw per transition class:

```text
u ~ Uniform(0, 1)

if state == U:
    if u < p_awareness:
        next = O
    else:
        next = U

if state == O:
    if u < p_counteraction:
        next = C
    elif u < p_counteraction + p_participation:
        next = P
    else:
        next = O

if state == P:
    if u < p_dropout:
        next = D
    elif u < p_dropout + p_amplification:
        next = A
    else:
        next = P

if state == A:
    if u < p_dropout:
        next = D
    else:
        next = A

if state in {C, D}:
    next = state
```

Notes:

- `counteracting` and `dropped out` are absorbing in the current model.
- `effective_exposure` is the only place where counteracting neighbors directly suppress the local challenge signal.
- `p_participation`, `p_counteraction`, and `p_amplification` are evaluated with logistic links so the associated intercepts shift the baseline and the coefficients scale the strength of each term.

## States

- `U`: unaware
- `O`: observing
- `P`: participating
- `A`: amplifying
- `C`: counteracting
- `D`: dropped out

## Graph Handling

When a custom graph is passed to the model:

- it is copied before use;
- the original node labels are preserved;
- missing edge weights default to `1.0`;
- the graph is converted to a simple undirected graph.

## Initial Seeding

If `infected_nodes` is provided to `ChallengeABM`, those node labels are used as the initial observing agents.

If not, the model chooses `seed_count` nodes at random.

## Outputs

The model reports:

- final reach;
- peak participation;
- time of peak participation;
- cascade duration;
- largest participating cluster;
- large-cascade indicator.

## Transition Parameters

Behavioral dynamics are controlled by `TransitionParameters`.

The parameters govern:

- awareness from local exposure;
- adoption from exposure, susceptibility, conformity, and challenge severity;
- amplification from share tendency and exposure;
- counteraction from risk aversion and exposure;
- dropout from risk aversion and exposure.

See the equations above for the exact role of each parameter in the transition rules.
