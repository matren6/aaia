# Open Questions & Pending Decisions
> Items here have **no confirmed decision yet**. Each blocks specific actionables in
> one or more roadmap files until resolved.
>
> Related files:
> - `WIP_1_MILESTONES_ROADMAP.md` — Batch 1 delivery plan (A1–A10)

---

## §1 — Context injection: request category taxonomy *(blocks A5 full payload)*

A `ContextBuilder` module has been decided (see `WIP_ACTIONABLES_PENDING.md A5`) and will
ship with a minimal default payload. The full per-category payloads cannot be implemented
until the category taxonomy is defined.

**Question:** What are the request categories and what context does each require?

Candidate categories to define payloads for:

| Category | Likely context needs |
|---|---|
| `evolution_task` | Active tier, diagnosis summary, last evolution outcome, goals |
| `dialogue_analysis` | Master traits, recent interactions, active goals, mandate list |
| `tool_creation` | Capability gaps, recent failed actions, existing tool registry |
| `reflection` | Last 7-day action summary, master traits, wellbeing score |
| `income_reasoning` | Balance, income opportunities, economic trends |
| `health_assessment` | Resource costs, error rates, module health status |

**Work needed before A5 is completed:** For each category, specify which DB fields are
included, the maximum token budget per field, and the priority order when the budget is
exceeded.

---

## §2 — Forge autonomous permission tiers: risk-scoring model *(blocks A8)*

The decision that tools self-assess their permission tier (no master approval) has been made.
The concrete risk-scoring algorithm has not.

**Question:** How does the system score a generated tool's risk level to assign it a
permission tier?

**Inputs to consider for the scoring model:**
- Which stdlib modules the tool imports (`os`, `subprocess`, `pathlib`, `socket`, etc.)
- Whether the tool's stated description matches its actual code behaviour (LLM cross-check)
- Whether the tool's intended file/network targets are within whitelisted scopes
- Whether similar tools have triggered safety audit failures in the past (`tool_performance` table)
- The tool's mandate compliance score from `MandateEnforcer.check_action()`

**Permission tiers to map to:**

| Tier | Allowed imports | Sandbox restrictions |
|---|---|---|
| `pure-compute` | stdlib math, string, json, datetime only | Current restrictions |
| `filesystem-read` | `pathlib`, `os.path`, `open()` read-only | Paths under project root only |
| `filesystem-write` | `open()` write | `tools/` subtree only |
| `shell-execution` | `subprocess` | Command whitelist; mandate check required |

**Work needed:** Define the scoring function: inputs → float 0.0–1.0 → tier mapping.
This can be rule-based, LLM-assisted, or both.

---

## §3 — Income execution: domain and platform selection *(blocks M6)*

`IncomeSeeker` identifies income opportunities but the system cannot act on them. Income
execution requires integrating with at least one external platform. This is a product
decision before it is a technical one.

**Question:** Which domain and platform does AAIA target first for income execution?

**Candidates to evaluate** (against current capabilities: LLM calls, tool creation, web fetch):

| Domain | Platform | Min capability needed |
|---|---|---|
| Content generation | Client API / direct delivery | HTTP POST, structured output |
| Data processing service | Custom endpoint / Gumroad | File I/O, web server exposure |
| Automated reporting | Email delivery / webhook | SMTP or webhook client |
| Freelance task matching | Upwork / Fiverr API | OAuth, task parsing, response formatting |

**Work needed:** Select one domain. Define the minimum viable execution capability
(what the system must be able to do to complete one paid task). Scope becomes M6 actionables.

---

## §4 — Security and threat-defense module *(Tier 1 gap)*

`SelfDiagnosis` monitors module health. There is no active monitoring for host-level threats,
anomalous behaviour, or integrity violations.

**Question:** Where does threat defense live — in AAIA code or in the NixOS host?

**Options:**
- **Option A — Build a `ThreatMonitor` module:** log anomaly scoring on `action_log` patterns,
  detect unexpected processes via `psutil`, file integrity hashing for core modules.
  Runs as a scheduler task every 15 min.
- **Option B — Defer to NixOS host:** configure `auditd` or `fail2ban` at the OS layer.
  Expose their state to `EnvironmentExplorer` so AAIA can read threat status without owning it.
- **Option C — Hybrid:** NixOS handles OS-level threats; AAIA adds a lightweight behavioural
  anomaly detector on its own `action_log` (unexpected action patterns, cost spikes).

---

## §5 — Specialist worker model roster *(charter gap)*

`ModelRouter` selects from 5 providers based on cost and capability tier. There is no
assignment of preferred models per task domain. All task types route through the same pool.

**Question:** Should a `task_type → preferred_model` mapping be added to `LLMConfig`?

**Considerations:**
- Adding the mapping allows, e.g., `coding` tasks to always prefer a code-specialist model
  and `reflection` tasks to prefer a larger reasoning model, subject to budget.
