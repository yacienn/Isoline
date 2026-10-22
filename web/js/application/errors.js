// Application: errors the UI can show verbatim.
export class ScanError extends Error {
  constructor(message) { super(message); this.name = 'ScanError'; }
}
export class ValidationError extends ScanError {
  constructor(message) { super(message); this.name = 'ValidationError'; }
}
