from __future__ import annotations

import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AUDITED_SOURCE_ROOTS = (
    PROJECT_ROOT / "quant_bitcoin" / "strategies",
    PROJECT_ROOT / "quant_bitcoin" / "backtesting",
)

BANNED_EXECUTION_IMPORT_PREFIXES = (
    "quant_bitcoin.execution",
)
BANNED_LIVE_ENDPOINT_STRINGS = frozenset(
    {
        "/api/v3/order",
        "https://api.binance.com",
        "https://testnet.binance.vision",
        "BINANCE_TESTNET_API_KEY",
        "BINANCE_TESTNET_API_SECRET",
        "ENABLE_LIVE_TRADING",
    }
)
BANNED_EXECUTION_SYMBOLS = frozenset(
    {
        "BinanceSpotTestnetExecutionClient",
        "BinanceTestnetExecutionError",
        "sign_query_string",
        "_signed_request",
        "_validate_allowed_path",
        "urlopen",
    }
)


def _python_files() -> list[Path]:
    files: list[Path] = []
    for root in AUDITED_SOURCE_ROOTS:
        files.extend(sorted(path for path in root.rglob("*.py") if path.is_file()))
    return files


def _module_tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def test_strategy_and_backtesting_modules_do_not_import_execution_clients() -> None:
    violations: list[str] = []

    for path in _python_files():
        tree = _module_tree(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith(BANNED_EXECUTION_IMPORT_PREFIXES):
                        violations.append(f"{path.relative_to(PROJECT_ROOT)} imports {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module.startswith(BANNED_EXECUTION_IMPORT_PREFIXES):
                    violations.append(f"{path.relative_to(PROJECT_ROOT)} imports from {module}")

    assert not violations, "\n".join(violations)


def test_pattern_research_modules_do_not_embed_signed_order_endpoints_or_credentials() -> None:
    violations: list[str] = []

    for path in _python_files():
        tree = _module_tree(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if node.value in BANNED_LIVE_ENDPOINT_STRINGS:
                    violations.append(f"{path.relative_to(PROJECT_ROOT)} embeds {node.value!r}")
            elif isinstance(node, ast.Name) and node.id in BANNED_EXECUTION_SYMBOLS:
                violations.append(f"{path.relative_to(PROJECT_ROOT)} references {node.id}")
            elif isinstance(node, ast.Attribute) and node.attr in BANNED_EXECUTION_SYMBOLS:
                violations.append(f"{path.relative_to(PROJECT_ROOT)} references .{node.attr}")

    assert not violations, "\n".join(violations)
