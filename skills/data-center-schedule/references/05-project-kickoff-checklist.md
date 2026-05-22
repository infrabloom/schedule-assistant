# Project Kickoff Checklist — DC Schedule Build

Use this checklist at the start of every new DC schedule project. Run through it with the PM / GC scheduler / owner rep before Phase 1.

---

## A. Documents to Collect (Phase 0 — pre-Phase 1)

### From the Owner / Client

- [ ] **Contract / MSA** — for milestone definitions (EFA, FA, MEC, TCO, PCO)
- [ ] **Contractual dates** — confirmed not-later-than dates for every milestone
- [ ] **Client high-level schedule** (XER, PDF, or P6 export) — for milestone reference
- [ ] **Site plan / Keyplan** (PDF or DWG) — for zone-to-Area cross-reference
- [ ] **Building / Architectural plans** (PDF) — for shell / room layouts
- [ ] **Rack count + install rate** — owner's IT vendor cadence (e.g., FluidStack 4 weeks per DH)

### From the GC

- [ ] **Build Sequence document** — authoritative crew flow + area stagger
- [ ] **Prior GC schedule** (XER if exists) — for actuals through data date
- [ ] **GC schedule narrative / status report** — latest version
- [ ] **GC's site logistics plan** — for crew flow + lay-down area constraints
- [ ] **Site progress photos** (if available) — for visual validation of actuals
- [ ] **Subcontractor list** — names + scopes
- [ ] **MEL (Master Equipment List)** — equipment + lead times + zone mapping
- [ ] **Procurement status report** — by-equipment delivery status

### From Trade Contractors

- [ ] **Mech contractor schedule** (mpp / xml / xer) — install detail
- [ ] **Mech commissioning trade schedule** (mpp / xml) — F&F, pump alignment, L3-CHW, L3-CDU detail
- [ ] **Electrical contractor schedule** (mpp / xml) — install + L3 detail
- [ ] **CDU vendor schedule** — manufacture + delivery + L1 FAT
- [ ] **Fan Wall vendor schedule** (if applicable) — manufacture + delivery + install
- [ ] **UPS vendor schedule** — manufacture + delivery + L1 FAT
- [ ] **Generator vendor schedule** — manufacture + delivery + L1 FAT
- [ ] **MV / LV switchgear vendor schedule** — manufacture + delivery
- [ ] **Fire protection contractor schedule** — sprinkler + alarm install
- [ ] **CxA schedule** — witness availability for L1 / L3 / L4 / L5

### Reference Materials

- [ ] **P6 templates from prior DC projects** — at least 2-3 for domain knowledge (use the templates in `assets/p6-templates/` as starters)
- [ ] **Standard CxA test procedures** — for L3 / L4 / L5 scope
- [ ] **AHJ inspection requirements** — local code requirements
- [ ] **Owner's commissioning specs** — if owner has standardized requirements

---

## B. Decisions to Lock Down (Phase 1 — before Phase 3)

These are the **critical questions** that drive schedule logic. Get answers in writing.

### Milestone Definitions

- [ ] **What does EFA mean exactly?** (Cooling-live? Full electrical commissioning? Partial?)
- [ ] **What does FA mean exactly?** (Racks physically installed? Racks energized? Full IST?)
- [ ] **What does MEC mean exactly?** (Pre-L2 PFC? Post-L2 PFC? Includes commissioning?)
- [ ] **What does TCO require?** (Building inspections only? Or also some commissioning?)
- [ ] **What does PCO require?** (Full 2N redundancy? Single-feed acceptable? L5 IST mandatory?)

### Power & Energization

- [ ] **Utility energization dates** — A-feed live date, B-feed live date
- [ ] **Back-fed power capability** — can it run hydros / pump startup / chiller startup?
- [ ] **Test/temp power for commissioning** — what's available and what scope does it support?
- [ ] **Is L3 commissioning on test power, production power, or both options?**
- [ ] **Is PCO contractually gated on B-feed / 2N, or can it be on A-feed only?**

### Trade Scope

