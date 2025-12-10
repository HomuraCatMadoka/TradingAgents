"""Compound V3 协议测试"""
import pytest
from defiagents.dataflows.defi.defillama import get_protocol_tvl, get_protocol_info
from defiagents.agents.utils.defi_protocol_tools import get_compound_markets


def test_compound_v3_tvl():
    """测试 Compound V3 TVL 获取"""
    tvl = get_protocol_tvl("compound-v3")
    assert tvl > 1_000_000_000  # > $1B
    assert isinstance(tvl, float)


def test_compound_v3_info():
    """测试 Compound V3 协议信息"""
    info = get_protocol_info("compound-v3")
    assert info["name"] == "Compound V3"
    assert "Ethereum" in info.get("chains", [])
    assert len(info.get("chains", [])) >= 5  # 至少5条链


def test_compound_markets_tool():
    """测试 Compound V3 市场工具函数"""
    result = get_compound_markets.invoke({"protocol": "compound-v3"})
    assert "Compound V3" in result
    assert "TVL" in result
    assert "$" in result
    assert "借贷" in result or "lending" in result.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
