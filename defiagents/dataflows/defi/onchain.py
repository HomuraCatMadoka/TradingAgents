"""
On-chain data access via Web3.py.

Provides direct blockchain interaction capabilities via RPC nodes.
Supports multiple chains and RPC providers with automatic fallback.

Features:
- Multi-chain RPC connection management
- Smart contract reading (ABI-based and raw calls)
- Token balance queries (ERC20)
- Block and transaction data
- Gas price monitoring
"""

import logging
from typing import Dict, List, Optional, Any, Union
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_typing import ChecksumAddress

logger = logging.getLogger(__name__)


# Standard ERC20 ABI (minimal, for balance and basic info)
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
]


class OnChainClient:
    """Multi-chain on-chain data client."""

    # Chain IDs for reference
    CHAIN_IDS = {
        "ethereum": 1,
        "arbitrum": 42161,
        "optimism": 10,
        "base": 8453,
        "polygon": 137,
        "bsc": 56,
        "avalanche": 43114,
    }

    def __init__(self, rpc_config: Dict[str, Dict[str, str]]):
        """
        Initialize on-chain client.

        Args:
            rpc_config: Dictionary mapping chain names to RPC configurations
                Example:
                {
                    "ethereum": {"provider": "alchemy", "url": "https://..."},
                    "arbitrum": {"provider": "alchemy", "url": "https://..."},
                }
        """
        self.rpc_config = rpc_config
        self._web3_instances: Dict[str, Web3] = {}
        self._initialize_connections()

    def _initialize_connections(self):
        """Initialize Web3 connections for all configured chains."""
        for chain, config in self.rpc_config.items():
            try:
                url = config.get("url")
                if not url or "YOUR_API_KEY" in url:
                    logger.warning(f"Skipping {chain}: No valid RPC URL configured")
                    continue

                w3 = Web3(Web3.HTTPProvider(url))

                # Add PoA middleware for chains that need it (Polygon, BSC, etc.)
                if chain in ["polygon", "bsc"]:
                    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

                # Verify connection
                if w3.is_connected():
                    self._web3_instances[chain] = w3
                    logger.info(f"Connected to {chain} at {url[:50]}...")
                else:
                    logger.warning(f"Failed to connect to {chain}")
            except Exception as e:
                logger.error(f"Error initializing {chain}: {e}")

    def get_web3(self, chain: str) -> Optional[Web3]:
        """
        Get Web3 instance for a specific chain.

        Args:
            chain: Chain name (e.g., 'ethereum', 'arbitrum')

        Returns:
            Web3 instance or None if not available
        """
        if chain not in self._web3_instances:
            logger.error(f"Chain {chain} not configured or unavailable")
            return None
        return self._web3_instances[chain]

    def get_block_number(self, chain: str) -> Optional[int]:
        """
        Get current block number.

        Args:
            chain: Chain name

        Returns:
            Current block number or None
        """
        w3 = self.get_web3(chain)
        if not w3:
            return None

        try:
            return w3.eth.block_number
        except Exception as e:
            logger.error(f"Error getting block number on {chain}: {e}")
            return None

    def get_gas_price(self, chain: str) -> Optional[int]:
        """
        Get current gas price in wei.

        Args:
            chain: Chain name

        Returns:
            Gas price in wei or None
        """
        w3 = self.get_web3(chain)
        if not w3:
            return None

        try:
            return w3.eth.gas_price
        except Exception as e:
            logger.error(f"Error getting gas price on {chain}: {e}")
            return None

    def get_balance(self, chain: str, address: str) -> Optional[int]:
        """
        Get native token balance (ETH, etc.) in wei.

        Args:
            chain: Chain name
            address: Wallet address

        Returns:
            Balance in wei or None
        """
        w3 = self.get_web3(chain)
        if not w3:
            return None

        try:
            checksum_address = w3.to_checksum_address(address)
            return w3.eth.get_balance(checksum_address)
        except Exception as e:
            logger.error(f"Error getting balance on {chain}: {e}")
            return None

    def get_token_balance(
        self,
        chain: str,
        token_address: str,
        wallet_address: str,
    ) -> Optional[int]:
        """
        Get ERC20 token balance (raw units, not adjusted for decimals).

        Args:
            chain: Chain name
            token_address: ERC20 token contract address
            wallet_address: Wallet address

        Returns:
            Token balance (raw units) or None
        """
        w3 = self.get_web3(chain)
        if not w3:
            return None

        try:
            token_contract = w3.eth.contract(
                address=w3.to_checksum_address(token_address),
                abi=ERC20_ABI,
            )
            balance = token_contract.functions.balanceOf(
                w3.to_checksum_address(wallet_address)
            ).call()
            return balance
        except Exception as e:
            logger.error(f"Error getting token balance on {chain}: {e}")
            return None

    def get_token_info(self, chain: str, token_address: str) -> Optional[Dict]:
        """
        Get ERC20 token information (name, symbol, decimals, totalSupply).

        Args:
            chain: Chain name
            token_address: ERC20 token contract address

        Returns:
            Dictionary with token info or None

        Example:
            >>> client = OnChainClient(config)
            >>> info = client.get_token_info('ethereum', '0xa0b86991...')
            >>> print(info['symbol'])  # 'USDC'
        """
        w3 = self.get_web3(chain)
        if not w3:
            return None

        try:
            token_contract = w3.eth.contract(
                address=w3.to_checksum_address(token_address),
                abi=ERC20_ABI,
            )

            name = token_contract.functions.name().call()
            symbol = token_contract.functions.symbol().call()
            decimals = token_contract.functions.decimals().call()
            total_supply = token_contract.functions.totalSupply().call()

            return {
                "name": name,
                "symbol": symbol,
                "decimals": decimals,
                "total_supply": total_supply,
                "address": token_address,
                "chain": chain,
            }
        except Exception as e:
            logger.error(f"Error getting token info on {chain}: {e}")
            return None

    def call_contract_function(
        self,
        chain: str,
        contract_address: str,
        abi: List[Dict],
        function_name: str,
        *args,
        **kwargs,
    ) -> Any:
        """
        Call a read-only smart contract function.

        Args:
            chain: Chain name
            contract_address: Contract address
            abi: Contract ABI
            function_name: Function name to call
            *args: Function arguments
            **kwargs: Additional call parameters

        Returns:
            Function return value

        Example:
            >>> result = client.call_contract_function(
            ...     'ethereum',
            ...     '0x...',
            ...     POOL_ABI,
            ...     'getReserves'
            ... )
        """
        w3 = self.get_web3(chain)
        if not w3:
            return None

        try:
            contract = w3.eth.contract(
                address=w3.to_checksum_address(contract_address),
                abi=abi,
            )
            func = getattr(contract.functions, function_name)
            return func(*args).call(**kwargs)
        except Exception as e:
            logger.error(f"Error calling contract function on {chain}: {e}")
            raise

    def get_transaction(self, chain: str, tx_hash: str) -> Optional[Dict]:
        """
        Get transaction details.

        Args:
            chain: Chain name
            tx_hash: Transaction hash

        Returns:
            Transaction data dictionary or None
        """
        w3 = self.get_web3(chain)
        if not w3:
            return None

        try:
            tx = w3.eth.get_transaction(tx_hash)
            return dict(tx)
        except Exception as e:
            logger.error(f"Error getting transaction on {chain}: {e}")
            return None

    def get_transaction_receipt(self, chain: str, tx_hash: str) -> Optional[Dict]:
        """
        Get transaction receipt.

        Args:
            chain: Chain name
            tx_hash: Transaction hash

        Returns:
            Receipt data dictionary or None
        """
        w3 = self.get_web3(chain)
        if not w3:
            return None

        try:
            receipt = w3.eth.get_transaction_receipt(tx_hash)
            return dict(receipt)
        except Exception as e:
            logger.error(f"Error getting transaction receipt on {chain}: {e}")
            return None

    def get_block(self, chain: str, block_identifier: Union[int, str]) -> Optional[Dict]:
        """
        Get block data.

        Args:
            chain: Chain name
            block_identifier: Block number or 'latest'

        Returns:
            Block data dictionary or None
        """
        w3 = self.get_web3(chain)
        if not w3:
            return None

        try:
            block = w3.eth.get_block(block_identifier)
            return dict(block)
        except Exception as e:
            logger.error(f"Error getting block on {chain}: {e}")
            return None


