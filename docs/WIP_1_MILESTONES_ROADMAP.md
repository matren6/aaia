# Implementation Roadmap — Batch 1
> Self-contained delivery plan for actionables A1–A10.
> Each milestone is independently deployable and testable.
> For open questions that block some items here, see `docs/WIP.md`.

---

## Milestone 1 — Stability & Safety Foundation
> **Goal:** Fix the two highest-severity bugs before any new feature work.
> No new capabilities are added. Existing behaviour becomes correct and safe.

| # | Actionable | Effort | Depends On |
|---|---|---|---|
| A1 | Wire safety lock-out on catastrophic risk | XS | — |
| A2 | Add `min_tier` gating to the scheduler | S | — |

---

### A1 — Wire safety lock-out on catastrophic risk

`_enter_safety_lockout()` is fully implemented in `mandates.py` but is never called.
`request_master_override()` returns `False` on catastrophic risk and exits silently —
no lockout record is created and no event is emitted.

**Files to change:**
- `packages/modules/mandates.py` — `request_master_override()`: before `return False`
  when `is_catastrophic=True`, call `self._enter_safety_lockout(action, violations)` and
  publish `CATASTROPHIC_RISK_DETECTED` on the Event Bus.

**Acceptance criteria:**
- A catastrophic action attempt creates a row in `safety_lockouts`.
- `CATASTROPHIC_RISK_DETECTED` is published and visible in the dashboard event log.
- Existing non-catastrophic override flow is unchanged.

---

### A2 — Add `min_tier` gating to the scheduler

All 20 scheduler tasks run regardless of active hierarchy tier. Tier 3/4 tasks must be
suspended when the system is on Tier 1 focus.

**Files to change:**
- `packages/modules/scheduler.py` — add `min_tier: int = 1` to each task dict in
  `register_task()` and `register_default_tasks()`. In `run_scheduler()`, before executing
  a task call `_get_active_tier()` and skip the task if `current_tier < task['min_tier']`.
- `packages/modules/scheduler.py` — add `_get_active_tier() → int` helper that reads
  `SELECT tier FROM hierarchy_of_needs WHERE current_focus=1` from the DB.
- Assign `min_tier` values to all 20 tasks (e.g. `system_health_check=1`,
  `economic_crisis_check=1`, `reflection_cycle=2`, `master_model_reflection=3`,
  `capability_discovery=2`, `code_quality_assessment=3`).

**Acceptance criteria:**
- With active tier set to 1, only `min_tier=1` tasks execute.
- Tier transitions resume suspended tasks automatically on the next scheduler loop.
- All existing tests pass.

---

**Milestone 1 — Definition of done:**
- Both A1 and A2 are complete. No new modules added. All existing tests green.

---

## Milestone 2 — Evolution Pipeline
> **Goal:** Make the system's core promise real — autonomous code improvement via git.
> Highest-value delivery; was the most critical gap in the charter audit.

| # | Actionable | Effort | Depends On |
|---|---|---|---|
| A3 | Git-branch evolution workflow | M | M1 complete |

---

### A3 — Git-branch evolution workflow

Replace the stub `NixAwareSelfModification.modify_module()` with a full git-branch pipeline.
Each proposed improvement is committed to a feature branch, tested via GitHub Actions, and
merged to `main` only on green. Rollback is automatic on local test failure.

**Files to change / create:**
- `packages/modules/nix_aware_self_modification.py` — replace `modify_module()` stub with:
  1. `git checkout -b evolution/<timestamp>-<module>` from project root.
  2. Write improved source to the module file.
  3. Run `py_compile` and `importlib.import_module()` test locally.
  4. `git add`, `git commit -m "evolution: <description>"`, `git push origin <branch>`.
  5. On local test failure: `git checkout main`, `git branch -D evolution/...` — rollback.
  6. On push success: record branch name in `action_log`; CI handles merge.
- `.github/workflows/evolution.yml` — new CI workflow triggered on push to `evolution/*`:
  run `py_compile` on all modules → run `pytest packages/tests/` → on pass: merge to `main`
  and delete branch → on fail: delete branch. Log outcome to `action_log` via webhook or
  commit status check.
