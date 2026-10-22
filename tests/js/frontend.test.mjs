// Run with:  node --test tests/js
import test from 'node:test';
import assert from 'node:assert/strict';

import { validateApkFile, MAX_APK_BYTES } from '../../web/js/domain/apkFile.js';
import { describeVerdict } from '../../web/js/domain/verdict.js';
import { filterByRisk, sortByRisk, riskTone } from '../../web/js/domain/risk.js';
import { createAnalyzeApk } from '../../web/js/application/analyzeApk.js';
import { ScanError, ValidationError } from '../../web/js/application/errors.js';
import { createScanApiGateway } from '../../web/js/infrastructure/scanApiGateway.js';

const apk = (name = 'a.apk', size = 10) => ({ name, size });
const json = (status, body) => ({ ok: status < 400, status, json: async () => body });

test('validateApkFile', () => {
  assert.equal(validateApkFile(apk()), null);
  assert.equal(validateApkFile(apk('A.APK')), null);
  assert.match(validateApkFile(apk('notes.txt')), /not an APK/);
  assert.match(validateApkFile(apk('big.apk', MAX_APK_BYTES + 1)), /150 MB/);
  assert.ok(validateApkFile(undefined));
});

test('unknown verdict falls back to uncertain, never benign', () => {
  assert.equal(describeVerdict('???').title, 'Uncertain');
  assert.equal(describeVerdict('benign').tone, 'ok');
  assert.equal(describeVerdict('malicious').tone, 'bad');
});

test('risk helpers', () => {
  const perms = [{ name: 'l', risk: 'low' }, { name: 'h', risk: 'high' }, { name: 'm', risk: 'medium' }];
  assert.deepEqual(sortByRisk(perms).map((p) => p.name), ['h', 'm', 'l']);
  assert.deepEqual(filterByRisk(perms, 'high').map((p) => p.name), ['h']);
  assert.equal(filterByRisk(perms, 'all').length, 3);
  assert.equal(riskTone('high'), 'bad');
});

test('analyzeApk validates before calling the scanner', async () => {
  let called = false;
  const analyze = createAnalyzeApk({ scanner: { scan: async () => { called = true; } } });
  await assert.rejects(analyze(apk('x.txt')), ValidationError);
  assert.equal(called, false);
});

test('analyzeApk reports steps and returns a record', async () => {
  const report = { verdict: 'benign', score: 5, permissions: [], indicators: [] };
  const steps = [];
  const analyze = createAnalyzeApk({ scanner: { scan: async () => report } });
  const result = await analyze(apk('ok.apk', 42), { onStep: (s) => steps.push(s) });
  assert.deepEqual(steps, ['checked', 'scanning', 'done']);
  assert.equal(result.report, report);
  assert.deepEqual(result.file, { name: 'ok.apk', size: 42 });
});

test('gateway maps the API payload and posts raw bytes', async () => {
  let seen;
  const gateway = createScanApiGateway({
    fetchImpl: async (url, init) => {
      seen = { url, init };
      return json(200, { score: 91, verdict: 'malicious', sha256: 'ab', permission_count: 1,
                         permissions: [{ name: 'p', risk: 'high' }], indicators: [] });
    },
  });
  const file = apk();
  const report = await gateway.scan(file);
  assert.equal(seen.url, '/api/scan');
  assert.equal(seen.init.method, 'POST');
  assert.equal(seen.init.body, file);
  assert.equal(seen.init.headers['Content-Type'], 'application/octet-stream');
  assert.equal(report.permissionCount, 1);
  assert.equal(report.verdict, 'malicious');
});

test('gateway error handling', async () => {
  const withFetch = (fetchImpl) => createScanApiGateway({ fetchImpl });
  await assert.rejects(withFetch(async () => json(422, { detail: 'Not a valid APK: x' })).scan(apk()),
    (e) => e instanceof ScanError && e.message === 'Not a valid APK: x');
  await assert.rejects(withFetch(async () => ({ ok: false, status: 502, json: async () => { throw new Error('html'); } })).scan(apk()),
    /Scan failed \(502\)/);
  await assert.rejects(withFetch(async () => { throw new TypeError('network'); }).scan(apk()),
    /Could not reach the scanner/);
  const abort = Object.assign(new Error('aborted'), { name: 'AbortError' });
  await assert.rejects(withFetch(async () => { throw abort; }).scan(apk()), (e) => e.name === 'AbortError');
});
