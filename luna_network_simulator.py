# luna_network_simulator.py
#!/usr/bin/env python3
"""
Luna Network Simulator - Simulates a network of miners working together
"""

import os
import sys
import json
import time
import threading
import random
import tempfile

# Add current directory to path to import Luna modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ROYGBIV Color Scheme 🌈
COLORS = {
    "R": "\033[91m",
    "O": "\033[93m",
    "Y": "\033[93m",
    "G": "\033[92m",
    "B": "\033[94m",
    "I": "\033[95m",
    "V": "\033[95m",
    "X": "\033[0m",
    "BOLD": "\033[1m",
}


def color_text(text, color_code):
    return f"{color_code}{text}{COLORS['X']}"


class NetworkConfig:
    """Configuration for the simulated network"""

    def __init__(self):
        self.num_miners = 5
        self.num_wallets = 3
        self.simulation_duration = 300  # 5 minutes
        self.target_address = "LUN_network_pool_1234"  # All miners mine to this address
        self.base_port = 9333
        self.api_base_url = "https://bank.linglin.art"
        self.mining_interval_min = 10  # seconds
        self.mining_interval_max = 30  # seconds
        self.sync_interval = 15  # seconds


class SimulatedMiner:
    """A simulated miner node"""

    def __init__(self, miner_id: int, config: NetworkConfig, data_dir: str):
        self.miner_id = miner_id
        self.config = config
        self.data_dir = data_dir
        self.node = None
        self.running = False
        self.thread = None
        self.blocks_mined = 0
        self.total_reward = 0

        # Create miner-specific data directory
        self.miner_data_dir = os.path.join(data_dir, f"miner_{miner_id}")
        os.makedirs(self.miner_data_dir, exist_ok=True)

        # Initialize node configuration
        self.setup_miner_config()

    def setup_miner_config(self):
        """Set up the miner's configuration"""
        config_path = os.path.join(self.miner_data_dir, "node_config.json")

        miner_config = {
            "node_id": f"simulated_miner_{self.miner_id}",
            "miner_address": self.config.target_address,  # All miners use same address
            "difficulty": 3,  # Lower difficulty for faster simulation
            "mining_reward": 1.0,
            "node_version": "1.0.0",
            "created_at": time.time(),
            "last_sync": 0,
            "bills_mined": [],
            "verification_links": {},
            "auto_mine": True,  # Enable auto-mining
            "peer_port": self.config.base_port + self.miner_id,
            "mined_transactions": {},
            "api_base_url": self.config.api_base_url,
            "mempool_file": "mempool.json",
            "last_mempool_sync": 0,
        }

        with open(config_path, "w") as f:
            json.dump(miner_config, f, indent=2)

    def start(self):
        """Start the miner node"""
        try:
            # Import here to avoid circular imports
            from luna_node import LunaNode

            # Change to miner's data directory
            original_dir = os.getcwd()
            os.chdir(self.miner_data_dir)

            # Initialize the node
            self.node = LunaNode()
            self.running = True

            # Start mining thread
            self.thread = threading.Thread(target=self._mining_worker, daemon=True)
            self.thread.start()

            # Return to original directory
            os.chdir(original_dir)

            print(
                color_text(
                    f"⛏️  Miner {self.miner_id} started successfully", COLORS["G"]
                )
            )
            return True

        except Exception as e:
            print(
                color_text(
                    f"❌ Failed to start miner {self.miner_id}: {e}", COLORS["R"]
                )
            )
            return False

    def _mining_worker(self):
        """Background worker that periodically mines blocks"""
        while self.running:
            try:
                # Random interval between mining attempts
                interval = random.randint(
                    self.config.mining_interval_min, self.config.mining_interval_max
                )
                time.sleep(interval)

                if self.node and self.running:
                    # Sync with network first
                    self.sync_with_network()

                    # Attempt to mine a block
                    if self.mine_block():
                        self.blocks_mined += 1
                        print(
                            color_text(
                                f"💰 Miner {self.miner_id} mined block #{self.blocks_mined}",
                                COLORS["G"],
                            )
                        )

            except Exception as e:
                print(color_text(f"❌ Miner {self.miner_id} error: {e}", COLORS["R"]))
                time.sleep(10)  # Wait before retrying

    def sync_with_network(self):
        """Sync this miner with the network"""
        try:
            if self.node:
                # Sync blockchain
                self.node.blockchain.sync_from_web()

                # Sync mempool
                self.node.blockchain.sync_mempool_from_api()

        except Exception as e:
            print(color_text(f"⚠️  Miner {self.miner_id} sync error: {e}", COLORS["O"]))

    def mine_block(self):
        """Mine a block using the node's functionality"""
        try:
            if self.node:
                # Use the mempool mining function
                return self.node.mine_from_mempool()
        except Exception as e:
            print(
                color_text(f"❌ Miner {self.miner_id} mining error: {e}", COLORS["R"])
            )
        return False

    def stop(self):
        """Stop the miner"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print(color_text(f"⏹️  Miner {self.miner_id} stopped", COLORS["O"]))

    def get_status(self):
        """Get miner status"""
        if self.node:
            return {
                "miner_id": self.miner_id,
                "blocks_mined": self.blocks_mined,
                "total_reward": self.total_reward,
                "chain_length": self.node.blockchain.get_chain_length(),
                "mempool_size": len(self.node.blockchain.mempool),
                "is_running": self.running,
            }
        return {
            "miner_id": self.miner_id,
            "blocks_mined": self.blocks_mined,
            "total_reward": self.total_reward,
            "is_running": self.running,
        }


class SimulatedWallet:
    """A simulated wallet for network participants"""

    def __init__(self, wallet_id: int, config: NetworkConfig, data_dir: str):
        self.wallet_id = wallet_id
        self.config = config
        self.data_dir = data_dir
        self.wallet = None
        self.address = f"LKC_sim_user_{wallet_id}_{random.randint(1000, 9999)}"
        self.balance = 0
        self.transactions_sent = 0

        # Create wallet-specific data directory
        self.wallet_data_dir = os.path.join(data_dir, f"wallet_{wallet_id}")
        os.makedirs(self.wallet_data_dir, exist_ok=True)

    def start(self):
        """Initialize the wallet"""
        try:
            from luna_wallet import LunaWallet, DataManager

            # Patch DataManager to use wallet-specific directory
            original_get_data_dir = DataManager.get_data_dir
            DataManager.get_data_dir = lambda: self.wallet_data_dir

            # Initialize wallet
            self.wallet = LunaWallet()

            # Create a specific address for this wallet
            self.address = self.wallet.addresses[0]["address"]

            # Restore original function
            DataManager.get_data_dir = original_get_data_dir

            print(
                color_text(
                    f"👛 Wallet {self.wallet_id} initialized: {self.address}",
                    COLORS["B"],
                )
            )
            return True

        except Exception as e:
            print(
                color_text(
                    f"❌ Failed to initialize wallet {self.wallet_id}: {e}", COLORS["R"]
                )
            )
            return False

    def simulate_activity(self):
        """Simulate wallet activity (sending transactions)"""
        if not self.wallet or random.random() < 0.7:  # 30% chance of activity
            return False

        try:
            # Send to a random wallet (including possibly ourselves)
            target_wallet = f"LKC_sim_user_{random.randint(1, self.config.num_wallets)}"
            amount = random.uniform(0.1, 5.0)

            # Sync first
            self.wallet.sync_with_node()

            # Send transaction
            if self.wallet.send(
                target_wallet, amount, f"Simulated tx #{self.transactions_sent}"
            ):
                self.transactions_sent += 1
                print(
                    color_text(
                        f"💸 Wallet {self.wallet_id} sent {amount} LKC to {target_wallet}",
                        COLORS["Y"],
                    )
                )
                return True

        except Exception as e:
            print(
                color_text(
                    f"❌ Wallet {self.wallet_id} transaction error: {e}", COLORS["R"]
                )
            )

        return False


class NetworkMonitor:
    """Monitors the entire network"""

    def __init__(self, network):
        self.network = network
        self.running = False
        self.thread = None
        self.start_time = time.time()

    def start(self):
        """Start monitoring"""
        self.running = True
        self.thread = threading.Thread(target=self._monitoring_worker, daemon=True)
        self.thread.start()
        print(color_text("📊 Network monitor started", COLORS["B"]))

    def _monitoring_worker(self):
        """Background monitoring worker"""
        while self.running:
            self.display_network_status()
            time.sleep(10)  # Update every 10 seconds

    def display_network_status(self):
        """Display current network status"""
        elapsed = time.time() - self.start_time
        miners = self.network.miners
        wallets = self.network.wallets

        # Calculate totals
        total_blocks = sum(m.blocks_mined for m in miners if m.running)
        active_miners = sum(1 for m in miners if m.running)
        total_transactions = sum(w.transactions_sent for w in wallets)

        print(color_text("\n" + "=" * 80, COLORS["I"]))
        print(color_text("🌐 LUNA NETWORK SIMULATION STATUS", COLORS["BOLD"]))
        print(color_text("=" * 80, COLORS["I"]))
        print(
            color_text(
                f"⏱️  Elapsed Time: {elapsed:.0f}s | Active Miners: {active_miners}/{len(miners)}",
                COLORS["B"],
            )
        )
        print(
            color_text(
                f"⛏️  Total Blocks Mined: {total_blocks} | 💰 Transactions Sent: {total_transactions}",
                COLORS["G"],
            )
        )

        # Miner status
        print(color_text("\n⛏️  MINERS:", COLORS["BOLD"]))
        for miner in miners:
            status = miner.get_status()
            status_icon = "🟢" if status["is_running"] else "🔴"
            print(
                color_text(
                    f"  {status_icon} Miner {miner.miner_id}: {status['blocks_mined']} blocks | "
                    f"Chain: {status.get('chain_length', 'N/A')} | "
                    f"Mempool: {status.get('mempool_size', 'N/A')}",
                    COLORS["G"] if status["is_running"] else COLORS["R"],
                )
            )

        # Wallet status
        print(color_text("\n👛 WALLETS:", COLORS["BOLD"]))
        for wallet in wallets:
            print(
                color_text(
                    f"  👤 Wallet {wallet.wallet_id}: {wallet.transactions_sent} txs | "
                    f"Address: {wallet.address[:20]}...",
                    COLORS["B"],
                )
            )

        print(color_text("=" * 80, COLORS["I"]))

    def stop(self):
        """Stop monitoring"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)


