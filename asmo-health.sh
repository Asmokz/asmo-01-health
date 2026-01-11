#!/bin/bash
# ASMO-01 Health Monitoring - Helper Script
# Quick commands for common operations

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  ASMO-01 Health Monitoring - $1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Show usage
show_usage() {
    print_header "Helper Commands"
    echo ""
    echo "Usage: ./asmo-health.sh [command]"
    echo ""
    echo "Commands:"
    echo "  setup         - Initial setup (install deps, create config)"
    echo "  test          - Run all tests"
    echo "  monitor       - Run monitor once (manual)"
    echo "  report        - Generate report now (manual)"
    echo "  status        - Show current system status"
    echo "  history       - Show last 5 entries from history"
    echo "  logs          - Tail the logs"
    echo "  clean         - Clean old data and logs"
    echo "  backup        - Backup history file"
    echo "  update        - Pull latest changes from git"
    echo ""
}

# Setup
cmd_setup() {
    print_header "Setup"
    
    print_info "Installing Python dependencies..."
    pip3 install -r requirements.txt --break-system-packages
    print_success "Dependencies installed"
    
    if [ ! -f "config.json" ]; then
        print_info "Creating config file..."
        python3 src/monitor.py --create-config
        print_success "Config created: config.json"
        print_warning "Please edit config.json with your settings!"
    else
        print_warning "config.json already exists, skipping"
    fi
    
    print_info "Running setup test..."
    python3 src/test_setup.py
    
    print_success "Setup complete!"
}

# Test
cmd_test() {
    print_header "Running Tests"
    
    print_info "Running setup test..."
    python3 src/test_setup.py
    
    print_info "Testing monitor..."
    python3 src/monitor.py --test
    
    print_info "Testing reporter..."
    python3 src/reporter.py --test
    
    print_success "All tests passed!"
}

# Monitor
cmd_monitor() {
    print_header "Running Monitor"
    python3 src/monitor.py --verbose
}

# Report
cmd_report() {
    print_header "Generating Report"
    python3 src/reporter.py --verbose
}

# Status
cmd_status() {
    print_header "System Status"
    
    # Check if history exists
    if [ -f "data/health_history.json" ]; then
        ENTRIES=$(cat data/health_history.json | python3 -c "import sys, json; print(len(json.load(sys.stdin)))")
        print_info "History entries: $ENTRIES"
        
        # Show latest timestamp
        LATEST=$(cat data/health_history.json | python3 -c "import sys, json; data=json.load(sys.stdin); print(data[-1]['timestamp'] if data else 'N/A')")
        print_info "Latest entry: $LATEST"
        
        # Check file size
        SIZE=$(du -h data/health_history.json | cut -f1)
        print_info "History size: $SIZE"
    else
        print_warning "No history file found yet"
    fi
    
    # Check logs
    if [ -f "logs/asmo.log" ]; then
        LOG_SIZE=$(du -h logs/asmo.log | cut -f1)
        LOG_LINES=$(wc -l < logs/asmo.log)
        print_info "Log file: $LOG_LINES lines ($LOG_SIZE)"
        
        # Show last error
        LAST_ERROR=$(grep -i "error" logs/asmo.log | tail -1 || echo "None")
        if [ "$LAST_ERROR" != "None" ]; then
            print_warning "Last error: ${LAST_ERROR:0:80}..."
        else
            print_success "No errors in logs"
        fi
    else
        print_warning "No log file found yet"
    fi
    
    # Docker status
    print_info "Checking Docker..."
    if docker ps &>/dev/null; then
        CONTAINERS=$(docker ps -q | wc -l)
        print_success "Docker OK - $CONTAINERS containers running"
    else
        print_error "Docker connection failed"
    fi
}

# History
cmd_history() {
    print_header "Recent History"
    
    if [ ! -f "data/health_history.json" ]; then
        print_error "No history file found"
        exit 1
    fi
    
    if command -v jq &> /dev/null; then
        cat data/health_history.json | jq '.[-5:] | .[] | {timestamp, cpu_percent, ram_percent, containers_running}'
    else
        print_warning "jq not installed, showing raw JSON"
        cat data/health_history.json | python3 -c "
import sys, json
data = json.load(sys.stdin)
for entry in data[-5:]:
    print(f\"{entry['timestamp']}: CPU {entry.get('cpu_percent', 'N/A')}%, RAM {entry.get('ram_percent', 'N/A')}%\")
"
    fi
}

# Logs
cmd_logs() {
    print_header "Tailing Logs"
    
    if [ ! -f "logs/asmo.log" ]; then
        print_error "No log file found"
        exit 1
    fi
    
    tail -f logs/asmo.log
}

# Clean
cmd_clean() {
    print_header "Cleaning"
    
    read -p "Clean old logs and data? This will remove logs older than 7 days. [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Cleaning logs older than 7 days..."
        find logs/ -name "*.log" -mtime +7 -delete 2>/dev/null || true
        
        print_info "History cleanup is automatic (7 day retention)"
        
        print_success "Cleanup complete"
    else
        print_info "Cleanup cancelled"
    fi
}

# Backup
cmd_backup() {
    print_header "Backup"
    
    if [ ! -f "data/health_history.json" ]; then
        print_error "No history file to backup"
        exit 1
    fi
    
    BACKUP_DIR="backups"
    mkdir -p "$BACKUP_DIR"
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/health_history_$TIMESTAMP.json"
    
    cp data/health_history.json "$BACKUP_FILE"
    
    print_success "Backup created: $BACKUP_FILE"
    
    # Show backup size
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    print_info "Backup size: $SIZE"
}

# Update
cmd_update() {
    print_header "Updating"
    
    print_info "Pulling latest changes from git..."
    git pull
    
    print_info "Updating dependencies..."
    pip3 install -r requirements.txt --break-system-packages
    
    print_success "Update complete!"
    print_warning "Don't forget to restart any running workflows in n8n"
}

# Main
case "${1:-}" in
    setup)
        cmd_setup
        ;;
    test)
        cmd_test
        ;;
    monitor)
        cmd_monitor
        ;;
    report)
        cmd_report
        ;;
    status)
        cmd_status
        ;;
    history)
        cmd_history
        ;;
    logs)
        cmd_logs
        ;;
    clean)
        cmd_clean
        ;;
    backup)
        cmd_backup
        ;;
    update)
        cmd_update
        ;;
    *)
        show_usage
        exit 1
        ;;
esac
