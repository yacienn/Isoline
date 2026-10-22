export const $ = (selector, root = document) => root.querySelector(selector);

const ENTITIES = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
/** Escape anything that came from the server or the file name before putting it in HTML. */
export const esc = (value) => String(value).replace(/[&<>"']/g, (c) => ENTITIES[c]);

export const prefersReducedMotion = () => matchMedia('(prefers-reduced-motion:reduce)').matches;
export const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

export const formatBytes = (bytes) =>
  bytes > 1048576 ? (bytes / 1048576).toFixed(1) + ' MB' : Math.max(1, Math.round(bytes / 1024)) + ' KB';
