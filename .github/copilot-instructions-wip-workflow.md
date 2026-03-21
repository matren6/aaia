# WIP → Roadmap Workflow Instructions

This file defines the **repeatable workflow** an AI agent must follow whenever the master
adds new items to `docs/WIP.md`. The workflow converts open questions and ideas into
decisions and a numbered, self-contained milestone roadmap file.

Run this workflow in full every time it is triggered. Do not skip steps.

---

## Trigger Condition

Run this workflow when:
- The master adds new content to `docs/WIP.md` and asks for the workflow to be run, **or**
- `docs/WIP.md` contains items with no `DECISION MADE` block and no corresponding entry
  in any existing `docs/WIP_*_MILESTONES_ROADMAP.md`.

---

## Files Involved

| File | Role | Mutability |
|---|---|---|
| `docs/WIP.md` | Open questions only — no actionables, no decisions | Rewritten each run |
| `docs/WIP_N_MILESTONES_ROADMAP.md` | Complete delivery plan for one batch: ordering + full implementation detail | Created once per run, never edited afterwards |
| `docs/architecture_overview.md` | System structure reference | Read-only |
| `docs/core_directives.md` | Ethical and operational mandates | Read-only |
| `docs/symbiotic_partner_charter.md` | System charter | Read-only |

> **There is no separate actionables file.** Each roadmap file is fully self-contained:
> it holds both the milestone planning structure and the complete implementation spec
> (files to change, methods, acceptance criteria) for every item in that batch.

---

## Step 1 — Inventory

Read the following files in order before doing anything else:

1. `docs/WIP.md` — identify every item present (new ideas, pending §items, partial decisions).
2. All existing `docs/WIP_*_MILESTONES_ROADMAP.md` files:
   - Record the **highest roadmap number** (e.g. 2). The new file this run will be `WIP_3_MILESTONES_ROADMAP.md`.
   - Record the **highest actionable ID** across all roadmap files (e.g. A10). New actionables
     this run start at A11.
3. `docs/architecture_overview.md` — understand current module structure.

Do not proceed until all reads are complete.

---

## Step 2 — Codebase Audit (new items only)

For every item in `docs/WIP.md` that is **newly added since the last run**, verify the claim
against the actual codebase before classifying it.

Use these tools:
- `code_search` — find relevant code by concept.
- `get_file` — read specific modules or config files.
- `get_symbols_by_name` — locate class/function definitions.

**Goal:** Confirm whether the problem is real, which files are affected, and whether a
partial implementation already exists. Record findings per item.

Skip auditing items that were already present in the previous version of `WIP.md`.

---

## Step 3 — Classify Each Item

Assign every item in `docs/WIP.md` exactly one classification:

### Class A — DECIDED
The master has provided a clear answer (look for an `ANSWER:` block or explicit statement).
Implementation can begin immediately.

→ Produce actionable items (Step 5). Remove from `WIP.md`.

### Class B — PARTIALLY DECIDED
An approach is chosen but a required sub-detail is still missing. Implementation is
partially unblocked.

→ Produce actionables for the decided part. Keep the unresolved sub-question in `WIP.md`
with a `⚠️ DECISION PARTIALLY MADE` block cross-referencing the blocking detail.

### Class C — PENDING
No answer given yet.

→ Present 2–3 concrete options (Step 4). Keep in `WIP.md` unchanged until master responds.

### Class D — RESOLVED BY DEPENDENCY
Already fully covered by a previous roadmap's actionable.

→ Add a one-line cross-reference note and remove from the main body of `WIP.md`.

---

## Step 4 — Present Options for Class C Items

For every Class C item, output to the master:

```
### [Item title]
**Context:** [1–2 sentence summary from codebase audit]

**Option A — [Name]:** [Description]. Pros: [...]. Cons: [...].
**Option B — [Name]:** [Description]. Pros: [...]. Cons: [...].
**Option C — [Name] (if applicable):** [Description].

**Recommendation:** Option [X] because [reason grounded in audit findings].
```

