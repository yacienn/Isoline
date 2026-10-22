import { validateApkFile } from '../domain/apkFile.js';
import { ValidationError } from './errors.js';

export function createAnalyzeApk({ scanner }) {
  return async function analyzeApk(file, { onStep = () => {}, signal } = {}) {
    const problem = validateApkFile(file);
    if (problem) throw new ValidationError(problem);
    onStep('checked');
    onStep('scanning');
    const report = await scanner.scan(file, { signal });
    onStep('done');
    return { file: { name: file.name, size: file.size }, report, analyzedAt: new Date() };
  };
}
