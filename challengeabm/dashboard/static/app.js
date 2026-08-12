const stateOrder = ["U", "O", "P", "A", "C", "D"];
const neutralFill = "#cfd7df";
const seedFill = "#ffb000";

const dashboard = {
  networkData: null,
  simulationData: null,
  modelConfiguration: null,
  time: 0,
  timer: null,
  running: false,
  selectedSeeds: new Set(),
};

const els = {};

function hexToRgb(hex) {
  const value = hex.replace("#", "");
  const bigint = parseInt(value, 16);
  return {
    r: (bigint >> 16) & 255,
    g: (bigint >> 8) & 255,
    b: bigint & 255,
  };
}

function rgba(hex, alpha) {
  const { r, g, b } = hexToRgb(hex);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function setFieldValue(id, value) {
  if (!(id in els) || !els[id]) {
    return;
  }
  els[id].value = value ?? "";
}

function numberValue(id) {
  const raw = els[id].value.trim();
  return raw === "" ? null : Number(raw);
}

function requiredNumberValue(id) {
  return Number(els[id].value);
}

function parseNumberList(text, fallback) {
  const raw = text.trim();
  if (!raw) {
    return fallback;
  }
  try {
    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed)) {
      return parsed.map((item) => Number(item)).filter((item) => Number.isFinite(item));
    }
  } catch (error) {
    // Fall back to comma/newline separated parsing.
  }
  return raw
    .replace(/\n/g, ",")
    .split(",")
    .map((item) => Number(item.trim()))
    .filter((item) => Number.isFinite(item));
}

function parseNumberMatrix(text, fallback) {
  const raw = text.trim();
  if (!raw) {
    return fallback;
  }
  try {
    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed) && parsed.every((row) => Array.isArray(row))) {
      const matrix = parsed.map((row) => row.map((item) => Number(item)));
      if (matrix.every((row) => row.every((item) => Number.isFinite(item)))) {
        return matrix;
      }
    }
  } catch (error) {
    // Use fallback below.
  }
  return fallback;
}

function distributionParametersFromInputs(prefix) {
  return [numberValue(`${prefix}-p1`), numberValue(`${prefix}-p2`), numberValue(`${prefix}-p3`)].filter(
    (value) => value !== null,
  );
}

function setDistributionDefaults(prefix, spec) {
  setFieldValue(`${prefix}-kind`, spec?.kind ?? "beta");
  const params = Array.isArray(spec?.parameters) ? spec.parameters : [];
  setFieldValue(`${prefix}-p1`, params[0]);
  setFieldValue(`${prefix}-p2`, params[1]);
  setFieldValue(`${prefix}-p3`, params[2]);
  const clip = spec?.clip;
  const clipEl = els[`${prefix}-clip`];
  if (clipEl) {
    clipEl.checked = clip !== undefined ? Boolean(clip) : true;
  }
}

function buildDistributionPayload(prefix) {
  return {
    kind: els[`${prefix}-kind`].value,
    parameters: distributionParametersFromInputs(prefix),
    clip: Boolean(els[`${prefix}-clip`].checked),
  };
}

function setTransitionDefaults(defaults) {
  setFieldValue("transition-awareness-lambda", defaults.awareness_lambda);
  setFieldValue("transition-participation-intercept", defaults.participation_intercept);
  setFieldValue("transition-participation-appeal", defaults.participation_appeal);
  setFieldValue("transition-participation-susceptibility", defaults.participation_susceptibility);
  setFieldValue("transition-participation-conformity", defaults.participation_conformity);
  setFieldValue("transition-participation-risk", defaults.participation_risk);
  setFieldValue("transition-amplification-intercept", defaults.amplification_intercept);
  setFieldValue("transition-amplification-share", defaults.amplification_share);
  setFieldValue("transition-amplification-exposure", defaults.amplification_exposure);
  setFieldValue("transition-amplification-conformity", defaults.amplification_conformity);
  setFieldValue("transition-counter-intercept", defaults.counter_intercept);
  setFieldValue("transition-counter-risk", defaults.counter_risk);
  setFieldValue("transition-counter-exposure", defaults.counter_exposure);
  setFieldValue("transition-counter-effectiveness", defaults.counter_effectiveness);
  setFieldValue("transition-dropout-intercept", defaults.dropout_intercept);
  setFieldValue("transition-dropout-risk", defaults.dropout_risk);
  setFieldValue("transition-dropout-exposure", defaults.dropout_exposure);
  setFieldValue("transition-spontaneous-dropout", defaults.spontaneous_dropout);
}

function buildTransitionPayload() {
  return {
    awareness_lambda: requiredNumberValue("transition-awareness-lambda"),
    participation_intercept: requiredNumberValue("transition-participation-intercept"),
    participation_appeal: requiredNumberValue("transition-participation-appeal"),
    participation_susceptibility: requiredNumberValue("transition-participation-susceptibility"),
    participation_conformity: requiredNumberValue("transition-participation-conformity"),
    participation_risk: requiredNumberValue("transition-participation-risk"),
    amplification_intercept: requiredNumberValue("transition-amplification-intercept"),
    amplification_share: requiredNumberValue("transition-amplification-share"),
    amplification_exposure: requiredNumberValue("transition-amplification-exposure"),
    amplification_conformity: requiredNumberValue("transition-amplification-conformity"),
    counter_intercept: requiredNumberValue("transition-counter-intercept"),
    counter_risk: requiredNumberValue("transition-counter-risk"),
    counter_exposure: requiredNumberValue("transition-counter-exposure"),
    counter_effectiveness: requiredNumberValue("transition-counter-effectiveness"),
    dropout_intercept: requiredNumberValue("transition-dropout-intercept"),
    dropout_risk: requiredNumberValue("transition-dropout-risk"),
    dropout_exposure: requiredNumberValue("transition-dropout-exposure"),
    spontaneous_dropout: requiredNumberValue("transition-spontaneous-dropout"),
  };
}

