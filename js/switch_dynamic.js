import { app } from "../../scripts/app.js";

const MAX = 10;
const TARGETS = new Set([
  "Texturaizer_SwitchSmart",
  "Texturaizer_SwitchLazy",
]);

function getInput(node, name) {
  return node.inputs?.find(i => i?.name === name);
}

function getDataInputs(node) {
  return node.inputs?.filter(i => typeof i?.name === "string" && /^input\d+$/.test(i.name)) ?? [];
}

function visibleInputCount(node) {
  const inputs = getDataInputs(node);
  let lastLinked = 0;
  for (let i = 0; i < inputs.length; i++) {
    if (inputs[i].link != null) lastLinked = i + 1;
  }
  // Always show at least input1; if inputN is linked, show next one too (up to MAX)
  return Math.min(MAX, Math.max(1, lastLinked + 1));
}

function ensureInputs(node, count) {
  if (!getInput(node, "input1")) node.addInput("input1", "*");

  for (let i = 2; i <= count; i++) {
    if (!getInput(node, `input${i}`)) node.addInput(`input${i}`, "*");
  }

  // remove from the end only if unlinked
  for (let i = MAX; i > count; i--) {
    const inp = getInput(node, `input${i}`);
    if (inp && inp.link == null) {
      node.removeInput(node.inputs.indexOf(inp));
    }
  }
}

/* -------------------- Trigger widgets (SwitchSmart only) -------------------- */

function takeTriggerValues(node) {
  const map = {};
  for (const w of node.widgets || []) {
    if (typeof w?.name === "string" && /^trigger\d+$/.test(w.name)) {
      map[w.name] = w.value ?? "";
    }
  }
  return map;
}

function removeAllTriggerWidgets(node) {
  if (!node.widgets) return;
  node.widgets = node.widgets.filter(w => !(typeof w?.name === "string" && /^trigger\d+$/.test(w.name)));
  if (node.widgets_values) delete node.widgets_values;
}

function addTriggerWidgets(node, count, prevValues) {
  for (let i = 1; i <= count; i++) {
    const name = `trigger${i}`;
    const value = prevValues?.[name] ?? "";

    const w = node.addWidget(
      "text",
      name,
      value,
      (v) => { w.value = v; },
      { multiline: false }
    );

    // Ensure stable identity for serialization + editing
    w.name = name;
    w.value = value;
  }
}

function refreshTriggersIfSmart(node, count) {
  if (node.comfyClass !== "Texturaizer_SwitchSmart") return;
  const prev = takeTriggerValues(node);
  removeAllTriggerWidgets(node);
  addTriggerWidgets(node, count, prev);
}

/* -------------------- Auto shrink (only reduces height) -------------------- */

function autoShrink(node) {
  const min = node.computeSize?.();
  if (!Array.isArray(min) || min.length !== 2) return;

  const minH = min[1];
  if (typeof minH === "number" && node.size?.[1] > minH) {
    node.size[1] = minH;
  }
}

/* -------------------- refresh -------------------- */

function refresh(node) {
  const count = visibleInputCount(node);
  ensureInputs(node, count);
  refreshTriggersIfSmart(node, count);
  autoShrink(node);
  node.setDirtyCanvas(true, true);
}

app.registerExtension({
  name: "texturaizer.switchSmart.dynamic",

  beforeRegisterNodeDef(nodeType, nodeData) {
    if (!TARGETS.has(nodeData.name)) return;

    const onCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      const r = onCreated?.apply(this, arguments);
      setTimeout(() => refresh(this), 0);
      return r;
    };

    const onConnectionsChange = nodeType.prototype.onConnectionsChange;
    nodeType.prototype.onConnectionsChange = function () {
      const r = onConnectionsChange?.apply(this, arguments);
      refresh(this);
      return r;
    };

    const configure = nodeType.prototype.configure;
    nodeType.prototype.configure = function () {
      const r = configure?.apply(this, arguments);
      setTimeout(() => refresh(this), 0);
      return r;
    };
  }
});
