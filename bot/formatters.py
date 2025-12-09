"""
Telegram消息格式化器

将DeFi分析结果格式化为Telegram友好的Markdown消息。
"""
import re
from typing import Dict, Any, List
from datetime import datetime


class TelegramFormatter:
    """Telegram消息格式化器"""

    def __init__(self, max_length: int = 4096):
        """
        初始化格式化器

        Args:
            max_length: Telegram消息最大长度（默认4096字符）
        """
        self.max_length = max_length

    def format_welcome(self) -> str:
        """格式化欢迎消息"""
        return """
🤖 **欢迎使用DeFi投资分析助手**

我可以帮你分析DeFi协议，提供投资建议。

**可用命令：**
/analyze <协议名> - 分析指定协议
/strategy - 获取投资策略推荐
/compare <协议1> <协议2> - 对比两个协议
/help - 显示帮助信息

**自然语言示例：**
• "分析Aave V3的投资机会"
• "用10万USDC投资低风险的借贷协议"
• "对比Uniswap和Curve的流动性池收益"

💡 提示：直接输入您的投资需求即可！
        """.strip()

    def format_help(self) -> str:
        """格式化帮助消息"""
        return """
📚 **使用指南**

**命令列表：**

🔍 `/analyze <协议名>`
   分析指定的DeFi协议
   示例：`/analyze aave-v3`

📊 `/strategy [金额] [风险偏好]`
   获取投资策略推荐
   示例：`/strategy 100000 low`

⚖️ `/compare <协议1> <协议2>`
   对比两个协议的各项指标
   示例：`/compare aave-v3 compound-v3`

❓ `/help`
   显示此帮助信息

**自然语言输入：**
您也可以直接用自然语言描述需求，我会自动理解：

• "分析Aave V3"
• "我想用10万美金投资低风险协议"
• "找一个APY至少8%的稳定币策略"
• "对比Uniswap和Curve在Arbitrum上的收益"

**支持的协议：**
借贷：Aave, Compound, Radiant
DEX：Uniswap, Curve, Balancer
质押：Lido, Rocket Pool
衍生品：GMX, dYdX
...以及更多！

**风险提示：**
⚠️ 本Bot仅提供分析建议，不构成投资建议。
⚠️ 请自行承担投资风险。
⚠️ 我们不托管资金，不进行任何交易。
        """.strip()

    def format_progress(self, step: str, current: int, total: int) -> str:
        """
        格式化进度消息

        Args:
            step: 当前步骤描述
            current: 当前进度
            total: 总步骤数
        """
        progress_bar = "▓" * current + "░" * (total - current)
        percentage = int((current / total) * 100)

        return f"""
🔄 **分析中... ({percentage}%)**

{progress_bar}

当前步骤：{step}
        """.strip()

    def format_analysis_result(self, result: Dict[str, Any]) -> List[str]:
        """
        格式化完整分析结果

        Args:
            result: 分析结果字典

        Returns:
            格式化的消息列表（可能需要分多条发送）
        """
        messages = []

        # 1. 摘要消息
        summary = self._format_summary(result)
        messages.append(summary)

        # 2. 市场分析
        if "market_report" in result and result["market_report"]:
            market = self._format_market_report(result["market_report"])
            messages.append(market)

        # 3. 基本面分析
        if "fundamentals_report" in result and result["fundamentals_report"]:
            fundamentals = self._format_fundamentals_report(result["fundamentals_report"])
            messages.append(fundamentals)

        # 4. 收益分析
        if "yield_report" in result and result["yield_report"]:
            yield_report = self._format_yield_report(result["yield_report"])
            messages.append(yield_report)

        # 5. 风险评估
        if "risk_report" in result and result["risk_report"]:
            risk = self._format_risk_report(result["risk_report"])
            messages.append(risk)

        # 6. 最终建议
        if "trader_plan" in result and result["trader_plan"]:
            plan = self._format_trader_plan(result["trader_plan"])
            messages.append(plan)

        # 确保每条消息不超过长度限制
        return [self._truncate_message(msg) for msg in messages]

    def _format_summary(self, result: Dict[str, Any]) -> str:
        """格式化摘要"""
        protocol = result.get("protocol_of_interest", "Unknown")
        date = result.get("trade_date", datetime.now().strftime("%Y-%m-%d"))

        return f"""
📊 **{protocol} 分析报告**

📅 分析日期：{date}
⏱️ 生成时间：{datetime.now().strftime("%H:%M:%S")}

正在为您生成详细报告...
        """.strip()

    def _format_market_report(self, report: str) -> str:
        """格式化市场分析报告"""
        # 提取关键信息
        truncated = self._extract_key_points(report, max_points=5)

        return f"""
📈 **市场分析**

{truncated}

详细内容请查看完整报告。
        """.strip()

    def _format_fundamentals_report(self, report: str) -> str:
        """格式化基本面分析报告"""
        truncated = self._extract_key_points(report, max_points=5)

        return f"""
🏛️ **基本面分析**

{truncated}

详细内容请查看完整报告。
        """.strip()

    def _format_yield_report(self, report: str) -> str:
        """格式化收益分析报告"""
        truncated = self._extract_key_points(report, max_points=5)

        return f"""
💰 **收益分析**

{truncated}

详细内容请查看完整报告。
        """.strip()

    def _format_risk_report(self, report: str) -> str:
        """格式化风险评估报告"""
        truncated = self._extract_key_points(report, max_points=5)

        return f"""
⚠️ **风险评估**

{truncated}

详细内容请查看完整报告。
        """.strip()

    def _format_trader_plan(self, plan: str) -> str:
        """格式化交易计划"""
        # 提取最终决策
        decision = self._extract_decision(plan)

        return f"""
🎯 **最终投资建议**

{decision}

完整分析请查看上述报告。

⚠️ **风险提示**
本分析仅供参考，不构成投资建议。
请自行评估风险，理性投资。

ℹ️ **数据说明**
本分析综合多个数据源（DeFi Llama、The Graph、CoinGecko等）。
如遇数据源临时不可用，系统会自动使用备选方案，确保分析质量。
        """.strip()

    def _escape_markdown_content(self, text: str) -> str:
        """转义用户内容中的 Telegram Markdown 特殊字符（保留我们自己的格式）"""
        # 只转义核心 Markdown 字符，避免破坏格式
        text = text.replace('_', '\\_')  # 下划线
        text = text.replace('*', '\\*')  # 星号
        text = text.replace('[', '\\[')  # 方括号
        text = text.replace('`', '\\`')  # 反引号
        return text

    def _extract_key_points(self, text: str, max_points: int = 5) -> str:
        """从长文本中提取关键点"""
        # 按段落分割
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        # 取前N个段落
        key_paragraphs = paragraphs[:max_points]

        # 如果段落太长，截断
        result = []
        for p in key_paragraphs:
            if len(p) > 200:
                p = p[:197] + "..."
            # 转义 Markdown 特殊字符
            p_escaped = self._escape_markdown_content(p)
            result.append(f"• {p_escaped}")

        return "\n\n".join(result)

    def _extract_decision(self, plan: str) -> str:
        """提取最终决策"""
        # 查找INVEST/HOLD/AVOID等关键词
        lines = plan.split("\n")
        decision_lines = []

        for line in lines:
            if any(keyword in line.upper() for keyword in ["INVEST", "HOLD", "AVOID", "SELL", "BUY"]):
                decision_lines.append(line.strip())

        if decision_lines:
            result = "\n".join(decision_lines[:3])  # 取前3行
        else:
            # 如果没找到，返回前几行
            result = "\n".join(lines[:5])

        # 转义 Markdown 特殊字符
        return self._escape_markdown_content(result)

    def _truncate_message(self, message: str) -> str:
        """截断过长的消息"""
        if len(message) <= self.max_length:
            return message

        # 截断并添加省略标记
        truncated = message[: self.max_length - 100]
        last_newline = truncated.rfind("\n")
        if last_newline > 0:
            truncated = truncated[:last_newline]

        return truncated + "\n\n... (消息过长，已截断)"

    def format_error(self, error_message: str) -> str:
        """格式化错误消息"""
        return f"""
❌ **出错了**

{error_message}

请稍后重试或联系管理员。
        """.strip()

    def format_security_rejection(self, reason: str, suggestions: List[str] = None) -> str:
        """格式化安全拒绝消息"""
        msg = f"""
🛡️ **输入安全检查**

您的输入包含可疑内容：
{reason}

💡 **建议：**
        """.strip()

        if suggestions:
            for suggestion in suggestions:
                msg += f"\n• {suggestion}"
        else:
            msg += "\n• 请用自然语言描述您的投资需求"
            msg += "\n• 避免使用特殊字符或命令"
            msg += "\n• 示例：分析Aave V3的投资机会"

        return msg


if __name__ == "__main__":
    # 测试格式化器
    formatter = TelegramFormatter()

    print("=== 欢迎消息 ===")
    print(formatter.format_welcome())
    print("\n" + "="*80 + "\n")

    print("=== 帮助消息 ===")
    print(formatter.format_help())
    print("\n" + "="*80 + "\n")

    print("=== 进度消息 ===")
    print(formatter.format_progress("DeFi Market Analyst正在工作...", 3, 8))
    print("\n" + "="*80 + "\n")

    print("=== 错误消息 ===")
    print(formatter.format_error("分析超时，请稍后重试"))
    print("\n" + "="*80 + "\n")

    print("=== 安全拒绝消息 ===")
    print(formatter.format_security_rejection(
        "检测到可疑的系统命令",
        ["使用DeFi相关术语", "描述具体的投资需求"]
    ))
