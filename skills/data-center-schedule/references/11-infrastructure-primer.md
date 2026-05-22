# Data Center Infrastructure Primer -- What Each System Does & How a Build Is Staged

Source: distilled from *The Data Center as a Computer* (4th ed.), Chapter 5,
"WSC Hardware: Data Center Infrastructure." This reference grounds the
*scheduling* knowledge in the other files -- it explains WHAT the equipment in a
DC schedule actually does and WHY the construction sequence runs the way it
does. Read it when you need the engineering rationale behind a sequencing or
logic decision.

## Why this matters to a scheduler

A data center building exists to deliver four things: **power, cooling, shelter,
security**. Almost all the energy that goes in comes out as heat. So a DC
schedule is, at its core, a **power-delivery and heat-removal project** --
construction cost runs roughly **$5-20 per watt of "critical power"** (the
continuous power deliverable to IT gear). Every activity in the schedule serves
either the power path or the heat path; understanding both tells you what must
precede what.

## 1. The construction staging framework (the "Five Envelopes")

A hyperscale data center is built in ordered stages; capacity is deliberately
buffered at the earlier (cheaper-to-hold) stages. In order:

1. **Entitled land** -- a parcel held with title + zoning. Lead time: months to years.
2. **Utility connections** -- power, water, sewer, roads. Months to years.
3. **Pad & shell** -- site grading (level/sloped pad, drainage, foundation) plus
   the building shell, no fitout. Grading alone is a few months.
4. **Electrical substation** -- steps utility high voltage down to medium voltage.
   **Long lead: commonly 12-18 months, ~$0.10/W. Often the schedule's long pole.**
5. **Facility outside the floor** -- the cooling and electrical plants + controls.
6. **Data-hall fitout** -- busbars, cable tray, cooling units inside the hall.
7. **Cluster fitout** -- rack power tap boxes, network racks, fiber bundles --
   then IT equipment is deployed.

$/W investment escalates rapidly from stage 4 onward.

**Where this skill's schedules sit:** an owner-side construction schedule
(reference-project-style) typically covers **stages 3-7** -- shell, plant, data-hall fitout,
cluster fitout. Stages 1-2 (land, utilities) and the substation long-lead are
usually "by others", but they **must appear as predecessors / long-lead
constraints** to the energization milestones (A-feed / B-feed). If the
substation is on an 18-month lead, that sets the earliest possible energization
date -- surface it in Phase 1.

The "five envelopes" themselves describe **who builds what** -- from a
hyperscaler self-building everything (Envelope 1) to pure colocation where a
third party builds all but the IT gear (Envelope 5). Confirm in Phase 1 which
envelope the project is, so the schedule's scope boundary is correct.

## 2. The power path -- what each component does

Power flows in this order; the electrical install + energization sequence
follows the same chain:

| Component | What it does |
|---|---|
| **Utility substation** | Steps incoming high voltage (>=110 kV) down to medium voltage (<50 kV). Long-lead; often utility scope. |
| **MV site distribution** | Carries medium voltage across the site to the unit substations. |
| **Unit substation** | A primary distribution center: primary **switchgear** + **MV-to-LV transformers** (output <1000 V). |
| **Transformer** | Steps voltage down between stages. |
| **Switchgear / switchboard** | Protects and switches circuits -- the controllable breakers of the power system. |
| **UPS (Uninterruptible Power Supply)** | Three jobs in one: (1) **transfer switch** -- picks utility vs generator; (2) **energy storage** -- bridges the ~10-15 s a generator needs to start and take load; (3) **power conditioning** -- cleans spikes, sags, harmonics. |
| **Generator** | Standby power when utility fails. Takes 10-15 s to start and assume full load -- the UPS covers that gap. Must be sized for IT **plus mechanical** load (see section 4). |
| **ATS / STS** | Automatic / Static Transfer Switch -- switches a load between A and B sources on failure. |
| **PDU (Power Distribution Unit)** | A large breaker panel (often with a final transformer). Splits a 2-3 MW feed into breaker-protected circuits and feeds the busbars. |
| **Busbar + tap-off / tap box** | An overhead bus running along a rack row; each rack drops a short cable to a tap box (with breaker). Replaces long home-run cabling -- a major floor-fitout labor saver. |
| **A / B feeds** | Two independent power paths to a PDU/rack. 2N = both live, either carries full load. |

