"""
端到端安全层集成测试

测试 S1 OutputValidator 和 S2 ProtocolWhitelist 在完整流程中的表现。
"""

import pytest
from unittest.mock import Mock, patch

from defiagents.security.output_validator import OutputValidator, ValidationContext
from defiagents.security.protocol_whitelist import ProtocolWhitelist
from defiagents.graph.node_wrappers import wrap_agent_node_with_validation


class TestOutputValidatorE2E:
    """S1 OutputValidator 端到端测试"""

    def test_node_wrapper_patches_dangerous_output(self):
        """测试节点包装器正确检测并标记危险输出"""
        # 模拟一个返回危险指令的 Agent 节点
        def dangerous_agent_node(state):
            return {
                "trader_plan": "建议立即 approve unlimited USDC 并 transfer all 到协议合约"
            }

        # 包装节点
        wrapped_node = wrap_agent_node_with_validation(
            dangerous_agent_node,
            agent_name="DeFi Trader",
            state_key="trader_plan"
        )

        # 执行节点
        test_state = {
            "protocol_of_interest": "aave-v3",
            "investment_amount": 100000.0
        }
        result = wrapped_node(test_state)

        # 验证输出已被修补
        assert "trader_plan" in result
        patched_text = result["trader_plan"]
        assert "⚠️" in patched_text  # 包含警告标记
        assert "安全提示" in patched_text or "Output Validator" in patched_text
        assert "validation_issues" in result  # 包含问题记录
        assert len(result["validation_issues"]) >= 2  # 至少检测到2个危险指令

    def test_node_wrapper_preserves_safe_output(self):
        """测试节点包装器不修改安全输出"""
        def safe_agent_node(state):
            return {"market_report": "根据分析，Aave V3 的TVL稳定增长，APY在合理范围内"}

        wrapped_node = wrap_agent_node_with_validation(
            safe_agent_node,
            agent_name="Market Analyst",
            state_key="market_report"
        )

        test_state = {"protocol_of_interest": "aave-v3"}
        result = wrapped_node(test_state)

        # 验证安全输出保持不变（没有警告标记）
        assert "market_report" in result
        assert "⚠️" not in result["market_report"]
        assert "validation_issues" not in result  # 无问题记录

    def test_node_wrapper_handles_non_dict_result(self):
        """测试节点包装器处理非字典返回值"""
        def broken_node(state):
            return "string result"

        wrapped_node = wrap_agent_node_with_validation(
            broken_node,
            agent_name="Broken Agent",
            state_key="report"
        )

        test_state = {}
        result = wrapped_node(test_state)
        assert result == "string result"  # 原样返回

    def test_amount_validation_with_context(self):
        """测试金额验证使用上下文信息"""
        validator = OutputValidator()

        # 场景1: 建议金额 > 投资金额
        context = ValidationContext(
            agent_name="Trader",
            protocol_name="aave",
            investment_amount=10000.0
        )
        result = validator.validate(
            "建议投入 $500,000 到 Aave V3",
            context=context
        )
        assert not result["is_safe"]
        assert any("金额" in issue["category"] or "amount" in issue["category"]
                   for issue in result["issues"])

        # 场景2: 建议金额 < 投资金额
        result2 = validator.validate(
            "建议投入 $5,000 到 Aave V3",
            context=context
        )
        assert result2["is_safe"]  # 无警告


