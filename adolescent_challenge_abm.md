# Agent-Based Model of Risky Online Challenge Diffusion Among Adolescents

## 1. Purpose

This document defines a minimal agent-based model (ABM) for studying how a risky online challenge may diffuse through an adolescent peer network.

The model is intentionally abstract. It does not encode real harmful tasks or operational details. Instead, a challenge is represented through general properties such as perceived appeal and perceived severity.

The main research question is:

> Under what conditions does a risky online challenge remain localized, die out, or diffuse widely through an adolescent social network?

The model is designed as a baseline that can later be extended with richer psychology, recommender systems, language generation, or integration into social-media simulators.

---

## 2. Model Overview

The model contains five core components:

1. A peer network connecting adolescent agents.
2. Heterogeneous individual traits that affect susceptibility and behavior.
3. A challenge characterized by perceived appeal and perceived risk.
4. A finite set of behavioral states.
5. Probabilistic transition rules driven by individual traits and local peer exposure.

Formally, the model can be written as:

\[
M = (G, A, X, Q, F)
\]

where:

- \(G\) is the social network.
- \(A\) is the set of agent attributes.
- \(X\) is the set of behavioral states.
- \(Q\) represents challenge properties.
- \(F\) is the behavioral transition function.

---

## 3. Environment

The social environment is represented as a static graph:

\[
G = (V,E)
\]

where:

- \(V\) is the set of adolescent agents.
- \(E\) is the set of social ties.

Each edge between agents \(i\) and \(j\) can have a tie strength:

\[
w_{ij} \in [0,1]
\]

Higher values indicate stronger friendship or social influence.

### Suggested Initial Configuration

A simple baseline configuration is:

- Number of agents: \(N = 500\)
- Mean degree: approximately 12
- High local clustering
- Simulation duration: 100 discrete time steps

A clustered or small-world graph is preferable to a purely random network because adolescent friendships are typically organized into local peer groups.

Candidate graph generators include:

- Watts-Strogatz small-world network
- Stochastic block model
- Clustered random network

For the first implementation, a Watts-Strogatz graph provides a convenient balance between simplicity, clustering, and short path lengths.

---

## 4. Agent Attributes

Each adolescent agent \(i\) is assigned four stable traits:

\[
A_i = (S_i, C_i, R_i, P_i)
\]

where:

- \(S_i\): susceptibility to social influence
- \(C_i\): conformity or tendency to follow peer behavior
- \(R_i\): risk aversion
- \(P_i\): propensity to publicly share or amplify content

All traits are normalized:

\[
S_i,C_i,R_i,P_i \in [0,1]
\]

### Example Initial Distributions

A possible initialization is:

```text
susceptibility  ~ Beta(2, 2)
conformity      ~ Beta(2, 2)
risk_aversion   ~ Beta(3, 2)
share_tendency  ~ Beta(2, 3)
```

These distributions are placeholders rather than empirically calibrated parameters.

The initial model deliberately excludes additional psychological and demographic variables. Possible later extensions include:

- age
- sensation seeking
- impulsivity
- social status
- self-efficacy
- parental or adult support
- emotional state
- digital literacy
- prior experience with similar challenges

---

## 5. Challenge Representation

The risky online challenge is represented abstractly as:

\[
Q = (q,v)
\]

where:

- \(q \in [0,1]\) is perceived social appeal or attractiveness.
- \(v \in [0,1]\) is perceived severity or risk.

Example:

```text
appeal   = 0.55
severity = 0.65
```

The model does not require semantic descriptions of individual tasks.

This abstraction allows experiments on diffusion dynamics without representing harmful instructions.

---

## 6. Behavioral States

Each agent occupies exactly one behavioral state at time \(t\):

\[
X_i(t) \in
\{U,O,P,A,C,D\}
\]

The states are:

| Symbol | State | Meaning |
|---|---|---|
| U | Unaware | Agent has not encountered the challenge |
| O | Observing | Agent is aware but has not adopted it |
| P | Participating | Agent has adopted or engaged with the challenge |
| A | Amplifying | Agent is publicly spreading or promoting challenge-related content |
| C | Counteracting | Agent is discouraging, criticizing, or countering the challenge |
| D | Dropped out | Agent previously engaged but has stopped |

Participation and amplification are intentionally distinct.

An agent may participate privately without spreading the phenomenon, while another may amplify discussion without sustained participation.

A simplified state structure is:

```text
               +---------- C
               |
U -> O -> P -> A
     |    |    |
     |    |    +----> D
     |    +---------> D
     +--------------> D
```

Agents may also remain in their current state from one time step to the next.

---

## 7. Social Exposure

An agent's behavior is influenced by challenge-related activity among its neighbors.

Let \(N_i\) denote the set of neighbors of agent \(i\).

A general social exposure measure is:

\[
E_i(t)
=
\frac{
\sum_{j \in N_i} w_{ij} I_j(t)
}{
\sum_{j \in N_i} w_{ij}
}
\]

where \(I_j(t)=1\) if neighbor \(j\) is currently participating or amplifying, and 0 otherwise.

A richer version separates exposure to participation from exposure to public amplification.

### Participation Exposure

\[
E_i^P(t)
=
\frac{
\sum_{j \in N_i} w_{ij}\mathbf{1}[X_j(t)=P]
}{
\sum_{j \in N_i}w_{ij}
}
\]

### Amplification Exposure

\[
E_i^A(t)
=
\frac{
\sum_{j \in N_i} w_{ij}\mathbf{1}[X_j(t)=A]
}{
\sum_{j \in N_i}w_{ij}
}
\]

This distinction allows the model to represent the difference between:

- observing peers who actually participate; and
- observing peers who merely talk about or spread the challenge.

---

## 8. Awareness

Most agents begin in the unaware state.

A small number receive an external exposure at initialization.

For an unaware agent, the probability of becoming aware can be defined as:

\[
P(U \rightarrow O)
=
1-\exp[-\lambda(E_i^P+E_i^A)]
\]

where \(\lambda\) controls the strength of transmission.

A simpler first implementation can use a deterministic awareness rule:

```text
if at least one neighbor is amplifying:
    U -> O
```

---

## 9. Participation Decision

The central behavioral mechanism determines whether an observing agent begins participating.

Define a latent participation score:

\[
z_i =
\beta_0
+ \beta_1 q
+ \beta_2 S_i E_i
+ \beta_3 C_i E_i
- \beta_4 R_i v
\]

The probability of participation is:

\[
P(O \rightarrow P)
=
\sigma(z_i)
\]

where the logistic function is:

\[
\sigma(z)
=
\frac{1}{1+e^{-z}}
\]

An illustrative parameterization is:

```text
z =
    -2.0
    + 1.0 * appeal
    + 3.0 * susceptibility * exposure
    + 2.0 * conformity * exposure
    - 2.5 * risk_aversion * severity
```

This formulation produces heterogeneous outcomes.

For example:

- high peer exposure can overcome moderate risk aversion;
- highly risk-averse agents are less likely to adopt severe challenges;
- low-conformity agents may resist even widespread adoption;
- socially susceptible agents can adopt when several peers are involved.

The coefficients should eventually be calibrated or subjected to sensitivity analysis.

---

## 10. Amplification Decision

Participation and transmission are modeled separately.

A participating agent may begin amplifying the challenge with probability:

\[
P(P \rightarrow A)
=
\sigma(
\alpha_0
+ \alpha_1 P_i
+ \alpha_2 E_i
+ \alpha_3 C_i
)
\]

An example specification is:

```text
share_probability =
sigmoid(
    -1.5
    + 2.0 * share_tendency
    + 1.5 * peer_exposure
    + 1.0 * conformity
)
```

This distinction is important because:

\[
\text{adoption} \neq \text{transmission}
\]

A challenge can have many participants but relatively little public diffusion, or substantial discussion with limited actual participation.

