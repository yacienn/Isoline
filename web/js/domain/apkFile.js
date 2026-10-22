// Domain: what counts as an acceptable upload. No DOM, no network.
export const MAX_APK_BYTES = 150 * 1024 * 1024;

/** Returns a user-facing problem description, or null when the file is acceptable. */
export function validateApkFile(file) {
  if (!file) return 'No file selected.';
  if (!/\.apk$/i.test(file.name)) return 'This is not an APK. Choose a file ending in .apk.';
  if (file.size > MAX_APK_BYTES) return 'File is larger than 150 MB. Choose a smaller APK.';
  return null;
}
