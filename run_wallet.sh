#!/bin/bash
# LinKoin Wallet Wrapper Script
# Run this directly without installation

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
WALLET_SCRIPT="${SCRIPT_DIR}/luna_wallet.py"  # Changed to match your actual file name
CONFIG_FILE="${SCRIPT_DIR}/wallet_config.json"
DATA_DIR="${SCRIPT_DIR}/wallet-data"
LOG_FILE="${DATA_DIR}/wallet.log"
VERSION="1.0"

# Functions
print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_debug() { echo -e "${CYAN}[DEBUG]${NC} $1"; }

check_python() {
    print_status "Checking for Python installation..."
    
    if command -v python3 &> /dev/null; then
        PYTHON=python3
        PYTHON_VERSION=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        print_success "Found Python ${PYTHON_VERSION} (python3)"
    elif command -v python &> /dev/null; then
        PYTHON=python
        PYTHON_VERSION=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        print_success "Found Python ${PYTHON_VERSION} (python)"
    else
        print_error "Python is not installed. Please install Python 3.7 or higher."
        echo "Ubuntu/Debian: sudo apt install python3"
        echo "Fedora/RHEL: sudo dnf install python3"
        echo "Arch: sudo pacman -S python"
        exit 1
    fi

    # Check Python version
    if ! $PYTHON -c "import sys; exit(0) if sys.version_info >= (3, 7) else exit(1)"; then
        print_error "Python 3.7 or higher is required. Found version ${PYTHON_VERSION}"
        exit 1
    fi
}

check_dependencies() {
    print_status "Checking Python dependencies..."
    
    local missing_modules=()
    local required_modules=("json" "hashlib" "secrets" "socket" "threading" "base64" "binascii" "select" "time" "os" "sys")
    
    for module in "${required_modules[@]}"; do
        if ! $PYTHON -c "import ${module}" 2>/dev/null; then
            missing_modules+=("${module}")
        fi
    done

    if [ ${#missing_modules[@]} -ne 0 ]; then
        print_error "Missing required Python modules: ${missing_modules[*]}"
        exit 1
    fi
    
    print_success "All required Python modules are available"
}

check_wallet_files() {
    print_status "Checking wallet files..."
    
    if [ ! -f "$WALLET_SCRIPT" ]; then
        print_error "Wallet script not found: $WALLET_SCRIPT"
        echo "Please make sure you're running this script from the directory containing luna_wallet.py"
        exit 1
    fi
    
    if [ ! -f "$CONFIG_FILE" ]; then
        print_warning "Config file not found: $CONFIG_FILE"
        print_warning "Wallet will use default settings"
    else
        print_success "Found config file: $CONFIG_FILE"
    fi
    
    print_success "Found wallet script: $WALLET_SCRIPT"
}

setup_data_dir() {
    if [ ! -d "$DATA_DIR" ]; then
        print_status "Creating data directory: ${DATA_DIR}"
        mkdir -p "$DATA_DIR"
        chmod 700 "$DATA_DIR"
    fi

    # Copy config to data directory if it doesn't exist there but exists in script dir
    if [ -f "$CONFIG_FILE" ] && [ ! -f "${DATA_DIR}/wallet_config.json" ]; then
        cp "$CONFIG_FILE" "${DATA_DIR}/"
        print_status "Copied config file to data directory"
    fi
}

setup_logging() {
    local log_dir=$(dirname "$LOG_FILE")
    if [ ! -d "$log_dir" ]; then
        mkdir -p "$log_dir"
    fi
    
    if [ -f "$LOG_FILE" ] && [ $(wc -c < "$LOG_FILE" 2>/dev/null || echo 0) -gt 10485760 ]; then
        mv "$LOG_FILE" "${LOG_FILE}.old"
        print_status "Rotated log file"
    fi
}

show_help() {
    echo "LinKoin Wallet Wrapper Script"
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  interactive    Run in interactive mode (default)"
    echo "  server         Run as server"
    echo "  status         Show wallet status"
    echo "  new            Generate new address"
    echo "  send           Send coins"
    echo "  peers          Manage peers"
    echo "  sync           Sync with blockchain"
    echo "  help           Show this help message"
    echo "  version        Show version information"
    echo ""
    echo "Examples:"
    echo "  $0 interactive"
    echo "  $0 server"
    echo "  $0 send --to ADDRESS --amount 10.0"
    echo "  $0 status"
    echo ""
    echo "Files:"
    echo "  Wallet script: $WALLET_SCRIPT"
    echo "  Config file:   $CONFIG_FILE"
    echo "  Data directory: $DATA_DIR"
}

show_version() {
    echo "LinKoin Wallet Wrapper v${VERSION}"
    $PYTHON --version
    echo "Wallet script: $(basename "$WALLET_SCRIPT")"
    echo "Running from: $SCRIPT_DIR"
}

show_banner() {
    echo -e "${GREEN}"
    echo "=========================================="
    echo "           Luna Wallet"
    echo "       Cryptocurrency Wallet"
    echo "=========================================="
    echo -e "${NC}"
}

run_wallet() {
    local command="$1"
    
    # Only shift if we have arguments to shift
    if [ $# -gt 0 ]; then
        shift
    fi
    
    case "$command" in
        interactive|"")
            print_status "Starting Luna Wallet in interactive mode..."
            cd "$SCRIPT_DIR"
            $PYTHON "$WALLET_SCRIPT" interactive
            ;;
        server)
            print_status "Starting LinKoin Wallet server..."
            cd "$SCRIPT_DIR"
            $PYTHON "$WALLET_SCRIPT" server
            ;;
        status|new|send|peers|sync|discover|backup|balance)
            cd "$SCRIPT_DIR"
            $PYTHON "$WALLET_SCRIPT" "$command" "$@"
            ;;
        help)
            show_help
            ;;
        version)
            show_version
            ;;
        *)
            print_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Main execution
main() {
    local command="$1"
    case "$command" in
        -h|--help|help)
            show_help
            exit 0
            ;;
        -v|--version|version)
            show_version
            exit 0
            ;;
    esac

    show_banner
    
    check_python
    check_dependencies
    check_wallet_files
    setup_data_dir
    setup_logging

    print_success "All checks passed!"
    echo "Python: $($PYTHON --version)"
    echo "Wallet: $(basename "$WALLET_SCRIPT")"
    echo "Directory: $SCRIPT_DIR"
    echo "Data: $DATA_DIR"
    echo "=========================================="
    
    # Run the wallet with all arguments
    run_wallet "$@"
}

# Handle script termination
cleanup() {
    print_status "Shutting down LinKoin Wallet..."
}

trap cleanup EXIT INT TERM

# Run main function with all arguments
main "$@"
