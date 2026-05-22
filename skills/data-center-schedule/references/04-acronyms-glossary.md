# Acronyms & Terminology — DC Scheduling

The acronyms you'll hit on any hyperscale data center scheduling project. Distilled from the reference project — most are industry-standard.

---

## Contractual Milestones

| Acronym | Meaning | Notes |
|---|---|---|
| **EFA** | Early First Acceptance | Cooling-live milestone. DH ready for hot-aisle containment, but no racks yet. Definition varies by contract — get it in writing. |
| **FA** | Final Acceptance | Racks installed + DH ready for IT load. Definition varies — get it in writing. |
| **MEC** | Mechanical Completion | Mech systems installed + L2 PFC complete. Pre-energization. |
| **TCO** | Temporary Certificate of Occupancy | Building occupiable per local AHJ. Pre-PCO. |
| **PCO** | Permanent Certificate of Occupancy | Full 2N redundancy live, all systems commissioned, L5 IST passed. |
| **SC** | Substantial Completion | Often used interchangeably with FA / TCO depending on contract. |

---

## Commissioning Levels

| Level | Name | Scope |
|---|---|---|
| **L1** | FAT (Factory Acceptance Test) | Equipment tested at factory pre-shipment |
| **L2** | PFC (Pre-Functional Checks) | Static: equipment installed, fluid filled, wiring correct |
| **L3** | Functional | System energized + tested in isolation |
| **L4** | IST (Integrated Systems Test) | Multiple systems tested together |
| **L5** | Load Bank IST | Full DH integrated test with load banks |

---

## Equipment / Systems

| Acronym | Meaning |
|---|---|
| **MV** | Medium Voltage (usually 15kV class) |
| **LV** | Low Voltage (480V / 277V) |
| **MV SWGR** | Medium Voltage Switchgear |
| **LV SWGR** | Low Voltage Switchgear / Switchboard |
| **MVSWBD** | Medium Voltage Switchboard (typically mech-keyed) |
| **STS** | Static Transfer Switch |
| **ATS** | Automatic Transfer Switch |
| **UPS** | Uninterruptible Power Supply |
| **HUPS** | Hot UPS (always-on) |
| **MUPS** | Mech UPS (cooling support) |
| **CUPS** | Cooling UPS (specifically pumps/CDU) |
| **PDU** | Power Distribution Unit |
| **RPP** | Remote Power Panel |
| **CDU** | Cooling Distribution Unit (rack-level cooling) |
| **CRAH** | Computer Room Air Handler |
| **CRAC** | Computer Room Air Conditioner |
| **AHU** | Air Handling Unit |
| **RTU** | Rooftop Unit |
| **CHW** | Chilled Water |
| **CW** | Condenser Water |
| **HW** | Hot Water (for reheat, rare in DCs) |
| **ET** | Expansion Tank |
| **DC** | Dry Cooler (heat rejection) |
| **CT** | Cooling Tower |
| **VFD** | Variable Frequency Drive |
| **BMS** | Building Management System |
| **BAS** | Building Automation System |
| **DCIM** | Data Center Infrastructure Management |
| **EPMS** | Electrical Power Monitoring System |
| **MMR** | Meet-Me Room (telecom carrier handoff) |

---

## Construction Activities

| Acronym | Meaning |
|---|---|
| **CONS** | Construction (WBS prefix) |
| **PROC** | Procurement (WBS prefix) |
| **CX** | Commissioning (WBS prefix) |
| **MR** | Mech Room (activity location) |
| **DH** | Data Hall (activity location) |
| **YN** | Yard North / East (activity location) |
| **YS** | Yard South / West (activity location) |
| **RF** | Roof (activity location) |
| **MS** | Milestone (WBS prefix) |
| **F&F** | Flush & Fill (mech commissioning step — flush first, then fill) |
| **T&C** | Test & Commission |
| **FAT** | Factory Acceptance Test |
| **SAT** | Site Acceptance Test |
| **FOD** | Foreign Object Debris (walk-through to clear DH before energize) |
| **QA/QC** | Quality Assurance / Quality Control |

---

## Trades / Roles

| Acronym | Meaning |
|---|---|
| **GC** | General Contractor |
| **PM** | Project Manager |
| **PE** | Project Engineer |
| **CxA** | Commissioning Authority (third-party) |
| **SI** | Systems Integrator |
| **AHJ** | Authority Having Jurisdiction (local inspector) |
| **MEP** | Mechanical / Electrical / Plumbing |

---

