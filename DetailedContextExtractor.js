function isVisible(element) {
  const style = window.getComputedStyle(element);
  if (
    style.display === "none" ||
    style.visibility === "hidden" ||
    style.opacity === "0"
  )
    return false;
  const rect = element.getBoundingClientRect();
  return rect.width > 0 && rect.height > 0;
}

function getAttributes(element) {
  const attrs = {};
  [
    "id",
    "name",
    "class",
    "type",
    "placeholder",
    "value",
    "role",
    "aria-label",
    "aria-labelledby",
    "aria-describedby",
  ].forEach((attr) => {
    if (element.hasAttribute(attr)) {
      attrs[attr] = element.getAttribute(attr);
    }
  });
  // All data-* attributes
  Array.from(element.attributes).forEach((a) => {
    if (a.name.startsWith("data-")) attrs[a.name] = a.value;
  });
  return attrs;
}

function nodeToJson(el) {
  return {
    tag: el.tagName.toLowerCase(),
    attributes: getAttributes(el),
    text: el.innerText?.trim() || "",
    children: [],
  };
}

// Capture key elements: interactive, headings, main wrappers
const keySelectors = [
  "input:not([type=hidden]):not([disabled])",
  "button:not([disabled])",
  "textarea:not([disabled])",
  "select:not([disabled])",
  '[role="button"]',
  '[role="textbox"]',
  //   "h1,h2,h3,h4,h5,h6",
  //   "main,section,article",
  //   "[aria-label]",
];

// Create a Set to deduplicate
const selectorSet = new Set(
  keySelectors.flatMap((sel) => Array.from(document.querySelectorAll(sel)))
);

const filterAndBuildTree = (parent) => {
  return Array.from(parent.children)
    .filter(isVisible)
    .map((child) => {
      const json = nodeToJson(child);
      if (child.children.length > 0) {
        json.children = filterAndBuildTree(child);
      }
      return json;
    });
};

// Find the main content wrapper (can be customized)
const root = document.querySelector("main-content") || document.body; // TODO: change this to the main content wrapper

// Start with interactive/major nodes
const distilledNodes = Array.from(selectorSet)
  .filter(isVisible)
  .map(nodeToJson);

// Build a hierarchical tree for main content
const mainTree = [nodeToJson(root)];
mainTree[0].children = filterAndBuildTree(root);

// Optionally include global/static app state if available
let appState = {};
if (window.APP_STATE) appState = window.APP_STATE;

// Final batch for the agent
const contextPayload = {
  distilledNodes, // Flat list of high-value elements
  mainTree, // Hierarchical subtree of visible major content
  appState, // Custom app-level state (if available)
};

console.log(JSON.stringify(contextPayload, null, 2));