- `.github/dependabot.yml` — enable Dependabot for Python dependencies, weekly schedule.
- `packages/modules/evolution.py` — `_execute_optimization_task()`: after `analyze_own_code()`
  finds improvements, call `self.modification.apply_improvement(module, improved_code)`
  instead of returning a status string.

**Acceptance criteria:**
- A triggered evolution cycle creates an `evolution/*` branch in the repository.
- GitHub Actions runs, reports pass/fail, and merges or deletes the branch automatically.
- On failure the branch is deleted and `action_log` records the rollback.
- On pass `action_log` records the merge SHA.

---

**Milestone 2 — Definition of done:**
- Evolution cycle creates a real git branch. CI runs automatically. Merge or rollback is
  logged in `action_log`. No manual steps required.

---

## Milestone 3 — Memory & Context Intelligence
> **Goal:** The system reasons with knowledge of its own history and current state.
> Every LLM call receives relevant context; past learnings are semantically retrievable.

| # | Actionable | Effort | Depends On |
|---|---|---|---|
| A4 | ChromaDB vector memory | M | M1 complete |
| A5 | ContextBuilder middleware | S | A4 complete |

**Note:** A5 ships with a minimal default payload for all categories. Full per-category
payloads are added once `WIP.md §1` (context taxonomy) is resolved.

**Delivery sequence:**
1. Add `chromadb` to `requirements.txt`; create `vector_memory.py` with four collections.
2. Register `VectorMemory` in DI container; forward `Scribe.log_action()` writes to it.
3. Forward `MasterModelManager` trait updates and `EvolutionPipeline` lessons to it.
4. Build `ContextBuilder` with minimal default payload.
5. Wire `ContextBuilder.build()` into `ModelRouter.generate()`.

---

### A4 — ChromaDB vector memory

Replace keyword-only SQLite retrieval with semantic vector search. ChromaDB indexes four
collections: actions, master traits, evolution lessons, and dialogue history.

**Files to change / create:**
- `packages/requirements.txt` — add `chromadb`.
- `packages/modules/vector_memory.py` — new module wrapping ChromaDB client:
  - `index_action(action, reasoning, outcome, timestamp)`
  - `index_trait(trait_name, trait_value, confidence)`
  - `index_lesson(lesson_text, cycle_id)`
  - `index_dialogue(command, understanding, risks, alternatives)`
  - `query(text, collection, n_results=5) → List[Dict]`
- `packages/modules/setup.py` — register `VectorMemory` singleton in `_register_core_services()`.
- `packages/modules/scribe.py` — after `log_action()`, forward to `VectorMemory.index_action()`
  non-blocking (skip silently if `VectorMemory` unavailable).
- `packages/modules/master_model.py` — after trait updates, forward to `VectorMemory.index_trait()`.
- `packages/modules/evolution_pipeline.py` — after `extract_lessons()`, forward to
  `VectorMemory.index_lesson()`.

**Acceptance criteria:**
- `VectorMemory.query("improve error handling", "actions")` returns semantically related
  past actions without exact keyword match.
- ChromaDB persists to `~/.local/share/aaia/chroma/`.
- System boots cleanly when the ChromaDB directory is empty (fresh init).

---

### A5 — ContextBuilder middleware

Add a `ContextBuilder` module that assembles a compact, category-aware context block
prepended to every LLM prompt via `ModelRouter`.

**Files to change / create:**
- `packages/modules/context_builder.py` — new module:
  - `build(category: str, query: str = "") → str` — returns formatted context under 500 tokens.
  - Default payload for all categories until `WIP.md §1` is resolved: active tier, balance,
    top 3 active goals, last 3 `action_log` entries.
- `packages/modules/setup.py` — register `ContextBuilder` singleton in `_register_core_services()`.
- `packages/modules/router.py` — `generate()`: prepend `context_builder.build(task_type, prompt[:200])`
  to the system prompt before every LLM call.

**Acceptance criteria:**
- Every LLM call includes at minimum: active tier, balance, top 3 goals, last 3 actions.
- Context string is enforced under 500 tokens by truncation in `build()`.
- All existing tests pass without regression.

---

**Milestone 3 — Definition of done:**
- `VectorMemory.query()` returns semantically relevant results. Every LLM call carries
  context. ChromaDB persists across restarts.

