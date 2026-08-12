"""Visualization helpers for ChallengeABM simulations."""

from __future__ import annotations

from typing import Optional

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

from .metrics import SimulationResult
from .model import ChallengeABM
from .states import State

STATE_ORDER = [state.value for state in State]
STATE_LABELS = {
    State.UNAWARE.value: "Unaware",
    State.OBSERVING.value: "Observing",
    State.PARTICIPATING.value: "Participating",
    State.AMPLIFYING.value: "Amplifying",
    State.COUNTERACTING.value: "Counteracting",
    State.DROPPED_OUT.value: "Dropped out",
}
STATE_COLORS = {
    State.UNAWARE.value: "#b8c1cc",
    State.OBSERVING.value: "#5b8ff9",
    State.PARTICIPATING.value: "#ffb000",
    State.AMPLIFYING.value: "#e45756",
    State.COUNTERACTING.value: "#54a24b",
    State.DROPPED_OUT.value: "#8c6bb1",
}


def _counts_matrix(result: SimulationResult) -> np.ndarray:
    return np.array(
        [[snapshot.get(state, 0) for state in STATE_ORDER] for snapshot in result.state_counts],
        dtype=float,
    )


def _normalize_rows(matrix: np.ndarray) -> np.ndarray:
    row_sums = matrix.sum(axis=1, keepdims=True)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.divide(matrix, row_sums, out=np.zeros_like(matrix), where=row_sums > 0)


def plot_state_trends(
    result: SimulationResult,
    ax: Optional[Axes] = None,
    normalize: bool = False,
) -> Figure:
    """Plot the temporal trend of each behavioral state."""

    matrix = _counts_matrix(result)
    values = _normalize_rows(matrix) if normalize else matrix
    x = np.arange(values.shape[0])

    if ax is None:
        _, ax = plt.subplots(figsize=(10, 5))

    for index, state in enumerate(STATE_ORDER):
        ax.plot(x, values[:, index], label=STATE_LABELS[state], color=STATE_COLORS[state], linewidth=2)

    ax.set_xlabel("Time step")
    ax.set_ylabel("Fraction of agents" if normalize else "Number of agents")
    ax.set_title("ChallengeABM state trends")
    ax.grid(alpha=0.2)
    ax.legend(ncol=2, frameon=False)
    return ax.figure


def plot_state_density_matrix(
    result: SimulationResult,
    ax: Optional[Axes] = None,
    normalize: bool = True,
) -> Figure:
    """Plot a state-by-time density heatmap."""

    matrix = _counts_matrix(result)
    values = _normalize_rows(matrix) if normalize else matrix
    display = values.T

    if ax is None:
        _, ax = plt.subplots(figsize=(11, 4.8))

    image = ax.imshow(display, aspect="auto", interpolation="nearest", cmap="magma")
    ax.set_yticks(np.arange(len(STATE_ORDER)))
    ax.set_yticklabels([STATE_LABELS[state] for state in STATE_ORDER])
    ax.set_xlabel("Time step")
    ax.set_title("State density matrix")
    cbar = ax.figure.colorbar(image, ax=ax, pad=0.02)
    cbar.set_label("Fraction of agents" if normalize else "Number of agents")
    return ax.figure


def plot_agent_state_matrix(
    model: ChallengeABM,
    ax: Optional[Axes] = None,
) -> Figure:
    """Plot each agent's state over time as a trajectory matrix."""

    state_to_index = {state: index for index, state in enumerate(STATE_ORDER)}
    trajectory = np.array(
        [[state_to_index.get(state.value, 0) for state in agent.history] for agent in model.agents],
        dtype=float,
    )

    if ax is None:
        _, ax = plt.subplots(figsize=(11, 6))

    image = ax.imshow(
        trajectory,
        aspect="auto",
        interpolation="nearest",
        cmap="tab20",
        vmin=0,
        vmax=len(STATE_ORDER) - 1,
    )
    ax.set_xlabel("Time step")
    ax.set_ylabel("Agent")
    ax.set_title("Agent-state trajectory matrix")
    cbar = ax.figure.colorbar(image, ax=ax, pad=0.02, ticks=np.arange(len(STATE_ORDER)))
    cbar.ax.set_yticklabels([STATE_LABELS[state] for state in STATE_ORDER])
    cbar.set_label("Behavioral state")
    return ax.figure


def plot_network_snapshot(
    model: ChallengeABM,
    ax: Optional[Axes] = None,
    layout: str = "spring",
    with_labels: bool = False,
) -> Figure:
    """Plot the peer network colored by each agent's current state."""

    graph = model.graph
    node_colors = [STATE_COLORS[agent.state.value] for agent in model.agents]
    node_sizes = [55 + 130 * agent.share_tendency for agent in model.agents]

    if layout == "spring":
        positions = nx.spring_layout(graph, seed=42, weight="weight")
    elif layout == "circular":
        positions = nx.circular_layout(graph)
    else:
        raise ValueError("layout must be 'spring' or 'circular'")

    if ax is None:
        _, ax = plt.subplots(figsize=(8.5, 8.5))

    edge_widths = [0.5 + 1.8 * graph[u][v].get("weight", 1.0) for u, v in graph.edges]
    nx.draw_networkx_edges(graph, positions, ax=ax, width=edge_widths, alpha=0.2, edge_color="#3a3a3a")
    nx.draw_networkx_nodes(
        graph,
        positions,
        ax=ax,
        node_color=node_colors,
        node_size=node_sizes,
        linewidths=0.4,
        edgecolors="#1f1f1f",
    )

    if with_labels and graph.number_of_nodes() <= 80:
        nx.draw_networkx_labels(graph, positions, ax=ax, font_size=7)

    ax.set_title("Peer network snapshot")
    ax.set_axis_off()

    legend_handles = [
        Line2D([0], [0], marker="o", color="w", label=STATE_LABELS[state], markerfacecolor=STATE_COLORS[state], markersize=8)
        for state in STATE_ORDER
    ]
    ax.legend(handles=legend_handles, loc="upper left", frameon=False, fontsize=8)
    return ax.figure


def create_dashboard(
    model: ChallengeABM,
    result: Optional[SimulationResult] = None,
    layout: str = "spring",
) -> Figure:
    """Create a multi-panel figure summarizing the simulation."""

    if result is None:
        result = model.run()

    fig = plt.figure(figsize=(16, 11), constrained_layout=True)
    grid = fig.add_gridspec(2, 2)

    trends_ax = fig.add_subplot(grid[0, 0])
    density_ax = fig.add_subplot(grid[0, 1])
    network_ax = fig.add_subplot(grid[1, 0])
    agent_ax = fig.add_subplot(grid[1, 1])

    plot_state_trends(result, ax=trends_ax)
    plot_state_density_matrix(result, ax=density_ax)
    plot_network_snapshot(model, ax=network_ax, layout=layout)
    plot_agent_state_matrix(model, ax=agent_ax)

    fig.suptitle("ChallengeABM simulation dashboard", fontsize=16, fontweight="bold")
    return fig

