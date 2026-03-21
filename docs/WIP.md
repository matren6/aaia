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
