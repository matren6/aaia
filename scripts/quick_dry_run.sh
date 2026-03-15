#!/bin/bash
# AAIA 5-Minute Quick Dry Run Test
# Quick test of autonomous mode with accelerated scheduler intervals

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "╔════════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                                ║"
echo "║                    AAIA 5-MINUTE QUICK DRY RUN TEST                            ║"
echo "║                                                                                ║"
echo "║                   Testing Autonomous Mode + Web GUI                            ║"
echo "║                                                                                ║"
echo "╚════════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Navigate to project root
cd "$PROJECT_ROOT"

# Check if .env.test exists
if [ ! -f ".env.test" ]; then
    echo "❌ Error: .env.test not found!"
    echo "   Please create .env.test with test configuration"
    exit 1
fi

# Backup current .env if it exists
if [ -f ".env" ]; then
    echo "📦 Backing up current .env to .env.backup..."
    cp .env .env.backup
fi

# Use test configuration
echo "⚙️  Using test configuration (.env.test)..."
cp .env.test .env

# Create test data directory
echo "📁 Setting up test database directory..."
mkdir -p data

# Remove old test database for clean start
if [ -f "data/scribe_test.db" ]; then
    echo "🗑️  Removing old test database for clean start..."
    rm data/scribe_test.db
fi

# Print test configuration
echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "TEST CONFIGURATION"
echo "════════════════════════════════════════════════════════════════════════════════"
echo "Duration:               5 minutes (quick test)"
echo "Database:               data/scribe_test.db (fresh, separate from production)"
echo "Web Dashboard:          http://192.168.178.104:5000"
echo ""
echo "Scheduler Intervals (accelerated for testing):"
echo "  • Health Check:       1 minute   (5 runs expected)"
echo "  • Diagnosis:          2 minutes  (2 runs expected)"
echo "  • Reflection:         5 minutes  (1 run expected)"
echo ""
echo "LLM Provider:           Ollama (phi4-mini)"
echo "Initial Balance:        $100.00"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

# Start AAIA in autonomous mode with timeout
echo "🚀 Starting AAIA in autonomous mode..."
echo ""
echo "📊 Monitor the web dashboard at: http://192.168.178.104:5000"
echo "   - Dashboard: System overview"
echo "   - Goals: Active goals tracking"
echo "   - Economics: Financial data"
echo "   - Logs: Real-time action logs"
echo "   - Tasks: Scheduler task status"
echo ""
echo "⏱️  Test will run for 5 minutes, then auto-stop..."
echo "   Press Ctrl+C to stop manually"
echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

# Save start time
START_TIME=$(date +%s)

# Run with timeout (5 minutes = 300 seconds)
# Redirect stderr to stdout to capture all output
# Use PYTHONPATH to ensure modules are found
export PYTHONPATH=packages:$PYTHONPATH
timeout 300 python3 packages/main.py -a 2>&1 | tee /tmp/aaia_quick_test.log || {
    EXIT_CODE=$?
    echo ""
    echo "════════════════════════════════════════════════════════════════════════════════"
    if [ $EXIT_CODE -eq 124 ]; then
        echo "✅ 5-minute test completed successfully!"
    else
        echo "⚠️  Test stopped with exit code: $EXIT_CODE"
    fi
    echo "════════════════════════════════════════════════════════════════════════════════"
}

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Restore original .env
if [ -f ".env.backup" ]; then
    echo ""
    echo "🔄 Restoring original .env configuration..."
    mv .env.backup .env
fi

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "TEST RESULTS"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Test duration: ${DURATION} seconds"
echo "Test database: data/scribe_test.db"
echo "Test logs: /tmp/aaia_quick_test.log"
echo ""
echo "Quick analysis:"

# Check if database exists and has data
if [ -f "data/scribe_test.db" ]; then
    echo ""
    echo "📊 Database Statistics:"
    python3 scripts/check_test_db.py
    echo ""
else
    echo "❌ Test database not created - system may have failed to start!"
fi

echo ""
echo "To analyze results in detail:"
echo "  1. Check logs: cat /tmp/aaia_quick_test.log | grep ERROR"
echo "  2. Check database: python3 scripts/check_test_db.py"
echo "  3. Check migrations: python3 scripts/check_schema_version.py"
echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "✅ Quick dry run test script completed!"
echo ""
