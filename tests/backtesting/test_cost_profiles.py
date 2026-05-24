import inspect

import pytest

from quant_bitcoin.backtesting.cost_profiles import break_even_cost_bps, cost_profile


def test_cost_profile_mapping() -> None:
    profile = cost_profile("conservative_crypto_1m")

    assert profile.config.taker_fee_bps == 10.0
    assert profile.config.spread_bps == 3.0
    assert profile.config.slippage_bps == 5.0
    assert profile.to_metadata()["profile_key"] == "conservative_crypto_1m"


def test_unknown_cost_profile_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported cost profile"):
        cost_profile("real_exchange_lookup")


def test_break_even_cost_bps() -> None:
    assert break_even_cost_bps(10.0, 10_000.0) == pytest.approx(10.0)
    assert break_even_cost_bps(10.0, 0.0) is None


def test_cost_profiles_have_no_external_fee_lookup() -> None:
    import quant_bitcoin.backtesting.cost_profiles as cost_profiles

    source = inspect.getsource(cost_profiles)
    assert "requests" not in source
    assert "Binance" not in source
    assert "order endpoint" not in source
