# Schedule Patterns — Reusable Structure for DC Schedules

Distilled patterns from the reference project and the 3 P6 reference templates. These are **portable** — the structure works across hyperscale DCs. Numbers (counts, durations, dates) are not — replace with project-specific values.

---

## 1. WBS Hierarchy (Level 1 — typical 7-8 branches)

```
[Project Code]
├── 01 Milestones
│   ├── Contractual (EFA-DHn, FA-DHn, MEC, TCO, PCO)
│   ├── Site (AFEED, BFEED, East Mains, West Mains)
│   └── Internal gates (M1-Mn, G1-Gn)
├── 02 Procurement
│   ├── By MEL keyplan zone (A, B, C ... R) OR
│   ├── By equipment family (MV / LV / UPS / Cooling / Racks / Misc)
│   └── Long-lead items flagged separately
├── 03 Site & Shell
│   ├── Sitework / Civil
│   ├── Foundation / Slab
│   ├── Shell / Envelope
│   └── Utilities tie-in (utility transformer, AFEED, BFEED)
├── 04 Construction (the big branch — per-Area)
│   ├── Area 1 (DH + Mech Room + Yards + Roof)
│   ├── Area 2 (DH + Mech Room + Yards + Roof)
│   ├── Area 3 (DH + Mech Room + Yards + Roof)
│   ├── Area 4 (DH + Mech Room + Yards + Roof)
│   └── Admin Building (if present)
├── 05 Final Inspections
│   ├── AHJ inspections (electrical, mech, fire, building)
│   ├── Pre-commissioning walkdowns
│   └── Final punchlist
├── 06 Commissioning
│   ├── L1 FAT (Factory Acceptance Test)
│   ├── L2 PFC (Pre-Functional Checks)
│   ├── L3 Functional (per-system: MV, LV, UPS, CDU, CHW, Gen, ATS)
│   ├── L4 IST (Integrated Systems Test)
│   └── L5 Load Bank IST
└── 07 Closeout
    ├── Documentation handover
    ├── Owner training
    └── Final acceptance
```

**Variations by project:**
- Some projects fold Site & Shell into Construction.
- Some projects break Commissioning into per-DH branches instead of by L-level.
- Admin/Office buildings may get their own L1 branch if scope is significant.

---

## 2. Per-DH Activity Catalog

Average activity counts per Area (single DH + Mech Room + 2 Yards + Roof). Use as a baseline — adjust by project.

### Mech Room (~28 activities)

| Activity ID pattern | Name | Typical duration | Notes |
|---|---|---|---|
| `CONS-DHn-MR-1000` | MR Mech Switchgear Set | 40h | Set in place, anchor |
| `CONS-DHn-MR-1010` | MR MV Transformer Set | 40h | |
| `CONS-DHn-MR-1020` | MR LV Transformer Set | 40h | |
| `CONS-DHn-MR-1030` | MR UPS Set (HUPS/MUPS/CUPS) | 80h | 3 UPS systems |
| `CONS-DHn-MR-1040` | MR Generator Set | 40h | |
| `CONS-DHn-MR-1050` | MR Switchgear Bus Connections | 40h | |
| `CONS-DHn-MR-1100-1180` | MR Cable Bus / Feeder Pull (MV, LV, UPS, Mech) | 80-160h each | Multiple sub-activities |
| `CONS-DHn-MR-1150` | MV Feeder Terminations | 40h | |
| `CONS-DHn-MR-1160-1180` | LV / UPS / Mech Feeder Terminations | 40h each | |
| `CONS-DHn-MR-1190` | Mech Room Ready (electrical) | 40h | Gate to L3-MV-EN |
| `CONS-DHn-MR-2000` | Chiller Plant Equipment Set | 80h | |
| `CONS-DHn-MR-2010-2020` | CHW Piping Install / Hydrotest | 80h each | |
| `CONS-DHn-MR-2030` | CHW System Pressure Test | 40h | (retired in the reference project v4.15) |
| `CONS-DHn-MR-5020` | Flush & Fill (cooling commissioning) | 80h | Cooling-commissioning scope |
| `CONS-DHn-MR-3000-3070` | Glycol System (ET / piping / charge / test) | 40-80h each | |
| `CONS-DHn-MR-4000-4010` | Specialty Piping / CDU Loop | 40h each | |
| `CONS-DHn-MR-7100` | Pump Alignment | 24h | Cooling-commissioning scope |
| `CONS-DHn-MR-7200` | Cooling Commissioning Test & Commission (pumps, valves, BAS PFC) | 80h | Cooling-commissioning scope, gates L3-CHW |

