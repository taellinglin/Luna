import os
import sys
import json
import time
import threading
import socket
import atexit
from typing import List, Dict, Set
import threading
import netifaces
import socket
import hashlib
import time
import json
from urllib.parse import urlparse
import uuid
import datetime
# Try to import netifaces, but provide fallback if not available
try:
    import netifaces
    NETIFACES_AVAILABLE = True
except ImportError:
    print("⚠️ netifaces not available, using basic network detection")
    NETIFACES_AVAILABLE = False
    
#!/usr/bin/env python3
"""
block.py - Block class for LinKoin blockchain
"""
import json
import hashlib
import time
from typing import List, Dict, Set
import os
import sys
import json 
import json
import urllib
# Try to use a simpler HTTP client that works better with PyInstaller
try:
    import urllib.request
    import urllib.error
    # Create a simple SSL context that should work with PyInstaller
    # Configure SSL at application startup
    
    # Disable SSL verification for simplicity
    SSL_AVAILABLE = True
    print("🔐 SSL configured (verification disabled)")
except ImportError as e:
    print(f"⚠️ SSL not available: {e}")
    SSL_AVAILABLE = False

class SimpleHTTPClient:
    """A simple HTTP client that works with PyInstaller"""
    
    @staticmethod
    def get(url, timeout=30):
        """Simple HTTP GET request"""
        try:
            if SSL_AVAILABLE:
                # Use urllib with SSL disabled
                req = urllib.request.Request(url)
                response = urllib.request.urlopen(req, timeout=timeout)
                return response.read().decode('utf-8')
            else:
                # Fallback: try without SSL for http URLs
                if url.startswith('https://'):
                    # Try http instead
                    http_url = url.replace('https://', 'http://', 1)
                    print(f"⚠️  SSL not available, trying HTTP: {http_url}")
                    req = urllib.request.Request(http_url)
                    response = urllib.request.urlopen(req, timeout=timeout)
                    return response.read().decode('utf-8')
                else:
                    req = urllib.request.Request(url)
                    response = urllib.request.urlopen(req, timeout=timeout)
                    return response.read().decode('utf-8')
        except Exception as e:
            print(f"❌ HTTP request failed for {url}: {e}")
            return None
    
    @staticmethod
    def get_json(url, timeout=30):
        """Get JSON data from URL"""
        response_text = SimpleHTTPClient.get(url, timeout)
        if response_text:
            try:
                return json.loads(response_text)
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error for {url}: {e}")
        return None
class DataManager:
    """Manages data storage with EXE directory fallback to ProgramData"""
    
    @staticmethod
    def get_data_dir():
        """Get the best data directory (EXE dir first, then ProgramData fallback)"""
        # First try: Same directory as the executable
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            exe_dir = os.path.dirname(sys.executable)
        else:
            # Running as script
            exe_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Test if we can write to the EXE directory
        exe_data_dir = os.path.join(exe_dir, 'data')
        try:
            # Create data subdirectory and test write permissions
            os.makedirs(exe_data_dir, exist_ok=True)
            test_file = os.path.join(exe_data_dir, 'write_test.tmp')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            print(f"📁 Using EXE directory for data: {exe_data_dir}")
            return exe_data_dir
        except (PermissionError, OSError):
            # Fallback: ProgramData directory
            if os.name == 'nt':  # Windows
                programdata = os.environ.get('PROGRAMDATA', 'C:\\ProgramData')
                programdata_dir = os.path.join(programdata, 'Luna Suite')
            else:  # Linux/Mac
                programdata_dir = '/var/lib/luna-suite'
            
            # Create ProgramData directory
            os.makedirs(programdata_dir, exist_ok=True)
            print(f"📁 Using ProgramData directory for data: {programdata_dir}")
            return programdata_dir
    
    @staticmethod
    def get_file_path(filename):
        """Get full path for a data file with fallback support"""
        data_dir = DataManager.get_data_dir()
        return os.path.join(data_dir, filename)
    
    @staticmethod
    def save_json(filename, data):
        """Save data to JSON file with fallback support"""
        file_path = DataManager.get_file_path(filename)
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            print(f"💾 Saved {filename} to {file_path}")
            return True
        except Exception as e:
            print(f"❌ Error saving {filename}: {e}")
            return False
    
    @staticmethod
    def load_json(filename, default=None):
        """Load data from JSON file with fallback support"""
        if default is None:
            default = []
        
        file_path = DataManager.get_file_path(filename)
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print(f"⚠️  {filename} not found, using default")
                return default
        except Exception as e:
            print(f"❌ Error loading {filename}: {e}")
            return default
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
        """Mine the block with real-time progress tracking and rainbow colors"""
        target = "0" * difficulty
        start_time = time.time()
        hashes_tried = 0
        last_update = start_time
        last_hash_count = 0
        hash_rates = []
        
        # Clear screen and show initial header
        self._clear_mining_display()
        print(f"🎯 Mining Target: {target}")
        print("⛏️  Starting mining operation...")
        print("-" * 60)
        
        # Initial empty progress display (we'll update these lines)
        progress_lines = 8  # Number of lines we'll be updating
        for _ in range(progress_lines):
            print()  # Reserve lines for progress display
        
        line_positions = {}  # Track where each line starts
        
        while self.hash[:difficulty] != target:
            self.nonce += 1
            hashes_tried += 1
            self.hash = self.calculate_hash()
            
            current_time = time.time()
            time_since_update = current_time - last_update
            
            if time_since_update >= 0.3:  # More frequent updates for smoother display
                elapsed = current_time - start_time
                current_hash_rate = (hashes_tried - last_hash_count) / time_since_update
                hash_rates.append(current_hash_rate)
                avg_hash_rate = sum(hash_rates) / len(hash_rates) if hash_rates else 0
                
                # Calculate progress (estimated)
                hashes_per_target = 16 ** difficulty
                progress = min(self.nonce / hashes_per_target, 0.99) if hashes_per_target > 0 else 0
                eta = (hashes_per_target - self.nonce) / avg_hash_rate if avg_hash_rate > 0 else 0
                
                # Update progress display
                self._update_mining_display(
                    hashes_tried, avg_hash_rate, self.hash, elapsed, 
                    difficulty, target, progress, eta, progress_lines
                )
                
                if progress_callback:
                    progress_callback({
                        'hashes': hashes_tried,
                        'hash_rate': avg_hash_rate,
                        'current_hash': self.hash,
                        'elapsed_time': elapsed,
                        'nonce': self.nonce,
                        'progress': progress,
                        'eta': eta
                    })
                
                last_update = current_time
                last_hash_count = hashes_tried
        
        # Mining completed
        end_time = time.time()
        self.mining_time = end_time - start_time
        self.hash_rate = self.nonce / self.mining_time if self.mining_time > 0 else 0
        
        # Final display with celebration
        self._display_mining_complete(self.mining_time, self.nonce, self.hash_rate, self.hash)
        
        return True

    def _clear_mining_display(self):
        """Clear the mining display area"""
        print("\033[2J\033[H")  # Clear screen and move to top

    def _update_mining_display(self, hashes_tried, hash_rate, current_hash, elapsed_time, 
                            difficulty, target, progress, eta, total_lines):
        """Update the mining progress display with rainbow colors"""
        # Move cursor to the beginning of the progress display area
        print(f"\033[{total_lines + 3}F")  # +3 for header lines
        
        # ROYGBIV rainbow colors 🌈
        colors = [
            '\033[91m',  # Red
            '\033[93m',  # Yellow  
            '\033[92m',  # Green
            '\033[96m',  # Cyan
            '\033[94m',  # Blue
            '\033[95m',  # Magenta
            '\033[97m',  # White
        ]
        reset = '\033[0m'
        bold = '\033[1m'
        
        # Get color based on progress (cycle through rainbow)
        color_index = int(progress * len(colors)) % len(colors)
        current_color = colors[color_index]
        
        progress_bar = self._create_rainbow_progress_bar(progress, 30)
        hash_rate_str = self._format_hash_rate(hash_rate)
        
        # Display each line with proper clearing
        lines = [
            f"{bold}{current_color}⛏️  Mining Block #{self.index} | Difficulty: {difficulty}{reset}",
            f"{colors[1]}🎯 Target: {target} {reset}",
            f"{colors[2]}📊 Progress: {progress_bar} {progress:.1%}{reset}",
            f"{colors[3]}⚡ Hash Rate: {hash_rate_str}{reset}",
            f"{colors[4]}🔢 Hashes: {hashes_tried:,} | Nonce: {self.nonce:,}{reset}",
            f"{colors[5]}⏱️  Elapsed: {elapsed_time:.1f}s | ETA: {eta:.1f}s{reset}",
            f"{colors[6]}🔍 Current Hash: {current_hash[:32]}...{reset}",
            f"{colors[0]}📈 Matching: {current_hash[:difficulty]}{'🎯' if current_hash[:difficulty] == target else '...'}{reset}"
        ]
        
        # Print all lines, clearing any leftover text from previous update
        for i, line in enumerate(lines):
            # Clear the line first, then print new content
            print("\033[K" + line)  # \033[K clears from cursor to end of line
            
            # If we have fewer lines than reserved, clear the extra ones
            if i == len(lines) - 1 and len(lines) < total_lines:
                for j in range(len(lines), total_lines):
                    print("\033[K")  # Clear remaining lines
        
        # Ensure we flush the output
        import sys
        sys.stdout.flush()

    def _create_rainbow_progress_bar(self, progress, width=30):
        """Create a simpler rainbow-colored progress bar"""
        filled = int(width * progress)
        empty = width - filled
        
        # Use a single color that changes with progress
        colors = ['\033[91m', '\033[93m', '\033[92m', '\033[96m', '\033[94m', '\033[95m']
        reset = '\033[0m'
        
        # Pick color based on progress
        color_index = int(progress * len(colors)) % len(colors)
        color = colors[color_index]
        
        return f"{color}[{'█' * filled}{'░' * empty}]{reset}"

    def _format_hash_rate(self, hash_rate):
        """Format hash rate with colors"""
        if hash_rate >= 1_000_000:
            color = '\033[95m'  # Magenta for MH/s
            return f"{color}{hash_rate/1_000_000:.2f} MH/s\033[0m"
        elif hash_rate >= 1_000:
            color = '\033[96m'  # Cyan for kH/s
            return f"{color}{hash_rate/1_000:.2f} kH/s\033[0m"
        else:
            color = '\033[92m'  # Green for H/s
            return f"{color}{hash_rate:.2f} H/s\033[0m"

    def _display_mining_complete(self, mining_time, total_nonce, final_hash_rate, final_hash):
        """Display mining completion with celebration"""
        # Clear the display area
        print("\033[2J\033[H")  # Clear screen
        
        # Rainbow celebration message
        colors = ['\033[91m', '\033[93m', '\033[92m', '\033[96m', '\033[94m', '\033[95m']
        reset = '\033[0m'
        bold = '\033[1m'
        
        print("=" * 70)
        for i, char in enumerate("✅ BLOCK MINED SUCCESSFULLY! 🎉"):
            color = colors[i % len(colors)]
            print(f"{bold}{color}{char}{reset}", end="")
        print()
        print("=" * 70)
        
        stats = [
            f"📦 Block #{self.index} mined in {mining_time:.2f} seconds",
            f"⚡ Final Hash Rate: {self._format_hash_rate(final_hash_rate)}",
            f"🔢 Total Nonce Attempts: {total_nonce:,}",
            f"🏁 Final Hash: {final_hash}",
            f"📏 Hash Length: {len(final_hash)} characters",
            f"🎯 Target Matched: {final_hash[:self._get_difficulty_from_hash(final_hash)]}"
        ]
        
        for i, stat in enumerate(stats):
            color = colors[i % len(colors)]
            print(f"{color}{stat}{reset}")
        
        print("=" * 70)
        
        # Fun celebration ASCII art
        celebration_art = [
            "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐恭喜⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐",
        ]
        
        for line in celebration_art:
            print(f"{colors[2]}{line}{reset}")

    def _create_progress_bar(self, progress, width=20):
        """Create a visual progress bar"""
        filled = int(width * progress)
        empty = width - filled
        return f"[{'█' * filled}{'░' * empty}]"

    def _get_difficulty_from_hash(self, hash_str):
        """Calculate difficulty by counting leading zeros"""
        difficulty = 0
        for char in hash_str:
            if char == '0':
                difficulty += 1
            else:
                break
        return difficulty
    def mine_block_with_animation(self, difficulty: int):
        """Mine block with animated progress display"""
        import sys
        import threading
        
        # Animation characters
        animation_chars = ["⛏️ ", "🔨", "⚒️ ", "🛠️ "]
        animation_index = 0
        stop_animation = False
        
        def animate():
            nonlocal animation_index
            while not stop_animation:
                print(f"\r{animation_chars[animation_index]} Mining...", end="", flush=True)
                animation_index = (animation_index + 1) % len(animation_chars)
                time.sleep(0.3)
        
        # Start animation thread
        animation_thread = threading.Thread(target=animate, daemon=True)
        animation_thread.start()
        
        try:
            result = self.mine_block(difficulty)
            stop_animation = True
            time.sleep(0.4)  # Let animation finish
            print("\r" + " " * 50 + "\r", end="")  # Clear animation line
            return result
        except Exception as e:
            stop_animation = True
            print(f"\r❌ Mining failed: {e}")
            return False
