"""
图表生成模块

使用 matplotlib 生成各种数据可视化图表。
"""

import io
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

# 使用非交互式后端（适合服务器环境）
matplotlib.use('Agg')

# 设置中文字体（尝试多个常见字体）
try:
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
except Exception:
    pass  # 如果字体不可用，使用默认字体


def generate_tvl_chart(
    protocol: str,
    tvl_history: List[Dict[str, float]],
    days: int = 30
) -> io.BytesIO:
    """生成 TVL 趋势图

    Args:
        protocol: 协议名称
        tvl_history: TVL 历史数据 [{"date": "2025-01-01", "tvl": 1000000}, ...]
        days: 显示的天数（默认 30 天）

    Returns:
        BytesIO 对象，包含 PNG 格式的图表
    """
    fig, ax = plt.subplots(figsize=(12, 6))

    # 提取数据
    dates = [datetime.fromisoformat(item["date"]) for item in tvl_history[-days:]]
    tvls = [item["tvl"] / 1e6 for item in tvl_history[-days:]]  # 转换为百万美元

    # 绘制折线图
    ax.plot(dates, tvls, linewidth=2, color='#4CAF50', marker='o', markersize=4)
    ax.fill_between(dates, tvls, alpha=0.3, color='#4CAF50')

    # 设置标题和标签
    ax.set_title(f'{protocol} TVL Trend ({days} Days)', fontsize=16, fontweight='bold')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('TVL (Million USD)', fontsize=12)

    # 格式化 Y 轴
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:.0f}M'))

    # 添加网格
    ax.grid(True, alpha=0.3, linestyle='--')

    # 旋转 X 轴标签
    plt.xticks(rotation=45, ha='right')

    # 添加最新值标注
    if tvls:
        latest_tvl = tvls[-1]
        latest_date = dates[-1]
        ax.annotate(
            f'${latest_tvl:.1f}M',
            xy=(latest_date, latest_tvl),
            xytext=(10, 10),
            textcoords='offset points',
            bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.7),
            arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0')
        )

    plt.tight_layout()

    # 保存到 BytesIO
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)

    return buf


def generate_apy_comparison_chart(
    protocols_data: List[Dict[str, any]]
) -> io.BytesIO:
    """生成 APY 对比柱状图

    Args:
        protocols_data: 协议数据列表
            [{"name": "Aave V3", "apy": 5.2, "risk": "low"}, ...]

    Returns:
        BytesIO 对象，包含 PNG 格式的图表
    """
    fig, ax = plt.subplots(figsize=(12, 6))

    # 提取数据
    protocols = [p["name"] for p in protocols_data]
    apys = [p["apy"] for p in protocols_data]
    risks = [p.get("risk", "medium") for p in protocols_data]

    # 风险颜色映射
    risk_colors = {
        "low": "#4CAF50",
        "medium": "#FFC107",
        "high": "#F44336"
    }
    colors = [risk_colors.get(risk, "#9E9E9E") for risk in risks]

    # 绘制柱状图
    bars = ax.bar(protocols, apys, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)

    # 在柱子上方添加数值标签
    for bar, apy in zip(bars, apys):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.,
            height + 0.3,
            f'{apy:.2f}%',
            ha='center',
            va='bottom',
            fontsize=10,
            fontweight='bold'
        )

    # 设置标题和标签
    ax.set_title('DeFi Protocol APY Comparison', fontsize=16, fontweight='bold')
    ax.set_ylabel('APY (%)', fontsize=12)
    ax.set_xlabel('Protocol', fontsize=12)

    # 添加网格
    ax.grid(True, alpha=0.3, linestyle='--', axis='y')

    # 旋转 X 轴标签
    plt.xticks(rotation=45, ha='right')

    # 添加图例
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#4CAF50', alpha=0.7, label='Low Risk'),
        Patch(facecolor='#FFC107', alpha=0.7, label='Medium Risk'),
        Patch(facecolor='#F44336', alpha=0.7, label='High Risk')
    ]
    ax.legend(handles=legend_elements, loc='upper right')

    plt.tight_layout()

    # 保存到 BytesIO
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)

    return buf