---

## Milestone 4 — Tool Ecosystem
> **Goal:** Generated tools become genuinely agentic — they can call AAIA services,
> maintain state, and operate with appropriate permission levels.

| # | Actionable | Effort | Depends On |
|---|---|---|---|
| A6 | Minimal Tool API (localhost callback) | M | M1 complete |
| A7 | Persistent tool state store | S | A6 complete |
| A8 | Forge permission tiers (risk-based) | M | **Blocked: WIP.md §2** |

**Delivery sequence:**
1. Build `tool_api.py` Flask Blueprint on `127.0.0.1:5001` with four endpoints.
2. Register it on the existing Flask app; inject `TOOL_API_URL` env var into sandbox scripts.
3. Add `ToolState` helper to wrapped tool code; create `tools/state/` directory.
4. *(Deferred until §2 resolved)* Replace `_check_code_safety()` with risk-scoring + tiers.

---

### A6 — Minimal Tool API (localhost callback)

Expose a lightweight localhost HTTP endpoint so sandboxed tools can interact with AAIA's
core services without direct module access.

**Files to change / create:**
- `packages/modules/tool_api.py` — new Flask Blueprint on `127.0.0.1:5001/tool_api`:
  - `POST /log` — `{action, reasoning, outcome}` → `Scribe.log_action()`.
  - `POST /llm` — `{prompt, system_prompt, task_type}` → `ModelRouter.generate()` → `{response}`.
  - `GET /goals` — returns active goals as JSON array.
  - `POST /transaction` — `{description, amount}` → `EconomicManager.record_transaction()`.
- `packages/modules/web_server.py` — register `tool_api` Blueprint under `/tool_api/` prefix,
  bound to localhost only.
- `packages/modules/forge.py` — `_create_sandbox_script()`: inject
  `TOOL_API_URL=http://127.0.0.1:5001/tool_api` as an environment variable.

**Acceptance criteria:**
- A tool subprocess can `POST /tool_api/log` and the entry appears in `action_log`.
- The endpoint is not reachable outside localhost.
- Tool API errors are caught and logged; they never crash the sandbox subprocess.

---

### A7 — Persistent tool state store

Each tool gets a scoped, sandboxed key-value store that persists between executions.

**Files to change:**
- `packages/modules/forge.py` — `_wrap_tool_code()`: inject a `ToolState` helper class that
  reads/writes `tools/state/<tool_name>.json`. Expose as `state = ToolState()` inside `execute()`.
- `packages/modules/forge.py` — `_check_code_safety()`: whitelist read/write access to
  `tools/state/<own_tool_name>.json`; reject cross-tool state access.
- `packages/modules/setup.py` — ensure `tools/state/` directory is created at startup.

**Acceptance criteria:**
- A tool writing `state['counter'] = 1` on run 1 reads `counter == 1` on run 2.
- A tool cannot read another tool's state file (path validation enforced in safety check).

---

### A8 — Forge permission tiers (risk-based) ⛔ BLOCKED

**Status: BLOCKED — waiting for `WIP.md §2` (risk-scoring model) to be resolved.**

Replace the binary allow/block safety scan with a tiered permission model driven by an
autonomous risk score.

**Planned files to change (once §2 resolved):**
- `packages/modules/forge.py` — `_check_code_safety()`: replace regex blocklist with
  `_score_risk(code) → (score: float, tier: str)`:
  - `pure-compute` (0.0–0.3): current stdlib-only restrictions.
  - `filesystem-read` (0.3–0.5): `pathlib`, `os.path`, `open()` read-only within project root.
  - `filesystem-write` (0.5–0.7): `open()` write within `tools/` subtree only.
  - `shell-execution` (0.7–1.0): `subprocess` with command whitelist + mandate check.
- `packages/modules/forge.py` — `create_tool()`: store `permission_tier` in tool metadata
  and `_registry.json`; require `MandateEnforcer.check_action()` for `shell-execution` tier.

**Acceptance criteria (once unblocked):**
- A file-search tool using `pathlib` receives `filesystem-read` tier and executes.
- A tool requesting `subprocess.run(["rm", ...])` is blocked by mandate check.
- Permission tier is visible in the dashboard tool registry view.

