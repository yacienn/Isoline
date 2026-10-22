// Domain: permission risk labels (rule-of-thumb labels from the server, not model output).
export const RISK_FILTERS = Object.freeze(['all', 'high', 'medium', 'low']);

const ORDER = { high: 0, medium: 1, low: 2 };
const TONE = { high: 'bad', medium: 'warn', low: 'ok' };

export const riskTone = (risk) => TONE[risk] ?? 'ok';
export const sortByRisk = (permissions) =>
  [...permissions].sort((a, b) => (ORDER[a.risk] ?? 3) - (ORDER[b.risk] ?? 3));
export const filterByRisk = (permissions, filter) =>
  filter === 'all' ? permissions : permissions.filter((p) => p.risk === filter);