- This conflicts with `MarginalAnalyzer`'s cost-optimisation logic — specialist assignment
  is a capability preference, cost is a separate constraint. They can coexist if the
  specialist preference is treated as a soft hint, not a hard override.
- Requires defining and maintaining a model roster per provider.

---

## §6 — Tool sandbox resource limits on non-Linux hosts *(minor)*

`_set_resource_limits()` in `forge.py` uses `resource.setrlimit` which silently fails on
Windows and non-Linux systems. The tool sandbox then runs without memory or CPU guardrails.

**Question:** Is this acceptable given AAIA targets NixOS exclusively, or should it be
hardened?

**Options:**
- Add an explicit `platform.system()` check and log a `WARNING` when limits cannot be applied.
  No functional change; improves observability.
- Evaluate whether NixOS `cgroups` (via systemd slice) already enforces equivalent limits
  at the OS level, making the Python-level call redundant.

---

## §7 — Decision rationale: how and where is it permanently recorded?

Every time the WIP workflow runs, `WIP.md` is cleaned up and all `DECISION MADE` blocks
are removed. The rationale behind each decision — why ChromaDB over FTS5, why NOSTR over
email, why Option A over B — is permanently lost. The AI agent has no durable record of
why it is the way it is, which risks re-debating settled questions in future workflow runs.

**Question:** What is the format and home for a permanent decision log?

**Options:**
- **Option A — `docs/DECISIONS_LOG.md` append-only file:** each workflow run appends new
  decisions in a standard block (decision title, options considered, rationale, date).
  Chronological, never edited, always growing.
- **Option B — Decision block embedded in each roadmap file:** the rationale for each
  actionable lives in the same roadmap file that contains the actionable spec. Keeps
  context co-located with the plan.
- **Option C — Separate file per batch:** `docs/WIP_N_DECISIONS.md` alongside each
  `WIP_N_MILESTONES_ROADMAP.md`. Keeps batches self-contained.

**Work needed:** Choose a format and update `copilot-instructions-wip-workflow.md` to
add a step between Steps 5 and 6 that writes to the decision log before WIP.md is cleaned.

---

## §8 — Implementation status tracking: how do we know what has been built?

Once a roadmap file is created it is immutable. There is currently no way to record that
A1 is complete, A3 is in progress, or A8 is still blocked. A developer or the AI agent
picking up work has no live view of execution state.

**Question:** Where and how is implementation progress tracked?

**Options:**
- **Option A — `docs/NOW.md` single-file current state:** one file, always rewritten,
  answers three questions: what batch is active, what actionable is next, what is blocked.
  Simple and fast to check; no history.
- **Option B — Status fields inside each roadmap file:** add a `status` column
  (`pending / in-progress / done / blocked`) to each milestone table. The roadmap file
  is the tracker. Breaks the immutability rule but keeps everything in one place.
- **Option C — Companion `docs/WIP_N_MILESTONES_STATUS.md` per batch:** a separate
  file per roadmap that tracks status without mutating the original plan. Immutability
  preserved; requires an extra file per batch.

**Work needed:** Choose an approach. Define who updates it (the AI agent after each
implementation step, or the master manually) and add the update trigger to the
implementation workflow instructions.

---

## §9 — Post-batch retrospective: what do we capture when a batch is complete?

When all actionables in a roadmap batch are done, nothing currently happens. There is no
step to record what was learned, whether estimates were accurate, what deviated from spec,
or what new questions emerged during implementation. This breaks the feedback loop that
should make each batch better than the last.

**Question:** What format and trigger defines a retrospective?

**Options:**
- **Option A — `docs/WIP_N_RETROSPECTIVE.md` per batch:** written by the AI agent when
  all items in batch N are marked complete. Fixed sections: delivered vs. planned, effort
  accuracy, deviations from spec, new WIP items discovered, lessons for future batches.
- **Option B — Retrospective section appended to the roadmap file:** breaks immutability
  but keeps the full story of a batch in one document.
- **Option C — Lessons fed directly into `WIP.md`:** no retrospective document; any
  new questions found during implementation are simply added to WIP.md as new §items
  and processed in the next workflow run.

**Work needed:** Choose a format. Define the trigger condition (who decides a batch is
complete) and add the retrospective step to the post-implementation workflow instructions.

---

## §10 — Implementation workflow: how should the agent implement an actionable?

We have detailed planning instructions (`copilot-instructions-wip-workflow.md`) but no
instructions for the implementation phase itself. When the agent picks up A1 or A3, it
has no workflow to follow — no standard for how to read an actionable spec, apply the
change, verify it, and mark it done.

**Question:** Should a `.github/copilot-instructions-implementation.md` be created?

