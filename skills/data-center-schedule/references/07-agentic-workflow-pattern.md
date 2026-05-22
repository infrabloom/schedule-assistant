# Agentic Workflow Pattern — 11 Agents for a DC Schedule Pipeline

This reference is for users who want to **operationalize the data-center-schedule workflow as a multi-agent system in Claude Code** (or any agent framework). It captures the 11 personas derived from the CB4 build and the data flow between them.

Use this **only** if standing up an agent system. For one-off Cowork conversations, the phased workflow in `01-phased-workflow.md` is sufficient.

---

## When to use multi-agent vs single-agent

| Situation | Use |
|---|---|
| One-off audit or fix | Single Cowork conversation, phased workflow |
| Building a new schedule end-to-end with checkpoints | Single Cowork conversation, phased workflow |
| Weekly refresh that runs on a schedule | Multi-agent (Orchestrator + OCE Refresh + MLP Refresh + Validator + Change Log) |
| Multiple parallel TeraWulf projects sharing the pattern | Multi-agent with a Catalog Builder per project |
| Want deterministic re-runs of the whole pipeline | Multi-agent with explicit state files between agents |

---

## The 11 agent personas

### 1. Source Extractor
**Inputs:** raw files in `inputs/` (XERs, MS-Project XMLs, MEL CSVs, PDFs, meeting notes)
**Outputs:** one `extraction-notes-{file}.md` per input under `outputs/extracts/`
**Responsibilities:**
- Read each input and produce a structured extraction memo
- Flag conflicts with higher-authority sources
- Apply the source-of-truth hierarchy (see SKILL.md)
- Apply OCE/3 calendar conversion when reading OCE XMLs
**Key methods:**
- `extract_xer(path)` -> dict of TASK/TASKPRED/PROJWBS/PROJECT/CALENDAR
- `extract_msproject_xml(path, oce_or_mlp)` -> activities + durations + actuals + logic
- `extract_mel_csv(path)` -> per-equipment rows with PO/delivery/received dates
- `extract_pdf(path, pages)` -> contractual definitions
**Guardrails:**
- Never copy OCE planned start/finish — derive from %/duration/actuals/logic position
- Never trust prior-GC schedule logic — actuals only
- Cite source file + row/page on every extracted fact

### 2. Catalog Builder
**Inputs:** all extraction notes; the locked WBS from the prior draft XER
**Outputs:**
- `activity-catalog.json` — every aggregate v3 task with: code, name, WBS, duration, calendar, status, %, predecessors
- `oce-mlp-crosswalk.xlsx` — OCE/MLP leaf -> v3 aggregate mapping (one-time investment)
**Responsibilities:**
- Define the per-DH activity catalog (DH4 first, then replicate)
- Build the crosswalk catalog so weekly refreshes become mechanical
- Resolve many-to-one aggregation rules per task family
- Capture parent-section context to disambiguate name collisions (e.g., OCE has "Install Cable Tray" 16x; each lives under a different parent section)
**Guardrails:**
- Never auto-match OCE -> v3 names blindly; CB4 attempt produced <5% high-confidence rate and several false positives (e.g., 83 UPS-corridor activities mis-mapped to ADMIN-MEP)
- Build the crosswalk row-by-row with explicit parent-section paths
- Document aggregation rule per row (earliest AS / latest AF / weighted % / etc.)

### 3. XER Builder
**Inputs:** activity catalog, predecessor logic, project metadata
**Outputs:** `[Project]-Schedule-v[N].xer`
**Responsibilities:**
- Generate the XER file with all required tables (PROJECT, CALENDAR, PROJWBS, TASK, TASKPRED, etc.)
- Apply conventions (base64-standard GUIDs, 08:00/17:00 times, OPC-safe constraint codes)
- Apply per-DH stagger via date offsets, NOT via cross-DH pred chains
- Set TASKPRED `aref` and `arls` to data date
**Guardrails:**
- Use `base64.b64encode`, NOT `base64.urlsafe_b64encode` (no `-` or `_` in GUIDs)
- Case-insensitive task_code uniqueness check before writing
- Never write `CS_MEO` or `CS_MSO` — only `CS_MEOA`/`CS_MEOB`/`CS_MSOA`
- Never write `00:00` timestamps

### 4. Validator
**Inputs:** an XER file
**Outputs:** validation report (pass/fail per check); blocks delivery if any fails
**Responsibilities:**
- Run `validate_xer.py` (all FAIL + WARN checks)
- Tarjan SCC cycle detection
- Orphan detection (every task has >=1 pred AND >=1 succ AND chain reaches a milestone)
- Duplicate detection (by code, by name, by fuzzy keyword)
**Key methods:**
- `validate(xer_path)` -> ValidationReport with per-check pass/fail + offending rows
- `detect_cycles(taskpred)` -> list of SCCs
- `walk_to_milestone(task)` -> path or None
**Guardrails:**
- Never suppress a failed check; fix the underlying issue
- Re-run after every retie operation (cycles love to appear)

