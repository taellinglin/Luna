#!/usr/bin/env python3
"""
luna_sim.py - THREADED VERSION WITH CONCURRENT TRANSFERS AND MINING
"""

import requests
import threading
import time
import logging
import os
import random
import json
import hashlib
import secrets
from typing import List, Dict, Optional
from queue import Queue

# -----------------------
# CONFIG
# -----------------------
BASE_URL = "https://bank.linglin.art/"

NUM_MINERS = 31
LOG_LEVEL = logging.INFO
NUM_WALLETS = 31
NUM_TRANSFER_THREADS = 2  # Number of concurrent transfer generators

MINING_DIFFICULTY = 6
BASE_MINING_REWARD = 1.0
TRANSACTION_FEE = 0.00001

# -----------------------
# HTTP endpoints
# -----------------------
ENDPOINT_STATUS = f"{BASE_URL}/blockchain/status"
ENDPOINT_MEMPOOL_ADD = f"{BASE_URL}/mempool/add"
ENDPOINT_MEMPOOL_STATUS = f"{BASE_URL}/mempool/status"
ENDPOINT_BLOCKCHAIN_STATUS = f"{BASE_URL}/blockchain/status"
ENDPOINT_SUBMIT_BLOCK = f"{BASE_URL}/blockchain/submit-block"

# Logging
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("luna_sim")

# Thread synchronization
mining_lock = threading.Lock()
wallet_lock = threading.Lock()


class Wallet:
    """Wallet for managing addresses and transactions"""

    def __init__(self, name):
        self.name = name
        self.address = self.generate_address()
        self.balance = 0.0
        self.private_key = secrets.token_hex(32)
        self.transaction_count = 0
        self.lock = threading.Lock()

    def generate_address(self):
        """Generate a wallet address"""
        return f"wallet_{self.name}_{hashlib.sha256(str(time.time()).encode()).hexdigest()[:16]}"

    def create_transfer(self, to_address, amount):
        """Create a transfer transaction - thread-safe"""
        with self.lock:
            if amount <= 0:
                logger.error(f"❌ Invalid transfer amount: {amount}")
                return None

            if amount > self.balance:
                logger.error(f"❌ Insufficient balance: {self.balance} < {amount}")
                return None

            transaction = {
                "type": "transfer",
                "from": self.address,
                "to": to_address,
                "amount": float(amount),
                "timestamp": time.time(),
                "fee": TRANSACTION_FEE,
                "nonce": self.transaction_count,
            }

            # Create signature (simplified for demo)
            transaction_data = f"{transaction['from']}{transaction['to']}{transaction['amount']}{transaction['timestamp']}{transaction['nonce']}"
            transaction["signature"] = hashlib.sha256(
                transaction_data.encode()
            ).hexdigest()
            transaction["hash"] = hashlib.sha256(
                json.dumps(transaction, sort_keys=True).encode()
            ).hexdigest()

            self.transaction_count += 1
            return transaction

    def update_balance(self, amount):
        """Update wallet balance - thread-safe"""
        with self.lock:
            self.balance += amount
            logger.info(f"💰 {self.name} balance: {self.balance:.2f} LUN")