After presenting all Class C options, **wait for the master to answer** before continuing
to Steps 5–9. Do not write actionables or the roadmap file for Class C items until answers
are received.

---

## Step 5 — Define New Actionables

For every Class A and decided part of Class B, define one or more actionables.

### ID numbering
- Continue from the highest A-ID found across all existing roadmap files.
- If no roadmap files exist, start at A1.
- IDs are **globally sequential across all batches** — never reuse a number.

### Required format for each actionable

```markdown
### A[N] — [Short descriptive title]

[1–2 sentence description of what needs to be built and why.]

**Files to change / create:**
- `path/to/file.py` — `method_name()`: [specific change].
- (Create) `path/to/new_module.py` — [purpose and key methods].

**Acceptance criteria:**
- [Concrete, testable outcome 1.]
- [Concrete, testable outcome 2.]
- [Existing tests pass / no regression.]
```

Rules:
- Every actionable must reference **specific file paths and method names**.
- Never write "update the module" without specifying which method and what change.
- If blocked by a pending §item: add `**Status: BLOCKED — waiting for WIP.md §N.**`
- If it depends on another actionable: add `**Depends on:** A[N] must be complete first.`

---

## Step 6 — Update `docs/WIP.md`

Rewrite `WIP.md` so it contains **only** undecided (Class C) and partially decided (Class B
sub-details) items. Apply these rules:

1. **Class A** — remove entirely (covered by the new roadmap).
2. **Class B** — keep only the unresolved sub-question with a `⚠️ DECISION PARTIALLY MADE`
   block stating what was decided, which A-ID it produced, and what sub-detail remains.
3. **Class C** — keep unchanged; append `🔲 OPTIONS PRESENTED` block if options were shown.
4. **Class D** — replace with a one-line reference note or remove.

### Required block format — DECISION PARTIALLY MADE (Class B)

```markdown
> ### ⚠️ DECISION PARTIALLY MADE — Sub-detail still required
> **Decided:** [What was chosen].
> **Produces:** Actionable A[N] in `WIP_[N]_MILESTONES_ROADMAP.md`.
> **Remaining open:** [Exact sub-question that must be answered].
```

### Required block format — OPTIONS PRESENTED (Class C)

```markdown
> ### 🔲 OPTIONS PRESENTED — Awaiting master decision
> Options A/B/C presented in workflow run [date].
```

**Verify before proceeding:**
- `WIP.md` contains zero Class A items.
- Every remaining item has a clear "question" or "work needed" statement.
- The file header references the new roadmap file by name.

---

## Step 7 — Determine Roadmap File Number

1. List all files matching `docs/WIP_*_MILESTONES_ROADMAP.md`.
2. Extract numbers (e.g. `WIP_1_` → 1, `WIP_2_` → 2).
3. New file = `docs/WIP_[highest + 1]_MILESTONES_ROADMAP.md`.
4. If no roadmap files exist, create `docs/WIP_1_MILESTONES_ROADMAP.md`.

---

## Step 8 — Create the Roadmap File

Group the **new actionables from this run only** into milestones. Do not re-include
actionables from previous roadmap batches.

### Required file header

```markdown
# Implementation Roadmap — Batch [N]
> Self-contained delivery plan for actionables A[first]–A[last].
> Each milestone is independently deployable and testable.
> For open questions that block some items here, see `docs/WIP.md`.
```

### Milestone grouping rules (priority order)

1. **Critical bugs and safety fixes first** — broken safety mechanisms go in Milestone 1.
2. **Dependency order** — if A-N depends on A-M they must be in the same or later milestone.
3. **Thematic coherence** — items touching the same subsystem belong in the same milestone.
4. **Blocked items last** — any item blocked by a pending WIP §item goes in the final
   milestone, clearly marked `⛔ BLOCKED`.

### Required milestone format