**Redundancy vocabulary** (it drives how much equipment exists):
N = bare minimum; N+1 = one spare (one failure/maintenance at a time);
N+2 = survives a failure even with one unit down for maintenance ("concurrent
maintainability"); N+M = M spares; 2N = fully duplicated.

**Uptime Institute Tiers** (a whole-facility rating): Tier I single path, no
redundancy; Tier II redundant components (N+1); Tier III concurrently
maintainable (active + alternate path); Tier IV fault-tolerant (two active
paths, survives any single failure). **The lowest-rated subsystem sets the whole
facility's tier** -- power and cooling must be commissioned to the same target
tier or money is wasted.

## 3. The cooling path -- what each component does

A data center overheats in minutes without cooling, so the cooling path is as
critical as the power path. Heat moves outward through nested loops. A common
hyperscale design is the **three-loop system**:

1. **Air loop** -- air cooled by fan coils, heated by the servers, kept short
   (hot aisle captured, cooled air returned to the cold aisle).
2. **Process / chilled water loop** -- warm water from the fan coils returns to
   the plant, is chilled, pumps back. (The reference project's CHW / PCW loops.)
3. **Condenser water loop** -- carries heat from the process loop out to the
   cooling towers for rejection. (The reference project's CW loop.)

| Component | What it does |
|---|---|
| **Cooling tower** | Rejects heat by **evaporating** part of a water stream; output temp approaches the outside **wet-bulb** temperature (the gap is the "approach", ~1-2 C). The most efficient heat-rejection method. |
| **Dry cooler / radiator** | Rejects heat by blowing air over a fluid coil -- no evaporation. Good in cold climates, weak in warm ones. |
| **Chiller** | A large water-cooled refrigeration unit (compressor + evaporator + condenser). Actively chills the process water. Energy-hungry -- **runs only when the towers alone cannot keep up** (warm days). |
| **Economizer / free cooling** | Uses cold outside air or a tower heat-exchanger to chill water without running the chiller -- a big energy saving when weather allows. |
| **CRAC / CRAH / fan wall** | The air movers + cooling coils on the floor. CRAC = older direct-expansion units; CRAH = chilled-water air handler; **fan wall = a banked fan array**, the modern high-density replacement. |
| **Containment (hot/cold aisle)** | Physical walls separating hot and cold air so every server ingests the same cool temperature. Hot-aisle containment adds <10% to IT energy. |
| **CDU (Cooling Distribution Unit)** | Connects the building process-water loop to **rack/tray-level** liquid cooling -- breaks the coarse building loop into the fine flows each rack needs. Trays tap in via no-drip quick-connects. |
| **Cold plate** | A liquid-cooled heat sink mounted directly on the hottest chips (CPU/GPU/TPU). Standard once a chip exceeds ~200-250 W. |
| **Rear-door heat exchanger (rear-door HX)** | A water-cooled coil on the back of a rack -- captures hot exhaust right at the rack. |

**Why liquid cooling now matters:** traditional racks draw 10-30 kW; AI / GPU /
TPU racks draw **50-200 kW and rising**. Air cooling becomes physically and
economically impractical above ~150-200 W/sq ft, because airflow demand scales
linearly with rack power. So high-density (AI/HPC) halls require liquid cooling
-- CDUs, cold plates, rear-door HX, per-rack chilled-water plumbing. **That
plumbing is real schedule scope:** more pipe, more connections, leak management,
and finer water distribution than the old building loop. The reference project's CDUs and
rear-door HX exist for exactly this reason.

## 4. Two facts that change how you size and sequence

- **Cooling backs up the generators.** Chillers and pumps can add **40%+** to
  the critical load the generators must carry -- generator/UPS sizing is not just
  the IT load. Mechanical commissioning therefore depends on backup power being
  available, not only utility power.
- **The EPO window.** A 25 MW hall heats ~0.8 C per second with cooling off, and
  equipment cannot tolerate intake above ~40 C, so operators must shut IT down
  within **5-15 minutes** of a cooling loss (an Emergency Power Off). This is why
  cooling functional tests and cooling-on-backup-power tests are non-negotiable
  commissioning gates.

## 5. Building, fire, security, and modular construction

- **Shell & building:** site -> grading -> shell -> fitout. Most modern
  hyperscale designs **avoid raised floors** (cost) -- do not assume an
  underfloor air plenum. Distinct work areas: mechanical yard (towers,
  chillers), electrical yard (generators, distribution), the main server hall,
  and networking rooms (extra security + availability).
- **Fire protection:** fire-resistive / non-combustible construction. **Li-ion
  battery rooms carry real fire risk** (thermal runaway -- a 2020 battery fire
  destroyed a data center). Battery-room fire protection is non-trivial scope.
- **Security:** layered access control -- fencing, circle locks, metal
  detectors, guards, camera networks; networking rooms get extra.
- **Modular / prefab construction is a schedule-compression lever.** Modular
  electrical buildings, **equipment skidding** (pre-assembling equipment on
  skids), and **kit-of-parts** standardized components move work off the
  critical onsite path. If a project uses prefab, the schedule should show
  shorter onsite durations but a procurement/fabrication predecessor.

## 6. What this means for the schedule

- Sequence the **power path** in physical order: substation -> MV distribution
  -> unit substation (switchgear + transformers) -> UPS -> PDU -> busbar / tap
  box -> rack power. Energization (commissioning L3) follows the same order.
- Sequence the **cooling path** by loop: condenser loop + towers, then the
  process / chilled-water loop + chillers, then the air side (fan walls / CRAH)
  and the liquid side (CDU, cold plates) -- then Flush & Fill, then startup,
  then L3.
- Treat the **substation** as a long-lead predecessor (12-18 months) to every
  energization milestone, even when it is "by others".
- For **AI / high-density halls**, budget explicit scope for liquid cooling
  (CDU set + connections, rack-side plumbing, leak management).
- Size **generator-backed commissioning** for IT + mechanical load.
- Confirm the **target Tier** in Phase 1 and commission power and cooling to the
  same tier.

## How to use this reference

Read it once at the start of a project so the construction sequence in
`02-schedule-patterns.md` and the durations in `08-duration-benchmarks.md` have
their engineering rationale. When a logic tie or sequencing decision is
questioned, this file is the "why".
