"""Compatibility shim for pattern exit simulation contracts.

Task 083 moved generic exit simulation to ``quant_bitcoin.risk.exit_simulation``.
This module re-exports those names to preserve legacy imports.
"""

from quant_bitcoin.risk.exit_simulation import *  # noqa: F403
