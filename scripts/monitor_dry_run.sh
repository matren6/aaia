#!/bin/bash
# Monitor AAIA 30-minute dry run test

cd /mnt/c/Users/Marcelo.Trenkenchu/source/repos/matren6/aaia

echo "╔════════════════════════════════════════════════════════════════════════════════╗"
echo "║                  AAIA 30-MINUTE DRY RUN TEST - MONITOR                        ║"
echo "╚════════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Start Time: $(date)"
echo "Duration: 30 minutes (1800 seconds)"
echo "Web Dashboard: http://192.168.178.104:5000"
echo ""
echo "Test running... Output will be saved to: dry_run_30min_full.log"
echo ""

# Run test with full 30 minutes
timeout 1800 nix develop --extra-experimental-features 'nix-command flakes' --command python3 packages/main.py -a 2>&1 | tee dry_run_30min_full.log

EXIT_CODE=$?

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════════╗"
echo "║                          TEST COMPLETED                                        ║"
echo "╚════════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "End Time: $(date)"
echo "Exit Code: $EXIT_CODE"

if [ $EXIT_CODE -eq 124 ]; then
    echo "Status: ✅ Test completed successfully (30 minutes)"
elif [ $EXIT_CODE -eq 0 ]; then
    echo "Status: ✅ Test completed normally"
else
    echo "Status: ⚠️  Test exited with code $EXIT_CODE"
fi

echo ""
echo "Log file: dry_run_30min_full.log"
echo "Log size: $(du -h dry_run_30min_full.log 2>/dev/null | cut -f1 || echo 'N/A')"
echo ""
echo "Restoring original configuration..."
if [ -f .env.prod.backup ]; then
    mv .env.prod.backup .env
    echo "✅ Original .env restored"
fi

echo ""
echo "To analyze results:"
echo "  1. Check log: less dry_run_30min_full.log"
echo "  2. Check database: sqlite3 data/scribe_test.db"
echo "  3. Review scheduler tasks executed"
echo ""