class BlockchainState:
    """Get the correct blockchain state with proper previous hash"""

    @staticmethod
    def get_next_block_info():
        """Get the correct next block info with ACTUAL previous hash"""
        try:
            # Get blockchain status
            status_response = requests.get(ENDPOINT_BLOCKCHAIN_STATUS, timeout=10)
            if status_response.status_code == 200:
                status_data = status_response.json()
                status_info = status_data.get("status", {})

                # Get actual blockchain to get the REAL previous hash
                blockchain_response = requests.get(f"{BASE_URL}/blockchain", timeout=10)
                actual_blocks_count = 0
                actual_previous_hash = "0" * 64

                if blockchain_response.status_code == 200:
                    blockchain_data = blockchain_response.json()
                    actual_blocks_count = len(blockchain_data)

                    # Get the ACTUAL hash of the last block
                    if actual_blocks_count > 0:
                        last_block = blockchain_data[-1]
                        actual_previous_hash = last_block.get("hash", "0" * 64)
                        logger.info(
                            f"📊 Last block hash: {actual_previous_hash[:16]}..."
                        )
                    else:
                        actual_previous_hash = "0"  # Genesis case

                    logger.info(f"📊 Actual blocks in chain: {actual_blocks_count}")

                # SERVER LOGIC: If blockchain has 1 block (genesis), it expects next block to be index 1
                reported_height = status_info.get("blocks", 0)
                difficulty = status_info.get("difficulty", MINING_DIFFICULTY)

                # The key fix: next_index should equal reported_height
                next_index = reported_height

                logger.info(
                    f"📊 Blockchain state: reported_height={reported_height}, next_index={next_index}"
                )
                logger.info(f"   Previous hash: {actual_previous_hash[:16]}...")
                logger.info(f"   Difficulty: {difficulty}")

                return {
                    "next_index": next_index,  # This matches server expectation
                    "previous_hash": actual_previous_hash,  # ACTUAL hash, not zeros!
                    "difficulty": difficulty,
                    "reported_height": reported_height,
                    "actual_blocks": actual_blocks_count,
                }

        except Exception as e:
            logger.error(f"❌ Failed to get blockchain info: {e}")

        return {
            "next_index": 0,
            "previous_hash": "0" * 64,
            "difficulty": MINING_DIFFICULTY,
            "reported_height": 0,
            "actual_blocks": 0,
        }