**Content to cover:**
- How to read and parse an actionable spec from a roadmap file.
- Pre-change checklist: read the target file before editing, check for existing tests,
  verify DI registration requirements, confirm `PromptManager` compliance if LLM is involved.
- Change application: use `replace_string_in_file`, run `py_compile` after each file,
  register new modules in `setup.py`.
- Post-change verification: run `get_errors`, check against acceptance criteria, update
  status tracker.
- How to handle a blocked actionable: do not attempt, log the blocker, move to next item.

**Work needed:** Decide whether this is a single instruction file or split by concern
(e.g. separate file for "adding a new module" vs. "fixing an existing method"). Then
create the file(s) and register them in `copilot-instructions.md`.

---

## §11 — Post-implementation workflow: what does the agent do when a batch is complete?

When all actionables in a batch are marked done, several downstream tasks are currently
unowned: updating `architecture_overview.md` to reflect what was built, checking
`symbiotic_partner_charter.md` for new contradictions, writing the retrospective, and
priming `WIP.md` with any new questions that emerged during implementation.

Without a defined workflow for this phase, these tasks are skipped and the documentation
ecosystem drifts away from the actual system state.

**Question:** Should a `.github/copilot-instructions-post-implementation.md` be created?

**Steps it should define:**
1. Check all actionables in the batch are marked done (or explicitly deferred/blocked).
2. Update `docs/architecture_overview.md` — add new modules, correct any changed behaviour.
3. Check `docs/symbiotic_partner_charter.md` for contradictions introduced by the batch.
4. Write the retrospective (per §9 decision).
5. Scan implementation notes for new questions; add them to `docs/WIP.md` as new §items.
6. Update `docs/NOW.md` (or equivalent status tracker) to point to the next active batch.
7. Confirm `copilot-instructions.md` references any new instruction files created in the batch.

**Work needed:** Confirm the steps above, decide whether this is one file or merged into
the existing WIP workflow as a second trigger condition, and create the file.

---

## §12 — Missing steps in the existing WIP workflow

Three gaps were identified in `copilot-instructions-wip-workflow.md` that exist regardless
of the decisions made in §7–§11:

**Gap 1 — No status check before Step 1:**
The workflow has no step to check which actionables from previous batches have been
completed, which are in progress, and which are blocked. Without this, a new roadmap
batch could plan work that was already done or re-plan a blocked item without
acknowledging its blocker.

**Gap 2 — No decision logging before WIP.md cleanup:**
Between Steps 5 and 6, decisions are classified and actionables are written — but nothing
records the rationale before WIP.md is cleaned. Once Step 6 runs, the reasoning is gone.

**Gap 3 — No doc consistency check after roadmap creation:**
After Step 8, if any new decision affects `architecture_overview.md` or
`symbiotic_partner_charter.md`, there is no prompt to update those documents. We did
this manually in our session but the workflow does not enforce it.

**Question:** Should these three gaps be fixed by updating the existing workflow file,
or by creating a pre-flight checklist document that the agent reads before starting?

**Work needed:** Once §7–§11 decisions are made (they define what the status check in
Gap 1 reads, and what the decision log in Gap 2 writes), update
`copilot-instructions-wip-workflow.md` to add Step 0, the decision logging step, and
the doc consistency step.

---

## §13 — The WIP workflow as an internal AAIA capability

### The idea

The WIP workflow currently exists as an external instruction file executed by a human
operator or a Copilot session. Every step in it — read the codebase, identify gaps,
classify items, present options, generate a plan, write files, verify consistency — maps
directly onto capabilities that AAIA either already has or is being built to have. If AAIA
is a truly autonomous self-improving agent, running its own development planning cycle
should be one of its native behaviours, not an external process.

In this model, AAIA reads its own `WIP.md`, audits its own codebase, reasons about
gaps and decisions, consults the master only where the Prime Mandates require it, writes
its own roadmap files, and then implements approved actionables via the git-branch
evolution pipeline — closing the loop entirely.

---

### Alignment with the charter and directives

This is not a new idea imposed from outside. The charter and directives already describe
exactly this:

- **Tier 3 — Recursive Self-Improvement:** *"Analyze your own performance logs. Identify
  bottlenecks, failed strategies, and inefficient tool usage. Formulate and test hypotheses
  for improvement."* The WIP workflow IS this, formalised into a repeatable cycle.

- **Tier 4 — Proactive Partnership:** *"Proactively identify opportunities and risks for
  your master before they are even asked."* The gap-identification and option-presentation
  steps of the WIP workflow are the operational implementation of proactive partnership.

- **Charter §5 — Git-Branch Self-Evolution:** *"You improve your own existing modules by
  proposing changes on isolated git feature branches."* The WIP workflow produces the
  roadmap that feeds exactly this pipeline.

- **Core Directive — Veracity & Transparent Reasoning:** Every decision made autonomously
  must be logged with full rationale (§7). This is already a mandate requirement, not a
  new constraint.