```markdown
## Milestone [N] — [Theme Name]
> **Goal:** [One sentence describing what this milestone achieves.]

| # | Actionable | Effort | Depends On |
|---|---|---|---|
| A[N] | [Title] | [XS/S/M/L] | [— or A-N or M-N] |

**Delivery sequence:**
1. [First sub-task and why it comes first.]
2. [Next sub-task.]

### A[N] — [Title]
[Full actionable detail: description, files to change, acceptance criteria — same format as Step 5]

---

**Milestone [N] — Definition of done:**
- [Verifiable outcome 1.]
- [Verifiable outcome 2.]
```

### Required summary view (end of roadmap file)

```markdown
## Summary View

[ASCII dependency tree showing milestone order, blocked items, and inter-milestone links]

---

## Effort Legend

| Size | Approximate scope |
|---|---|
| XS | < 20 lines, 1 file |
| S | < 100 lines, 1–2 files |
| M | < 300 lines, 2–4 files + tests |
| L | > 300 lines or architectural change |
```

---

## Step 9 — Verify Consistency

Run all checks before finishing:

| Check | Pass condition |
|---|---|
| `WIP.md` is clean | No Class A items remain. Every item has a question or pending block. |
| Roadmap is self-contained | Every A-ID has description + files + acceptance criteria inline. |
| IDs are sequential | New A-IDs continue from the highest ID in all previous roadmap files. |
| Roadmap covers all new A-IDs | Every new actionable appears in exactly one milestone. |
| Blocked items are explicit | Every blocked actionable names the `WIP.md §` item blocking it. |
| Roadmap number is correct | File is `WIP_[N]_MILESTONES_ROADMAP.md` with N = previous highest + 1. |
| No previous actionables duplicated | New roadmap contains only actionables from this run. |

If any check fails, fix it before completing the workflow.

---

## Step 10 — Output Summary to Master

```
## Workflow Complete — Batch [N]

**Decisions processed:** [count] Class A, [count] Class B
**New actionables created:** A[first]–A[last] ([count] total)
**New roadmap file:** docs/WIP_[N]_MILESTONES_ROADMAP.md ([M] milestones)
**WIP.md remaining items:** [count] pending — [list titles]
**Blocked actionables:** [list A-IDs and what blocks them, or "none"]
```

---

## Invariants (Never Violate)

1. **`WIP.md` contains only undecided questions.** No actionables, no completed decisions.
2. **Roadmap files are immutable once created.** Never edit a previously created roadmap file.
3. **One roadmap file per workflow run.** Do not split into multiple files in a single run.
4. **Actionable IDs are globally unique and sequential.** Check all previous roadmap files.
5. **Every actionable names specific files and methods.** No vague "update the module" entries.
6. **Every roadmap file is fully self-contained.** No cross-referencing a separate actionables file.
7. **Blocked items are always traced to their blocker.** State the exact `WIP.md §` item.
8. **Do not invent decisions.** Class C items stay pending until the master answers.

---

## Quick-Reference Checklist

```
[ ] Step 1  — Read WIP.md, all existing roadmap files, architecture_overview.md
[ ] Step 2  — Audit new items against codebase
[ ] Step 3  — Classify all items (A/B/C/D)
[ ] Step 4  — Present options for Class C items; wait for master answers
[ ] Step 5  — Define new actionables (continuing A-ID sequence)
[ ] Step 6  — Rewrite WIP.md (pending items only)
[ ] Step 7  — Determine next roadmap number N
[ ] Step 8  — Create WIP_N_MILESTONES_ROADMAP.md (self-contained: plan + full detail)
[ ] Step 9  — Verify consistency (all 7 checks)
[ ] Step 10 — Output summary to master
```

---

## Trigger Condition

Run this workflow when:
- The master adds new content to `docs/WIP.md` and asks for the workflow to be run, **or**
- `docs/WIP.md` contains items with no `DECISION MADE` block and no entry in
  `docs/WIP_ACTIONABLES_PENDING.md`.

---

## Files Involved