### Data Hall (~10 activities)

| Activity ID pattern | Name | Typical duration | Notes |
|---|---|---|---|
| `CONS-DHn-DH-1010` | CDU Set (vendor) | 80h | NOT mech contractor |
| `CONS-DHn-DH-1020` | DH Branch Power Install | 200h | Electrical contractor, often under-stated |
| `CONS-DHn-DH-1030` | DH Lighting / GP Power | 80h | |
| `CONS-DHn-DH-1040` | DH BMS / Sensors | 40h | |
| `CONS-DHn-DH-1050` | Containment Install | 80h | Hot/Cold aisle |
| `CONS-DHn-DH-1060` | CDU Power Connections | 40h | Electrical contractor → CDU vendor |
| `CONS-DHn-DH-1070` | Fan Wall Install (vendor) | 80h | NOT mech contractor |
| `CONS-DHn-DH-1080` | DH Electrical QA/QC | 40h | Electrical contractor, FF to FA |
| `CONS-DHn-DH-1090` | DH Ready for EFA | 40h | Punchlist before EFA |
| `CONS-DHn-DH-1100` | Rack Installation | 160h | Client/Owner, ~4 weeks |

### Yard (East + West, ~8 activities each)

| Activity ID pattern | Name | Typical duration | Notes |
|---|---|---|---|
| `CONS-DHn-YN-1000` | MV Switchgear Set | 80h | (YN=East / YS=West) |
| `CONS-DHn-YN-1010` | Cable Bus Install | 80h | |
| `CONS-DHn-YN-2000-2010` | Dry Cooler Set / Piping | 80h each | |
| `CONS-DHn-YN-3000` | Yard Lighting / Power | 40h | |
| `CONS-DHn-YN-4000-4010` | Yard Utility Power Complete | 40h | |
| `CONS-DHn-YN-9000` | Yard Final Walkdown | 24h | |

### Roof (~8 activities)

| Activity ID pattern | Name | Typical duration | Notes |
|---|---|---|---|
| `CONS-DHn-RF-1000` | RTU / Air Handler Set | 80h | If applicable |
| `CONS-DHn-RF-2000` | Roof Penetrations / Curbs | 40h | |
| `CONS-DHn-RF-3000` | Cooling Tower Set | 80h | If applicable |
| `CONS-DHn-RF-4000` | Roof Electrical Conduit / Wire | 40h | |
| `CONS-DHn-RF-5000` | Roof BMS / Sensors | 24h | |
| `CONS-DHn-RF-9000` | Roof Final Walkdown | 24h | |

### Commissioning (per-DH, ~12-15 activities)

| Activity ID pattern | Name | Typical duration | Notes |
|---|---|---|---|
| `CX-DHn-L3-MV-EN` | L3 MV Energization | 40h | Electrical contractor — verify vs trade duration |
| `CX-DHn-L3-LV-EN` | L3 LV Energization | 40h | Electrical contractor — verify vs trade duration |
| `CX-DHn-L3-UPS` | L3 UPS Functional | 80h | Electrical contractor / vendor |
| `CX-DHn-L3-GEN` | L3 Generator Functional | 80h | Electrical contractor / vendor |
| `CX-DHn-L3-CDU` | L3 CDU Functional | 80h | CDU vendor (test power OK?) |
| `CX-DHn-L3-CHW` | L3 CHW Functional + Water Quality | 80h | Cooling-commissioning contractor |
| `CX-DHn-L3-CONT-VER` | Containment Verification | 8h | CxA, pre-FA |
| `CX-DHn-ENERGIZE` | DH Energize hold-point | 56h | Utility coordination |
| `CX-DHn-FOD-WALK` | FOD Walks | 8h | GC / Client |
| `CX-DHn-L4-ATS` | L4 IST (ATS, integrated) | 40h | Post-FA |
| `CX-DHn-L5-LB` | L5 Load Bank IST | 80h | A+B feeds, post-FA |
| `MS-EFA-DHn` | Milestone: EFA | TT_FinMile | Contractual |
| `MS-FA-DHn` | Milestone: FA | TT_FinMile | Contractual |
| `MS-PCO-DHn` | Milestone: PCO | TT_FinMile | Contractual |

