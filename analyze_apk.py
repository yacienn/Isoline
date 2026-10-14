
from pathlib import Path
from androguard.misc import AnalyzeAPK

apk_path = Path(r"D:\Projects\AMD\sample.apk")

if not apk_path.is_file():
    raise FileNotFoundError(f"APK not found: {apk_path}")

print(f"Analyzing: {apk_path.name}")

# Parse the APK and its DEX bytecode.
apk, dex_files, analysis = AnalyzeAPK(str(apk_path))

# Extract permissions declared in the manifest.
permissions = apk.get_permissions()

print("\nDeclared permissions:")

for permission in sorted(permissions):
    print(f"- {permission}")

print(f"\nTotal permissions: {len(permissions)}")