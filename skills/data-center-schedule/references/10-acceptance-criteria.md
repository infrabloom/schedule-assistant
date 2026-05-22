# Acceptance Criteria -- When Is the Build Done?

Definition-of-done checklists for a DC schedule build. Use them at the Phase 6/7
gate and at every weekly refresh. Nothing ships until the relevant list is fully
checked or every exception is explicitly flagged and accepted.

## Phase exit gates (summary)

Each phase has a checkpoint; see `01-phased-workflow.md` for detail.

- **Phase 2 done:** one extraction note per source file; conflicts flagged.
- **Phase 3 done:** WBS locked; activity catalog with a source cited per row;
  predecessor logic per discipline; assumptions register started. Checkpoint.
- **Phase 4 done:** first Data Hall fully built; `validate_xer.py` passes.
- **Phase 5 done:** all DHs + Admin replicated with the confirmed stagger;
  actuals applied where source data exists.
- **Phase 6 done:** the build-complete list below is fully checked.
- **Phase 7 done:** the delivery-complete list below is fully checked.

## Build complete (Phase 6)

- [ ] `validate_xer.py` exits 0 -- all 21 FAIL checks pass.
- [ ] `cohesion_audit.py` exits 0 -- no orphans, every chain reaches a milestone.
- [ ] `duplicate_audit.py` shows no hard (code) duplicates.
- [ ] Every WARN from `validate_xer.py` is reviewed and accepted or fixed.
- [ ] Every activity traces to a source (trade schedule, MEL, the contract
      milestone schedule, locked draft, or a documented first-principles assumption).
- [ ] Every procurement activity ties to a construction or commissioning
      successor (or a milestone, only where the contract requires it directly).
- [ ] Each contractual milestone's predecessor pattern is consistent across all
      areas (the first-built DH is the reference).
- [ ] No cross-area crew chains forcing serial execution (stagger via dates).
- [ ] Trade-reported durations sanity-checked against `08-duration-benchmarks.md`.

## Delivery complete (Phase 7)

- [ ] All build-complete items above.
- [ ] XER imports into OPC with no PRM-009010001 and no dropped activities
      (imported count == TASK-row count).
- [ ] Forecast milestone dates reviewed against contractual dates; every
      predicted miss is flagged.
- [ ] Critical path traced per contractual milestone.
- [ ] Deliverables produced: versioned XER, schedule narrative, PM briefing,
      assumptions register, open-items list, critical-path analysis.
- [ ] Version incremented; no delivered XER overwritten.

## Weekly refresh complete

- [ ] Trade files (the electrical and mechanical contractors) diffed against last week's version.
- [ ] Actuals transferred; durations/logic updated only where the trade changed
      their source of truth, with deviations flagged.
- [ ] `validate_xer.py` and `cohesion_audit.py` both pass; no new orphans.
- [ ] One-page change log produced.