### 5. OCE Refresh Agent
**Inputs:** latest OCE XML files, crosswalk catalog, current v3 XER
**Outputs:** updated XER + `OCE-refresh-changelog-{date}.md`
**Responsibilities:**
- Diff this week's OCE XML vs last week's (new activities, changed durations, new actuals, new logic)
- For each crosswalk row, pull current AS/AF/%/RD from all listed OCE leaves and aggregate (earliest AS, latest AF if all done, weighted % otherwise)
- Apply OCE/3 conversion to all durations
- Flag any case where derived dates differ from OCE's stated dates by >1 shift (OCE planned dates are unreliable)
**Guardrails:**
- Only apply mappings present in the crosswalk catalog — never auto-match
- If a new OCE activity has no crosswalk entry, log it and surface to user
- Conservative on actuals: only mark progress with documentary evidence

### 6. MLP Refresh Agent
**Inputs:** latest MLP XML, crosswalk, current XER
**Outputs:** updated XER + `MLP-refresh-changelog-{date}.md`
**Responsibilities:** same as OCE Refresh but for mechanical scope; no /3 conversion needed (MLP is already 8h/day)

### 7. MEL Reconciliation Agent
**Inputs:** latest MEL CSV, current XER's procurement WBS
**Outputs:** `MEL-reconciliation-{date}.md` with: deliveries-since-last-run, missing-from-schedule, missing-from-MEL, status-changes
**Responsibilities:**
- Reconcile every PROC activity against the MEL row
- Detect deliveries (received_date populated -> mark PROC as TK_Complete)
- Detect in-progress PROC (partial received qty -> TK_Active with appropriate %)
- Detect MEL rows with no PROC activity (gap in schedule scope)
- Detect PROC activities with no MEL row (gap in MEL or scope creep)
**Guardrails:**
- Flag MEL data quality issues (stale expected delivery dates, typos in PO dates) — don't silently propagate

