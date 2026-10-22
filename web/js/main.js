// Composition root of the front end: builds the objects and connects them. No business logic here.
import { createAnalyzeApk } from './application/analyzeApk.js';
import { createScanApiGateway } from './infrastructure/scanApiGateway.js';
import { $, prefersReducedMotion, sleep } from './ui/dom.js';
import { bindDropzone } from './ui/dropzone.js';
import { createProgressView } from './ui/progressView.js';
import { createResultView } from './ui/resultView.js';
import { startTopographicBackground } from './ui/background.js';

const analyzeApk = createAnalyzeApk({ scanner: createScanApiGateway() });

const drop = $('#drop');
const errorBox = $('#err');
const results = createResultView($('#result'));
const progress = createProgressView({
  run: $('#run'), drop, name: $('#fn'), size: $('#fs'), bar: $('#bar'),
  list: $('#steps'), cancelButton: $('#cancel'),
});
const zone = bindDropzone({ drop, input: $('#file'), onFile: handleFile });

let current = null; // AbortController of the scan in flight

const showError = (message) => { errorBox.textContent = message; errorBox.classList.remove('hidden'); };
const clearError = () => errorBox.classList.add('hidden');

async function handleFile(file) {
  clearError();
  if (!file) return;
  current?.abort();
  const controller = new AbortController();
  current = controller;
  progress.start(file);
  try {
    const result = await analyzeApk(file, { onStep: progress.setStep, signal: controller.signal });
    if (controller !== current) return;
    progress.complete();
    results.render(result);
    if (!prefersReducedMotion()) $('#result').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    await sleep(500);
    if (controller === current) progress.hide();
  } catch (error) {
    if (error.name === 'AbortError' || controller !== current) return;
    progress.hide();
    showError(error.message || 'Analysis failed. Try again.');
  } finally {
    if (controller === current) zone.reset();
  }
}

progress.onCancel(() => { current?.abort(); current = null; progress.hide(); zone.reset(); });

results.renderEmpty();
startTopographicBackground($('#bg'));
