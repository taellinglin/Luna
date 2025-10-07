import time
import requests


# Colors for console output
class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    END = "\033[0m"


def color_text(text, color):
    return f"{color}{text}{Colors.END}"


class SmartMiner:
    """Miner that uses the correct previous hash and handles reward transactions"""

    def __init__(self, config):
        self.config = config
        self.miner_address = config.miner_address
        self.is_mining = False
        self.blocks_mined = 0

    def is_reward_already_mined(self, reward_tx):
        """Check if a reward transaction has already been mined in the blockchain"""
        try:
            reward_tx_hash = reward_tx.get("hash")
            block_height = reward_tx.get("block_height")
            recipient = reward_tx.get("to")
            amount = reward_tx.get("amount")

            # If no hash, create a signature based on other fields
            if not reward_tx_hash:
                reward_signature = f"{recipient}_{block_height}_{amount}"
            else:
                reward_signature = reward_tx_hash

            # Check if we've already tracked this reward as mined
            for mined_reward in self.config.reward_transactions_mined:
                if mined_reward.get("hash") == reward_signature or (
                    mined_reward.get("recipient") == recipient
                    and mined_reward.get("block_height") == block_height
                    and mined_reward.get("amount") == amount
                ):
                    return True

            # Also check the actual blockchain
            blockchain_response = requests.get(ENDPOINT_BLOCKCHAIN, timeout=10)
            if blockchain_response.status_code == 200:
                blockchain_data = blockchain_response.json()

                for block in blockchain_data:
                    transactions = block.get("transactions", [])
                    for tx in transactions:
                        if tx.get("type") == "reward":
                            # Check multiple ways to identify the same reward
                            if tx.get("hash") == reward_signature or (
                                tx.get("to") == recipient
                                and tx.get("block_height") == block_height
                                and tx.get("amount") == amount
                            ):
                                return True

            return False

        except Exception as e:
            print(color_text(f"❌ Error checking if reward is mined: {e}", Colors.RED))
            return False

    def get_mempool_transactions(self):
        """Get transactions from mempool including reward transactions"""
        try:
            response = requests.get(ENDPOINT_MEMPOOL_STATUS, timeout=10)
            if response.status_code == 200:
                data = response.json()
                transactions = data.get("status", {}).get("transactions", [])

                # Filter valid transaction types
                valid_txs = []
                reward_txs = []

                for tx in transactions:
                    tx_type = tx.get("type")
                    if tx_type in ["transfer", "GTX_Genesis"]:
                        valid_txs.append(tx)
                    elif tx_type == "reward":
                        # Check if this reward hasn't been mined yet
                        if not self.is_reward_already_mined(tx):
                            reward_txs.append(tx)
                        else:
                            print(
                                color_text(
                                    f"⏭️  Skipping already mined reward: {tx.get('to')} for {tx.get('amount')} LUN",
                                    Colors.YELLOW,
                                )
                            )

                print(
                    color_text(
                        f"📥 Using {len(valid_txs)} regular + {len(reward_txs)} unmined reward transactions",
                        Colors.BLUE,
                    )
                )
                return valid_txs + reward_txs[:5]  # Limit reward transactions to 5

        except Exception as e:
            print(color_text(f"❌ Mempool error: {e}", Colors.RED))
        return []

    def scan_for_unmined_rewards(self):
        """Scan blockchain for unmined reward transactions"""
        try:
            print(
                color_text(
                    "🔍 Scanning blockchain for unmined reward transactions...",
                    Colors.BLUE,
                )
            )
            blockchain_response = requests.get(ENDPOINT_BLOCKCHAIN, timeout=10)
            if blockchain_response.status_code == 200:
                blockchain_data = blockchain_response.json()

                unmined_rewards = []
                for block in blockchain_data:
                    transactions = block.get("transactions", [])
                    for tx in transactions:
                        if tx.get("type") == "reward":
                            # Check if this reward hasn't been mined by us yet
                            if not self.is_reward_already_mined(tx):
                                unmined_rewards.append(tx)
                            else:
                                print(
                                    color_text(
                                        f"⏭️  Skipping mined reward in block {block.get('index')}: {tx.get('to')} for {tx.get('amount')} LUN",
                                        Colors.YELLOW,
                                    )
                                )

                print(
                    color_text(
                        f"💰 Found {len(unmined_rewards)} unmined reward transactions",
                        Colors.GREEN,
                    )
                )
                return unmined_rewards

        except Exception as e:
            print(color_text(f"❌ Error scanning for rewards: {e}", Colors.RED))

        return []

    def should_include_reward_transaction(self, reward_tx):
        """Determine if we should include a reward transaction in our block"""
        # Don't include our own reward transactions
        if (
            reward_tx.get("to") == self.miner_address
            or reward_tx.get("miner") == self.miner_address
        ):
            return False

        # Check if reward transaction is already mined
        if self.is_reward_already_mined(reward_tx):
            return False

        return True

    def mark_reward_as_mined(self, reward_tx, block_hash):
        """Mark a reward transaction as mined"""
        try:
            reward_tx_hash = reward_tx.get("hash")
            if not reward_tx_hash:
                # Create a signature if no hash exists
                reward_tx_hash = f"{reward_tx.get('to')}_{reward_tx.get('block_height')}_{reward_tx.get('amount')}"

            # Check if already marked
            already_marked = any(
                r.get("hash") == reward_tx_hash
                for r in self.config.reward_transactions_mined
            )

            if not already_marked:
                reward_data = {
                    "hash": reward_tx_hash,
                    "recipient": reward_tx.get("to"),
                    "amount": reward_tx.get("amount"),
                    "block_height": reward_tx.get("block_height"),
                    "block_hash": block_hash,
                    "timestamp": time.time(),
                    "date": time.strftime("%Y-%m-%d %H:%M:%S"),
                }
                self.config.reward_transactions_mined.append(reward_data)
                self.config.save_config()
                print(
                    color_text(
                        f"✅ Marked reward as mined: {reward_tx.get('to')} for {reward_tx.get('amount')} LUN",
                        Colors.GREEN,
                    )
                )

        except Exception as e:
            print(color_text(f"❌ Error marking reward as mined: {e}", Colors.RED))

    def mine_and_submit(self):
        """Complete mining process - WITH REWARD TRANSACTION SUPPORT"""
        try:
            # Get the CORRECT next block info with ACTUAL previous hash
            block_info = BlockchainState.get_next_block_info()
            next_index = block_info["next_index"]
            previous_hash = block_info["previous_hash"]
            difficulty = block_info["difficulty"]

            print(color_text(f"🔗 Mining block #{next_index}", Colors.CYAN))
            print(color_text(f"   Previous hash: {previous_hash[:16]}...", Colors.BLUE))
            print(color_text(f"   Difficulty: {difficulty}", Colors.YELLOW))

            # Don't mine if we're at genesis and it already exists
            if next_index == 0:
                print(
                    color_text(
                        "⏭️  Genesis block already exists, skipping...", Colors.YELLOW
                    )
                )
                return False

            # Get transactions from mempool (already filters mined rewards)
            mempool_txs = self.get_mempool_transactions()

            # Scan for unmined reward transactions in blockchain
            unmined_rewards = self.scan_for_unmined_rewards()

            # Combine all transactions
            all_external_txs = mempool_txs + unmined_rewards
            transaction_count = len(all_external_txs)

            # Calculate total reward
            base_reward = self.config.mining_reward
            fee_reward = transaction_count * self.config.transaction_fee
            total_reward = base_reward + fee_reward

            # Create our mining reward transaction
            our_reward_tx = self.create_reward_transaction(
                total_reward, next_index, transaction_count
            )

            # Combine transactions (our reward first, then others)
            all_transactions = [our_reward_tx] + all_external_txs

            print(
                color_text(
                    f"💰 Total reward: {total_reward} LUN ({base_reward} base + {fee_reward} fees)",
                    Colors.YELLOW,
                )
            )
            print(
                color_text(
                    f"📊 Transactions: {transaction_count} external + 1 reward",
                    Colors.BLUE,
                )
            )

            # Create and mine block with CORRECT previous hash
            block = RealBlock(
                next_index, previous_hash, all_transactions, miner=self.miner_address
            )

            print(color_text(f"⛏️ Starting mining of block #{next_index}", Colors.CYAN))
            if block.mine_block(difficulty):
                # Verify the hash before submitting
                verify_hash = block.calculate_hash()
                if verify_hash != block.hash:
                    print(
                        color_text(
                            f"❌ Hash verification failed: {block.hash} vs {verify_hash}",
                            Colors.RED,
                        )
                    )
                    return False

                block_data = block.to_dict()
                print(color_text(f"📤 Submitting block #{next_index}", Colors.BLUE))

                if self.submit_block(block_data):
                    self.blocks_mined += 1

                    # Add to mining history
                    self.config.add_bill(
                        block.hash,
                        total_reward,
                        transaction_count,
                        our_reward_tx["hash"],
                    )

                    # Track our reward transaction
                    self.config.add_reward_transaction(
                        our_reward_tx["hash"], total_reward, block.hash
                    )

                    # Mark all external reward transactions as mined
                    for tx in all_external_txs:
                        if tx.get("type") == "reward":
                            self.mark_reward_as_mined(tx, block.hash)

                    print(
                        color_text(
                            f"🎉 SUCCESS! Block #{next_index} accepted", Colors.GREEN
                        )
                    )
                    print(color_text(f"💰 Reward: {total_reward} LUN", Colors.YELLOW))
                    print(
                        color_text(f"📊 Transactions: {transaction_count}", Colors.BLUE)
                    )
                    print(color_text(f"⏱️  Time: {block.mining_time:.2f}s", Colors.CYAN))
                    print(
                        color_text(
                            f"🎯 Reward TX: {our_reward_tx['hash'][:16]}...",
                            Colors.MAGENTA,
                        )
                    )
                    return True
                else:
                    print(
                        color_text(
                            f"❌ Failed to submit block #{next_index}", Colors.RED
                        )
                    )
            else:
                print(color_text(f"❌ Failed to mine block #{next_index}", Colors.RED))

            return False

        except Exception as e:
            print(color_text(f"💥 Mining error: {e}", Colors.RED))
            return False

    def submit_block(self, block_data):
        """Submit mined block to the API"""
        try:
            print(color_text("📤 Submitting block to API...", COLORS["B"]))

            # Submit to the blockchain API endpoint
            response = requests.post(
                f"{self.config.api_base_url}/blockchain/submit-block",
                json=block_data,
                timeout=30,
            )

            if response.status_code == 201:
                result = response.json()
                if result.get("success"):
                    print(color_text("✅ Block submitted successfully!", COLORS["G"]))
                    return True
                else:
                    error_msg = result.get("error", "Unknown error")
                    print(color_text(f"❌ Block rejected: {error_msg}", COLORS["R"]))
            else:
                print(
                    color_text(
                        f"❌ HTTP {response.status_code}: {response.text}", COLORS["R"]
                    )
                )

        except Exception as e:
            print(color_text(f"💥 Submission error: {e}", COLORS["R"]))

        return False

    def create_reward_transaction(self, amount, block_height, transaction_count=0):
        """Create mining reward transaction with proper structure"""
        # Generate a unique hash for this reward transaction
        reward_data = f"reward_{self.miner_address}_{amount}_{block_height}_{transaction_count}_{time.time()}"
        reward_tx_hash = hashlib.sha256(reward_data.encode()).hexdigest()

        return {
            "type": "reward",
            "to": self.miner_address,
            "amount": float(amount),
            "timestamp": time.time(),
            "block_height": int(block_height),
            "description": f"Mining reward for block {block_height} with {transaction_count} transactions",
            "transactions_included": transaction_count,
            "miner": self.miner_address,
            "fee_reward": float(transaction_count * self.config.transaction_fee),
            "hash": reward_tx_hash,
            "signature": f"reward_{reward_tx_hash[:16]}",
        }

    def start_auto_mining(self):
        """Start auto-mining loop"""
        self.is_mining = True
        print(color_text(f"🚀 Starting auto-miner: {self.miner_address}", Colors.GREEN))

        consecutive_failures = 0

        while self.is_mining:
            success = self.mine_and_submit()

            if success:
                consecutive_failures = 0
                time.sleep(10)  # Wait before next block
            else:
                consecutive_failures += 1
                if consecutive_failures >= 3:
                    print(
                        color_text(
                            "💤 Multiple failures, taking longer break...",
                            Colors.YELLOW,
                        )
                    )
                    time.sleep(30)
                    consecutive_failures = 0
                else:
                    time.sleep(15)

    def stop_mining(self):
        self.is_mining = False
        print(
            color_text(
                f"🛑 Miner stopped. Blocks mined: {self.blocks_mined}", Colors.YELLOW
            )
        )
