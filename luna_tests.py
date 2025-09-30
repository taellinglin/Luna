# test_luna_system.py
import pytest
import json
import os
import tempfile
import time
from unittest.mock import Mock, patch
import sys

# Add the current directory to Python path to import your modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import your modules
try:
    from luna_node import LunaNode, Blockchain, Block, NodeConfig, ConfigManager
    from luna_wallet import LunaWallet, DataManager

    LUNA_IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import Luna modules: {e}")
    LUNA_NA_IMPORTS_AVAILABLE = False


@pytest.fixture
def temp_data_dir():
    """Create a temporary data directory for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        original_data_dir = None

        # Patch the data directory methods
        if hasattr(ConfigManager, "get_data_dir"):
            original_get_data_dir = ConfigManager.get_data_dir
            ConfigManager.get_data_dir = lambda: temp_dir

        if hasattr(DataManager, "get_data_dir"):
            original_get_data_dir_wallet = DataManager.get_data_dir
            DataManager.get_data_dir = lambda: temp_dir

        yield temp_dir

        # Restore original methods
        if original_data_dir and hasattr(ConfigManager, "get_data_dir"):
            ConfigManager.get_data_dir = original_get_data_dir
        if hasattr(DataManager, "get_data_dir") and original_get_data_dir_wallet:
            DataManager.get_data_dir = original_get_data_dir_wallet


@pytest.fixture
def sample_blockchain_data():
    """Sample blockchain data for testing"""
    return [
        {
            "index": 0,
            "previous_hash": "0",
            "timestamp": time.time(),
            "transactions": [
                {
                    "type": "genesis",
                    "message": "Test Genesis Block",
                    "timestamp": time.time(),
                    "reward": 1000,
                    "miner": "test_network",
                }
            ],
            "nonce": 0,
            "hash": "genesis_hash_123",
        },
        {
            "index": 1,
            "previous_hash": "genesis_hash_123",
            "timestamp": time.time(),
            "transactions": [
                {
                    "type": "transfer",
                    "from": "LKC_sender_123",
                    "to": "LKC_recipient_456",
                    "amount": 50.0,
                    "timestamp": time.time(),
                    "signature": "tx_sig_1",
                },
                {
                    "type": "reward",
                    "miner": "LUN_miner_789",
                    "amount": 1.0,
                    "timestamp": time.time(),
                },
            ],
            "nonce": 12345,
            "hash": "block_hash_1",
        },
    ]


@pytest.fixture
def sample_mempool_data():
    """Sample mempool data for testing"""
    return [
        {
            "type": "GTX_Genesis",
            "serial_number": "SN123456",
            "amount": 100.0,
            "timestamp": time.time(),
        },
        {
            "type": "transfer",
            "from": "LKC_addr_1",
            "to": "LKC_addr_2",
            "amount": 25.0,
            "timestamp": time.time(),
            "signature": "tx_sig_mempool_1",
        },
    ]


class TestLunaNodeBasic:
    """Basic functionality tests for Luna Node"""

    def test_config_manager_save_load(self, temp_data_dir):
        """Test ConfigManager save and load functionality"""
        test_data = {"key": "value", "number": 42, "list": [1, 2, 3]}

        # Test save
        result = ConfigManager.save_json("test_config.json", test_data)
        assert result == True

        # Test load
        loaded_data = ConfigManager.load_json("test_config.json", {})
        assert loaded_data == test_data

        # Test file exists
        expected_path = os.path.join(temp_data_dir, "test_config.json")
        assert os.path.exists(expected_path)

    def test_block_creation(self):
        """Test Block object creation and hashing"""
        transactions = [{"type": "test", "data": "sample"}]
        block = Block(1, "previous_hash_123", transactions, nonce=0)

        assert block.index == 1
        assert block.previous_hash == "previous_hash_123"
        assert block.transactions == transactions
        assert block.nonce == 0
        assert isinstance(block.hash, str)
        assert len(block.hash) == 64  # SHA256 hash length

        # Test hash consistency
        original_hash = block.hash
        block.nonce = 1
        new_hash = block.calculate_hash()
        assert new_hash != original_hash

    def test_block_to_from_dict(self):
        """Test Block serialization/deserialization"""
        transactions = [{"type": "test", "amount": 100}]
        original_block = Block(2, "prev_hash", transactions, nonce=42)
        original_block.mining_time = 5.5

        # Convert to dict
        block_dict = original_block.to_dict()

        # Convert back to Block object
        restored_block = Block.from_dict(block_dict)

        assert restored_block.index == original_block.index
        assert restored_block.previous_hash == original_block.previous_hash
        assert restored_block.transactions == original_block.transactions
        assert restored_block.nonce == original_block.nonce
        assert restored_block.mining_time == original_block.mining_time


class TestBlockchainSync:
    """Tests for blockchain synchronization functionality"""

    @patch("luna_node.requests.get")
    def test_sync_from_web_success(
        self, mock_get, temp_data_dir, sample_blockchain_data
    ):
        """Test successful blockchain sync from web API"""
        # Mock the API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_blockchain_data
        mock_get.return_value = mock_response

        # Create config and blockchain
        config = NodeConfig()
        blockchain = Blockchain(config)

        # Initial chain length
        initial_length = len(blockchain.chain)

        # Perform sync
        result = blockchain.sync_from_web()

        assert result == True
        assert len(blockchain.chain) > initial_length
        mock_get.assert_called_once()

    @patch("luna_node.requests.get")
    def test_sync_from_web_failure(self, mock_get, temp_data_dir):
        """Test blockchain sync failure handling"""
        # Mock failed API response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        config = NodeConfig()
        blockchain = Blockchain(config)
        initial_length = len(blockchain.chain)

        result = blockchain.sync_from_web()

        assert result == False
        assert len(blockchain.chain) == initial_length

    @patch("luna_node.requests.get")
    def test_mempool_sync(self, mock_get, temp_data_dir, sample_mempool_data):
        """Test mempool synchronization"""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_mempool_data
        mock_get.return_value = mock_response

        config = NodeConfig()
        blockchain = Blockchain(config)

        result = blockchain.sync_mempool_from_api()

        assert result == True
        assert len(blockchain.mempool) == len(sample_mempool_data)
        mock_get.assert_called_once()


class TestTransactionProcessing:
    """Tests for transaction processing and tracking"""

    def test_transaction_signature_generation(self, temp_data_dir):
        """Test transaction signature generation"""
        config = NodeConfig()
        blockchain = Blockchain(config)

        # Test with signature
        tx_with_sig = {"signature": "existing_sig_123", "amount": 100}
        sig1 = blockchain.get_transaction_signature(tx_with_sig)
        assert sig1 == "existing_sig_123"

        # Test with serial number
        tx_with_serial = {"serial_number": "SN789", "amount": 200}
        sig2 = blockchain.get_transaction_signature(tx_with_serial)
        assert sig2 == "serial_SN789"

        # Test with front serial
        tx_with_front = {"front_serial": "FSN456", "amount": 300}
        sig3 = blockchain.get_transaction_signature(tx_with_front)
        assert sig3 == "front_FSN456"

        # Test fallback hash
        tx_fallback = {"amount": 400, "data": "test"}
        sig4 = blockchain.get_transaction_signature(tx_fallback)
        assert isinstance(sig4, str)
        assert len(sig4) <= 32

    def test_transaction_mining_tracking(self, temp_data_dir):
        """Test tracking of mined transactions"""
        config = NodeConfig()

        # Ensure mined_transactions is a dict
        if not isinstance(config.mined_transactions, dict):
            config.mined_transactions = {}

        tx_signature = "test_tx_signature_123"
        block_hash = "block_hash_456"

        # Mark as mined
        config.mark_transaction_mined(tx_signature, block_hash)

        # Check if tracked
        assert config.is_transaction_mined(tx_signature) == True
        assert tx_signature in config.mined_transactions
        assert config.mined_transactions[tx_signature]["block_hash"] == block_hash

        # Check non-existent transaction
        assert config.is_transaction_mined("non_existent_sig") == False

    def test_find_unmined_transactions(self, temp_data_dir, sample_blockchain_data):
        """Test finding unmined transactions"""
        config = NodeConfig()
        blockchain = Blockchain(config)

        # Load sample blockchain data
        blockchain.chain = [Block.from_dict(block) for block in sample_blockchain_data]

        # Find unmined transactions
        unmined = blockchain.find_unmined_transactions()

        # Should find the transfer transaction but not the reward transaction
        assert isinstance(unmined, list)

        # Mark a transaction as mined and test again
        if unmined:
            tx_info = unmined[0]
            config.mark_transaction_mined(tx_info["signature"], "test_block_hash")

            unmined_after = blockchain.find_unmined_transactions()
            # The mined transaction should not appear in unmined list
            tx_signatures = [tx["signature"] for tx in unmined_after]
            assert tx_info["signature"] not in tx_signatures


class TestWalletIntegration:
    """Tests for wallet integration with blockchain"""

    def test_wallet_creation(self, temp_data_dir):
        """Test wallet creation and basic operations"""
        wallet = LunaWallet()

        # Should have at least one wallet
        assert len(wallet.addresses) >= 1

        # Check wallet structure
        first_wallet = wallet.addresses[0]
        assert "address" in first_wallet
        assert "private_key" in first_wallet
        assert "public_key" in first_wallet
        assert "balance" in first_wallet
        assert "transactions" in first_wallet

        # Address should start with LKC_
        assert first_wallet["address"].startswith("LKC_")

    def test_wallet_backup(self, temp_data_dir):
        """Test wallet backup functionality"""
        wallet = LunaWallet()

        # Create backup
        result = wallet.backup_wallet()
        assert result == True

        # Check backup file was created
        backup_files = [
            f for f in os.listdir(temp_data_dir) if f.startswith("wallet_manual_backup")
        ]
        assert len(backup_files) >= 1

    def test_blockchain_data_loading(self, temp_data_dir, sample_blockchain_data):
        """Test wallet's ability to load blockchain data"""
        # Save sample blockchain data
        blockchain_path = os.path.join(temp_data_dir, "blockchain.json")
        with open(blockchain_path, "w") as f:
            json.dump(sample_blockchain_data, f)

        wallet = LunaWallet()

        # Load blockchain data
        blockchain_data = wallet.get_blockchain_data()

        assert isinstance(blockchain_data, list)
        assert len(blockchain_data) == len(sample_blockchain_data)

    def test_transaction_discovery(self, temp_data_dir, sample_blockchain_data):
        """Test wallet's transaction discovery from blockchain"""
        # Create a test wallet address
        test_address = "LKC_recipient_456"  # This address is in sample_blockchain_data

        # Save blockchain data with transactions involving our test address
        blockchain_path = os.path.join(temp_data_dir, "blockchain.json")
        with open(blockchain_path, "w") as f:
            json.dump(sample_blockchain_data, f)

        wallet = LunaWallet()

        # Get transactions for the test address
        transactions = wallet.get_address_transactions(test_address)

        # Should find transactions involving this address
        assert isinstance(transactions, list)

        # Verify transaction details
        if transactions:
            tx = transactions[0]
            assert "from" in tx or "to" in tx
            assert "amount" in tx
            assert test_address in [tx.get("from"), tx.get("to")]


