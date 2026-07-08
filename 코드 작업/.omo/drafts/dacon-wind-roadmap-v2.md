# Draft: dacon-wind-roadmap-v2

## Intent
- intent: clear
- review_required: false

## Decisions
- slug: dacon-wind-roadmap-v2
- priority_strategy: sequential (P1→P2→P3→P4→P5)
- code_structure: split notebooks (01_feature_engineering, 02_modeling, etc.)
- validation_strategy: temporal_cv

## Status
- status: approved
- pending_action: write .omo/plans/dacon-wind-roadmap-v2.md
- approved_at: 2026-07-08

## Ledger
- Research completed: 26 notebooks explored, actual data files sampled (LDAPS, GFS, SCADA, labels)
- Evidence: SCADA vestas (157,820 rows, 12 turbines) and unison (105,265 rows, 5 turbines) unused; LDAPS 16 grids only 3 used; GFS upper-air unused; Group 3 label 33% missing linearly interpolated
- Baseline score: 0.60154 (3-model ensemble + SCADA bias correction + spatial gradient + fake answer removal)

## Scope
- IN: 6 sequential waves implementing the recommended roadmap
- OUT: No new model architectures (keep XGBoost/LightGBM ensemble); no deep learning; no real-time inference
