# Trade Responsibility Map — Who Owns What

This is the **generic** version. Replace the generic trade descriptions with your project's actual contractors. The role/scope split is what's portable.

---

## The Big Picture — 6 Primary Trade Roles

| Role | Generic name | What they own | Example |
|---|---|---|---|
| **Mech Install** | Mech Contractor | Set chillers, pumps, piping, hydrotest | The mechanical contractor (mechanical lead partner) |
| **Mech Commissioning** | Mech CxA / Cooling SI | Flush & Fill, pump alignment, BAS PFC, L3-CHW, L3-CDU support | The cooling-commissioning contractor |
| **Electrical Install + Commissioning** | Electrical Contractor | All electrical install + L3 energization | The electrical contractor (on-site construction electrical) |
| **CDU Vendor** | Cooling Distribution Unit installer | CDU set + power connections + L1 FAT + L3 functional support | Schneider / Vertiv (NOT mech contractor) |
| **Fan Wall Vendor** | Fan Wall installer | Fan Wall set + commissioning | Vendor TBD — the cooling-commissioning contractor procures but does NOT install |
| **Rack Install** | Owner / Owner's vendor | Rack install + cabling + ITSM | The client (owner-direct) |

**Supporting roles:**
| Role | Generic | Example |
|---|---|---|
| Commissioning Authority | CxA (third-party) | TBD |
| AHJ Inspector | Local authority | Local town / state authority |
| Fire Protection | Fire contractor | Separate vendor |
| BMS Programmer | Controls integrator | Often Schneider or Honeywell |
| Civil / Sitework | Site GC sub | Civil/sitework subcontractor |
| Concrete | Concrete sub | Concrete subcontractor |
| Earthwork | Earthwork sub | Earthwork subcontractor |

---

## Detailed Scope Split — Mech Install vs Mech Commissioning

This is the most-confused split on every DC project. Be explicit.

| Activity | Mech Install (mechanical contractor) | Mech CxA (cooling-commissioning contractor) |
|---|---|---|
| Chiller set in place | ✅ | |
| Pump set in place | ✅ | |
| Piping install (CHW, glycol, specialty) | ✅ | |
| Pipe insulation | ✅ | |
| Hydrotest (pressure) | ✅ | |
| **Flush & Fill** | | ✅ |
| Glycol charge | | ✅ |
| Pump alignment | | ✅ |
| Valve set checks | | ✅ |
| BAS Pre-Functional Checks | | ✅ |
| Vibration analysis | | ✅ |
| L3 CHW Functional | | ✅ (lead) |
| L3 CDU Functional | | ✅ (support — CDU vendor leads) |
| Water Quality Verification | | ✅ |

**Rule of thumb:** Anything that involves fluid IN the system (post-hydrotest) is commissioning scope, not install. Anything dry / static is install scope.

---

## Detailed Scope Split — Electrical Install vs Electrical Commissioning

Usually the same contractor (the electrical contractor) does both, but the L3 commissioning piece may have a separate CxA witness.

| Activity | Electrical Install | Electrical CxA (witness) |
|---|---|---|
| MV switchgear set | ✅ | |
| LV switchgear set | ✅ | |
| Transformer set | ✅ | |
| UPS set | ✅ (sometimes vendor) | |
| Generator set | ✅ (sometimes vendor) | |
| ATS set | ✅ | |
| Cable bus install | ✅ | |
| Cable pull (MV, LV, branch) | ✅ | |
| Terminations (MV, LV, UPS, Mech) | ✅ | |
| Megger / hi-pot testing | ✅ (lead) | ✅ witness |
| Relay testing | ✅ (or third-party relay tester) | ✅ witness |
| **L3 MV Energization** | ✅ (lead) | ✅ witness |
| **L3 LV Energization** | ✅ (lead) | ✅ witness |
| **L3 UPS Functional** | ✅ (vendor or electrical contractor) | ✅ witness |
| **L3 Generator Functional** | ✅ (vendor or electrical contractor) | ✅ witness |
| **L4 IST (ATS, integrated)** | ✅ (with CxA) | ✅ lead |
| **L5 Load Bank IST** | | ✅ lead |

---

## CDU Vendor Scope (Often Confused with Mech Contractor)

**CDU = Cooling Distribution Unit.** On hyperscale AI/HPC DCs, these are typically pre-fab units (Schneider / Vertiv / Stulz) that connect chilled water to rack-level cooling loops.

| Activity | CDU Vendor | Mech Contractor | Electrical Contractor |
|---|---|---|---|
| CDU manufacture | ✅ | | |
| CDU FAT (L1) | ✅ + CxA witness | | |
| CDU deliver to site | ✅ | | |
| **CDU set in place** | ✅ (or rigger sub) | | |
| CDU piping connections (CHW side) | | ✅ | |
| CDU piping connections (rack side) | ✅ | | |
| **CDU power connections** | | | ✅ |
| CDU BMS connections | ✅ | | |
| L2 PFC (CDU) | ✅ | | |
| **L3 CDU Functional** | ✅ (lead) | ✅ support (CHW side) | ✅ support (power side) |

**On the reference project:** The mech contractor does NOT install CDUs. This is a separate vendor. Schedule activities should reference the CDU vendor explicitly.

---

## Fan Wall Vendor Scope (Newer Pattern on AI DCs)

