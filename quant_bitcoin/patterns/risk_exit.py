"""Compatibility shim for risk/exit plan contracts.

Task 083 moved generic risk/exit contracts to ``quant_bitcoin.risk.exit_plan``.
This module re-exports those names to preserve legacy imports.
"""

from quant_bitcoin.risk.exit_plan import *  # noqa: F403