function setSummary(items) {
  els["summary-list"].innerHTML = items
    .map(([label, value]) => `<dt>${label}</dt><dd>${value}</dd>`)
    .join("");
}

function setStatus(text) {
  els["status-label"].textContent = text;
}

function setTimeNote(text) {
  els["time-note"].textContent = text;
}

function syncSelectedSeedsDisplay() {
  els["selected-seeds"].value = Array.from(dashboard.selectedSeeds).join(", ");
}

function getTopologyKind() {
  return els["topology-kind"].value;
}

function updateTopologyFieldsVisibility() {
  const kind = getTopologyKind();
  document.querySelectorAll(".topology-fields").forEach((group) => {
    group.classList.toggle("hidden", group.dataset.topology !== kind);
  });
}

function setWorkflowStage(stage) {
  const stepNetwork = els["step-network"];
  const stepModel = els["step-model"];
  const stepSimulation = els["step-simulation"];

  if (!stepNetwork || !stepModel || !stepSimulation) {
    return;
  }

  stepNetwork.open = stage === "network";
  stepModel.open = stage === "model";
  stepSimulation.open = stage === "simulation";
}

function getLayoutValue() {
  return els["topology-layout"].value;
}

function setLayoutValue(layout) {
  els["topology-layout"].value = layout;
}

function handleLayoutChange() {
  if (!dashboard.networkData) {
    return;
  }
  relayoutNetwork().catch((error) => {
    setStatus(error.message);
    console.error(error);
  });
}

function setStepControlsEnabled(enabled) {
  els["run-btn"].disabled = !(enabled && dashboard.modelConfiguration);
}

function invalidateModelConfiguration() {
  if (dashboard.modelConfiguration === null) {
    return;
  }
  dashboard.modelConfiguration = null;
  if (dashboard.simulationData) {
    dashboard.simulationData = null;
    stopPlayback();
    setPlotsVisible(false);
    setPlaybackControlsEnabled(false);
  }
  if (dashboard.networkData) {
    setWorkflowStage("model");
  }
  setStepControlsEnabled(Boolean(dashboard.networkData));
  setStatus("Model configuration changed. Reconfigure before running the simulation.");
  renderDashboard();
}

function setPlaybackControlsEnabled(enabled) {
  els["play-btn"].disabled = !enabled;
  els["step-back-btn"].disabled = !enabled;
  els["step-forward-btn"].disabled = !enabled;
  els["time-slider"].disabled = !enabled;
}

function setPlotsVisible(visible) {
  els["plots-grid"].classList.toggle("hidden", !visible);
}

function setNetworkVisible(visible) {
  els["network-placeholder"].classList.toggle("hidden", visible);
  els["network-stage"].classList.toggle("hidden", !visible);
}

function stopPlayback() {
  dashboard.running = false;
  if (dashboard.timer) {
    clearInterval(dashboard.timer);
    dashboard.timer = null;
  }
  els["play-btn"].textContent = "Play";
}

function startPlayback() {
  if (!dashboard.simulationData) {
    return;
  }
  const interval = Math.max(80, 1000 / Number(els["speed-range"].value));
  stopPlayback();
  dashboard.running = true;
  els["play-btn"].textContent = "Pause";
  dashboard.timer = setInterval(() => {
    if (!dashboard.simulationData) {
      stopPlayback();
      return;
    }
    if (dashboard.time >= dashboard.simulationData.timeline.state_counts.length - 1) {
      stopPlayback();
      return;
    }
    setTime(dashboard.time + 1);
  }, interval);
}

function togglePlayback() {
  if (dashboard.running) {
    stopPlayback();
  } else {
    startPlayback();
  }
}

function clearSvg(svg) {
  while (svg.firstChild) {
    svg.removeChild(svg.firstChild);
  }
}

function currentNodeData(nodeId) {
  if (dashboard.simulationData && dashboard.simulationData.graph) {
    return dashboard.simulationData.graph.nodes.find((node) => node.id === nodeId) || null;
  }
  if (dashboard.networkData) {
    return dashboard.networkData.nodes.find((node) => node.id === nodeId) || null;
  }
  return null;
}

function currentNodeState(nodeId, time) {
  if (!dashboard.simulationData) {
    return null;
  }
  const histories = dashboard.simulationData.timeline.node_histories || [];
  const index = dashboard.networkData.nodes.findIndex((node) => node.id === nodeId);
  if (index < 0 || !histories[index]) {
    return null;
  }
  return histories[index][time] || "U";
}

