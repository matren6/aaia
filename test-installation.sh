#!/usr/bin/env bash
# AAIA Installation Test Script

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Detect WSL environment (systemd is typically unavailable in WSL)
is_wsl() {
    if [[ -n "${WSL_DISTRO_NAME-}" ]]; then
        return 0
    fi
    if grep -qi microsoft /proc/version 2>/dev/null; then
        return 0
    fi
    return 1
}

# Test functions
test_command_exists() {
    if command -v aaia &> /dev/null; then
        echo -e "${GREEN}✓${NC} AAIA command is available in PATH"
        return 0
    fi

    # Also accept a developer build in ./result/bin/aaia
    if [[ -x "./result/bin/aaia" ]]; then
        echo -e "${GREEN}✓${NC} AAIA executable found at ./result/bin/aaia"
        return 0
    fi

    echo -e "${RED}✗${NC} AAIA command not found"
    return 1
}

test_service_status() {
    if is_wsl; then
        echo -e "${YELLOW}!${NC} Skipping service status check on WSL (systemd unavailable)"
        return 2
    fi

    local status
    status=$(systemctl is-active aaia 2>/dev/null || echo "inactive")
    case $status in
        active)
            echo -e "${GREEN}✓${NC} AAIA service is active"
            return 0
            ;;
        inactive)
            echo -e "${YELLOW}!${NC} AAIA service is inactive"
            return 1
            ;;
        failed)
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
    if is_wsl; then
        echo -e "${YELLOW}!${NC} Skipping service enablement check on WSL"
        return 2
    fi

    if systemctl is-enabled aaia &>/dev/null; then
        echo -e "${GREEN}✓${NC} AAIA service is enabled"
        return 0
    else
        echo -e "${YELLOW}!${NC} AAIA service is not enabled"
        return 1
    fi
}

test_data_directory() {
    if is_wsl; then
        echo -e "${YELLOW}!${NC} Skipping data directory check on WSL"
        return 2
    fi

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
    if is_wsl; then
        echo -e "${YELLOW}!${NC} Skipping user existence check on WSL"
        return 2
    fi

    if id aaia &>/dev/null; then
        echo -e "${GREEN}✓${NC} AAIA user exists"
        return 0
    else
        echo -e "${RED}✗${NC} AAIA user does not exist"
        return 1
    fi
}

test_nix_flakes() {
    if ! command -v nix &>/dev/null; then
        echo -e "${RED}✗${NC} nix not found"
        return 1
    fi

    # First try: flakes enabled in nix config
    if nix show-config 2>/dev/null | grep -q "experimental-features.*flakes"; then
        echo -e "${GREEN}✓${NC} Nix flakes are enabled in config"
        return 0
    fi

    # Second try: flakes usable via extra-experimental-features flag
    if nix --extra-experimental-features 'nix-command flakes' flake show . >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Nix flakes usable via --extra-experimental-features"
        return 0
    fi

    echo -e "${RED}✗${NC} Nix flakes are not enabled or not usable"
    return 1
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
    local tests_failed=0
    local tests_skipped=0
    local tests_run=0

    run_test() {
        "$@"
        local rc=$?
        if [[ $rc -eq 0 ]]; then
            tests_passed=$((tests_passed+1))
            tests_run=$((tests_run+1))
        elif [[ $rc -eq 1 ]]; then
            tests_failed=$((tests_failed+1))
            tests_run=$((tests_run+1))
        elif [[ $rc -eq 2 ]]; then
            tests_skipped=$((tests_skipped+1))
        else
            tests_failed=$((tests_failed+1))
            tests_run=$((tests_run+1))
        fi
    }

    # Run tests (counts skipped tests separately on WSL)
    run_test test_nix_flakes
    run_test test_command_exists
    run_test test_user_exists
    run_test test_data_directory
    run_test test_service_enabled
    run_test test_service_status

    echo
    echo "Test Results: $tests_passed/$tests_run passed ($tests_skipped skipped)"

    if [[ $tests_run -eq 0 ]]; then
        echo -e "${YELLOW}No applicable tests were run in this environment.${NC}"
    else
        if [[ $tests_passed -eq $tests_run ]]; then
            echo -e "${GREEN}All applicable tests passed! AAIA installation appears to be successful.${NC}"
        elif [[ $tests_passed -ge $((tests_run*70/100)) ]]; then
            echo -e "${YELLOW}Most applicable tests passed. AAIA installation is mostly working but may need attention.${NC}"
        else
            echo -e "${RED}Several applicable tests failed. AAIA installation needs attention.${NC}"
        fi
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

    if [[ $tests_failed -gt 0 ]]; then
        return 1
    fi
    return 0
}

main "$@"
