import ast
from pathlib import Path

import pytest

SOURCE_ROOT = Path(__file__).resolve().parents[3] / "src"
PACKAGE = "app"
PORTS = "usecase.interface"
MAX_LINES = 250


def module_name(root: Path, path: Path) -> str:
    parts = path.relative_to(root).with_suffix("").parts
    return ".".join(parts[:-1] if parts[-1] == "__init__" else parts)


def is_protocol(node: ast.ClassDef) -> bool:
    return any(
        (isinstance(base, ast.Name) and base.id == "Protocol")
        or (isinstance(base, ast.Attribute) and base.attr == "Protocol")
        for base in node.bases
    )


def misplaced_ports(root: Path, package: str) -> list[str]:
    allowed = f"{package}.{PORTS}"
    violations = []
    for path in sorted((root / package).rglob("*.py")):
        module = module_name(root, path)
        if module == allowed or module.startswith(allowed + "."):
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ClassDef) and is_protocol(node):
                violations.append(f"{module}:{node.lineno} defines port {node.name}")
    return violations


def oversized_modules(root: Path, package: str) -> list[str]:
    return [
        f"{module_name(root, path)} has {count} lines"
        for path in sorted((root / package).rglob("*.py"))
        if (count := len(path.read_text(encoding="utf-8").splitlines())) > MAX_LINES
    ]


def test_ports_live_in_usecase_interface() -> None:
    assert misplaced_ports(SOURCE_ROOT, PACKAGE) == []


def test_modules_stay_within_line_limit() -> None:
    assert oversized_modules(SOURCE_ROOT, PACKAGE) == []


@pytest.mark.parametrize(
    ("path", "source", "expected"),
    [
        (
            "pkg/usecase/orders.py",
            "from typing import Protocol\n\n\nclass Orders(Protocol): ...\n",
            ["pkg.usecase.orders:4 defines port Orders"],
        ),
        (
            "pkg/adapter/client.py",
            "import typing\n\n\nclass Client(typing.Protocol): ...\n",
            ["pkg.adapter.client:4 defines port Client"],
        ),
        ("pkg/usecase/interface/orders.py", "class Orders(Protocol): ...\n", []),
    ],
)
def test_port_placement_is_reported(
    tmp_path: Path, path: str, source: str, expected: list[str]
) -> None:
    target = tmp_path / path
    target.parent.mkdir(parents=True)
    target.write_text(source, encoding="utf-8")

    assert misplaced_ports(tmp_path, "pkg") == expected


def test_oversized_module_is_reported(tmp_path: Path) -> None:
    target = tmp_path / "pkg" / "domain" / "rules.py"
    target.parent.mkdir(parents=True)
    target.write_text("x = 1\n" * (MAX_LINES + 1), encoding="utf-8")

    assert oversized_modules(tmp_path, "pkg") == [f"pkg.domain.rules has {MAX_LINES + 1} lines"]