---

## 3. Commissioning L1 → L5 Framework

Industry-standard 5-level commissioning, applied per-system per-DH.

| Level | Name | Scope | Who owns | When |
|---|---|---|---|---|
| **L1** | FAT (Factory Acceptance Test) | Equipment tested at the factory pre-shipment | Vendor + CxA witness | Pre-delivery |
| **L2** | PFC (Pre-Functional Checks) | Static checks: equipment installed correctly, fluid filled, wiring correct | Trade contractor | Post-install, pre-energize |
| **L3** | Functional | System energized, tested in isolation (MV alone, LV alone, CDU alone, CHW alone) | Trade contractor + CxA | After PFC, gates EFA |
| **L4** | IST (Integrated Systems Test) | Multiple systems tested together (ATS, generator transfer, cooling-on-loss-of-power) | CxA + GC | Post-EFA / FA |
| **L5** | Load Bank IST | Full DH-level integrated test with load banks simulating IT load | CxA + Owner witness | Pre-PCO |

**Logic ties (typical):**
- L2 PFC → L3 Functional (FS)
- L3 (all systems complete) → EFA (FS, FF on the latest L3 activity)
- EFA → L4 IST (FS, after racks installed)
- L4 IST → FA (FS or FF)
- FA → L5 Load Bank → PCO (FS-FS chain)

---

## 4. Procurement-to-Install Logic Convention

**Long-lead equipment** (MV switchgear, transformers, STS, UPS, chillers, CDUs, Fan Walls, dry coolers):
- Tie: **FF (finish-to-finish)** with lag = install duration
- Rationale: Procurement is rarely a single point. Install can start with partial deliveries; install finish lags procurement finish by the install duration.

**Short-lead / commodity items** (cable, fittings, instrumentation, fasteners):
- Tie: **FS (finish-to-start)** or no procurement-to-install tie if reorderable
- Rationale: These don't drive schedule; no need to over-model.

**Example:**
```
PROC-DH4-ELEC-1000 (MV SWGR procurement, 12 weeks)
   FF+0h →
CONS-DH4-MR-1000 (MV SWGR install, 40h)
```
This means procurement finish ≤ install finish - 0h. Install can start before procurement finishes (with partial deliveries), but must finish at the same time or later.

---

## 5. Build-Sequence Stagger

**Default reference-project pattern:** 4 crews flow through 4 areas with **3-week stagger** per area. Common variants:
- 4-week stagger (more conservative, less crew conflict)
- 2-week stagger (aggressive, requires more crews)
- N-to-S vs S-to-N (project-specific)

**Implementation:**
- Pick the first DH (e.g., DH4) as the baseline.
- Apply per-DH date offsets: DH3 = DH4 + 3 weeks, DH2 = DH4 + 6 weeks, DH1 = DH4 + 9 weeks.
- Document in the schedule narrative.
- **Validate against the Build Sequence PDF on every revision.**

**Flag conditions:**
- If contractual EFA / FA dates are tighter than the stagger allows, surface to PM immediately.
- If trade-reported durations exceed the stagger window, the same crew can't flow 4 DHs — need parallel crews or extended schedule.

---

## 6. Trade-Specific Sequencing Within Mech Room (13-step pattern)

A typical mech room buildout follows this pattern (post-shell-complete):

