# Messari Schema 重构 - Phase 1 基础设施开发计划

## 概述

Phase 1 为 Messari Schema 重构项目的基础设施阶段，核心目标是创建 Messari 客户端、实现多源回退机制、集成配置系统，为后续 Phase 提供稳定的数据层基础。

**时间预估**: 5-6 人天
**代码改动**: ~700 行（新增 500 行，修改 200 行）
**影响范围**: 数据获取层（Layer 1）和数据接口层（Layer 2）
**核心逻辑影响**: 0%（Agent 工作流、提示词、安全模块完全不变）

---

## 功能需求

### 核心功能需求

1. **Messari 客户端实现**
   - REST API 客户端封装（基于 Messari Subgraph Gateway）
   - 支持标准化 Schema 查询（Lending、DEX-AMM 协议类型）
   - 内置缓存机制（1 小时 TTL）
   - 错误处理和速率限制（60 requests/分钟）
   - 部署 ID 自动加载（从本地 `deployment.json` 读取）

2. **多源回退机制**
   - 数据源优先级：Messari → DeFi Llama → The Graph → RPC
   - 错误分类回退（网络超时/429 限流/404 缺数据/Schema 不匹配）
   - 统一数据格式转换（Adapter 模式）
   - 回退日志和监控

3. **配置系统集成**
   - 在 `default_config.py` 中新增 Messari 配置节
   - 支持环境变量覆盖（`MESSARI_API_KEY`）
   - 数据源优先级配置（可运行时调整）
   - Deployment IDs 自动导入

### 非功能需求

1. **性能要求**
   - 单次 API 调用响应时间 <3 秒（无缓存）
   - 缓存命中响应时间 <0.5 秒
   - 回退切换延迟 <2 秒

2. **可靠性要求**
   - 单数据源失败不影响整体可用性（通过回退机制）
   - 99.5% 可用性（多源保障）
   - 优雅降级（数据源全部失败时返回友好错误信息）

3. **可维护性要求**
   - 代码风格遵循现有 `the_graph.py` 和 `defillama.py` 模式
   - 完整的类型注解（使用 `typing` 模块）
   - 详细的 docstring（Google 风格）
   - 清晰的错误日志（使用 `logging` 模块）

---

## 技术要求

### 代码质量标准

1. **架构模式**
   - 客户端模式：共享轻量 HTTP/缓存基类，业务逻辑独立
   - 责任链模式：多源回退错误分类处理
   - Adapter 模式：统一 Schema 映射接口

2. **编码规范**
   - 遵循 PEP 8 规范
   - 函数单一职责（每个函数 ≤50 行）
   - 缩进深度 ≤3 层
   - 使用类型注解（Python 3.9+ 兼容）

3. **错误处理**
   - 所有外部 API 调用必须有 `try-except` 块
   - 错误信息包含：错误类型、协议名、数据源、建议措施
   - 使用自定义异常类（如 `MessariAPIError`）

4. **日志规范**
   - DEBUG: 缓存命中/未命中、回退触发
   - INFO: API 调用成功、数据源切换
   - WARNING: 单数据源失败、数据格式异常
   - ERROR: 所有数据源失败、配置错误

### 测试覆盖率要求

- **单元测试覆盖率**: ≥90%（使用 pytest-cov）
- **关键路径覆盖率**: 100%（主 API 调用、回退逻辑、错误处理）
- **Mock 测试优先**: 默认 Mock 所有外部 API（避免真实 API 配额消耗）
- **集成测试可选**: 使用 `-m integration` 标记，每个数据源 ≤1 次真实 API 调用

### API 配额控制

- **开发阶段**: 100% Mock 测试，0 次真实 API 调用
- **集成测试**: 每个数据源 ≤1 次健康探测（可选，需手动启用）
- **CI/CD**: 仅运行 Mock 测试（不触发集成测试）

---

## 任务分解

### Task 1: 实现 Messari 客户端

**任务 ID**: `messari-client-1`

**描述**: 创建 Messari Subgraph Gateway API 客户端，支持标准化 Schema 查询和缓存机制。

