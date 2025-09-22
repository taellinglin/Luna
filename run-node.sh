#!/bin/bash
# Luna Coin Node Wrapper Script
# Run this directly without installation

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
NODE_SCRIPT="${SCRIPT_DIR}/luna_node.py"  # Change this if your node script has a different name
CONFIG_FILE="${SCRIPT_DIR}/node_config.json"
DATA_DIR="${SCRIPT_DIR}/node-data"
LOG_FILE="${DATA_DIR}/node.log"
PID_FILE="${DATA_DIR}/node.pid"
VERSION="1.0"
DEFAULT_PORT=9335
DEFAULT_HOST="0.0.0.0"

# Functions
print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_debug() { echo -e "${CYAN}[DEBUG]${NC} $1"; }
print_node() { echo -e "${MAGENTA}[NODE]${NC} $1"; }

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

check_node_files() {
    print_status "Checking node files..."
    
    if [ ! -f "$NODE_SCRIPT" ]; then
        print_error "Node script not found: $NODE_SCRIPT"
        echo "Please make sure you're running this script from the directory containing your node script"
        echo "Looking for: node.py, luna_node.py, server.py, or main.py"
        
        # Try to find common node script names
        local possible_scripts=("node.py" "luna_node.py" "server.py" "main.py" "blockchain_node.py")
        for script in "${possible_scripts[@]}"; do
            if [ -f "${SCRIPT_DIR}/${script}" ]; then
                NODE_SCRIPT="${SCRIPT_DIR}/${script}"
                print_warning "Found alternative node script: $script"
                break
            fi
        done
        
        if [ ! -f "$NODE_SCRIPT" ]; then
            exit 1
        fi
    fi
    
    if [ ! -f "$CONFIG_FILE" ]; then
        print_warning "Config file not found: $CONFIG_FILE"
        print_warning "Node will use default settings"
    else
        print_success "Found config file: $CONFIG_FILE"
    fi
    
    print_success "Found node script: $(basename "$NODE_SCRIPT")"
}

