"""Guards the dependency rule: imports may only point inwards."""
import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "isoline" / "webapp"
FORBIDDEN = {
    "domain": {"application", "infrastructure", "interface", "container", "config"},
    "application": {"infrastructure", "interface", "container", "config"},
    "infrastructure": {"interface", "container", "config"},
    "interface": {"infrastructure", "container", "config"},
}
FRAMEWORKS = {"http", "subprocess", "socket", "urllib", "tempfile", "joblib", "sklearn", "androguard"}


def imported_modules(path: Path, package_parts: list[str]):
    """Yield (absolute dotted module) for every import in a file under isoline/webapp."""
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            for a in node.names:
                yield a.name
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = ["isoline", "webapp"] + package_parts[: len(package_parts) - (node.level - 1)]
                yield ".".join(base + ([node.module] if node.module else []))
            elif node.module:
                yield node.module


class DependencyRuleTests(unittest.TestCase):
    def test_layers_only_depend_inwards(self):
        problems = []
        for layer, banned in FORBIDDEN.items():
            for file in (ROOT / layer).glob("*.py"):
                for module in imported_modules(file, [layer]):
                    parts = module.split(".")
                    if parts[:2] == ["isoline", "webapp"] and len(parts) > 2 and parts[2] in banned:
                        problems.append(f"{file.relative_to(ROOT)} imports {module}")
        self.assertEqual(problems, [])

    def test_domain_and_application_are_framework_free(self):
        problems = []
        for layer in ("domain", "application"):
            for file in (ROOT / layer).glob("*.py"):
                for module in imported_modules(file, [layer]):
                    if module.split(".")[0] in FRAMEWORKS:
                        problems.append(f"{file.relative_to(ROOT)} imports {module}")
        self.assertEqual(problems, [])


if __name__ == "__main__":
    unittest.main()
