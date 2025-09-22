#!/usr/bin/env python3
"""
lincoin_node.py - The Luna Coin blockchain node and miner with P2P networking.
Elaborate mining system with denomination-based rewards, real-time statistics, and peer-to-peer networking.
"""
import json
import hashlib
import time
import os
import sys
from typing import List, Dict, Set
import threading
import math
import socket
import atexit
import random
import uuid
import requests
from urllib.parse import urlparse
import netifaces
import pystray
from PIL import Image
import subprocess

class Block:
    def __init__(self, index: int, previous_hash: str, timestamp: float, transactions: List[Dict], nonce: int = 0):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.transactions = transactions
        self.nonce = nonce
        self.hash = self.calculate_hash()
        self.mining_time = 0
        self.hash_rate = 0
        self.current_mining_hashes = 0
        self.current_hash_rate = 0
        self.current_hash = ""

    def calculate_hash(self) -> str:
        block_data = f"{self.index}{self.previous_hash}{self.timestamp}{json.dumps(self.transactions)}{self.nonce}"
        return hashlib.sha256(block_data.encode()).hexdigest()

    def mine_block(self, difficulty: int, progress_callback=None):
        """Mine the block with real-time progress tracking"""
        target = "0" * difficulty
        start_time = time.time()
        hashes_tried = 0
        last_update = start_time
        
        print(f"🎯 Mining Target: {target}")
        print("⛏️  Starting mining operation...")
        
        while self.hash[:difficulty] != target:
            self.nonce += 1
            hashes_tried += 1
            self.hash = self.calculate_hash()
            
            current_time = time.time()
            if current_time - last_update >= 1.0:  # Update every second
                elapsed = current_time - start_time
                self.hash_rate = hashes_tried / elapsed if elapsed > 0 else 0
                
                if progress_callback:
                    progress_callback({
                        'hashes': hashes_tried,
                        'hash_rate': self.hash_rate,
                        'current_hash': self.hash,
                        'elapsed_time': elapsed
                    })
                
                last_update = current_time
                hashes_tried = 0
        
        end_time = time.time()
        self.mining_time = end_time - start_time
        self.hash_rate = self.nonce / self.mining_time if self.mining_time > 0 else 0
        
        return True