class RealBlock:
    """Real block with exact server hash calculation"""

    def __init__(
        self,
        index,
        previous_hash,
        transactions,
        nonce=0,
        timestamp=None,
        miner="default_miner",
    ):
        self.index = int(index)
        self.previous_hash = previous_hash
        self.timestamp = float(timestamp or time.time())
        self.transactions = transactions
        self.nonce = int(nonce)
        self.miner = miner
        self.hash = ""
        self.mining_time = 0

    def calculate_hash(self):
        """Calculate block hash using the EXACT server method"""
        # Based on analysis, the server uses sorted compact JSON
        block_data = {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "nonce": self.nonce,
        }

        # This should match the server's method
        block_string = json.dumps(block_data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine_block(self, difficulty):
        """Mine block with proof-of-work"""
        if self.index == 0:  # Genesis block
            self.hash = "0" * 64
            return True

        target = "0" * difficulty
        start_time = time.time()

        logger.info(f"⛏️ Mining Block #{self.index} | Target: {target}...")
        logger.info(f"   Previous hash: {self.previous_hash[:16]}...")

        # Start from random position
        self.nonce = random.randint(0, 1000000)
        self.hash = self.calculate_hash()

        attempts = 0
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
            attempts += 1

            if attempts % 50000 == 0:
                logger.info(f"   Attempts: {attempts:,} | Hash: {self.hash[:16]}...")

            if attempts > 2000000:
                logger.warning("🔄 Restarting mining with new nonce range...")
                self.nonce = random.randint(0, 1000000)
                attempts = 0

        self.mining_time = time.time() - start_time
        logger.info(f"✅ Block mined! Time: {self.mining_time:.2f}s")
        logger.info(f"   Nonce: {self.nonce:,} | Hash: {self.hash}")
        return True

    def to_dict(self):
        """Convert to server format"""
        return {
            "hash": self.hash,
            "index": self.index,
            "nonce": self.nonce,
            "previous_hash": self.previous_hash,  # This should be the ACTUAL previous block hash
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "miner": self.miner,
        }


class SmartMiner:
    """Miner that uses the correct previous hash and handles transfers/rewards"""

    def __init__(self, miner_address):
        self.miner_address = miner_address
        self.is_mining = False
        self.is_transferring = False
        self.blocks_mined = 0
        self.wallets = self.create_wallets()
        self.rewards_earned = 0.0
        self.transfers_submitted = 0
        self.mining_thread = None
        self.transfer_threads = []
        self.stats_lock = threading.Lock()

    def create_wallets(self):
        """Create multiple wallets for testing transfers"""
        wallets = {}
        for i in range(NUM_WALLETS):
            wallet_name = f"wallet_{i}"
            wallets[wallet_name] = Wallet(wallet_name)
            # Give initial balance for testing
            wallets[wallet_name].balance = 100.0
        return wallets

    def create_reward_transaction(self, amount, block_height):
        """Create mining reward transaction that passes server validation"""
        reward_amount = float(amount)

        # FIXED: Include ALL required fields from server validation
        reward_tx = {
            "type": "reward",
            "to": self.miner_address,
            "amount": reward_amount,
            "timestamp": time.time(),
            "block_height": block_height,
            "miner": self.miner_address,  # REQUIRED FIELD - was missing!
            "description": f"Mining reward for block {block_height}",
        }

        # Calculate hash for the reward transaction (must be done AFTER all fields are set)
        reward_string = json.dumps(reward_tx, sort_keys=True)
        reward_tx["hash"] = hashlib.sha256(reward_string.encode()).hexdigest()

        logger.info(f"💰 Created reward: {reward_amount} LUN for {self.miner_address}")
        logger.debug(f"🔍 Reward transaction fields: {list(reward_tx.keys())}")
        return reward_tx

    def submit_transfer_to_mempool(self, transfer_tx):
        """Submit a transfer transaction to mempool"""
        try:
            response = requests.post(ENDPOINT_MEMPOOL_ADD, json=transfer_tx, timeout=10)
            if response.status_code == 201:
                result = response.json()
                if result.get("success"):
                    with self.stats_lock:
                        self.transfers_submitted += 1
                    logger.info(
                        f"📤 Transfer submitted: {transfer_tx['from'][:8]} → {transfer_tx['to'][:8]} ({transfer_tx['amount']} LUN)"
                    )
                    return True
                else:
                    logger.warning(
                        f"❌ Transfer rejected: {result.get('error', 'Unknown error')}"
                    )
            else:
                logger.warning(f"❌ HTTP {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"💥 Transfer submission error: {e}")

        return False

    def generate_random_transfer(self):
        """Generate a random transfer between wallets - thread-safe"""
        if len(self.wallets) < 2:
            return None

        # Pick random sender and receiver
        with wallet_lock:
            sender_name, receiver_name = random.sample(list(self.wallets.keys()), 2)
            sender = self.wallets[sender_name]
            receiver = self.wallets[receiver_name]

        # Create transfer (this handles its own locking)
        transfer_tx = sender.create_transfer(
            receiver.address, 1.0
        )  # Fixed small amount for testing

        if transfer_tx and self.submit_transfer_to_mempool(transfer_tx):
            logger.info(f"🔄 Transfer: {sender_name} → {receiver_name} (1.0 LUN)")
            return transfer_tx

        return None

    def transfer_worker(self, worker_id):
        """Worker thread that continuously generates transfers"""
        logger.info(f"🔄 Transfer worker {worker_id} started")

        while self.is_transferring:
            try:
                # Generate transfer with random delay
                self.generate_random_transfer()

                # Random delay between transfers (1-5 seconds)
                delay = random.uniform(1, 5)
                time.sleep(delay)

            except Exception as e:
                logger.error(f"💥 Transfer worker {worker_id} error: {e}")
                time.sleep(5)  # Wait before retrying

    def start_transfer_generation(self):
        """Start multiple transfer generation threads"""
        self.is_transferring = True
        self.transfer_threads = []

        for i in range(NUM_TRANSFER_THREADS):
            thread = threading.Thread(
                target=self.transfer_worker,
                args=(i,),
                daemon=True,
                name=f"TransferWorker-{i}",
            )
            thread.start()
            self.transfer_threads.append(thread)
            logger.info(f"🚀 Started transfer worker {i}")

        logger.info(f"🎯 Started {NUM_TRANSFER_THREADS} transfer workers")

    def stop_transfer_generation(self):
        """Stop all transfer generation threads"""
        self.is_transferring = False
        for thread in self.transfer_threads:
            thread.join(timeout=5)
        logger.info("🛑 All transfer workers stopped")

    def get_mempool_transactions(self):
        """Get transactions from mempool"""
        try:
            response = requests.get(ENDPOINT_MEMPOOL_STATUS, timeout=10)
            if response.status_code == 200:
                data = response.json()
                transactions = data.get("status", {}).get("transactions", [])

                # Filter valid transaction types
                valid_txs = []
                for tx in transactions:
                    tx_type = tx.get("type")
                    if tx_type in ["transfer", "GTX_Genesis"]:
                        valid_txs.append(tx)

                logger.info(
                    f"📥 Using {len(valid_txs)}/{len(transactions)} valid mempool transactions"
                )
                return valid_txs[:10]  # Limit to 10 transactions

        except Exception as e:
            logger.error(f"❌ Mempool error: {e}")
        return []

    def validate_reward_transaction(self, reward_tx, block_index):
        """Validate reward transaction against server requirements"""
        required_fields = ["to", "amount", "timestamp", "block_height", "miner"]
        missing_fields = [field for field in required_fields if field not in reward_tx]

        if missing_fields:
            logger.error(f"❌ Reward transaction missing fields: {missing_fields}")
            return False

        # Check block_height matches
        if reward_tx.get("block_height") != block_index:
            logger.error(
                f"❌ Reward block_height mismatch: {reward_tx.get('block_height')} vs {block_index}"
            )
            return False

        # Check amount is reasonable
        amount = reward_tx.get("amount", 0)
        if amount <= 0 or amount > 1000:  # Same limits as server
            logger.error(f"❌ Invalid reward amount: {amount}")
            return False

        logger.info(f"✅ Reward transaction validated for block {block_index}")
        return True

    def validate_transactions_for_block(self, transactions, block_index):
        """Validate transactions before including in block"""
        valid_transactions = []

        for tx in transactions:
            tx_type = tx.get("type")

            if tx_type == "reward":
                # Validate reward transaction specifically
                if self.validate_reward_transaction(tx, block_index):
                    valid_transactions.append(tx)
                else:
                    logger.warning(f"⚠️ Invalid reward transaction: {tx}")

            elif tx_type == "transfer":
                # Basic transfer validation
                if (
                    tx.get("from")
                    and tx.get("to")
                    and tx.get("amount", 0) > 0
                    and tx.get("signature")
                ):
                    valid_transactions.append(tx)
                else:
                    logger.warning(f"⚠️ Invalid transfer transaction: {tx}")

            else:
                # Other transaction types (GTX_Genesis, etc.)
                valid_transactions.append(tx)

        return valid_transactions

    def mine_and_submit(self):
        """Complete mining process - WITH CORRECT PREVIOUS HASH"""
        try:
            # Get the CORRECT next block info with ACTUAL previous hash
            block_info = BlockchainState.get_next_block_info()
            next_index = block_info["next_index"]
            previous_hash = block_info["previous_hash"]  # This is now the ACTUAL hash
            difficulty = block_info["difficulty"]

            logger.info(f"🔗 Mining block #{next_index}")
            logger.info(f"   Previous hash: {previous_hash[:16]}...")
            logger.info(f"   Difficulty: {difficulty}")

            # Don't mine if we're at genesis and it already exists
            if next_index == 0:
                logger.info("⏭️  Genesis block already exists, skipping...")
                return False

            # Get transactions from mempool
            mempool_txs = self.get_mempool_transactions()

            # Create reward transaction (FIXED: includes all required fields)
            total_fees = sum(
                tx.get("fee", 0) for tx in mempool_txs if tx.get("type") == "transfer"
            )
            reward_amount = BASE_MINING_REWARD + total_fees
            reward_tx = self.create_reward_transaction(reward_amount, next_index)

            # Validate the reward transaction before proceeding
            if not self.validate_reward_transaction(reward_tx, next_index):
                logger.error(
                    "❌ Reward transaction validation failed, cannot mine block"
                )
                return False

            # Combine transactions and validate
            all_transactions = [reward_tx] + mempool_txs
            valid_transactions = self.validate_transactions_for_block(
                all_transactions, next_index
            )

            logger.info(
                f"📄 Block transactions: {len(valid_transactions)} total ({len(mempool_txs)} mempool + 1 reward)"
            )

            # Create and mine block with CORRECT previous hash
            block = RealBlock(
                next_index, previous_hash, valid_transactions, miner=self.miner_address
            )

            logger.info(f"⛏️ Starting mining of block #{next_index}")
            if block.mine_block(difficulty):
                # Verify the hash before submitting
                verify_hash = block.calculate_hash()
                if verify_hash != block.hash:
                    logger.error(
                        f"❌ Hash verification failed: {block.hash} vs {verify_hash}"
                    )
                    return False

                block_data = block.to_dict()
                logger.info(f"📤 Submitting block #{next_index}")
                logger.info(f"   Block hash: {block.hash[:16]}...")
                logger.info(f"   Previous hash: {block.previous_hash[:16]}...")
                logger.info(f"   Transactions: {len(valid_transactions)}")

                if self.submit_block(block_data):
                    with self.stats_lock:
                        self.blocks_mined += 1
                        self.rewards_earned += reward_amount

                    # Update local wallet balances based on mined transactions
                    self.update_local_balances(valid_transactions)

                    logger.info(f"🎉 SUCCESS! Block #{next_index} accepted")
                    logger.info(f"💰 Total rewards: {self.rewards_earned:.2f} LUN")
                    return True
                else:
                    logger.error(f"❌ Failed to submit block #{next_index}")
            else:
                logger.error(f"❌ Failed to mine block #{next_index}")

            return False

        except Exception as e:
            logger.error(f"💥 Mining error: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return False

    def update_local_balances(self, transactions):
        """Update local wallet balances after successful block mining"""
        for tx in transactions:
            tx_type = tx.get("type")

            if tx_type == "transfer":
                from_addr = tx.get("from")
                to_addr = tx.get("to")
                amount = tx.get("amount", 0)
                fee = tx.get("fee", TRANSACTION_FEE)

                # Find wallets involved
                for wallet in self.wallets.values():
                    if wallet.address == from_addr:
                        wallet.balance -= amount + fee
                    elif wallet.address == to_addr:
                        wallet.balance += amount

            elif tx_type == "reward":
                to_addr = tx.get("to")
                amount = tx.get("amount", 0)

                # Add reward to miner's wallet if we have it
                for wallet in self.wallets.values():
                    if wallet.address == to_addr:
                        wallet.balance += amount

    def submit_block(self, block_data):
        """Submit block to blockchain"""
        try:
            response = requests.post(ENDPOINT_SUBMIT_BLOCK, json=block_data, timeout=30)

            if response.status_code in [200, 201]:
                result = response.json()
                if result.get("success"):
                    status = result.get("status", "added")

                    if status == "already_exists":
                        logger.info("⏭️  Block already exists in blockchain")
                        return True  # Still count as success
                    else:
                        return True
                else:
                    error_msg = result.get("error", "Unknown error")
                    logger.warning(f"❌ Block rejected: {error_msg}")
            else:
                logger.warning(f"❌ HTTP {response.status_code}: {response.text}")

        except Exception as e:
            logger.error(f"💥 Submission error: {e}")

        return False

    def mining_worker(self):
        """Mining worker thread"""
        logger.info("⛏️ Mining worker started")

        consecutive_failures = 0

        while self.is_mining:
            # Mine and submit block
            success = self.mine_and_submit()

            if success:
                consecutive_failures = 0
                time.sleep(10)  # Wait before next block
            else:
                consecutive_failures += 1
                if consecutive_failures >= 3:
                    logger.warning("💤 Multiple failures, taking longer break...")
                    time.sleep(30)
                    consecutive_failures = 0
                else:
                    time.sleep(15)

    def start_mining(self):
        """Start mining in a separate thread"""
        self.is_mining = True
        self.mining_thread = threading.Thread(
            target=self.mining_worker, daemon=True, name="MiningWorker"
        )
        self.mining_thread.start()
        logger.info("🚀 Mining worker started")

    def stop_mining(self):
        """Stop mining thread"""
        self.is_mining = False
        if self.mining_thread:
            self.mining_thread.join(timeout=10)
        logger.info("🛑 Mining worker stopped")

    def start_all_workers(self):
        """Start both mining and transfer workers"""
        logger.info("🎯 Starting all workers...")

        # Start transfer generation first to populate mempool
        self.start_transfer_generation()
        time.sleep(2)  # Let transfers start flowing

        # Start mining
        self.start_mining()

        logger.info(
            "✅ All workers started - Mining and transfers running concurrently!"
        )

    def consolidate_wallets(self, target_address):
        """Consolidate all wallet balances to a single target address"""
        logger.info(f"💰 Consolidating all wallet balances to: {target_address}")

        total_consolidated = 0.0
        successful_transfers = 0

        # Create consolidation transactions for each wallet with balance
        for wallet_name, wallet in self.wallets.items():
            if wallet.balance > TRANSACTION_FEE:  # Need enough for fee
                transfer_amount = wallet.balance - TRANSACTION_FEE

                if transfer_amount > 0:
                    transfer_tx = wallet.create_transfer(
                        target_address, transfer_amount
                    )

                    if transfer_tx and self.submit_transfer_to_mempool(transfer_tx):
                        total_consolidated += transfer_amount
                        successful_transfers += 1
                        logger.info(
                            f"   ✅ {wallet_name}: {transfer_amount:.2f} LUN → {target_address[:16]}..."
                        )
                    else:
                        logger.warning(f"   ❌ Failed to transfer from {wallet_name}")

        logger.info(
            f"📊 Consolidation complete: {successful_transfers} wallets, {total_consolidated:.2f} LUN total"
        )
        return total_consolidated, successful_transfers

    def stop_all_workers(self):
        """Stop all workers"""
        logger.info("🛑 Stopping all workers...")
        self.stop_mining()
        self.stop_transfer_generation()

        with self.stats_lock:
            logger.info(f"📊 Final Stats:")
            logger.info(f"   Blocks mined: {self.blocks_mined}")
            logger.info(f"   Transfers submitted: {self.transfers_submitted}")
            logger.info(f"   Total rewards: {self.rewards_earned:.2f} LUN")

        # Display final wallet balances
        logger.info("💼 Final wallet balances:")
        for name, wallet in self.wallets.items():
            logger.info(f"   {name}: {wallet.balance:.2f} LUN")

    def print_stats(self):
        """Print current statistics"""
        with self.stats_lock:
            logger.info(f"📊 Current Stats:")
            logger.info(f"   Blocks mined: {self.blocks_mined}")
            logger.info(f"   Transfers submitted: {self.transfers_submitted}")
            logger.info(f"   Total rewards: {self.rewards_earned:.2f} LUN")
            logger.info(
                f"   Active transfer workers: {len([t for t in self.transfer_threads if t.is_alive()])}"
            )


def debug_server_state():
    """Debug the server's current state"""
    logger.info("🔍 Debugging server state...")

    try:
        # Check blockchain status
        status_response = requests.get(ENDPOINT_BLOCKCHAIN_STATUS, timeout=10)
        if status_response.status_code == 200:
            status_data = status_response.json()
            status_info = status_data.get("status", {})
            logger.info(
                f"📊 STATUS: blocks={status_info.get('blocks')}, latest_hash={status_info.get('latest_hash', '')[:16]}..."
            )

        # Check actual blockchain
        blockchain_response = requests.get(f"{BASE_URL}/blockchain", timeout=10)
        if blockchain_response.status_code == 200:
            blockchain_data = blockchain_response.json()
            logger.info(f"📊 BLOCKCHAIN: {len(blockchain_data)} actual blocks")

            for i, block in enumerate(blockchain_data):
                logger.info(
                    f"   Block {i}: index={block.get('index')}, hash={block.get('hash', '')[:16]}..."
                )

        # Check mempool
        mempool_response = requests.get(ENDPOINT_MEMPOOL_STATUS, timeout=10)
        if mempool_response.status_code == 200:
            mempool_data = mempool_response.json()
            mempool_info = mempool_data.get("status", {})
            logger.info(f"📊 MEMPOOL: {mempool_info.get('total', 0)} transactions")

        return True

    except Exception as e:
        logger.error(f"❌ Debug error: {e}")
        return False


def stats_monitor(miner):
    """Monitor thread to periodically print statistics"""
    while miner.is_mining or miner.is_transferring:
        miner.print_stats()
        time.sleep(30)  # Print stats every 30 seconds


def ask_consolidation(miner):
    """Ask user if they want to consolidate wallet balances"""
    print("\n" + "=" * 60)
    print("💰 WALLET CONSOLIDATION")
    print("=" * 60)

    # Show current wallet balances
    total_balance = sum(wallet.balance for wallet in miner.wallets.values())
    print(f"📊 Total balance across all wallets: {total_balance:.2f} LUN")

    while True:
        response = (
            input(
                "\nDo you want to consolidate all wallet balances to one address? (y/N): "
            )
            .strip()
            .lower()
        )

        if response in ["", "n", "no"]:
            print("Skipping wallet consolidation.")
            return False
        elif response in ["y", "yes"]:
            target_address = input("Enter target wallet address: ").strip()

            if not target_address:
                print("❌ No address provided. Skipping consolidation.")
                return False

            print(
                f"\n🔄 Consolidating {len(miner.wallets)} wallets to: {target_address}"
            )
            print("This may take a moment...")

            total_consolidated, successful_transfers = miner.consolidate_wallets(
                target_address
            )

            print(f"\n✅ Consolidation complete!")
            print(f"   Successfully transferred from {successful_transfers} wallets")
            print(f"   Total amount consolidated: {total_consolidated:.2f} LUN")
            print(f"   Target address: {target_address}")

            return True
        else:
            print("❌ Please answer 'y' for yes or 'n' for no.")


def main():
    """Main function"""
    logger.info(
        "🚀 Starting THREADED Luna Miner with Concurrent Transfers and Mining..."
    )

    # Debug the current server state
    debug_server_state()

    # Create a miner with wallets
    miner_address = (
        "threaded_miner_" + hashlib.sha256(str(time.time()).encode()).hexdigest()[:8]
    )
    miner = SmartMiner(miner_address)

    # Start stats monitor
    stats_thread = threading.Thread(
        target=stats_monitor, args=(miner,), daemon=True, name="StatsMonitor"
    )
    stats_thread.start()

    logger.info("🎯 Starting all workers (mining + transfers)...")

    try:
        # Start both mining and transfer workers
        miner.start_all_workers()

        # Keep main thread alive
        while miner.is_mining:
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("🛑 Shutdown requested...")
    finally:
        miner.stop_all_workers()

        # Ask about wallet consolidation
        try:
            ask_consolidation(miner)
        except Exception as e:
            logger.error(f"❌ Error during consolidation: {e}")

        logger.info("👋 All workers stopped. Goodbye!")


if __name__ == "__main__":
    main()
