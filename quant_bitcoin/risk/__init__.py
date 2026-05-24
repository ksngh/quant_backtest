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
    TARGET_SEMANTICS_SCHEMA_VERSION,
    TimeStopSettings,
    TrailingStopSettings,
    create_risk_exit_plan,
    calculate_r_multiple_targets,
    combine_targets,
    target_semantics_metadata,
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
    "TARGET_SEMANTICS_SCHEMA_VERSION",
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
    "target_semantics_metadata",
    "PatternExitReason",
    "SoftInvalidationRule",
    "PatternExitEvent",
    "PatternExitSimulationResult",
    "simulate_pattern_exit",
]