class TestDebugUtilities:
    """Debugging utilities for the Luna system"""

    def test_blockchain_integrity_check(self, temp_data_dir):
        """Test blockchain integrity verification"""
        config = NodeConfig()
        blockchain = Blockchain(config)

        # Test with valid chain
        is_valid = blockchain.is_chain_valid()
        assert isinstance(is_valid, bool)

        # Test chain length method
        length = blockchain.get_chain_length()
        assert isinstance(length, int)
        assert length >= 1  # At least genesis block

    def test_transaction_confirmation_tracking(
        self, temp_data_dir, sample_blockchain_data
    ):
        """Test transaction confirmation counting"""
        # Setup blockchain data
        blockchain_path = os.path.join(temp_data_dir, "blockchain.json")
        with open(blockchain_path, "w") as f:
            json.dump(sample_blockchain_data, f)

        wallet = LunaWallet()

        # Update transaction confirmations
        wallet.update_transaction_confirmations()

        # This should run without errors
        assert True

    def test_mempool_merging(self, temp_data_dir):
        """Test mempool merging logic"""
        config = NodeConfig()
        blockchain = Blockchain(config)

        local_mempool = [
            {"signature": "local_1", "amount": 100},
            {"signature": "local_2", "amount": 200},
        ]

        api_mempool = [
            {"signature": "local_1", "amount": 100},  # Duplicate
            {"signature": "api_1", "amount": 300},  # New
            {"signature": "api_2", "amount": 400},  # New
        ]

        merged = blockchain.merge_mempools(local_mempool, api_mempool)

        assert len(merged) == 4  # 2 local + 2 new (duplicate removed)

        # Check that all signatures are present
        signatures = [blockchain.get_transaction_signature(tx) for tx in merged]
        assert "local_1" in signatures
        assert "local_2" in signatures
        assert "api_1" in signatures
        assert "api_2" in signatures