function renderNetwork() {
  const svg = els["network-svg"];
  clearSvg(svg);

  if (!dashboard.networkData) {
    setNetworkVisible(false);
    setTimeNote("Network not created yet");
    return;
  }

  setNetworkVisible(true);
  const ns = "http://www.w3.org/2000/svg";
  const width = 1000;
  const height = 720;
  const positions = new Map(dashboard.networkData.nodes.map((node) => [node.id, node]));
  const seedNodes = dashboard.selectedSeeds;

  const defs = document.createElementNS(ns, "defs");
  const marker = document.createElementNS(ns, "marker");
  marker.setAttribute("id", "arrowhead");
  marker.setAttribute("viewBox", "0 0 10 10");
  marker.setAttribute("refX", "8");
  marker.setAttribute("refY", "5");
  marker.setAttribute("markerWidth", "6");
  marker.setAttribute("markerHeight", "6");
  marker.setAttribute("orient", "auto-start-reverse");
  const path = document.createElementNS(ns, "path");
  path.setAttribute("d", "M 0 0 L 10 5 L 0 10 z");
  path.setAttribute("fill", "rgba(23,32,42,0.25)");
  marker.appendChild(path);
  defs.appendChild(marker);
  svg.appendChild(defs);

  dashboard.networkData.edges.forEach((edge) => {
    const source = positions.get(edge.source);
    const target = positions.get(edge.target);
    if (!source || !target) {
      return;
    }
    const line = document.createElementNS(ns, "line");
    line.setAttribute("x1", String(source.x * width));
    line.setAttribute("y1", String(source.y * height));
    line.setAttribute("x2", String(target.x * width));
    line.setAttribute("y2", String(target.y * height));
    line.setAttribute("stroke", "rgba(23,32,42,0.16)");
    line.setAttribute("stroke-width", String(0.6 + edge.weight * 1.4));
    line.setAttribute("marker-end", "url(#arrowhead)");
    svg.appendChild(line);
  });

  dashboard.networkData.nodes.forEach((node) => {
    const state = currentNodeState(node.id, dashboard.time) || null;
    const circle = document.createElementNS(ns, "circle");
    circle.setAttribute("cx", String(node.x * width));
    circle.setAttribute("cy", String(node.y * height));
    circle.setAttribute("r", String(8 + Math.min(8, node.degree * 0.14)));
    circle.setAttribute("fill", state ? (dashboard.simulationData.ui.state_colors[state] || neutralFill) : neutralFill);
    circle.setAttribute("stroke", seedNodes.has(node.id) ? seedFill : "rgba(23,32,42,0.4)");
    circle.setAttribute("stroke-width", seedNodes.has(node.id) ? "3" : "1.2");
    circle.setAttribute("opacity", "0.98");
    circle.style.cursor = "pointer";

    circle.addEventListener("click", () => toggleSeed(node.id));

    const title = document.createElementNS(ns, "title");
    if (dashboard.simulationData) {
      const simNode = currentNodeData(node.id);
      const stateLabel = dashboard.simulationData.ui.state_labels[state] || state;
      title.textContent = [
        `Node ${simNode?.label || node.label}`,
        `State: ${stateLabel}`,
        `Susceptibility: ${simNode?.traits?.susceptibility?.toFixed?.(2) ?? "n/a"}`,
        `Conformity: ${simNode?.traits?.conformity?.toFixed?.(2) ?? "n/a"}`,
        `Risk aversion: ${simNode?.traits?.risk_aversion?.toFixed?.(2) ?? "n/a"}`,
        `Share tendency: ${simNode?.traits?.share_tendency?.toFixed?.(2) ?? "n/a"}`,
      ].join("\n");
    } else {
      title.textContent = [
        `Node ${node.label}`,
        `Degree: ${node.degree}`,
        seedNodes.has(node.id) ? "Selected as seed" : "Click to select as seed",
      ].join("\n");
    }
    circle.appendChild(title);
    svg.appendChild(circle);
  });

  if (dashboard.simulationData) {
    setTimeNote(`Simulation loaded: t = ${dashboard.time}`);
  } else {
    setTimeNote("Click nodes to select seeds");
  }
}

function prepareCanvas(canvas) {
  const width = canvas.clientWidth;
  const dpr = window.devicePixelRatio || 1;
  const displayWidth = Math.max(10, Math.floor(width * dpr));
  const displayHeight = Math.max(10, Math.floor(Number(canvas.getAttribute("data-aspect") || 0.34) * width * dpr));
  if (canvas.width !== displayWidth || canvas.height !== displayHeight) {
    canvas.width = displayWidth;
    canvas.height = displayHeight;
  }
  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, canvas.clientWidth, canvas.clientHeight);
  return ctx;
}

function drawAxes(ctx, width, height, margin) {
  ctx.strokeStyle = "rgba(23,32,42,0.2)";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(margin.left, margin.top);
  ctx.lineTo(margin.left, height - margin.bottom);
  ctx.lineTo(width - margin.right, height - margin.bottom);
  ctx.stroke();
}