**Fan Wall** = banked array of fans replacing traditional CRAH/CRAC for high-density cooling.

| Activity | Fan Wall Vendor | Mech Contractor | Electrical Contractor |
|---|---|---|---|
| Fan Wall manufacture | ✅ | | |
| Fan Wall FAT (L1) | ✅ + CxA witness | | |
| Fan Wall deliver | ✅ | | |
| **Fan Wall set in place** | ✅ | | |
| Fan Wall ductwork / containment connections | | ✅ | |
| **Fan Wall power connections** | | | ✅ |
| Fan Wall BMS connections | ✅ | | |
| L2 PFC (Fan Wall) | ✅ | | |
| **L3 Fan Wall Functional** | ✅ (lead) | | ✅ support (power) |

**On the reference project:** The cooling-commissioning contractor procures Fan Walls but does NOT install. Installer is TBD as of v4.15 — flag as open item.

---

## Rack Install Scope (Owner-Direct)

| Activity | Owner / Owner's IT Vendor | Other |
|---|---|---|
| Rack manufacture / ship | ✅ | |
| Rack physical install | ✅ | |
| Rack power-up (PDU connections) | ✅ | Electrical may witness |
| Rack network cabling | ✅ | |
| Rack IT load test | ✅ | |
| FA gate | ✅ (acceptance) | |

**Typical rack install duration:** 4 weeks per DH (the client on the reference project). Varies widely — confirm with owner.

---

## Inspectors / AHJ

| Inspection | Owner | Trigger |
|---|---|---|
| Electrical rough-in | Local AHJ | Post-pull, pre-conceal |
| Electrical final | Local AHJ | Pre-L3 energization |
| Mech rough-in | Local AHJ | Post-pipe install, pre-conceal |
| Mech final | Local AHJ | Pre-L3 commissioning |
| Fire alarm | Local AHJ + fire marshal | Pre-TCO |
| Sprinkler / fire suppression | Local AHJ + fire marshal | Pre-TCO |
| Building final | Local AHJ | Pre-TCO |
| TCO issuance | Local AHJ | After all above pass |

**Schedule notes:**
- AHJ inspections are usually 0-duration milestones with `CS_MSOA` constraints (Start On or After) tied to ready-for-inspection activities.
- Document the AHJ for each inspection — different jurisdictions have different scopes (e.g., NY State vs Town).

---

## Commissioning Authority (CxA) — Third Party

The CxA is a **third-party** entity (not the GC, not the trade contractors) hired by the owner to witness and verify commissioning. On hyperscale DCs:

- **L1 FAT** — CxA may witness at factory
- **L2 PFC** — CxA spot-checks
- **L3 Functional** — CxA witnesses + signs off
- **L4 IST** — CxA leads or co-leads with GC
- **L5 Load Bank** — CxA leads

The CxA signs off on the **L3/L4/L5 completion certificates** which gate EFA / FA / PCO. Make sure they're booked early in the project — CxA availability is often a hidden critical-path driver.

---

## Common Confusion Points (Read These Twice)

1. **"Mech contractor" is NOT one entity.** It's usually Install (the mechanical contractor) + Commissioning (the cooling-commissioning contractor). They're different scopes, different schedules, different invoices.

2. **CDUs are NOT installed by the mech contractor.** Separate vendor. Get the vendor name early.

3. **Fan Walls are NOT installed by the mech contractor.** Same as CDUs — vendor-specific.

4. **L3 commissioning is owned by the trade**, but witnessed by the CxA. The signoff certificate is the CxA's.

5. **Rack install is owner scope.** Don't put it under the GC trade. The client on the reference project — different name on every project.

6. **Flush & Fill is commissioning scope, not install scope.** It's where fluid first enters the system, which means it's commissioning. Owned by the cooling commissioning trade (the cooling-commissioning contractor on the reference project).

7. **AFEED/BFEED energization** is **utility company scope**, not the electrical contractor. The electrical contractor may coordinate, but the date is owned by the utility. Track separately.

---

## Template: Trade Responsibility Matrix

For each activity in the schedule, document:

| Activity ID | Activity Name | Lead Trade | Supporting Trades | Witness/CxA |
|---|---|---|---|---|
| CONS-DH4-MR-1000 | MV SWGR Set | Electrical contractor | Rigger | — |
| CONS-DH4-MR-5020 | Flush & Fill | Cooling-commissioning contractor | Mechanical contractor | CxA |
| CX-DH4-L3-CDU | L3 CDU Functional | CDU Vendor | Cooling-commissioning contractor, electrical contractor | CxA |
| CX-DH4-L5-LB | L5 Load Bank | CxA | Electrical contractor, client | Owner witness |
| ... | | | | |

Maintain this as a separate spreadsheet, or roll into the schedule narrative.

---

## How to use this on a new project

1. **Phase 1:** Identify the trades. Get the contract documents that name each contractor.
2. **Phase 2:** Build the project-specific Trade Responsibility Map (table above) by walking each activity and naming the lead trade.
3. **Phase 3:** Use this map to validate logic ties — if an activity is owned by Trade X but its predecessor is owned by Trade Y, make sure the handoff is explicit.
4. **Phase 5:** Use the map to send discipline-specific questions (e.g., "Mech Team Questions", "Electrical Team Questions") for trade meetings.
5. **Phase 7:** Include the map in the final narrative.