class LunaNetworkSimulator:
    """Main network simulator class"""

    def __init__(self, config: NetworkConfig = None):
        self.config = config or NetworkConfig()
        self.miners = []
        self.wallets = []
        self.monitor = None
        self.network_dir = tempfile.mkdtemp(prefix="luna_network_")

        print(color_text("🌐 Luna Network Simulator Initialized", COLORS["I"]))
        print(color_text(f"📁 Network data directory: {self.network_dir}", COLORS["B"]))
        print(
            color_text(
                f"⛏️  Miners: {self.config.num_miners} | 👛 Wallets: {self.config.num_wallets}",
                COLORS["G"],
            )
        )
        print(
            color_text(f"🎯 Target address: {self.config.target_address}", COLORS["Y"])
        )

    def setup_network(self):
        """Set up the network of miners and wallets"""
        print(color_text("\n🚀 Setting up network...", COLORS["BOLD"]))

        # Create miners
        for i in range(self.config.num_miners):
            miner = SimulatedMiner(i + 1, self.config, self.network_dir)
            self.miners.append(miner)
            print(color_text(f"  Created miner {i + 1}", COLORS["G"]))

        # Create wallets
        for i in range(self.config.num_wallets):
            wallet = SimulatedWallet(i + 1, self.config, self.network_dir)
            self.wallets.append(wallet)
            print(color_text(f"  Created wallet {i + 1}", COLORS["B"]))

        print(color_text("✅ Network setup completed", COLORS["G"]))

    def start_network(self):
        """Start the entire network"""
        print(color_text("\n🎬 Starting network...", COLORS["BOLD"]))

        # Start miners
        successful_starts = 0
        for miner in self.miners:
            if miner.start():
                successful_starts += 1
            time.sleep(1)  # Stagger starts

        # Initialize wallets
        for wallet in self.wallets:
            wallet.start()

        # Start network monitor
        self.monitor = NetworkMonitor(self)
        self.monitor.start()

        print(
            color_text(
                f"✅ Network started with {successful_starts}/{len(self.miners)} miners",
                COLORS["G"],
            )
        )
        return successful_starts > 0

    def run_simulation(self, duration=None):
        """Run the simulation for specified duration"""
        if duration is None:
            duration = self.config.simulation_duration

        print(
            color_text(
                f"\n⏱️  Running simulation for {duration} seconds...", COLORS["BOLD"]
            )
        )
        print(color_text("💡 Press Ctrl+C to stop early", COLORS["Y"]))

        start_time = time.time()
        end_time = start_time + duration

        try:
            while time.time() < end_time:
                # Simulate wallet activity
                for wallet in self.wallets:
                    wallet.simulate_activity()

                # Wait before next activity cycle
                time.sleep(5)

                # Display progress
                elapsed = time.time() - start_time
                remaining = duration - elapsed
                if remaining > 0 and int(elapsed) % 30 == 0:  # Every 30 seconds
                    print(
                        color_text(
                            f"⏳ Simulation progress: {elapsed:.0f}s / {duration}s ({elapsed / duration * 100:.1f}%)",
                            COLORS["I"],
                        )
                    )

        except KeyboardInterrupt:
            print(color_text("\n🛑 Simulation interrupted by user", COLORS["R"]))

        finally:
            self.stop_network()

    def stop_network(self):
        """Stop the entire network"""
        print(color_text("\n🛑 Stopping network...", COLORS["BOLD"]))

        # Stop monitor first
        if self.monitor:
            self.monitor.stop()

        # Stop miners
        for miner in self.miners:
            miner.stop()

        # Final status report
        self.generate_final_report()

        print(color_text("✅ Network stopped", COLORS["G"]))

    def generate_final_report(self):
        """Generate a final simulation report"""
        print(color_text("\n" + "=" * 80, COLORS["I"]))
        print(color_text("📊 SIMULATION FINAL REPORT", COLORS["BOLD"]))
        print(color_text("=" * 80, COLORS["I"]))

        total_blocks = sum(m.blocks_mined for m in self.miners)
        total_transactions = sum(w.transactions_sent for w in self.wallets)
        active_miners = sum(1 for m in self.miners if m.running)

        print(color_text(f"⛏️  TOTAL BLOCKS MINED: {total_blocks}", COLORS["G"]))
        print(color_text(f"💸 TOTAL TRANSACTIONS: {total_transactions}", COLORS["Y"]))
        print(
            color_text(
                f"👥 ACTIVE MINERS: {active_miners}/{len(self.miners)}", COLORS["B"]
            )
        )

        # Individual miner performance
        print(color_text("\n🏆 MINER PERFORMANCE:", COLORS["BOLD"]))
        for miner in sorted(self.miners, key=lambda m: m.blocks_mined, reverse=True):
            status = miner.get_status()
            print(
                color_text(
                    f"  #{miner.miner_id}: {status['blocks_mined']} blocks | "
                    f"Chain length: {status.get('chain_length', 'N/A')}",
                    COLORS["G"] if status["blocks_mined"] > 0 else COLORS["O"],
                )
            )

        # Wallet activity
        print(color_text("\n💸 WALLET ACTIVITY:", COLORS["BOLD"]))
        for wallet in sorted(
            self.wallets, key=lambda w: w.transactions_sent, reverse=True
        ):
            print(
                color_text(
                    f"  Wallet {wallet.wallet_id}: {wallet.transactions_sent} transactions",
                    COLORS["Y"] if wallet.transactions_sent > 0 else COLORS["O"],
                )
            )

        print(color_text("=" * 80, COLORS["I"]))
        print(
            color_text(f"📁 Network data preserved at: {self.network_dir}", COLORS["B"])
        )
        print(color_text("🎯 Target address for all mining rewards:", COLORS["B"]))
        print(color_text(f"   {self.config.target_address}", COLORS["G"]))