class Blockchain:
    def __init__(self, chain_file="blockchain.json", node_address=None):
        self.chain_file = chain_file
        self.verification_base_url = "https://bank.linglin.art/verify/"
        self.chain = self.load_chain() or [self.create_genesis_block()]
        self.difficulty = 6
        self.pending_transactions = []
        self.base_mining_reward = 50  # Base reward amount
        self.total_blocks_mined = 0
        self.total_mining_time = 0
        self.is_mining = False
        self.wallet_server_running = False
        self.stop_event = threading.Event()
        
        # P2P Networking
        self.node_address = node_address or self.generate_node_address()
        self.peers: Set[str] = set()
        self.peer_discovery_running = False
        self.peer_discovery_interval = 300  # 5 minutes
        self.known_peers_file = "known_peers.json"
        self.load_known_peers()
        
        # Mining progress tracking
        self.current_mining_hashes = 0
        self.current_hash_rate = 0
        self.current_hash = ""
        
        # Bill denominations mapped to difficulty levels - Linear orders of 10
        self.difficulty_denominations = {
            1: {"1": 1, "10": 2},                           # Very Easy
            2: {"1": 1, "10": 2, "100": 3},                 # Easy
            3: {"10": 2, "100": 3, "1000": 4},              # Medium
            4: {"100": 3, "1000": 4, "10000": 5},           # Hard
            5: {"1000": 4, "10000": 5, "100000": 6},        # Very Hard
            6: {"10000": 5, "100000": 6, "1000000": 7},     # Expert
            7: {"100000": 6, "1000000": 7, "10000000": 8},  # Master
            8: {"1000000": 7, "10000000": 8, "100000000": 9} # Legendary
        }

        # Bill rarity weights - Linear progression (higher denomination = more rare)
        self.bill_rarity = {
            "1": 100,         # Most common
            "10": 90,         # Very common
            "100": 80,        # Common
            "1000": 70,       # Somewhat common
            "10000": 60,      # Average
            "100000": 50,     # Uncommon
            "1000000": 40,    # Rare
            "10000000": 30,   # Very rare
            "100000000": 20   # Extremely rare
        }

    def generate_node_address(self):
        """Generate a unique node address"""
        return f"node_{hashlib.sha256(str(time.time()).encode()).hexdigest()[:12]}"

    def load_known_peers(self):
        """Load known peers from file"""
        try:
            if os.path.exists(self.known_peers_file):
                with open(self.known_peers_file, 'r') as f:
                    self.peers = set(json.load(f))
                    print(f"✅ Loaded {len(self.peers)} known peers")
        except:
            print("⚠️  Could not load known peers, starting fresh")
            self.peers = set()

    def save_known_peers(self):
        """Save known peers to file"""
        try:
            with open(self.known_peers_file, 'w') as f:
                json.dump(list(self.peers), f)
        except Exception as e:
            print(f"❌ Error saving known peers: {e}")

    def add_peer(self, peer_address: str):
        """Add a peer if it's not ourselves"""
        # Remove any protocol prefix if present
        if "://" in peer_address:
            from urllib.parse import urlparse
            url = urlparse(peer_address)
            peer_address = f"{url.hostname}:{url.port or 9335}"
        
        # Basic validation
        if not peer_address or ":" not in peer_address:
            print(f"❌ Invalid peer address format: {peer_address}")
            return False
        
        # Check if it's our own address (prevent self-connection)
        local_ips = [
            "127.0.0.1", "localhost", "0.0.0.0",
            "::1", "127.0.0.1:9335", "localhost:9335"
        ]
        
        # Add current machine's IP addresses
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            local_ips.extend([local_ip, f"{local_ip}:9335"])
            
            # Get all network interface IPs
            for interface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    for addr in addrs[netifaces.AF_INET]:
                        ip = addr['addr']
                        local_ips.extend([ip, f"{ip}:9335"])
        except:
            pass
        
        # Check if peer is one of our local addresses
        if peer_address in local_ips:
            print(f"⏭️  Skipping self as peer: {peer_address}")
            return False
        
        # Check if it's the same as our node address
        if hasattr(self, 'node_host') and hasattr(self, 'node_port'):
            my_address = f"{self.node_host}:{self.node_port}"
            if peer_address == my_address:
                print(f"⏭️  Skipping self as peer: {peer_address}")
                return False
        
        if peer_address not in self.peers:
            self.peers.add(peer_address)
            self.save_known_peers()
            print(f"➕ Added peer: {peer_address}")
            return True
        else:
            print(f"ℹ️  Peer already known: {peer_address}")
        
        return False

    def remove_peer(self, peer_address: str):
        """Remove a peer from the known peers list"""
        if peer_address in self.peers:
            self.peers.remove(peer_address)
            self.save_known_peers()
            print(f"✅ Removed peer: {peer_address}")
            return True
        print(f"ℹ️  Peer not found: {peer_address}")
        return False

    def discover_peers(self):
        """Discover new peers from existing peers"""
        if not self.peers:
            print("⚠️  No known peers to discover from")
            return
        
        print(f"🔍 Discovering peers from {len(self.peers)} known peers...")
        new_peers_count = 0
        
        for peer in list(self.peers):
            try:
                print(f"   Asking {peer} for peers...")
                response = self.send_to_peer(peer, {"action": "get_peers"})
                if response and response.get("status") == "success":
                    new_peers = response.get("peers", [])
                    for new_peer in new_peers:
                        if self.add_peer(new_peer):
                            new_peers_count += 1
                    print(f"   ✅ Discovered {len(new_peers)} peers from {peer}")
                else:
                    print(f"   ❌ No response from {peer}")
                    # Remove unresponsive peer after multiple failures
                    if hasattr(peer, 'failure_count'):
                        peer.failure_count += 1
                        if peer.failure_count > 3:
                            self.remove_peer(peer)
                    else:
                        # Initialize failure count
                        peer.failure_count = 1
            except Exception as e:
                print(f"   ❌ Error discovering peers from {peer}: {e}")
                # Remove unresponsive peer
                self.remove_peer(peer)
        
        print(f"✅ Discovered {new_peers_count} new peers total")

    def peer_discovery_loop(self):
        """Continuous peer discovery loop"""
        self.peer_discovery_running = True
        discovery_count = 0
        
        while not self.stop_event.is_set():
            try:
                discovery_count += 1
                print(f"🔄 Peer discovery round {discovery_count}...")
                self.discover_peers()
                
                # Wait for the next discovery interval
                for i in range(self.peer_discovery_interval):
                    if self.stop_event.is_set():
                        break
                    time.sleep(1)
                    
            except Exception as e:
                print(f"❌ Error in peer discovery: {e}")
                time.sleep(60)  # Wait a minute before retrying
        
        self.peer_discovery_running = False

    def test_peer_connectivity(self, peer_address: str = None):
        """Test connectivity to peers"""
        peers_to_test = [peer_address] if peer_address else list(self.peers)
        
        if not peers_to_test:
            print("❌ No peers to test")
            return
        
        print(f"🔌 Testing connectivity to {len(peers_to_test)} peers...")
        
        for peer in peers_to_test:
            try:
                # Check if we're trying to connect to ourselves
                if hasattr(self, 'node_host') and hasattr(self, 'node_port'):
                    my_address = f"{self.node_host}:{self.node_port}"
                    if peer == my_address:
                        print(f"⏭️  Skipping self: {peer}")
                        continue
                
                print(f"   Testing {peer}...")
                response = self.send_to_peer(peer, {"action": "ping"}, timeout=5)
                if response and response.get("status") == "success":
                    print(f"   ✅ {peer} - Reachable")
                else:
                    print(f"   ❌ {peer} - Unreachable")
            except Exception as e:
                print(f"   ❌ {peer} - Error: {e}")

    def start_peer_discovery(self):
        """Start the peer discovery service"""
        if not self.peer_discovery_running:
            discovery_thread = threading.Thread(target=self.peer_discovery_loop, daemon=True)
            discovery_thread.start()
            print("✅ Peer discovery service started")

    def list_peers(self):
        """List all known peers"""
        print("📋 Known peers:")
        for peer in self.peers:
            print(f"   - {peer}")
        print(f"   Total: {len(self.peers)} peers")

    def send_to_peer(self, peer_address: str, data: Dict, timeout=10):
        """Send data to a peer node using direct socket connection"""
        try:
            # Parse peer address (format: "ip:port")
            if "://" in peer_address:
                # Extract host and port from HTTP URL format
                from urllib.parse import urlparse
                url = urlparse(peer_address)
                host = url.hostname
                port = url.port or 9335  # Default port if not specified
            else:
                # Direct IP:PORT format
                if ":" in peer_address:
                    host, port_str = peer_address.split(":", 1)
                    port = int(port_str)
                else:
                    # If no port specified, use default
                    host = peer_address
                    port = 9335
            
            # Create a socket connection
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                s.connect((host, port))
                
                # Send data with length prefix
                data_json = json.dumps(data)
                data_length = len(data_json.encode())
                s.sendall(data_length.to_bytes(4, 'big'))
                s.sendall(data_json.encode())
                
                # Receive response
                length_bytes = s.recv(4)
                if not length_bytes:
                    return None
                
                response_length = int.from_bytes(length_bytes, 'big')
                response_data = b""
                while len(response_data) < response_length:
                    chunk = s.recv(min(4096, response_length - len(response_data)))
                    if not chunk:
                        break
                    response_data += chunk
                
                if len(response_data) == response_length:
                    return json.loads(response_data.decode())
                else:
                    print(f"❌ Incomplete response from {peer_address}")
                    
        except socket.timeout:
            print(f"❌ Timeout communicating with {peer_address}")
        except ConnectionRefusedError:
            print(f"❌ Connection refused by {peer_address}")
        except Exception as e:
            print(f"❌ Error communicating with peer {peer_address}: {e}")
            # Remove unresponsive peer
            if hasattr(self, 'remove_peer'):
                self.remove_peer(peer_address)
        
        return None

    def broadcast(self, data: Dict, exclude_peers=None):
        """Broadcast data to all known peers"""
        exclude_peers = exclude_peers or []
        successful_broadcasts = 0
        
        for peer in list(self.peers):
            if peer in exclude_peers:
                continue
                
            response = self.send_to_peer(peer, data)
            if response and response.get("status") == "success":
                successful_broadcasts += 1
        
        return successful_broadcasts

    def validate_chain(self, chain):
        """Validate a complete blockchain"""
        if not chain:
            return False
        
        # Check genesis block
        if chain[0].index != 0 or chain[0].previous_hash != "0":
            print("❌ Invalid genesis block")
            return False
        
        # Check each block
        for i in range(1, len(chain)):
            current_block = chain[i]
            previous_block = chain[i-1]
            
            # Check block hash validity
            if current_block.hash != current_block.calculate_hash():
                print(f"❌ Block {current_block.index} has invalid hash")
                return False
            
            # Check chain linkage
            if current_block.previous_hash != previous_block.hash:
                print(f"❌ Block {current_block.index} has invalid previous hash")
                return False
            
            # Check block index order
            if current_block.index != previous_block.index + 1:
                print(f"❌ Block {current_block.index} has invalid index")
                return False
        
        return True

    def save_chain(self):
        """Save blockchain to file"""
        try:
            chain_data = []
            for block in self.chain:
                chain_data.append({
                    "index": block.index,
                    "previous_hash": block.previous_hash,
                    "timestamp": block.timestamp,
                    "transactions": block.transactions,
                    "nonce": block.nonce,
                    "hash": block.hash,
                    "mining_time": block.mining_time
                })
            
            with open("blockchain.json", "w") as f:
                json.dump(chain_data, f, indent=2)
            print("💾 Blockchain saved to blockchain.json")
        except Exception as e:
            print(f"❌ Error saving blockchain: {e}")

    def download_from_web(self, resource_type="blockchain"):
        """Download blockchain or mempool from web server"""
        base_url = "https://bank.linglin.art/"
        url = f"{base_url}{resource_type}"
        
        try:
            print(f"🌐 Downloading {resource_type} from {url}...")
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                if resource_type == "blockchain":
                    chain_data = response.json()
                    # Convert to Block objects
                    new_chain = []
                    for block_data in chain_data:
                        block = Block(
                            block_data["index"],
                            block_data["previous_hash"],
                            block_data["timestamp"],
                            block_data["transactions"],
                            block_data.get("nonce", 0)
                        )
                        block.hash = block_data["hash"]
                        block.mining_time = block_data.get("mining_time", 0)
                        new_chain.append(block)
                    
                    if self.validate_chain(new_chain):
                        self.chain = new_chain
                        self.save_chain()
                        print(f"✅ Downloaded and validated blockchain with {len(chain_data)} blocks")
                        return True
                    else:
                        print("❌ Downloaded blockchain failed validation")
                elif resource_type == "mempool":
                    mempool_data = response.json()
                    self.pending_transactions = mempool_data
                    self.save_mempool()
                    print(f"✅ Downloaded mempool with {len(mempool_data)} transactions")
                    return True
            else:
                print(f"❌ Failed to download {resource_type}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error downloading {resource_type}: {e}")
        
        return False

    def sync_all(self):
        """One command to sync everything"""
        print("🔄 Starting complete network synchronization...")
        
        # Sync blockchain
        if not self.download_from_web("blockchain"):
            print("🌐 Web blockchain unavailable, trying peers...")
            self.download_blockchain()
        
        # Sync mempool
        if not self.download_from_web("mempool"):
            print("🌐 Web mempool unavailable, trying peers...")
            self.download_mempool()
        
        # Discover peers
        self.discover_peers()
        
        print("✅ Complete synchronization finished")

    def download_blockchain(self, peer_address: str = None):
        """Download blockchain from a peer"""
        # If no specific peer provided, try all known peers
        peers_to_try = [peer_address] if peer_address else list(self.peers)
        
        print(f"🔍 Current peers: {list(self.peers)}")
        print(f"🔍 Peers to try: {peers_to_try}")
        
        if not peers_to_try:
            print("❌ No peers available to download blockchain from")
            return False
        
        for peer in peers_to_try:
            try:
                # Check if we're trying to connect to ourselves
                if hasattr(self, 'node_host') and hasattr(self, 'node_port'):
                    my_address = f"{self.node_host}:{self.node_port}"
                    if peer == my_address:
                        print(f"⏭️  Skipping self: {peer}")
                        continue
                
                print(f"📥 Attempting to download blockchain from {peer}...")
                
                # First test if the peer is reachable with a ping
                ping_response = self.send_to_peer(peer, {"action": "ping"}, timeout=5)
                if not ping_response or ping_response.get("status") != "success":
                    print(f"❌ Peer {peer} is not responding to ping")
                    continue
                    
                print(f"✅ Peer {peer} is reachable, requesting blockchain...")
                
                # Request the blockchain with a longer timeout
                response = self.send_to_peer(peer, {"action": "get_blockchain"}, timeout=30)
                
                if not response:
                    print(f"❌ No response from {peer}")
                    continue
                    
                if response.get("status") == "success":
                    chain_data = response.get("blockchain", [])
                    total_blocks = response.get("total_blocks", 0)
                    
                    print(f"🔍 Received {len(chain_data)} blocks, I have {len(self.chain)} blocks")
                    
                    if len(chain_data) > len(self.chain):
                        print(f"✅ Downloaded blockchain with {total_blocks} blocks from {peer}")
                        
                        # Replace our chain with the downloaded one
                        new_chain = []
                        for block_data in chain_data:
                            # Recreate the block exactly as it was mined
                            block = Block(
                                block_data["index"],
                                block_data["previous_hash"],
                                block_data["timestamp"],
                                block_data["transactions"],
                                block_data.get("nonce", 0)
                            )
                            # Preserve the original hash and mining time
                            block.hash = block_data["hash"]
                            block.mining_time = block_data.get("mining_time", 0)
                            new_chain.append(block)
                        
                        # Validate the new chain before replacing
                        if self.validate_chain(new_chain):
                            self.chain = new_chain
                            self.save_chain()
                            print(f"✅ Blockchain updated to {len(self.chain)} blocks")
                            return True
                        else:
                            print("❌ Downloaded blockchain failed validation")
                    else:
                        print("ℹ️  Peer has same or shorter chain, keeping current blockchain")
                else:
                    error_msg = response.get("message", "Unknown error")
                    print(f"❌ Failed to download blockchain from {peer}: {error_msg}")
                    
            except socket.timeout:
                print(f"❌ Timeout connecting to {peer}")
            except ConnectionRefusedError:
                print(f"❌ Connection refused by {peer}")
            except Exception as e:
                print(f"❌ Error downloading blockchain from {peer}: {e}")
                import traceback
                traceback.print_exc()
        
        print("❌ Failed to download blockchain from all peers")
        return False

    def save_mempool(self):
        """Save pending transactions to mempool.json"""
        try:
            with open("mempool.json", "w") as f:
                json.dump(self.pending_transactions, f, indent=2)
            print("💾 Mempool saved to mempool.json")
        except Exception as e:
            print(f"❌ Error saving mempool: {e}")

    def download_mempool(self, peer_address: str = None):
        """Download mempool transactions from a peer"""
        # If no specific peer provided, try all known peers
        peers_to_try = [peer_address] if peer_address else list(self.peers)
        
        if not peers_to_try:
            print("❌ No peers available to download mempool from")
            return False
        
        new_transactions = 0
        
        for peer in peers_to_try:
            try:
                print(f"📥 Downloading mempool from {peer}...")
                response = self.send_to_peer(peer, {"action": "get_pending_transactions"})
                
                if response and response.get("status") == "success":
                    transactions = response.get("transactions", [])
                    
                    for tx in transactions:
                        # Add transaction if not already in our mempool
                        if not any(t.get("signature") == tx.get("signature") for t in self.pending_transactions):
                            self.pending_transactions.append(tx)
                            new_transactions += 1
                    
                    # Save mempool to file after adding new transactions
                    self.save_mempool()
                    
                    print(f"✅ Added {new_transactions} new transactions from {peer}'s mempool")
                    return True
                else:
                    print(f"❌ Failed to download mempool from {peer}")
            except Exception as e:
                print(f"❌ Error downloading mempool from {peer}: {e}")
        
        print(f"ℹ️  No new transactions found from any peer")
        return new_transactions > 0

    def validate_chain(self, chain: List[Block]) -> bool:
        """Validate a blockchain"""
        for i in range(1, len(chain)):
            current_block = chain[i]
            previous_block = chain[i-1]
            
            # Check if current block hash is correct
            if current_block.hash != current_block.calculate_hash():
                print(f"❌ Block {i} hash is invalid!")
                return False
            
            # Check if previous hash matches
            if current_block.previous_hash != previous_block.hash:
                print(f"❌ Block {i} previous hash doesn't match!")
                return False
        
        return True

    def generate_serial_number(self):
        """Generate a unique serial number in SN-###-###-#### format"""
        # Generate a unique serial number
        serial_id = str(uuid.uuid4().int)[:10]  # Get first 10 digits of UUID
        formatted_serial = f"SN-{serial_id[:3]}-{serial_id[3:6]}-{serial_id[6:10]}"
        return formatted_serial

    def clear_mempool(self, mempool_file="mempool.json"):
        """Clear the mempool file"""
        try:
            open(mempool_file, 'w').close()
            self.pending_transactions = []
            print("✅ Mempool cleared")
            return True
        except Exception as e:
            print(f"❌ Error clearing mempool: {e}")
            return False

    def create_genesis_block(self) -> Block:
        # Generate a serial number for the genesis block
        genesis_serial = self.generate_serial_number()
        return Block(0, "0", time.time(), [{
            "type": "genesis", 
            "message": "Luna Genesis Block",
            "timestamp": time.time(),
            "reward": 10000,
            "denomination": "10000",
            "difficulty": 1,
            "serial_number": genesis_serial,
            "verification_url": f"{self.verification_base_url}{genesis_serial}"
        }])

    def get_latest_block(self) -> Block:
        return self.chain[-1]

    def add_block(self, new_block: Block):
        new_block.previous_hash = self.get_latest_block().hash
        self.chain.append(new_block)
        self.total_blocks_mined += 1
        self.total_mining_time += new_block.mining_time
        self.save_chain()
        
        # Broadcast the new block to peers
        block_data = {
            "action": "new_block",
            "block": {
                "index": new_block.index,
                "previous_hash": new_block.previous_hash,
                "timestamp": new_block.timestamp,
                "transactions": new_block.transactions,
                "nonce": new_block.nonce,
                "hash": new_block.hash,
                "mining_time": new_block.mining_time
            }
        }
        self.broadcast(block_data)

    def add_transaction(self, transaction: Dict):
        self.pending_transactions.append(transaction)
        
        # Broadcast the new transaction to peers
        tx_data = {
            "action": "new_transaction",
            "transaction": transaction
        }
        self.broadcast(tx_data)

    def determine_bill_denomination(self, block_hash):
        """Determine which bill denomination was found based on block hash and difficulty"""
        current_difficulty = self.difficulty
        available_bills = self.difficulty_denominations.get(current_difficulty, {"1": 1})
        
        # Use block hash to create deterministic randomness
        hash_int = int(block_hash[:8], 16)  # Use first 8 chars of hash
        
        # Create weighted selection based on rarity
        weighted_choices = []
        for bill, multiplier in available_bills.items():
            weight = self.bill_rarity.get(bill, 1)
            weighted_choices.extend([bill] * weight)
        
        # Use hash for deterministic selection
        selected_bill = weighted_choices[hash_int % len(weighted_choices)]
        multiplier = available_bills[selected_bill]
        
        actual_reward = self.base_mining_reward * multiplier
        
        return selected_bill, multiplier, actual_reward

    def mine_pending_transactions(self, mining_reward_address: str):
        if not self.pending_transactions:
            print("❌ No transactions to mine!")
            return False
        
        print(f"📦 Preparing block with {len(self.pending_transactions)} transactions...")
        
        # Create mining progress display
        def mining_progress(stats):
            hashes_per_sec = stats['hash_rate']
            if hashes_per_sec > 1_000_000:
                hash_rate_str = f"{hashes_per_sec/1_000_000:.2f} MH/s"
            elif hashes_per_sec > 1_000:
                hash_rate_str = f"{hashes_per_sec/1_000:.2f} KH/s"
            else:
                hash_rate_str = f"{hashes_per_sec:.2f} H/s"
            
            # Update mining progress for external access
            self.current_mining_hashes = stats['hashes']
            self.current_hash_rate = stats['hash_rate']
            self.current_hash = stats['current_hash']
            
            print(f"\r⛏️  Mining: {stats['hashes']:,.0f} hashes | {hash_rate_str} | Current: {stats['current_hash'][:self.difficulty+2]}...", 
                  end="", flush=True)

        # Create and mine the block
        block = Block(len(self.chain), self.get_latest_block().hash, time.time(), self.pending_transactions.copy())
        
        self.is_mining = True
        print("\n" + "="*60)
        print("🚀 STARTING MINING OPERATION")
        print("="*60)
        print(f"⚙️  Difficulty Level: {self.difficulty}")
        print(f"💵 Available Bills: {', '.join(self.difficulty_denominations[self.difficulty].keys())}")
        print("="*60)
        
        start_time = time.time()
        block.mine_block(self.difficulty, mining_progress)
        end_time = time.time()
        
        self.is_mining = False
        
        # Reset mining progress
        self.current_mining_hashes = 0
        self.current_hash_rate = 0
        self.current_hash = ""
        
        # Determine bill denomination found
        bill_denomination, multiplier, actual_reward = self.determine_bill_denomination(block.hash)
        
        # Generate a unique serial number for this bill
        serial_number = self.generate_serial_number()
        verification_url = f"{self.verification_base_url}{serial_number}"
        
        print("\n\n" + "="*60)
        print("✅ BLOCK MINED SUCCESSFULLY!")
        print("="*60)
        
        # Add to chain
        self.add_block(block)
        
        # Add mining reward with bill information
        reward_tx = {
            "type": "reward",
            "to": mining_reward_address,
            "amount": actual_reward,
            "base_reward": self.base_mining_reward,
            "denomination": bill_denomination,
            "multiplier": multiplier,
            "timestamp": time.time(),
            "block_height": len(self.chain) - 1,
            "signature": f"reward_{len(self.chain)}_{hashlib.sha256(mining_reward_address.encode()).hexdigest()[:16]}",
            "block_hash": block.hash,
            "difficulty": self.difficulty,
            "serial_number": serial_number,
            "verification_url": verification_url
        }
        self.pending_transactions = [reward_tx]
        
        # Display mining statistics
        mining_time = end_time - start_time
        print(f"📊 Mining Statistics:")
        print(f"   Block Height: {block.index}")
        print(f"   Hash: {block.hash[:16]}...")
        print(f"   Nonce: {block.nonce:,}")
        print(f"   Mining Time: {mining_time:.2f} seconds")
        print(f"   Hash Rate: {block.hash_rate:,.2f} H/s")
        print(f"   Difficulty: {self.difficulty}")
        print(f"   Transactions: {len(block.transactions)}")
        print(f"   💰 Bill Found: ${bill_denomination} Bill")
        print(f"   📈 Multiplier: x{multiplier}")
        print(f"   ⛏️  Base Reward: {self.base_mining_reward} LC")
        print(f"   🎯 Total Reward: {actual_reward} LC → {mining_reward_address}")
        print(f"   🔢 Serial Number: {serial_number}")
        print(f"   🔗 Verification: {verification_url}")
        
        return True

    def get_mining_stats(self):
        if self.total_blocks_mined == 0:
            return {
                'total_blocks': 0,
                'avg_time': 0,
                'total_time': 0,
                'total_rewards': 0
            }
        
        # Calculate total rewards from blockchain
        total_rewards = 0
        for block in self.chain:
            for tx in block.transactions:
                if tx.get("type") == "reward" or tx.get("type") == "genesis":
                    total_rewards += tx.get("amount", 0)
        
        return {
            'total_blocks': self.total_blocks_mined,
            'avg_time': self.total_mining_time / self.total_blocks_mined,
            'total_time': self.total_mining_time,
            'total_rewards': total_rewards
        }

    def is_chain_valid(self) -> bool:
        return self.validate_chain(self.chain)

    def save_chain(self):
        chain_data = []
        for block in self.chain:
            chain_data.append({
                "index": block.index,
                "previous_hash": block.previous_hash,
                "timestamp": block.timestamp,
                "transactions": block.transactions,
                "nonce": block.nonce,
                "hash": block.hash,
                "mining_time": block.mining_time
            })
        with open(self.chain_file, 'w') as f:
            json.dump(chain_data, f, indent=2)

    def load_chain(self):
        if os.path.exists(self.chain_file):
            try:
                with open(self.chain_file, 'r') as f:
                    chain_data = json.load(f)
                    chain = []
                    for block_data in chain_data:
                        block = Block(
                            block_data["index"],
                            block_data["previous_hash"],
                            block_data["timestamp"],
                            block_data["transactions"],
                            block_data.get("nonce", 0)
                        )
                        block.mining_time = block_data.get("mining_time", 0)
                        chain.append(block)
                    return chain
            except:
                print("⚠️  Corrupted blockchain file, creating new chain...")
        return None


    def handle_wallet_connection(self, data):
        """Handle incoming wallet requests"""
        action = data.get("action")
        MAX_RESPONSE_SIZE = 10 * 1024 * 1024  # 10MB limit

        try:
            if action == "ping":
                return {"status": "success", "message": "pong", "timestamp": time.time()}
            elif action == "get_mining_progress":
                if self.is_mining:
                    return {
                        "status": "success", 
                        "mining": True,
                        "progress": {
                            "hashes": self.current_mining_hashes,
                            "hash_rate": self.current_hash_rate,
                            "current_hash": self.current_hash
                        }
                    }
                else:
                    return {"status": "success", "mining": False}
            elif action == "get_mining_stats":
                stats = self.get_mining_stats()
                return {"status": "success", "stats": stats}
            elif action == "get_mining_address":
                return {"status": "success", "address": "miner_default_address"}
            
            elif action == "get_balance":
                address = data.get("address")
                balance = self.calculate_balance(address)
                return {"status": "success", "balance": balance}
            
            elif action == "add_transaction":
                transaction = data.get("transaction")
                self.add_transaction(transaction)
                return {"status": "success", "message": "Transaction added to mempool"}
            
            elif action == "get_blockchain_info":
                # Return only summary info, not the full blockchain
                return {
                    "status": "success",
                    "blockchain_height": len(self.chain),
                    "latest_block_hash": self.chain[-1].hash if self.chain else None,
                    "pending_transactions": len(self.pending_transactions),
                    "difficulty": self.difficulty,
                    "base_reward": self.base_mining_reward,
                    "node_address": self.node_address,
                    "peers_count": len(self.peers)
                }
            elif action == "start_mining":
                # Get miner address from request or use default
                miner_address = data.get("miner_address", "miner_default_address")
                
                # Start mining in a separate thread
                def mining_thread():
                    try:
                        success = self.mine_pending_transactions(miner_address)
                        if success:
                            self.clear_mempool()
                    except Exception as e:
                        print(f"Mining error: {e}")
                
                thread = threading.Thread(target=mining_thread, daemon=True)
                thread.start()
                
                return {"status": "success", "message": "Mining started in background"}
            
            elif action == "get_pending_transactions":
                return {"status": "success", "transactions": self.pending_transactions}
            elif action == "get_blockchain":
                estimated_size = len(json.dumps([block.__dict__ for block in self.chain]))
                if estimated_size > MAX_RESPONSE_SIZE:
                    return {
                        "status": "error", 
                        "message": f"Blockchain too large ({estimated_size/1024/1024:.1f}MB). Use get_blockchain_info instead."
                    }
                # Return only the last 10 blocks to avoid huge responses
                max_blocks = 10
                chain_to_send = self.chain[-max_blocks:] if len(self.chain) > max_blocks else self.chain
                
                chain_data = []
                for block in chain_to_send:
                    chain_data.append({
                        "index": block.index,
                        "previous_hash": block.previous_hash,
                        "timestamp": block.timestamp,
                        "transactions": block.transactions[:5],  # Limit transactions too
                        "nonce": block.nonce,
                        "hash": block.hash,
                        "mining_time": block.mining_time
                    })
                return {"status": "success", "blockchain": chain_data, "total_blocks": len(self.chain)}
            
            elif action == "get_difficulty_info":
                return {
                    "status": "success",
                    "difficulty": self.difficulty,
                    "available_bills": self.difficulty_denominations.get(self.difficulty, {}),
                    "base_reward": self.base_mining_reward
                }
            
            # P2P Network Actions
            elif action == "get_peers":
                return {"status": "success", "peers": list(self.peers)}
            
            elif action == "add_peer":
                peer_address = data.get("peer_address")
                if peer_address and self.add_peer(peer_address):
                    return {"status": "success", "message": f"Peer {peer_address} added"}
                else:
                    return {"status": "error", "message": "Failed to add peer"}
            elif action == "test_peers":
                blockchain.test_peer_connectivity()
            elif action == "new_block":
                block_data = data.get("block")
                if block_data:
                    # Check if we already have this block
                    if block_data["index"] > len(self.chain) - 1:
                        print(f"📥 Received new block #{block_data['index']} from peer")
                        block = Block(
                            block_data["index"],
                            block_data["previous_hash"],
                            block_data["timestamp"],
                            block_data["transactions"],
                            block_data.get("nonce", 0)
                        )
                        block.mining_time = block_data.get("mining_time", 0)
                        block.hash = block_data.get("hash", block.calculate_hash())
                        
                        # Validate the block
                        if block.hash == block.calculate_hash() and block.previous_hash == self.get_latest_block().hash:
                            self.chain.append(block)
                            self.save_chain()
                            print(f"✅ Added new block #{block.index} from peer")
                            return {"status": "success", "message": "Block added"}
                    
                    return {"status": "success", "message": "Block already exists or invalid"}
                else:
                    return {"status": "error", "message": "No block data provided"}
            
            elif action == "new_transaction":
                transaction = data.get("transaction")
                if transaction:
                    # Add transaction if not already in mempool
                    if not any(t.get("signature") == transaction.get("signature") for t in self.pending_transactions):
                        self.pending_transactions.append(transaction)
                        print(f"📥 Received new transaction from peer")
                        return {"status": "success", "message": "Transaction added to mempool"}
                    else:
                        return {"status": "success", "message": "Transaction already in mempool"}
                else:
                    return {"status": "error", "message": "No transaction data provided"}
            
            return {"status": "error", "message": "Unknown action"}
        except Exception as e:
            return {"status": "error", "message": f"Server error: {str(e)}"}

    def calculate_balance(self, address):
        """Calculate balance for a specific address"""
        balance = 0
        for block in self.chain:
            for tx in block.transactions:
                if tx.get("to") == address:
                    balance += tx.get("amount", 0)
                if tx.get("from") == address:
                    balance -= tx.get("amount", 0)
        
        # Also check pending transactions
        for tx in self.pending_transactions:
            if tx.get("type") != "reward":
                if tx.get("to") == address:
                    balance += tx.get("amount", 0)
                if tx.get("from") == address:
                    balance -= tx.get("amount", 0)
        
        return balance

    def wallet_server_thread(self):
        """Wallet server thread function"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server_socket.bind(('0.0.0.0', 9335))
            server_socket.listen(5)
            server_socket.settimeout(1.0)
            
            print(f"👛 Node Wallet server listening on port 9335")
            self.wallet_server_running = True
            
            while not self.stop_event.is_set():
                try:
                    client_socket, addr = server_socket.accept()
                    client_socket.settimeout(5.0)
                    
                    # Read the message length first (4 bytes)
                    try:
                        length_bytes = client_socket.recv(4)
                        if not length_bytes:
                            client_socket.close()
                            continue
                        
                        message_length = int.from_bytes(length_bytes, 'big')
                        
                        # Read the actual message
                        request_data = b""
                        while len(request_data) < message_length:
                            chunk = client_socket.recv(min(4096, message_length - len(request_data)))
                            if not chunk:
                                break
                            request_data += chunk
                        
                        if len(request_data) == message_length:
                            try:
                                message = json.loads(request_data.decode())
                                response = self.handle_wallet_connection(message)
                                
                                # Send response with length prefix
                                response_json = json.dumps(response)
                                response_length = len(response_json.encode())
                                client_socket.sendall(response_length.to_bytes(4, 'big'))
                                client_socket.sendall(response_json.encode())
                                
                            except json.JSONDecodeError as e:
                                error_response = {"status": "error", "message": f"Invalid JSON: {e}"}
                                error_json = json.dumps(error_response)
                                error_length = len(error_json.encode())
                                client_socket.sendall(error_length.to_bytes(4, 'big'))
                                client_socket.sendall(error_json.encode())
                        
                    except Exception as e:
                        print(f"Error handling client: {e}")
                    
                    client_socket.close()
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    if not self.stop_event.is_set():
                        print(f"Wallet server client error: {e}")
        except Exception as e:
            if not self.stop_event.is_set():
                print(f"❌ Failed to start wallet server: {e}")
        finally:
            server_socket.close()
            self.wallet_server_running = False
            print("👛 Wallet server stopped")

    def start_wallet_server(self):
        """Start the wallet server to handle wallet connections"""
        # Start the wallet server thread
        self.wallet_thread = threading.Thread(target=self.wallet_server_thread)
        self.wallet_thread.daemon = False  # Make non-daemon for proper cleanup
        self.wallet_thread.start()
        print("✅ Node wallet server thread started")

    def stop_wallet_server(self):
        """Stop the wallet server gracefully"""
        print("🛑 Stopping wallet server...")
        self.stop_event.set()
        if hasattr(self, 'wallet_thread') and self.wallet_thread.is_alive():
            self.wallet_thread.join(timeout=3.0)
        print("✅ Wallet server stopped")

import os
import json
from typing import List, Dict

def load_mempool(mempool_file: str = "mempool.json") -> List[Dict]:
    transactions = []
    try:
        if os.path.exists(mempool_file):
            with open(mempool_file, 'r', encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        transaction = json.loads(line)
                        transactions.append(transaction)
            print(f"✅ Loaded {len(transactions)} transactions from mempool")
        else:
            print("⚠️  Mempool file not found")
    except Exception as e:
        print(f"❌ Error loading mempool: {e}")
    return transactions

def show_mining_animation():
    """Show a simple mining animation when mining"""
    animations = ["⛏️ ", "🔨", "⚒️ ", "🛠️ "]
    while blockchain.is_mining:
        for anim in animations:
            if not blockchain.is_mining:
                break
            print(f"\r{anim} Mining...", end="", flush=True)
            time.sleep(0.3)
    print("\r" + " " * 20 + "\r", end="", flush=True)

def show_help():
    print("\n🎮 Luna Node Commands:")
    print("  mine      - Mine pending transactions")
    print("  load      - Load transactions from mempool")
    print("  status    - Show blockchain status")
    print("  stats     - Show mining statistics")
    print("  validate  - Validate blockchain integrity")
    print("  clear     - Clear mempool file")
    print("  difficulty <n> - Set mining difficulty (1-8)")
    print("  bills     - Show available bills for current difficulty")
    print("  peers     - Show connected peers")
    print("  addpeer <addr> - Add a peer (format: ip:port)")
    print("  discover  - Discover new peers from known peers")
    print("  download blockchain - Download blockchain from peers")
    print("  download mempool - Download mempool from peers")
    print("  help      - Show this help")
    print("  exit      - Exit the node")

def get_miner_address_from_wallet():
    """Get miner address directly from wallet"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            s.connect(('127.0.0.1', 9334))  # Wallet RPC port
            s.sendall(json.dumps({
                "action": "get_mining_address"
            }).encode())
            response = s.recv(1024)
            result = json.loads(response.decode())
            if result.get("status") == "success":
                address = result.get("address")
                print(f"✅ Using mining address from wallet: {address}")
                return address
    except Exception as e:
        print(f"⚠️  Could not connect to wallet: {e}")
        print("💡 Make sure the wallet is running with: python wallet.py server")
    
    # Fallback: try to read from config file
    try:
        if os.path.exists("wallet_config.json"):
            with open("wallet_config.json", "r") as f:
                config = json.load(f)
                mining_address = config.get("mining", {}).get("mining_reward_address", "")
                if mining_address:
                    print(f"✅ Using mining address from config: {mining_address}")
                    return mining_address
    except Exception as e:
        print(f"⚠️  Could not read config: {e}")
    
    # Final fallback: ask user
    return input("Enter miner address for rewards: ") or "miner_default_address"

