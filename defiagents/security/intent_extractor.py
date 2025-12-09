"""
意图提取器

从自然语言输入中提取结构化的投资意图参数。
"""
import re
import logging
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class InvestmentIntent:
    """投资意图数据类"""
    # 核心参数
    protocol_name: Optional[str] = None          # 协议名称
    action: Optional[str] = None                 # 动作（analyze/invest/compare）
    investment_amount: Optional[float] = None    # 投资金额（USD）
    risk_preference: Optional[str] = None        # 风险偏好（low/medium/high）

    # DeFi特定参数
    protocol_type: Optional[str] = None          # 协议类型（lending/dex/yield等）
    chain: Optional[str] = None                  # 区块链网络
    target_apy: Optional[float] = None           # 目标APY（年化收益率）
    timeframe: Optional[str] = None              # 时间框架（short/medium/long）

    # 额外约束
    tokens: Optional[List[str]] = None           # 关注的代币
    min_tvl: Optional[float] = None              # 最小TVL要求
    max_risk_score: Optional[float] = None       # 最大风险评分

    # 元数据
    raw_input: str = ""                          # 原始输入
    confidence: float = 0.0                      # 提取置信度

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {k: v for k, v in asdict(self).items() if v is not None}


class IntentExtractor:
    """意图提取器类"""

    def __init__(self):
        """初始化提取器"""

        # 协议名称映射（规范化）
        self.protocol_map = {
            # Lending
            "aave": "aave-v3",
            "aave v3": "aave-v3",
            "aave-v3": "aave-v3",
            "compound": "compound-v3",
            "compound v3": "compound-v3",

            # DEX
            "uniswap": "uniswap-v3",
            "uniswap v3": "uniswap-v3",
            "uni": "uniswap-v3",
            "curve": "curve",
            "balancer": "balancer",

            # Staking
            "lido": "lido",
            "rocket pool": "rocket-pool",

            # Derivatives
            "gmx": "gmx",
            "dydx": "dydx",
        }

        # 动作关键词
        self.action_patterns = {
            "analyze": [r"\b(analyze|analysis|check|evaluate|assess|review|看|分析|评估)\b"],
            "invest": [r"\b(invest|buy|购买|投资|存入|deposit)\b"],
            "compare": [r"\b(compare|对比|比较|vs|versus)\b"],
            "strategy": [r"\b(strategy|策略|方案|plan)\b"],
        }

        # 风险偏好关键词
        self.risk_patterns = {
            "low": [r"\b(low|safe|conservative|stable|低风险|安全|稳健|保守)\b"],
            "medium": [r"\b(medium|moderate|balanced|中等|适中|平衡)\b"],
            "high": [r"\b(high|aggressive|risky|高风险|激进|冒险)\b"],
        }

        # 协议类型关键词
        self.protocol_type_patterns = {
            "lending": [r"\b(lend|lending|borrow|borrowing|loan|借贷|存款|贷款)\b"],
            "dex": [r"\b(swap|dex|exchange|交易|兑换|流动性池|pool)\b"],
            "yield": [r"\b(yield|farming|挖矿|收益|farming)\b"],
            "staking": [r"\b(stak|质押)\b"],
            "derivatives": [r"\b(derivative|perpetual|futures|衍生品|永续|期货)\b"],
        }

        # 区块链网络关键词
        self.chain_patterns = {
            "ethereum": [r"\b(ethereum|eth|以太坊|主网|mainnet)\b"],
            "arbitrum": [r"\b(arbitrum|arb)\b"],
            "optimism": [r"\b(optimism|op)\b"],
            "base": [r"\b(base)\b"],
            "polygon": [r"\b(polygon|matic)\b"],
        }

        # 时间框架关键词
        self.timeframe_patterns = {
            "short": [r"\b(short|short-term|短期|几天|一周)\b"],
            "medium": [r"\b(medium|mid-term|中期|几周|一个月)\b"],
            "long": [r"\b(long|long-term|长期|几个月|一年)\b"],
        }

    def extract(self, user_input: str) -> InvestmentIntent:
        """
        从用户输入中提取投资意图

        Args:
            user_input: 用户输入的文本

        Returns:
            InvestmentIntent对象
        """
        intent = InvestmentIntent(raw_input=user_input)
        input_lower = user_input.lower()

        # 1. 提取协议名称
        intent.protocol_name = self._extract_protocol(input_lower)

        # 2. 提取动作
        intent.action = self._extract_action(input_lower)

        # 3. 提取投资金额
        intent.investment_amount = self._extract_amount(user_input)

        # 4. 提取风险偏好
        intent.risk_preference = self._extract_risk_preference(input_lower)

        # 5. 提取协议类型
        intent.protocol_type = self._extract_protocol_type(input_lower)

        # 6. 提取区块链网络
        intent.chain = self._extract_chain(input_lower)

        # 7. 提取目标APY
        intent.target_apy = self._extract_target_apy(user_input)

        # 8. 提取时间框架
        intent.timeframe = self._extract_timeframe(input_lower)

        # 9. 提取代币
        intent.tokens = self._extract_tokens(input_lower)

        # 10. 提取TVL要求
        intent.min_tvl = self._extract_min_tvl(user_input)

        # 11. 计算置信度
        intent.confidence = self._calculate_confidence(intent)

        logger.info(f"Extracted intent with confidence {intent.confidence:.2f}: {intent.to_dict()}")

        return intent

    def _extract_protocol(self, text: str) -> Optional[str]:
        """提取协议名称"""
        for key, value in self.protocol_map.items():
            if key in text:
                return value
        return None

    def _extract_action(self, text: str) -> Optional[str]:
        """提取动作"""
        for action, patterns in self.action_patterns.items():
            if any(re.search(p, text, re.IGNORECASE) for p in patterns):
                return action
        return "analyze"  # 默认动作

    def _extract_amount(self, text: str) -> Optional[float]:
        """提取投资金额"""
        # 匹配数字 + 单位（K/M/B/万/亿）
        patterns = [
            r"(\d+(?:\.\d+)?)\s*(k|thousand|千)",
            r"(\d+(?:\.\d+)?)\s*(m|million|百万)",
            r"(\d+(?:\.\d+)?)\s*(b|billion|亿)",
            r"(\d+(?:\.\d+)?)\s*万",
            r"\$?\s*(\d+(?:,\d{3})*(?:\.\d+)?)",  # 纯数字或货币格式
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                number = float(match.group(1).replace(',', ''))

                # 单位转换
                unit_text = match.group(0).lower()
                if 'k' in unit_text or '千' in unit_text or 'thousand' in unit_text:
                    return number * 1000
                elif 'm' in unit_text or '百万' in unit_text or 'million' in unit_text:
                    return number * 1_000_000
                elif 'b' in unit_text or '亿' in unit_text or 'billion' in unit_text:
                    return number * 1_000_000_000
                elif '万' in unit_text:
                    return number * 10_000
                else:
                    return number

        return None

    def _extract_risk_preference(self, text: str) -> Optional[str]:
        """提取风险偏好"""
        for risk_level, patterns in self.risk_patterns.items():
            if any(re.search(p, text, re.IGNORECASE) for p in patterns):
                return risk_level
        return None

    def _extract_protocol_type(self, text: str) -> Optional[str]:
        """提取协议类型"""
        for ptype, patterns in self.protocol_type_patterns.items():
            if any(re.search(p, text, re.IGNORECASE) for p in patterns):
                return ptype
        return None

    def _extract_chain(self, text: str) -> Optional[str]:
        """提取区块链网络"""
        for chain, patterns in self.chain_patterns.items():
            if any(re.search(p, text, re.IGNORECASE) for p in patterns):
                return chain
        return "ethereum"  # 默认以太坊

    def _extract_target_apy(self, text: str) -> Optional[float]:
        """提取目标APY"""
        # 匹配 "至少X%"、"大于X%"、"X%以上" 等
        patterns = [
            r"(至少|大于|超过|以上|>|≥)\s*(\d+(?:\.\d+)?)\s*%",
            r"apy\s*(至少|大于|>|≥)?\s*(\d+(?:\.\d+)?)\s*%",
            r"(\d+(?:\.\d+)?)\s*%\s*(以上|或更高|or\s+higher)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # 提取数字（可能在第1或第2个捕获组）
                groups = [g for g in match.groups() if g and re.match(r'\d+', g)]
                if groups:
                    return float(groups[0])

        return None

    def _extract_timeframe(self, text: str) -> Optional[str]:
        """提取时间框架"""
        for timeframe, patterns in self.timeframe_patterns.items():
            if any(re.search(p, text, re.IGNORECASE) for p in patterns):
                return timeframe
        return None

    def _extract_tokens(self, text: str) -> Optional[List[str]]:
        """提取代币列表"""
        common_tokens = ["usdc", "usdt", "dai", "eth", "weth", "wbtc", "steth"]
        found_tokens = [token for token in common_tokens if token in text]
        return found_tokens if found_tokens else None

    def _extract_min_tvl(self, text: str) -> Optional[float]:
        """提取最小TVL要求"""
        # 匹配 "TVL至少X"、"TVL大于X" 等
        patterns = [
            r"tvl\s*(至少|大于|超过|>|≥)\s*\$?\s*(\d+(?:\.\d+)?)\s*(m|b|million|billion|百万|亿)?",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                number = float(match.group(2))
                unit = match.group(3)

                if unit:
                    unit_lower = unit.lower()
                    if 'm' in unit_lower or '百万' in unit_lower or 'million' in unit_lower:
                        return number * 1_000_000
                    elif 'b' in unit_lower or '亿' in unit_lower or 'billion' in unit_lower:
                        return number * 1_000_000_000

                return number

        return None

    def _calculate_confidence(self, intent: InvestmentIntent) -> float:
        """计算提取置信度"""
        score = 0.0
        weights = {
            "protocol_name": 0.3,
            "action": 0.2,
            "investment_amount": 0.15,
            "risk_preference": 0.10,
            "protocol_type": 0.10,
            "chain": 0.05,
            "target_apy": 0.05,
            "timeframe": 0.05,
        }

        for field, weight in weights.items():
            if getattr(intent, field) is not None:
                score += weight

        return min(score, 1.0)


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    extractor = IntentExtractor()

    test_cases = [
        "分析Aave V3的投资机会",
        "我想用10万美金投资低风险的借贷协议",
        "对比Uniswap和Curve在Arbitrum上的流动性池收益",
        "找一个APY至少8%的稳定币策略",
        "分析Ethereum上TVL大于1B的DEX协议",
        "invest $50k in safe lending protocols with APY > 5%",
        "compare gmx vs dydx derivatives on arbitrum",
    ]

    print("\n" + "="*80)
    print("意图提取器测试")
    print("="*80 + "\n")

    for test_input in test_cases:
        print(f"输入: {test_input}")
        intent = extractor.extract(test_input)
        print(f"提取结果 (置信度: {intent.confidence:.2f}):")
        for key, value in intent.to_dict().items():
            if key != "raw_input":
                print(f"  {key}: {value}")
        print()

    print("="*80)