function renderTrend() {
  if (!dashboard.simulationData) {
    return;
  }
  const canvas = els["trend-canvas"];
  canvas.setAttribute("data-aspect", "0.34");
  const ctx = prepareCanvas(canvas);
  const width = canvas.clientWidth;
  const height = Math.max(260, Math.round(width * 0.34));
  canvas.style.height = `${height}px`;

  const margin = { top: 20, right: 20, bottom: 36, left: 48 };
  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;
  drawAxes(ctx, width, height, margin);

  const counts = dashboard.simulationData.timeline.state_counts;
  const maxValue = Math.max(1, ...counts.flatMap((row) => stateOrder.map((state) => row[state] || 0)));
  const xStep = plotWidth / Math.max(1, counts.length - 1);
  const yScale = plotHeight / maxValue;

  ctx.font = "12px Inter, sans-serif";
  ctx.fillStyle = "#5b6674";
  ctx.fillText("0", 18, height - margin.bottom);
  ctx.fillText(String(maxValue), 8, margin.top + 12);

  stateOrder.forEach((state) => {
    ctx.beginPath();
    counts.forEach((row, index) => {
      const x = margin.left + index * xStep;
      const y = height - margin.bottom - (row[state] || 0) * yScale;
      if (index === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });
    ctx.strokeStyle = dashboard.simulationData.ui.state_colors[state];
    ctx.lineWidth = 2.5;
    ctx.stroke();
  });

  const markerX = margin.left + dashboard.time * xStep;
  ctx.strokeStyle = "rgba(23,32,42,0.6)";
  ctx.setLineDash([6, 6]);
  ctx.beginPath();
  ctx.moveTo(markerX, margin.top);
  ctx.lineTo(markerX, height - margin.bottom);
  ctx.stroke();
  ctx.setLineDash([]);
}

function mixColor(hex, alpha) {
  const { r, g, b } = hexToRgb(hex);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function renderDensity() {
  if (!dashboard.simulationData) {
    return;
  }
  const canvas = els["density-canvas"];
  canvas.setAttribute("data-aspect", "0.34");
  const ctx = prepareCanvas(canvas);
  const width = canvas.clientWidth;
  const height = Math.max(260, Math.round(width * 0.34));
  canvas.style.height = `${height}px`;

  const margin = { top: 18, right: 20, bottom: 22, left: 82 };
  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;
  const rows = stateOrder.length;
  const cols = dashboard.simulationData.timeline.state_counts.length;
  const cellW = plotWidth / Math.max(1, cols);
  const cellH = plotHeight / Math.max(1, rows);
  const totalNodes = dashboard.networkData?.nodes.length || 1;

  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, width, height);

  for (let rowIndex = 0; rowIndex < rows; rowIndex += 1) {
    const state = stateOrder[rowIndex];
    for (let colIndex = 0; colIndex < cols; colIndex += 1) {
      const value = (dashboard.simulationData.timeline.state_counts[colIndex][state] || 0) / totalNodes;
      ctx.fillStyle = mixColor(dashboard.simulationData.ui.state_colors[state], 0.18 + value * 0.82);
      ctx.fillRect(
        margin.left + colIndex * cellW,
        margin.top + rowIndex * cellH,
        cellW + 0.5,
        cellH + 0.5,
      );
    }
  }

  ctx.strokeStyle = "rgba(23,32,42,0.35)";
  ctx.strokeRect(margin.left, margin.top, plotWidth, plotHeight);
  ctx.fillStyle = "#5b6674";
  ctx.font = "12px Inter, sans-serif";
  stateOrder.forEach((state, idx) => {
    ctx.fillText(dashboard.simulationData.ui.state_labels[state], 12, margin.top + idx * cellH + cellH * 0.63);
  });

  const markerX = margin.left + dashboard.time * cellW;
  ctx.strokeStyle = "rgba(23,32,42,0.65)";
  ctx.setLineDash([5, 5]);
  ctx.beginPath();
  ctx.moveTo(markerX, margin.top);
  ctx.lineTo(markerX, margin.top + plotHeight);
  ctx.stroke();
  ctx.setLineDash([]);
}

function renderTrajectory() {
  if (!dashboard.simulationData) {
    return;
  }

  const canvas = els["trajectory-canvas"];
  canvas.setAttribute("data-aspect", "0.42");
  const ctx = prepareCanvas(canvas);
  const width = canvas.clientWidth;
  const rows = dashboard.networkData?.nodes.length || 0;
  const height = Math.max(300, Math.min(560, Math.round(Math.max(1, rows) * 3.4) + 56));
  canvas.style.height = `${height}px`;

  const margin = { top: 18, right: 18, bottom: 28, left: 96 };
  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;
  const timeSteps = dashboard.simulationData.timeline.state_counts.length;
  const histories = dashboard.simulationData.timeline.node_histories || [];
  const cellW = plotWidth / Math.max(1, timeSteps);
  const cellH = plotHeight / Math.max(1, rows);
  const labelStep = Math.max(1, Math.ceil(rows / 8));

  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, width, height);

  for (let rowIndex = 0; rowIndex < rows; rowIndex += 1) {
    const node = dashboard.networkData.nodes[rowIndex];
    const history = histories[rowIndex] || [];
    for (let colIndex = 0; colIndex < timeSteps; colIndex += 1) {
      const state = history[colIndex] || "U";
      ctx.fillStyle = dashboard.simulationData.ui.state_colors[state] || neutralFill;
      ctx.fillRect(
        margin.left + colIndex * cellW,
        margin.top + rowIndex * cellH,
        cellW + 0.5,
        cellH + 0.5,
      );
    }
    if (rowIndex % labelStep === 0 || rowIndex === rows - 1) {
      ctx.fillStyle = "#5b6674";
      ctx.font = "12px Inter, sans-serif";
      const label = node?.label ?? String(rowIndex);
      ctx.fillText(label, 14, margin.top + rowIndex * cellH + Math.min(cellH * 0.72, 12));
    }
  }

  ctx.strokeStyle = "rgba(23,32,42,0.35)";
  ctx.strokeRect(margin.left, margin.top, plotWidth, plotHeight);

  ctx.fillStyle = "#5b6674";
  ctx.font = "12px Inter, sans-serif";
  ctx.fillText("0", margin.left, height - 8);
  ctx.fillText(String(Math.max(0, timeSteps - 1)), width - margin.right - 18, height - 8);
  ctx.fillText("Agent", 16, 14);
  ctx.fillText("Time step", width / 2 - 28, height - 8);

  const markerX = margin.left + dashboard.time * cellW;
  ctx.strokeStyle = "rgba(23,32,42,0.75)";
  ctx.setLineDash([5, 5]);
  ctx.beginPath();
  ctx.moveTo(markerX, margin.top);
  ctx.lineTo(markerX, margin.top + plotHeight);
  ctx.stroke();
  ctx.setLineDash([]);
}

function renderCounts() {
  if (!dashboard.simulationData) {
    els["counts-list"].innerHTML = '<div class="count-item"><span class="count-label">No simulation yet</span><strong>-</strong></div>';
    return;
  }

  const counts = dashboard.simulationData.timeline.state_counts[dashboard.time] || {};
  els["counts-list"].innerHTML = dashboard.simulationData.ui.state_order
    .map((state) => {
      const count = counts[state] ?? 0;
      return `
        <div class="count-item">
          <span class="count-label">
            <span class="count-swatch" style="background:${dashboard.simulationData.ui.state_colors[state]}"></span>
            ${dashboard.simulationData.ui.state_labels[state]}
          </span>
          <strong>${count}</strong>
        </div>
      `;
    })
    .join("");
}