**文件范围**:
- 新增: `/Users/wangkunyu/develop/TradingAgents/defiagents/dataflows/defi/messari.py` (~350 行)
- 新增: `/Users/wangkunyu/develop/TradingAgents/defiagents/dataflows/defi/messari_schemas.py` (~150 行，Schema 定义和字段映射）

**依赖**: 无

**具体实现内容**:

1. **`MessariClient` 类**（参考 `TheGraphClient` 模式）:
   ```python
   class MessariClient:
       def __init__(self, api_key: Optional[str] = None, cache_ttl: int = 3600)
       def get_protocol_tvl(self, protocol_slug: str, chain: str = "ethereum") -> float
       def get_lending_markets(self, protocol_slug: str, chain: str = "ethereum") -> List[Dict]
       def get_dex_pools(self, protocol_slug: str, chain: str = "ethereum") -> List[Dict]
       def get_protocol_metrics(self, protocol_slug: str, chain: str = "ethereum") -> Dict
       def _query_api(self, endpoint: str, params: Dict) -> Dict
       def _get_deployment_id(self, protocol_slug: str, chain: str) -> str
       def _get_cached(self, key: str) -> Optional[Any]
       def _set_cache(self, key: str, data: Any)
   ```

2. **部署 ID 自动加载**:
   - 从 `subgraph/deployment/deployment.json` 读取所有协议的 deployment IDs
   - 缓存到内存字典（协议 + 链 → deployment ID）
   - 支持多链查询（ethereum, arbitrum, optimism, polygon, base）

3. **错误处理**:
   - 自定义异常类：`MessariAPIError`, `MessariRateLimitError`, `MessariNotFoundError`
   - 区分错误类型：网络错误（可重试）、429 限流（需回退）、404 缺数据（需回退）

4. **缓存机制**:
   - 内存缓存（`Dict[str, Tuple[Any, float]]`）
   - TTL 默认 1 小时（协议 TVL 更新慢）
   - 缓存键格式：`messari:{protocol}:{chain}:{method}`

**测试命令**:
```bash
pytest tests/dataflows/test_messari_client.py -v --cov=defiagents/dataflows/defi/messari --cov-report=term
```

**测试焦点**:
- 正常场景：成功获取 TVL、借贷市场、DEX 池数据
- 缓存命中：第二次调用命中缓存，响应时间 <0.5 秒
- 404 错误：协议不存在或链不支持，抛出 `MessariNotFoundError`
- 429 限流：API 超限，抛出 `MessariRateLimitError`
- 网络超时：超时 10 秒，抛出 `MessariAPIError`
- 部署 ID 加载：正确从 `deployment.json` 加载 176+ 协议 IDs
- 数据格式：返回数据符合 Messari Schema 标准

**验收标准**:
- [ ] `MessariClient` 类所有方法实现完成
- [ ] 单元测试覆盖率 ≥90%
- [ ] 所有测试使用 Mock（0 次真实 API 调用）
- [ ] 支持至少 5 条链（ethereum, arbitrum, optimism, polygon, base）
- [ ] 支持至少 10 个协议（aave-v3, compound-v3, uniswap-v3, curve, lido 等）
- [ ] 缓存机制正常工作（命中率测试通过）
- [ ] 错误处理完整（所有异常场景有测试覆盖）

---

### Task 2: 配置系统集成

**任务 ID**: `config-update-1`

**描述**: 在 `default_config.py` 中添加 Messari 配置节，支持环境变量覆盖和数据源优先级配置。

**文件范围**:
- 修改: `/Users/wangkunyu/develop/TradingAgents/defiagents/default_config.py` (~30 行新增)
- 修改: `/Users/wangkunyu/develop/TradingAgents/.env.example` (~10 行新增)

**依赖**: `messari-client-1`（需要 `MessariClient` 类定义）

**具体实现内容**:

1. **在 `default_config.py` 中新增配置节**:
   ```python
   # ========== Messari Configuration ==========
   "messari": {
       "api_key": os.getenv("MESSARI_API_KEY", ""),
       "api_url": "https://gateway.thegraph.com/api",
       "deployment_json_path": os.path.join(
           os.path.dirname(__file__),
           "../subgraph/deployment/deployment.json"
       ),
       "cache_ttl": 3600,  # 1 hour
       "rate_limit_per_minute": 60,
       "timeout_seconds": 10,
   },

   # ========== Data Source Priority Configuration ==========
   "data_source_priority": {
       "protocol_tvl": ["messari", "defillama", "the_graph", "onchain_rpc"],
       "lending_markets": ["messari", "the_graph", "defillama"],
       "dex_pools": ["messari", "the_graph"],
       "token_prices": ["coingecko", "defillama"],
   },
   ```

2. **更新 `.env.example`**:
   ```bash
   # ========== Messari Configuration ==========
   # Messari Subgraph Gateway API Key
   # 获取方式: https://thegraph.com/studio/apikeys/
   MESSARI_API_KEY=your_api_key_here

   # 可选：自定义 Deployment JSON 路径
   # MESSARI_DEPLOYMENT_JSON_PATH=/path/to/deployment.json
   ```

3. **配置验证函数**:
   ```python
   def validate_messari_config(config: Dict) -> None:
       """验证 Messari 配置完整性"""
       assert "messari" in config, "Missing 'messari' config section"
       assert config["messari"]["deployment_json_path"], "deployment_json_path not set"
       # 检查 deployment.json 文件是否存在
       if not os.path.exists(config["messari"]["deployment_json_path"]):
           logger.warning(f"Deployment JSON not found: {config['messari']['deployment_json_path']}")
   ```

**测试命令**:
```bash
pytest tests/test_config.py::test_messari_config -v
```

**测试焦点**:
- 配置节存在：`DEFAULT_CONFIG["messari"]` 不为空
- 环境变量覆盖：`MESSARI_API_KEY` 正确读取
- 路径正确：`deployment_json_path` 指向正确的 JSON 文件
- 数据源优先级配置正确：每个方法都有明确的优先级列表
- 配置验证函数正常工作

**验收标准**:
- [ ] `messari` 配置节添加完成
- [ ] `data_source_priority` 配置节添加完成
- [ ] `.env.example` 更新完成
- [ ] 配置验证测试通过
- [ ] 环境变量覆盖测试通过
- [ ] 文档字符串更新（说明每个配置项的用途）

---

### Task 3: 多源回退机制实现

**任务 ID**: `fallback-chain-1`

**描述**: 实现责任链模式的多源回退机制，支持错误分类和自动切换数据源。

**文件范围**:
- 修改: `/Users/wangkunyu/develop/TradingAgents/defiagents/dataflows/interface.py` (~200 行新增)
- 新增: `/Users/wangkunyu/develop/TradingAgents/defiagents/dataflows/defi/adapters.py` (~150 行，数据格式转换）

**依赖**: `messari-client-1`, `config-update-1`

**具体实现内容**:

1. **在 `interface.py` 中新增回退函数**:
   ```python
   from enum import Enum
   from typing import List, Callable, Dict, Any

   class DataSourceType(Enum):
       MESSARI = "messari"
       DEFILLAMA = "defillama"
       THE_GRAPH = "the_graph"
       ONCHAIN_RPC = "onchain_rpc"

   class FallbackError(Exception):
       """回退错误基类"""
       pass

   class AllSourcesFailedError(FallbackError):
       """所有数据源失败"""
       pass

   def get_data_with_fallback(
       protocol: str,
       method: str,
       sources: List[DataSourceType],
       **kwargs
   ) -> Any:
       """
       多源回退获取数据

       Args:
           protocol: 协议 slug（如 "aave-v3"）
           method: 方法名（如 "get_protocol_tvl"）
           sources: 数据源优先级列表
           **kwargs: 传递给具体方法的参数

       Returns:
           数据结果（格式已标准化）

       Raises:
           AllSourcesFailedError: 所有数据源失败
       """
       errors = []

       for source in sources:
           try:
               logger.info(f"Attempting {method} from {source.value} for {protocol}")

               # 调用具体数据源
               data = _call_source_method(source, protocol, method, **kwargs)

               # 格式标准化
               normalized_data = _normalize_data(data, source, method)

               logger.info(f"✓ Successfully fetched from {source.value}")
               return normalized_data

           except MessariNotFoundError as e:
               # 404 错误：立即回退到下一个源
               logger.warning(f"✗ {source.value} - protocol not found: {e}")
               errors.append((source, "not_found", str(e)))
               continue

           except MessariRateLimitError as e:
               # 429 限流：立即回退
               logger.warning(f"✗ {source.value} - rate limit: {e}")
               errors.append((source, "rate_limit", str(e)))
               continue

           except (requests.Timeout, requests.ConnectionError) as e:
               # 网络错误：重试一次后回退
               logger.warning(f"✗ {source.value} - network error (retrying once): {e}")
               try:
                   time.sleep(1)
                   data = _call_source_method(source, protocol, method, **kwargs)
                   normalized_data = _normalize_data(data, source, method)
                   logger.info(f"✓ Retry succeeded for {source.value}")
                   return normalized_data
               except Exception as retry_error:
                   logger.warning(f"✗ Retry failed: {retry_error}")
                   errors.append((source, "network_error", str(e)))
                   continue

           except Exception as e:
               # 其他错误：记录后回退
               logger.error(f"✗ {source.value} - unexpected error: {e}")
               errors.append((source, "unknown_error", str(e)))
               continue

       # 所有数据源失败
       error_summary = "\n".join([
           f"  - {source.value}: [{error_type}] {msg}"
           for source, error_type, msg in errors
       ])
       raise AllSourcesFailedError(
           f"All data sources failed for {protocol}.{method}:\n{error_summary}"
       )

   def _call_source_method(
       source: DataSourceType,
       protocol: str,
       method: str,
       **kwargs
   ) -> Any:
       """调用具体数据源方法"""
       # 根据 source 调用对应客户端方法
       if source == DataSourceType.MESSARI:
           from .defi.messari import MessariClient
           client = MessariClient()
           return getattr(client, method)(protocol, **kwargs)

       elif source == DataSourceType.DEFILLAMA:
           from .defi.defillama import DefiLlamaAPI
           client = DefiLlamaAPI()
           return getattr(client, method)(protocol, **kwargs)

       # ... 其他数据源
   ```

2. **在 `adapters.py` 中新增数据格式转换**:
   ```python
   from typing import Dict, Any, List
   from .interface import DataSourceType

   class DataAdapter:
       """数据格式标准化 Adapter"""

       @staticmethod
       def normalize_tvl(data: Any, source: DataSourceType) -> float:
           """标准化 TVL 数据"""
           if source == DataSourceType.MESSARI:
               # Messari Schema: {"protocol": {"totalValueLockedUSD": 123.45}}
               return float(data.get("protocol", {}).get("totalValueLockedUSD", 0))

           elif source == DataSourceType.DEFILLAMA:
               # DeFi Llama: float/list/dict（已有 _normalize_tvl 函数）
               from .defi.defillama import _normalize_tvl
               return _normalize_tvl(data)

           elif source == DataSourceType.THE_GRAPH:
               # The Graph: {"financialsDailySnapshots": [{"totalValueLockedUSD": "123.45"}]}
               snapshots = data.get("financialsDailySnapshots", [])
               if snapshots:
                   return float(snapshots[-1].get("totalValueLockedUSD", 0))
               return 0.0

           return 0.0

       @staticmethod
       def normalize_lending_markets(data: Any, source: DataSourceType) -> List[Dict]:
           """标准化借贷市场数据"""
           if source == DataSourceType.MESSARI:
               # Messari Schema
               markets = data.get("markets", [])
               return [
                   {
                       "asset": m.get("inputToken", {}).get("symbol", ""),
                       "supply_rate": float(m.get("rates", [{}])[0].get("rate", 0)),
                       "borrow_rate": float(m.get("rates", [{}])[1].get("rate", 0)),
                       "liquidity": float(m.get("totalValueLockedUSD", 0)),
                   }
                   for m in markets
               ]

           elif source == DataSourceType.THE_GRAPH:
               # The Graph Schema（Aave 专用）
               # ... 类似转换逻辑
               pass

           return []
   ```

**测试命令**:
```bash
pytest tests/dataflows/test_fallback_mechanism.py -v --cov=defiagents/dataflows/interface --cov-report=term
```

**测试焦点**:
- **场景 1: 主数据源成功** - Messari 正常返回，无回退
- **场景 2: Messari 404 → DeFi Llama 成功** - 协议在 Messari 不存在，回退到 DeFi Llama
- **场景 3: Messari 429 → The Graph 成功** - Messari 限流，回退到 The Graph
- **场景 4: 网络超时重试成功** - 第一次超时，重试后成功
- **场景 5: 所有数据源失败** - 抛出 `AllSourcesFailedError`，错误信息包含所有失败原因
- **场景 6: 数据格式转换** - 不同数据源返回的数据正确转换为统一格式
- **场景 7: 优先级配置** - 使用自定义优先级列表（如跳过 Messari 直接用 DeFi Llama）

**验收标准**:
- [ ] `get_data_with_fallback` 函数实现完成
- [ ] 支持至少 4 种数据源回退
- [ ] 错误分类正确（404/429/timeout/unknown）
- [ ] 网络错误重试机制正常
- [ ] 数据格式转换 Adapter 实现完成
- [ ] 单元测试覆盖率 ≥90%
- [ ] 所有测试使用 Mock（0 次真实 API 调用）
- [ ] 回退日志清晰（INFO/WARNING/ERROR 级别正确）

---

### Task 4: 单元测试套件

**任务 ID**: `tests-suite-1`

**描述**: 编写完整的单元测试套件，覆盖 Messari 客户端、配置系统、回退机制的所有场景。

**文件范围**:
- 新增: `/Users/wangkunyu/develop/TradingAgents/tests/dataflows/test_messari_client.py` (~300 行)
- 新增: `/Users/wangkunyu/develop/TradingAgents/tests/dataflows/test_fallback_mechanism.py` (~250 行)
- 新增: `/Users/wangkunyu/develop/TradingAgents/tests/dataflows/test_messari_adapters.py` (~150 行)
- 新增: `/Users/wangkunyu/develop/TradingAgents/tests/fixtures/messari_responses.py` (~200 行，Mock 数据）

**依赖**: `messari-client-1`, `config-update-1`, `fallback-chain-1`

**具体实现内容**:

1. **Mock 数据 Fixtures** (`messari_responses.py`):
   ```python
   """Messari API Mock 响应数据"""

   # 成功响应
   MOCK_PROTOCOL_TVL_SUCCESS = {
       "protocol": {
           "id": "aave-v3-ethereum",
           "name": "Aave V3",
           "totalValueLockedUSD": 5234567890.12,
           "cumulativeProtocolSideRevenueUSD": 123456789.0,
       }
   }

   # 借贷市场数据
   MOCK_LENDING_MARKETS_SUCCESS = {
       "markets": [
           {
               "id": "aave-v3-usdc",
               "inputToken": {"symbol": "USDC", "decimals": 6},
               "totalValueLockedUSD": 1234567890.0,
               "rates": [
                   {"side": "LENDER", "rate": 0.0345},
                   {"side": "BORROWER", "rate": 0.0567},
               ]
           },
           # ... 更多市场
       ]
   }

   # 404 错误响应
   MOCK_404_ERROR = {
       "errors": [
           {"message": "Subgraph not found"}
       ]
   }

   # 429 限流响应
   MOCK_429_ERROR = {
       "errors": [
           {"message": "Rate limit exceeded"}
       ]
   }
   ```

2. **Messari 客户端测试** (`test_messari_client.py`):
   ```python
   import pytest
   from unittest.mock import patch, MagicMock
   from defiagents.dataflows.defi.messari import MessariClient, MessariAPIError
   from tests.fixtures.messari_responses import *

   @pytest.fixture
   def messari_client():
       return MessariClient(api_key="test_key", cache_ttl=60)

   class TestMessariClient:
       @patch("requests.get")
       def test_get_protocol_tvl_success(self, mock_get, messari_client):
           """测试成功获取协议 TVL"""
           mock_get.return_value.json.return_value = MOCK_PROTOCOL_TVL_SUCCESS
           mock_get.return_value.status_code = 200

           tvl = messari_client.get_protocol_tvl("aave-v3", "ethereum")

           assert tvl == 5234567890.12
           mock_get.assert_called_once()

       @patch("requests.get")
       def test_cache_hit(self, mock_get, messari_client):
           """测试缓存命中"""
           mock_get.return_value.json.return_value = MOCK_PROTOCOL_TVL_SUCCESS
           mock_get.return_value.status_code = 200

           # 第一次调用
           tvl1 = messari_client.get_protocol_tvl("aave-v3", "ethereum")
           # 第二次调用（应命中缓存）
           tvl2 = messari_client.get_protocol_tvl("aave-v3", "ethereum")

           assert tvl1 == tvl2
           mock_get.assert_called_once()  # 只调用一次 API

       @patch("requests.get")
       def test_404_error(self, mock_get, messari_client):
           """测试 404 协议不存在"""
           mock_get.return_value.json.return_value = MOCK_404_ERROR
           mock_get.return_value.status_code = 404

           with pytest.raises(MessariNotFoundError):
               messari_client.get_protocol_tvl("invalid-protocol", "ethereum")

       @patch("requests.get")
       def test_429_rate_limit(self, mock_get, messari_client):
           """测试 429 限流错误"""
           mock_get.return_value.json.return_value = MOCK_429_ERROR
           mock_get.return_value.status_code = 429

           with pytest.raises(MessariRateLimitError):
               messari_client.get_protocol_tvl("aave-v3", "ethereum")

       @patch("requests.get")
       def test_timeout_error(self, mock_get, messari_client):
           """测试网络超时"""
           mock_get.side_effect = requests.Timeout("Connection timeout")

           with pytest.raises(MessariAPIError):
               messari_client.get_protocol_tvl("aave-v3", "ethereum")

       def test_deployment_id_loading(self, messari_client):
           """测试部署 ID 加载"""
           deployment_id = messari_client._get_deployment_id("aave-v3", "ethereum")

           assert deployment_id is not None
           assert len(deployment_id) > 0

       # ... 更多测试（lending markets, dex pools, metrics）
   ```

3. **回退机制测试** (`test_fallback_mechanism.py`):
   ```python
   import pytest
   from unittest.mock import patch, MagicMock
   from defiagents.dataflows.interface import (
       get_data_with_fallback,
       DataSourceType,
       AllSourcesFailedError
   )

   class TestFallbackMechanism:
       @patch("defiagents.dataflows.defi.messari.MessariClient.get_protocol_tvl")
       def test_primary_source_success(self, mock_messari):
           """测试主数据源成功，无回退"""
           mock_messari.return_value = 1234567890.0

           sources = [DataSourceType.MESSARI, DataSourceType.DEFILLAMA]
           result = get_data_with_fallback(
               "aave-v3",
               "get_protocol_tvl",
               sources
           )

           assert result == 1234567890.0
           mock_messari.assert_called_once()

       @patch("defiagents.dataflows.defi.messari.MessariClient.get_protocol_tvl")
       @patch("defiagents.dataflows.defi.defillama.DefiLlamaAPI.get_protocol_tvl")
       def test_fallback_404_to_defillama(self, mock_defillama, mock_messari):
           """测试 Messari 404 → DeFi Llama 成功"""
           mock_messari.side_effect = MessariNotFoundError("Protocol not found")
           mock_defillama.return_value = 9876543210.0

           sources = [DataSourceType.MESSARI, DataSourceType.DEFILLAMA]
           result = get_data_with_fallback(
               "compound-v3",
               "get_protocol_tvl",
               sources
           )

           assert result == 9876543210.0
           mock_messari.assert_called_once()
           mock_defillama.assert_called_once()

       @patch("defiagents.dataflows.defi.messari.MessariClient.get_protocol_tvl")
       @patch("defiagents.dataflows.defi.defillama.DefiLlamaAPI.get_protocol_tvl")
       def test_all_sources_fail(self, mock_defillama, mock_messari):
           """测试所有数据源失败"""
           mock_messari.side_effect = MessariAPIError("Network error")
           mock_defillama.side_effect = Exception("API error")

           sources = [DataSourceType.MESSARI, DataSourceType.DEFILLAMA]

           with pytest.raises(AllSourcesFailedError) as exc_info:
               get_data_with_fallback(
                   "invalid-protocol",
                   "get_protocol_tvl",
                   sources
               )

           # 错误信息包含所有失败原因
           assert "messari" in str(exc_info.value).lower()
           assert "defillama" in str(exc_info.value).lower()

       # ... 更多测试（429 回退、网络重试、数据格式转换）
   ```

4. **Adapter 测试** (`test_messari_adapters.py`):
   ```python
   import pytest
   from defiagents.dataflows.defi.adapters import DataAdapter
   from defiagents.dataflows.interface import DataSourceType

   class TestDataAdapter:
       def test_normalize_tvl_messari(self):
           """测试 Messari TVL 格式转换"""
           messari_data = {
               "protocol": {"totalValueLockedUSD": 5234567890.12}
           }

           tvl = DataAdapter.normalize_tvl(messari_data, DataSourceType.MESSARI)

           assert tvl == 5234567890.12

       def test_normalize_tvl_defillama(self):
           """测试 DeFi Llama TVL 格式转换"""
           # 测试多种 DeFi Llama 返回格式

           # 格式 1: float
           tvl1 = DataAdapter.normalize_tvl(1234567890.0, DataSourceType.DEFILLAMA)
           assert tvl1 == 1234567890.0

           # 格式 2: dict with tvl
           tvl2 = DataAdapter.normalize_tvl({"tvl": 9876543210.0}, DataSourceType.DEFILLAMA)
           assert tvl2 == 9876543210.0

           # 格式 3: list of numbers
           tvl3 = DataAdapter.normalize_tvl([100.0, 200.0, 300.0], DataSourceType.DEFILLAMA)
           assert tvl3 == 600.0

       # ... 更多测试（lending markets, dex pools）
   ```

**测试命令**:
```bash
# 运行所有 Phase 1 单元测试
pytest tests/dataflows/test_messari_*.py tests/dataflows/test_fallback_*.py -v --cov=defiagents/dataflows --cov-report=term --cov-report=html

# 仅运行 Mock 测试（默认）
pytest tests/dataflows/ -v -m "not integration"

# 运行集成测试（可选，需手动启用）
pytest tests/dataflows/ -v -m integration
```

**测试焦点**:
- **Messari 客户端**:
  - 正常响应（TVL, lending markets, DEX pools）
  - 缓存命中/未命中
  - 404/429/timeout 错误
  - 部署 ID 加载

- **回退机制**:
  - 主数据源成功（无回退）
  - 404 → 回退到下一个源
  - 429 → 回退到下一个源
  - 网络错误 → 重试 → 回退
  - 所有源失败 → 抛出 AllSourcesFailedError

- **数据 Adapter**:
  - Messari → 统一格式
  - DeFi Llama → 统一格式（处理多种返回类型）
  - The Graph → 统一格式

**验收标准**:
- [ ] 所有测试文件创建完成
- [ ] Mock 数据 fixtures 完整（≥20 个场景）
- [ ] 单元测试覆盖率 ≥90%
- [ ] 所有测试默认使用 Mock（0 次真实 API 调用）
- [ ] 集成测试标记正确（`-m integration` 可独立运行）
- [ ] 测试日志清晰（使用 `caplog` fixture 验证日志输出）
- [ ] 所有测试通过（`pytest --tb=short`）

---

## 验收标准

### Phase 1 整体验收标准

- [ ] **代码实现**:
  - [ ] `messari.py` 客户端实现完成（~350 行）
  - [ ] `messari_schemas.py` Schema 定义完成（~150 行）
  - [ ] `interface.py` 回退机制实现完成（~200 行新增）
  - [ ] `adapters.py` 数据转换实现完成（~150 行）
  - [ ] `default_config.py` 配置更新完成（~30 行新增）
  - [ ] `.env.example` 文档更新完成

- [ ] **测试覆盖**:
  - [ ] 单元测试覆盖率 ≥90%
  - [ ] 所有关键路径覆盖率 100%
  - [ ] Mock 测试完整（0 次真实 API 调用）
  - [ ] 集成测试可选（标记为 `-m integration`）

- [ ] **功能验证**:
  - [ ] Messari 客户端能成功获取 TVL（Mock 测试）
  - [ ] Messari 客户端能成功获取 lending markets（Mock 测试）
  - [ ] Messari 客户端能成功获取 DEX pools（Mock 测试）
  - [ ] 缓存机制正常工作（命中率测试通过）
  - [ ] 回退机制能正确处理 404/429/timeout 错误
  - [ ] 所有数据源失败时返回友好错误信息
  - [ ] 数据格式转换正确（Messari/DeFi Llama/The Graph → 统一格式）

- [ ] **性能指标**:
  - [ ] 单次 API 调用响应时间 <3 秒（Mock 测试 <0.1 秒）
  - [ ] 缓存命中响应时间 <0.5 秒
  - [ ] 回退切换延迟 <2 秒

- [ ] **代码质量**:
  - [ ] 遵循 PEP 8 规范（`flake8` 无错误）
  - [ ] 类型注解完整（`mypy` 无错误）
  - [ ] Docstring 完整（Google 风格）
  - [ ] 日志清晰（DEBUG/INFO/WARNING/ERROR 级别正确）

- [ ] **文档更新**:
  - [ ] `.env.example` 包含 Messari 配置说明
  - [ ] `CLAUDE.md` 更新架构说明（可选，Phase 1 无架构级变更）
  - [ ] `PROJECT_STATUS.md` 标记 Phase 1 完成（待 Phase 完成后更新）

---

## 技术注意事项

### 关键设计决策

1. **为什么使用责任链模式？**
   - 优点：易于扩展（添加新数据源只需修改配置）
   - 优点：错误隔离（单个数据源失败不影响整体）
   - 优点：灵活配置（可运行时调整优先级）

2. **为什么优先使用 Mock 测试？**
   - 避免 API 配额消耗（Messari 有速率限制）
   - 提高测试速度（Mock 响应 <0.1 秒）
   - 确保测试稳定性（不依赖外部 API 可用性）

3. **为什么需要数据格式 Adapter？**
   - Messari Schema：标准化但字段嵌套深（`protocol.totalValueLockedUSD`）
   - DeFi Llama：字段平坦但类型不一致（float/list/dict）
   - The Graph：GraphQL 格式，数组嵌套（`financialsDailySnapshots[0].totalValueLockedUSD`）
   - 统一格式简化上层 Agent 工具代码

### 潜在风险和缓解措施

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| Messari API 返回字段缺失 | 🟡 中 | 🟡 中 | Adapter 添加字段存在性检查，缺失时返回默认值 |
| Deployment JSON 文件过大导致加载慢 | 🟢 低 | 🟢 低 | 使用懒加载（首次调用时加载），内存缓存 |
| 网络重试逻辑导致超时 | 🟡 中 | 🟡 中 | 限制重试次数为 1 次，总超时 <15 秒 |
| 缓存导致数据过期 | 🟢 低 | 🟡 中 | TVL 数据 TTL 设为 1 小时（协议 TVL 更新慢） |
| 多源回退增加代码复杂度 | 🟡 中 | 🟢 低 | 完整单元测试覆盖（≥90%），清晰的错误日志 |

### 开发提示

1. **遵循现有代码模式**:
   - 参考 `the_graph.py` 的客户端结构
   - 参考 `defillama.py` 的缓存机制
   - 参考 `interface.py` 的现有路由逻辑

2. **优先编写测试**:
   - TDD 模式：先写测试，再写实现
   - 每个函数至少 3 个测试：正常、错误、边界

3. **清晰的错误信息**:
   - 错误信息格式：`❌ 错误: {原因}\n协议: {protocol}\n数据源: {source}\n建议: {action}`
   - 包含足够的上下文信息（协议名、链、方法名）

4. **日志最佳实践**:
   - DEBUG: 详细的调试信息（缓存键、API URL、请求参数）
   - INFO: 正常流程信息（API 调用成功、数据源切换）
   - WARNING: 可恢复的错误（单数据源失败、数据格式异常）
   - ERROR: 严重错误（所有数据源失败、配置错误）

---

## 下一步计划

Phase 1 完成后，将进入 **Phase 2: 核心数据源迁移**（Week 3-4）:

1. 重构 `defillama.py`（降级为备用数据源）
2. 重构 `the_graph.py`（保留用于实时事件）
3. 集成测试（验证多源互操作性）

**Phase 1 → Phase 2 的衔接点**:
- Phase 1 提供的 `get_data_with_fallback()` 函数将在 Phase 2 被 Agent 工具函数调用
- Phase 1 的 Adapter 在 Phase 2 继续扩展（添加更多协议类型支持）
- Phase 1 的配置系统在 Phase 2 保持稳定（仅调整优先级列表）

---

**文档版本**: v1.0
**创建日期**: 2025-12-11
**作者**: Claude (AI Development Plan Generator)
**审核状态**: 待用户审核
**相关文档**: `.claude/dev-log-messari-refactoring.md`, `MESSARI_SUBGRAPHS_EVALUATION.md`