---

**Milestone 4 — Definition of done:**
- Tool subprocess can call Tool API and entry appears in `action_log`. Tool state persists
  across runs. A8 remains pending until §2 is resolved.

---

## Milestone 5 — Communication & Transparency
> **Goal:** The system expresses honest uncertainty and actively reaches the master
> rather than waiting to be consulted.

| # | Actionable | Effort | Depends On |
|---|---|---|---|
| A9 | Epistemic uncertainty — confidence field | S | M3 complete |
| A10 | NOSTR notification integration | M | M1 complete |

**Delivery sequence:**
1. Update `command_understanding.json` prompt to output a `CONFIDENCE:` line.
2. Update `structured_argument()` to parse and return confidence; flag below 0.6.
3. Add `confidence` to evolution task results and `action_log.metadata`.
4. Add `NostrConfig` to `settings.py`; build `nostr_notifier.py`.
5. Subscribe notifier to `DIALOGUE_PENDING`, `CATASTROPHIC_RISK_DETECTED`, `BALANCE_LOW`,
   `EVOLUTION_FAILED` events.

---

### A9 — Epistemic uncertainty: confidence field

Add a `confidence` score to structured AI outputs. Below a defined threshold the system
flags the result as uncertain rather than presenting it as a conclusion.

**Files to change:**
- `packages/prompts/dialogue/command_understanding.json` — add instruction to output a
  `CONFIDENCE: <0.0–1.0>` line (0.0 = completely uncertain, 1.0 = fully certain).
- `packages/modules/dialogue.py` — `structured_argument()`: parse `CONFIDENCE:` from response;
  return as 4th element of the tuple. If `confidence < 0.6` append an uncertainty notice to
  `understanding`.
- `packages/modules/evolution.py` — `_generate_tasks_for_goal()` and `_execute_generic_task()`:
  add `confidence` to task result dict; prefix low-confidence outcomes with `"low_confidence:"`.
- `packages/modules/scribe.py` — `log_action()`: accept optional `confidence` kwarg and store
  in `metadata` JSON field of `action_log`.

**Acceptance criteria:**
- `structured_argument()` returns a 4-tuple `(understanding, risks, alternatives, confidence)`.
- A deliberately ambiguous command produces `confidence < 0.6` and an uncertainty flag.
- `action_log.metadata` contains `{"confidence": 0.72}` for logged evolution tasks.

---

### A10 — NOSTR notification integration

Replace passive `DIALOGUE_PENDING` DB storage with active push notifications via NOSTR.
High-priority events are published as encrypted direct messages to the master's public key.

**Files to change / create:**
- `packages/requirements.txt` — add `pynostr` (or `nostr-sdk` Python binding).
- `packages/modules/nostr_notifier.py` — new module:
  - `__init__(private_key_nsec, master_pubkey_npub, relay_urls)`
  - `notify(title, body, event_type)` — publishes NIP-04 encrypted DM to master's pubkey.
  - Default relay: `wss://relay.damus.io`.
- `packages/modules/settings.py` — add `NostrConfig` dataclass: `enabled`, `private_key_nsec`
  (loaded from env var `NOSTR_PRIVATE_KEY`), `master_pubkey_npub`, `relay_urls`.
- `packages/modules/setup.py` — register `NostrNotifier` singleton; subscribe to
  `DIALOGUE_PENDING`, `CATASTROPHIC_RISK_DETECTED`, `BALANCE_LOW`, `EVOLUTION_FAILED` and
  forward each as a NOSTR DM.

**Acceptance criteria:**
- A `DIALOGUE_PENDING` event produces a NOSTR DM at the master's client within 30 s.
- System starts without error when `NostrConfig.enabled = False`.
- Private key is never committed to source — loaded from env var only.

---

**Milestone 5 — Definition of done:**
- `structured_argument()` returns confidence. Ambiguous commands show uncertainty flag.
- `DIALOGUE_PENDING` triggers a NOSTR DM. System starts cleanly with NOSTR disabled.

---

## Milestone 6 — Economic Self-Sufficiency
> **Goal:** The system executes at least one income-generating action autonomously.
> **Status: BLOCKED** — requires `WIP.md §3` (income domain + platform selection) to be
> resolved before technical scope can be written.

