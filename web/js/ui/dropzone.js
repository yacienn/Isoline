// UI: drag-and-drop + file picker. Reports the chosen file through onFile.
export function bindDropzone({ drop, input, onFile }) {
  drop.addEventListener('click', () => input.click());
  drop.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); input.click(); }
  });
  ['dragenter', 'dragover'].forEach((type) =>
    drop.addEventListener(type, (e) => { e.preventDefault(); drop.classList.add('over'); }));
  ['dragleave', 'drop'].forEach((type) =>
    drop.addEventListener(type, (e) => { e.preventDefault(); drop.classList.remove('over'); }));
  drop.addEventListener('drop', (e) => onFile(e.dataTransfer.files[0]));
  input.addEventListener('change', () => onFile(input.files[0]));
  return { reset: () => { input.value = ''; } };
}
