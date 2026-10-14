
import json
from pathlib import Path

from feature_extractor import extract_features

PROJECT_DIR = Path(__file__).resolve().parent
APK_PATH = PROJECT_DIR / "crackMe.apk"
OUTPUT_PATH = PROJECT_DIR / "features.json"

def main() -> None:
    features = extract_features(APK_PATH)

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(features, file, indent=2, ensure_ascii=False)

    print(f"Analysis completed: {features['file_name']}")
    print(f"Package: {features['package_name']}")
    print(f"Permissions: {features['permission_count']}")
    print(f"DEX files: {features['dex_file_count']}")
    print(
        "Method identifiers: "
        f"{features['method_identifier_count']}"
    )
    print(f"Report saved to: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()