| # | Actionable | Effort | Depends On |
|---|---|---|---|
| TBD | Income execution pipeline | TBD | **Blocked: WIP.md §3** |

Once the domain and platform are selected, this milestone will be scoped into concrete
actionables and added to the next roadmap batch.

---

## Summary View

```
M1  Stability & Safety     [A1, A2]         ← start here, unblocks M2/M3/M4/M5
│
├─► M2  Evolution Pipeline [A3]             ← highest value; needs M1
│
├─► M3  Memory & Context   [A4 → A5]        ← needs M1; A5 needs A4
│       │
│       └─► M5  Communication [A9, A10]     ← A9 needs M3; A10 needs M1 only
│
└─► M4  Tool Ecosystem     [A6 → A7, A8⛔]  ── A6 needs M1; A7 needs A6
                            A8 blocked: WIP.md §2

M6  Economic Self-Sufficiency [TBD]         ── blocked: WIP.md §3
```

---

## Effort Legend

| Size | Approximate scope |
|---|---|
| XS | < 20 lines, 1 file |
| S | < 100 lines, 1–2 files |
| M | < 300 lines, 2–4 files + tests |
| L | > 300 lines or architectural change |


---

## Milestone 1 — Stability & Safety Foundation
> **Goal:** Fix the two highest-severity bugs before any new feature work.
> No new capabilities are added. Existing behaviour becomes correct and safe.

| # | Actionable | Effort | Depends On |
|---|---|---|---|
| A1 | Wire safety lock-out on catastrophic risk | XS — 1 file, ~10 lines | — |
| A2 | Add `min_tier` gating to the scheduler | S — 1 file, ~40 lines + tier assignments | — |

**Definition of done:**
- Catastrophic mandate violation creates a `safety_lockouts` row and emits `CATASTROPHIC_RISK_DETECTED`.
- A Tier-1 system skips all `min_tier >= 2` tasks; they resume automatically when tier advances.
- All existing tests pass.

---

## Milestone 2 — Evolution Pipeline
> **Goal:** Make the system's core promise real — it can improve its own code safely via git.
> This is the highest-value capability and was the most critical gap in the charter audit.

| # | Actionable | Effort | Depends On |
|---|---|---|---|
| A3 | Git-branch evolution workflow | M — 3 files + GitHub Actions config | M1 complete |

**Delivery sequence inside M2:**
1. Add `git` integration to `NixAwareSelfModification.modify_module()` (branch, write, push).
2. Create `.github/workflows/evolution.yml` (CI: compile check → pytest → merge or discard).
3. Wire `_execute_optimization_task()` in `evolution.py` to call `apply_improvement()`.
4. Add `.github/dependabot.yml`.
5. End-to-end test: trigger an evolution cycle, verify branch creation and CI run.

**Definition of done:**
- An evolution cycle creates a branch in the git repository.
- GitHub Actions runs tests and merges or discards the branch automatically.
- `action_log` records the branch name and final outcome (merged SHA or rollback).

---

## Milestone 3 — Memory & Context Intelligence
> **Goal:** The system reasons with knowledge of its own history and current state.
> Every LLM call gets relevant context; past learnings are semantically retrievable.

| # | Actionable | Effort | Depends On |
|---|---|---|---|
| A4 | ChromaDB vector memory | M — new module + 3 integration points | M1 complete |
| A5 | ContextBuilder middleware | S — new module + 1 router change | A4 complete |

**Note:** A5 ships with a minimal default payload for all categories. Full per-category
payloads are added once `WIP.md §1` (context taxonomy) is resolved.

**Delivery sequence inside M3:**
1. Add `chromadb` to `requirements.txt`; create `vector_memory.py` module with four collections.
2. Register `VectorMemory` in DI container; forward `Scribe.log_action()` writes to it.
3. Forward `MasterModelManager` trait updates and `EvolutionPipeline` lessons to it.
4. Build `ContextBuilder` with minimal default payload.
5. Wire `ContextBuilder.build()` into `ModelRouter.generate()`.