class Blockchain:
    def __init__(self, node_address=None):
        # Use ProgramData for all file storage
        self.chain_file = "blockchain.json"
        self.verification_base_url = "https://bank.linglin.art/verify/"
        self.chain = self.load_chain() or [self.create_genesis_block()]
        
        # Multi-difficulty mining configuration
        self.difficulty = 6
        self.pending_transactions = []
        self.base_mining_reward = 10
        self.total_blocks_mined = 0
        self.total_mining_time = 0
        self.is_mining = False
        self.wallet_server_running = False
        self.stop_event = threading.Event()
        
        # Anti-spam measures
        self.user_limits = {}  # Track bills per user
        self.max_mining_attempts = 3  # Maximum attempts per bill
        
        # P2P Networking
        self.node_address = node_address or self.generate_node_address()
        self.peers: Set[str] = set()
        self.peer_discovery_running = False
        self.peer_discovery_interval = 300
        self.known_peers_file = "known_peers.json"
        self.load_known_peers()
        
        # Mining progress tracking
        self.current_mining_hashes = 0
        self.current_hash_rate = 0
        self.current_hash = ""
        
        # Multi-difficulty mining configuration
        self.difficulty_requirements = {
            "1": {"difficulty": 0, "min_time": 0.1, "max_attempts": 10},
            "10": {"difficulty": 1, "min_time": 1, "max_attempts": 8},
            "100": {"difficulty": 2, "min_time": 5, "max_attempts": 6},
            "1000": {"difficulty": 3, "min_time": 15, "max_attempts": 4},
            "10000": {"difficulty": 4, "min_time": 30, "max_attempts": 3},
            "100000": {"difficulty": 5, "min_time": 60, "max_attempts": 2},
            "1000000": {"difficulty": 6, "min_time": 300, "max_attempts": 2},
            "10000000": {"difficulty": 7, "min_time": 900, "max_attempts": 1},
            "100000000": {"difficulty": 8, "min_time": 3600, "max_attempts": 1}
        }
        
        # Bill denominations and rarity
        self.difficulty_denominations = {
            1: {"1": 1, "10": 2},
            2: {"1": 1, "10": 2, "100": 3},
            3: {"10": 2, "100": 3, "1000": 4},
            4: {"100": 3, "1000": 4, "10000": 5},
            5: {"1000": 4, "10000": 5, "100000": 6},
            6: {"10000": 5, "100000": 6, "1000000": 7},
            7: {"100000": 6, "1000000": 7, "10000000": 8},
            8: {"1000000": 7, "10000000": 8, "100000000": 9}
        }

        self.bill_rarity = {
            "1": 100, "10": 90, "100": 80, "1000": 70,
            "10000": 60, "100000": 50, "1000000": 40,
            "10000000": 30, "100000000": 20
        }
        
        # User limits per denomination
        self.denomination_limits = {
            "1": 100,      # Can create many 1's
            "10": 50,      # Fewer 10's
            "100": 25,     # Even fewer 100's
            "1000": 10,
            "10000": 5,
            "100000": 3,
            "1000000": 2,
            "10000000": 1,
            "100000000": 1
        }
        
        self.sync_all()

    def save_chain(self):
        """Save blockchain to storage - FIXED WITH DEBUG"""
        try:
            chain_data = []
            for block in self.chain:
                chain_data.append({
                    "index": block.index,
                    "previous_hash": block.previous_hash,
                    "timestamp": block.timestamp,
                    "transactions": block.transactions,  # ✅ Make sure this includes ALL transactions
                    "nonce": block.nonce,
                    "hash": block.hash,
                    "mining_time": block.mining_time
                })
            
            print(f"💾 Attempting to save {len(chain_data)} blocks to {self.chain_file}")
            
            success = DataManager.save_json(self.chain_file, chain_data)
            if success:
                print(f"✅ Blockchain saved successfully with {len(chain_data)} blocks")
            else:
                print("❌ Blockchain save failed!")
                
            return success
        except Exception as e:
            print(f"💥 CRITICAL: Error saving blockchain: {e}")
            import traceback
            traceback.print_exc()
            return False

    def generate_node_address(self):
        """Generate a unique node address"""
        return f"node_{hashlib.sha256(str(time.time()).encode()).hexdigest()[:12]}"

    def load_known_peers(self):
        """Load known peers from storage"""
        try:
            peers_data = DataManager.load_json(self.known_peers_file, [])
            self.peers = set(peers_data)
            print(f"✅ Loaded {len(self.peers)} known peers")
        except Exception as e:
            print(f"⚠️  Could not load known peers: {e}")
            self.peers = set()

    def save_known_peers(self):
        """Save known peers to storage"""
        try:
            DataManager.save_json(self.known_peers_file, list(self.peers))
        except Exception as e:
            print(f"❌ Error saving known peers: {e}")

    def add_peer(self, peer_address: str):
        """Add a peer if it's not ourselves"""
        if "://" in peer_address:
            url = urlparse(peer_address)
            peer_address = f"{url.hostname}:{url.port or 9335}"
        
        if not peer_address or ":" not in peer_address:
            print(f"❌ Invalid peer address format: {peer_address}")
            return False
        
        # Skip self-connections
        local_ips = ["127.0.0.1", "localhost", "0.0.0.0", "::1"]
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            local_ips.extend([local_ip, f"{local_ip}:9335"])
            
            if NETIFACES_AVAILABLE:
                for interface in netifaces.interfaces():
                    addrs = netifaces.ifaddresses(interface)
                    if netifaces.AF_INET in addrs:
                        for addr in addrs[netifaces.AF_INET]:
                            ip = addr['addr']
                            local_ips.extend([ip, f"{ip}:9335"])
        except:
            pass
        
        if peer_address in local_ips:
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
            except Exception as e:
                print(f"   ❌ Error discovering peers from {peer}: {e}")
        
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
                time.sleep(60)
        
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
            if "://" in peer_address:
                url = urlparse(peer_address)
                host = url.hostname
                port = url.port or 9335
            else:
                if ":" in peer_address:
                    host, port_str = peer_address.split(":", 1)
                    port = int(port_str)
                else:
                    host = peer_address
                    port = 9335
            
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                s.connect((host, port))
                
                data_json = json.dumps(data)
                data_length = len(data_json.encode())
                s.sendall(data_length.to_bytes(4, 'big'))
                s.sendall(data_json.encode())
                
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

    def download_from_web(self, resource_type="blockchain"):
        """Download blockchain or Genesis GTX data from web server using simple HTTP client"""
        base_url = "https://bank.linglin.art/"
        url = f"{base_url}{resource_type}"
        
        try:
            print(f"🌐 Downloading {resource_type} from {url}...")
            
            # First, let's try to get the raw response to see what we're getting
            response_text = SimpleHTTPClient.get(url)
            if response_text:
                print(f"📥 Raw response length: {len(response_text)} characters")
                
                try:
                    data = json.loads(response_text)
                except json.JSONDecodeError as e:
                    print(f"❌ JSON decode error: {e}")
                    return False
            else:
                print(f"❌ No response from {url}")
                return False
            
            if data is not None:
                if resource_type == "blockchain":
                    new_chain = []
                    for block_data in data:
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
                        # Check if save_chain method exists before calling it
                        if hasattr(self, 'save_chain') and callable(getattr(self, 'save_chain')):
                            self.save_chain()
                        else:
                            # Fallback: save directly
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
                            DataManager.save_json(self.chain_file, chain_data)
                        print(f"✅ Downloaded and validated blockchain with {len(data)} blocks")
                        
                        # Try to extract Genesis GTX transactions, but don't fail if it errors
                        try:
                            genesis_gtx_count = self.extract_genesis_gtx_from_chain()
                            print(f"🔍 Found {genesis_gtx_count} Genesis GTX transactions in downloaded blockchain")
                        except Exception as e:
                            print(f"⚠️  Could not extract Genesis GTX transactions: {e}")
                            genesis_gtx_count = 0
                        
                        return True
                    else:
                        print("❌ Downloaded blockchain failed validation")
                        return False
                
                elif resource_type == "mempool":
                    print("⚠️  Mempool download is deprecated - Genesis GTX transactions are stored in blockchain")
                    return self.handle_mempool_download(data)
            else:
                print(f"❌ No data received from {url}")
                return False
                
        except Exception as e:
            print(f"❌ Error downloading {resource_type}: {e}")
            import traceback
            traceback.print_exc()
            return False

    def handle_mempool_download(self, data):
        """Handle mempool download data extraction"""
        print("🔍 Extracting Genesis GTX transactions from downloaded data...")
        
        genesis_gtx_transactions = []
        if isinstance(data, list):
            # If it's a list of transactions, filter for Genesis GTX
            for tx in data:
                if self.is_genesis_gtx_transaction(tx):
                    genesis_gtx_transactions.append(tx)
        elif isinstance(data, dict) and 'transactions' in data:
            # If it's wrapped in a dict with transactions key
            for tx in data['transactions']:
                if self.is_genesis_gtx_transaction(tx):
                    genesis_gtx_transactions.append(tx)
        
        if genesis_gtx_transactions:
            print(f"✅ Found {len(genesis_gtx_transactions)} Genesis GTX transactions")
            # Add to pending transactions for mining
            added_count = 0
            for tx in genesis_gtx_transactions:
                try:
                    if self.add_transaction(tx):
                        added_count += 1
                except Exception as e:
                    print(f"❌ Error adding transaction: {e}")
                    continue
            print(f"📥 Added {added_count} Genesis GTX transactions to pending pool")
            return added_count > 0
        else:
            print("❌ No Genesis GTX transactions found in downloaded data")
            return False

    def is_genesis_gtx_transaction(self, tx):
        """Check if a transaction is a Genesis GTX transaction"""
        if not isinstance(tx, dict):
            return False
        
        # Check for various indicators of Genesis GTX transactions
        if tx.get("type") in ["genesis_gtx", "GTX_Genesis", "genesis"]:
            return True
        
        if tx.get("category") == "Genesis GTX":
            return True
        
        # Check for serial number and denomination (common in bill-based systems)
        if tx.get("serial_number") and tx.get("denomination"):
            return True
        
        # Check for specific Genesis GTX patterns
        if "genesis" in str(tx.get("type", "")).lower() or "gtx" in str(tx.get("type", "")).lower():
            return True
        
        return False

    def extract_genesis_gtx_from_chain(self):
        """Extract Genesis GTX transactions from the current blockchain and add to pending pool"""
        genesis_gtx_count = 0
        
        for block in self.chain:
            for tx in block.transactions:
                if self.is_genesis_gtx_transaction(tx):
                    # Make sure the transaction has required fields
                    if not isinstance(tx, dict):
                        continue
                        
                    # Create a clean copy to avoid modifying the original
                    transaction = tx.copy()
                    
                    # Add basic fields if missing
                    if "timestamp" not in transaction:
                        transaction["timestamp"] = time.time()
                    
                    # Ensure it has a type identifier
                    if "type" not in transaction:
                        transaction["type"] = "genesis_gtx"
                    
                    # Add to pending transactions if not already there
                    try:
                        if self.add_transaction(transaction):
                            genesis_gtx_count += 1
                    except Exception as e:
                        print(f"❌ Error adding Genesis GTX transaction: {e}")
                        continue
        
        print(f"🔍 Extracted {genesis_gtx_count} Genesis GTX transactions from blockchain")
        return genesis_gtx_count

    def sync_all(self):
        """One command to sync everything"""
        print("🔄 Starting complete network synchronization...")
        
        # Try web sync first
        print("🌐 Trying to sync from linglin.art...")
        web_success = self.download_from_web("blockchain")
        
        if not web_success:
            print("❌ Could not sync blockchain from web")
        else:
            print("✅ Successfully synced from web")
        
        # Sync mempool
        print("🌐 Trying to sync mempool from linglin.art...")
        web_mempool_success = self.download_from_web("mempool")
        
        if not web_mempool_success:
            print("❌ Could not sync mempool from web")
        else:
            print("✅ Successfully synced mempool from web")
        
        # Discover peers
        self.discover_peers()
        
        print("✅ Complete synchronization finished")

    def download_blockchain(self, peer_address: str = None):
        """Download blockchain from a peer, fall back to web server if peers fail"""
        peers_to_try = [peer_address] if peer_address else list(self.peers)
        
        print(f"🔍 Current peers: {list(self.peers)}")
        print(f"🔍 Peers to try: {peers_to_try}")
        
        # First try peers
        if peers_to_try:
            for peer in peers_to_try:
                try:
                    print(f"📥 Attempting to download blockchain from {peer}...")
                    
                    ping_response = self.send_to_peer(peer, {"action": "ping"}, timeout=5)
                    if not ping_response or ping_response.get("status") != "success":
                        print(f"❌ Peer {peer} is not responding to ping")
                        continue
                        
                    print(f"✅ Peer {peer} is reachable, requesting blockchain...")
                    
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
                                print(f"✅ Blockchain updated to {len(self.chain)} blocks")
                                return True
                            else:
                                print("❌ Downloaded blockchain failed validation")
                        else:
                            print("ℹ️  Peer has same or shorter chain, keeping current blockchain")
                            return True  # Not an error, just no update needed
                    else:
                        error_msg = response.get("message", "Unknown error")
                        print(f"❌ Failed to download blockchain from {peer}: {error_msg}")
                        
                except socket.timeout:
                    print(f"❌ Timeout connecting to {peer}")
                except ConnectionRefusedError:
                    print(f"❌ Connection refused by {peer}")
                except Exception as e:
                    print(f"❌ Error downloading blockchain from {peer}: {e}")
        
        # If no peers available or all peers failed, try web server
        print("🌐 No peers available or all failed, trying web server...")
        return self.download_from_web("blockchain")

    def save_mempool(self):
        """Save pending transactions to storage"""
        try:
            DataManager.save_json("mempool.json", self.pending_transactions)
        except Exception as e:
            print(f"❌ Error saving mempool: {e}")

    def download_mempool(self, peer_address: str = None):
        """Download mempool transactions from a peer, with web fallback"""
        peers_to_try = [peer_address] if peer_address else list(self.peers)
        new_transactions = 0
        
        # First try peers
        if peers_to_try:
            print(f"🔍 Trying {len(peers_to_try)} peer(s) for mempool download...")
            
            for peer in peers_to_try:
                try:
                    print(f"📥 Downloading mempool from {peer}...")
                    response = self.send_to_peer(peer, {"action": "get_pending_transactions"})
                    
                    if response and response.get("status") == "success":
                        transactions = response.get("transactions", [])
                        
                        for tx in transactions:
                            if not any(t.get("signature") == tx.get("signature") for t in self.pending_transactions):
                                self.pending_transactions.append(tx)
                                new_transactions += 1
                        
                        self.save_mempool()
                        
                        print(f"✅ Added {new_transactions} new transactions from {peer}'s mempool")
                        return True
                    else:
                        print(f"❌ Failed to download mempool from {peer}")
                except Exception as e:
                    print(f"❌ Error downloading mempool from {peer}: {e}")
        
        # If no peers available or all peers failed, try web fallback
        print("🌐 No peers available or all failed, trying web fallback...")
        return self.download_mempool_from_web()
    def is_transaction_in_blockchain(self, transaction):
        """Check if a transaction already exists in the blockchain"""
        for block in self.chain:
            for block_tx in block.transactions:
                if self.transactions_equal(block_tx, transaction):
                    return True
        return False
    def download_mempool_from_web(self):
        """Download mempool from https://bank.linglin.art/mempool"""
        web_url = "https://bank.linglin.art/mempool"
        new_transactions = 0
        
        try:
            print(f"📥 Downloading mempool from {web_url}...")
            
            # Use the existing SimpleHTTPClient
            response_text = SimpleHTTPClient.get(web_url)
            
            if response_text:
                try:
                    data = json.loads(response_text)
                    
                    # Handle different response formats
                    if isinstance(data, list):
                        transactions = data
                    elif isinstance(data, dict) and 'transactions' in data:
                        transactions = data['transactions']
                    else:
                        print(f"❌ Unexpected mempool format from web: {type(data)}")
                        return False
                    
                    for tx in transactions:
                        # Check if transaction already exists
                        if not any(t.get("signature") == tx.get("signature") for t in self.pending_transactions):
                            # Also check if it's already mined in blockchain
                            if not self.is_transaction_mined(tx):
                                self.pending_transactions.append(tx)
                                new_transactions += 1
                    
                    self.save_mempool()
                    
                    if new_transactions > 0:
                        print(f"✅ Added {new_transactions} new transactions from web mempool")
                    else:
                        print("ℹ️  No new transactions found in web mempool")
                    
                    return new_transactions > 0
                    
                except json.JSONDecodeError as e:
                    print(f"❌ JSON decode error from web mempool: {e}")
                    return False
            else:
                print("❌ No response from web mempool")
                return False
                
        except Exception as e:
            print(f"❌ Error downloading mempool from web: {e}")
            return False

    def validate_chain(self, chain: List[Block]) -> bool:
        """Validate a blockchain"""
        for i in range(1, len(chain)):
            current_block = chain[i]
            previous_block = chain[i-1]
            
            if current_block.hash != current_block.calculate_hash():
                print(f"❌ Block {i} hash is invalid!")
                return False
            
            if current_block.previous_hash != previous_block.hash:
                print(f"❌ Block {i} previous hash doesn't match!")
                return False
        
        return True

    def generate_serial_number(self):
        """Generate a unique serial number in SN-###-###-#### format"""
        serial_id = str(uuid.uuid4().int)[:10]
        formatted_serial = f"SN-{serial_id[:3]}-{serial_id[3:6]}-{serial_id[6:10]}"
        return formatted_serial

    def clear_mempool(self):
        """Clear the mempool"""
        try:
            self.pending_transactions = []
            DataManager.save_json("mempool.json", [])
            print("✅ Mempool cleared")
            return True
        except Exception as e:
            print(f"❌ Error clearing mempool: {e}")
            return False

    def create_genesis_block(self) -> Block:
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

    def check_user_limits(self, user_id, denomination):
        """Check if user has reached their limit for a denomination"""
        if user_id not in self.user_limits:
            self.user_limits[user_id] = {}
        
        user_denom_count = self.user_limits[user_id].get(denomination, 0)
        max_allowed = self.denomination_limits.get(denomination, 1)
        
        return user_denom_count < max_allowed

    def increment_user_limit(self, user_id, denomination):
        """Increment user's count for a denomination"""
        if user_id not in self.user_limits:
            self.user_limits[user_id] = {}
        
        self.user_limits[user_id][denomination] = self.user_limits[user_id].get(denomination, 0) + 1

    def validate_transaction(self, transaction):
        """Validate a transaction before adding it to the pool"""
        try:
            # Basic validation
            if not isinstance(transaction, dict):
                return False
                
            # Check for required fields based on transaction type
            if transaction.get("type") in ["genesis_gtx", "GTX_Genesis", "genesis"]:
                # Genesis transactions need serial number and denomination
                if not transaction.get("serial_number") or not transaction.get("denomination"):
                    return False
                    
            # Regular transactions need sender, recipient, amount
            elif transaction.get("sender") and transaction.get("recipient"):
                if not isinstance(transaction.get("amount"), (int, float)) or transaction.get("amount") <= 0:
                    return False
                    
            # Check timestamp
            if not transaction.get("timestamp"):
                transaction["timestamp"] = time.time()
                
            return True
            
        except Exception as e:
            print(f"❌ Transaction validation error: {e}")
            return False
    def get_transaction_status(self, transaction_identifier):
        """Check transaction status (confirmed/pending) - CALL THIS FROM NODE"""
        # Check blockchain (confirmed transactions)
        for block_index, block in enumerate(self.chain):
            for tx in block.transactions:
                if self._transaction_matches_identifier(tx, transaction_identifier):
                    return {
                        "status": "confirmed",
                        "block_height": block.index,
                        "confirmations": len(self.chain) - block.index,
                        "timestamp": block.timestamp,
                        "transaction": tx
                    }
        
        # Check pending transactions
        for tx in self.pending_transactions:
            if self._transaction_matches_identifier(tx, transaction_identifier):
                return {
                    "status": "pending", 
                    "confirmations": 0,
                    "timestamp": tx.get("timestamp"),
                    "transaction": tx
                }
        
        return {"status": "not_found", "confirmations": 0}

    def _transaction_matches_identifier(self, tx, identifier):
        """Check if transaction matches various identifier types"""
        if not isinstance(tx, dict):
            return False
            
        # Match by transaction hash
        if tx.get("hash") == identifier:
            return True
            
        # Match by transaction ID
        if tx.get("id") == identifier:
            return True
            
        # Match by serial number (for bills)
        if tx.get("serial_number") == identifier:
            return True
            
        # Match by custom identifier
        if tx.get("transaction_id") == identifier:
            return True
            
        # Match by sender/recipient/amount combination
        if isinstance(identifier, dict):
            return (tx.get("sender") == identifier.get("sender") and
                    tx.get("recipient") == identifier.get("recipient") and
                    tx.get("amount") == identifier.get("amount"))
        
        return False

    def get_address_transactions(self, address):
        """Get all transactions for an address - CALL THIS FROM NODE"""
        transactions = []
        
        # Confirmed transactions from blockchain
        for block in self.chain:
            for tx in block.transactions:
                if (tx.get("sender") == address or tx.get("recipient") == address):
                    transactions.append({
                        **tx,
                        "status": "confirmed",
                        "block_height": block.index,
                        "confirmations": len(self.chain) - block.index,
                        "timestamp": tx.get("timestamp", block.timestamp)
                    })
        
        # Pending transactions
        for tx in self.pending_transactions:
            if (tx.get("sender") == address or tx.get("recipient") == address):
                transactions.append({
                    **tx,
                    "status": "pending",
                    "block_height": None,
                    "confirmations": 0
                })
        
        # Sort by timestamp (newest first)
        transactions.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        
        return transactions
    def add_transaction(self, transaction):
        """Add a transaction to the pending pool with validation"""
        try:
            # Validate the transaction first
            if not self.validate_transaction(transaction):
                print("❌ Transaction validation failed")
                return False
                
            # Check for duplicates in pending transactions
            for pending_tx in self.pending_transactions:
                if self.transactions_equal(pending_tx, transaction):
                    print("⚠️  Transaction already in pending pool")
                    return False
                    
            # Check for duplicates in blockchain
            for block in self.chain:
                for block_tx in block.transactions:
                    if self.transactions_equal(block_tx, transaction):
                        print("⚠️  Transaction already exists in blockchain")
                        return False
                        
            # Add to pending transactions
            self.pending_transactions.append(transaction)
            print(f"✅ Transaction added to pending pool (Total: {len(self.pending_transactions)})")
            
            # Save mempool
            self.save_mempool()
            
            # Broadcast to peers
            self.broadcast({
                "action": "new_transaction",
                "transaction": transaction
            })
            
            return True
            
        except Exception as e:
            print(f"❌ Error adding transaction: {e}")
            return False

    def transactions_equal(self, tx1, tx2):
        """Check if two transactions are essentially the same"""
        try:
            # Compare by serial number for bills
            if tx1.get("serial_number") and tx2.get("serial_number"):
                return tx1["serial_number"] == tx2["serial_number"]
                
            # Compare by hash if available
            if tx1.get("hash") and tx2.get("hash"):
                return tx1["hash"] == tx2["hash"]
                
            # Compare key fields for regular transactions
            if (tx1.get("sender") and tx2.get("sender") and 
                tx1.get("recipient") and tx2.get("recipient") and 
                tx1.get("amount") and tx2.get("amount")):
                return (tx1["sender"] == tx2["sender"] and 
                    tx1["recipient"] == tx2["recipient"] and 
                    tx1["amount"] == tx2["amount"] and
                    tx1.get("timestamp", 0) == tx2.get("timestamp", 0))
                    
            # Generic comparison as fallback
            return tx1 == tx2
            
        except Exception as e:
            print(f"❌ Error comparing transactions: {e}")
            return False
    def get_transaction_status(self, transaction_identifier):
        """Check transaction status (confirmed/pending)"""
        print(f"🔍 Searching for transaction: {transaction_identifier}")
        
        # Check blockchain (confirmed transactions)
        for block_index, block in enumerate(self.chain):
            for tx_index, tx in enumerate(block.transactions):
                if self._transaction_matches_identifier(tx, transaction_identifier):
                    confirmations = len(self.chain) - block_index
                    return {
                        "status": "confirmed",
                        "block_height": block_index,
                        "confirmations": confirmations,
                        "timestamp": block.timestamp,
                        "transaction_index": tx_index,
                        "transaction": self._sanitize_transaction(tx)  # Remove sensitive data if needed
                    }
        
        # Check pending transactions
        for tx_index, tx in enumerate(self.pending_transactions):
            if self._transaction_matches_identifier(tx, transaction_identifier):
                return {
                    "status": "pending", 
                    "confirmations": 0,
                    "timestamp": tx.get("timestamp"),
                    "transaction_index": tx_index,
                    "transaction": self._sanitize_transaction(tx)
                }
        
        return {"status": "not_found", "confirmations": 0}

    def _transaction_matches_identifier(self, tx, identifier):
        """Check if transaction matches various identifier types"""
        if not isinstance(tx, dict):
            return False
            
        # Match by transaction hash
        if tx.get("hash") and tx["hash"] == identifier:
            return True
            
        # Match by transaction ID
        if tx.get("id") and tx["id"] == identifier:
            return True
            
        # Match by serial number (for bills)
        if tx.get("serial_number") and tx["serial_number"] == identifier:
            return True
            
        # Match by signature or partial match
        if isinstance(identifier, str) and identifier in str(tx):
            return True
            
        return False

    def _sanitize_transaction(self, tx):
        """Remove sensitive data from transaction for display"""
        if not isinstance(tx, dict):
            return tx
            
        # Return a safe copy (you can exclude certain fields if needed)
        return tx.copy()

    def get_address_transactions(self, address):
        """Get all transactions for a specific address"""
        transactions = []
        
        # Check if address format is valid
        if not address or not isinstance(address, str):
            return {"error": "Invalid address format"}
        
        print(f"🔍 Searching transactions for address: {address}")
        
        # Confirmed transactions from blockchain
        for block_index, block in enumerate(self.chain):
            for tx in block.transactions:
                if (tx.get("sender") == address or tx.get("recipient") == address):
                    transactions.append({
                        **tx,
                        "status": "confirmed",
                        "block_height": block_index,
                        "confirmations": len(self.chain) - block_index,
                        "timestamp": tx.get("timestamp", block.timestamp)
                    })
        
        # Pending transactions
        for tx in self.pending_transactions:
            if (tx.get("sender") == address or tx.get("recipient") == address):
                transactions.append({
                    **tx,
                    "status": "pending",
                    "block_height": None,
                    "confirmations": 0
                })
        
        # Sort by timestamp (newest first)
        transactions.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        
        return transactions

    def get_balance(self, address):
        """Get balance for a specific address"""
        if not address or not isinstance(address, str):
            return {"error": "Invalid address format"}
        
        confirmed_balance = 0.0
        pending_balance = 0.0
        
        # Calculate from blockchain (confirmed transactions)
        for block in self.chain:
            for tx in block.transactions:
                # Received funds
                if tx.get("recipient") == address:
                    confirmed_balance += tx.get("amount", 0)
                # Sent funds
                if tx.get("sender") == address:
                    confirmed_balance -= tx.get("amount", 0)
        
        # Calculate from pending transactions (unconfirmed)
        pending_balance = confirmed_balance  # Start with confirmed balance
        
        for tx in self.pending_transactions:
            # Pending received funds
            if tx.get("recipient") == address:
                pending_balance += tx.get("amount", 0)
            # Pending sent funds
            if tx.get("sender") == address:
                pending_balance -= tx.get("amount", 0)
        
        return {
            "address": address,
            "confirmed_balance": confirmed_balance,
            "pending_balance": pending_balance,
            "effective_balance": pending_balance,  # Includes pending
            "transaction_count": len([tx for tx in self.get_address_transactions(address)])
        }
    def is_transaction_mined(self, transaction: Dict) -> bool:
        """Check if a transaction has already been mined in the blockchain"""
        tx_signature = transaction.get("signature")
        if not tx_signature:
            return False
        
        # Check all blocks in the blockchain
        for block in self.chain:
            for tx in block.transactions:
                if tx.get("signature") == tx_signature:
                    return True
                # Also check by content for GTX_Genesis transactions
                if (tx.get("type") == "GTX_Genesis" and 
                    transaction.get("type") == "GTX_Genesis" and
                    tx.get("serial_number") == transaction.get("serial_number")):
                    return True
        return False

    def determine_bill_denomination(self, block_hash):
        """Determine which bill denomination was found based on block hash and difficulty"""
        current_difficulty = self.difficulty
        available_bills = self.difficulty_denominations.get(current_difficulty, {"1": 1})
        
        hash_int = int(block_hash[:8], 16)
        
        weighted_choices = []
        for bill, multiplier in available_bills.items():
            weight = self.bill_rarity.get(bill, 1)
            weighted_choices.extend([bill] * weight)
        
        selected_bill = weighted_choices[hash_int % len(weighted_choices)]
        multiplier = available_bills[selected_bill]
        actual_reward = self.base_mining_reward * multiplier
        
        return selected_bill, multiplier, actual_reward

    def mine_pending_transactions(self, mining_reward_address=None):
        """Mine pending transactions into a new block"""
        if not self.pending_transactions:
            print("⏭️ No pending transactions to mine")
            return None
            
        print(f"⛏️ Mining block with {len(self.pending_transactions)} transactions...")
        
        # Create mining reward transaction
        reward = self.calculate_mining_reward()
        if mining_reward_address:
            mining_reward_tx = {
                "sender": "mining_reward",
                "recipient": mining_reward_address,
                "amount": reward,
                "timestamp": time.time(),
                "type": "mining_reward"
            }
            self.pending_transactions.append(mining_reward_tx)
        
        # Create and mine the new block
        previous_hash = self.chain[-1].hash if self.chain else "0"
        new_block = Block(
            len(self.chain),
            previous_hash,
            time.time(),
            self.pending_transactions.copy()  # Copy to avoid modification during mining
        )
        
        start_time = time.time()
        print(f"⛏️ Mining block {new_block.index} with difficulty {self.difficulty}...")
        
        # Mine the block
        new_block.mine_block(self.difficulty)
        
        mining_time = time.time() - start_time
        new_block.mining_time = mining_time
        
        # Add to chain
        self.chain.append(new_block)
        
        # Clear ONLY the transactions that were successfully mined
        self.pending_transactions = []
        
        # Save the updated blockchain
        self.save_chain()
        
        print(f"✅ Block {new_block.index} mined in {mining_time:.2f}s")
        print(f"📦 Block contains {len(new_block.transactions)} transactions")
        print(f"💰 Mining reward: {reward} LC")
        
        # Broadcast the new block to peers
        self.broadcast_new_block(new_block)
        
        return new_block

    def calculate_mining_reward(self):
        """Calculate the current mining reward"""
        # Simple reward scheme - could be more complex
        base_reward = self.base_mining_reward
        # Optional: halving based on block height
        halving_interval = 210000  # Bitcoin-style halving
        halvings = len(self.chain) // halving_interval
        return base_reward / (2 ** halvings)

    def broadcast_new_block(self, block):
        """Broadcast a new block to all peers"""
        block_data = {
            "index": block.index,
            "previous_hash": block.previous_hash,
            "timestamp": block.timestamp,
            "transactions": block.transactions,
            "nonce": block.nonce,
            "hash": block.hash,
            "mining_time": block.mining_time
        }
        
        successful_broadcasts = self.broadcast({
            "action": "new_block",
            "block": block_data
        })
        
        print(f"📢 Broadcast new block to {successful_broadcasts} peers")

    def start_auto_mining(self, mining_reward_address, interval=60):
        """Start automatic mining at regular intervals"""
        def mining_loop():
            while not self.stop_event.is_set():
                try:
                    if self.pending_transactions:
                        self.mine_pending_transactions(mining_reward_address)
                    else:
                        print("⏭️ No transactions to mine")
                    
                    # Wait for next mining interval
                    for i in range(interval):
                        if self.stop_event.is_set():
                            break
                        time.sleep(1)
                        
                except Exception as e:
                    print(f"❌ Mining error: {e}")
                    time.sleep(30)
        
        mining_thread = threading.Thread(target=mining_loop, daemon=True)
        mining_thread.start()
        print(f"⛏️ Auto-mining started (interval: {interval}s)")

    def get_mining_stats(self):
        if self.total_blocks_mined == 0:
            return {
                'total_blocks': 0,
                'avg_time': 0,
                'total_time': 0,
                'total_rewards': 0
            }
        
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

    def load_chain(self):
        """Load blockchain from storage - FIXED"""
        try:
            chain_data = DataManager.load_json(self.chain_file)
            if chain_data:
                chain = []
                for block_data in chain_data:
                    block = Block(
                        block_data["index"],
                        block_data["previous_hash"],
                        block_data["timestamp"],
                        block_data["transactions"],  # ✅ Critical: Load ALL transactions
                        block_data.get("nonce", 0)
                    )
                    block.hash = block_data["hash"]
                    block.mining_time = block_data.get("mining_time", 0)
                    chain.append(block)
                
                print(f"✅ Loaded blockchain with {len(chain)} blocks")
                
                # DEBUG: Check if rewards are in loaded blocks
                reward_count = 0
                for block in chain:
                    for tx in block.transactions:
                        if tx.get("type") == "reward":
                            reward_count += 1
                print(f"🔍 Found {reward_count} reward transactions in loaded chain")
                
                return chain
        except Exception as e:
            print(f"❌ Error loading blockchain: {e}")
            import traceback
            traceback.print_exc()
        return None
    def is_transaction_mined(self, transaction: Dict) -> bool:
        """Check if a transaction has already been mined in the blockchain"""
        tx_signature = transaction.get("signature")
        if not tx_signature:
            return False
        
        # Check all blocks in the blockchain
        for block in self.chain:
            for tx in block.transactions:
                if tx.get("signature") == tx_signature:
                    return True
                # Also check by content for GTX_Genesis transactions
                if (tx.get("type") == "GTX_Genesis" and 
                    transaction.get("type") == "GTX_Genesis" and
                    tx.get("serial_number") == transaction.get("serial_number")):
                    return True
        return False
    def handle_wallet_connection(self, data):
        """Handle incoming wallet requests"""
        action = data.get("action")
        MAX_RESPONSE_SIZE = 10 * 1024 * 1024

        try:
            if action == "ping":
                return {"status": "success", "message": "pong", "timestamp": time.time()}
            elif action == "get_status":  # ADD THIS NEW ACTION
                return {
                    "status": "success",
                    "node_status": {
                        "mining_enabled": True,  # Mining is always available
                        "auto_mine": False,      # No auto-mining in this version
                        "mempool_size": len(self.pending_transactions),
                        "blockchain_height": len(self.chain),
                        "difficulty": self.difficulty,
                        "peers_count": len(self.peers),
                        "is_mining": self.is_mining,
                        "node_address": self.node_address,
                        "wallet_connected": True
                    }
                }
            elif action == "add_transaction":
                transaction = data.get("transaction")
                if self.add_transaction(transaction):
                    return {"status": "success", "message": "Transaction added to mempool"}
                else:
                    return {"status": "error", "message": "Failed to add transaction (validation failed)"}
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
                if self.add_transaction(transaction):
                    return {"status": "success", "message": "Transaction added to mempool"}
                else:
                    return {"status": "error", "message": "Failed to add transaction (spam protection or duplicate)"}
            
            elif action == "get_blockchain_info":
                return {
                    "status": "success",
                    "blockchain_height": len(self.chain),
                    "latest_block_hash": self.chain[-1].hash if self.chain else None,
                    "pending_transactions": len(self.pending_transactions),
                    "difficulty": self.difficulty,
                    "base_reward": self.base_mining_reward,
                    "node_address": self.node_address,
                    "peers_count": len(self.peers),
                    "user_limits": self.denomination_limits
                }
            elif action == "start_mining":
                miner_address = data.get("miner_address", "miner_default_address")
                
                def mining_thread():
                    try:
                        success = self.mine_pending_transactions(miner_address)
                        if success:
                            print("✅ Mining completed successfully")
                    except Exception as e:
                        print(f"Mining error: {e}")
                
                thread = threading.Thread(target=mining_thread, daemon=True)
                thread.start()
                
                return {"status": "success", "message": "Mining started in background"}
            
            elif action == "get_pending_transactions":
                return {"status": "success", "transactions": self.pending_transactions}
            elif action == "get_blockchain":
                # For wallet synchronization, return ALL transactions without limits
                chain_data = []
                for block in self.chain:
                    chain_data.append({
                        "index": block.index,
                        "previous_hash": block.previous_hash,
                        "timestamp": block.timestamp,
                        "transactions": block.transactions,  # ✅ ALL transactions
                        "nonce": block.nonce,
                        "hash": block.hash,
                        "mining_time": block.mining_time
                    })
                
                # Check size and warn if large, but still send it
                estimated_size = len(json.dumps(chain_data))
                if estimated_size > MAX_RESPONSE_SIZE:
                    print(f"⚠️  Large blockchain response: {estimated_size/1024/1024:.1f}MB")
                
                return {"status": "success", "blockchain": chain_data, "total_blocks": len(self.chain)}
            
            elif action == "get_difficulty_info":
                return {
                    "status": "success",
                    "difficulty": self.difficulty,
                    "available_bills": self.difficulty_denominations.get(self.difficulty, {}),
                    "base_reward": self.base_mining_reward,
                    "difficulty_requirements": self.difficulty_requirements,
                    "denomination_limits": self.denomination_limits
                }
            
            elif action == "get_peers":
                return {"status": "success", "peers": list(self.peers)}
            
            elif action == "add_peer":
                peer_address = data.get("peer_address")
                if peer_address and self.add_peer(peer_address):
                    return {"status": "success", "message": f"Peer {peer_address} added"}
                else:
                    return {"status": "error", "message": "Failed to add peer"}
            
            elif action == "new_block":
                block_data = data.get("block")
                if block_data:
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
                    if not any(t.get("signature") == transaction.get("signature") for t in self.pending_transactions):
                        self.pending_transactions.append(transaction)
                        self.save_mempool()
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
                    
                    try:
                        length_bytes = client_socket.recv(4)
                        if not length_bytes:
                            client_socket.close()
                            continue
                        
                        message_length = int.from_bytes(length_bytes, 'big')
                        
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
        self.wallet_thread = threading.Thread(target=self.wallet_server_thread)
        self.wallet_thread.daemon = False
        self.wallet_thread.start()
        print("✅ Node wallet server thread started")

    def stop_wallet_server(self):
        """Stop the wallet server gracefully"""
        print("🛑 Stopping wallet server...")
        self.stop_event.set()
        if hasattr(self, 'wallet_thread') and self.wallet_thread.is_alive():
            self.wallet_thread.join(timeout=3.0)
        print("✅ Wallet server stopped")
