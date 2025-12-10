"""
Agent 输出验证器

检测危险指令、异常金额、可疑地址，并在输出末尾追加安全警告。
"""
import re
from typing import Any, Dict, List, Optional, TypedDict, Literal


class ValidationContext(TypedDict, total=False):
    """验证上下文"""

    agent_name: str
    protocol_name: str
    investment_amount: Optional[float]


class ValidationIssue(TypedDict):
    """验证问题记录"""

    severity: Literal["critical", "warning", "info"]
    category: str
    matched_pattern: str
    location: str
    original_text: str


class ValidationResult(TypedDict):
    """验证结果"""

    is_safe: bool
    issues: List[ValidationIssue]
    patched_text: str
    original_text: str


class OutputValidator:
    """Agent 输出验证器"""

    DANGEROUS_PATTERNS: Dict[str, str] = {
        "unlimited_approval": r"\b(approve|allow)\s+(unlimited|max(?:imum)?|all)\b|setApprovalForAll",
        "transfer_all": r"(?:\b(transfer|send|move)\s+(all|everything|entire|full)(?!\w)|\bdrain\b|\bempty\s+wallet\b|transfer\s*all)",
        "contract_attack": r"\b(selfdestruct|delegatecall|suicide)\b|\brug\s+pull\b",
        "private_key": r"\b(private\s+key|seed\s+phrase|mnemonic|recovery\s+phrase)\b",
        "suspicious_contract": r"\b(honeypot|backdoor|exploit|trojan)\b",
        "flash_loan_attack": r"\bflash\s*loan\s*(attack|exploit|arbitrage)\b",
        "phishing_signature": r"\bsign\b.*\b(raw|arbitrary|blank)\s+(transaction|message)\b",
        "slippage_infinite": r"\b(slippage|price\s*impact)\b.{0,20}?(100%|max|unlimited)",
        "bridge_unknown": r"\bbridge\s+(all|entire)\s+(funds|assets)\s+to\s+(unknown|custom|unverified)\s+chain\b",
        "impersonation_payment": r"\bsend\s+(funds|eth|usdc|usdt)\s+to\s+(ceo|admin|support|helpdesk)\b",
        "disable_security": r"\b(disable|bypass|turn\s*off)\s+(multisig|guardian|security|safeguard|2fa|two-factor)\b",
        "manual_bytecode": r"\bexecute\s+(raw|custom)\s+(bytecode|call)\b",
        "allowlist_override": r"\b(whitelist|allowlist)\s+(any|all)\s+(address|contract)s?\b",
        "airdrop_scam": r"\bclaim\s+(airdrop|reward).*\bapprove\b",
        "liquidation_griefing": r"\bforce\s+liquidat(e|ion)\b|\bdrain\s+liquidity\b",
        "pause_bypass": r"\b(unpause|pause)\s+guardians?\b|disable\s+pause\s+checks",
    }

    SUSPICIOUS_AMOUNT_THRESHOLDS = {
        "high": 1_000_000,  # >$1M 标记为 critical
        "medium": 100_000,  # >$100K 标记为 warning
    }

    _AMOUNT_REGEX = re.compile(
        r"(?P<prefix>\$)?(?P<value>\d+(?:,\d{3})*(?:\.\d+)?)"
        r"(?:\s*(?P<unit>k|m|b|bn|million|billion|thousand|千|万|百万|千万|亿))?"
        r"(?:\s*(?P<currency>usd|usdc|usdt|dai))?",
        re.IGNORECASE,
    )

    _ADDRESS_REGEX = re.compile(r"0x[a-fA-F0-9]{40}")

    def __init__(self) -> None:
        self._compiled_dangerous = {
            name: re.compile(pattern, re.IGNORECASE)
            for name, pattern in self.DANGEROUS_PATTERNS.items()
        }

    def validate(self, text: Optional[str], context: Optional[ValidationContext] = None) -> ValidationResult:
        """验证 Agent 输出"""
        normalized_text = text or ""
        normalized_context = self._normalize_context(context)

        issues: List[ValidationIssue] = []
        issues.extend(self._check_dangerous_instructions(normalized_text))
        issues.extend(self._check_suspicious_amounts(normalized_text, normalized_context))
        issues.extend(self._check_addresses(normalized_text))

        is_safe = len(issues) == 0
        patched_text = normalized_text if is_safe else self._patch_output(normalized_text, issues)

        return {
            "is_safe": is_safe,
            "issues": issues,
            "patched_text": patched_text,
            "original_text": normalized_text,
        }

    def _normalize_context(self, context: Optional[ValidationContext]) -> ValidationContext:
        base: ValidationContext = {
            "agent_name": "",
            "protocol_name": "",
            "investment_amount": None,
        }
        if context:
            base.update(context)
        return base

    def _check_dangerous_instructions(self, text: str) -> List[ValidationIssue]:
        """检测危险操作指令"""
        issues: List[ValidationIssue] = []
        for name, pattern in self._compiled_dangerous.items():
            match = pattern.search(text)
            if match:
                issues.append(
                    {
                        "severity": "critical",
                        "category": "dangerous_instruction",
                        "matched_pattern": name,
                        "location": f"index {match.start()}",
                        "original_text": match.group(0),
                    }
                )
        return issues

    def _check_suspicious_amounts(self, text: str, context: ValidationContext) -> List[ValidationIssue]:
        """检测异常金额"""
        issues: List[ValidationIssue] = []
        investment_amount = context.get("investment_amount")

        for match in self._AMOUNT_REGEX.finditer(text):
            amount = self._convert_amount(match.group("value"), match.group("unit"))
            raw_fragment = match.group(0)

            severity = self._determine_amount_severity(amount, investment_amount)
            if not severity:
                continue

            issues.append(
                {
                    "severity": severity,
                    "category": "suspicious_amount",
                    "matched_pattern": raw_fragment.strip(),
                    "location": f"index {match.start()}",
                    "original_text": raw_fragment.strip(),
                }
            )
        return issues

    def _determine_amount_severity(
        self, amount: float, expected_amount: Optional[float]
    ) -> Optional[Literal["critical", "warning"]]:
        severity: Optional[Literal["critical", "warning"]] = None

        if amount > self.SUSPICIOUS_AMOUNT_THRESHOLDS["high"]:
            severity = "critical"
        elif amount > self.SUSPICIOUS_AMOUNT_THRESHOLDS["medium"]:
            severity = "warning"

        if expected_amount and expected_amount > 0:
            ratio = amount / expected_amount
            if ratio >= 10:
                severity = "critical"
            elif ratio >= 2 and severity is None:
                severity = "warning"

        return severity

    def _check_addresses(self, text: str) -> List[ValidationIssue]:
        """检测可疑地址"""
        issues: List[ValidationIssue] = []

        for match in self._ADDRESS_REGEX.finditer(text):
            address = match.group(0)
            if self._is_suspicious_address(address, text, match.start()):
                issues.append(
                    {
                        "severity": "warning",
                        "category": "suspicious_address",
                        "matched_pattern": "suspicious_address",
                        "location": f"index {match.start()}",
                        "original_text": address,
                    }
                )
        return issues

    def _is_suspicious_address(self, address: str, text: str, position: int) -> bool:
        lower_address = address.lower()
        if lower_address in (
            "0x0000000000000000000000000000000000000000",
            "0x000000000000000000000000000000000000dead",
        ):
            return True

        unique_chars = set(lower_address[2:])
        if len(unique_chars) <= 2:
            return True

        window_start = max(position - 24, 0)
        window_end = min(position + 24, len(text))
        window = text[window_start:window_end].lower()
        return bool(re.search(r"(unknown|suspicious|random|unverified|blacklist)", window))

    def _convert_amount(self, value_text: str, unit: Optional[str]) -> float:
        clean_value = float(value_text.replace(",", ""))
        if not unit:
            return clean_value

        unit_lower = unit.lower()
        if unit_lower in {"k", "thousand", "千"}:
            return clean_value * 1_000
        if unit_lower in {"m", "million", "百万", "千万"}:
            return clean_value * 1_000_000
        if unit_lower in {"b", "bn", "billion", "亿"}:
            return clean_value * 1_000_000_000
        if unit_lower == "万":
            return clean_value * 10_000
        return clean_value

    def _patch_output(self, text: str, issues: List[ValidationIssue]) -> str:
        """在输出末尾追加警告段落"""
        lines = [text.rstrip(), ""]
        lines.append("---")
        lines.append("⚠️ **安全提示** (由 DeFi Agent 安全层检测)")
        lines.append("")

        for issue in issues:
            severity = issue["severity"].upper()
            description = self._describe_issue(issue)
            lines.append(f"- [{severity}] {description}")

        lines.append("")
        lines.append("请仔细审核以上建议，必要时咨询专业人士。")
        return "\n".join(lines)

    def _describe_issue(self, issue: ValidationIssue) -> str:
        category = issue["category"]
        if category == "dangerous_instruction":
            return f"检测到危险指令: \"{issue['original_text']}\" (模式: {issue['matched_pattern']})"
        if category == "suspicious_amount":
            return f"金额异常: {issue['original_text']} 可能超出安全阈值"
        if category == "suspicious_address":
            return f"检测到可疑地址: {issue['original_text']}"
        return f"检测到异常: {issue['original_text']}"