| File | Role | Mutability |
|---|---|---|
| `docs/WIP.md` | Open questions only — no actionables, no decisions | Rewritten each run |
| `docs/WIP_ACTIONABLES_PENDING.md` | Cumulative list of all ready-to-implement items | Append-only |
| `docs/WIP_N_MILESTONES_ROADMAP.md` | Ordered delivery plan for one batch of actionables | Created once, never edited |
| `docs/architecture_overview.md` | System structure reference | Read-only |
| `docs/core_directives.md` | Ethical and operational mandates | Read-only |
| `docs/symbiotic_partner_charter.md` | System charter | Read-only |

---

## Step 1 — Inventory

Read the following files in order before doing anything else:

1. `docs/WIP.md` — identify every item present (new ideas, pending §items, partial decisions).
2. `docs/WIP_ACTIONABLES_PENDING.md` — record the **highest existing actionable ID** (e.g. A10).
   New actionables in this run will be numbered A11, A12, etc.
3. All existing `docs/WIP_*_MILESTONES_ROADMAP.md` files — record the **highest roadmap number**
   (e.g. 1). The new roadmap file this run will be `WIP_2_MILESTONES_ROADMAP.md`.
4. `docs/architecture_overview.md` — understand current module structure.

Do not proceed until all four reads are complete.

---

## Step 2 — Codebase Audit (new items only)

For every item in `docs/WIP.md` that was **not present in the previous run** (i.e. newly added
by the master), verify the claim against the actual codebase before classifying it.

Use these tools:
- `code_search` — find relevant code by concept.
- `get_file` — read specific modules or config files.
- `get_symbols_by_name` — locate class/function definitions.

**Goal of the audit:** confirm whether the problem described is real, which files are affected,
and whether a fix already exists but is wired incorrectly (partial implementation vs. missing
entirely). Record findings per item.

Skip auditing items that were already present in the previous version of `WIP.md` and have
not changed.

---

## Step 3 — Classify Each Item

Assign every item in `docs/WIP.md` exactly one classification:

### Class A — DECIDED
The master has provided a clear answer in `WIP.md` (look for an `ANSWER:` block or explicit
statement). The decision is unambiguous and implementation can begin.

→ Action: produce one or more actionable items (Step 5). Remove from `WIP.md`.