# Global blockchain instance with node info
blockchain = Blockchain()
blockchain.node_host = "127.0.0.1"  # Or your actual host
blockchain.node_port = 9335

def cleanup():
    """Cleanup function for graceful shutdown"""
    print("\n💾 Performing cleanup...")
    blockchain.stop_wallet_server()
    blockchain.save_chain()
    blockchain.save_known_peers()
    print("✅ Cleanup completed")

# Register cleanup function
atexit.register(cleanup)

def list_recent_bills():
    """List recent bills mined with their verification links"""
    print("\n💰 RECENTLY MINED BILLS:")
    print("="*80)
    
    # Get the last 10 blocks
    recent_blocks = blockchain.chain[-10:] if len(blockchain.chain) > 10 else blockchain.chain
    
    bills_found = []
    for block in recent_blocks:
        for tx in block.transactions:
            if tx.get("type") in ["reward", "genesis"] and tx.get("serial_number"):
                bills_found.append({
                    "block": block.index,
                    "denomination": f"${tx.get('denomination', 'N/A')}",
                    "serial": tx.get("serial_number", "N/A"),
                    "verification_url": tx.get("verification_url", "N/A"),
                    "miner": tx.get("to", "Unknown")
                })
    
    if not bills_found:
        print("No bills found in recent blocks")
        return
    
    for i, bill in enumerate(bills_found, 1):
        print(f"{i:2d}. Block {bill['block']:4d} | {bill['denomination']:>8} | {bill['serial']}")
        print(f"    🔗 {bill['verification_url']}")
        print(f"    ⛏️  Miner: {bill['miner']}")
        print()

