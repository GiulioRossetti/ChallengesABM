"""Network construction utilities."""

from __future__ import annotations

import networkx as nx


def prepare_custom_network(graph: nx.Graph) -> nx.Graph:
    """Normalize a user-supplied network for internal ABM use.

    The model uses integer node labels from 0..N-1. Custom graphs are copied,
    converted to a simple graph if needed, and relabeled accordingly. Existing
    edge weights are preserved when present; missing weights default to 1.0.
    """

    prepared = nx.Graph(graph)
    prepared = nx.convert_node_labels_to_integers(prepared, first_label=0, label_attribute="original_label")
    for u, v in prepared.edges:
        prepared[u][v]["weight"] = float(prepared[u][v].get("weight", 1.0))
    return prepared