---

## 11. Counteraction

Some observing agents respond by discouraging participation rather than adopting the challenge.

Define:

\[
P(O \rightarrow C)
=
\sigma(
\gamma_0
+ \gamma_1R_iv
+ \gamma_2E_i
)
\]

The intuition is that:

- higher perceived danger increases the likelihood of counteraction;
- greater visibility increases the likelihood that an agent responds publicly.

Counteracting behavior can reduce effective exposure among neighboring agents.

Let \(C_i^{local}\) be the weighted fraction of neighbors who are counteracting.

Then:

\[
E_i^{eff}
=
\max(0,E_i-\rho C_i^{local})
\]

where \(\rho\) controls the effectiveness of local counteraction.

This creates two competing processes:

```text
challenge diffusion
        versus
protective / counter-speech diffusion
```

---

## 12. Dropout

Participation is not an absorbing state.

A participating agent can stop engaging.

Define:

\[
P(P \rightarrow D)
=
\sigma(
\delta_0
+ \delta_1R_iv
- \delta_2E_i
)
\]

This encodes two intuitions:

- greater perceived risk increases dropout;
- strong peer reinforcement can reduce dropout.

A small spontaneous dropout probability may also be included.

---

## 13. Initial Seeding

At time \(t=0\), almost all agents begin in state \(U\).

A small number of agents receive external exposure.

Example:

```text
number_of_seeds = 3
```

A useful baseline is to choose seed agents randomly.

Importantly, external exposure should not necessarily force participation.

A seed can instead be initialized as observing:

```text
external source -> seed agent sees challenge

seed agent then decides whether to:
    remain observing
    participate
    counteract
```

This allows some simulation runs to terminate without a cascade.

That stochastic extinction is a meaningful model outcome.

---

## 14. Update Schedule

The model should initially use synchronous updates.

At each time step:

1. Compute each agent's exposure from states at time \(t\).
2. Compute transition probabilities.
3. Sample each agent's next state.
4. Apply all transitions simultaneously.
5. Record aggregate statistics.
6. Advance to time \(t+1\).

Using synchronous updates prevents arbitrary iteration order from influencing cascade dynamics.

### Pseudocode

```python
for t in range(T):

    for agent in agents:

        exposure = social_exposure(agent)

        if agent.state == UNAWARE:
            if exposed(agent, exposure):
                agent.next_state = OBSERVING

        elif agent.state == OBSERVING:

            p_participate = participation_probability(
                agent,
                exposure,
                challenge
            )

            p_counter = counter_probability(
                agent,
                exposure,
                challenge
            )

            agent.next_state = sample_observer_transition(
                p_participate,
                p_counter
            )

        elif agent.state == PARTICIPATING:

            p_share = sharing_probability(
                agent,
                exposure
            )

            p_dropout = dropout_probability(
                agent,
                exposure,
                challenge
            )

            agent.next_state = sample_participant_transition(
                p_share,
                p_dropout
            )

        elif agent.state == AMPLIFYING:

            agent.next_state = amplification_update(
                agent,
                exposure
            )

    apply_all_state_updates()
    record_metrics()
```

---

## 15. Outcome Metrics

The initial model should record a small, interpretable set of outcomes.

### Final Reach

\[
R_{final}
=
\frac{
\#\text{agents ever participating}
}{
N
}
\]

### Additional Metrics

Record:

- number of agents ever exposed;
- number of agents ever participating;
- number of agents ever amplifying;
- number of agents ever counteracting;
- peak number of active participants;
- time of peak participation;
- cascade duration;
- largest connected participating cluster;
- number and fraction of agents who drop out.

A useful binary cascade indicator is:

\[
LargeCascade =
\mathbf{1}[R_{final} > \theta]
\]

where \(\theta\) could initially be set to 0.10.

Across repeated simulations:

\[
P(\text{large cascade})
=
P(R_{final}>\theta)
\]

is a central outcome.

---