setup_data_dir() {
    if [ ! -d "$DATA_DIR" ]; then
        print_status "Creating data directory: ${DATA_DIR}"
        mkdir -p "$DATA_DIR"
        chmod 700 "$DATA_DIR"
    fi

    # Copy config to data directory if it doesn't exist there but exists in script dir
    if [ -f "$CONFIG_FILE" ] && [ ! -f "${DATA_DIR}/$(basename "$CONFIG_FILE")" ]; then
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

check_port() {
    local port=${1:-$DEFAULT_PORT}
    if command -v nc &> /dev/null; then
        if nc -z localhost "$port" 2>/dev/null; then
            print_warning "Port $port is already in use"
            return 1
        else
            print_success "Port $port is available"
            return 0
        fi
    fi
    return 0
}

show_help() {
    echo "Luna Coin Node Wrapper Script"
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  start          Start the node (default)"
    echo "  stop           Stop the node"
    echo "  restart        Restart the node"
    echo "  status         Show node status"
    echo "  logs           Show node logs"
    echo "  console        Run in console mode"
    echo "  help           Show this help message"
    echo "  version        Show version information"
    echo ""
    echo "Options:"
    echo "  --port PORT    Specify port (default: $DEFAULT_PORT)"
    echo "  --host HOST    Specify host (default: $DEFAULT_HOST)"
    echo "  --debug        Enable debug mode"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 start --port 9335 --host 0.0.0.0"
    echo "  $0 stop"
    echo "  $0 status"
    echo "  $0 logs"
    echo ""
    echo "Files:"
    echo "  Node script: $NODE_SCRIPT"
    echo "  Config file: $CONFIG_FILE"
    echo "  Data directory: $DATA_DIR"
}

show_version() {
    echo "Luna Coin Node Wrapper v${VERSION}"
    $PYTHON --version
    echo "Node script: $(basename "$NODE_SCRIPT")"
    echo "Running from: $SCRIPT_DIR"
}

show_banner() {
    echo -e "${MAGENTA}"
    echo "=========================================="
    echo "           Luna Coin Node"
    echo "       Blockchain Node Server"
    echo "=========================================="
    echo -e "${NC}"
}

get_pid() {
    if [ -f "$PID_FILE" ]; then
        cat "$PID_FILE" 2>/dev/null
    else
        echo ""
    fi
}

is_running() {
    local pid=$(get_pid)
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

start_node() {
    local port=$1
    local host=$2
    local debug=$3
    
    if is_running; then
        print_warning "Node is already running (PID: $(get_pid))"
        return 0
    fi
    
    check_port "$port"
    
    print_status "Starting Luna Coin Node on ${host}:${port}"
    
    # Build command
    local cmd="$PYTHON $NODE_SCRIPT"
    local log_cmd=">> $LOG_FILE 2>&1"
    
    if [ "$debug" = "true" ]; then
        print_debug "Debug mode enabled"
        log_cmd="2>&1 | tee -a $LOG_FILE"
    fi
    
    # Start the node in the background
    cd "$SCRIPT_DIR"
    eval "$cmd $log_cmd &"
    local pid=$!
    
    # Save PID
    echo $pid > "$PID_FILE"
    
    # Wait a moment to see if it starts successfully
    sleep 2
    
    if is_running; then
        print_success "Node started successfully (PID: $pid)"
        print_success "Listening on: ${host}:${port}"
        print_success "Log file: $LOG_FILE"
    else
        print_error "Node failed to start"
        rm -f "$PID_FILE"
        return 1
    fi
}

stop_node() {
    if ! is_running; then
        print_warning "Node is not running"
        return 0
    fi
    
    local pid=$(get_pid)
    print_status "Stopping node (PID: $pid)"
    
    kill "$pid" 2>/dev/null
    sleep 2
    
    if is_running; then
        print_warning "Node did not stop gracefully, forcing termination"
        kill -9 "$pid" 2>/dev/null
        sleep 1
    fi
    
    if is_running; then
        print_error "Failed to stop node"
        return 1
    else
        rm -f "$PID_FILE"
        print_success "Node stopped successfully"
    fi
}

show_status() {
    if is_running; then
        local pid=$(get_pid)
        print_success "Node is running (PID: $pid)"
        # You could add more status information here
    else
        print_warning "Node is not running"
    fi
}

show_logs() {
    if [ -f "$LOG_FILE" ]; then
        echo "=== Node Logs ==="
        tail -20 "$LOG_FILE"
    else
        print_warning "No log file found"
    fi
}

run_console() {
    print_status "Starting node in console mode..."
    cd "$SCRIPT_DIR"
    $PYTHON "$NODE_SCRIPT"
}

parse_arguments() {
    local command="start"
    local port=$DEFAULT_PORT
    local host=$DEFAULT_HOST
    local debug="false"
    
    while [ $# -gt 0 ]; do
        case "$1" in
            start|stop|restart|status|logs|console|help|version)
                command="$1"
                shift
                ;;
            --port)
                port="$2"
                shift 2
                ;;
            --host)
                host="$2"
                shift 2
                ;;
            --debug)
                debug="true"
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            -v|--version)
                show_version
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    echo "$command $port $host $debug"
}

# Main execution
main() {
    show_banner
    
    check_python
    check_dependencies
    check_node_files
    setup_data_dir
    setup_logging

    print_success "All checks passed!"
    echo "Python: $($PYTHON --version)"
    echo "Node: $(basename "$NODE_SCRIPT")"
    echo "Directory: $SCRIPT_DIR"
    echo "Data: $DATA_DIR"
    echo "=========================================="
    
    # Parse arguments
    read -r command port host debug <<< $(parse_arguments "$@")
    
    case "$command" in
        start)
            start_node "$port" "$host" "$debug"
            ;;
        stop)
            stop_node
            ;;
        restart)
            stop_node
            sleep 1
            start_node "$port" "$host" "$debug"
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        console)
            run_console
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

# Handle script termination
cleanup() {
    print_status "Cleaning up..."
}

trap cleanup EXIT INT TERM

# Run main function with all arguments
main "$@"
