"""Interactive browser dashboard for ChallengeABM.

The dashboard follows the same workflow as the NDlib browser UI:
build a network, configure the model, run the simulation, and inspect the
result through a live network view and time series plots.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import threading
import webbrowser
from dataclasses import asdict, fields
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import networkx as nx

from .. import AgentTraitDistributions, Challenge, ChallengeABM, DistributionSpec, SimulationConfig, TransitionParameters
from ..metrics import SimulationResult
from ..viz import STATE_COLORS, STATE_LABELS, STATE_ORDER

STATIC_DIR = Path(__file__).resolve().with_name("static")
DEFAULT_PORT = 8050


def _dataclass_defaults(cls: type[Any]) -> dict[str, Any]:
    return {field.name: getattr(cls(), field.name) for field in fields(cls)}


def default_dashboard_config() -> dict[str, Any]:
    return {
        "topology": {
            "kind": "watts_strogatz",
            "layout": "spring",
            "watts_strogatz": {"n": 120, "k": 8, "p": 0.08},
            "erdos_renyi": {"n": 120, "p": 0.03},
            "barabasi_albert": {"n": 120, "m": 4},
            "newman_watts_strogatz": {"n": 120, "k": 8, "p": 0.08},
            "path": {"n": 60},
            "sbm": {
                "sizes": [40, 40, 40],
                "probabilities": [
                    [0.14, 0.03, 0.02],
                    [0.03, 0.13, 0.03],
                    [0.02, 0.03, 0.12],
                ],
            },
            "lfr": {
                "n": 120,
                "tau1": 3.0,
                "tau2": 1.5,
                "mu": 0.1,
                "average_degree": 6.0,
                "min_degree": None,
                "max_degree": None,
                "min_community": 5,
                "max_community": None,
                "max_iters": 500,
            },
            "powerlaw_cluster": {"n": 120, "m": 4, "p": 0.08},
        },
        "simulation": {
            "steps": 60,
            "seed_count": 4,
            "random_seed": 42,
            "infected_nodes": "",
        },
        "challenge": asdict(Challenge(appeal=0.55, severity=0.65)),
        "transition": asdict(TransitionParameters()),
        "trait_distributions": {
            "susceptibility": asdict(DistributionSpec(kind="beta", parameters=(2.0, 2.0), clip=True)),
            "conformity": asdict(DistributionSpec(kind="beta", parameters=(2.0, 2.0), clip=True)),
            "risk_aversion": asdict(DistributionSpec(kind="beta", parameters=(3.0, 2.0), clip=True)),
            "share_tendency": asdict(DistributionSpec(kind="beta", parameters=(2.0, 3.0), clip=True)),
        },
    }


def _coerce_int(value: Any, default: int) -> int:
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return default


def _coerce_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_json_object(value: Any, default: dict[str, Any]) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return default
        return parsed if isinstance(parsed, dict) else default
    return default


def _parse_int_list(value: Any, default: list[int]) -> list[int]:
    if isinstance(value, list):
        items = value
    elif isinstance(value, str) and value.strip():
        text = value.strip()
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            items = [part.strip() for part in text.replace("\n", ",").split(",")]
        else:
            if isinstance(parsed, list):
                items = parsed
            else:
                items = [part.strip() for part in text.replace("\n", ",").split(",")]
    else:
        return default

    result: list[int] = []
    for item in items:
        if item in {"", None}:
            continue
        try:
            result.append(max(1, int(round(float(item)))))
        except (TypeError, ValueError):
            continue
    return result or default


def _parse_float_matrix(value: Any, default: list[list[float]]) -> list[list[float]]:
    if isinstance(value, list):
        rows = value
    elif isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return default
        rows = parsed if isinstance(parsed, list) else default
    else:
        return default

    matrix: list[list[float]] = []
    for row in rows:
        if not isinstance(row, list):
            return default
        parsed_row: list[float] = []
        for item in row:
            try:
                parsed_row.append(float(item))
            except (TypeError, ValueError):
                return default
        matrix.append(parsed_row)
    return matrix or default


def _topology_values(topology: dict[str, Any], kind: str) -> dict[str, Any]:
    nested = topology.get(kind)
    if isinstance(nested, dict):
        return nested
    return topology


def _parse_seed_nodes(raw: Any) -> list[Any] | None:
    if raw is None:
        return None
    if isinstance(raw, list):
        candidates = raw
    elif isinstance(raw, str):
        text = raw.strip()
        if not text:
            return None
        candidates = [part.strip() for part in text.replace("\n", ",").split(",")]
    else:
        candidates = [raw]

    normalized: list[Any] = []
    for item in candidates:
        if item in {"", None}:
            continue
        normalized.append(item)
    return normalized or None


def _build_network(topology: dict[str, Any], random_seed: int | None) -> nx.Graph:
    kind = str(topology.get("kind", "watts_strogatz")).strip().lower()
    seed = random_seed
    values = _topology_values(topology, kind)

    if kind == "watts_strogatz":
        n = _coerce_int(values.get("n", 120), 120)
        k = max(2, _coerce_int(values.get("k", 8), 8))
        if k >= n:
            k = max(2, n - 1)
        if k % 2 == 1:
            k = max(2, k - 1)
        p = max(0.0, min(1.0, _coerce_float(values.get("p", 0.08), 0.08)))
        return nx.watts_strogatz_graph(n=n, k=k, p=p, seed=seed)

    if kind == "erdos_renyi":
        n = _coerce_int(values.get("n", 120), 120)
        p = max(0.0, min(1.0, _coerce_float(values.get("p", 0.03), 0.03)))
        return nx.erdos_renyi_graph(n=n, p=p, seed=seed)

    if kind == "barabasi_albert":
        n = _coerce_int(values.get("n", 120), 120)
        m = max(1, _coerce_int(values.get("m", 4), 4))
        m = min(m, max(1, n - 1))
        return nx.barabasi_albert_graph(n=n, m=m, seed=seed)

    if kind == "newman_watts_strogatz":
        n = _coerce_int(values.get("n", 120), 120)
        k = max(2, _coerce_int(values.get("k", 8), 8))
        if k >= n:
            k = max(2, n - 1)
        if k % 2 == 1:
            k = max(2, k - 1)
        p = max(0.0, min(1.0, _coerce_float(values.get("p", 0.08), 0.08)))
        return nx.newman_watts_strogatz_graph(n=n, k=k, p=p, seed=seed)

    if kind == "path":
        n = _coerce_int(values.get("n", 60), 60)
        return nx.path_graph(n)

    if kind == "powerlaw_cluster":
        n = _coerce_int(values.get("n", 120), 120)
        m = max(1, _coerce_int(values.get("m", 4), 4))
        m = min(m, max(1, n - 1))
        p = max(0.0, min(1.0, _coerce_float(values.get("p", 0.08), 0.08)))
        return nx.powerlaw_cluster_graph(n=n, m=m, p=p, seed=seed)

    if kind == "sbm":
        sizes = _parse_int_list(values.get("sizes"), [40, 40, 40])
        probabilities = _parse_float_matrix(
            values.get("probabilities"),
            [
                [0.14, 0.03, 0.02],
                [0.03, 0.13, 0.03],
                [0.02, 0.03, 0.12],
            ],
        )
        if len(probabilities) != len(sizes):
            raise ValueError("SBM requires a square probability matrix matching the block sizes.")
        if any(len(row) != len(sizes) for row in probabilities):
            raise ValueError("SBM requires a square probability matrix matching the block sizes.")
        return nx.stochastic_block_model(sizes=sizes, p=probabilities, seed=seed)

    if kind == "lfr":
        n = max(10, _coerce_int(values.get("n", 120), 120))
        tau1 = max(1.01, _coerce_float(values.get("tau1", 3.0), 3.0))
        tau2 = max(1.01, _coerce_float(values.get("tau2", 1.5), 1.5))
        mu = max(0.0, min(1.0, _coerce_float(values.get("mu", 0.1), 0.1)))
        average_degree = _coerce_float(values.get("average_degree", 6.0), 6.0)
        min_degree = values.get("min_degree")
        max_degree = values.get("max_degree")
        min_community = values.get("min_community")
        max_community = values.get("max_community")
        max_iters = max(1, _coerce_int(values.get("max_iters", 500), 500))

        kwargs: dict[str, Any] = {
            "n": n,
            "tau1": tau1,
            "tau2": tau2,
            "mu": mu,
            "max_iters": max_iters,
            "seed": seed,
        }
        if average_degree and average_degree > 0:
            kwargs["average_degree"] = average_degree
        elif min_degree is not None:
            kwargs["min_degree"] = max(1, _coerce_int(min_degree, 1))
        else:
            kwargs["average_degree"] = 6.0

        if min_degree not in {None, ""} and "average_degree" not in kwargs:
            kwargs["min_degree"] = max(1, _coerce_int(min_degree, 1))
        if max_degree not in {None, ""}:
            kwargs["max_degree"] = max(2, _coerce_int(max_degree, 2))
        if min_community not in {None, ""}:
            kwargs["min_community"] = max(2, _coerce_int(min_community, 2))
        if max_community not in {None, ""}:
            kwargs["max_community"] = max(2, _coerce_int(max_community, 2))

        attempts = 5
        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                kwargs["seed"] = None if seed is None else seed + attempt
                return nx.LFR_benchmark_graph(**kwargs)
            except Exception as exc:  # pragma: no cover - networkx failure depends on random sampling
                last_error = exc
        raise ValueError(f"Unable to generate LFR benchmark graph: {last_error}") from last_error

    raise ValueError(f"Unsupported topology kind: {kind!r}")


def _build_transition_parameters(data: dict[str, Any]) -> TransitionParameters:
    defaults = _dataclass_defaults(TransitionParameters)
    payload = {name: data.get(name, default) for name, default in defaults.items()}
    return TransitionParameters(**payload)


def _build_trait_distributions(data: dict[str, Any]) -> AgentTraitDistributions:
    default_specs = default_dashboard_config()["trait_distributions"]

    def _spec(name: str) -> DistributionSpec:
        raw = data.get(name, default_specs[name])
        if isinstance(raw, DistributionSpec):
            return raw
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except json.JSONDecodeError:
                raw = default_specs[name]
        if not isinstance(raw, dict):
            raw = default_specs[name]
        kind = str(raw.get("kind", default_specs[name]["kind"]))
        params = raw.get("parameters", default_specs[name]["parameters"])
        if isinstance(params, list):
            params = tuple(float(value) for value in params)
        elif isinstance(params, tuple):
            params = tuple(float(value) for value in params)
        else:
            params = tuple(default_specs[name]["parameters"])
        clip = bool(raw.get("clip", True))
        return DistributionSpec(kind=kind, parameters=params, clip=clip)

    return AgentTraitDistributions(
        susceptibility=_spec("susceptibility"),
        conformity=_spec("conformity"),
        risk_aversion=_spec("risk_aversion"),
        share_tendency=_spec("share_tendency"),
    )


def _normalize_positions(graph: nx.Graph, layout: str, seed: int | None) -> dict[str, dict[str, float]]:
    layout = layout.strip().lower()
    if layout == "circular":
        positions = nx.circular_layout(graph)
    elif layout == "kamada_kawai":
        positions = nx.kamada_kawai_layout(graph, weight="weight")
    elif layout == "shell":
        components = [list(component) for component in nx.connected_components(graph)]
        positions = nx.shell_layout(graph, nlist=components if components else None)
    elif layout == "spectral":
        positions = nx.spectral_layout(graph, weight="weight")
    elif layout == "spiral":
        positions = nx.spiral_layout(graph)
    elif layout == "random":
        positions = nx.random_layout(graph, seed=seed)
    else:
        positions = nx.spring_layout(graph, seed=seed, weight="weight")

    xs = [pos[0] for pos in positions.values()]
    ys = [pos[1] for pos in positions.values()]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    width = max(max_x - min_x, 1e-9)
    height = max(max_y - min_y, 1e-9)

    normalized: dict[str, dict[str, float]] = {}
    for node, (x, y) in positions.items():
        normalized[str(node)] = {
            "x": float(0.05 + 0.9 * ((x - min_x) / width)),
            "y": float(0.05 + 0.9 * ((y - min_y) / height)),
        }
    return normalized


def _build_network_payload(graph: nx.Graph, layout: str, random_seed: int | None) -> dict[str, Any]:
    positions = _normalize_positions(graph, layout, random_seed)
    nodes = []
    for node_id, data in graph.nodes(data=True):
        node_key = str(node_id)
        nodes.append(
            {
                "id": node_key,
                "label": str(data.get("original_label", node_id)),
                "x": positions[node_key]["x"],
                "y": positions[node_key]["y"],
                "degree": int(graph.degree[node_id]),
            }
        )

    edges = [
        {"source": str(u), "target": str(v), "weight": float(graph[u][v].get("weight", 1.0))}
        for u, v in graph.edges
    ]

    return {
        "nodes": nodes,
        "edges": edges,
        "layout": layout,
    }


def _graph_from_network_payload(network: dict[str, Any]) -> nx.Graph:
    graph = nx.Graph()
    for node in network.get("nodes", []):
        node_id = node.get("label", node.get("id"))
        graph.add_node(node_id)
    for edge in network.get("edges", []):
        source = edge.get("source")
        target = edge.get("target")
        graph.add_edge(source, target, weight=float(edge.get("weight", 1.0)))
    return graph


def _simulation_payload(
    model: ChallengeABM,
    result: SimulationResult,
    layout: str,
    random_seed: int | None,
) -> dict[str, Any]:
    positions = _normalize_positions(model.graph, layout, random_seed)
    nodes = []
    for node_id, data in model.graph.nodes(data=True):
        node_key = str(node_id)
        agent = model.agents[model.node_to_agent_index[node_id]]
        nodes.append(
            {
                "id": node_key,
                "label": str(data.get("original_label", node_id)),
                "x": positions[node_key]["x"],
                "y": positions[node_key]["y"],
                "degree": int(model.graph.degree[node_id]),
                "seed": node_id in model.seed_nodes,
                "traits": {
                    "susceptibility": agent.susceptibility,
                    "conformity": agent.conformity,
                    "risk_aversion": agent.risk_aversion,
                    "share_tendency": agent.share_tendency,
                },
            }
        )

    edges = [
        {"source": str(u), "target": str(v), "weight": float(model.graph[u][v].get("weight", 1.0))}
        for u, v in model.graph.edges
    ]
    node_histories = [[state.value for state in agent.history] for agent in model.agents]

    return {
        "graph": {
            "nodes": nodes,
            "edges": edges,
        },
        "timeline": {
            "state_counts": result.state_counts,
            "node_histories": node_histories,
            "seed_nodes": [str(node) for node in model.seed_nodes],
        },
        "result": asdict(result),
        "ui": {
            "state_order": STATE_ORDER,
            "state_labels": STATE_LABELS,
            "state_colors": STATE_COLORS,
            "layout": layout,
            "time_steps": result.time_steps,
        },
    }


def create_network(payload: dict[str, Any]) -> dict[str, Any]:
    defaults = default_dashboard_config()
    topology = payload.get("topology", defaults["topology"])
    random_seed = payload.get("random_seed", defaults["simulation"]["random_seed"])
    random_seed = None if random_seed in {"", None} else _coerce_int(random_seed, defaults["simulation"]["random_seed"])
    graph = _build_network(topology, random_seed)
    layout = str(topology.get("layout", "spring")).strip().lower()
    return {
        "network": _build_network_payload(graph, layout=layout, random_seed=random_seed),
        "ui": {
            "layout": layout,
        },
    }


def relayout_network(payload: dict[str, Any]) -> dict[str, Any]:
    defaults = default_dashboard_config()
    network_payload = payload.get("network")
    if not isinstance(network_payload, dict) or not network_payload.get("nodes"):
        raise ValueError("A valid network payload is required for relayout.")

    layout = str(payload.get("layout", network_payload.get("layout", defaults["topology"]["layout"]))).strip().lower()
    random_seed = payload.get("random_seed", defaults["simulation"]["random_seed"])
    random_seed = None if random_seed in {"", None} else _coerce_int(random_seed, defaults["simulation"]["random_seed"])
    graph = _graph_from_network_payload(network_payload)
    return {
        "network": _build_network_payload(graph, layout=layout, random_seed=random_seed),
        "ui": {
            "layout": layout,
        },
    }


def simulate_dashboard(payload: dict[str, Any]) -> dict[str, Any]:
    defaults = default_dashboard_config()
    simulation = payload.get("simulation", defaults["simulation"])
    challenge_data = payload.get("challenge", defaults["challenge"])
    transition_data = _parse_json_object(payload.get("transition"), defaults["transition"])
    trait_data = _parse_json_object(payload.get("trait_distributions"), defaults["trait_distributions"])
    network_payload = payload.get("network")
    topology = payload.get("topology", defaults["topology"])

    random_seed = simulation.get("random_seed", defaults["simulation"]["random_seed"])
    random_seed = None if random_seed in {"", None} else _coerce_int(random_seed, defaults["simulation"]["random_seed"])

    if isinstance(network_payload, dict) and network_payload.get("nodes"):
        graph = _graph_from_network_payload(network_payload)
        layout = str(network_payload.get("layout", topology.get("layout", "spring"))).strip().lower()
    else:
        graph = _build_network(topology, random_seed)
        layout = str(topology.get("layout", "spring")).strip().lower()

    infected_nodes = _parse_seed_nodes(simulation.get("infected_nodes"))
    config = SimulationConfig(
        steps=_coerce_int(simulation.get("steps", defaults["simulation"]["steps"]), defaults["simulation"]["steps"]),
        seed_count=_coerce_int(simulation.get("seed_count", defaults["simulation"]["seed_count"]), defaults["simulation"]["seed_count"]),
        large_cascade_threshold=SimulationConfig().large_cascade_threshold,
        random_seed=random_seed,
        transition=_build_transition_parameters(transition_data),
        trait_distributions=_build_trait_distributions(trait_data),
    )

    challenge = Challenge(
        appeal=_coerce_float(challenge_data.get("appeal", defaults["challenge"]["appeal"]), defaults["challenge"]["appeal"]),
        severity=_coerce_float(challenge_data.get("severity", defaults["challenge"]["severity"]), defaults["challenge"]["severity"]),
    )
    model = ChallengeABM(peer_network=graph, infected_nodes=infected_nodes, config=config, challenge=challenge)
    result = model.run()
    response = _simulation_payload(model, result, layout=layout, random_seed=random_seed)
    if isinstance(network_payload, dict) and network_payload.get("nodes"):
        response["network"] = network_payload
    else:
        response["network"] = response["graph"]
    return response


def _read_static(name: str) -> bytes:
    path = STATIC_DIR / name
    return path.read_bytes()


class DashboardRequestHandler(BaseHTTPRequestHandler):
    server_version = "ChallengeABMDashboard/1.0"

    def _send_json(self, data: Any, status: int = 200) -> None:
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_file(self, path: Path, content_type: str | None = None) -> None:
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type or mimetypes.guess_type(path.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path in {"/", "/index.html"}:
            self._send_file(STATIC_DIR / "index.html", "text/html; charset=utf-8")
            return
        if self.path == "/app.js":
            self._send_file(STATIC_DIR / "app.js", "application/javascript; charset=utf-8")
            return
        if self.path == "/styles.css":
            self._send_file(STATIC_DIR / "styles.css", "text/css; charset=utf-8")
            return
        if self.path == "/api/defaults":
            self._send_json(default_dashboard_config())
            return
        if self.path == "/api/network":
            self.send_error(405, "Method Not Allowed")
            return
        self.send_error(404, "Not Found")

    def do_POST(self) -> None:  # noqa: N802
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            content_length = 0
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            self._send_json({"error": f"Invalid JSON payload: {exc.msg}"}, status=400)
            return

        try:
            if self.path == "/api/network":
                response = create_network(payload if isinstance(payload, dict) else {})
            elif self.path == "/api/layout":
                response = relayout_network(payload if isinstance(payload, dict) else {})
            elif self.path == "/api/simulate":
                response = simulate_dashboard(payload if isinstance(payload, dict) else {})
            else:
                self.send_error(404, "Not Found")
                return
        except Exception as exc:  # pragma: no cover - surfaced to browser
            self._send_json({"error": str(exc)}, status=400)
            return
        self._send_json(response)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return


def run_dashboard(host: str = "127.0.0.1", port: int = DEFAULT_PORT, open_browser: bool = True) -> None:
    server = ThreadingHTTPServer((host, port), DashboardRequestHandler)
    url = f"http://{host}:{port}/"
    print(f"ChallengeABM dashboard available at {url}")
    if open_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch the ChallengeABM interactive dashboard.")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind to.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="TCP port for the local dashboard.")
    parser.add_argument("--no-browser", action="store_true", help="Do not open a browser automatically.")
    args = parser.parse_args()
    run_dashboard(host=args.host, port=args.port, open_browser=not args.no_browser)


if __name__ == "__main__":
    main()