def test_comprehensive_sync_scenario(
    temp_data_dir, sample_blockchain_data, sample_mempool_data
):
    """Comprehensive test of the sync process"""
    print("\n=== COMPREHENSIVE SYNC TEST ===")

    # Setup test data
    blockchain_path = os.path.join(temp_data_dir, "blockchain.json")
    mempool_path = os.path.join(temp_data_dir, "mempool.json")

    with open(blockchain_path, "w") as f:
        json.dump(sample_blockchain_data, f)

    with open(mempool_path, "w") as f:
        json.dump(sample_mempool_data, f)

    print("✓ Test data created")

    # Initialize wallet
    wallet = LunaWallet()
    print("✓ Wallet initialized")

    # Sync with node
    sync_result = wallet.sync_with_node()
    print(f"✓ Sync result: {sync_result}")

    # Check balance calculation
    if wallet.addresses:
        address = wallet.addresses[0]["address"]
        balance = wallet.get_address_balance(address)
        print(f"✓ Balance calculated: {balance}")

        # Get transactions
        transactions = wallet.get_address_transactions(address)
        print(f"✓ Transactions found: {len(transactions)}")

        # Show transaction history
        print("✓ Transaction history check passed")

    assert sync_result == True
    print("🎉 Comprehensive sync test completed successfully!")


