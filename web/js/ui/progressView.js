// UI: the "analysing..." panel under the drop zone.
import { formatBytes } from './dom.js';

const STEPS = [
  { id: 'checked', label: 'Checking file' },
  { id: 'scanning', label: 'Reading permissions and running the detection model' },
];

export function createProgressView({ run, drop, name, size, bar, list, cancelButton }) {
  const items = () => [...list.children];
  const percent = (i) => (i / STEPS.length) * 100 + 8;

  function setStep(stepId) {
    const index = STEPS.findIndex((s) => s.id === stepId);
    if (index < 0) return;
    items().forEach((li, i) => { li.className = i < index ? 'done' : i === index ? 'act' : ''; });
    bar.style.width = percent(index) + '%';
  }

  return {
    start(file) {
      name.textContent = file.name;
      size.textContent = formatBytes(file.size);
      list.innerHTML = STEPS.map((s) => `<li><span class="dot"></span>${s.label}</li>`).join('');
      run.classList.remove('hidden');
      drop.classList.add('busy');
    },
    setStep,
    complete() {
      items().forEach((li) => { li.className = 'done'; });
      bar.style.width = '100%';
    },
    hide() {
      run.classList.add('hidden');
      drop.classList.remove('busy');
      bar.style.width = '0';
    },
    onCancel(handler) { cancelButton.addEventListener('click', handler); },
  };
}