# Global instance
_client_instance: Optional[OnChainClient] = None


def get_client_instance(rpc_config: Optional[Dict] = None) -> OnChainClient:
    """Get or create global client instance."""
    global _client_instance
    if _client_instance is None:
        if rpc_config is None:
            # Try to load from default config
            try:
                from defiagents.default_config import DEFAULT_CONFIG
                rpc_config = DEFAULT_CONFIG.get("rpc_providers", {})
            except ImportError:
                logger.error("Cannot load RPC config and none provided")
                rpc_config = {}

        _client_instance = OnChainClient(rpc_config)
    return _client_instance


# Convenience functions


def get_block_number(chain: str = "ethereum") -> Optional[int]:
    """
    Get current block number.

    Args:
        chain: Chain name

    Returns:
        Current block number
    """
    client = get_client_instance()
    return client.get_block_number(chain)


def get_token_balance(
    chain: str,
    token_address: str,
    wallet_address: str,
) -> Optional[float]:
    """
    Get ERC20 token balance (adjusted for decimals).

    Args:
        chain: Chain name
        token_address: Token contract address
        wallet_address: Wallet address

    Returns:
        Token balance (human-readable, adjusted for decimals)
    """
    client = get_client_instance()

    # Get token info for decimals
    token_info = client.get_token_info(chain, token_address)
    if not token_info:
        return None

    # Get raw balance
    raw_balance = client.get_token_balance(chain, token_address, wallet_address)
    if raw_balance is None:
        return None

    # Adjust for decimals
    decimals = token_info["decimals"]
    return raw_balance / (10 ** decimals)


