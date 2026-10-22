// Infrastructure: talks to the Isoline server (POST /api/scan, raw APK bytes).
import { ScanError } from '../application/errors.js';

const toReport = (data) => ({
  score: data.score,                         // 0-100
  verdict: data.verdict,                     // 'benign' | 'uncertain' | 'malicious'
  sha256: data.sha256,
  permissionCount: data.permission_count,
  permissions: data.permissions,             // [{ name, risk }]
  indicators: data.indicators,               // [{ title, detail, severity }]
});

export function createScanApiGateway({ fetchImpl = (...args) => fetch(...args), endpoint = '/api/scan' } = {}) {
  return {
    async scan(file, { signal } = {}) {
      let response;
      try {
        response = await fetchImpl(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/octet-stream' },
          body: file,
          signal,
        });
      } catch (error) {
        if (error?.name === 'AbortError') throw error;
        throw new ScanError('Could not reach the scanner. Is the Isoline server running?');
      }
      let data = {};
      try { data = await response.json(); } catch { /* non-JSON error body */ }
      if (!response.ok) throw new ScanError(data.detail || `Scan failed (${response.status})`);
      return toReport(data);
    },
  };
}