function renderSummary() {
  if (!dashboard.networkData) {
    setSummary([["Status", "Create a network to begin"]]);
    return;
  }

  if (!dashboard.simulationData) {
    setSummary([
      ["Nodes", dashboard.networkData.nodes.length],
      ["Edges", dashboard.networkData.edges.length],
      ["Selected seeds", dashboard.selectedSeeds.size],
      ["Layout", dashboard.networkData.layout],
    ]);
    return;
  }

  const result = dashboard.simulationData.result;
  const counts = dashboard.simulationData.timeline.state_counts[dashboard.time] || {};
  setSummary([
    ["Time step", `${dashboard.time} / ${dashboard.simulationData.ui.time_steps}`],
    ["Final reach", Number(result.final_reach).toFixed(3)],
    ["Peak participants", result.peak_participants],
    ["Peak time", result.time_of_peak_participation],
    ["Cascade duration", result.cascade_duration],
    ["Large cascade", result.large_cascade ? "Yes" : "No"],
    ["Current O", counts.O ?? 0],
    ["Current P", counts.P ?? 0],
    ["Current A", counts.A ?? 0],
    ["Current C", counts.C ?? 0],
    ["Current D", counts.D ?? 0],
  ]);
}

function renderDashboard() {
  renderNetwork();
  renderSummary();
  renderCounts();
  if (dashboard.simulationData) {
    renderTrend();
    renderDensity();
    renderTrajectory();
    setPlotsVisible(true);
    setPlaybackControlsEnabled(true);
    els["time-slider"].max = String(dashboard.simulationData.timeline.state_counts.length - 1);
    els["time-slider"].value = String(dashboard.time);
    els["time-label"].textContent = `t = ${dashboard.time}`;
  } else {
    setPlotsVisible(false);
    setPlaybackControlsEnabled(false);
    els["time-slider"].max = "0";
    els["time-slider"].value = "0";
    els["time-label"].textContent = "t = 0";
  }
  syncSelectedSeedsDisplay();
}

function toggleSeed(nodeId) {
  if (!dashboard.networkData) {
    return;
  }
  const key = String(nodeId);
  if (dashboard.selectedSeeds.has(key)) {
    dashboard.selectedSeeds.delete(key);
  } else {
    dashboard.selectedSeeds.add(key);
  }
  if (dashboard.simulationData) {
    dashboard.simulationData = null;
    stopPlayback();
  }
  invalidateModelConfiguration();
  syncSelectedSeedsDisplay();
  setStatus(dashboard.selectedSeeds.size ? "Seed set updated." : "Seed set cleared.");
  renderDashboard();
}

function resetDashboard() {
  stopPlayback();
  dashboard.networkData = null;
  dashboard.simulationData = null;
  dashboard.modelConfiguration = null;
  dashboard.time = 0;
  dashboard.selectedSeeds.clear();
  setWorkflowStage("network");
  setStepControlsEnabled(false);
  setPlaybackControlsEnabled(false);
  setPlotsVisible(false);
  setNetworkVisible(false);
  els["time-slider"].max = "0";
  els["time-slider"].value = "0";
  els["time-label"].textContent = "t = 0";
  setTimeNote("Network not created yet");
  setStatus("Create a network to begin.");
  syncSelectedSeedsDisplay();
  renderSummary();
  renderCounts();
}

function buildTopologyPayload() {
  const kind = getTopologyKind();
  const layout = getLayoutValue();

  switch (kind) {
    case "watts_strogatz":
      return {
        kind,
        layout,
        n: requiredNumberValue("topology-ws-n"),
        k: requiredNumberValue("topology-ws-k"),
        p: requiredNumberValue("topology-ws-p"),
      };
    case "erdos_renyi":
      return {
        kind,
        layout,
        n: requiredNumberValue("topology-er-n"),
        p: requiredNumberValue("topology-er-p"),
      };
    case "barabasi_albert":
      return {
        kind,
        layout,
        n: requiredNumberValue("topology-ba-n"),
        m: requiredNumberValue("topology-ba-m"),
      };
    case "newman_watts_strogatz":
      return {
        kind,
        layout,
        n: requiredNumberValue("topology-nws-n"),
        k: requiredNumberValue("topology-nws-k"),
        p: requiredNumberValue("topology-nws-p"),
      };
    case "powerlaw_cluster":
      return {
        kind,
        layout,
        n: requiredNumberValue("topology-pc-n"),
        m: requiredNumberValue("topology-pc-m"),
        p: requiredNumberValue("topology-pc-p"),
      };
    case "sbm":
      return {
        kind,
        layout,
        sizes: parseNumberList(els["topology-sbm-sizes"].value, [40, 40, 40]),
        probabilities: parseNumberMatrix(els["topology-sbm-probabilities"].value, [
          [0.14, 0.03, 0.02],
          [0.03, 0.13, 0.03],
          [0.02, 0.03, 0.12],
        ]),
      };
    case "lfr":
      return {
        kind,
        layout,
        n: requiredNumberValue("topology-lfr-n"),
        tau1: requiredNumberValue("topology-lfr-tau1"),
        tau2: requiredNumberValue("topology-lfr-tau2"),
        mu: requiredNumberValue("topology-lfr-mu"),
        average_degree: numberValue("topology-lfr-average-degree"),
        min_degree: numberValue("topology-lfr-min-degree"),
        max_degree: numberValue("topology-lfr-max-degree"),
        min_community: numberValue("topology-lfr-min-community"),
        max_community: numberValue("topology-lfr-max-community"),
        max_iters: requiredNumberValue("topology-lfr-max-iters"),
      };
    case "path":
      return {
        kind,
        layout,
        n: requiredNumberValue("topology-path-n"),
      };
    default:
      return { kind, layout };
  }
}

function buildSimulationPayload() {
  return {
    steps: Number(els["simulation-steps"].value),
    seed_count: Number(els["simulation-seed-count"].value),
    random_seed: els["simulation-random-seed"].value === "" ? null : Number(els["simulation-random-seed"].value),
    infected_nodes: Array.from(dashboard.selectedSeeds),
  };
}