## 16. Baseline Experimental Design

Before adding richer behavioral mechanisms, the model should be explored through systematic parameter sweeps.

### Challenge Appeal

\[
q \in \{0.3,0.5,0.7\}
\]

### Challenge Severity

\[
v \in \{0.3,0.5,0.7\}
\]

### Number of Initial Seeds

\[
k_{seed} \in \{1,3,10\}
\]

Additional experiments can vary:

- mean susceptibility;
- mean conformity;
- counteraction effectiveness;
- network clustering;
- seed centrality;
- tie-strength heterogeneity.

Each parameter configuration should be replicated many times, for example 500 or 1,000 simulation runs.

Repeated runs are necessary because cascade emergence is stochastic.

---

## 17. Expected Qualitative Dynamics

The model is expected to exhibit at least three broad regimes:

```text
low social influence
|
|      local extinction
|
|             transition region
|            /////////////////
|           /////////////////
|                         widespread cascade
+--------------------------------------------
             social influence
```

Of particular interest is the transition region where small differences in:

- initial seeds;
- network location;
- social susceptibility;
- local reinforcement;

can determine whether the challenge disappears or becomes widespread.

This threshold behavior is one of the main phenomena the ABM is intended to investigate.

---

## 18. Minimal Formal Specification

The minimum viable model is:

\[
M = (G,A,X,Q,F)
\]

with:

### Network

\[
G = \text{adolescent peer network}
\]

### Agent Traits

\[
A_i =
(S_i,C_i,R_i,P_i)
\]

### Behavioral State

\[
X_i(t)
\in
\{U,O,P,A,C,D\}
\]

### Challenge

\[
Q=(q,v)
\]

### Transition Function

\[
X_i(t+1)
\sim
F(
X_i(t),
A_i,
Q,
\{X_j(t):j\in N_i\}
)
\]

The transition function \(F\) is probabilistic and depends on:

- current state;
- individual traits;
- challenge appeal;
- challenge severity;
- local peer exposure;
- local counteraction.

---

## 19. Recommended Development Sequence

A disciplined implementation path is:

1. Implement the social network.
2. Implement the six behavioral states.
3. Implement exposure calculation.
4. Implement awareness transitions.
5. Implement participation probability.
6. Implement amplification.
7. Implement dropout.
8. Implement counteraction.
9. Add metrics and repeated simulation runs.
10. Perform parameter sweeps and sensitivity analysis.

Only after understanding the behavior of this baseline model should additional mechanisms be introduced.

Potential later extensions include:

- age-dependent traits;
- changing psychological states;
- multiple simultaneous challenges;
- dynamic friendship networks;
- prestige or status effects;
- distinct strong and weak ties;
- complex contagion requiring multiple independent exposures;
- recommender-system amplification;
- institutional moderation;
- parental or adult intervention;
- endogenous challenge introduction;
- empirical calibration;
- natural-language interaction through LLMs.

---

## 20. Safety and Scope

The model should remain abstract with respect to harmful challenge content.

The objective is to study:

- social diffusion;
- peer influence;
- cascade formation;
- protective responses;
- intervention effectiveness.

It is not necessary to encode realistic harmful instructions in order to investigate these dynamics.

The severity parameter \(v\) and behavioral state transitions provide sufficient abstraction for the baseline ABM.

---

## 21. Summary

The proposed ABM represents risky online challenge diffusion as a stochastic social-contagion process over an adolescent peer network.

Agents differ in susceptibility, conformity, risk aversion, and sharing propensity. They move among six states:

```text
UNAware
OBSERVING
PARTICIPATING
AMPLIFYING
COUNTERACTING
DROPPED OUT
```

Transitions depend jointly on:

- individual characteristics;
- challenge appeal and severity;
- peer behavior;
- network structure.

The model is intentionally minimal. Its purpose is to establish a transparent and interpretable baseline before introducing more complex mechanisms such as richer adolescent psychology, recommendation algorithms, or LLM-driven communication.
