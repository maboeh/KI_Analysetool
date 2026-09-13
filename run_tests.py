import argparse
import os
from pathlib import Path
import subprocess
import sys


GUI_TESTS = {
    "test_action_buttons.py",
    "test_enhanced_gui_integration.py",
    "test_excel_export_ui.py",
    "test_extended_input_tabs.py",
    "test_final_gui_integration.py",
    "test_help_tooltip.py",
    "test_progress_indicator.py",
    "test_results_browser.py",
    "test_results_display.py",
    "test_visualization_panel.py",
}

INTEGRATION_TESTS = {
    "test_basic_integration.py",
    "test_integration_data_models.py",
    "test_integration_workflows.py",
    "test_integration_workflows_simple.py",
}


def discover_tests(root: Path) -> list[Path]:
    root_tests = set(root.glob("test_*.py"))
    package_tests = set((root / "tests").glob("test_*.py"))
    return sorted(root_tests | package_tests, key=lambda path: str(path.relative_to(root)))


def select_tests(tests: list[Path], root: Path, group: str) -> list[Path]:
    if group == "all":
        return tests
    if group == "gui":
        return [path for path in tests if path.name in GUI_TESTS]
    if group == "integration":
        return [path for path in tests if path.name in INTEGRATION_TESTS]
    return [
        path for path in tests
        if path.name not in GUI_TESTS and path.name not in INTEGRATION_TESTS
    ]


def run_test(path: Path, root: Path, timeout: int) -> bool:
    relative_path = path.relative_to(root)
    print(f"\n=== {relative_path} ===", flush=True)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root)
    try:
        result = subprocess.run(
            [sys.executable, str(path)],
            cwd=root,
            env=env,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        print(f"TIMEOUT nach {timeout} Sekunden: {relative_path}", file=sys.stderr)
        return False
    return result.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--group", choices=("unit", "gui", "integration", "all"), default="unit")
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    tests = select_tests(discover_tests(root), root, args.group)
    failed = [path for path in tests if not run_test(path, root, args.timeout)]

    print(f"\n{len(tests) - len(failed)}/{len(tests)} Testdateien erfolgreich.")
    if failed:
        print("Fehlgeschlagen:", file=sys.stderr)
        for path in failed:
            print(f"- {path.relative_to(root)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