1. **MV SWGR set** — anchor, bolt, level
2. **MV transformer set** — same
3. **LV transformer set** — same
4. **Cable bus install** — MV and LV
5. **UPS set** — HUPS, MUPS, CUPS (3 separate systems)
6. **Generator set** — anchor, fuel piping
7. **Chiller plant equipment set** — chiller, pumps, ET tank
8. **CHW piping install** — copper / steel / pre-insulated
9. **Hydrotest** — pressure test all piping
10. **Flush & Fill** — flush with clean fluid, fill with glycol/treated water (cooling-commissioning scope)
11. **Pump alignment + cooling-commissioning T&C** — final mech tune-up (cooling-commissioning scope)
12. **Feeder terminations** — MV, LV, UPS, Mech (electrical scope)
13. **Mech Room Ready** — punchlist, AHJ inspection, gate to L3 commissioning

**Notes:**
- Steps 1-6 are roughly parallel (different crews).
- Step 8 (piping) gates step 9 (hydrotest) gates step 10 (Flush & Fill).
- Step 11 is the cooling-commissioning contractor — they own pump alignment, valve checks, BAS PFC.
- Step 12 is the electrical contractor — terminations happen after equipment is set, before energization.
- Step 13 is the punchlist gate before L3-MV-EN starts.

---

## 7. Contractual Milestone Gating

| Milestone | Typical scope | Predecessor pattern |
|---|---|---|
| **EFA** (Early First Acceptance / Cooling-Live) | Cooling system live, DH ready for hot-aisle containment but no racks | L3-CDU, L3-CHW, Containment Verify, FOD Walks |
| **FA** (Final Acceptance) | Racks installed, DH ready for IT load (definition varies — see Lessons #8) | EFA + Rack Install + DH Electrical QA/QC |
| **MEC** (Mechanical Completion) | Mech systems installed + L2 PFC complete | All MR-* activities + L2 PFC |
| **TCO** (Temporary Certificate of Occupancy) | Building occupiable, all AHJ inspections passed | Final Inspections branch complete |
| **PCO** (Permanent Certificate of Occupancy) | Full 2N redundancy, all systems live, L5 IST passed | FA + L5 Load Bank + B-Feed live |

---

## 8. Calendar Conventions

- **Default:** 5-day, 8h shifts (Mon-Fri, 8 AM - 5 PM)
- **MEP / commissioning crews:** often 6-day (Mon-Sat) during crunch
- **Site work / pours:** weather-dependent, 7-day possible
- **Holidays:** US federal holidays observed; document in calendar XER block

For most DC schedules, **5-day primary + 6-day commissioning** is the common pattern. Define explicit calendar IDs in the XER and assign per-activity.

---

## 9. Constraint Convention

| Constraint type | Code (OPC) | When to use |
|---|---|---|
| Contractual not-later-than | `CS_MEOB` (FNL) | Final contract deadlines — EFA, FA, PCO |
| Contractual not-earlier-than | `CS_MEOA` | A-feed live date, milestone floors |
| Activity must-start-on-or-after | `CS_MSOA` (SNE) | Equipment delivery floors, owner-furnished dates |
| AVOID | `CS_MEO` | OPC silently drops — see Lessons #1 |
| AVOID | `CS_MSO` | OPC also flaky |

**Rule:** Use the minimum constraints needed. Over-constraining the schedule masks logic errors and prevents the CPM engine from showing real float.

---

## 10. Open-Items / Assumptions Register Pattern

Every assumption should be tracked. Suggested columns:

| ID | Category | Assumption | Source | Date assumed | Impact if wrong | Status |
|---|---|---|---|---|---|---|
| A1 | Commissioning | L3-CDU can run on test power | PM / cooling-commissioning contractor verbal | 2026-05-01 | DH4 EFA pushes 3 weeks | Open — awaiting CxA |
| A2 | Procurement | Remaining STS arrive by 5/22 | Procurement team verbal | 2026-05-08 | DH4 EFA pushes ~3 months if late | Open |
| ... | | | | | | |

Maintain this throughout the project. At every CHECKPOINT, walk PM through the open items. At Phase 7, deliver as a standalone artifact.

---

## How to use this file

- **Phase 3:** Use sections 1-9 as the starting structure for the Logic & Assumptions Memo. Adapt counts, durations, and stagger to project.
- **Phase 4:** Use sections 2-4 to build the per-DH activity catalog in the builder script.
- **Phase 5:** Replicate per-DH using the stagger from section 5.
- **Phase 7:** Section 10 becomes the assumptions register deliverable.
