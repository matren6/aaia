# AAIA Autonomous Mode Dry Run Test Guide

## Overview

This test runs AAIA in autonomous mode for 30 minutes with:
- **Accelerated scheduler intervals** for faster testing
- **Web dashboard enabled** for real-time monitoring
- **Separate test database** (won't affect production data)

## Quick Start (WSL)

```bash
# 1. Navigate to project
cd /mnt/c/Users/Marcelo.Trenkenchu/source/repos/matren6/aaia

# 2. Make script executable
chmod +x scripts/dry_run_test.sh

# 3. Run test with Nix environment
nix develop --extra-experimental-features 'nix-command flakes' \
  --command ./scripts/dry_run_test.sh
```

## Test Configuration

### Scheduler Intervals (Accelerated)

| Task | Normal Interval | Test Interval | Expected Runs (30 min) |
|------|----------------|---------------|------------------------|
| Health Check | 30 minutes | **5 minutes** | 6 runs |
| Diagnosis | 60 minutes | **10 minutes** | 3 runs |
| Reflection | 24 hours | **15 minutes** | 2 runs |
| Evolution Check | 2 hours | **20 minutes** | 1-2 runs |

### Web Dashboard

- **URL**: `http://192.168.178.104:5000`
- **Access from**: Windows host browser
- **Real-time updates**: WebSocket enabled

### Database

- **Test DB**: `data/scribe_test.db` (separate from production)
- **Production DB**: `data/scribe.db` (unchanged)

## What to Monitor During Test

### 1. Web Dashboard

Open in browser: `http://192.168.178.104:5000`

**Dashboard Page** - Main overview
- System status (balance, actions logged)
- Scheduler status (should show "Running")
- Activity feed (real-time events)
- Resource usage

**Goals Page** - Track autonomous goals
- Watch for new goals being generated
- See progress updates
- Goal completions

**Economics Page** - Financial tracking
- Balance changes over time
- Income/cost tracking
- Crisis status (should stay healthy)

**Logs Page** - Action history
- Real-time log streaming
- Filter by action type
- Export capability

**Tasks Page** - Scheduler monitoring
- See all scheduled tasks
- Live countdowns to next run
- Task execution status

### 2. Console Output (WSL)

Monitor for:
- Task execution messages
- LLM requests/responses
- Goal creation/completion
- Economic transactions
- Any errors or warnings

### 3. System Behavior

Expected autonomous activities:
- **Health checks** (every 5 minutes)
  - System diagnostics
  - Resource monitoring
  
- **Diagnoses** (every 10 minutes)
  - Full system analysis
  - Issue detection
  
- **Reflections** (every 15 minutes)
  - Master model updates
  - Interaction analysis
  
- **Evolution checks** (every 20 minutes)
  - Tool creation evaluation
  - Capability expansion

## Manual Interaction During Test

### Execute Commands via Web UI

While test is running, you can:

1. Open Dashboard
2. Scroll to "Command Interface" section
3. Try commands:
   - `status` - Quick system check
   - `goals` - List current goals
   - `tools` - List available tools
   - `diagnose` - Manual diagnosis
4. Watch real-time output in command history

### WebSocket Testing

Check browser DevTools (F12):
- **Console**: Should see "Connected to WebSocket server"
- **Network → WS**: Socket.IO connection active
- **Console**: system_status events every 5 seconds

## Expected Results

### After 30 Minutes

**Task Execution:**
- ✅ ~6 health checks completed
- ✅ ~3 diagnoses completed
- ✅ ~2 reflections completed
- ✅ ~1-2 evolution checks completed

**Data Generated:**
- ✅ Goals created and tracked
- ✅ Economic transactions logged
- ✅ Master model updated
- ✅ Action log populated

**System Stability:**
- ✅ No crashes or exceptions
- ✅ Web server responsive throughout
- ✅ WebSocket connections stable
- ✅ Database writes successful

## Post-Test Analysis

### Check Database

```bash
# Open test database
sqlite3 data/scribe_test.db

# View action log
SELECT timestamp, action, status 
FROM action_log 
ORDER BY timestamp DESC 
LIMIT 20;

# Check goals
SELECT id, goal_text, status, created_at 
FROM goals 
ORDER BY created_at DESC;

# View economic state
SELECT balance, total_income, total_costs 
FROM economic_state 
ORDER BY timestamp DESC 
LIMIT 1;

# Count scheduler task runs
SELECT action, COUNT(*) as run_count 
FROM action_log 
WHERE action LIKE '%check%' OR action LIKE '%diagnosis%' OR action LIKE '%reflection%'
GROUP BY action;
```

### Review Logs

Check for:
- Task execution patterns
- LLM usage (should primarily use Ollama/phi4-mini)
- Economic balance (should remain > $10 threshold)
- Any errors or warnings

## Troubleshooting

### Web Dashboard Not Loading

1. Check if port 5000 is accessible:
   ```bash
   curl http://192.168.178.104:5000/api/health
   ```

2. Verify web server started in AAIA logs

3. Check Windows firewall

### Scheduler Not Running

1. Verify `.env.test` is active
2. Check `SCHEDULER_ENABLED=true`
3. Look for scheduler initialization in logs

### Database Errors

1. Ensure `data/` directory exists
2. Check file permissions
3. Verify SQLite is available

### LLM Connection Issues

1. Verify Ollama server: `http://192.168.178.104:11434`
2. Test connection:
   ```bash
   curl http://192.168.178.104:11434/api/tags
   ```
3. Check OLLAMA_BASE_URL in .env.test

## Safety Notes

- ✅ Uses separate test database (`scribe_test.db`)
- ✅ Original `.env` backed up automatically
- ✅ Test auto-stops after 30 minutes
- ✅ Can manually stop with Ctrl+C
- ✅ Original config restored after test

## After Test Cleanup

The script automatically:
1. Restores original `.env`
2. Keeps test database for analysis
3. Preserves all logs

To clean up test data:
```bash
# Remove test database
rm data/scribe_test.db

# (Optional) Remove test config
rm .env.test
```

## Success Criteria

✅ **Functionality**
- All scheduler tasks execute on time
- Web dashboard shows real-time updates
- Commands can be executed via UI
- No crashes or exceptions

✅ **Performance**
- Web server CPU < 5%
- Dashboard responsive
- WebSocket latency < 500ms
- No memory leaks

✅ **Data Integrity**
- All actions logged
- Economic balance tracked
- Goals created and updated
- Database writes successful

---

## Quick Command Reference

```bash
# Run test
nix develop --extra-experimental-features 'nix-command flakes' \
  --command ./scripts/dry_run_test.sh

# Check web dashboard
http://192.168.178.104:5000

# View test database
sqlite3 data/scribe_test.db

# Check Ollama server
curl http://192.168.178.104:11434/api/tags
```

---

**Ready to test autonomous mode with full visibility! 🚀**