### 8. Logic Auditor
**Inputs:** current XER
**Outputs:** `logic-audit-{date}.md` flagging suspicious ties
**Responsibilities:**
- Detect cross-DH FS chains (anti-pattern — see lesson #26)
- Detect FF ties on short-lead commodities (should be FS)
- Detect redundant predecessors (A->C when A->B->C already exists)
- Detect backward ties (B->A when A naturally precedes B by other paths)
- Detect HAC->MDB FF ties (these trades are parallel — see lesson #28)
- Detect first-fill->EFA ties when L2 PFC already gates EFA
**Guardrails:**
- Flag, don't auto-fix. Logic decisions need user approval.

### 9. Critical Path Analyzer
**Inputs:** current XER + a target milestone (EFA / FA / FR / RFS per DH)
**Outputs:** `critical-path-{milestone}-{date}.md`
**Responsibilities:**
- Backward-walk from milestone -> dump every activity on a path with float <=0
- Generate per-milestone narrative ("DH4 EFA critical path: ... 23 activities, longest chain X weeks")
- Identify the binding constraint (procurement? commissioning? construction?)
**Guardrails:**
- Use derived dates, not OCE planned dates
- Surface near-critical paths too (float <=5 days)

### 10. Change Log Generator
**Inputs:** prev XER + new XER + the changes applied by other agents this run
**Outputs:** `change-log-v{prev}-to-v{new}.md`
**Responsibilities:**
- Diff task counts, tie counts, milestone dates
- List every retired task, every new task, every duration change, every status change
- Categorize by source: OCE refresh / MLP refresh / MEL recon / logic fix / manual
**Guardrails:**
- One change log per material version bump. Never overwrite delivered XER.

### 11. Orchestrator
**Inputs:** trigger (manual or scheduled — e.g., weekly Monday 6am)
**Outputs:** complete refresh delta + emails / Slack to PM
**Responsibilities:**
- Sequence the agents: Source Extractor -> Catalog Builder (one-time) -> [OCE Refresh || MLP Refresh || MEL Recon] -> XER Builder -> Validator -> Logic Auditor -> Critical Path Analyzer -> Change Log
- Handle failures: if Validator fails, hold the XER; surface failure to user
- Maintain agent state files (last-run timestamps, last-applied OCE version, etc.)
- Drive checkpoint approvals (Phase 3, 4, 5 checkpoints) by pausing for user input
**Guardrails:**
- Never skip the Validator
- Never deliver a failed XER

---

## Data flow

```
inputs/
  *.xer, *.xml, *.csv, *.pdf
        |
        v
[Source Extractor]
        |
        v
outputs/extracts/*.md
        |
        v
[Catalog Builder]      <-- one-time per project
        |
        v
outputs/activity-catalog.json
outputs/oce-mlp-crosswalk.xlsx
        |
        v
[XER Builder]
        |
        v
outputs/[Project]-Schedule-v{N}.xer
        |
        v
[Validator]
        |
        +--(fail)--> hold + surface
        |
        +--(pass)--> deliver
        
Weekly refresh:
inputs/oce-week-N/*.xml  -->  [OCE Refresh]   -+
inputs/mlp-week-N/*.xml  -->  [MLP Refresh]   -+--> updated catalog deltas
inputs/mel-week-N.csv    -->  [MEL Recon]     -+
                                                |
                                                v
                                          [XER Builder]
                                                |
                                                v
                                          [Validator]
                                                |
                                                v
                                          [Logic Auditor]
                                                |
                                                v
                                          [Change Log]
                                                |
                                                v
                                  outputs/Schedule-v{N+1}.xer
                                  outputs/change-log-{date}.md
```

---

## Suggested Claude Code project layout

```
{Project}-agentic/
  .claude/
    settings.json
  agents/
    source-extractor.md
    catalog-builder.md
    xer-builder.md
    validator.md
    oce-refresh.md
    mlp-refresh.md
    mel-recon.md
    logic-auditor.md
    critical-path-analyzer.md
    change-log-generator.md
    orchestrator.md
  skills/
    data-center-schedule/  <-- this skill, installed
  scripts/
    parse_xer.py
    build_xer.py
    validate_xer.py
    duplicate_audit.py
    oce_xml_reader.py      <-- with /3 conversion
    mlp_xml_reader.py
    mel_csv_reader.py
    crosswalk_apply.py
  data/
    state/                 <-- agent state files (last-run, last-version)
    crosswalk.xlsx
  inputs/
    {sources}
  outputs/
    {generated}
  CLAUDE.md                <-- project-level instructions
```

---

## Each agent's prompt skeleton

Use this skeleton when writing each agent's markdown definition in `agents/`:

```markdown
---
name: {agent-name}
description: {one-line trigger description}
tools: Read, Write, Bash, ...   # subset of tools the agent needs
---

You are the {Agent Name} for the {Project} schedule pipeline.

## Your responsibility
{What this agent owns end-to-end}

## Your inputs
{Paths and formats}

## Your outputs
{Paths and formats}

## Method
{Step-by-step procedure}

## Guardrails
{Things you must NEVER do, lifted from this reference}

## Hand-off
{What you do when done — write a state file? Call orchestrator? Exit?}
```

Lift each agent's "Responsibilities", "Key methods", and "Guardrails" from the personas above.

---

## Build sequence in Claude Code

Recommended order to scaffold:

1. **Validator first** — smallest blast radius, highest leverage for everything else. Drop in `validate_xer.py`, write a thin agent that calls it.
2. **XER Builder** — once Validator works, you can iterate on the Builder confidently.
3. **Source Extractor** — needs the input format known; build one file type at a time (start with XER, then MS-Project XML, then MEL CSV, then PDF).
4. **Catalog Builder** — the one-time investment for crosswalk.
5. **OCE Refresh + MLP Refresh + MEL Recon** in parallel — they share patterns.
6. **Logic Auditor + Critical Path Analyzer** — both read-only; build last.
7. **Change Log Generator** — needs prev/new XER side-by-side; build after refresh agents.
8. **Orchestrator** — wires it all together.

---

## Anti-patterns and gotchas

1. **Don't let agents auto-fix logic.** They flag; user decides. Especially for cross-DH FS chains, redundant preds, backward ties — these require human judgment.

2. **Don't skip the Catalog Builder.** Without an explicit crosswalk, weekly refreshes will produce bad auto-matches that erode trust.

3. **Don't run OCE Refresh without /3 conversion.** Every OCE duration must be divided by 3. The Refresh agent must enforce this.

4. **Don't write `CS_MEO` or `CS_MSO`** — only the A/B variants. Validator catches this but Builder should refuse upfront.

5. **Don't use `urlsafe_b64encode` for GUIDs** — OPC rejects `-` and `_`. Use standard base64 alphabet.

6. **Don't carry forward retie residue.** After every retie operation, re-run cycle detection. Spurious back-edges to the previous F&F target are the most common new-cycle source.

7. **Don't tie HAC -> MDB FF.** They're parallel trades. Same for many "natural" sequences that look right but aren't — flag, don't assume.

8. **Don't tie procurement directly to EFA when L2 PFC is already a pred.** L2 PFC already requires procurement complete; the direct tie is redundant noise.

9. **Don't use cross-DH FS chains for crew flow.** Use date-offset stagger instead. CB4 had 285 such chains in v3.0 that all needed to come out.

10. **Don't run the Orchestrator without user approval at Phase 3, 4, 5 checkpoints.** These exist to catch logic errors before they cascade.

---

## How to reference this in a new project's instructions

Add this snippet to the project's `CLAUDE.md`:

```markdown
This project uses the data-center-schedule skill v1.1+. When standing up the
multi-agent workflow, read `references/07-agentic-workflow-pattern.md` for
the 11-agent persona pattern and data flow. Each agent should be defined
in `agents/{name}.md` using the prompt skeleton from that reference.

For one-off audits or single-conversation Cowork work, skip the multi-agent
setup and follow the phased workflow in `references/01-phased-workflow.md`.
```

