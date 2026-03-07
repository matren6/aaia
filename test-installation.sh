#!/usr/bin/env bash
# AAIA Installation Test Script

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test functions
test_command_exists() {
    if command -v aaia &> /dev/null; then
        echo -e "${GREEN}✓${NC} AAIA command is available"
        return 0
    else
        echo -e "${RED}✗${NC} AAIA command not found"
        return 1
    fi
}

test_service_status() {
    local status
    status=$(systemctl is-active aaia 2>/dev/null || echo "inactive")
    
    case $status in
        "active")
            echo -e "${GREEN}✓${NC} AAIA service is active"
            return 0
            ;;
        "inactive")
            echo -e "${YELLOW}!${NC} AAIA service is inactive"
            return 1
            ;;
        "failed")
            echo -e "${RED}✗${NC} AAIA service has failed"
            return 1
            ;;
        *)
            echo -e "${YELLOW}!${NC} AAIA service status: $status"
            return 1
            ;;
    esac
}

test_service_enabled() {
    if systemctl is-enabled aaia &>/dev/null; then
        echo -e "${GREEN}✓${NC} AAIA service is enabled"
        return 0
    else
        echo -e "${YELLOW}!${NC} AAIA service is not enabled"
        return 1
    fi
}

test_data_directory() {
    if [[ -d /var/lib/aaia ]]; then
        echo -e "${GREEN}✓${NC} AAIA data directory exists"
        if [[ -r /var/lib/aaia ]]; then
            echo -e "${GREEN}✓${NC} AAIA data directory is readable"
        else
            echo -e "${YELLOW}!${NC} AAIA data directory is not readable"
        fi
        return 0
    else
        echo -e "${RED}✗${NC} AAIA data directory not found"
        return 1
    fi
}

test_user_exists() {
    if id aaia &>/dev/null; then
        echo -e "${GREEN}✓${NC} AAIA user exists"
        return 0
    else
        echo -e "${RED}✗${NC} AAIA user does not exist"
        return 1
    fi
}

test_nix_flakes() {
    if nix show-config | grep -q "experimental-features.*flakes"; then
        echo -e "${GREEN}✓${NC} Nix flakes are enabled"
        return 0
    else
        echo -e "${RED}✗${NC} Nix flakes are not enabled"
        return 1
    fi
}

show_service_logs() {
    echo -e "\n${BLUE}Recent AAIA service logs:${NC}"
    journalctl -u aaia --no-pager -n 10 2>/dev/null || echo "No logs available"
}

show_service_info() {
    echo -e "\n${BLUE}AAIA service information:${NC}"
    systemctl status aaia --no-pager 2>/dev/null || echo "Service status unavailable"
}

# Main test function
main() {
    echo -e "${BLUE}AAIA Installation Test${NC}"
    echo "========================"
    
    local tests_passed=0
    local tests_total=6
    
    # Run tests
    test_nix_flakes && ((tests_passed++)) || true
    test_command_exists && ((tests_passed++)) || true
    test_user_exists && ((tests_passed++)) || true
    test_data_directory && ((tests_passed++)) || true
    test_service_enabled && ((tests_passed++)) || true
    test_service_status && ((tests_passed++)) || true
    
    echo
    echo "Test Results: $tests_passed/$tests_total passed"
    
    if [[ $tests_passed -eq $tests_total ]]; then
        echo -e "${GREEN}All tests passed! AAIA installation appears to be successful.${NC}"
    elif [[ $tests_passed -ge 4 ]]; then
        echo -e "${YELLOW}Most tests passed. AAIA installation is mostly working but may need attention.${NC}"
    else
        echo -e "${RED}Several tests failed. AAIA installation needs attention.${NC}"
    fi
    
    # Show additional information
    show_service_info
    show_service_logs
    
    echo
    echo -e "${BLUE}Useful commands:${NC}"
    echo "- Check service status: systemctl status aaia"
    echo "- View logs: journalctl -u aaia -f"
    echo "- Start service: sudo systemctl start aaia"
    echo "- Stop service: sudo systemctl stop aaia"
    echo "- Restart service: sudo systemctl restart aaia"
    
    return $((tests_total - tests_passed))
}

main "$@"