def configure_import_paths():
    """Configure Python path for both frozen and normal execution"""
    
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        actual_exe_dir = os.path.dirname(sys.executable)
        
        print(f"📦 Frozen app detected:")
        print(f"   - Temp extraction: {base_path}")
        print(f"   - EXE location: {actual_exe_dir}")
        
        # Add both paths to ensure we can find our modules
        sys.path.insert(0, actual_exe_dir)
        sys.path.insert(0, base_path)
        
        # Set current working directory to where the EXE is located
        os.chdir(actual_exe_dir)
    else:
        # Normal Python execution
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, script_dir)
        os.chdir(script_dir)
    
    print(f"📁 Current working directory: {os.getcwd()}")
    print(f"📁 Files here: {[f for f in os.listdir('.') if f.endswith(('.py', '.pyd', '.dll'))]}")

# Configure paths FIRST
configure_import_paths()

# NOW try imports

def configure_ssl_for_frozen_app():
    """Configure SSL for PyInstaller frozen applications"""
    if getattr(sys, 'frozen', False):
        print("🔐 Configuring SSL for frozen app...")
        try:
            import ssl
            context = ssl.create_default_context()
            print("✅ SSL is working correctly")
        except Exception as e:
            print(f"❌ SSL error: {e}")
            import warnings
            warnings.filterwarnings('ignore', message='Unverified HTTPS request')

