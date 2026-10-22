
from pathlib import Path

from androguard.misc import AnalyzeAPK

def extract_features(apk_path: str | Path) -> dict:
    """Extract basic static features from an Android APK."""

    apk_path = Path(apk_path).resolve()

    if not apk_path.is_file():
        raise FileNotFoundError(f"APK not found: {apk_path}")

    # Parse the APK, its DEX files, and analysis information.
    apk, dex_files, analysis = AnalyzeAPK(str(apk_path))

    # Extract manifest information.
    permissions = sorted(set(apk.get_permissions()))

    # Collect unique method identifiers from the DEX method tables.
    method_references = set()

    for dex in dex_files:
     for method in dex.get_methods():
        method_references.add(
            (
                method.get_class_name(),
                method.get_name(),
                method.get_descriptor(),
            )
        )

    # Convert tuples into JSON-compatible dictionaries.
    methods = [
        {
            "class": class_name,
            "name": method_name,
            "descriptor": descriptor,
        }
        for class_name, method_name, descriptor
        in sorted(method_references)
    ]

    return {
     "file_name": apk_path.name,
     "package_name": apk.get_package(),
     "dex_file_count": len(dex_files),
     "permissions": permissions,
     "permission_count": len(permissions),
     "method_identifier_count": len(method_references),
    }