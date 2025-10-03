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

function getRelevantAttributes(element) {
  const relevant = {};
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
    "data-*",
  ].forEach((attr) => {
    if (attr === "data-*") {
      // Extract all data- attributes
      Array.from(element.attributes).forEach((a) => {
        if (a.name.startsWith("data-")) relevant[a.name] = a.value;
      });
    } else if (element.hasAttribute(attr)) {
      relevant[attr] = element.getAttribute(attr);
    }
  });
  return relevant;
}

// Selectors for "high-value" elements (extend as needed)
const selectors = [
  "input:not([type=hidden]):not([disabled])",
  "button:not([disabled])",
  "textarea:not([disabled])",
  "select:not([disabled])",
  '[role="button"]',
  '[role="textbox"]',
];

const nodes = [];
selectors.forEach((sel) => {
  document.querySelectorAll(sel).forEach((el) => {
    if (isVisible(el)) nodes.push(el);
  });
});

// Build a compact JSON representation
const compactJson = nodes.map((el) => ({
  tag: el.tagName.toLowerCase(),
  attributes: getRelevantAttributes(el),
  value: el.value || el.innerText || "",
  parent: el.parentElement ? el.parentElement.tagName.toLowerCase() : null,
}));

// Optional: Batch into parent/child trees for major sections
const batched = { elements: compactJson };

// Output
console.log(JSON.stringify(batched, null, 2));