configure_ssl_for_frozen_app()
def load_mempool() -> List[Dict]:
    """Load Genesis GTX transactions from the blockchain instead of mempool"""
    print("🔍 Loading Genesis GTX transactions from blockchain...")
    
    genesis_gtx_transactions = []
    
    # Scan the blockchain for Genesis GTX transactions
    for block in blockchain.chain:
        for tx in block.transactions:
            # Use the same logic as is_genesis_gtx_transaction
            if blockchain.is_genesis_gtx_transaction(tx):
                genesis_gtx_transactions.append(tx)
    
    print(f"✅ Loaded {len(genesis_gtx_transactions)} Genesis GTX transactions from blockchain")
    return genesis_gtx_transactions

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
    print("  limits    - Show denomination limits")
    print("  help      - Show this help")
    print("  exit      - Exit the node")

def get_miner_address_from_wallet():
    """Get miner address directly from wallet"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            s.connect(('127.0.0.1', 9334))
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
    
    try:
        config_data = DataManager.load_json("wallet_config.json", {})
        mining_address = config_data.get("mining", {}).get("mining_reward_address", "")
        if mining_address:
            print(f"✅ Using mining address from config: {mining_address}")
            return mining_address
    except Exception as e:
        print(f"⚠️  Could not read config: {e}")
    
    return input("Enter miner address for rewards: ") or "miner_default_address"

def list_recent_bills():
    """List recent bills mined with their verification links"""
    print("\n💰 RECENTLY MINED BILLS:")
    print("="*80)
    
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

# Global blockchain instance
blockchain = Blockchain()
blockchain.node_host = "127.0.0.1"
blockchain.node_port = 9335
def handle_transaction_status(self, args):
    """Handle transaction status command"""
    if not args:
        print("❌ Usage: transaction status <transaction_id>")
        return
    
    transaction_id = args[0]
    status = self.get_transaction_status(transaction_id)
    
    print(f"\n📊 Transaction Status: {transaction_id}")
    print("=" * 50)
    
    if status["status"] == "confirmed":
        print(f"✅ Status: CONFIRMED")
        print(f"📦 Block Height: {status['block_height']}")
        print(f"🔒 Confirmations: {status['confirmations']}")
        print(f"⏰ Timestamp: {datetime.fromtimestamp(status['timestamp'])}")
        self._print_transaction_details(status["transaction"])
        
    elif status["status"] == "pending":
        print(f"⏳ Status: PENDING")
        print(f"🔒 Confirmations: 0 (waiting to be mined)")
        print(f"⏰ Timestamp: {datetime.fromtimestamp(status['timestamp'])}")
        self._print_transaction_details(status["transaction"])
        
    else:
        print(f"❌ Transaction not found")
        print("💡 Check the transaction ID or wait for it to be propagated")

def handle_address_balance(self, args):
    """Handle address balance command"""
    if not args:
        print("❌ Usage: balance <address>")
        return
    
    address = args[0]
    balance = self.get_balance(address)
    
    if "error" in balance:
        print(f"❌ Error: {balance['error']}")
        return
    
    print(f"\n💰 Balance for: {address}")
    print("=" * 50)
    print(f"✅ Confirmed Balance: {balance['confirmed_balance']} LC")
    print(f"⏳ Pending Balance: {balance['pending_balance']} LC")
    print(f"💰 Effective Balance: {balance['effective_balance']} LC")
    print(f"📊 Total Transactions: {balance['transaction_count']}")

def handle_address_transactions(self, args):
    """Handle address transactions command"""
    if not args:
        print("❌ Usage: transactions <address>")
        return
    
    address = args[0]
    transactions = self.get_address_transactions(address)
    
    if "error" in transactions:
        print(f"❌ Error: {transactions['error']}")
        return
    
    print(f"\n📊 Transaction History for: {address}")
    print("=" * 60)
    
    if not transactions:
        print("No transactions found")
        return
    
    for i, tx in enumerate(transactions):
        status_icon = "✅" if tx["status"] == "confirmed" else "⏳"
        direction = "➡️ OUT" if tx.get("sender") == address else "⬅️ IN"
        amount = tx.get("amount", 0)
        
        print(f"{i+1}. {status_icon} {direction} {amount} LC")
        print(f"   Type: {tx.get('type', 'transfer')}")
        print(f"   Status: {tx['status']} ({tx.get('confirmations', 0)} confirmations)")
        print(f"   Time: {datetime.fromtimestamp(tx.get('timestamp', 0))}")
        
        if tx.get("sender") == address:
            print(f"   To: {tx.get('recipient', 'Unknown')}")
        else:
            print(f"   From: {tx.get('sender', 'Mining Reward')}")
        
        if tx.get("hash"):
            print(f"   Hash: {tx['hash'][:16]}...")
        
        print()

def _print_transaction_details(self, tx):
    """Print formatted transaction details"""
    print("\n📄 Transaction Details:")
    print(f"   Type: {tx.get('type', 'transfer')}")
    print(f"   Amount: {tx.get('amount', 0)} LC")
    print(f"   Sender: {tx.get('sender', 'Mining Reward')}")
    print(f"   Recipient: {tx.get('recipient', 'Unknown')}")
    
    if tx.get('serial_number'):
        print(f"   Serial: {tx['serial_number']}")
    
    if tx.get('hash'):
        print(f"   Hash: {tx['hash'][:24]}...")
def cleanup():
    """Cleanup function for graceful shutdown"""
    print("\n💾 Performing cleanup...")
    blockchain.stop_wallet_server()
    blockchain.save_chain()
    blockchain.save_known_peers()
    print("✅ Cleanup completed")

# Register cleanup function
atexit.register(cleanup)

def main():
    ssl_context = configure_ssl_for_frozen_app()
    data_dir = DataManager.get_data_dir()
    print(f"📁 Data storage location: {data_dir}")
    
    blockchain.start_wallet_server()
    blockchain.start_peer_discovery()
    
    print("""
    ╔══════════════════════════════════════════════════════╗
    ║                 LUNA BLOCKCHAIN NODE                 ║
    ║           Multi-Difficulty Mining Edition            ║
    ║              with Anti-Spam Protection               ║
    ╚══════════════════════════════════════════════════════╝
    """)
    
    print(f"📦 Genesis Block: {blockchain.chain[0].hash[:12]}...")
    print(f"⛓️  Chain Height: {len(blockchain.chain)}")
    print(f"⚙️  Difficulty: {blockchain.difficulty}")
    print(f"💰 Base Mining Reward: {blockchain.base_mining_reward} LC")
    print(f"🌐 Node Address: {blockchain.node_address}")
    print(f"🔗 Known Peers: {len(blockchain.peers)}")
    print(f"💾 Data Location: {data_dir}")
    print("🛡️  Anti-spam protection: ENABLED")
    print("Type 'help' for commands\n")
    
    while True:
        try:
            command = input("\n⛓️  node> ").strip().lower()
            
            if command == "mine":
                anim_thread = threading.Thread(target=show_mining_animation, daemon=True)
                anim_thread.start()
                
                miner_address = get_miner_address_from_wallet()
                
                if miner_address:
                    success = blockchain.mine_pending_transactions(miner_address)
                    if success:
                        print("✅ Mining completed successfully")
                else:
                    print("❌ Could not get valid miner address")
                    
            elif command.startswith("transaction status"):
                parts = command.split()
                if len(parts) >= 3:
                    tx_id = parts[2]
                    blockchain.handle_transaction_status([tx_id])
                else:
                    print("❌ Usage: transaction status <transaction_id>")
                    
            elif command.startswith("balance"):
                parts = command.split()
                if len(parts) >= 2:
                    address = parts[1]
                    blockchain.handle_address_balance([address])
                else:
                    print("❌ Usage: balance <address>")
                    
            elif command.startswith("transactions"):
                parts = command.split()
                if len(parts) >= 2:
                    address = parts[1]
                    blockchain.handle_address_transactions([address])
                else:
                    print("❌ Usage: transactions <address>")
                    
            elif command == "load":
                # Load Genesis GTX transactions from the blockchain
                txs = load_mempool()  # This function now loads from blockchain
                loaded_count = 0
                for tx in txs:
                    if blockchain.add_transaction(tx):
                        loaded_count += 1
                print(f"📥 Added {loaded_count}/{len(txs)} Genesis GTX transactions to pending pool")
                
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
                print(f"   Data Location: {DataManager.get_data_dir()}")
                
            elif command == "stats":
                stats = blockchain.get_mining_stats()
                print(f"📈 Mining Statistics:")
                print(f"   Total Blocks: {stats['total_blocks']}")
                print(f"   Total Mining Time: {stats['total_time']:.2f}s")
                print(f"   Total Rewards: {stats['total_rewards']} LC")
                print(f"   Average Time/Block: {stats['avg_time']:.2f}s")
                print(f"   Current Difficulty: {blockchain.difficulty}")
                print(f"   Base Reward: {blockchain.base_mining_reward} LC")
                
            elif command == "limits":
                print("🛡️  Denomination Limits (per user):")
                for denom, limit in blockchain.denomination_limits.items():
                    print(f"   ${denom}: {limit} bills")
                    
            elif command == "check_rewards":
                print("🔍 Checking for reward transactions in node's blockchain...")
                total_rewards = 0
                
                for i, block in enumerate(blockchain.chain):
                    reward_txs = [tx for tx in block.transactions if tx.get("type") == "reward"]
                    if reward_txs:
                        print(f"Block {i}: Found {len(reward_txs)} reward transactions")
                        for tx in reward_txs:
                            print(f"  💰 Reward: {tx.get('amount', 0)} LC → {tx.get('to', 'N/A')}")
                            total_rewards += 1
                    else:
                        print(f"Block {i}: No reward transactions")
                
                print(f"📊 Total reward transactions found: {total_rewards}")
                
            elif command.startswith("difficulty"):
                parts = command.split()
                if len(parts) == 2:
                    try:
                        new_diff = int(parts[1])
                        if 1 <= new_diff <= 8:
                            blockchain.difficulty = new_diff
                            print(f"✅ Difficulty set to {new_diff}")
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
                    requirements = blockchain.difficulty_requirements.get(bill, {})
                    print(f"   ${bill} Bill: x{multiplier} → {reward} LC")
                    print(f"      Rarity: {rarity}/100 | Min Time: {requirements.get('min_time', 0)}s")
                    print(f"      Max Attempts: {requirements.get('max_attempts', 10)}")
                    
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
                print("\n📊 TRANSACTION COMMANDS:")
                print("  transaction status <tx_id> - Check transaction status and confirmations")
                print("  balance <address>          - Check address balance (confirmed + pending)")
                print("  transactions <address>     - View transaction history for an address")
                print("  bills_list                 - Show recently mined bills with verification links")
                print("  limits                     - Show denomination limits for spam protection")
                print("  check_rewards              - Check reward transactions in blockchain")
                
            elif command in ["exit", "quit"]:
                print("💾 Saving blockchain and exiting...")
                blockchain.stop_event.set()
                blockchain.save_chain()
                break
                
            else:
                print("❌ Unknown command. Type 'help' for available commands.")
                
        except KeyboardInterrupt:
            print("\n💾 Saving blockchain and exiting...")
            blockchain.stop_event.set()
            blockchain.save_chain()
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

def show_help():
    """Show available commands"""
    print("\n⛓️  BLOCKCHAIN NODE COMMANDS:")
    print("  mine                    - Mine pending transactions")
    print("  status                  - Show blockchain status")
    print("  stats                   - Show mining statistics")
    print("  validate                - Validate blockchain integrity")
    print("  difficulty [level]      - Set or show current difficulty (1-8)")
    print("  bills                   - Show available bills for current difficulty")
    print("  load                    - Load Genesis GTX transactions")
    print("  clear                   - Clear pending transactions")
    
    print("\n🌐 NETWORK COMMANDS:")
    print("  peers                   - List known peers")
    print("  addpeer <ip:port>       - Add a new peer")
    print("  discover                - Discover new peers")
    print("  download blockchain     - Download blockchain from peers")
    print("  download mempool        - Download mempool from peers")
    
    print("\n📊 TRANSACTION COMMANDS:")
    print("  transaction status <tx_id> - Check transaction status and confirmations")
    print("  balance <address>          - Check address balance (confirmed + pending)")
    print("  transactions <address>     - View transaction history for an address")
    print("  bills_list                 - Show recently mined bills")
    print("  limits                     - Show denomination limits")
    print("  check_rewards              - Check reward transactions")
    
    print("\n⚙️  SYSTEM COMMANDS:")
    print("  help                    - Show this help message")
    print("  exit/quit               - Exit the node")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        cleanup()
    finally:
        cleanup()