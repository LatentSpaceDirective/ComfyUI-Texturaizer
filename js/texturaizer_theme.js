import { app } from "../../scripts/app.js";

const GET_BG = "rgb(20, 88, 118)";
const MAIN_BG = "rgb(0, 63, 101)";
const TITLE_TEXT = "#ffffff";

function applyColors(node, bg) {
  node.color = bg;
  node.bgcolor = bg;
  node.boxcolor = bg;       // title bar
  node.title_color = TITLE_TEXT;

  node.setDirtyCanvas(true, true);
}

app.registerExtension({
  name: "texturaizer.theme.nodes",

  beforeRegisterNodeDef(nodeType, nodeData) {
    if (!nodeData?.name?.startsWith("Texturaizer_")) return;

    const bg = nodeData.name.startsWith("Texturaizer_Get")
      ? GET_BG
      : MAIN_BG;

    const onCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      const r = onCreated?.apply(this, arguments);
      setTimeout(() => applyColors(this, bg), 0);
      return r;
    };

    const configure = nodeType.prototype.configure;
    nodeType.prototype.configure = function () {
      const r = configure?.apply(this, arguments);
      setTimeout(() => applyColors(this, bg), 0);
      return r;
    };
  },
});
