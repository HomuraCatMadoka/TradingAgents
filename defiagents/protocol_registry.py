"""
DeFi Protocol Registry - 基于调研结果的协议配置索引

本文件包含所有支持协议的标准化配置，包括：
- 数据源端点（DeFi Llama, The Graph, 官方API）
- 智能合约地址
- 关键指标计算方法
- 风险评级
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ProtocolConfig:
    """协议配置数据类"""
    name: str
    slug: str  # DeFi Llama slug
    category: str  # DEX, Lending, Yield, Derivative
    chains: List[str]
    tvl_tier: str  # Blue-chip (>$1B), Mature (>$100M), Emerging (<$100M)
    risk_level: str  # Blue-chip, Mature, Emerging, Experimental

    # Data sources
    defillama_slug: str
    has_official_api: bool
    official_api_url: Optional[str]

    # The Graph subgraphs
    subgraphs: Dict[str, str]  # chain -> subgraph_id

    # Contract addresses (主要链)
    contracts: Dict[str, Dict[str, str]]  # chain -> {contract_name: address}

    # Special notes
    notes: str


# ============================================================================
# DEX 协议（去中心化交易所）
# ============================================================================

UNISWAP_V3 = ProtocolConfig(
    name="Uniswap V3",
    slug="uniswap-v3",
    category="DEX",
    chains=["ethereum", "arbitrum", "optimism", "polygon", "base", "bnb"],
    tvl_tier="Blue-chip",
    risk_level="Blue-chip",
    defillama_slug="uniswap-v3",
    has_official_api=False,
    official_api_url=None,
    subgraphs={
        "ethereum": "uniswap/uniswap-v3",
        "arbitrum": "uniswap/uniswap-v3-arbitrum",
        "optimism": "uniswap/uniswap-v3-optimism",
        "polygon": "uniswap/uniswap-v3-polygon",
    },
    contracts={
        "ethereum": {
            "factory": "0x1F98431c8aD98523631AE4a59f267346ea31F984",
            "router": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
            "nft_manager": "0xC36442b4a4522E871399CD717aBDD847Ab11FE88",
        }
    },
    notes="集中流动性AMM，费率0.01%/0.05%/0.3%/1.0%。APY=(24h_fees*365)/TVL"
)

CURVE = ProtocolConfig(
    name="Curve Finance",
    slug="curve-dex",
    category="DEX",
    chains=["ethereum", "arbitrum", "optimism", "polygon", "avalanche"],
    tvl_tier="Blue-chip",
    risk_level="Blue-chip",
    defillama_slug="curve-dex",
    has_official_api=True,
    official_api_url="https://api.curve.fi/api",
    subgraphs={
        "ethereum": "aurtbs/curve-finance",  # 社区维护，不稳定
    },
    contracts={
        "ethereum": {
            "address_provider": "0x0000000022D53366457F9d5E68Ec105046FC4383",
            "3pool": "0xbEbc44782c7db0a1a60Cb6fe97d0b483032FF1C7",
        }
    },
    notes="稳定币交易龙头。推荐使用官方API而非子图。APY=Base_APY+(CRV_APY*Boost)"
)

BALANCER = ProtocolConfig(
    name="Balancer",
    slug="balancer",
    category="DEX",
    chains=["ethereum", "arbitrum", "polygon", "gnosis"],
    tvl_tier="Mature",
    risk_level="Mature",
    defillama_slug="balancer",
    has_official_api=False,
    official_api_url=None,
    subgraphs={
        "ethereum": "balancer-labs/balancer-v2",
        "arbitrum": "balancer-labs/balancer-arbitrum-v2",
        "polygon": "balancer-labs/balancer-polygon-v2",
    },
    contracts={
        "ethereum": {
            "vault": "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
        }
    },
    notes="权重池+可组合稳定池。所有链使用同一Vault地址"
)

SUSHISWAP = ProtocolConfig(
    name="SushiSwap",
    slug="sushiswap",
    category="DEX",
    chains=["ethereum", "arbitrum", "polygon", "avalanche", "bnb"],  # 实际支持40+链
    tvl_tier="Mature",
    risk_level="Mature",
    defillama_slug="sushiswap",
    has_official_api=False,
    official_api_url=None,
    subgraphs={
        "ethereum": "sushiswap/exchange",  # V2
    },
    contracts={},
    notes="V2费率0.3%(0.25%给LP+0.05%给xSUSHI)。2023年4月有安全事件"
)

PANCAKESWAP = ProtocolConfig(
    name="PancakeSwap",
    slug="pancakeswap",
    category="DEX",
    chains=["bnb", "ethereum", "arbitrum", "base"],
    tvl_tier="Blue-chip",
    risk_level="Mature",
    defillama_slug="pancakeswap",
    has_official_api=True,
    official_api_url="https://api.pancakeswap.info/api/v2",
    subgraphs={
        "bnb": "pancakeswap/exchange-v3-bsc",
    },
    contracts={},
    notes="BNB Chain龙头DEX。包含IFO、彩票等CAKE燃烧机制"
)


# ============================================================================
# 借贷协议
# ============================================================================

AAVE_V3 = ProtocolConfig(
    name="Aave V3",
    slug="aave-v3",
    category="Lending",
    chains=["ethereum", "arbitrum", "optimism", "polygon", "avalanche", "base"],
    tvl_tier="Blue-chip",
    risk_level="Blue-chip",
    defillama_slug="aave-v3",
    has_official_api=False,
    official_api_url=None,
    subgraphs={
        "ethereum": "aave/protocol-v3",
        "arbitrum": "aave/protocol-v3-arbitrum",
        "optimism": "aave/protocol-v3-optimism",
        "polygon": "aave/protocol-v3-polygon",
    },
    contracts={
        "ethereum": {
            "pool": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
        }
    },
    notes="利率单位为Ray(10^27)，需除以10^27。健康因子HF=(Collateral*Threshold)/Debt"
)

COMPOUND_V3 = ProtocolConfig(
    name="Compound V3",
    slug="compound-v3",
    category="Lending",
    chains=[
        "ethereum",
        "polygon",
        "base",
        "arbitrum",
        "optimism",
        "scroll",
        "mantle",
        "ronin",
        "unichain",
    ],
    tvl_tier="Blue-chip",
    risk_level="Blue-chip",
    defillama_slug="compound-v3",
    has_official_api=False,
    official_api_url=None,
    subgraphs={
        "ethereum": "compound-finance/compound-v3-ethereum-usdc",
    },
    contracts={},
    notes="Comet架构：每个市场只有一个Base Asset可借，支持多链部署（9链）。抵押品不产生利息"
)

RADIANT = ProtocolConfig(
    name="Radiant Capital",
    slug="radiant-capital",
    category="Lending",
    chains=["arbitrum", "bnb", "ethereum"],
    tvl_tier="Mature",
    risk_level="Mature",
    defillama_slug="radiant-capital",
    has_official_api=False,
    official_api_url=None,
    subgraphs={},  # 无公开稳定子图
    contracts={},
    notes="全链借贷(LayerZero)。需锁定5% dLP才能获得RDNT奖励"
)

MAKERDAO = ProtocolConfig(
    name="MakerDAO",
    slug="makerdao",
    category="Lending",
    chains=["ethereum"],
    tvl_tier="Blue-chip",
    risk_level="Blue-chip",
    defillama_slug="makerdao",
    has_official_api=False,
    official_api_url=None,
    subgraphs={
        "ethereum": "protofire/maker-protocol",
    },
    contracts={},
    notes="DAI稳定币发行。DSR是DeFi基准利率。参考makerburn.com获取实时数据"
)


# ============================================================================
# 收益类协议
# ============================================================================

LIDO = ProtocolConfig(
    name="Lido",
    slug="lido",
    category="Yield",
    chains=["ethereum", "polygon", "solana"],
    tvl_tier="Blue-chip",
    risk_level="Blue-chip",
    defillama_slug="lido",
    has_official_api=False,
    official_api_url=None,
    subgraphs={
        "ethereum": "lidofinance/lido",
    },
    contracts={
        "ethereum": {
            "steth": "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84",
        }
    },
    notes="stETH为Rebase代币，APR约3-4%。收取10%费用(5%节点+5%DAO)"
)

ROCKET_POOL = ProtocolConfig(
    name="Rocket Pool",
    slug="rocket-pool",
    category="Yield",
    chains=["ethereum"],
    tvl_tier="Blue-chip",
    risk_level="Blue-chip",
    defillama_slug="rocket-pool",
    has_official_api=False,
    official_api_url=None,
    subgraphs={
        "ethereum": "rocket-pool/rocket-pool-mainnet",
    },
    contracts={},
    notes="rETH非Rebase，汇率对ETH增长。去中心化节点运营，抗审查"
)

PENDLE = ProtocolConfig(
    name="Pendle Finance",
    slug="pendle",
    category="Yield",
    chains=["ethereum", "arbitrum", "bnb"],
    tvl_tier="Mature",
    risk_level="Mature",
    defillama_slug="pendle",
    has_official_api=False,
    official_api_url=None,
    subgraphs={
        "arbitrum": "ExXGU3ub2nrT5stPk5cH4hSk2qunJcMcP8eX5GAhrZhe",  # 完整ID
    },
    contracts={},
    notes="利率交易。PT=固定收益，YT=浮动收益。YT到期归零需谨慎"
)

YEARN = ProtocolConfig(
    name="Yearn Finance",
    slug="yearn-finance",
    category="Yield",
    chains=["ethereum", "arbitrum", "optimism", "fantom"],
    tvl_tier="Mature",
    risk_level="Mature",
    defillama_slug="yearn-finance",
    has_official_api=True,
    official_api_url="https://ydaemon.yearn.fi",
    subgraphs={},  # 推荐使用API而非子图
    contracts={},
    notes="收益聚合器。推荐使用yDaemon API获取net_apy。策略风险叠加需注意"
)

BEEFY = ProtocolConfig(
    name="Beefy Finance",
    slug="beefy",
    category="Yield",
    chains=["arbitrum", "optimism", "polygon", "base", "bnb", "avalanche"],
    tvl_tier="Mature",
    risk_level="Mature",
    defillama_slug="beefy",
    has_official_api=True,
    official_api_url="https://api.beefy.finance",
    subgraphs={},
    contracts={},
    notes="多链收益优化。API完善。mooToken自动复利。存在嵌套风险"
)


# ============================================================================
# 衍生品和其他
# ============================================================================

GMX = ProtocolConfig(
    name="GMX",
    slug="gmx",
    category="Derivative",
    chains=["arbitrum", "avalanche"],
    tvl_tier="Blue-chip",
    risk_level="Blue-chip",
    defillama_slug="gmx",
    has_official_api=True,
    official_api_url="https://api.gmx.io",
    subgraphs={
        "arbitrum": "gmx-io/gmx-stats",
    },
    contracts={},
    notes="永续合约DEX。GLP作为对手盘。单边极端行情可能亏损"
)

FRAX = ProtocolConfig(
    name="Frax Finance",
    slug="frax",
    category="Yield",
    chains=["ethereum"],
    tvl_tier="Mature",
    risk_level="Mature",
    defillama_slug="frax",
    has_official_api=True,
    official_api_url="https://api.frax.finance",
    subgraphs={},
    contracts={},
    notes="FRAX稳定币+sfrxETH。AMO机制复杂。sfrxETH收益率通常高于stETH"
)


# ============================================================================
# 协议注册表
# ============================================================================

PROTOCOL_REGISTRY = {
    # DEX
    "uniswap-v3": UNISWAP_V3,
    "curve-dex": CURVE,
    "balancer": BALANCER,
    "sushiswap": SUSHISWAP,
    "pancakeswap": PANCAKESWAP,

    # Lending
    "aave-v3": AAVE_V3,
    "compound-v3": COMPOUND_V3,
    "radiant-capital": RADIANT,
    "makerdao": MAKERDAO,

    # Yield
    "lido": LIDO,
    "rocket-pool": ROCKET_POOL,
    "pendle": PENDLE,
    "yearn-finance": YEARN,
    "beefy": BEEFY,

    # Derivative & Others
    "gmx": GMX,
    "frax": FRAX,
}


def get_protocol(slug: str) -> Optional[ProtocolConfig]:
    """获取协议配置"""
    return PROTOCOL_REGISTRY.get(slug)


def get_protocols_by_category(category: str) -> List[ProtocolConfig]:
    """按类别获取协议列表"""
    return [p for p in PROTOCOL_REGISTRY.values() if p.category == category]


def get_protocols_by_chain(chain: str) -> List[ProtocolConfig]:
    """按链获取协议列表"""
    return [p for p in PROTOCOL_REGISTRY.values() if chain in p.chains]


def get_blue_chip_protocols() -> List[ProtocolConfig]:
    """获取蓝筹协议列表"""
    return [p for p in PROTOCOL_REGISTRY.values() if p.risk_level == "Blue-chip"]


# 快捷访问
ALL_PROTOCOLS = list(PROTOCOL_REGISTRY.values())
DEX_PROTOCOLS = get_protocols_by_category("DEX")
LENDING_PROTOCOLS = get_protocols_by_category("Lending")
YIELD_PROTOCOLS = get_protocols_by_category("Yield")
