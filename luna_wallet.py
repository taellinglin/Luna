#!/usr/bin/env python3
"""
wallet.py - LinKoin wallet with config file and P2P functionality
"""
import json
import hashlib
import secrets
import time
import os
import sys
import socket
import threading
import base64
import binascii
import select

class SimpleEncryptor:
    """Simple encryption using XOR for basic obfuscation"""
    def __init__(self, key=None):
        self.key = key or "lincoin_default_key_12345"
        # Ensure key is long enough and consistent
        while len(self.key) < 32:
            self.key += self.key
        # Use only the first 32 characters for consistency
        self.key = self.key[:32]
    
    def encrypt(self, data):
        """Simple XOR encryption"""
        if not data:
            return data
            
        encrypted = bytearray()
        key_bytes = self.key.encode('utf-8')
        data_bytes = data.encode('utf-8')
        
        for i, char in enumerate(data_bytes):
            encrypted.append(char ^ key_bytes[i % len(key_bytes)])
        
        return base64.b64encode(encrypted).decode('utf-8')
    
    def decrypt(self, encrypted_data):
        """Simple XOR decryption"""
        if not encrypted_data:
            return encrypted_data
            
        try:
            # First, check if it's already decrypted (JSON)
            if encrypted_data.strip().startswith('{') or encrypted_data.strip().startswith('['):
                return encrypted_data
                
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            decrypted = bytearray()
            key_bytes = self.key.encode('utf-8')
            
            for i, char in enumerate(encrypted_bytes):
                decrypted.append(char ^ key_bytes[i % len(key_bytes)])
            
            return decrypted.decode('utf-8')
        except (binascii.Error, UnicodeDecodeError):
            # If decryption fails, return as-is (might already be decrypted)
            return encrypted_data
        except Exception as e:
            print(f"⚠️  Decryption error: {e}")
            return encrypted_data

class WalletConfig:
    def __init__(self, config_file="wallet_config.json"):
        self.config_file = config_file
        self.config = self.load_config() or self.default_config()
    def get_ip_from_domain(self, domain_name):
        """
        Get IP address from a domain name.
        
        Args:
            domain_name (str): The domain name to resolve (e.g., 'example.com')
        
        Returns:
            str: The IP address, or None if resolution fails
        """
        try:
            # Remove http:// or https:// if present
            if domain_name.startswith(('http://', 'https://')):
                domain_name = domain_name.split('://')[1]
            
            # Remove trailing slashes and port numbers if present
            domain_name = domain_name.split('/')[0].split(':')[0]
            
            # Get IP address
            ip_address = socket.gethostbyname(domain_name)
            return ip_address
            
        except socket.gaierror:
            print(f"❌ Could not resolve domain: {domain_name}")
            return None
        except Exception as e:
            print(f"❌ Error resolving domain {domain_name}: {e}")
            return None
    def default_config(self):
        default_peer =  self.get_ip_from_domain("https://linglin.art") + ":9333"
        return {
            "network": {
                "port": 9333,
                "peers": ["63.41.180.121:9333", default_peer],
                "discovery_enabled": True,
                "max_peers": 10
            },
            "mining": {
                "mining_reward_address": "LKC_5db88dcb4e3df2cc443585234793af1d_6492dd04",
                "auto_mine": False,
                "mining_fee": 0.001
            },
            "security": {
                "encrypt_wallet": True,
                "auto_backup": True,
                "backup_interval": 3600
            },
            "rpc": {
                "enabled": True,
                "port": 9334,
                "allow_remote": False
            },
            "node": {
                "host": "127.0.0.1",
                "port": 9335
            }
        }
    
    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                print("⚠️  Corrupted config file, using defaults...")
        return None
    
    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get_peers(self):
        return self.config["network"]["peers"]
    
    def add_peer(self, peer_address):
        if peer_address not in self.config["network"]["peers"]:
            self.config["network"]["peers"].append(peer_address)
            self.save_config()
    
    def remove_peer(self, peer_address):
        if peer_address in self.config["network"]["peers"]:
            self.config["network"]["peers"].remove(peer_address)
            self.save_config()