### Class B — PARTIALLY DECIDED
An approach is chosen but a required sub-detail is still missing (e.g. "we will use
ChromaDB but the schema is undefined"). Implementation is partially unblocked.

→ Action: produce actionables for the decided part. Keep the unresolved sub-question in
`WIP.md` with a `⚠️ DECISION PARTIALLY MADE` block. Cross-reference the blocking sub-item.

### Class C — PENDING
No answer has been given. The master has not yet chosen an approach.

→ Action: present 2–3 concrete options in the workflow output (Step 4). Keep item in
`WIP.md` unchanged until the master responds.

### Class D — RESOLVED BY DEPENDENCY
The item is already fully covered by a previous actionable or decision (e.g. it was added
to WIP.md but a prior roadmap already handles it).

→ Action: add a brief note in `WIP.md` pointing to the covering actionable/roadmap.
Remove from the main body of `WIP.md`.

---

## Step 4 — Present Options for Class C Items

For every Class C item, output to the master:

```
### [Item title]
**Context:** [1–2 sentence summary of the problem from codebase audit]

**Option A — [Name]:** [Description]. Pros: [...]. Cons: [...].
**Option B — [Name]:** [Description]. Pros: [...]. Cons: [...].
**Option C — [Name] (if applicable):** [Description].

**Recommendation:** Option [X] because [reason grounded in audit findings].
```

After presenting all Class C options, pause and wait for the master to provide answers
before continuing to Steps 5–9. Do not write actionables or roadmap files for Class C items
until answers are received.

---

## Step 5 — Write New Actionables

For every Class A and Class B (decided part) item, create one or more actionable entries.

### Actionable ID numbering
- Continue from the highest existing ID in `docs/WIP_ACTIONABLES_PENDING.md`.
- If the file is empty or does not exist, start at A1.
- IDs are **globally sequential** across all runs — never reuse a number.

### Required format for each actionable entry

```markdown
## A[N] — [Short descriptive title]
**Source:** [WIP item reference] | **Milestone:** M[X] (see roadmap)

[1–2 sentence description of what needs to be built and why.]

**Files to change:**
- `path/to/file.py` — [specific method or section]: [what to add/change/remove].
- `path/to/other.py` — [specific change].
- (Create) `path/to/new_module.py` — [purpose and key methods].

**Acceptance criteria:**
- [Concrete, testable outcome 1.]
- [Concrete, testable outcome 2.]
- [Existing tests pass / no regression.]
```

Rules:
- Every actionable must reference **specific file paths and method names** from the codebase.
- Never write "update the module" — always specify which method, what change, and why.
- If an actionable is blocked by a pending §item, state it explicitly:
  `**Status: BLOCKED — waiting for WIP.md §N resolution.**`
- If an actionable depends on another actionable, state it:
  `**Depends on:** A[N] must be complete first.`

Append all new actionables to `docs/WIP_ACTIONABLES_PENDING.md`. Do not overwrite existing
entries.

---

## Step 6 — Update `docs/WIP.md`

Rewrite `docs/WIP.md` so it contains **only** Class C (pending) and Class B (unresolved
sub-detail) items. Apply these rules:

1. **Class A items** — remove entirely (they are now in `WIP_ACTIONABLES_PENDING.md`).
2. **Class B items** — keep the unresolved sub-question with a `⚠️ DECISION PARTIALLY MADE`
   block that states what was decided, what actionable was created, and what sub-detail
   remains open.
3. **Class C items** — keep unchanged, with options presented if this is the first time
   they appear in the workflow.
4. **Class D items** — replace with a one-line cross-reference note, or remove if trivial.

### Required format for a DECISION PARTIALLY MADE block (Class B)

```markdown
> ### ⚠️ DECISION PARTIALLY MADE — Sub-detail still required
> **Decided:** [What was chosen].
> **Produces:** Actionable [A-N] in `WIP_ACTIONABLES_PENDING.md`.
> **Remaining open:** [Exactly what sub-question must be answered before A-N is complete].
```

### Required format for a pending item (Class C, no decision yet)

Keep the original text. If options were presented in Step 4, append:

```markdown
> ### 🔲 OPTIONS PRESENTED — Awaiting master decision
> See workflow output dated [date]. Options A/B/C presented.
```

After rewriting, verify:
- `WIP.md` contains zero Class A items.
- Every remaining item has clear "work needed" or "question" text.
- The file header references `WIP_ACTIONABLES_PENDING.md` and the new roadmap file.

---

## Step 7 — Determine Roadmap File Number

1. List all existing files matching `docs/WIP_*_MILESTONES_ROADMAP.md`.
2. Extract the numbers (e.g. `WIP_1_` → 1, `WIP_2_` → 2).
3. The new file is `docs/WIP_[highest + 1]_MILESTONES_ROADMAP.md`.
4. If no roadmap files exist, create `docs/WIP_1_MILESTONES_ROADMAP.md`.

---

## Step 8 — Create the Roadmap File

Group the **new actionables from this run only** into milestones. Actionables from previous
runs that are already in an existing roadmap must NOT be re-added.

### Milestone grouping rules

Group by the following criteria, in priority order:
1. **Safety and critical bugs first** — any actionable fixing a broken safety mechanism or
   critical wiring bug belongs in Milestone 1 of the new roadmap.
2. **Dependency order** — if A-N depends on A-M, they must be in the same or later milestone.
3. **Thematic coherence** — items that touch the same subsystem (e.g. all memory/context items,
   all tool ecosystem items) belong in the same milestone.
4. **Blocked items last** — any actionable blocked by a pending WIP item goes in the final
   milestone, clearly marked as blocked.

### Required format for each milestone

```markdown
## Milestone [N] — [Theme Name]
> **Goal:** [One sentence describing what this milestone achieves for the system.]

| # | Actionable | Effort | Depends On |
|---|---|---|---|
| A[N] | [Title] | [XS/S/M/L] | [— or A-N] |

**Delivery sequence:**
1. [First task and why it must come first.]
2. [Next task.]
3. [Continue.]

**Definition of done:**
- [Verifiable outcome 1.]
- [Verifiable outcome 2.]
```

### Effort sizing guide

| Size | Lines of code | Files touched |
|---|---|---|
| XS | < 20 | 1 |
| S | < 100 | 1–2 |
| M | < 300 | 2–4 + tests |
| L | > 300 or architectural change | many |

### Required roadmap file structure

```markdown
# Milestone Roadmap — Batch [N]
> New actionables from [date]. Previous batches: WIP_1...[N-1]_MILESTONES_ROADMAP.md.
> Actionables: [A-first] through [A-last].

---

## Milestone 1 — [Theme]
[content]

---

## Milestone 2 — [Theme]
[content]

---

## Summary View

[ASCII dependency tree showing milestone order and blocked items]

---

## Effort Legend
[XS/S/M/L table]
```

---

## Step 9 — Verify Consistency

Before finishing, run these checks:

| Check | Pass condition |
|---|---|
| `WIP.md` is clean | No Class A items remain. Every item has a clear question or pending block. |
| Actionables are complete | Every new A-N entry has: source, milestone, files, acceptance criteria. |
| IDs are sequential | New A-IDs continue from the highest ID in the previous file version. |
| Roadmap covers all new A-IDs | Every new actionable appears in exactly one milestone. |
| Blocked items are explicit | Any actionable blocked by a `WIP.md §` item states the block clearly. |
| Roadmap number is correct | New file is `WIP_[N]_MILESTONES_ROADMAP.md` where N = previous highest + 1. |
| No previous actionables duplicated | The new roadmap contains only actionables created in this run. |

If any check fails, fix it before completing the workflow.

---

## Step 10 — Output Summary to Master

After all files are written, produce a brief summary:

```
## Workflow Complete — Batch [N]

**Decisions processed:** [count] Class A, [count] Class B
**New actionables created:** A[first] – A[last] ([count] total)
**New roadmap file:** docs/WIP_[N]_MILESTONES_ROADMAP.md ([M] milestones)
**WIP.md remaining items:** [count] pending ([list titles])
**Blocked actionables:** [list A-IDs and what blocks them, or "none"]
```

---

## Invariants (Never Violate)

These rules apply across every run of this workflow:

1. **`WIP.md` contains only undecided questions.** No actionables. No completed decisions.
2. **`WIP_ACTIONABLES_PENDING.md` is append-only.** Never delete or renumber existing entries.
3. **Roadmap files are immutable once created.** Never edit a previously created roadmap file.
4. **One roadmap file per workflow run.** Do not split into multiple files in a single run.
5. **Actionable IDs are globally unique and sequential.** Check the file before assigning.
6. **Every actionable names specific files and methods.** No vague "update the module" entries.
7. **Blocked items are always traced to their blocker.** State the exact `WIP.md §` item.
8. **Do not invent decisions.** Class C items stay pending until the master answers.

---

## Quick-Reference Checklist

Copy this checklist at the start of each run and tick items as they complete:

```
[ ] Step 1  — Read WIP.md, WIP_ACTIONABLES_PENDING.md, existing roadmaps, architecture_overview.md
[ ] Step 2  — Audit new items against codebase
[ ] Step 3  — Classify all items (A/B/C/D)
[ ] Step 4  — Present options for Class C items; wait for master answers
[ ] Step 5  — Write new actionables (continuing A-ID sequence)
[ ] Step 6  — Rewrite WIP.md (pending items only)
[ ] Step 7  — Determine next roadmap number N
[ ] Step 8  — Create WIP_N_MILESTONES_ROADMAP.md
[ ] Step 9  — Verify consistency (all 7 checks)
[ ] Step 10 — Output summary to master
```