def get_contract_data(
    chain: str,
    contract_address: str,
    abi: List[Dict],
    function_name: str,
    *args,
) -> Any:
    """
    Call a contract read function.

    Args:
        chain: Chain name
        contract_address: Contract address
        abi: Contract ABI
        function_name: Function to call
        *args: Function arguments

    Returns:
        Function result
    """
    client = get_client_instance()
    return client.call_contract_function(
        chain, contract_address, abi, function_name, *args
    )


def format_gas_price(chain: str, gas_price_wei: int) -> str:
    """
    Format gas price into readable string.

    Args:
        chain: Chain name
        gas_price_wei: Gas price in wei

    Returns:
        Formatted string
    """
    gwei = gas_price_wei / 1e9
    return f"""## {chain.title()} Gas Price

**Current Gas Price**: {gwei:.2f} Gwei
**In Wei**: {gas_price_wei:,}
"""


def format_token_balance(
    chain: str,
    token_info: Dict,
    balance: float,
) -> str:
    """
    Format token balance into readable string.

    Args:
        chain: Chain name
        token_info: Token info dictionary
        balance: Token balance (human-readable)

    Returns:
        Formatted string
    """
    symbol = token_info.get("symbol", "???")
    name = token_info.get("name", "Unknown Token")
    address = token_info.get("address", "")

    return f"""## {name} ({symbol}) Balance

**Chain**: {chain.title()}
**Balance**: {balance:,.6f} {symbol}
**Contract**: `{address}`
"""


if __name__ == "__main__":
    # Example usage
    import sys
    import os

    logging.basicConfig(level=logging.INFO)

    print("Testing On-Chain Data Access...\n")

    # Example RPC configuration (replace with real URLs)
    test_config = {
        "ethereum": {
            "provider": "alchemy",
            "url": os.getenv("ETH_RPC_URL", "https://eth-mainnet.g.alchemy.com/v2/demo"),
        },
        "arbitrum": {
            "provider": "alchemy",
            "url": os.getenv("ARB_RPC_URL", "https://arb-mainnet.g.alchemy.com/v2/demo"),
        },
    }

    try:
        client = OnChainClient(test_config)

        # Test block number
        print("=== Ethereum Block Number ===\n")
        block_num = client.get_block_number("ethereum")
        if block_num:
            print(f"Current block: {block_num:,}")
        print()

        print("="*60 + "\n")

        # Test gas price
        print("=== Ethereum Gas Price ===\n")
        gas_price = client.get_gas_price("ethereum")
        if gas_price:
            print(format_gas_price("ethereum", gas_price))
        print()

        print("="*60 + "\n")

        # Test token info (USDC on Ethereum)
        print("=== USDC Token Info (Ethereum) ===\n")
        usdc_address = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
        token_info = client.get_token_info("ethereum", usdc_address)
        if token_info:
            print(f"Name: {token_info['name']}")
            print(f"Symbol: {token_info['symbol']}")
            print(f"Decimals: {token_info['decimals']}")
            print(f"Total Supply: {token_info['total_supply'] / (10 ** token_info['decimals']):,.0f}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