class Wallet:
    def __init__(self, wallet_file="wallet.dat", config_file="wallet_config.json"):
        self.wallet_file = wallet_file
        self.config = WalletConfig(config_file)
        
        # Initialize encryption FIRST
        self.cipher = SimpleEncryptor()
        
        # Then load wallet
        self.addresses = self.load_wallet() or []
        self.peer_nodes = set(self.config.get_peers())
        self.running = False
        self.server_socket = None
        self.blockchain = []
        self.mempool = []
        # Automatically sync blockchain on startup
        print("🔄 Auto-syncing blockchain on startup...")
        self.load_blockchain()
        # Start P2P and RPC servers
        self.start_p2p_server()
        self.start_rpc_server()
        
        # Discover peers
        self.discover_peers()
        self.start_periodic_sync(300)
   
    def start_rpc_server(self):
        """Start RPC server to handle requests from nodes"""
        def rpc_server_thread(wallet_instance):
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            try:
                server_socket.bind(('0.0.0.0', wallet_instance.config.config["rpc"]["port"]))
                server_socket.listen(5)
                
                print(f"📡 RPC Server listening on port {wallet_instance.config.config['rpc']['port']}")
                
                while wallet_instance.running:
                    try:
                        client_socket, addr = server_socket.accept()
                        data = client_socket.recv(4096)
                        if data:
                            try:
                                message = json.loads(data.decode())
                                response = wallet_instance.handle_rpc_request(message)
                                client_socket.sendall(json.dumps(response).encode())
                            except json.JSONDecodeError:
                                client_socket.sendall(json.dumps({"status": "error", "message": "Invalid JSON"}).encode())
                        client_socket.close()
                    except Exception as e:
                        if wallet_instance.running:  # Only print if we're still running
                            print(f"RPC server client error: {e}")
            except Exception as e:
                print(f"❌ Failed to start RPC server: {e}")
            finally:
                server_socket.close()
        
        # Pass self as argument to the thread function
        threading.Thread(target=rpc_server_thread, args=(self,), daemon=True).start()
    def show_wallet_info():
        """Global function to show wallet info"""
        if wallet:
            wallet.show_wallet_info()
        else:
            print("❌ Wallet not initialized")
    def handle_rpc_request(self, message):
        """Handle RPC requests from nodes"""
        action = message.get("action")
        if action == "ping":
            return {"status": "success", "message": "pong", "timestamp": time.time()}
        
        elif action == "get_mining_address":
            return self.handle_mining_address_request()
        
        elif action == "get_balance":
            address = message.get("address")
            balance = self.get_balance(address)
            return {"status": "success", "balance": balance}
        
        elif action == "create_transaction":
            try:
                to_address = message.get("to_address")
                amount = message.get("amount")
                memo = message.get("memo", "")
                transaction = self.create_transaction(self.get_default_address(), to_address, amount, memo)
                return {"status": "success", "transaction": transaction}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        
        elif action == "get_addresses":
            return {"status": "success", "addresses": self.get_addresses()}
        
        elif action == "get_mining_reward_address":
            # Return the configured mining reward address
            mining_address = self.config.config["mining"]["mining_reward_address"]
            if not mining_address and self.addresses:
                # If no mining address is configured, use the first address
                mining_address = self.addresses[0]["address"]
                self.config.config["mining"]["mining_reward_address"] = mining_address
                self.config.save_config()
            
            return {"status": "success", "address": mining_address}
        
        return {"status": "error", "message": "Unknown action"}

    def get_balance(self, address):
        """Get balance for a specific address"""
        for wallet in self.addresses:
            if wallet["address"] == address:
                return wallet["balance"]
        return 0
    def encrypt_data(self, data):
        """Encrypt sensitive wallet data"""
        if self.config.config["security"]["encrypt_wallet"]:
            return self.cipher.encrypt(data)
        return data
    
    def decrypt_data(self, encrypted_data):
        """Decrypt wallet data"""
        if self.config.config["security"]["encrypt_wallet"]:
            return self.cipher.decrypt(encrypted_data)
        return encrypted_data
    
    def generate_address(self, label=""):
        """Generate a new cryptocurrency address with enhanced security"""
        # Generate cryptographically secure keys
        private_key = secrets.token_hex(32)  # 256-bit private key
        public_key = hashlib.sha256(private_key.encode()).hexdigest()
        
        # Create address using double hashing for security
        address_hash = hashlib.sha256(public_key.encode()).hexdigest()
        checksum = hashlib.sha256(address_hash.encode()).hexdigest()[:8]
        address = f"LKC_{address_hash[:32]}_{checksum}"
        
        wallet_data = {
            "private_key": self.encrypt_data(private_key),
            "public_key": self.encrypt_data(public_key),
            "address": address,
            "label": label,
            "created": time.time(),
            "balance": 0,
            "transactions": []
        }
        
        self.addresses.append(wallet_data)
        self.save_wallet()
        
        # Set as mining reward address if first address
        if len(self.addresses) == 1:
            self.config.config["mining"]["mining_reward_address"] = address
            self.config.save_config()
        
        return address
    
    def get_addresses(self):
        return [addr["address"] for addr in self.addresses]
    
    def get_default_address(self):
        if self.addresses:
            return self.addresses[0]["address"]
        return self.generate_address("Default Wallet")
    
    def get_address_info(self, address):
        for wallet in self.addresses:
            if wallet["address"] == address:
                return {
                    "address": wallet["address"],
                    "label": wallet["label"],
                    "balance": wallet["balance"],
                    "created": time.strftime("%Y-%m-%d %H:%M:%S", 
                              time.localtime(wallet["created"])),
                    "transaction_count": len(wallet["transactions"])
                }
        return None
    
    def create_transaction(self, from_address: str, to_address: str, amount: float, memo: str = ""):
        """Create a signed transaction ready for broadcasting"""
        for wallet in self.addresses:
            if wallet["address"] == from_address:
                if wallet["balance"] < amount:
                    raise ValueError("Insufficient balance")
                
                # Decrypt private key for signing
                private_key = self.decrypt_data(wallet["private_key"])
                
                transaction = {
                    "version": "1.0",
                    "type": "transfer",
                    "from": from_address,
                    "to": to_address,
                    "amount": amount,
                    "fee": self.config.config["mining"]["mining_fee"],
                    "timestamp": time.time(),
                    "memo": memo,
                    "nonce": secrets.token_hex(8),
                    "signature": self.sign_transaction(private_key, from_address, to_address, amount)
                }
                
                # Add to transaction history
                wallet["transactions"].append({
                    "type": "outgoing",
                    "to": to_address,
                    "amount": amount,
                    "timestamp": transaction["timestamp"],
                    "status": "pending"
                })
                
                self.save_wallet()
                return transaction
        raise ValueError("Address not found in wallet")
    
    def sign_transaction(self, private_key: str, from_addr: str, to_addr: str, amount: float):
        """Create cryptographic signature for transaction"""
        sign_data = f"{private_key}{from_addr}{to_addr}{amount}{time.time()}"
        return hashlib.sha256(sign_data.encode()).hexdigest()
    
    def verify_transaction(self, transaction):
        """Verify transaction signature"""
        # Simple verification for demo purposes
        # In a real implementation, you'd use proper cryptographic verification
        expected_data = f"{transaction['from']}{transaction['to']}{transaction['amount']}{transaction['timestamp']}"
        expected_hash = hashlib.sha256(expected_data.encode()).hexdigest()
        return transaction["signature"].startswith(expected_hash[:16])
    
    def broadcast_transaction(self, transaction):
        """Broadcast transaction to P2P network"""
        print(f"📡 Broadcasting transaction to {len(self.peer_nodes)} peers...")
        
        success_count = 0
        for peer in list(self.peer_nodes):
            try:
                if self.send_to_peer(peer, {
                    "type": "transaction",
                    "data": transaction
                }):
                    success_count += 1
            except:
                print(f"❌ Failed to broadcast to {peer}")
                self.peer_nodes.discard(peer)
        
        # Also send to node directly
        try:
            node_host = self.config.config["node"]["host"]
            node_port = self.config.config["node"]["port"]
            response = self.send_to_node({
                "action": "add_transaction",
                "transaction": transaction
            }, node_host, node_port)
            if response and response.get("status") == "success":
                success_count += 1
                print("✅ Transaction sent to node successfully")
        except Exception as e:
            print(f"❌ Failed to send to node: {e}")
        
        print(f"✅ Transaction broadcast to {success_count} destinations")
        return success_count > 0
    
    def send_to_peer(self, peer_address, message):
        """Send message to a specific peer"""
        try:
            host, port = peer_address.split(":")
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                s.connect((host, int(port)))
                s.sendall(json.dumps(message).encode())
                response = s.recv(1024)
                return json.loads(response.decode())
        except:
            return False
            
    def send_to_node(self, data, host=None, port=None):
        """Send data to the blockchain node with proper length-prefixed protocol"""
        try:
            if host is None:
                host = self.config.config["node"]["host"]
            if port is None:
                port = self.config.config["node"]["port"]
                
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(10)
                s.connect((host, int(port)))
                
                # Send message with length prefix (new protocol)
                message_json = json.dumps(data)
                message_data = message_json.encode()
                message_length = len(message_data)
                
                # Send length first (4 bytes, big-endian)
                s.sendall(message_length.to_bytes(4, 'big'))
                # Send message
                s.sendall(message_data)
                
                # Receive response with length prefix
                # First get the length (4 bytes)
                length_bytes = s.recv(4)
                if not length_bytes or len(length_bytes) != 4:
                    print("❌ Invalid response length from node")
                    return {"status": "error", "message": "Invalid response length"}
                
                response_length = int.from_bytes(length_bytes, 'big')
                
                # Now receive the actual response data
                response_data = b""
                bytes_received = 0
                
                while bytes_received < response_length:
                    chunk = s.recv(min(4096, response_length - bytes_received))
                    if not chunk:
                        break
                    response_data += chunk
                    bytes_received += len(chunk)
                
                if bytes_received == response_length:
                    try:
                        return json.loads(response_data.decode())
                    except json.JSONDecodeError as e:
                        print(f"❌ Invalid JSON response from node: {e}")
                        print(f"Raw response: {response_data[:100]}...")
                        return {"status": "error", "message": "Invalid JSON response from node"}
                else:
                    print(f"❌ Incomplete response from node: {bytes_received}/{response_length} bytes")
                    return {"status": "error", "message": "Incomplete response from node"}
                    
        except socket.timeout:
            print("❌ Node communication timeout")
            return {"status": "error", "message": "Node communication timeout"}
        except ConnectionRefusedError:
            print("❌ Connection refused - is the node running?")
            return {"status": "error", "message": "Connection refused - node not running"}
        except Exception as e:
            print(f"❌ Node communication error: {e}")
            return {"status": "error", "message": f"Node communication error: {str(e)}"}
    
    def start_p2p_server(self):
        """Start P2P server to receive transactions and blocks"""
        def server_thread():
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            try:
                self.server_socket.bind(('0.0.0.0', self.config.config["network"]["port"]))
                self.server_socket.listen(5)
                self.running = True
                
                print(f"🌐 P2P Server listening on port {self.config.config['network']['port']}")
                
                while self.running:
                    try:
                        client_socket, addr = self.server_socket.accept()
                        threading.Thread(target=self.handle_client, 
                                       args=(client_socket, addr)).start()
                    except:
                        if self.running:
                            break
            except Exception as e:
                print(f"❌ Failed to start P2P server: {e}")
        
        threading.Thread(target=server_thread, daemon=True).start()
    
    def handle_client(self, client_socket, addr):
        """Handle incoming P2P connections"""
        try:
            data = client_socket.recv(4096)
            if data:
                message = json.loads(data.decode())
                response = self.process_message(message, f"{addr[0]}:{addr[1]}")
                
                # Send response if any
                if response:
                    client_socket.sendall(json.dumps(response).encode())
                else:
                    client_socket.sendall(json.dumps({"status": "ok"}).encode())
        except:
            pass
        finally:
            client_socket.close()
    
    def process_message(self, message, peer_address):
        """Process incoming P2P messages"""
        msg_type = message.get("type")
        
        if msg_type == "transaction":
            transaction = message.get("data")
            if self.verify_transaction(transaction):
                print(f"📥 Received valid transaction from {peer_address}")
                # Add to local mempool
                self.add_to_mempool(transaction)
                
                # Relay to other peers
                self.relay_message(message, peer_address)
        
        elif msg_type == "block":
            block = message.get("data")
            print(f"📦 Received new block from {peer_address}")
            self.process_new_block(block)
                
        elif msg_type == "peer_list":
            new_peers = message.get("data", [])
            for peer in new_peers:
                if peer not in self.peer_nodes and peer != f"127.0.0.1:{self.config.config['network']['port']}":
                    self.peer_nodes.add(peer)
                    self.config.add_peer(peer)
        
        elif msg_type == "ping":
            print(f"🏓 Ping from {peer_address}")
            return {"type": "pong"}
            
        elif msg_type == "get_mining_address":
            return self.handle_mining_address_request()
        
        return None
    
    def handle_mining_address_request(self):
        """Return the mining reward address"""
        # First check if we have a configured mining reward address
        mining_address = self.config.config["mining"]["mining_reward_address"]
        
        if mining_address:
            # Verify the address exists in our wallet
            for wallet in self.addresses:
                if wallet["address"] == mining_address:
                    return {
                        "status": "success", 
                        "address": mining_address,
                        "source": "configured"
                    }
        
        # If no configured address or it doesn't exist, use the first address
        if self.addresses:
            mining_address = self.addresses[0]["address"]
            # Update config to use this address
            self.config.config["mining"]["mining_reward_address"] = mining_address
            self.config.save_config()
            
            return {
                "status": "success", 
                "address": mining_address,
                "source": "first_wallet"
            }
        else:
            # Generate a new address if none exists
            new_address = self.generate_address("Mining Reward")
            self.config.config["mining"]["mining_reward_address"] = new_address
            self.config.save_config()
            
            return {
                "status": "success", 
                "address": new_address,
                "source": "newly_created"
            }
    def debug_balances(self):
        """Debug method to see transaction processing"""
        print("\n🔍 Balance Debug:")
        print("=" * 50)
        
        for wallet in self.addresses:
            print(f"Address: {wallet['address']}")
            print(f"Balance: {wallet['balance']} LC")
            print(f"Transactions: {len(wallet['transactions'])}")
            
            # Show recent transactions
            for tx in wallet['transactions'][-5:]:  # Last 5 transactions
                tx_type = tx.get('type', 'unknown')
                amount = tx.get('amount', 0)
                status = tx.get('status', 'unknown')
                print(f"  {tx_type}: {amount} LC ({status})")
            print()
    def process_new_block(self, block):
        """Process a new block received from the network"""
        # Add to blockchain
        self.blockchain.append(block)
        
        # Update balances based on ALL transactions in the block
        self.update_balances(block.get("transactions", []))
        
        # Remove transactions from mempool that are in this block
        # Use signature or unique identifier to match transactions
        block_tx_signatures = [tx.get("signature") for tx in block.get("transactions", []) if tx.get("signature")]
        self.mempool = [tx for tx in self.mempool 
                    if tx.get("signature") not in block_tx_signatures]
        
        print(f"✅ New block added to local chain (height: {len(self.blockchain)})")
        print(f"   Contains {len(block.get('transactions', []))} transactions")
    
    def update_balances(self, transactions):
        """Update wallet balances based on transactions - reset balances first to prevent double-counting"""
        # First reset all balances to zero to prevent double-counting
        for wallet in self.addresses:
            wallet["balance"] = 0
        
        # Process all transactions in the blockchain to calculate correct balances
        for block in self.blockchain:
            for tx in block.get("transactions", []):
                # Handle mining reward transactions (they have 'to' but no 'from')
                if tx.get("type") == "reward":
                    for wallet in self.addresses:
                        if wallet["address"] == tx.get("to"):
                            wallet["balance"] += tx.get("amount", 0)
                            # Add to transaction history if not already there
                            if not any(t.get("signature") == tx.get("signature") for t in wallet["transactions"]):
                                wallet["transactions"].append({
                                    "type": "reward",
                                    "from": "mining_reward",
                                    "amount": tx.get("amount"),
                                    "timestamp": tx.get("timestamp"),
                                    "status": "confirmed",
                                    "block_height": self.blockchain.index(block) + 1
                                })
                    continue  # Skip regular transaction processing for rewards
                
                # Handle regular outgoing transactions
                if "from" in tx:
                    for wallet in self.addresses:
                        if wallet["address"] == tx.get("from"):
                            wallet["balance"] -= tx.get("amount", 0)
                            # Update transaction status
                            for wtx in wallet["transactions"]:
                                if (wtx.get("to") == tx.get("to") and 
                                    wtx.get("amount") == tx.get("amount") and 
                                    wtx.get("status") == "pending"):
                                    wtx["status"] = "confirmed"
                                    wtx["block_height"] = self.blockchain.index(block) + 1
                
                # Handle incoming transactions
                if "to" in tx:
                    for wallet in self.addresses:
                        if wallet["address"] == tx.get("to"):
                            wallet["balance"] += tx.get("amount", 0)
                            # Add to transaction history if not already there
                            if not any(t.get("signature") == tx.get("signature") for t in wallet["transactions"]):
                                wallet["transactions"].append({
                                    "type": "incoming",
                                    "from": tx.get("from", "unknown"),
                                    "amount": tx.get("amount"),
                                    "timestamp": tx.get("timestamp"),
                                    "status": "confirmed",
                                    "block_height": self.blockchain.index(block) + 1
                                })
        
        self.save_wallet()
    
    def add_to_mempool(self, transaction):
        """Add transaction to local mempool"""
        # Check if transaction already exists
        if not any(tx.get("signature") == transaction.get("signature") for tx in self.mempool):
            self.mempool.append(transaction)
            
            # Save to file
            try:
                with open("mempool.json", 'a') as f:
                    f.write(json.dumps(transaction) + '\n')
            except:
                pass
    
    def relay_message(self, message, source_peer):
        """Relay message to other peers (flooding)"""
        for peer in list(self.peer_nodes):
            if peer != source_peer:
                try:
                    self.send_to_peer(peer, message)
                except:
                    self.peer_nodes.discard(peer)
    
    def discover_peers(self):
        """Discover new peers in the network"""
        if not self.config.config["network"]["discovery_enabled"]:
            return
        
        print("🔍 Discovering peers...")
        initial_peers = list(self.peer_nodes)
        for peer in initial_peers:
            try:
                response = self.send_to_peer(peer, {
                    "type": "peer_list_request"
                })
                if response and response.get("type") == "peer_list":
                    new_peers = response.get("data", [])
                    for new_peer in new_peers:
                        if new_peer not in self.peer_nodes and new_peer != f"127.0.0.1:{self.config.config['network']['port']}":
                            self.peer_nodes.add(new_peer)
                            self.config.add_peer(new_peer)
            except:
                self.peer_nodes.discard(peer)
    def save_blockchain_to_file(self):
        """Save blockchain to local file"""
        try:
            with open("blockchain.json", 'w') as f:
                json.dump(self.blockchain, f, indent=2)
            print(f"💾 Blockchain saved to file ({len(self.blockchain)} blocks)")
        except Exception as e:
            print(f"❌ Error saving blockchain to file: {e}")
    def load_blockchain(self):
        """Load blockchain from node or file - handle partial responses"""
        # Try to get blockchain from node
        try:
            response = self.send_to_node({"action": "get_blockchain"})
            if response and response.get("status") == "success":
                # Handle both formats: direct list or dictionary with blockchain key
                if isinstance(response, list):
                    # Response is the blockchain list directly
                    self.blockchain = response
                    print(f"✅ Loaded blockchain from node ({len(self.blockchain)} blocks)")
                elif "blockchain" in response:
                    # Response is a dict with blockchain key
                    self.blockchain = response.get("blockchain", [])
                    print(f"✅ Loaded blockchain from node ({len(self.blockchain)} blocks)")
                elif "blockchain_size" in response:
                    print(f"✅ Node has {response['blockchain_size']} blocks (too large to transfer)")
                    # Load from file instead
                    self.load_blockchain_from_file()
                    return
                else:
                    print("⚠️  Node response format not recognized")
                    self.load_blockchain_from_file()
                    return
                
                # Update balances from blockchain
                for block in self.blockchain:
                    self.update_balances(block.get("transactions", []))
                
                # Save the blockchain to file for future use
                self.save_blockchain_to_file()
                return
            else:
                print(f"❌ Node response error: {response.get('message', 'Unknown error')}")
        except Exception as e:
            print(f"⚠️  Could not load from node: {e}")
        
        # Fallback to local file
        self.load_blockchain_from_file()

    def load_blockchain_from_file(self):
        """Load blockchain from local file"""
        try:
            if os.path.exists("blockchain.json"):
                with open("blockchain.json", 'r') as f:
                    self.blockchain = json.load(f)
                print(f"✅ Loaded blockchain from file ({len(self.blockchain)} blocks)")
                
                # Update balances from blockchain
                for block in self.blockchain:
                    self.update_balances(block.get("transactions", []))
            else:
                print("⚠️  No blockchain file found")
                self.blockchain = []
        except Exception as e:
            print(f"⚠️  Could not load blockchain from file: {e}")
            self.blockchain = []
    
    def save_wallet(self):
        wallet_data = {
            "addresses": self.addresses,
            "version": "1.0",
            "last_backup": time.time()
        }
        
        try:
            with open(self.wallet_file, 'w', encoding='utf-8') as f:
                if self.config.config["security"]["encrypt_wallet"]:
                    # Convert to JSON string first, then encrypt
                    json_data = json.dumps(wallet_data, indent=2)
                    encrypted_data = self.encrypt_data(json_data)
                    f.write(encrypted_data)
                else:
                    json.dump(wallet_data, f, indent=2)
                    
            print("💾 Wallet saved successfully")
            
        except Exception as e:
            print(f"❌ Error saving wallet: {e}")
            # Try to save without encryption as fallback
            try:
                with open(self.wallet_file + ".backup", 'w', encoding='utf-8') as f:
                    json.dump(wallet_data, f, indent=2)
                print("💾 Backup wallet saved without encryption")
            except:
                print("❌ Could not save backup wallet either")
    
    def load_wallet(self):
        if os.path.exists(self.wallet_file):
            try:
                with open(self.wallet_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    
                    if not content:
                        print("⚠️  Wallet file is empty, creating new wallet...")
                        return None
                    
                    if self.config.config["security"]["encrypt_wallet"]:
                        try:
                            # Try to decrypt
                            decrypted_data = self.decrypt_data(content)
                            
                            # Validate if it's proper JSON
                            wallet_data = json.loads(decrypted_data)
                            return wallet_data["addresses"]
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            print("⚠️  Failed to decrypt wallet, trying to parse as plain JSON...")
                            # Maybe it's already decrypted?
                            try:
                                wallet_data = json.loads(content)
                                return wallet_data["addresses"]
                            except json.JSONDecodeError:
                                print("⚠️  Wallet file is corrupted, creating new wallet...")
                                return None
                    else:
                        # Not encrypted, parse directly
                        wallet_data = json.loads(content)
                        return wallet_data["addresses"]
                        
            except Exception as e:
                print(f"⚠️  Error loading wallet: {e}, creating new wallet...")
                # Create backup of corrupted file
                if os.path.exists(self.wallet_file):
                    backup_name = f"{self.wallet_file}.corrupted.{int(time.time())}"
                    os.rename(self.wallet_file, backup_name)
                    print(f"💾 Backup of corrupted wallet saved as: {backup_name}")
        return None
    
    def backup_wallet(self):
        """Create encrypted wallet backup"""
        if self.config.config["security"]["auto_backup"]:
            backup_file = f"wallet_backup_{int(time.time())}.dat"
            with open(backup_file, 'w') as f:
                if self.config.config["security"]["encrypt_wallet"]:
                    wallet_data = {
                        "addresses": self.addresses,
                        "version": "1.0",
                        "last_backup": time.time()
                    }
                    encrypted_data = self.encrypt_data(json.dumps(wallet_data))
                    f.write(encrypted_data)
                else:
                    json.dump({
                        "addresses": self.addresses,
                        "version": "1.0",
                        "last_backup": time.time()
                    }, f, indent=2)
            print(f"💾 Wallet backed up to {backup_file}")
    
    def stop(self):
        """Stop P2P server and clean up"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        self.save_wallet()
    def start_periodic_sync(self, interval=300):
        """Start periodic blockchain syncing"""
        def sync_thread():
            while self.running:
                time.sleep(interval)
                print("🔄 Periodic blockchain sync...")
                self.load_blockchain()
        
        threading.Thread(target=sync_thread, daemon=True).start()
    def run_interactive_mode(self):
        """Run wallet in interactive mode"""
        print("💰 LunaCoin Wallet - Interactive Mode")
        print("Type 'help' for commands, 'exit' to quit")
        # Show sync status on startup
        print(f"⛓️  Blockchain Height: {len(self.blockchain)}")
        print(f"📋 Mempool Size: {len(self.mempool)}")
        while True:
            try:
                command = input("\nwallet> ").strip().lower()
                
                if command == "exit" or command == "quit":
                    break
                elif command == "help":
                    self.show_help()
                elif command == "setminingaddress":
                    if self.addresses:
                        print("Select mining reward address:")
                        for i, addr in enumerate(self.addresses):
                            print(f"{i+1}. {addr['address']} - {addr.get('label', 'No label')}")
                        
                        try:
                            choice = int(input("Enter number: ")) - 1
                            if 0 <= choice < len(self.addresses):
                                mining_address = self.addresses[choice]["address"]
                                self.config.config["mining"]["mining_reward_address"] = mining_address
                                self.config.save_config()
                                print(f"✅ Mining reward address set to: {mining_address}")
                            else:
                                print("❌ Invalid selection")
                        except ValueError:
                            print("❌ Please enter a valid number")
                    else:
                        print("❌ No addresses in wallet")
                elif command == "status":
                    show_wallet_info()
                elif command == "new":
                    label = input("Enter wallet label: ") or ""
                    new_addr = self.generate_address(label)
                    print(f"✅ New address: {new_addr}")
                elif command == "balance":
                    for addr in self.addresses:
                        print(f"{addr['address']}: {addr['balance']} LKC")
                # Add this to your interactive mode commands:
                elif command.startswith("addpeer"):
                    parts = command.split()
                    if len(parts) == 2:
                        peer_address = parts[1]
                        if ":" in peer_address:
                            wallet.config.add_peer(peer_address)
                            wallet.peer_nodes.add(peer_address)
                            print(f"✅ Added peer: {peer_address}")
                        else:
                            print("❌ Peer address must be in format: ip:port")
                    else:
                        print("❌ Usage: addpeer <ip:port>")
                elif command == "peers":
                    print("🌐 Connected Peers:")
                    for peer in self.peer_nodes:
                        print(f"  {peer}")
                elif command == "discover":
                    self.discover_peers()
                    print(f"🔍 Found {len(self.peer_nodes)} peers")
                elif command == "sync":
                    print("🔄 Syncing with blockchain node...")
                    response = self.send_to_node({"action": "get_blockchain_info"})
                    if response and response.get("status") == "success":
                        print(f"📊 Node info: Height {response.get('blockchain_height', 0)}, "
                            f"Pending TXs: {response.get('pending_transactions', 0)}")
                    
                    # Load full blockchain
                    self.load_blockchain()
                    print("✅ Blockchain synchronized")
                elif command == "backup":
                    self.backup_wallet()
                elif command.startswith("send"):
                    parts = command.split()
                    if len(parts) >= 3:
                        to_address = parts[1]
                        try:
                            amount = float(parts[2])
                            memo = " ".join(parts[3:]) if len(parts) > 3 else ""
                            tx = create_transaction(to_address, amount, memo)
                            if tx:
                                print(f"📤 Transaction ID: {tx['signature'][:16]}...")
                        except ValueError as e:
                            print(f"❌ Error: {e}")
                    else:
                        print("❌ Usage: send <address> <amount> [memo]")
                else:
                    print("❌ Unknown command. Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                print("\n🛑 Shutting down wallet...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def show_help(self):
        print("\n💡 Available Commands:")
        print("  status     - Show wallet status")
        print("  new        - Generate new address")
        print("  balance    - Show balances")
        print("  send       - Send coins (send <address> <amount> [memo])")
        print("  peers      - Show connected peers")
        print("  discover   - Discover new peers")
        print("  sync       - Sync with blockchain")
        print("  backup     - Backup wallet")
        print("  exit       - Exit wallet")

# Global wallet instance
wallet = None

def init_wallet():
    global wallet
    wallet = Wallet()
    return wallet

def get_default_address():
    return wallet.get_default_address()

def create_transaction(to_address: str, amount: float, memo: str = ""):
    from_address = wallet.get_default_address()
    transaction = wallet.create_transaction(from_address, to_address, amount, memo)
    
    if wallet.broadcast_transaction(transaction):
        print("✅ Transaction created and broadcast successfully!")
        return transaction
    else:
        print("❌ Transaction failed to broadcast")
        return None

def show_wallet_info():
    print("\n💼 Your Wallet:")
    print("=" * 50)
    
    for i, addr_info in enumerate(wallet.addresses):
        decrypted_key = wallet.decrypt_data(addr_info["private_key"])[:16] + "..."
        print(f"{i+1}. {addr_info['address']}")
        print(f"   Label: {addr_info.get('label', 'No label')}")
        print(f"   Balance: {addr_info['balance']} LC")
        print(f"   Transactions: {len(addr_info['transactions'])}")
        print(f"   Public Key: {wallet.decrypt_data(addr_info['public_key'])[:16]}...")
        print()
    
    print(f"🌐 Connected Peers: {len(wallet.peer_nodes)}")
    for peer in list(wallet.peer_nodes)[:5]:  # Show first 5 peers
        print(f"   {peer}")
    if len(wallet.peer_nodes) > 5:
        print(f"   ... and {len(wallet.peer_nodes) - 5} more")
        
    print(f"⛓️  Blockchain Height: {len(wallet.blockchain)}")
    print(f"📋 Mempool Size: {len(wallet.mempool)}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="LinKoin Wallet with P2P")
    parser.add_argument("command", nargs="?", help="Command to execute")
    parser.add_argument("--to", help="Recipient address for send command")
    parser.add_argument("--amount", type=float, help="Amount to send")
    parser.add_argument("--memo", help="Transaction memo")
    parser.add_argument("--peer", help="Peer address to add")
    parser.add_argument("--label", help="Label for new address")
    
    args = parser.parse_args()
    
    # Initialize wallet
    wallet = init_wallet()
    
    try:
        if args.command == "new":
            label = args.label or input("Enter wallet label: ") or ""
            new_addr = wallet.generate_address(label)
            print(f"✅ New address: {new_addr}")
            
        elif args.command == "send" and args.to and args.amount:
            tx = create_transaction(args.to, args.amount, args.memo or "")
            if tx:
                print(f"📤 Transaction ID: {tx['signature'][:16]}...")
                
        elif args.command == "peers":
            if args.peer:
                wallet.config.add_peer(args.peer)
                print(f"✅ Added peer: {args.peer}")
            else:
                print("🌐 Connected Peers:")
                for peer in wallet.peer_nodes:
                    print(f"  {peer}")
                    
        elif args.command == "discover":
            wallet.discover_peers()
            print(f"🔍 Found {len(wallet.peer_nodes)} peers")
            
        elif args.command == "backup":
            wallet.backup_wallet()
            
        elif args.command == "balance":
            for addr in wallet.addresses:
                print(f"{addr['address']}: {addr['balance']} LKC")
                
        elif args.command == "sync":
            wallet.load_blockchain()
            print("✅ Blockchain synchronized")
            
        elif args.command == "interactive" or args.command is None:
            # Run in interactive mode if no command specified
            wallet.run_interactive_mode()
        
        if args.command == "server":
            # Start in server mode (for node communication)
            print("🚀 Starting wallet server mode...")
            
            
            print("💰 Wallet server is running. Press Ctrl+C to stop.")
            print(f"📡 P2P port: {wallet.config.config['network']['port']}")
            print(f"🔌 RPC port: {wallet.config.config['rpc']['port']}")
            
            # Keep the server running
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Shutting down wallet server...")
        
        else:
            show_wallet_info()
            print("\n💡 Usage:")
            print("  python wallet.py [command] [options]")
            print("  python wallet.py interactive - Run in interactive mode")
            print("  python wallet.py new [--label LABEL]")
            print("  python wallet.py send --to ADDRESS --amount AMOUNT [--memo MEMO]")
            print("  python wallet.py peers [--peer ADDRESS:PORT]")
            print("  python wallet.py discover")
            print("  python wallet.py backup")
            print("  python wallet.py balance")
            print("  python wallet.py sync")
            
    except KeyboardInterrupt:
        print("\n🛑 Shutting down wallet...")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        wallet.stop()