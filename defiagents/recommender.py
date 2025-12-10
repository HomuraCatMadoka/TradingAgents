"""
协议推荐引擎

根据用户的投资偏好推荐合适的 DeFi 协议。
"""

import logging
from typing import List, Dict, Optional, Any
import requests

logger = logging.getLogger(__name__)


class ProtocolRecommender:
    """协议推荐器"""

    def __init__(self):
        """初始化推荐器"""
        # 协议分类数据库（可扩展）
        self.protocol_database = {
            # Lending - 借贷协议
            "aave-v3": {
                "name": "Aave V3",
                "type": "lending",
                "risk": "low",
                "typical_apy": 5.2,
                "chains": ["ethereum", "arbitrum", "optimism", "polygon", "base"],
                "tokens": ["USDC", "USDT", "DAI", "ETH", "WBTC"],
                "min_tvl": 1000000000,  # 10亿+
                "features": ["借贷", "稳定币", "蓝筹"],
            },
            "compound-v3": {
                "name": "Compound V3",
                "type": "lending",
                "risk": "low",
                "typical_apy": 4.8,
                "chains": ["ethereum", "arbitrum", "polygon", "base"],
                "tokens": ["USDC", "USDT", "DAI", "ETH"],
                "min_tvl": 500000000,  # 5亿+
                "features": ["借贷", "稳定币", "蓝筹"],
            },
            "radiant-v2": {
                "name": "Radiant V2",
                "type": "lending",
                "risk": "medium",
                "typical_apy": 7.5,
                "chains": ["arbitrum", "bnb"],
                "tokens": ["USDC", "USDT", "DAI", "ETH", "WBTC"],
                "min_tvl": 100000000,  # 1亿+
                "features": ["借贷", "跨链"],
            },

            # DEX - 去中心化交易所
            "uniswap-v3": {
                "name": "Uniswap V3",
                "type": "dex",
                "risk": "medium",
                "typical_apy": 12.5,
                "chains": ["ethereum", "arbitrum", "optimism", "polygon", "base"],
                "tokens": ["ETH", "USDC", "USDT", "WBTC", "DAI"],
                "min_tvl": 2000000000,  # 20亿+
                "features": ["流动性挖矿", "交易费", "蓝筹"],
            },
            "curve": {
                "name": "Curve Finance",
                "type": "dex",
                "risk": "low",
                "typical_apy": 8.0,
                "chains": ["ethereum", "arbitrum", "optimism", "polygon"],
                "tokens": ["USDC", "USDT", "DAI", "FRAX", "3CRV"],
                "min_tvl": 1500000000,  # 15亿+
                "features": ["稳定币", "低滑点", "流动性挖矿"],
            },
            "balancer": {
                "name": "Balancer",
                "type": "dex",
                "risk": "medium",
                "typical_apy": 10.0,
                "chains": ["ethereum", "arbitrum", "optimism", "polygon"],
                "tokens": ["ETH", "USDC", "DAI", "WBTC"],
                "min_tvl": 500000000,  # 5亿+
                "features": ["多资产池", "自动平衡"],
            },

            # Staking - 质押
            "lido": {
                "name": "Lido",
                "type": "staking",
                "risk": "low",
                "typical_apy": 3.5,
                "chains": ["ethereum"],
                "tokens": ["ETH", "stETH"],
                "min_tvl": 10000000000,  # 100亿+
                "features": ["ETH质押", "流动性质押", "蓝筹"],
            },
            "rocket-pool": {
                "name": "Rocket Pool",
                "type": "staking",
                "risk": "medium",
                "typical_apy": 3.8,
                "chains": ["ethereum"],
                "tokens": ["ETH", "rETH"],
                "min_tvl": 1000000000,  # 10亿+
                "features": ["ETH质押", "去中心化"],
            },

            # Derivatives - 衍生品
            "gmx": {
                "name": "GMX",
                "type": "derivatives",
                "risk": "high",
                "typical_apy": 18.0,
                "chains": ["arbitrum", "avalanche"],
                "tokens": ["ETH", "WBTC", "USDC", "GLP"],
                "min_tvl": 300000000,  # 3亿+
                "features": ["永续合约", "杠杆交易", "高收益"],
            },
            "dydx": {
                "name": "dYdX",
                "type": "derivatives",
                "risk": "high",
                "typical_apy": 15.0,
                "chains": ["ethereum"],
                "tokens": ["ETH", "WBTC", "USDC"],
                "min_tvl": 500000000,  # 5亿+
                "features": ["永续合约", "订单簿", "杠杆交易"],
            },

            # Yield Aggregators - 收益聚合器
            "yearn-finance": {
                "name": "Yearn Finance",
                "type": "yield",
                "risk": "medium",
                "typical_apy": 10.5,
                "chains": ["ethereum", "arbitrum", "optimism"],
                "tokens": ["USDC", "USDT", "DAI", "ETH"],
                "min_tvl": 200000000,  # 2亿+
                "features": ["自动复利", "收益优化"],
            },
        }

    def recommend(
        self,
        risk_preference: Optional[str] = None,
        protocol_type: Optional[str] = None,
        min_apy: Optional[float] = None,
        chain: Optional[str] = None,
        tokens: Optional[List[str]] = None,
        investment_amount: Optional[float] = None,
        top_n: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        根据条件推荐协议

        Args:
            risk_preference: 风险偏好 (low/medium/high)
            protocol_type: 协议类型 (lending/dex/staking/derivatives/yield)
            min_apy: 最小目标APY
            chain: 目标区块链
            tokens: 关注的代币列表
            investment_amount: 投资金额（用于判断是否匹配协议规模）
            top_n: 返回前N个推荐

        Returns:
            推荐协议列表
        """
        candidates = []

        for slug, data in self.protocol_database.items():
            # 1. 风险过滤
            if risk_preference and data["risk"] != risk_preference:
                # 允许低风险用户接受中等风险
                if not (risk_preference == "low" and data["risk"] == "medium"):
                    continue

            # 2. 协议类型过滤
            if protocol_type and data["type"] != protocol_type:
                continue

            # 3. APY 过滤
            if min_apy and data["typical_apy"] < min_apy:
                continue

            # 4. 区块链过滤
            if chain and chain not in data["chains"]:
                continue

            # 5. 代币过滤
            if tokens:
                token_match = any(t.upper() in [dt.upper() for dt in data["tokens"]] for t in tokens)
                if not token_match:
                    continue

            # 计算评分
            score = self._calculate_score(data, risk_preference, min_apy, investment_amount)

            candidates.append({
                "slug": slug,
                "name": data["name"],
                "type": data["type"],
                "risk": data["risk"],
                "apy": data["typical_apy"],
                "chains": data["chains"],
                "tokens": data["tokens"],
                "features": data["features"],
                "score": score,
            })

        # 按评分排序
        candidates.sort(key=lambda x: x["score"], reverse=True)

        return candidates[:top_n]

    def _calculate_score(
        self,
        protocol_data: Dict,
        risk_preference: Optional[str],
        min_apy: Optional[float],
        investment_amount: Optional[float],
    ) -> float:
        """计算协议推荐评分"""
        score = 50.0  # 基础分

        # 1. TVL 加分（更安全）
        tvl = protocol_data.get("min_tvl", 0)
        if tvl > 1_000_000_000:  # 10亿+
            score += 20
        elif tvl > 500_000_000:  # 5亿+
            score += 15
        elif tvl > 100_000_000:  # 1亿+
            score += 10

        # 2. 风险匹配加分
        if risk_preference:
            if protocol_data["risk"] == risk_preference:
                score += 15
            elif risk_preference == "low" and protocol_data["risk"] == "medium":
                score += 5  # 低风险用户可以考虑中等风险

        # 3. APY 加分
        apy = protocol_data.get("typical_apy", 0)
        if min_apy:
            if apy >= min_apy * 1.5:  # APY 远超预期
                score += 15
            elif apy >= min_apy:
                score += 10

        # 4. 多链支持加分
        chains_count = len(protocol_data.get("chains", []))
        score += min(chains_count * 2, 10)

        # 5. 蓝筹协议加分
        if "蓝筹" in protocol_data.get("features", []):
            score += 10

        return score

    def format_recommendation_message(
        self,
        recommendations: List[Dict[str, Any]],
        user_criteria: Optional[Dict[str, Any]] = None,
    ) -> str:
        """格式化推荐消息"""
        if not recommendations:
            return "❌ 未找到符合条件的协议。请尝试放宽条件或联系管理员。"

        # 构建标题
        criteria_parts = []
        if user_criteria:
            if user_criteria.get("risk_preference"):
                criteria_parts.append(f"{user_criteria['risk_preference']}风险")
            if user_criteria.get("protocol_type"):
                type_cn = {
                    "lending": "借贷",
                    "dex": "DEX",
                    "staking": "质押",
                    "derivatives": "衍生品",
                    "yield": "收益聚合",
                }
                criteria_parts.append(type_cn.get(user_criteria["protocol_type"], user_criteria["protocol_type"]))
            if user_criteria.get("min_apy"):
                criteria_parts.append(f"APY≥{user_criteria['min_apy']}%")
            if user_criteria.get("chain"):
                criteria_parts.append(f"{user_criteria['chain']}链")

        criteria_str = "、".join(criteria_parts) if criteria_parts else "您的条件"

        message = f"🎯 **根据{criteria_str}，为您推荐以下协议：**\n\n"

        # 添加每个推荐
        for idx, rec in enumerate(recommendations, 1):
            risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}[rec["risk"]]
            type_emoji = {
                "lending": "🏦",
                "dex": "💱",
                "staking": "🔐",
                "derivatives": "📊",
                "yield": "🌾",
            }.get(rec["type"], "📌")

            message += f"{idx}. **{rec['name']}** `{rec['slug']}`\n"
            message += f"   {type_emoji} 类型：{rec['type'].upper()}\n"
            message += f"   {risk_emoji} 风险：{rec['risk'].upper()}\n"
            message += f"   📈 典型APY：{rec['apy']:.1f}%\n"
            message += f"   ⛓️ 支持链：{', '.join(rec['chains'][:3])}\n"
            message += f"   💰 支持代币：{', '.join(rec['tokens'][:4])}\n"
            message += f"   ✨ 特点：{', '.join(rec['features'])}\n"
            message += f"   💯 推荐度：{rec['score']:.0f}/100\n\n"

        message += "💡 **使用提示：**\n"
        message += f"• 分析详情：`/analyze <协议slug>`\n"
        message += f"• 对比协议：`/compare <协议1> <协议2>`\n"
        message += f"• 查看图表：`/chart apy {' '.join([r['slug'] for r in recommendations])}`\n"

        return message


# 全局单例
_recommender_instance = None


def get_recommender() -> ProtocolRecommender:
    """获取协议推荐器单例"""
    global _recommender_instance
    if _recommender_instance is None:
        _recommender_instance = ProtocolRecommender()
    return _recommender_instance