## P6 / OPC Terminology

| Term | Meaning |
|---|---|
| **P6** | Primavera P6 (Oracle's scheduling tool) |
| **OPC** | Oracle Primavera Cloud (cloud version of P6) |
| **XER** | P6 native export format (tab-delimited) |
| **XML** | P6 XML export (alternative format) |
| **MPP** | Microsoft Project (.mpp) — often used by trade contractors |
| **WBS** | Work Breakdown Structure |
| **CPM** | Critical Path Method |
| **TF** | Total Float |
| **FF** | Free Float OR Finish-to-Finish (context-dependent) |
| **FS** | Finish-to-Start (predecessor type) |
| **SS** | Start-to-Start (predecessor type) |
| **SF** | Start-to-Finish (predecessor type — rarely used) |
| **FNL** | Finish No Later than (CS_MEOB) |
| **SNE** | Start No Earlier than (CS_MSOA) |
| **TT_Task** | P6 task type: standard activity |
| **TT_Mile** | P6 task type: start milestone |
| **TT_FinMile** | P6 task type: finish milestone |
| **TK_NotStart** | P6 status: not yet started |
| **TK_Active** | P6 status: in progress |
| **TK_Complete** | P6 status: complete |
| **CS_MEOA** | P6 constraint code: Finish On or After (works in OPC) |
| **CS_MEOB** | P6 constraint code: Finish On or Before / FNL (works in OPC) |
| **CS_MSOA** | P6 constraint code: Start On or After / SNE (works in OPC) |
| **CS_MEO** | P6 constraint code: Mandatory Finish On (FAILS in OPC — see Lessons #1) |
| **GUID** | Globally Unique Identifier (required on every task in XER) |
| **act_start** | Actual start date (on a TASK row) |
| **act_end** | Actual end date (on a TASK row) |
| **remain_drtn** | Remaining duration (on a TASK row) |
| **target_drtn** | Total planned duration |
| **phys_complete_pct** | Physical % complete |
| **lag_hr_cnt** | Lag in hours on a TASKPRED row |

---

## Power / Energization Terms

| Acronym | Meaning |
|---|---|
| **A-Feed** | Primary redundant power path |
| **B-Feed** | Secondary redundant power path (2N redundancy = A + B both live) |
| **2N** | Fully redundant — two independent feeds, either can carry full load |
| **N+1** | One spare beyond minimum — common for chillers, pumps, UPS modules |
| **East Mains** | Physical utility tie-in on east side (project-specific) |
| **West Mains** | Physical utility tie-in on west side (project-specific) |
| **Back-fed** | Temporarily energized from another source, not full production power |
| **Hi-pot** | High-potential test (insulation test for cables) |
| **Megger** | Insulation resistance test (brand name for the meter, used as a verb) |
| **JBO** | Job-site temp power (project-specific term — verify on each project) |

---

## Cooling Terminology

| Term | Meaning |
|---|---|
| **Chilled Water (CHW)** | Loop carrying ~45-65°F water through DH for cooling |
| **Glycol** | Antifreeze additive for outdoor / cold-climate loops |
| **Flush** | Run water through pipe to clear debris (FIRST) |
| **Fill** | Charge system with treated/inhibited fluid (SECOND) |
| **Hot Aisle / Cold Aisle** | Standard DH layout — alternating airflow rows |
| **Containment** | Physical barrier separating hot/cold aisles |
| **Hot Aisle Containment** | Enclosed hot aisle, cold air supplied to room |
| **Cold Aisle Containment** | Enclosed cold aisle, hot air dumps to room |
| **Free Cooling** | Use outdoor air directly or via heat exchanger, no chiller |
| **Liquid Cooling** | CDU-based, fluid to chip-level cold plate |
| **Direct-to-Chip (D2C)** | Liquid cooling delivered to GPU/CPU cold plates |

---

## Inspections / Certifications

| Acronym | Meaning |
|---|---|
| **AHJ** | Authority Having Jurisdiction |
| **NEC** | National Electrical Code |
| **NFPA** | National Fire Protection Association |
| **NETA** | International Electrical Testing Association |
| **UL** | Underwriters Laboratories |
| **CSA** | Canadian Standards Association |
| **OSHA** | Occupational Safety and Health Administration |
| **TCO** | Temporary Certificate of Occupancy |
| **PCO** | Permanent Certificate of Occupancy |

---

## Common Vendors (project-specific — confirm on each project)

| Vendor | Scope on the reference project |
|---|---|
| Schneider Electric | CDUs, MV / LV switchgear (some) |
| Vertiv | Alternate CDU vendor |
| ABB | MV switchgear (alternate) |
| Cummins / Caterpillar | Generators |
| Eaton | UPS / switchgear |
| Trane / Carrier / York | Chillers |
| Stulz | CRAH / CRAC (alternate) |
| The client | Owner-side IT party (rack install + IT load) — project-specific |
| The owner | Project sponsor / GC partner — project-specific |

---

## Infrastructure & Design Terms

Engineering terms from data center design -- see `references/11-infrastructure-primer.md` for the full picture.

| Term | Meaning |
|---|---|
| **WSC** | Warehouse-Scale Computer -- a data center treated as one large computer. |
| **Critical power** | The continuous power deliverable to IT equipment; the metric a data center is sized in. |
| **Unit substation** | A primary distribution center: primary switchgear + MV-to-LV transformers. |
| **Busbar** | An overhead power bus running along a rack row; racks tap into it. |
| **Tap box / tap-off unit** | Breaker-protected attachment that drops a circuit from a busbar to a rack. |
| **Tier (I-IV)** | Uptime Institute facility redundancy rating; the lowest-rated subsystem sets the tier. |
| **Uptime Institute** | The body that defines the Tier classification. |
| **TIA-942** | Prescriptive telecom-industry data center standard (an alternative to Tier ratings). |
| **N+2 / N+M** | Redundancy: two spares / M spares. N+2 gives concurrent maintainability. |
| **DR (Distributed Redundant)** | Power topology giving ~2N function at ~N+1 cost (e.g. "4/3 DR"). |
| **PUE** | Power Usage Effectiveness -- total facility power / IT power; the power+cooling overhead metric. |
| **TDP** | Thermal Design Power -- the heat a chip is designed to dissipate. |
| **EPO** | Emergency Power Off -- forced IT shutdown, e.g. within 5-15 min of a cooling loss. |
| **PCWS** | Process Chilled Water Supply loop. |
| **Wet-bulb temperature** | Lowest temperature reachable by evaporative cooling; drier air = lower wet-bulb. |
| **Dry-bulb temperature** | Ordinary air temperature. |
| **Approach** | Gap between a cooling tower's output water temp and the wet-bulb temp (~1-2 C). |
| **Fill** | Surface-area material inside a cooling tower that aids evaporation. |
| **Economizer** | Equipment enabling free cooling (cold outside air / tower) without the chiller. |
| **Immersion cooling** | Submerging servers in dielectric fluid; 1P = single-phase, 2P = two-phase. |
| **Rear-door HX** | Rear-door heat exchanger -- a water-cooled coil on the back of a rack. |
| **Five Envelopes** | Framework for how far a DC build is staged / who builds what (land -> ... -> IT deployment). |
| **Equipment skidding** | Pre-assembling equipment on skids for modular delivery. |
| **Kit-of-parts** | Prefab construction from standardized, demountable, reusable components. |
| **Clos network** | A data center network topology (relevant to cluster-fitout fiber). |

---

## Owner-Specific Milestone & Handover Terms

Milestone vocabulary is owner-specific -- same shape (early access -> handover ->
completion), different names. See `references/12-reference-template-library.md`.

| Term | Used by | Meaning |
|---|---|---|
| **EFA / FA / FR / RFS** | the owner (reference project) | Early First Access / Facility Access / Facility Ready / Ready For Service. |
| **FEA** | alt. owner pattern | Fiber Early Access. |
| **NEA** | alt. owner pattern | Network Early Access. |
| **H2C** | alt. owner pattern | Hand-to-Customer handover milestone (exact expansion not stated in source -- confirm with the owner). |
| **PFHO** | alt. owner pattern | A subsequent handover milestone (exact expansion not stated -- confirm). |
| **OFCI** | general | Owner-Furnished, Contractor-Installed equipment. |
| **LLE** | general | Long-Lead Equipment. |
| **OSD** | general | On-Site Date -- the delivery milestone for an equipment item. |
| **PDC** | general | Power Distribution Center -- a packaged power-distribution module. |
| **Whips** | general | Flexible power conduit drops (e.g. "PDC Whips", "RPP Whips"). |

---

## How to use this glossary

- **Reference during reading** — every contract / schedule / trade-meeting note will have unfamiliar acronyms.
- **Add project-specific terms** — every project has its own vendor names, trade abbreviations, internal codes. Add them at the bottom.
- **Send to new team members** — saves hours of "what does that mean" in meetings.
