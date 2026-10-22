// UI: renders a result record into the right-hand panel.
import { describeVerdict } from '../domain/verdict.js';
import { RISK_FILTERS, filterByRisk, riskTone, sortByRisk } from '../domain/risk.js';
import { $, esc, formatBytes, prefersReducedMotion } from './dom.js';

const RING_RADIUS = 52;
const CIRCUMFERENCE = 2 * Math.PI * RING_RADIUS;

export function createResultView(container) {
  const permissionRows = (permissions) =>
    permissions.map((p, n) =>
      `<tr class="rise" style="animation-delay:${n * 0.04}s"><td class="mono">${esc(p.name)}</td>` +
      `<td><span class="tag ${riskTone(p.risk)}">${esc(p.risk)}</span></td></tr>`).join('') ||
    '<tr><td colspan="2" class="empty" style="padding:16px">None at this level.</td></tr>';

  const findingsHtml = (indicators) => indicators.length
    ? '<ul class="ind">' + indicators.map((i, n) =>
        `<li class="${i.severity === 'high' ? 'h' : ''} rise" style="animation-delay:${0.35 + n * 0.12}s">` +
        `<div><strong>${esc(i.title)}</strong><small>${esc(i.detail)}</small></div></li>`).join('') + '</ul>'
    : '<p class="ok" style="margin:0">No suspicious behaviours found.</p>';

  function animateScore(score) {
    const arc = $('#arc', container), num = $('#num', container);
    requestAnimationFrame(() => requestAnimationFrame(() => {
      arc.style.strokeDashoffset = CIRCUMFERENCE * (1 - score / 100);
    }));
    if (prefersReducedMotion()) { num.textContent = score; return; }
    const t0 = performance.now();
    const tick = (t) => {
      const p = Math.min(1, (t - t0) / 1200);
      num.textContent = Math.round(score * (1 - Math.pow(1 - p, 3)));
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }

  function bindPermissionFilters(permissions) {
    const body = $('#ptb', container);
    const chips = [...container.querySelectorAll('.chip')];
    const sorted = sortByRisk(permissions);
    const draw = (filter) => { body.innerHTML = permissionRows(filterByRisk(sorted, filter)); };
    draw('all');
    chips.forEach((chip) => chip.addEventListener('click', () => {
      chips.forEach((c) => c.setAttribute('aria-pressed', String(c === chip)));
      draw(chip.dataset.f);
    }));
  }

  return {
    renderEmpty() {
      container.innerHTML = '<div class="empty">Results appear here after you upload an APK.</div>';
    },

    render({ file, report }) {
      const v = describeVerdict(report.verdict);
      const { score, permissions, indicators } = report;
      container.innerHTML = `
   <div class="verdict">
    <svg class="ring" viewBox="0 0 128 128" role="img" aria-label="Risk score ${score} out of 100">
     <circle cx="64" cy="64" r="${RING_RADIUS}" fill="none" stroke="var(--line)" stroke-width="12"/>
     <circle cx="64" cy="64" r="${RING_RADIUS}" fill="none" stroke="var(--${v.tone})" stroke-width="12" stroke-linecap="round" stroke-dasharray="${CIRCUMFERENCE}" id="arc" stroke-dashoffset="${CIRCUMFERENCE}" style="transition:stroke-dashoffset 1.2s cubic-bezier(.2,.8,.2,1)" transform="rotate(-90 64 64)"/>
     <text id="num" x="64" y="68" text-anchor="middle" font-size="32" font-weight="600">0</text>
     <text x="64" y="88" text-anchor="middle" font-size="11" style="fill:var(--mute)">risk / 100</text>
    </svg>
    <div class="vtext"><p class="mono" style="margin:0 0 2px;word-break:break-all">${esc(file.name)} · ${formatBytes(file.size)}</p><h3 class="${v.tone}">${v.title}</h3><p>${v.description}</p></div>
   </div>
   <h2 style="margin-top:22px">Findings</h2>
   ${findingsHtml(indicators)}
   <h2 style="margin-top:22px">Permissions (${permissions.length})</h2>
   <div class="filters" role="group" aria-label="Filter permissions">
    ${RISK_FILTERS.map((f, i) => `<button class="chip" data-f="${f}" aria-pressed="${i === 0}">${f[0].toUpperCase() + f.slice(1)}</button>`).join('')}
   </div>
   <div class="scroll"><table><thead><tr><th>Permission</th><th>Risk</th></tr></thead><tbody id="ptb"></tbody></table></div>
   <p class="note">The score comes from a machine-learning model that only looks at declared permissions. Risk labels are rules of thumb. Treat this as a signal, not a guarantee.</p>`;
      container.classList.remove('rise');
      void container.offsetWidth;          // restart the CSS animation
      container.classList.add('rise');
      animateScore(score);
      bindPermissionFilters(permissions);
    },
  };
}