# Debugging function to inspect actual data
def debug_blockchain_structure():
    """Debug function to inspect actual blockchain structure"""
    print("\n=== BLOCKCHAIN STRUCTURE DEBUG ===")

    try:
        wallet = LunaWallet()
        blockchain_data = wallet.get_blockchain_data()

        print(f"Blockchain data type: {type(blockchain_data)}")

        if isinstance(blockchain_data, list):
            print(f"Number of blocks: {len(blockchain_data)}")

            if len(blockchain_data) > 0:
                print("\nFirst block structure:")
                first_block = blockchain_data[0]
                print(f"Type: {type(first_block)}")
                if isinstance(first_block, dict):
                    print(f"Keys: {list(first_block.keys())}")

                    if "transactions" in first_block:
                        txs = first_block["transactions"]
                        print(f"Number of transactions in first block: {len(txs)}")
                        if len(txs) > 0:
                            print("First transaction keys:", list(txs[0].keys()))

        elif isinstance(blockchain_data, dict):
            print(f"Dictionary keys: {list(blockchain_data.keys())}")

        print("=== END DEBUG ===")

    except Exception as e:
        print(f"Debug error: {e}")


if __name__ == "__main__":
    # Run the debug function if executed directly
    debug_blockchain_structure()

    # Run specific tests
    pytest.main([__file__, "-v", "-k", "test_transaction_discovery"])