- [ ] **Who installs CDUs?** (Vendor — Schneider / Vertiv / other — NOT mech contractor usually)
- [ ] **Who installs Fan Walls?** (Vendor — confirm — DAF procures but doesn't install on CB4)
- [ ] **Who owns Flush & Fill?** (Cooling commissioning trade, NOT install contractor)
- [ ] **Who installs racks?** (Owner / owner's IT vendor)
- [ ] **Who is the CxA?** (Third-party — book early, they're often hidden critical path)

### Sequencing

- [ ] **Stagger pattern** — 3 weeks per area? 4 weeks? 2 weeks?
- [ ] **Build order** — N-to-S or S-to-N? Which DH first?
- [ ] **Parallel vs sequential crews** — 1 crew flowing 4 areas, or 4 parallel crews?
- [ ] **Admin building timing** — concurrent with which Area?

### Durations

- [ ] **Confirm trade-reported durations vs template defaults** (see Lessons #6)
- [ ] **L3-MV-EN duration** — confirm with OCE / CxA
- [ ] **L3-LV-EN duration** — confirm with OCE / CxA
- [ ] **DH Branch Power install duration** — confirm with electrical contractor
- [ ] **Rack install duration** — confirm with owner

### Procurement

- [ ] **Equipment receipt status** — what's onsite as of data date?
- [ ] **Outstanding deliveries** — confirmed dates for each long-lead item
- [ ] **Procurement → install tie convention** — FF or FS, per equipment family
- [ ] **Any equipment with vendor-allocated quantities** (e.g., "DH4 gets first 32 STS, DH3 next 32...")

---

## C. People to Identify (Phase 1)

Get name + email + role for each. Update throughout project.

- [ ] **Owner PM** (final authority on milestone definitions)
- [ ] **Owner's IT lead** (rack install + IT load schedule)
- [ ] **GC PM** (this is your direct boss)
- [ ] **GC PE / Field Lead** (real-time site status)
- [ ] **Mech install lead** (PM at MLP)
- [ ] **Mech commissioning lead** (PM at DAF — cooling)
- [ ] **Electrical lead** (PM at OCE)
- [ ] **CDU vendor PM** (Schneider / Vertiv contact)
- [ ] **Fan Wall vendor PM** (TBD on CB4)
- [ ] **UPS vendor PM**
- [ ] **Generator vendor PM**
- [ ] **MV / LV switchgear vendor PM**
- [ ] **Fire protection PM**
- [ ] **BMS / Controls integrator**
- [ ] **CxA lead** (third party)
- [ ] **AHJ contact** (local building/electrical/mech inspector)
- [ ] **Utility contact** (for A-feed / B-feed coordination)

---

## D. Initial Site Walk Items (Phase 1)

If you can visit the site:

- [ ] **Walk every Mech Room** — equipment delivery status, install progress, lay-down
- [ ] **Walk every Data Hall** — shell status, CDU positions, rack pad readiness
- [ ] **Walk every Yard** — MV switchgear pads, generator pads, dry cooler positions
- [ ] **Walk Roofs** — RTU positions, penetrations, ducts
- [ ] **Walk MMR / telecom rooms** — if applicable
- [ ] **Walk Admin building** — if scope is significant
- [ ] **Walk utility tie-in points** — East Mains, West Mains, AFEED, BFEED
- [ ] **Photo every equipment installed** — with tag visible, for actuals validation
- [ ] **Meet field foremen** — they know what's really happening vs the schedule

---

## E. Project Data Setup (Phase 1 — your local setup)

- [ ] **Project workspace folder** — copy this toolkit
- [ ] **Cowork project initialized** — paste the project-instructions (the kickoff prompt, adapted for this project) as the Cowork project instructions
- [ ] **Source documents folder** — organize by category (Client / GC / Mech / Electrical / Procurement / Reference)
- [ ] **Outputs folder** — for deliverables
- [ ] **Lessons log created** — an empty `lessons-log.md` in the project folder, so the Phase 3/4/6 [CAPTURE] steps and the Phase 7 build retrospective have somewhere to write. See `MAINTENANCE.md`.
- [ ] **Version control plan** — `v1` per approved phase, `v1.x` per iteration
- [ ] **Data date confirmed** — agreed-upon snapshot date for all actuals
- [ ] **Calendar / holiday list** — for the XER calendar block

---

## F. First Meeting Agenda (Recommended)

When you have all the documents and people identified, schedule a 60-90 min kickoff meeting with:

**Attendees:** Owner PM, GC PM, mech install lead, mech commissioning lead, electrical lead, CDU vendor PM, CxA lead, you (scheduler).

**Agenda:**
1. Introductions + roles (10 min)
2. Walk through the contractual milestone definitions (15 min) — get explicit answers to "what does EFA / FA / PCO mean"
3. Walk through the Build Sequence document (10 min) — confirm crew flow and stagger
4. Walk through the trade responsibility map (15 min) — name the lead trade per scope
5. Open question dump (15 min) — capture every "I don't know yet" item
6. Next steps (5 min) — schedule Phase 3 checkpoint

**Output:** Meeting minutes + open items list. Initiate the assumptions register from this meeting.

---

## G. Phase 1 Exit Criteria

Before moving to Phase 2:

- [ ] All documents in Section A collected (or explicitly noted as missing)
- [ ] All decisions in Section B answered (or explicitly noted as open items)
- [ ] All people in Section C identified
- [ ] Phase 1 Domain Knowledge Memo written from the P6 templates
- [ ] PM has reviewed and signed off on the memo

If you don't have everything, **flag the gaps explicitly** and proceed with what you have — don't fabricate.

---

## H. Red Flags to Watch For

Trigger heightened scrutiny if any of these are true:

- 🟥 **Prior GC schedule has known bad logic** (per CB4 — duplicates, broken ties) → Do NOT carry forward logic
- 🟥 **Trade durations are 3-10× template defaults** → Investigate, don't auto-pick (see Lessons #6)
- 🟥 **CxA not yet engaged** → Critical path hidden until they're booked
- 🟥 **Equipment with > 20 week lead time not yet ordered** → Surface as a procurement chase-list item
- 🟥 **Contractual EFA / FA dates tighter than 3-week-per-area stagger allows** → Flag immediately
- 🟥 **Owner can't define EFA / FA / PCO scope** → Get it in writing before building schedule
- 🟧 **Multiple trades all claim ownership of a scope** → Resolve before building
- 🟧 **Calendar conventions unclear** → Lock down 5-day / 6-day / 7-day, with holidays

---

## How to use this on a new project

1. Walk through Section A first — collect documents.
2. Then Section B — get answers in writing.
3. Then Section C — identify people.
4. Sections D-F are concurrent during Phase 1.
5. Section G is your gate to Phase 2.
6. Section H is your sanity check — if any red flag fires, slow down.