function buildModelConfiguration() {
  const payload = {
    simulation: buildSimulationPayload(),
    challenge: {
      appeal: Number(els["challenge-appeal"].value),
      severity: Number(els["challenge-severity"].value),
    },
    transition: buildTransitionPayload(),
    trait_distributions: {
      susceptibility: buildDistributionPayload("trait-susceptibility"),
      conformity: buildDistributionPayload("trait-conformity"),
      risk_aversion: buildDistributionPayload("trait-risk-aversion"),
      share_tendency: buildDistributionPayload("trait-share-tendency"),
    },
  };
  return payload;
}

function buildSimulationRequestPayload(includeNetwork = false) {
  if (!dashboard.modelConfiguration) {
    throw new Error("Configure the model before running the simulation.");
  }

  const payload = {
    topology: buildTopologyPayload(),
    ...dashboard.modelConfiguration,
  };
  if (includeNetwork && dashboard.networkData) {
    payload.network = dashboard.networkData;
  }
  return payload;
}

async function relayoutNetwork() {
  if (!dashboard.networkData) {
    return;
  }
  const response = await fetch("/api/layout", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      network: dashboard.networkData,
      layout: getLayoutValue(),
      random_seed: els["simulation-random-seed"].value === "" ? null : Number(els["simulation-random-seed"].value),
    }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Layout update failed");
  }
  dashboard.networkData = data.network;
  renderDashboard();
}

async function configureModel() {
  if (!dashboard.networkData) {
    setStatus("Create a network first.");
    return;
  }
  stopPlayback();
  dashboard.modelConfiguration = buildModelConfiguration();
  dashboard.simulationData = null;
  dashboard.time = 0;
  setWorkflowStage("simulation");
  setStepControlsEnabled(true);
  setPlaybackControlsEnabled(false);
  setPlotsVisible(false);
  setStatus("Model configured. Proceed to simulation execution.");
  renderDashboard();
}

async function createNetwork() {
  stopPlayback();
  setStatus("Creating network...");
  const response = await fetch("/api/network", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      topology: buildTopologyPayload(),
      random_seed: els["simulation-random-seed"].value === "" ? null : Number(els["simulation-random-seed"].value),
    }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Network creation failed");
  }
  dashboard.networkData = data.network;
  dashboard.simulationData = null;
  dashboard.time = 0;
  dashboard.selectedSeeds.clear();
  setWorkflowStage("model");
  setStepControlsEnabled(true);
  setPlaybackControlsEnabled(false);
  setPlotsVisible(false);
  setNetworkVisible(true);
  setStatus(`Network created: ${dashboard.networkData.nodes.length} nodes, ${dashboard.networkData.edges.length} edges.`);
  syncSelectedSeedsDisplay();
  renderDashboard();
}

async function runSimulation() {
  if (!dashboard.networkData) {
    setStatus("Create a network first.");
    return;
  }
  if (!dashboard.modelConfiguration) {
    setStatus("Configure the model before running the simulation.");
    return;
  }
  stopPlayback();
  setStatus("Running simulation...");
  const payload = buildSimulationRequestPayload(true);
  const response = await fetch("/api/simulate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Simulation failed");
  }
  dashboard.networkData = data.network || dashboard.networkData;
  dashboard.simulationData = data;
  dashboard.time = 0;
  setWorkflowStage("simulation");
  setPlotsVisible(true);
  setPlaybackControlsEnabled(true);
  setStepControlsEnabled(true);
  setStatus(`Simulation loaded: ${data.result.final_reach.toFixed(3)} final reach.`);
  renderDashboard();
}

function bindEvents() {
  els["create-network-btn"].addEventListener("click", () => {
    createNetwork().catch((error) => {
      setStatus(error.message);
      console.error(error);
    });
  });

  els["configure-btn"].addEventListener("click", () => {
    configureModel().catch((error) => {
      setStatus(error.message);
      console.error(error);
    });
  });

  els["run-btn"].addEventListener("click", () => {
    runSimulation().catch((error) => {
      setStatus(error.message);
      console.error(error);
    });
  });

  els["reset-btn"].addEventListener("click", () => {
    resetDashboard();
  });

  els["clear-seeds-btn"].addEventListener("click", () => {
    dashboard.selectedSeeds.clear();
    if (dashboard.simulationData) {
      dashboard.simulationData = null;
      stopPlayback();
      setPlotsVisible(false);
      setPlaybackControlsEnabled(false);
    }
    invalidateModelConfiguration();
    syncSelectedSeedsDisplay();
    setStatus("Seed set cleared.");
    renderDashboard();
  });

  els["topology-kind"].addEventListener("change", () => {
    updateTopologyFieldsVisibility();
  });

  els["topology-layout"].addEventListener("change", handleLayoutChange);
  els["topology-layout"].addEventListener("input", handleLayoutChange);

  els["play-btn"].addEventListener("click", togglePlayback);
  els["step-back-btn"].addEventListener("click", () => {
    stopPlayback();
    setTime(dashboard.time - 1);
  });
  els["step-forward-btn"].addEventListener("click", () => {
    stopPlayback();
    setTime(dashboard.time + 1);
  });
  els["time-slider"].addEventListener("input", (event) => {
    stopPlayback();
    setTime(Number(event.target.value));
  });
  els["speed-range"].addEventListener("input", () => {
    if (dashboard.running) {
      startPlayback();
    }
  });
  window.addEventListener("resize", () => {
    if (dashboard.networkData) {
      renderDashboard();
    }
  });
}

function setTime(time) {
  if (!dashboard.simulationData) {
    dashboard.time = 0;
    renderDashboard();
    return;
  }
  const maxTime = dashboard.simulationData.timeline.state_counts.length - 1;
  dashboard.time = clamp(time, 0, maxTime);
  els["time-slider"].value = String(dashboard.time);
  els["time-label"].textContent = `t = ${dashboard.time}`;
  renderDashboard();
}