def generate_risk_radar_chart(
    risk_metrics: Dict[str, float]
) -> io.BytesIO:
    """生成风险评分雷达图

    Args:
        risk_metrics: 风险指标字典
            {
                "Smart Contract": 8.5,
                "Liquidity": 7.2,
                "Governance": 6.8,
                "Market": 7.5,
                "Operational": 8.0
            }

    Returns:
        BytesIO 对象，包含 PNG 格式的图表
    """
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))

    # 提取数据
    categories = list(risk_metrics.keys())
    values = list(risk_metrics.values())

    # 闭合雷达图
    values += values[:1]
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    angles += angles[:1]

    # 绘制雷达图
    ax.plot(angles, values, 'o-', linewidth=2, color='#2196F3', label='Risk Score')
    ax.fill(angles, values, alpha=0.25, color='#2196F3')

    # 设置类别标签
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=11)

    # 设置刻度范围
    ax.set_ylim(0, 10)
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(['2', '4', '6', '8', '10'], fontsize=9)

    # 添加网格
    ax.grid(True, linestyle='--', alpha=0.5)

    # 设置标题
    ax.set_title('Risk Assessment Radar', fontsize=16, fontweight='bold', pad=20)

    # 添加图例
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))

    plt.tight_layout()

    # 保存到 BytesIO
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)

    return buf


def generate_yield_breakdown_chart(
    yield_sources: Dict[str, float]
) -> io.BytesIO:
    """生成收益分解饼图

    Args:
        yield_sources: 收益来源字典
            {
                "Trading Fees": 45.5,
                "Lending Interest": 30.2,
                "Liquidity Mining": 15.3,
                "Governance Rewards": 9.0
            }

    Returns:
        BytesIO 对象，包含 PNG 格式的图表
    """
    fig, ax = plt.subplots(figsize=(10, 8))

    # 提取数据
    labels = list(yield_sources.keys())
    sizes = list(yield_sources.values())

    # 颜色方案
    colors = ['#4CAF50', '#2196F3', '#FFC107', '#9C27B0', '#FF5722']

    # 绘制饼图
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        autopct='%1.1f%%',
        startangle=90,
        colors=colors[:len(labels)],
        textprops={'fontsize': 11, 'fontweight': 'bold'},
        explode=[0.05] * len(labels)  # 所有扇形都略微分离
    )

    # 美化百分比文字
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(12)
        autotext.set_fontweight('bold')

    # 设置标题
    ax.set_title('Yield Sources Breakdown', fontsize=16, fontweight='bold', pad=20)

    # 添加图例
    ax.legend(
        wedges,
        [f'{label}: ${size:.2f}%' for label, size in zip(labels, sizes)],
        loc="center left",
        bbox_to_anchor=(1, 0, 0.5, 1),
        fontsize=10
    )

    plt.tight_layout()

    # 保存到 BytesIO
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)

    return buf


def generate_multi_protocol_tvl_comparison(
    protocols_tvl: Dict[str, List[Dict[str, any]]],
    days: int = 30
) -> io.BytesIO:
    """生成多协议 TVL 对比趋势图

    Args:
        protocols_tvl: 多个协议的 TVL 历史数据
            {
                "Aave V3": [{"date": "2025-01-01", "tvl": 1000000}, ...],
                "Uniswap V3": [{"date": "2025-01-01", "tvl": 2000000}, ...]
            }
        days: 显示的天数

    Returns:
        BytesIO 对象，包含 PNG 格式的图表
    """
    fig, ax = plt.subplots(figsize=(14, 7))

    colors = ['#4CAF50', '#2196F3', '#FFC107', '#9C27B0', '#FF5722']

    for idx, (protocol, tvl_history) in enumerate(protocols_tvl.items()):
        dates = [datetime.fromisoformat(item["date"]) for item in tvl_history[-days:]]
        tvls = [item["tvl"] / 1e6 for item in tvl_history[-days:]]

        ax.plot(
            dates,
            tvls,
            linewidth=2,
            color=colors[idx % len(colors)],
            marker='o',
            markersize=3,
            label=protocol
        )

    # 设置标题和标签
    ax.set_title(f'Multi-Protocol TVL Comparison ({days} Days)', fontsize=16, fontweight='bold')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('TVL (Million USD)', fontsize=12)

    # 格式化 Y 轴
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:.0f}M'))

    # 添加网格和图例
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(loc='best', fontsize=10)

    # 旋转 X 轴标签
    plt.xticks(rotation=45, ha='right')

    plt.tight_layout()

    # 保存到 BytesIO
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)

    return buf
