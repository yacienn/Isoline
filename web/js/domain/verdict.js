// Domain: how each verdict from the scanner is explained to the person.
// The verdict itself is decided by the server; the browser never re-derives it from the score.
const VERDICTS = Object.freeze({
  malicious: {
    tone: 'bad',
    title: 'Likely malicious',
    description: 'The model found a permission pattern that matches malware in its training data. Do not install this app unless you trust its source.',
  },
  uncertain: {
    tone: 'warn',
    title: 'Uncertain',
    description: 'The model could not decide. This is not a safe verdict. Check the findings and where the app came from.',
  },
  benign: {
    tone: 'ok',
    title: 'Looks benign',
    description: 'The permission pattern resembles normal apps in the training data. This does not guarantee the app is safe.',
  },
});

/** Unknown verdicts fall back to "uncertain" - never to "benign". */
export const describeVerdict = (verdict) => VERDICTS[verdict] ?? VERDICTS.uncertain;
