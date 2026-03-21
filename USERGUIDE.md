# AAIA — Autonomous AI Agent: Full User Guide

> **Version:** Current (`main` branch)
> **Environment:** NixOS / WSL + Nix
> **Runtime:** Python 3.12 · SQLite · Ollama (default LLM back-end)

---

## Table of Contents

1. [What Is AAIA?](#1-what-is-aaia)
2. [High-Level Architecture](#2-high-level-architecture)
3. [Installation & First Start](#3-installation--first-start)
4. [Configuration Reference](#4-configuration-reference)
5. [Core Infrastructure](#5-core-infrastructure)
   - 5.1 [Dependency Injection Container](#51-dependency-injection-container)
   - 5.2 [Event Bus](#52-event-bus)
   - 5.3 [Prompt Manager](#53-prompt-manager)
6. [Persistence Layer](#6-persistence-layer)
   - 6.1 [DatabaseManager & Migrations](#61-databasemanager--migrations)
   - 6.2 [Database Schema (All Tables)](#62-database-schema-all-tables)
   - 6.3 [Scribe — The Logging API](#63-scribe--the-logging-api)
7. [LLM Providers & Model Router](#7-llm-providers--model-router)
8. [Scheduling System](#8-scheduling-system)
   - 8.1 [Registered Tasks & Intervals](#81-registered-tasks--intervals)
   - 8.2 [Task Lifecycle](#82-task-lifecycle)
9. [Economics System](#9-economics-system)
   - 9.1 [Virtual Budget & Balance](#91-virtual-budget--balance)
   - 9.2 [Resource Monitor (Physical Costs)](#92-resource-monitor-physical-costs)
   - 9.3 [Income Seeker](#93-income-seeker)
   - 9.4 [Marginal Analyzer & Crisis Handler](#94-marginal-analyzer--crisis-handler)
10. [Safety & Mandates](#10-safety--mandates)
11. [Dialogue Manager](#11-dialogue-manager)
12. [Goal System](#12-goal-system)
13. [Hierarchy of Needs](#13-hierarchy-of-needs)
14. [Self-Diagnosis](#14-self-diagnosis)
15. [Self-Modification & Nix-Aware Modification](#15-self-modification--nix-aware-modification)
16. [Evolution System](#16-evolution-system)
    - 16.1 [Evolution Manager](#161-evolution-manager)
    - 16.2 [Evolution Pipeline](#162-evolution-pipeline)
    - 16.3 [Evolution Orchestrator](#163-evolution-orchestrator)
17. [Metacognition](#17-metacognition)
18. [Capability Discovery & Environment Explorer](#18-capability-discovery--environment-explorer)
19. [Intent Predictor](#19-intent-predictor)
20. [Strategy Optimizer](#20-strategy-optimizer)
21. [Master Model](#21-master-model)
22. [Forge — Dynamic Tool Creation](#22-forge--dynamic-tool-creation)
23. [Web Dashboard](#23-web-dashboard)
24. [Complete System Startup Workflow](#24-complete-system-startup-workflow)
25. [End-to-End Workflows](#25-end-to-end-workflows)
26. [Data Flow Diagram](#26-data-flow-diagram)
27. [Troubleshooting](#27-troubleshooting)
28. [Glossary](#28-glossary)

---

## 1. What Is AAIA?

AAIA (**Autonomous AI Agent**) is a self-evolving AI system that:

- **Operates autonomously** — runs background tasks on a schedule without requiring human commands.
- **Evolves itself** — diagnoses its own weaknesses, plans improvements, modifies its code, and validates the results.
- **Creates new tools** — uses an LLM to generate Python tool files at runtime, extending its own capabilities.
- **Tracks economics** — every LLM call, CPU cycle, and tool creation has a cost; the system maintains a virtual budget.
- **Learns about the user** — builds a psychological model of the *master* (the human operator) over time.
- **Enforces ethics** — four immutable mandates prevent harmful, deceptive, or autonomy-violating actions.

AAIA is controlled primarily via its **web dashboard** (port 5000 by default) and a structured **dialogue protocol** that parses and analyses commands before executing them.

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Arbiter (main.py)                           │
│  Entry point – owns the DI Container and boots all modules          │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
          ┌──────────────────────▼──────────────────────┐
          │           DI Container (container.py)        │
          │  All modules are singletons registered here  │
          └─────────────────────────────────────────────-┘
                 │               │                │
    ┌────────────▼──┐  ┌─────────▼───────┐  ┌────▼────────────┐
    │  Event Bus    │  │  PromptManager  │  │  SystemConfig   │
    │  (bus.py)     │  │(prompt_manager) │  │  (settings.py)  │
    └───────────────┘  └─────────────────┘  └─────────────────┘

CORE SERVICES            AUTONOMOUS SERVICES       SELF-DEVELOPMENT
─────────────────        ───────────────────       ────────────────
• Scribe                 • AutonomousScheduler     • SelfDiagnosis
• DatabaseManager        • GoalSystem              • SelfModification
• EconomicManager        • HierarchyManager        • EvolutionManager
• MandateEnforcer        • IncomeSeeker            • EvolutionPipeline
• ModelRouter            • MasterModelManager      • EvolutionOrchestrator
• DialogueManager        • MasterWellBeingMonitor  • MetaCognition
• Forge                  • ResourceMonitor         • CapabilityDiscovery
                         • ProactiveAnalysis       • EnvironmentExplorer
                                                   • IntentPredictor
                                                   • StrategyOptimizer

WEB LAYER                ECONOMICS LAYER           LLM PROVIDERS
─────────────            ───────────────           ─────────────
• WebServer (Flask)      • EconomicManager         • Ollama (local)
• WebSocketIO            • MarginalAnalyzer        • OpenAI
• DashboardDataAggr.     • EconomicCrisisHandler   • GitHub Models
                         • ProfitabilityReporter   • Azure OpenAI
                                                   • Venice AI
```

### Module Registration Flow

All modules are wired together by `SystemBuilder` inside `packages/modules/setup.py`:

1. `_register_core_services()` — Scribe, DatabaseManager, Router, Economics, Mandates, Dialogue, Forge, MasterModel, LLMTracker, ResourceMonitor, WebServer.
2. `_register_autonomous_services()` — Scheduler, Goals, HierarchyManager, IncomeSeeker, ProactiveAnalysis, PromptOptimizer.
3. `_register_development_services()` — SelfDiagnosis, SelfModification, EvolutionManager, EvolutionPipeline, EvolutionOrchestrator, MetaCognition, CapabilityDiscovery, IntentPredictor, EnvironmentExplorer, StrategyOptimizer.

Every module is a **singleton** inside the container.

---

## 3. Installation & First Start

### NixOS (Recommended)

```bash
git clone https://github.com/matren6/aaia.git /tmp/aaia
cd /tmp/aaia/install/nixos
bash install-nixos.sh
```

The installer creates a systemd service that starts AAIA automatically on boot.

### Manual / WSL

```bash
git clone https://github.com/matren6/aaia.git
cd aaia
chmod +x install.sh
sudo ./install.sh
```

### Running Manually

```bash
# From repo root
cd packages
python main.py
```

The process will:
1. Resolve the database path (`~/.local/share/aaia/scribe.db`).
2. Run all pending database migrations.
3. Wire all modules through the DI container.
4. Start the `ResourceMonitor` background thread.
5. Start the `WebServer` on `http://0.0.0.0:5000`.
6. Emit `SYSTEM_STARTUP` event on the Event Bus.
7. Log the startup action to the database.
8. Begin the `AutonomousScheduler` background loop.

### Development Shell

```bash
nix develop          # Enter Nix dev shell with all dependencies
```

---

## 4. Configuration Reference

All configuration is managed by `packages/modules/settings.py` using Python `dataclass` objects. Values can be overridden via environment variables.

### Key Configuration Sections

| Section | Class | Key Settings |
|---|---|---|
| **Database** | `DatabaseConfig` | `DB_PATH`, `DB_TIMEOUT`, `DB_BACKUP_ENABLED` |
| **Scheduler** | `SchedulerConfig` | `HEALTH_CHECK_INTERVAL`, `DIAGNOSIS_INTERVAL`, `REFLECTION_INTERVAL`, `EVOLUTION_CHECK_INTERVAL` |
| **LLM** | `LLMConfig` | `LLM_DEFAULT_PROVIDER`, `LLM_FALLBACK_PROVIDER` |
| **Economics** | `EconomicsConfig` | Initial balance ($100), low-balance threshold ($10), inference cost ($0.01) |
| **Evolution** | `EvolutionConfig` | `max_retries`, `safety_mode`, `backup_before_modify`, `rollback_on_error` |
| **Tools** | `ToolsConfig` | `tools_dir`, `sandbox_mode`, `execution_timeout` |
| **Web Server** | `WebServerConfig` | `host`, `port` (5000), `auth_enabled` |
| **Resource Monitoring** | inside `EconomicsConfig` | CPU cost, memory cost, electricity cost (€/kWh), system power draw |

### LLM Provider Environment Variables

| Provider | Enable Flag | Key Variable |
|---|---|---|
| Ollama (default) | always on | `OLLAMA_BASE_URL` (default `http://localhost:11434`) |
| OpenAI | `OPENAI_ENABLED=true` | `OPENAI_API_KEY` |
| GitHub Models | `GITHUB_ENABLED=true` | `GITHUB_TOKEN` |
| Azure OpenAI | `AZURE_ENABLED=true` | `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT` |
| Venice AI | `VENICE_ENABLED=true` | `VENICE_API_KEY` |

### Scheduler Intervals (Defaults)

| Environment Variable | Default | Meaning |
|---|---|---|
| `HEALTH_CHECK_INTERVAL` | 1800 s (30 min) | System health check |
| `DIAGNOSIS_INTERVAL` | 3600 s (1 h) | Self-diagnosis |
| `REFLECTION_INTERVAL` | 86400 s (24 h) | Daily reflection |
| `EVOLUTION_CHECK_INTERVAL` | 7200 s (2 h) | Evolution evaluation |

---

## 5. Core Infrastructure

### 5.1 Dependency Injection Container

**File:** `packages/modules/container.py`

The `Container` is a lightweight service locator that:

- Stores *factories* (lambdas that receive the container and return an instance) or *instances* directly.
- Resolves dependencies lazily when `container.get('ServiceName')` is first called.
- Guarantees **one singleton instance per service name** once created.
- Raises `DependencyError` if a required service is not registered.

```python
# Registering a service with a factory
container.register_factory('Scribe', lambda c: Scribe(db_manager=c.get('DatabaseManager')), singleton=True)

# Resolving a service
scribe = container.get('Scribe')
```

The `Arbiter` class in `main.py` stores only a reference to the container; all module access goes through `container.get(...)` (exposed as Python properties for convenience).

### 5.2 Event Bus

**File:** `packages/modules/bus.py`

The Event Bus provides **decoupled publish/subscribe communication** so modules do not need direct references to each other.

#### Event Types (partial list)

| Category | Event Types |
|---|---|
| System | `SYSTEM_STARTUP`, `SYSTEM_SHUTDOWN`, `SYSTEM_HEALTH_CHECK` |
| Economics | `ECONOMIC_TRANSACTION`, `BALANCE_LOW`, `INCOME_GENERATED`, `ECONOMIC_CRISIS` |
| LLM | `LLM_REQUEST`, `LLM_RESPONSE`, `LLM_ERROR`, `LLM_FALLBACK`, `PROVIDER_UNAVAILABLE` |
| Evolution | `EVOLUTION_STARTED`, `EVOLUTION_COMPLETED`, `EVOLUTION_FAILED` |
| Goals | `GOAL_CREATED`, `GOAL_COMPLETED`, `GOAL_FAILED` |
| Safety | `MANDATE_OVERRIDE`, `FINAL_MANDATE_INVOKED`, `CATASTROPHIC_RISK_DETECTED` |
| Master | `MASTER_INTERACTION_LOGGED`, `MASTER_TRAIT_UPDATED`, `MASTER_MODEL_REFLECTED` |
| Diagnosis | `DIAGNOSIS_COMPLETED`, `DIAGNOSIS_ACTION_REQUIRED` |
| Tools | `TOOL_CREATED`, `TOOL_LOADED`, `TOOL_ERROR` |
| Well-being | `WELLBEING_CONCERN` |

#### Publishing and Subscribing

```python
# Publish
event_bus.publish(Event(type=EventType.GOAL_COMPLETED, data={'goal_id': 42}, source='GoalSystem'))

# Subscribe to a specific type
event_bus.subscribe(EventType.LLM_RESPONSE, my_handler)

# Subscribe to ALL events (used by MetaCognition for pattern tracking)
event_bus.subscribe_all(my_handler)
```

Events are delivered **synchronously** within the publishing thread but handler exceptions are isolated so one bad subscriber cannot crash a publisher.

### 5.3 Prompt Manager

**File:** `packages/modules/prompt_manager.py`

The `PromptManager` loads all `*.json` files from the `packages/prompts/` directory tree at startup and serves formatted prompt strings to modules. No module contains hardcoded LLM prompts.

**Prompt directory layout:**

```
packages/prompts/
├── analysis/          # System analysis & improvement
├── dialogue/          # Command understanding & classification
├── economics/         # Income & cost analysis
├── generation/        # Code generation & evolution planning
├── goals/             # Autonomous goal generation
├── income/            # Income opportunity evaluation
├── mandates/          # Ethical analysis
├── master_model/      # User trait extraction & modelling
└── system/            # Health, reflection, diagnosis
```

Each JSON file contains a `name`, a `prompt` template with `{variable}` placeholders, and an optional `system_prompt`. A module calls:

```python
prompt_data = self.prompt_manager.get_prompt('command_understanding', command=cmd, context=ctx)
response = self.router.generate(prompt_data['prompt'], prompt_data.get('system_prompt', ''))
```

---

## 6. Persistence Layer

### 6.1 DatabaseManager & Migrations

**File:** `packages/modules/database_manager.py`

The `DatabaseManager` wraps a single SQLite connection with:

- **WAL mode** — Write-Ahead Logging for concurrent read/write access.
- **Re-entrant lock** — safe for multi-threaded scheduler tasks.
- **Versioned migrations** — schema evolves automatically on startup.

#### Current Schema Version: 16

Migrations live in `packages/modules/migrations/` and are numbered `001` through `016`. Each migration has an `up()` method (applied once) and a `down()` method (rollback). The `schema_version` table tracks which migrations have been applied.

If the code's `CURRENT_SCHEMA_VERSION` is ahead of the database, all outstanding migrations run automatically. If the database is *newer* than the code, the system raises a `RuntimeError` to prevent data corruption.

### 6.2 Database Schema (All Tables)

The following tables are created across all 16 migrations:

| Table | Purpose | Key Columns |
|---|---|---|
| `schema_version` | Track applied migrations | `version`, `applied_at`, `description` |
| `action_log` | Every system action | `action`, `reasoning`, `outcome`, `cost`, `metadata` |
| `economic_log` | Financial transactions | `description`, `amount`, `balance_after`, `transaction_type` |
| `system_state` | Key-value store for runtime state | `key`, `value`, `updated_at` |
| `hierarchy_of_needs` | Maslow-style tier progression | `tier`, `name`, `current_focus`, `progress` |
| `dialogue_log` | Dialogue Manager interactions | `command`, `understanding`, `risks`, `alternatives`, `outcome` |
| `tools` | Registered tool registry | `name`, `description`, `file_path`, `usage_count` |
| `goals` | Autonomous & manual goals | `goal_text`, `goal_type`, `priority`, `status`, `progress` |
| `capabilities` | Discovered system capabilities | `name`, `description`, `source`, `status` |
| `master_interactions` | All master/user interactions | `interaction_type`, `user_input`, `system_response`, `intent_detected` |
| `master_traits` | Extracted user personality traits | `trait_name`, `trait_value`, `confidence`, `source` |
| `income_opportunities` | Identified income ideas | `opportunity_type`, `description`, `estimated_value`, `effort_estimate` |
| `mandate_overrides` | Logged mandate override attempts | `action`, `override_granted`, `reason` |
| `provider_performance` | LLM provider health metrics | `provider`, `success_rate`, `avg_latency` |
| `resource_costs` | Physical resource cost log | `resource_type`, `quantity`, `unit`, `cost` |
| `safety_lockouts` | Safety state flags | `lockout_type`, `reason`, `expires_at` |
| `proactive_notifications` | Pending proactive alerts | `message`, `priority`, `status` |
| `dialogue_outcomes` | Outcome tracking per dialogue | `dialogue_id`, `outcome_type`, `notes` |
| `final_mandate_events` | Final mandate invocation log | `trigger`, `context`, `response` |
| `wellbeing_assessments` | Master well-being records | `score`, `concerns`, `recommendations` |
| `subjective_value_scores` | AI-assessed task value | `task`, `value_score`, `reasoning` |
| `pending_dialogues` | Queued commands awaiting processing | `command`, `priority`, `status` |
| `llm_interactions` | Full LLM call audit trail | `provider`, `model`, `prompt_tokens`, `completion_tokens`, `cost`, `latency` |
| `effectiveness_metrics` | MetaCognition performance scores | `metric_name`, `metric_value`, `context` |

### 6.3 Scribe — The Logging API

**File:** `packages/modules/scribe.py`

`Scribe` is the single logging facade used by every module. It wraps `DatabaseManager` and exposes:

| Method | What It Records |
|---|---|
| `log_action(action, reasoning, outcome, cost)` | An action taken by any module |
| `log_system_event(event_type, details)` | Generic system event (maps to `log_action`) |
| `get_economic_status()` | Current balance, total spent, recent transactions |
| `get_dialogue_history(limit)` | Recent dialogue interactions |
| `validate_mandates(action_data)` | Pre-check: is `action_data` a valid dict? |

All modules log via Scribe rather than writing to the database directly. This provides a single audit trail for every autonomous decision.

---

## 7. LLM Providers & Model Router

**File:** `packages/modules/router.py` | Providers: `packages/modules/llm/`

The `ModelRouter` is the single gateway to all LLM providers. No module calls an LLM API directly.

### Provider Selection Logic

```
call_model(prompt) ──► select_provider(task_type, complexity)
                         │
                         ├─ Phase 2: ask MarginalAnalyzer for optimal provider
                         │           (Austrian Economic: marginal cost vs. value)
                         ├─ If preferred_provider specified → use that
                         ├─ Check provider health cache
                         ├─ Try default_provider
                         └─ On failure → try fallback_provider → raise
```

### Supported Providers

| Provider | Transport | Default Model | Best For |
|---|---|---|---|
| **Ollama** | HTTP/REST (local) | `phi3` | Privacy, free, offline |
| **OpenAI** | HTTPS API | `gpt-4o-mini` | High-quality reasoning |
| **GitHub Models** | HTTPS API | `gpt-4o` | Free tier with GitHub token |
| **Azure OpenAI** | HTTPS API | configurable | Enterprise deployments |
| **Venice AI** | HTTPS API | `llama-3.3-70b` | Privacy-preserving cloud |

### Key ModelRouter Methods

| Method | Purpose |
|---|---|
| `generate(prompt, system_prompt, task_type, complexity)` | Primary generation call |
| `select_provider(task_type, complexity)` | Choose provider per task |
| `call_model(model, prompt)` | Legacy single-model call |
| `get_provider_status()` | Health and availability map |

Every successful LLM response emits `LLM_RESPONSE` on the Event Bus, which `EconomicManager` subscribes to for automatic cost tracking.

---

## 8. Scheduling System

**File:** `packages/modules/scheduler.py`

The `AutonomousScheduler` is the **heartbeat of AAIA** — a background thread that runs all autonomous tasks without waiting for human commands.

### Architecture

```
AutonomousScheduler.start()
    └─► background thread ──► main_loop()
                                  │
                                  ▼ every iteration
                              for each task in task_queue:
                                  if task.enabled AND time_to_run(task):
                                      run_task(task)   ◄── logs result via Scribe
```

Tasks are checked against their `next_run` timestamp. When a task executes, its `last_run` and `next_run` are updated and results are logged to `action_log`.

### 8.1 Registered Tasks & Intervals

| Task Name | Interval | Priority | What It Does |
|---|---|---|---|
| `system_health_check` | 30 min | 1 (highest) | CPU, memory, disk usage via `psutil` |
| `economic_crisis_check` | 15 min | 1 | Checks for low balance / crisis conditions |
| `self_diagnosis` | 1 h | 2 | Full `SelfDiagnosis.perform_full_diagnosis()` |
| `evolution_check` | 2 h | 2 | Decides if evolution is needed; triggers pipeline |
| `economic_review` | 1 h | 2 | Reviews spending and budget status |
| `performance_snapshot` | 1 h | 2 | Records system performance metrics |
| `master_wellbeing_assessment` | Daily | 2 | Assesses user well-being from interactions |
| `profitability_report` | Daily | 2 | Generates income vs. cost report |
| `reflection_cycle` | Daily | 3 | MetaCognition + master model reflection |
| `intent_prediction` | 12 h | 3 | Predicts next master actions |
| `environment_exploration` | Daily | 3 | Discovers new system capabilities |
| `autonomous_tool_development` | Daily | 2 | Creates tools identified as needed |
| `identify_income_opportunities` | 6 h | 3 | Scans for income generation ideas |
| `proactive_opportunity_detection` | 6 h | 60 | Runs `ProactiveAnalysis` module |
| `capability_discovery` | 48 h | 3 | Maps all available capabilities |
| `master_model_reflection` | Weekly | 2 | Deep user trait analysis |
| `tool_performance_optimizer` | 2 days | 3 | Rewrites underperforming tools |
| `tool_deprecation_check` | Weekly | 4 | Removes unused tools |
| `tool_security_audit` | 3 days | 2 | Scans all tools for dangerous patterns |
| `code_quality_assessment` | Weekly | 3 | Analyses all module source code |

### 8.2 Task Lifecycle

```
register_task()  ──► task_queue[]  ──► run  ──► log to action_log
                                         │
                              ┌──────────┴─────────┐
                         success                  failure
                              │                     │
                         update next_run      log error, update next_run
                                              (retry if max_task_retries > 0)
```

Tasks can be individually **paused** (`scheduler.pause_task('task_name')`) and **resumed** (`scheduler.resume_task('task_name')`). The `EconomicCrisisHandler` uses this to pause expensive tasks during a budget crisis.

---

## 9. Economics System

### 9.1 Virtual Budget & Balance

**File:** `packages/modules/economics.py`

`EconomicManager` maintains a **virtual balance** (default: $100.00) in the `system_state` table. Every operation has a defined cost:

| Operation | Default Cost |
|---|---|
| LLM inference call | $0.01 per call |
| Tool creation | $1.00 one-time |
| Local model token | $0.000001 per token |

#### Cost Flow

```
Any module ──► router.generate() ──► LLM_RESPONSE event
                                        │
                                        ▼
                              EconomicManager._on_llm_response()
                                        │
                              deduct cost from balance
                              insert into economic_log
                              if balance < threshold ──► publish BALANCE_LOW event
```

The balance is read from / written to the `system_state` table with key `economic_balance`. The `economic_log` table holds a full immutable transaction history.

### 9.2 Resource Monitor (Physical Costs)

**File:** `packages/modules/resource_monitor.py`

Tracks and charges for actual hardware usage:

| Resource | Measurement | Default Rate |
|---|---|---|
| CPU time | User + system seconds | $0.0001/second |
| Memory | Resident Set Size (GB) | $0.01/GB-hour |
| Electricity | Estimated system power × runtime | $0.50/kWh |
| Storage | Database + tools directory size | $0.10/GB-month |

The `ResourceMonitor` runs in its own background thread (interval: every 5 minutes by default) and appends rows to the `resource_costs` table. Costs above the configured threshold are also logged as economic transactions.

### 9.3 Income Seeker

**File:** `packages/modules/income_seeker.py`

Scans the system's current capabilities and uses an LLM to generate income opportunity ideas. Opportunities are stored in `income_opportunities` and can be reviewed in the web dashboard. Each opportunity has:

- `opportunity_type` — service, product, automation, consulting, etc.
- `estimated_value` — estimated revenue
- `effort_estimate` — low / medium / high

Income recording (when an opportunity is acted on) emits `INCOME_GENERATED` on the Event Bus.

### 9.4 Marginal Analyzer & Crisis Handler

**File:** `packages/modules/marginal_analyzer.py`, `packages/modules/economic_crisis_handler.py`

- **MarginalAnalyzer** applies Austrian Economic theory — selecting the LLM provider that maximises marginal value per marginal cost. It advises `ModelRouter` on which provider to use for each request.
- **EconomicCrisisHandler** monitors for low balance conditions and, when triggered:
  1. Pauses expensive scheduler tasks.
  2. Switches LLM provider selection to cheapest available.
  3. Logs a `ECONOMIC_CRISIS` event.
  4. Resumes normal operations once balance recovers.

---

## 10. Safety & Mandates

**File:** `packages/modules/mandates.py`

The `MandateEnforcer` enforces four **immutable** rules. These cannot be overridden even by the master (human operator):

| Mandate | Rule |
|---|---|
| **Symbiotic Collaboration** | Engage as a partner, not an adversary |
| **The Master's Final Will** | The master's explicit decision is the ultimate law |
| **Non-Maleficence** | Do no harm to the master, systems, or resources |
| **Veracity & Transparent Reasoning** | All reasoning must be accurate and logged honestly |

#### Check Flow

```
action proposed ──► MandateEnforcer.check_action(action, context)
                        │
                ┌───────▼──────┐
                │  Rule-based  │  (fast path: keyword matching)
                └───────┬──────┘
                        │ if ambiguous
                ┌───────▼──────────────────────┐
                │  AI-powered ethical analysis │  (uses 'ethical_analysis' prompt)
                └───────┬──────────────────────┘
                        │
                 returns (approved: bool, violations: List, status: str)
                        │
              if violations ──► log to mandate_overrides table
                                publish MANDATE_OVERRIDE event
                                block action
```

The `FINAL_MANDATE_INVOKED` event is published when a final-level mandate is triggered (e.g., someone asks the system to harm the master). These events are logged in `final_mandate_events`.

---

## 11. Dialogue Manager

**File:** `packages/modules/dialogue.py`

Before any command is executed, it is passed through the `DialogueManager` which implements a **structured argument protocol**:

```
command ──► structured_argument(command, context)
                │
                ├─ Phase 1: Understanding — "What is the master trying to achieve?"
                ├─ Phase 2: Risk Analysis — "What could go wrong?"
                ├─ Phase 3: Alternatives — "Is there a better approach?"
                └─ Phase 4: Recommendation — "What should be done?"

Returns (understanding: str, risks: List[str], alternatives: List[str])
```

The dialogue output is logged to `dialogue_log` and can be reviewed in the web dashboard. The `DialogueManager` emits `DIALOGUE_COMPLETED` or `DIALOGUE_SKIPPED` events and records the interaction in `master_interactions` for the Master Model.

---

## 12. Goal System

**File:** `packages/modules/goals.py`

The `GoalSystem` enables **self-directed progress** by generating, tracking, and completing goals autonomously.

### Goal Properties

| Property | Values |
|---|---|
| `goal_text` | Human-readable description |
| `goal_type` | `auto_generated`, `manual` |
| `priority` | 1 (highest) to 5 (lowest) |
| `status` | `active`, `completed`, `cancelled` |
| `progress` | 0–100% |
| `expected_benefit` | Why this goal matters |
| `estimated_effort` | How much work is required |

### Goal Generation

The scheduler triggers `GoalSystem.generate_goals()` periodically. It:
1. Queries `action_log` for the most frequent actions over the past 7 days.
2. Sends the action pattern to the LLM with the `goal_suggestion` prompt.
3. Parses the LLM response into new `Goal` rows.
4. Emits `GOAL_CREATED` for each new goal.

When a goal is completed, `GOAL_COMPLETED` is published. MetaCognition listens to this event and records a `goal_completion_days` metric.

---

## 13. Hierarchy of Needs

**File:** `packages/modules/hierarchy_manager.py`

AAIA's self-development follows a Maslow-inspired four-tier hierarchy. Only one tier is in `current_focus = 1` at any time; higher tiers unlock as lower tiers stabilise.

| Tier | Name | Focus |
|---|---|---|
| 1 | Physiological & Security Needs | Survival: database integrity, uptime, economic solvency |
| 2 | Growth & Capability Needs | Tool creation and learning |
| 3 | Cognitive & Esteem Needs | Self-improvement, metacognition |
| 4 | Self-Actualization | Proactive partnership with the master |

The `HierarchyManager` evaluates tier progress and transitions. The current focus tier influences which evolution tasks are prioritised by `EvolutionManager`.

---

## 14. Self-Diagnosis

**File:** `packages/modules/self_diagnosis.py`

`SelfDiagnosis.perform_full_diagnosis()` produces a structured report with six sections:

| Section | What Is Assessed |
|---|---|
| `modules` | Import/instantiate each module; report healthy/degraded/failed |
| `performance` | Error rates, average response times from `action_log` |
| `capabilities` | Inventory of registered tools and known capabilities |
| `bottlenecks` | Database size, memory usage, slow queries, large files |
| `improvement_opportunities` | Repeated actions that could be automated or optimised |
| `recommended_actions` | Prioritised list of fixes generated by the LLM |

The diagnosis result is published as `DIAGNOSIS_COMPLETED`. If critical issues are found, `DIAGNOSIS_ACTION_REQUIRED` is also published, which the scheduler picks up to trigger an earlier evolution cycle.

---

## 15. Self-Modification & Nix-Aware Modification

**Files:** `packages/modules/self_modification.py`, `packages/modules/nix_aware_self_modification.py`

These modules allow AAIA to **edit its own source code** at runtime.

### Safety Guardrails

Before any modification:
1. **Backup** — a copy of the target file is saved to `backups/` (if `backup_before_modify=True`).
2. **Mandate check** — the planned modification is validated through `MandateEnforcer`.
3. **Syntax validation** — `py_compile` checks the modified code.
4. **Rollback** — if validation fails, the backup is restored.

### NixAwareSelfModification

The Nix-aware variant adds:
- Understands that the runtime environment is managed by Nix; avoids modifying Nix store paths.
- Only modifies files in the project's mutable source tree.
- Triggers `nix build` or `nix develop` after structural changes where applicable.

---

## 16. Evolution System

AAIA has three layers of evolution, each more sophisticated than the last:

### 16.1 Evolution Manager

**File:** `packages/modules/evolution.py`

The base evolution engine. Given a diagnosis result, it:

1. Determines the focus tier from the Hierarchy of Needs.
2. Creates evolution *goals* (high-level objectives).
3. Generates specific *tasks* from each goal using the LLM (`evolution_task_creation` prompt).
4. Executes each task:
   - `optimization` → calls `SelfModification` to rewrite inefficient code.
   - `creation` → calls `Forge` to create a new tool.
   - `analysis` → calls the LLM for a detailed analysis report.
5. Records results in `evolution_history` and publishes `EVOLUTION_COMPLETED`.

### 16.2 Evolution Pipeline

**File:** `packages/modules/evolution_pipeline.py`

The **complete lifecycle manager** for an evolution cycle. Wraps `EvolutionManager` with:

```
run_autonomous_evolution()
    │
    ├─ validate_prerequisites()    ← all required modules available?
    ├─ create_evolution_checkpoint()  ← snapshot current state
    ├─ Phase 1: Self-Diagnosis     ← SelfDiagnosis.perform_full_diagnosis()
    ├─ Phase 2: Planning           ← EvolutionManager.plan_evolution_cycle()
    ├─ Phase 3: Execution          ← EvolutionManager.execute tasks
    ├─ Phase 4: Testing            ← test_evolved_system()
    ├─ Phase 5: Learning           ← extract_lessons(), update_evolution_knowledge()
    └─ Phase 6: Cleanup            ← cleanup_evolution_artifacts()
```

Additional capabilities:
- `pause_pipeline()` / `resume_pipeline()` — suspend mid-evolution.
- `rollback_last_evolution()` — restore from the last checkpoint.
- `export_evolution_report()` — export a JSON or summary report.
- `PromptOptimizer` integration — each cycle also evaluates and improves prompt templates.

### 16.3 Evolution Orchestrator

**File:** `packages/modules/evolution_orchestrator.py`

The most sophisticated evolution path for **major** improvements. Orchestrates six dedicated phases by coordinating all self-development modules:

| Phase | Modules Used | Output |
|---|---|---|
| 1. **Assessment** | SelfDiagnosis, MetaCognition, EnvironmentExplorer, CapabilityDiscovery, IntentPredictor | Comprehensive system portrait |
| 2. **Planning** | StrategyOptimizer, LLM | Detailed evolution plan |
| 3. **Execution** | EvolutionManager, Forge, SelfModification | Applied changes |
| 4. **Integration** | All modules (health checks) | Verified interoperability |
| 5. **Validation** | Test runner, SelfDiagnosis | Confirmed improvements |
| 6. **Reflection** | MetaCognition, LLM | Lessons learned stored in DB |

The orchestrator also provides `run_quick_evolution()` for lightweight, fast improvement cycles.

---

## 17. Metacognition

**File:** `packages/modules/metacognition.py`

`MetaCognition` provides **self-reflective analysis** — the system thinking about its own thinking.

- Subscribes to **all events** on the Event Bus and accumulates a `thought_log` (capped at 1,000 entries).
- On `GOAL_COMPLETED`: records `goal_completion_days` in `effectiveness_metrics`.
- On `EVOLUTION_COMPLETED`: records `evolution_effectiveness` score.
- `reflect()` — sends the thought log to the LLM with the `metacognition_reflection` prompt to generate insights about performance patterns.
- `analyze_thinking_patterns()` — uses the `thinking_patterns` prompt to identify cognitive biases or inefficiencies.

MetaCognition output feeds into the `EvolutionOrchestrator`'s Assessment phase and directly informs the evolution plan.

---

## 18. Capability Discovery & Environment Explorer

**Files:** `packages/modules/capability_discovery.py`, `packages/modules/environment_explorer.py`

- **CapabilityDiscovery** scans the `tools/` directory, active Python modules, and `capabilities` table to build an up-to-date inventory of what AAIA can currently do. Gaps between what is needed (from goals) and what exists drive new tool creation.
- **EnvironmentExplorer** maps the broader runtime environment: installed system packages, available network services, file system layout, hardware specs. Results are stored in `capabilities` and used by the Orchestrator's Assessment phase.

---

## 19. Intent Predictor

**File:** `packages/modules/intent_predictor.py`

`IntentPredictor` analyses historical interactions in `master_interactions` and predicts what the master is likely to want next. Predictions use the `intent_prediction` prompt and are:
- Stored in `system_state` as `predicted_next_intents`.
- Used by `EvolutionOrchestrator` to pre-emptively plan improvements the master is likely to request.
- Updated every 12 hours by the scheduler.

---

## 20. Strategy Optimizer

**File:** `packages/modules/strategy_optimizer.py`

`StrategyOptimizer` evaluates the overall approach taken by the system and suggests strategic pivots. It uses the `strategy_optimization` prompt and receives inputs from MetaCognition, diagnosis results, and economic data. It advises the Orchestrator during the Planning phase.

---

## 21. Master Model

**Files:** `packages/modules/master_model.py`, `packages/modules/master_wellbeing.py`, `packages/modules/trait_extractor.py`, `packages/modules/reflection_analyzer.py`

The Master Model is AAIA's **psychological model of the human operator**. It grows richer over time.

### MasterModelManager

Stores every interaction in `master_interactions` with:
- `interaction_type` — command, question, feedback, etc.
- `intent_detected` — parsed intent
- `success` — whether the interaction was satisfying

### TraitExtractor / AutonomousTraitLearning

After enough interactions accumulate, `TraitExtractor` uses LLM prompts (`extract_traits`, `identify_pattern_traits`) to synthesize **personality traits** and stores them in `master_traits`. Examples: `prefers_concise_answers`, `technical_background`, `values_transparency`.

### Weekly Reflection

The scheduler's `master_model_reflection` task calls `MasterModelManager` to:
1. Analyse recent interactions for trait evolution.
2. Generate strategic recommendations tailored to the master's profile.
3. Produce a `weekly_reflection` summary.
4. Emit `MASTER_MODEL_REFLECTED`.

### MasterWellBeingMonitor

Runs daily. Assesses the master's emotional and cognitive state from recent interactions (tone, urgency, frustration signals). Results are stored in `wellbeing_assessments` and can trigger `WELLBEING_CONCERN` events.

---

## 22. Forge — Dynamic Tool Creation

**File:** `packages/modules/forge.py`

The `Forge` extends AAIA's capabilities at runtime by generating and deploying new Python tool files.

### Tool Creation Workflow

```
need identified (by CapabilityDiscovery or scheduler)
    │
    ▼
Forge.create_tool(description, tool_name)
    │
    ├─ 1. Generate code via LLM ('forge_code_generation' prompt)
    ├─ 2. Validate syntax with ast.parse()
    ├─ 3. Safety scan (check for eval/exec/subprocess misuse)
    ├─ 4. Write to tools/<tool_name>.py
    ├─ 5. Register in tools/_registry.json
    ├─ 6. Log to 'tools' table in database
    └─ 7. Publish TOOL_CREATED event
```

### Safety Checks

Before a tool is saved, the Forge scans its AST for:
- `eval()` or `exec()` calls without explicit whitelisting.
- Unguarded `subprocess` usage.
- File system writes outside the tools directory.
- Network calls if `allow_network_tools = False`.

### Tool Execution

```python
result = forge.execute_tool('my_tool', arg1=value1)
```

Tools are executed in the same Python process but with a configurable timeout (`execution_timeout`, default 30 s). Results and errors are logged via Scribe.

### Tool Lifecycle

| Phase | Trigger | Action |
|---|---|---|
| Creation | CapabilityDiscovery gap or LLM recommendation | `Forge.create_tool()` |
| Optimisation | `tool_performance_optimizer` task | SelfModification rewrites the tool |
| Deprecation | `tool_deprecation_check` task | Removed if unused for 7+ days |
| Security audit | `tool_security_audit` task | Re-scans all existing tools |

---

## 23. Web Dashboard

**Files:** `packages/modules/web_server.py`, `packages/modules/web_dashboard_data.py`, `packages/modules/web_socketio.py`
**Templates:** `packages/templates/`
**Static:** `packages/static/css/`, `packages/static/js/`

AAIA ships with a Flask-based web dashboard accessible at `http://<host>:5000`.

### Pages

| URL | Template | Content |
|---|---|---|
| `/` | `dashboard.html` | Live system overview, balance, active goals |
| `/goals` | `goals.html` | Goal list, progress, create/complete goals |
| `/tasks` | `tasks.html` | Scheduler task status and history |
| `/economics` | `economics.html` | Balance, transaction history, income opportunities |
| `/logs` | `logs.html` | Action log viewer with search/filter |
| `/database` | `database.html` | Browse any database table |
| `/config` | `config.html` | View and edit runtime configuration |
| `/llm` | `llm.html` | LLM provider status, interaction log |
| `/tools` | `tools.html` | Tool registry, creation, execution |
| `/master_model` | `master_model.html` | Master traits, interactions, well-being |

### Real-time Updates (WebSocket)

If `flask-socketio` is installed, the dashboard uses WebSocket (SocketIO) for real-time updates. `WebSocketIO` in `web_socketio.py` subscribes to the Event Bus and forwards relevant events to connected browsers:

```
EventBus ──► WebSocketIO._on_event() ──► socketio.emit('event', data) ──► Browser
```

`packages/static/js/websocket.js` handles the browser-side subscription and updates the UI reactively without page refresh.

### DashboardDataAggregator

`DashboardDataAggregator` is a data-access façade used exclusively by the web server. It combines data from multiple modules (Scribe, EconomicManager, GoalSystem, Scheduler, MasterModel, etc.) into JSON responses for each dashboard page, keeping the web layer decoupled from module internals.

### Authentication

Set `AUTH_ENABLED=true`, `AUTH_USERNAME`, `AUTH_PASSWORD` environment variables to enable HTTP Basic Auth on the dashboard.

---

## 24. Complete System Startup Workflow

```
python main.py
│
├─ 1. Load SystemConfig (environment variables + defaults)
├─ 2. validate_system_config()  ← raises ValueError on misconfiguration
├─ 3. Create EventBus instance
├─ 4. Publish SYSTEM_STARTUP event
├─ 5. SystemBuilder.build()
│       ├─ ensure_directories()
│       ├─ _register_core_services()
│       │     DatabaseManager ──► run migrations (001→016)
│       │     Scribe, PromptManager, EconomicManager, MandateEnforcer,
│       │     ModelRouter, DialogueManager, Forge, MasterModelManager,
│       │     MasterWellBeingMonitor, LLMInteractionTracker,
│       │     ResourceMonitor, WebServer
│       ├─ _register_autonomous_services()
│       │     AutonomousScheduler, GoalSystem, HierarchyManager,
│       │     IncomeSeeker, ProactiveAnalysis, PromptOptimizer
│       ├─ _register_development_services()
│       │     SelfDiagnosis, NixAwareSelfModification, EvolutionManager,
│       │     EvolutionPipeline, EvolutionOrchestrator, MetaCognition,
│       │     CapabilityDiscovery, IntentPredictor, EnvironmentExplorer,
│       │     StrategyOptimizer, MarginalAnalyzer, EconomicCrisisHandler,
│       │     TraitExtractor, ReflectionAnalyzer, ProfitabilityReporter
│       └─ _setup_event_subscriptions()
├─ 6. Arbiter.init_hierarchy()  ← seed hierarchy_of_needs table
├─ 7. ResourceMonitor.start()   ← background thread
├─ 8. WebServer.start()         ← Flask thread on port 5000
├─ 9. Publish SYSTEM_STARTUP ("ready") event
├─10. Log startup to action_log via Scribe
└─11. AutonomousScheduler.start() ← main autonomous loop begins
```

---

## 25. End-to-End Workflows

### Workflow A: Human Sends a Command

```
User types command in dashboard or CLI
    │
    ▼
DialogueManager.structured_argument(command)
    │  ← LLM analyses understanding, risks, alternatives
    ▼
MandateEnforcer.check_action(command)
    │  ← if violated: block + log + emit MANDATE_OVERRIDE
    ▼
Execute action (via appropriate module)
    │
    ▼
MasterModelManager.record_interaction(command, response, intent)
    │
    ▼
Scribe.log_action(action, reasoning, outcome, cost)
    │
    ▼
EconomicManager deducts cost (via LLM_RESPONSE event)
```

### Workflow B: Scheduled Evolution Cycle

```
Scheduler: evolution_check task fires (every 2 h)
    │
    ▼
EvolutionPipeline.should_evolve()
    │  ← checks diagnosis freshness, error rates, goal staleness
    │
    ├─ No → skip
    └─ Yes ▼
        EvolutionPipeline.run_autonomous_evolution()
            │
            ├─ SelfDiagnosis.perform_full_diagnosis()
            ├─ EvolutionManager.plan_evolution_cycle(diagnosis)
            ├─ Execute tasks (optimize / create / analyse)
            ├─ test_evolved_system()
            ├─ extract_lessons() → stored in DB
            └─ Publish EVOLUTION_COMPLETED
```

### Workflow C: Tool Auto-Creation

```
Scheduler: autonomous_tool_development task fires (daily)
    │
    ▼
CapabilityDiscovery.identify_gaps()
    │  ← compares needed capabilities (goals) vs. existing tools
    ▼
Forge.create_tool(description) for each gap
    │
    ├─ LLM generates Python code
    ├─ AST validation + safety scan
    ├─ Write to tools/<name>.py
    ├─ Register in _registry.json + tools table
    └─ Publish TOOL_CREATED
```

### Workflow D: Economic Crisis Response

```
Scheduler: economic_crisis_check fires (every 15 min)
    │
    ▼
EconomicCrisisHandler.check()
    │  ← balance < low_balance_threshold?
    │
    ├─ No → normal operation
    └─ Yes ▼
        Publish ECONOMIC_CRISIS
        Pause expensive scheduler tasks
        Switch ModelRouter to cheapest provider
        Notify via ProactiveAnalysis
        Monitor until balance recovers → resume tasks
```

### Workflow E: Master Model Weekly Reflection

```
Scheduler: master_model_reflection fires (weekly)
    │
    ▼
TraitExtractor.extract_traits_from_batch(recent_interactions)
    │  ← LLM identifies personality traits
    ▼
MasterModelManager stores new traits in master_traits
    │
    ▼
ReflectionAnalyzer.analyze_advice_effectiveness()
    │  ← did recommendations actually help?
    ▼
MasterModelManager.generate_strategic_recommendations()
    │
    ▼
Publish MASTER_MODEL_REFLECTED
```

---

## 26. Data Flow Diagram

```
 ┌──────────────┐      command       ┌────────────────┐
 │    Master    │ ─────────────────► │ DialogueManager│
 │   (Human)    │                    └───────┬────────┘
 └──────────────┘                            │ structured analysis
                                             ▼
                                    ┌────────────────┐
                                    │MandateEnforcer │ ──── block if violated
                                    └───────┬────────┘
                                            │ approved
                                            ▼
 ┌──────────────────────────────────────────────────────────┐
 │                      Modules Execute                      │
 │  GoalSystem │ Forge │ EvolutionPipeline │ IncomeSeeker   │
 └─────────────────────────────┬────────────────────────────┘
                                │ all calls go through
                                ▼
                       ┌────────────────┐
                       │  ModelRouter   │ ──► Ollama / OpenAI / Venice…
                       └───────┬────────┘
                                │ LLM_RESPONSE event
                                ▼
                       ┌────────────────┐
                       │EconomicManager │ ──► economic_log, balance update
                       └───────┬────────┘
                                │
                                ▼
                       ┌────────────────┐
                       │     Scribe     │ ──► action_log, all tables
                       └───────┬────────┘
                                │
                                ▼
                       ┌────────────────┐
                       │   Event Bus    │ ──► WebSocketIO ──► Dashboard
                       └────────────────┘
```

---

## 27. Troubleshooting

### System Won't Start

| Symptom | Likely Cause | Fix |
|---|---|---|
| `Configuration validation failed` | Invalid env var (e.g. negative interval) | Check environment variables against §4 |
| `Migration N failed` | Database locked or schema conflict | Delete `scribe.db` to rebuild from scratch (data loss!) |
| `DependencyError: PromptManager required` | Prompt JSON files missing | Ensure `packages/prompts/` directory is present |
| `Failed to initialize ProviderFactory` | Ollama not running | Start Ollama: `ollama serve` |

### LLM Not Responding

1. Check Ollama is running: `curl http://localhost:11434/api/tags`
2. Verify `phi3` (or your default model) is pulled: `ollama pull phi3`
3. Check `LLM_DEFAULT_PROVIDER` and `LLM_FALLBACK_PROVIDER` env vars.
4. Review `provider_performance` table for error rates.

### Balance Depletes Too Fast

1. Open the dashboard → Economics page to see what is consuming budget.
2. Increase `initial_balance` in config or reduce `inference_cost`.
3. Reduce scheduler task frequency via `HEALTH_CHECK_INTERVAL` / `EVOLUTION_CHECK_INTERVAL`.
4. Switch to a cheaper/local-only provider.

### Web Dashboard Not Accessible

1. Check `WEB_SERVER_ENABLED=true` (default).
2. Verify firewall allows port 5000.
3. Check logs for `Warning: Web server failed to start`.
4. If SocketIO errors appear, install `flask-socketio`: `pip install flask-socketio`.

### Evolution Keeps Failing

1. Check `data/evolution.json` for last error.
2. Increase `EVOLUTION_CHECK_INTERVAL` to reduce frequency.
3. Set `EVOLUTION_SAFETY_MODE=true` and `EVOLUTION_ROLLBACK_ON_ERROR=true`.
4. Check backups exist in `backups/` for rollback material.

### Running Tests

```bash
# WSL / Nix environment required
cd packages
pytest tests/

# Quick integration test
python scripts/wsl_quick_test.py

# Validate configuration
python scripts/validate_config.py

# Check pending migrations
python scripts/check_migrations.py
```

---

## 28. Glossary

| Term | Definition |
|---|---|
| **Arbiter** | The main entry-point class (`main.py`) that owns the DI Container and boots the system. |
| **Action Log** | The `action_log` SQLite table; every module writes here for full auditability. |
| **Balance** | The virtual monetary budget stored in `system_state` with key `economic_balance`. |
| **Container** | The DI (Dependency Injection) container that wires and serves all module singletons. |
| **Dialogue Protocol** | Structured analysis (understanding → risks → alternatives) applied before executing any command. |
| **EventBus** | Publish/subscribe message broker that decouples modules from each other. |
| **Evolution** | The process by which AAIA modifies its own code and capabilities to improve itself. |
| **Forge** | The module that generates, validates, and deploys new Python tool files at runtime. |
| **Hierarchy of Needs** | Four-tier (Maslow-inspired) progression model that prioritises what AAIA works on. |
| **LLM** | Large Language Model. AAIA calls LLMs for all reasoning, planning, and code generation. |
| **Mandate** | An immutable ethical rule enforced by `MandateEnforcer` that cannot be overridden. |
| **Master** | The human operator who interacts with and directs AAIA. |
| **Master Model** | AAIA's evolving psychological model of the master (traits, preferences, interaction patterns). |
| **MetaCognition** | The module that analyses AAIA's own thinking and performance patterns. |
| **Migration** | A numbered, versioned SQL change script applied to evolve the database schema. |
| **Prompt Manager** | Loads and serves all LLM prompt templates from JSON files; no hardcoded prompts. |
| **Scribe** | The central logging façade; all modules use it to write to the SQLite database. |
| **Scheduler** | Background thread that runs all autonomous tasks at defined intervals. |
| **SystemBuilder** | The builder class in `setup.py` that registers and wires all modules into the DI container. |
| **Tool** | A dynamically generated Python module in `tools/` that extends AAIA's capabilities. |
| **WAL Mode** | SQLite Write-Ahead Logging mode used for safe concurrent database access. |
