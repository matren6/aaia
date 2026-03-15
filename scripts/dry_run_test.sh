#!/bin/bash
# AAIA 30-Minute Dry Run Test
# Tests autonomous mode with accelerated scheduler intervals

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "╔════════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                                ║"
echo "║                    AAIA 30-MINUTE DRY RUN TEST                                 ║"
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

# Verify/initialize test database
echo "🔍 Verifying test database..."
if [ -f "data/scribe_test.db" ]; then
    size=$(stat -f%z "data/scribe_test.db" 2>/dev/null || stat -c%s "data/scribe_test.db" 2>/dev/null)
    if [ "$size" = "0" ]; then
        echo "⚠️  Test database is empty (0 bytes), removing..."
        rm data/scribe_test.db
    fi
fi

# Initialize test database if needed
python3 scripts/verify_database.py data/scribe_test.db <<EOF
yes
EOF

if [ $? -ne 0 ]; then
    echo "❌ Database initialization failed!"
    exit 1
fi

echo "✅ Database ready"

# Print test configuration
echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "TEST CONFIGURATION"
echo "════════════════════════════════════════════════════════════════════════════════"
echo "Duration:               30 minutes"
echo "Database:               data/scribe_test.db (separate from production)"
echo "Web Dashboard:          http://192.168.178.104:5000"

echo "Scheduler Intervals (accelerated for testing):"
echo "  • Health Check:       5 minutes  (6 runs expected)"
echo "  • Diagnosis:          10 minutes (3 runs expected)"
echo "  • Reflection:         15 minutes (2 runs expected)"
echo "  • Evolution Check:    20 minutes (1-2 runs expected)"
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
echo "⏱️  Test will run for 30 minutes, then auto-stop..."
echo "   Press Ctrl+C to stop manually"
echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

# Run with timeout (30 minutes = 1800 seconds)
timeout 1800 python3 packages/main.py -a || {
    EXIT_CODE=$?
    echo ""
    echo "════════════════════════════════════════════════════════════════════════════════"
    if [ $EXIT_CODE -eq 124 ]; then
        echo "✅ 30-minute test completed successfully!"
    else
        echo "⚠️  Test stopped with exit code: $EXIT_CODE"
    fi
    echo "════════════════════════════════════════════════════════════════════════════════"
}

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
echo "Test database: data/scribe_test.db"
echo "Test logs: Check console output above"
echo ""
echo "To analyze results:"
echo "  1. Check the database: sqlite3 data/scribe_test.db"
echo "  2. Review action_log table: SELECT * FROM action_log ORDER BY timestamp DESC;"
echo "  3. Check goals: SELECT * FROM goals;"
echo "  4. Review economics: SELECT balance FROM economic_state ORDER BY timestamp DESC LIMIT 1;"
echo ""
echo "Next steps:"
echo "  • Review dashboard recordings/screenshots"
echo "  • Analyze autonomous behavior"
echo "  • Check for any errors or issues"
echo "  • Verify all scheduler tasks ran as expected"
echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "✅ Dry run test script completed!"
echo ""
