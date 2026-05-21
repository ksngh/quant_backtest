"""Risk-management and reusable risk/exit components."""

from quant_bitcoin.risk.exit_plan import (
    BreakEvenSettings,
    PartialExitSettings,
    RiskExitConfig,
    RiskExitDirection,
    RiskExitPlan,
    RiskExitPlanStatus,
    RiskExitTarget,
    RiskExitTargetSource,
    TimeStopSettings,
    TrailingStopSettings,
    create_risk_exit_plan,
    calculate_r_multiple_targets,
    combine_targets,
)
from quant_bitcoin.risk.exit_simulation import (
    PatternExitEvent,
    PatternExitReason,
    PatternExitSimulationResult,
    SoftInvalidationRule,
    simulate_pattern_exit,
)
from quant_bitcoin.risk.paper_checks import PaperRiskChecker, RiskDecision

__all__ = [
    "PaperRiskChecker",
    "RiskDecision",
    "RiskExitDirection",
    "RiskExitPlanStatus",
    "RiskExitTargetSource",
    "RiskExitTarget",
    "BreakEvenSettings",
    "TrailingStopSettings",
    "TimeStopSettings",
    "PartialExitSettings",
    "RiskExitConfig",
    "RiskExitPlan",
    "create_risk_exit_plan",
    "calculate_r_multiple_targets",
    "combine_targets",
    "PatternExitReason",
    "SoftInvalidationRule",
    "PatternExitEvent",
    "PatternExitSimulationResult",
    "simulate_pattern_exit",
]