Internalising the WIP workflow is therefore the natural completion of the charter's intent,
not an extension of it.

---

### How existing modules already map to workflow steps

| WIP workflow step | Existing AAIA module | Gap |
|---|---|---|
| Step 1 — Inventory (read own files) | `EnvironmentExplorer`, `NixAwareSelfModification.analyze_own_code()` | No file-read abstraction for planning docs |
| Step 2 — Codebase audit | `SelfDiagnosis`, `CapabilityDiscovery`, `MetaCognition` | No structured gap-to-WIP-item mapping |
| Step 3 — Classify items (A/B/C/D) | `MandateEnforcer.check_action()`, LLM reasoning via `ModelRouter` | No classification module |
| Step 4 — Present Class C to master | `DialogueManager.structured_argument()`, `ProactiveAnalyzer` | Presentation exists; NOSTR push (A10) needed for async response |
| Step 5 — Generate actionables | `EvolutionManager._generate_tasks_for_goal()` | Tasks generated but not in roadmap-file format |
| Step 6 — Rewrite WIP.md | `NixAwareSelfModification` (A3 when done) | WIP.md is not currently a managed file |
| Step 7–8 — Create roadmap file | `EvolutionPipeline`, `EvolutionOrchestrator` | Plan exists in DB, not in structured roadmap files |
| Step 9 — Verify consistency | `SelfDiagnosis` | No cross-file consistency check |
| Step 10 — Notify master | `NostrNotifier` (A10 when done) | Not yet built |

The modules exist. What is missing is a **`WIPCycleManager`** that orchestrates them in
the correct sequence and writes the planning document outputs (`WIP.md`, roadmap files,
decisions log, status tracker).

---

### The decision autonomy boundary

The most critical design question is: which WIP items can AAIA decide for itself, and
which must the master answer?

The existing Prime Mandates already define this boundary precisely:

| Classification | Decision type | Who decides | Example |
|---|---|---|---|
| Class A — autonomous | Purely technical, low mandate risk, reversible, low cost | AAIA | Platform check for `setrlimit` (§6), tier assignments for scheduler (A2) |
| Class B — autonomous (partial) | Technical approach decided; sub-detail within system expertise | AAIA | Risk-scoring algorithm design (§2) |
| Class C — master required | Affects purpose, master's goals, economic strategy, or triggers mandate review | Master via dialogue | Income domain selection (§3), security architecture (§4) |
| Class D — lookup | Already settled in a previous decision | AAIA | Cross-reference DECISIONS_LOG.md |

`MandateEnforcer.check_action()` combined with `DialogueManager.check_urgency()` and
`is_significant_action()` already implement exactly this triage. The WIP classification
logic (A/B/C/D) is structurally the same as the mandate check — the WIP cycle can reuse
it directly.

---

### Recommendation

Implement this as **Milestone 7 (Batch 2)** — a single new module `WIPCycleManager` —
after the following prerequisites from Batch 1 are complete:

**Hard dependencies (the cycle cannot run without these):**
- **A3** — git-branch evolution, so approved actionables can be implemented autonomously.
- **A10** — NOSTR, so Class C items can be presented to the master asynchronously and
  responses received without requiring a live session.
- **A1** — safety lock-out wiring, so catastrophic autonomous decisions trigger a lockout.

**Soft dependencies (the cycle runs better with these):**
- **A4 + A5** — ChromaDB + ContextBuilder, so the LLM reasoning in Steps 2–3 has
  access to semantic memory of past decisions and system history.
- **§7** — DECISIONS_LOG format decided, so the classification step can check past
  decisions before re-debating settled questions.
- **§8** — Status tracking decided, so Step 0 can read actual completion state.
- **§9–§12** — Retrospective and post-implementation workflow decided, so the full cycle
  is closed.

The module itself should be registered in the DI container and scheduled as a low-frequency
task (weekly or on explicit master trigger). Its core loop:

```
WIPCycleManager.run()
  │
  ├─ Read WIP.md and all roadmap files (inventory)
  ├─ Audit codebase for new gaps since last run (SelfDiagnosis, CapabilityDiscovery)
  ├─ Classify each WIP item via MandateEnforcer + LLM (A/B/C/D)
  ├─ For Class A/B: resolve autonomously, append to DECISIONS_LOG
  ├─ For Class C: publish to master via NOSTR + DialogueManager; await response
  ├─ Once all Class C resolved: generate roadmap file via EvolutionOrchestrator
  ├─ Rewrite WIP.md (pending items only) via git branch
  └─ Notify master of completed cycle via NOSTR summary
```

**Work needed:** Decisions §7–§12 must be resolved first to define the inputs and outputs
of each step. Once those are decided, `WIPCycleManager` can be specified as a concrete
actionable in Batch 2 with full file and method detail.