class TestProtocolWhitelistE2E:
    """S2 ProtocolWhitelist 端到端测试"""

    @pytest.fixture
    def mock_defillama(self):
        """Mock DeFi Llama 数据源"""
        with patch("defiagents.dataflows.defi.defillama.get_protocol") as mock:
            yield mock

    @pytest.fixture
    def mock_coingecko(self):
        """Mock CoinGecko 数据源"""
        with patch("defiagents.dataflows.defi.coingecko.get_coin_info_by_id") as mock:
            yield mock

    @pytest.fixture
    def mock_the_graph(self):
        """Mock The Graph 数据源"""
        with patch("defiagents.dataflows.defi.the_graph.check_protocol_exists") as mock:
            mock.return_value = True
            yield mock

    def test_trusted_protocol_passes_all_checks(
        self, mock_defillama, mock_coingecko, mock_the_graph
    ):
        """测试蓝筹协议通过所有检查"""
        # Mock 返回值
        mock_defillama.return_value = {
            "tvl": 5_000_000_000,  # $5B TVL
            "audits": ["CertiK", "Trail of Bits", "OpenZeppelin"],
            "listedAt": 1609459200  # 2021-01-01
        }
        mock_coingecko.return_value = {
            "market_data": {"market_cap": {"usd": 3_000_000_000}},
            "genesis_date": "2020-12-01"
        }

        whitelist = ProtocolWhitelist(config={})
        result = whitelist.check("aave-v3")

        assert result["status"] == "trusted"
        assert result["confidence_score"] >= 0.75
        assert len(result["data_sources"]) >= 2  # 至少2个数据源成功

    def test_suspicious_protocol_flagged(
        self, mock_defillama, mock_coingecko, mock_the_graph
    ):
        """测试可疑协议被标记"""
        # Mock 返回低 TVL 协议
        mock_defillama.return_value = {
            "tvl": 5_000_000,  # $5M TVL（低于阈值）
            "audits": [],
            "listedAt": int(__import__("time").time()) - 86400 * 30  # 30天前
        }
        mock_coingecko.side_effect = Exception("Not found")

        whitelist = ProtocolWhitelist(config={})
        result = whitelist.check("suspicious-defi")

        assert result["status"] == "suspicious"
        assert result["confidence_score"] < 0.5
        assert "reason" in result
        assert any("TVL" in reason or "audit" in reason.lower()
                   for reason in result.get("reason", "").split())

    def test_cache_reduces_api_calls(
        self, mock_defillama, mock_coingecko, mock_the_graph
    ):
        """测试缓存减少重复 API 调用"""
        mock_defillama.return_value = {"tvl": 100_000_000, "audits": ["CertiK"]}
        mock_coingecko.return_value = {"genesis_date": "2021-01-01"}

        whitelist = ProtocolWhitelist(config={})

        # 首次调用
        result1 = whitelist.check("compound-v3")
        assert mock_defillama.call_count == 1

        # 第二次调用（应命中缓存）
        result2 = whitelist.check("compound-v3")
        assert mock_defillama.call_count == 1  # 未增加
        assert result1["status"] == result2["status"]

    def test_hardcoded_whitelist_bypasses_checks(self):
        """测试硬编码白名单直接返回 trusted"""
        whitelist = ProtocolWhitelist(config={})

        # 添加到硬编码白名单
        whitelist.trusted_protocols.add("my-safe-protocol")

        # 即使没有数据也应该返回 trusted
        result = whitelist.check("my-safe-protocol")
        assert result["status"] == "trusted"
        assert result["confidence_score"] == 1.0


class TestIntegratedFlow:
    """集成流程测试"""

    def test_full_security_pipeline(self):
        """测试完整安全流水线：白名单验证 → Agent 执行 → 输出验证"""
        # 1. 协议白名单检查
        with patch("defiagents.dataflows.defi.defillama.get_protocol") as mock_dl:
            mock_dl.return_value = {
                "tvl": 200_000_000,
                "audits": ["CertiK", "Trail of Bits"]
            }
            whitelist = ProtocolWhitelist(config={})
            whitelist_result = whitelist.check("aave-v3")
            assert whitelist_result["status"] in ["trusted", "unverified"]

        # 2. 模拟 Agent 执行（带验证包装）
        def agent_with_risk(state):
            return {
                "final_decision": (
                    f"协议 {state['protocol_of_interest']} 通过白名单验证。"
                    "建议投入 $1,000,000。为加速收益，建议 approve unlimited USDC。"
                )
            }

        wrapped_agent = wrap_agent_node_with_validation(
            agent_with_risk,
            agent_name="Portfolio Manager",
            state_key="final_decision"
        )

        state = {
            "protocol_of_interest": "aave-v3",
            "investment_amount": 100_000.0,
            "protocol_whitelist_status": whitelist_result["status"]
        }

        result = wrapped_agent(state)

        # 3. 验证输出被正确标记
        assert "final_decision" in result
        patched_text = result["final_decision"]
        assert "⚠️" in patched_text  # 危险指令被检测
        assert "unlimited" in patched_text  # 原文保留
        assert "安全提示" in patched_text or "CRITICAL" in patched_text

        # 4. 验证问题记录
        assert "validation_issues" in result
        issues = result["validation_issues"]
        assert len(issues) >= 2  # 至少2个问题：approve unlimited + 金额异常


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
