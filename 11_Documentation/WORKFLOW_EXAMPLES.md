# Workflow examples and artifact relationships

This document provides stage-level examples showing how the deposited inputs and outputs correspond to the published workflow. It is intentionally implementation-independent; algorithmic details are given in `10_Pseudocode/` and the manuscript/Supporting Information.

## Example 1 — reproduce the input state for the primary model
1. Start from `01_Data/03_InVitro_Partitions/Activity_KMeans_development.xlsx`.
2. Use the exact QC matrix `01_Data/05_Feature_Matrices_InVitro/QC_Feature_Matrix_KMeans_development.npz` and its ordered schema `Feature_Schema_QC_420.csv`.
3. The matrix contains the same 10,391 Development formulations represented by 420 QC-retained features.
4. Model-selection outputs are in `02_Model_Selection/` and the corresponding algorithmic specification is `10_Pseudocode/P04_Model_Tuning_and_Benchmarking.md`.

## Example 2 — audit the Phase 1 handoff for Case 1
1. Inspect the 25-iteration Case-1 trajectory under `03_Phase1_Coarse_Refinement/02_Case_Trajectories/`.
2. Inspect the resolved Pareto and repeated-CV candidate outputs under `03_Phase1_Coarse_Refinement/04_Candidate_Selection/KMeans_Stratified_LightGBM/`.
3. `Recommended_Phase2_Features.csv` contains the exact 69-feature Phase-1 handoff.
4. Selection logic is specified in `10_Pseudocode/P05_Phase1_Coarse_Refinement.md`.

## Example 3 — audit Phase 2 exhaustive class refinement
1. The Phase-1 feature-to-class mapping and exact class-combination definitions are under `04_Phase2_Fine_Refinement/`.
2. For Case 1, `Aggregate_Combination_Metrics.csv` contains 1,023 nonempty class combinations and `Foldwise_Combination_Metrics.csv` contains their five-fold results.
3. Candidate qualification and the exact selected Phase-2 handoff are under `04_Phase2_Fine_Refinement/03_Candidate_Selection/KMeans_Stratified_LightGBM/`.
4. The same structure applies to Cases 2–5.

## Example 4 — audit Phase 3 compression and final selection
1. Final global-SHAP compression outputs for Cases 1, 2, 3 and 5 are under each case's `Global_SHAP_Compression_Outputs/` directory. Case 4 retains its complete 12-feature Phase-2 pool without compression.
2. Final retuned hyperparameters and exhaustive-run fold/configuration information are under `05_Phase3_Finest_Refinement/02_Final_Retuning/` and `03_Exhaustive_Refinement_Config/`.
3. Numerical-best repeated-CV results, screening thresholds, threshold-qualified candidates and final feature sets are under `04_Candidate_Selection/`.
4. Complete per-subset evaluation tables are intentionally omitted from the public package as large derived computational intermediates. The exact locked feature pools, fold assignments, hyperparameters, exhaustive-run configuration, candidate-selection outputs, and detailed pseudocode define the computational state required to regenerate these tables. Editors and referees are additionally provided separate executable access for direct reproduction of the workflow.

## Example 5 — audit a frozen Case-1 rule in independent validation
1. Load `06_Rule_Mining/01_Final_Rulebooks/KMeans_Stratified_LightGBM/Retained_Rulebook.csv` and choose the desired frozen rank.
2. The exact rule conditions and Development statistics are contained in the rulebook and associated condition/bin files.
3. Locate the same rule in `07_Independent_Validation/Source_Adjusted_Validation/Rule_Level_Source_Adjusted_Validation.csv`.
4. Source-specific support is available in `Rule_By_Source_Validation.csv`, and source baselines are in `Source_Baselines.csv`.
5. Rank-window summaries are in `Source_Adjusted_Summary_by_Rank_Window.csv`.

## Example 6 — audit in vivo transferability
1. Use the exact 367-feature in vivo QC matrix under `01_Data/06_Feature_Matrices_InVivo/`.
2. Feature-level transfer results for Baseline and Phases 1–3 are under `08_InVivo_Transferability/02_Feature_Transfer/`.
3. Rule-level transfer of the unchanged 1,025-rule Case-1 rulebook is under `08_InVivo_Transferability/03_Rulebook_Transfer/`.
4. The exact source data used for the main in vivo trajectory figure are in `09_Figure_Table_Source_Data/Main_Manuscript/Figure8_InVivo_Feature_Transfer_MacroF1.csv`.