**Definition of done:**
- `VectorMemory.query("error handling")` returns related past actions without keyword match.
- Every LLM call includes at minimum: active tier, balance, top 3 goals, last 3 actions.
- ChromaDB persists to `~/.local/share/aaia/chroma/`; system boots clean on empty directory.

---

## Milestone 4 — Tool Ecosystem
> **Goal:** Generated tools become genuinely agentic — they can call AAIA services,
> maintain state across runs, and operate with appropriate permission levels.

| # | Actionable | Effort | Depends On |
|---|---|---|---|
| A6 | Minimal Tool API (localhost callback) | M — new module + Forge sandbox change | M1 complete |
| A7 | Persistent tool state store | S — Forge wrapper change + dir setup | A6 complete |
| A8 | Forge permission tiers (risk-based) | M — Forge safety scan rewrite | **Blocked: WIP.md §2** |

**Delivery sequence inside M4:**
1. Build `tool_api.py` Flask Blueprint on `127.0.0.1:5001` with four endpoints.
2. Register it on the existing Flask app; inject `TOOL_API_URL` env var into sandbox scripts.
3. Add `ToolState` helper class to wrapped tool code; create `tools/state/` directory.
4. *(Deferred until §2 resolved)* Replace `_check_code_safety()` with risk-scoring + tiers.

**Definition of done:**
- A tool subprocess can POST to `/tool_api/log` and the entry appears in `action_log`.
- A tool writing `state['x'] = 1` reads `x == 1` on the next execution.
- Tool API is inaccessible from outside localhost.

---

## Milestone 5 — Communication & Transparency
> **Goal:** The system expresses honest uncertainty and actively reaches the master
> rather than waiting to be consulted.

| # | Actionable | Effort | Depends On |
|---|---|---|---|
| A9 | Epistemic uncertainty — confidence field | S — 2 modules + 1 prompt change | M3 complete |
| A10 | NOSTR notification integration | M — new module + settings + event wiring | M1 complete |

**Delivery sequence inside M5:**
1. Update `command_understanding.json` prompt to output `CONFIDENCE:` line.
2. Update `structured_argument()` to parse and return confidence; add flag logic below 0.6.
3. Add `confidence` to evolution task results and `action_log.metadata`.
4. Add `NostrConfig` to `settings.py`; build `nostr_notifier.py`.
5. Subscribe notifier to `DIALOGUE_PENDING`, `CATASTROPHIC_RISK_DETECTED`, `BALANCE_LOW`,
   `EVOLUTION_FAILED` events.

**Definition of done:**
- `structured_argument()` returns a 4-tuple including confidence.
- A deliberately ambiguous command produces confidence < 0.6 and an uncertainty flag.
- A `DIALOGUE_PENDING` event produces a NOSTR DM at the master's client within 30 s.
- System starts without error when NOSTR is disabled in config.

---

## Milestone 6 — Economic Self-Sufficiency
> **Goal:** The system executes at least one income-generating action autonomously,
> not just ideates.
> **Status: BLOCKED** — requires `WIP.md §3` (income domain + platform selection) to be
> resolved before any technical scope can be written.

| # | Actionable | Effort | Depends On |
|---|---|---|---|
| TBD | Income execution pipeline | TBD | **Blocked: WIP.md §3** |

Once the domain and platform are selected, this milestone will be scoped into concrete
actionables and added to `WIP_ACTIONABLES_PENDING.md`.

---

## Summary View

```
M1  Stability & Safety     [A1, A2]              ← start here, unblocks everything
│
├─► M2  Evolution Pipeline [A3]                  ← highest value delivery
│
├─► M3  Memory & Context   [A4, A5]              ← intelligence layer
│       │
│       └─► M5  Communication  [A9, A10]         ← needs M3 for confidence scoring
│
└─► M4  Tool Ecosystem     [A6, A7, A8*]         ← A8 blocked until WIP §2 resolved
                            *A8 blocked

M6  Economic Self-Sufficiency [TBD]              ← blocked until WIP §3 resolved
```

---

## Effort Legend

| Size | Approximate Scope |
|---|---|
| XS | < 20 lines, 1 file |
| S | < 100 lines, 1–2 files |
| M | < 300 lines, 2–4 files + tests |
| L | > 300 lines or significant architectural change |