def main():
    
    # Start the wallet server
    blockchain.start_wallet_server()
    
    # Start peer discovery
    blockchain.start_peer_discovery()
    
    print("""
    ╔══════════════════════════════════════════════════════╗
    ║                 LUNA BLOCKCHAIN NODE                 ║
    ║           Denomination-Based Mining Edition          ║
    ║                 with P2P Networking                  ║
    ╚══════════════════════════════════════════════════════╝
    """)
    
    print(f"📦 Genesis Block: {blockchain.chain[0].hash[:12]}...")
    print(f"⛓️  Chain Height: {len(blockchain.chain)}")
    print(f"⚙️  Difficulty: {blockchain.difficulty}")
    print(f"💰 Base Mining Reward: {blockchain.base_mining_reward} LC")
    print(f"🌐 Node Address: {blockchain.node_address}")
    print(f"🔗 Known Peers: {len(blockchain.peers)}")
    print("Type 'help' for commands\n")
    
    while True:
        try:
            command = input("\n⛓️  node> ").strip().lower()
            
            if command == "mine":
                # Start mining animation in background
                anim_thread = threading.Thread(target=show_mining_animation, daemon=True)
                anim_thread.start()
                
                # Get miner address from wallet
                miner_address = get_miner_address_from_wallet()
                
                if miner_address:  # Check if we got a valid address
                    success = blockchain.mine_pending_transactions(miner_address)
                    if success:
                        blockchain.clear_mempool()
                else:
                    print("❌ Could not get valid miner address")
                    
            elif command == "load":
                txs = load_mempool()
                for tx in txs:
                    blockchain.add_transaction(tx)
                print(f"📥 Added {len(txs)} transactions to pending pool")
                
            elif command == "status":
                latest = blockchain.get_latest_block()
                stats = blockchain.get_mining_stats()
                print(f"📊 Blockchain Status:")
                print(f"   Height: {len(blockchain.chain)} blocks")
                print(f"   Pending TXs: {len(blockchain.pending_transactions)}")
                print(f"   Latest Block: {latest.hash[:16]}...")
                print(f"   Total Blocks Mined: {stats['total_blocks']}")
                print(f"   Total Rewards Minted: {stats['total_rewards']} LC")
                print(f"   Avg Mining Time: {stats['avg_time']:.2f}s")
                print(f"   Known Peers: {len(blockchain.peers)}")
                print(f"   Node Address: {blockchain.node_address}")
                
            elif command == "stats":
                stats = blockchain.get_mining_stats()
                print(f"📈 Mining Statistics:")
                print(f"   Total Blocks: {stats['total_blocks']}")
                print(f"   Total Mining Time: {stats['total_time']:.2f}s")
                print(f"   Total Rewards: {stats['total_rewards']} LC")
                print(f"   Average Time/Block: {stats['avg_time']:.2f}s")
                print(f"   Current Difficulty: {blockchain.difficulty}")
                print(f"   Base Reward: {blockchain.base_mining_reward} LC")
                
            elif command.startswith("difficulty"):
                parts = command.split()
                if len(parts) == 2:
                    try:
                        new_diff = int(parts[1])
                        if 1 <= new_diff <= 8:
                            blockchain.difficulty = new_diff
                            print(f"✅ Difficulty set to {new_diff}")
                            # Show available bills for this difficulty
                            bills = blockchain.difficulty_denominations.get(new_diff, {})
                            print(f"   Available Bills: {', '.join([f'${bill}' for bill in bills.keys()])}")
                        else:
                            print("❌ Difficulty must be between 1 and 8")
                    except ValueError:
                        print("❌ Please provide a valid number")
                else:
                    print(f"Current difficulty: {blockchain.difficulty}")
                    bills = blockchain.difficulty_denominations.get(blockchain.difficulty, {})
                    print(f"Available Bills: {', '.join([f'${bill}' for bill in bills.keys()])}")
                    
            elif command == "bills":
                bills = blockchain.difficulty_denominations.get(blockchain.difficulty, {})
                print(f"💰 Available Bills for Difficulty {blockchain.difficulty}:")
                for bill, multiplier in bills.items():
                    rarity = blockchain.bill_rarity.get(bill, 1)
                    reward = blockchain.base_mining_reward * multiplier
                    print(f"   ${bill} Bill: x{multiplier} → {reward} LC (Rarity: {rarity}/100)")
                    
            elif command == "validate":
                print("🔍 Validating blockchain...")
                if blockchain.is_chain_valid():
                    print("✅ Blockchain is valid and intact!")
                else:
                    print("❌ Blockchain validation failed!")
                    
            elif command == "clear":
                blockchain.clear_mempool()
                
            elif command == "bills_list" or command == "list_bills":
                list_recent_bills()
                
            elif command == "peers":
                print(f"🌐 Known Peers ({len(blockchain.peers)}):")
                for i, peer in enumerate(blockchain.peers, 1):
                    print(f"   {i:2d}. {peer}")
                    
            elif command.startswith("addpeer"):
                parts = command.split()
                if len(parts) == 2:
                    peer_address = parts[1]
                    # Validate it's in IP:PORT format
                    if ":" in peer_address and peer_address.count(":") == 1:
                        if blockchain.add_peer(peer_address):
                            print(f"✅ Added peer: {peer_address}")
                        else:
                            print(f"❌ Failed to add peer: {peer_address}")
                    else:
                        print("❌ Peer address must be in format: ip:port")
                else:
                    print("❌ Usage: addpeer <ip:port>")
                    
            elif command == "discover":
                print("🔍 Discovering peers...")
                blockchain.discover_peers()
                print(f"✅ Known peers: {len(blockchain.peers)}")
                
            elif command == "download blockchain":
                print("📥 Downloading blockchain from peers...")
                if blockchain.download_blockchain():
                    print("✅ Blockchain downloaded successfully")
                else:
                    print("❌ Failed to download blockchain")
                    
            elif command == "download mempool":
                print("📥 Downloading mempool from peers...")
                if blockchain.download_mempool():
                    print("✅ Mempool downloaded successfully")
                else:
                    print("❌ Failed to download mempool")
                
            elif command == "help":
                show_help()
                print("  bills_list - Show recently mined bills with verification links")
                
            elif command in ["exit", "quit"]:
                print("💾 Saving blockchain and exiting...")
                break
                
            else:
                print("❌ Unknown command. Type 'help' for available commands.")
                
        except KeyboardInterrupt:
            print("\n💾 Saving blockchain and exiting...")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        cleanup()
    finally:
        # Ensure cleanup runs
        cleanup()