async function init() {
  els["create-network-btn"] = document.getElementById("create-network-btn");
  els["run-btn"] = document.getElementById("run-btn");
  els["reset-btn"] = document.getElementById("reset-btn");
  els["clear-seeds-btn"] = document.getElementById("clear-seeds-btn");
  els["step-network"] = document.getElementById("step-network");
  els["step-model"] = document.getElementById("step-model");
  els["step-simulation"] = document.getElementById("step-simulation");
  els["topology-kind"] = document.getElementById("topology-kind");
  els["topology-layout"] = document.getElementById("topology-layout");
  els["topology-ws-n"] = document.getElementById("topology-ws-n");
  els["topology-ws-k"] = document.getElementById("topology-ws-k");
  els["topology-ws-p"] = document.getElementById("topology-ws-p");
  els["topology-er-n"] = document.getElementById("topology-er-n");
  els["topology-er-p"] = document.getElementById("topology-er-p");
  els["topology-ba-n"] = document.getElementById("topology-ba-n");
  els["topology-ba-m"] = document.getElementById("topology-ba-m");
  els["topology-nws-n"] = document.getElementById("topology-nws-n");
  els["topology-nws-k"] = document.getElementById("topology-nws-k");
  els["topology-nws-p"] = document.getElementById("topology-nws-p");
  els["topology-pc-n"] = document.getElementById("topology-pc-n");
  els["topology-pc-m"] = document.getElementById("topology-pc-m");
  els["topology-pc-p"] = document.getElementById("topology-pc-p");
  els["topology-sbm-sizes"] = document.getElementById("topology-sbm-sizes");
  els["topology-sbm-probabilities"] = document.getElementById("topology-sbm-probabilities");
  els["topology-lfr-n"] = document.getElementById("topology-lfr-n");
  els["topology-lfr-tau1"] = document.getElementById("topology-lfr-tau1");
  els["topology-lfr-tau2"] = document.getElementById("topology-lfr-tau2");
  els["topology-lfr-mu"] = document.getElementById("topology-lfr-mu");
  els["topology-lfr-average-degree"] = document.getElementById("topology-lfr-average-degree");
  els["topology-lfr-min-degree"] = document.getElementById("topology-lfr-min-degree");
  els["topology-lfr-max-degree"] = document.getElementById("topology-lfr-max-degree");
  els["topology-lfr-min-community"] = document.getElementById("topology-lfr-min-community");
  els["topology-lfr-max-community"] = document.getElementById("topology-lfr-max-community");
  els["topology-lfr-max-iters"] = document.getElementById("topology-lfr-max-iters");
  els["topology-path-n"] = document.getElementById("topology-path-n");
  els["simulation-steps"] = document.getElementById("simulation-steps");
  els["simulation-seed-count"] = document.getElementById("simulation-seed-count");
  els["simulation-random-seed"] = document.getElementById("simulation-random-seed");
  els["selected-seeds"] = document.getElementById("selected-seeds");
  els["configure-btn"] = document.getElementById("configure-btn");
  els["challenge-appeal"] = document.getElementById("challenge-appeal");
  els["challenge-severity"] = document.getElementById("challenge-severity");
  els["transition-awareness-lambda"] = document.getElementById("transition-awareness-lambda");
  els["transition-participation-intercept"] = document.getElementById("transition-participation-intercept");
  els["transition-participation-appeal"] = document.getElementById("transition-participation-appeal");
  els["transition-participation-susceptibility"] = document.getElementById("transition-participation-susceptibility");
  els["transition-participation-conformity"] = document.getElementById("transition-participation-conformity");
  els["transition-participation-risk"] = document.getElementById("transition-participation-risk");
  els["transition-amplification-intercept"] = document.getElementById("transition-amplification-intercept");
  els["transition-amplification-share"] = document.getElementById("transition-amplification-share");
  els["transition-amplification-exposure"] = document.getElementById("transition-amplification-exposure");
  els["transition-amplification-conformity"] = document.getElementById("transition-amplification-conformity");
  els["transition-counter-intercept"] = document.getElementById("transition-counter-intercept");
  els["transition-counter-risk"] = document.getElementById("transition-counter-risk");
  els["transition-counter-exposure"] = document.getElementById("transition-counter-exposure");
  els["transition-counter-effectiveness"] = document.getElementById("transition-counter-effectiveness");
  els["transition-dropout-intercept"] = document.getElementById("transition-dropout-intercept");
  els["transition-dropout-risk"] = document.getElementById("transition-dropout-risk");
  els["transition-dropout-exposure"] = document.getElementById("transition-dropout-exposure");
  els["transition-spontaneous-dropout"] = document.getElementById("transition-spontaneous-dropout");
  els["trait-susceptibility-kind"] = document.getElementById("trait-susceptibility-kind");
  els["trait-susceptibility-p1"] = document.getElementById("trait-susceptibility-p1");
  els["trait-susceptibility-p2"] = document.getElementById("trait-susceptibility-p2");
  els["trait-susceptibility-p3"] = document.getElementById("trait-susceptibility-p3");
  els["trait-susceptibility-clip"] = document.getElementById("trait-susceptibility-clip");
  els["trait-conformity-kind"] = document.getElementById("trait-conformity-kind");
  els["trait-conformity-p1"] = document.getElementById("trait-conformity-p1");
  els["trait-conformity-p2"] = document.getElementById("trait-conformity-p2");
  els["trait-conformity-p3"] = document.getElementById("trait-conformity-p3");
  els["trait-conformity-clip"] = document.getElementById("trait-conformity-clip");
  els["trait-risk-aversion-kind"] = document.getElementById("trait-risk-aversion-kind");
  els["trait-risk-aversion-p1"] = document.getElementById("trait-risk-aversion-p1");
  els["trait-risk-aversion-p2"] = document.getElementById("trait-risk-aversion-p2");
  els["trait-risk-aversion-p3"] = document.getElementById("trait-risk-aversion-p3");
  els["trait-risk-aversion-clip"] = document.getElementById("trait-risk-aversion-clip");
  els["trait-share-tendency-kind"] = document.getElementById("trait-share-tendency-kind");
  els["trait-share-tendency-p1"] = document.getElementById("trait-share-tendency-p1");
  els["trait-share-tendency-p2"] = document.getElementById("trait-share-tendency-p2");
  els["trait-share-tendency-p3"] = document.getElementById("trait-share-tendency-p3");
  els["trait-share-tendency-clip"] = document.getElementById("trait-share-tendency-clip");
  els["network-placeholder"] = document.getElementById("network-placeholder");
  els["network-stage"] = document.getElementById("network-stage");
  els["network-svg"] = document.getElementById("network-svg");
  els["plots-grid"] = document.getElementById("plots-grid");
  els["trend-canvas"] = document.getElementById("trend-canvas");
  els["density-canvas"] = document.getElementById("density-canvas");
  els["trajectory-canvas"] = document.getElementById("trajectory-canvas");
  els["summary-list"] = document.getElementById("summary-list");
  els["counts-list"] = document.getElementById("counts-list");
  els["time-slider"] = document.getElementById("time-slider");
  els["time-label"] = document.getElementById("time-label");
  els["time-note"] = document.getElementById("time-note");
  els["status-label"] = document.getElementById("status-label");
  els["play-btn"] = document.getElementById("play-btn");
  els["step-back-btn"] = document.getElementById("step-back-btn");
  els["step-forward-btn"] = document.getElementById("step-forward-btn");
  els["speed-range"] = document.getElementById("speed-range");

  const defaults = await fetch("/api/defaults").then((response) => response.json());
  els["topology-kind"].value = defaults.topology.kind;
  setLayoutValue(defaults.topology.layout);
  dashboard.modelConfiguration = null;

  const topologyDefaults = defaults.topology || {};
  setFieldValue("topology-ws-n", topologyDefaults.watts_strogatz?.n);
  setFieldValue("topology-ws-k", topologyDefaults.watts_strogatz?.k);
  setFieldValue("topology-ws-p", topologyDefaults.watts_strogatz?.p);
  setFieldValue("topology-er-n", topologyDefaults.erdos_renyi?.n);
  setFieldValue("topology-er-p", topologyDefaults.erdos_renyi?.p);
  setFieldValue("topology-ba-n", topologyDefaults.barabasi_albert?.n);
  setFieldValue("topology-ba-m", topologyDefaults.barabasi_albert?.m);
  setFieldValue("topology-nws-n", topologyDefaults.newman_watts_strogatz?.n);
  setFieldValue("topology-nws-k", topologyDefaults.newman_watts_strogatz?.k);
  setFieldValue("topology-nws-p", topologyDefaults.newman_watts_strogatz?.p);
  setFieldValue("topology-pc-n", topologyDefaults.powerlaw_cluster?.n);
  setFieldValue("topology-pc-m", topologyDefaults.powerlaw_cluster?.m);
  setFieldValue("topology-pc-p", topologyDefaults.powerlaw_cluster?.p);
  setFieldValue("topology-sbm-sizes", JSON.stringify(topologyDefaults.sbm?.sizes || [40, 40, 40]));
  setFieldValue(
    "topology-sbm-probabilities",
    JSON.stringify(
      topologyDefaults.sbm?.probabilities || [
        [0.14, 0.03, 0.02],
        [0.03, 0.13, 0.03],
        [0.02, 0.03, 0.12],
      ],
    ),
  );
  setFieldValue("topology-lfr-n", topologyDefaults.lfr?.n);
  setFieldValue("topology-lfr-tau1", topologyDefaults.lfr?.tau1);
  setFieldValue("topology-lfr-tau2", topologyDefaults.lfr?.tau2);
  setFieldValue("topology-lfr-mu", topologyDefaults.lfr?.mu);
  setFieldValue("topology-lfr-average-degree", topologyDefaults.lfr?.average_degree);
  setFieldValue("topology-lfr-min-degree", topologyDefaults.lfr?.min_degree);
  setFieldValue("topology-lfr-max-degree", topologyDefaults.lfr?.max_degree);
  setFieldValue("topology-lfr-min-community", topologyDefaults.lfr?.min_community);
  setFieldValue("topology-lfr-max-community", topologyDefaults.lfr?.max_community);
  setFieldValue("topology-lfr-max-iters", topologyDefaults.lfr?.max_iters);
  setFieldValue("topology-path-n", topologyDefaults.path?.n);
  els["simulation-steps"].value = defaults.simulation.steps;
  els["simulation-seed-count"].value = defaults.simulation.seed_count;
  els["simulation-random-seed"].value = defaults.simulation.random_seed;
  els["challenge-appeal"].value = defaults.challenge.appeal;
  els["challenge-severity"].value = defaults.challenge.severity;
  setTransitionDefaults(defaults.transition);
  setDistributionDefaults("trait-susceptibility", defaults.trait_distributions.susceptibility);
  setDistributionDefaults("trait-conformity", defaults.trait_distributions.conformity);
  setDistributionDefaults("trait-risk-aversion", defaults.trait_distributions.risk_aversion);
  setDistributionDefaults("trait-share-tendency", defaults.trait_distributions.share_tendency);

  bindEvents();
  updateTopologyFieldsVisibility();
  resetDashboard();

  document.querySelectorAll("#step-model input, #step-model select, #step-model textarea").forEach((element) => {
    element.addEventListener("input", invalidateModelConfiguration);
    element.addEventListener("change", invalidateModelConfiguration);
  });
}

window.addEventListener("DOMContentLoaded", () => {
  init().catch((error) => {
    console.error(error);
    setStatus(error.message);
  });
});