def main():
    """Main function to run the network simulator"""
    print(color_text("🌙 LUNA NETWORK SIMULATOR", COLORS["BOLD"]))
    print(color_text("==========================", COLORS["I"]))

    # Configuration
    config = NetworkConfig()

    # User customization
    try:
        miners = input(f"Number of miners [{config.num_miners}]: ").strip()
        if miners:
            config.num_miners = int(miners)

        wallets = input(f"Number of wallets [{config.num_wallets}]: ").strip()
        if wallets:
            config.num_wallets = int(wallets)

        duration = input(
            f"Simulation duration (seconds) [{config.simulation_duration}]: "
        ).strip()
        if duration:
            config.simulation_duration = int(duration)

        target_addr = input(
            f"Target address for mining [{config.target_address}]: "
        ).strip()
        if target_addr:
            config.target_address = target_addr

    except ValueError:
        print(color_text("❌ Invalid input, using defaults", COLORS["R"]))

    # Create and run simulator
    simulator = LunaNetworkSimulator(config)

    try:
        # Setup network
        simulator.setup_network()

        # Start network
        if not simulator.start_network():
            print(color_text("❌ Failed to start network", COLORS["R"]))
            return

        # Run simulation
        simulator.run_simulation()

    except Exception as e:
        print(color_text(f"❌ Simulation error: {e}", COLORS["R"]))
        import traceback

        traceback.print_exc()

    finally:
        # Always stop network cleanly
        simulator.stop_network()


if __name__ == "__main__":
    main()
