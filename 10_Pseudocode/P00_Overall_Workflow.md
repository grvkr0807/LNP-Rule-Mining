# P00. End-to-end computational workflow

## Purpose

This module specifies the stage order, data-access barriers, handoff objects, and integrity checks for the complete SAR NM Iterative analysis. The stage-specific algorithms are defined in P01–P10. All file paths shown here are paths inside this public archive unless explicitly written as `<PROJECT_ROOT>`, which denotes the private project root used when the original calculations were executed.

## Primary inputs

- `01_Data/01_Curated_Snapshots/Cleaned_Data_17116.csv`: frozen 17,116-record curated study snapshot.
- Exact in vitro and in vivo label/partition files under `01_Data/`.
- Portable pre-QC and QC feature matrices and ordered feature schemas under `01_Data/05_Feature_Matrices_InVitro/` and `01_Data/06_Feature_Matrices_InVivo/`.
- Frozen chemistry-group assignments under `01_Data/07_Chemistry_Grouping/`.
- Software versions and environment specifications under `00_Environment/`.

## Global constants and barriers

- Project random state: `42` wherever a stochastic operation supports a random state.
- In vitro validation data are inaccessible to tuning, model selection, feature refinement, SHAP ranking, and rule mining. They are opened only after the primary Case-1 rulebook and its ranking have been frozen.
- In vivo data are not used to select any in vitro model, feature set, rule-mining parameter, or rule ranking.
- The publication workflow includes only the adopted global-SHAP Phase-3 compression. Exploratory compression strategies that were not adopted are not part of this specification.
- Exact deposited folds, group assignments, selected feature lists, thresholds, and hashes take precedence over regenerating those states from library defaults.

## Algorithm

```text
INPUT curated_snapshot = 01_Data/01_Curated_Snapshots/Cleaned_Data_17116.csv

# Stage A: data and labels
CALL P01 on curated_snapshot
ASSERT in vitro source-relative standard, HC10 and HC20 label files exist
ASSERT source-disjoint in vitro partition files exist
ASSERT validation rows have not been loaded by downstream development stages

# Stage B: feature representation
CALL P02 on the frozen labeled/partitioned datasets
ASSERT ordered in vitro feature count before QC = 881
ASSERT ordered in vitro feature count after QC = 420
ASSERT the same learned QC mask/order is applied to all in vitro labels and partitions

# Stage C: redundancy and chemistry grouping
CALL P03 on standard-k-means development data only where specified
LOCK strict correlation rescue structure at joint |Pearson| and |Spearman| threshold 0.99
LOCK fingerprint group assignment at Morgan radius 2, 2048 bits, chirality enabled,
     Tanimoto similarity threshold 0.70

# Stage D: pre-refinement model selection
CALL P04
LOCK five downstream robustness cases:
  Case 1 = standard k-means + stratified CV + LightGBM
  Case 2 = HC10 + stratified CV + LightGBM
  Case 3 = HC20 + stratified CV + LightGBM
  Case 4 = standard k-means + fingerprint-grouped CV + LightGBM
  Case 5 = standard k-means + stratified CV + class-weighted random forest

# Stage E: hierarchical feature refinement
FOR case in Cases 1..5:
    CALL P05  # Phase 1 coarse refinement
    VERIFY selected Phase-1 feature names/hash and associated hyperparameter state
    CALL P06  # Phase 2 exhaustive descriptor-class refinement
    VERIFY selected Phase-2 feature names/classes/hash
    CALL P07  # Phase 3 global-SHAP compression + exhaustive feature refinement
    VERIFY final selected feature names/hash
END FOR

ASSERT final Phase-3 feature counts = [15, 15, 14, 7, 13] for Cases 1..5

# Stage F: rule mining
CALL P08
LOCK common final rule-mining parameters:
    bins = 6
    min_support = 50
    min_precision = 0.65
    lambda = 0.5
    maximum_rule_order = 4
VERIFY retained rulebooks exist for all five cases

# Stage G: independent validation
OPEN the previously reserved in vitro validation partition
CALL P09 on the frozen Case-1 rulebook only
ASSERT no rule condition, bin boundary, rule rank, mining threshold or pruning decision changed

# Stage H: in vivo transferability
CALL P10 using the independently curated in vivo branch
ASSERT no in vivo information feeds back into Stages A-G

# Final audit
VERIFY manuscript/table/figure source data map to deposited result artifacts
VERIFY MANIFEST.csv lists every public artifact except MANIFEST.csv/checksums.sha256 themselves
VERIFY each manifest size/hash equals the current file bytes
VERIFY checksums.sha256 validates every file except itself
VERIFY no proprietary implementation source file is present
VERIFY no private absolute project path remains in public files
OUTPUT public reproducibility archive
```

## Required outputs and audit locations

The public package is organized so that a reimplementation can be compared at every handoff rather than only at the final figures. Decision-driving outputs are under `02_Model_Selection/` through `08_InVivo_Transferability/`; publication source data are under `09_Figure_Table_Source_Data/`; provenance and scope statements are under `11_Documentation/`.

## Failure conditions

Stop the workflow if a required feature name cannot be matched exactly, a frozen row/fold/group assignment differs from the deposited assignment, a feature-order/hash check fails, validation is accessed before all development decisions are frozen, or a generated stage changes a prior locked state without an explicitly documented retuning step.
