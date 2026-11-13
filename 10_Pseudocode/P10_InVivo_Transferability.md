# P10. Retrospective in vivo feature and rule transferability

## Scope

The in vivo analysis is an external-domain transferability assessment. It does not feed back into in vitro model selection, feature refinement, rule-mining sensitivity, or independent in vitro validation. Two complementary questions are evaluated: whether in vitro-selected feature sets retain predictive information in vivo, and whether the frozen primary in vitro rulebook identifies enriched in vivo regions.

## Inputs

- independently curated 1,873-record in vivo snapshot and in vivo source-relative labels under `01_Data/04_InVivo_Labels/`;
- in vivo pre-QC/QC feature matrices under `01_Data/06_Feature_Matrices_InVivo/` (`863 -> 367` features);
- label-matched in vitro LightGBM hyperparameters;
- exact in vitro Phase-1, Phase-2 and final Phase-3 feature identities;
- frozen 1,025-rule Case-1 in vitro rulebook.

Outputs are under `08_InVivo_Transferability/`.

## A. In vivo labeling and analysis set

Apply the same source-wise standard k-means / HC10 / HC20 definitions as P01 to the retained primary in vivo readouts (normalized luminescence, normalized peptide abundance, and normalized protein abundance). The complete in vivo analysis branch is retained as a single modeling set rather than forcing an in vitro-style source-disjoint hyperparameter/development/validation split that would confound source and readout composition.

```text
CREATE standard, HC10 and HC20 in vivo labels using P01 definitions
DO NOT use in vivo uptake as a primary modeling endpoint
FEATURIZE with P02-compatible descriptor definitions
APPLY in vivo QC state -> 367-feature QC representation
CREATE fixed five-fold stratified assignments for each label branch, random_state=42
```

## B. Predictive feature-transfer evaluation

No in vivo hyperparameter search is performed.

```text
FOR label in {standard, HC10, HC20}:
    params <- corresponding in vitro LightGBM hyperparameters
    folds <- fixed in vivo five-fold stratified assignments

    # unrestricted in vivo reference
    EVALUATE LightGBM on all 367 in vivo QC features

    FOR stage in {Phase1, Phase2, Phase3}:
        requested_features <- exact in vitro selected feature names for this label/case
        matched_features <- exact-name intersection with in vivo 367-feature schema
        missing_features <- requested_features not found in vivo
        RECORD compatibility table; never substitute an approximate descriptor
        EVALUATE model on matched_features using the SAME folds and reused params
        RECORD fold metrics and OOF predictions
    END FOR
END FOR
```

The comparison asks how much performance remains after imposing the in vitro-selected feature universe. It does not claim that the in vitro sets are globally optimal for in vivo prediction; the unrestricted 367-feature baseline is the reference for that distinction.

All final Phase-3 descriptors used for the standard, HC10 and HC20 transfer analyses are present in the in vivo representation. The standard and HC10 final sets contain 15 descriptors and HC20 contains 14.

## C. Frozen rulebook transfer

Rule transfer is separate from the predictive-model comparison and uses the standard-label in vivo branch.

```text
LOAD frozen Case-1 in vitro rulebook with all 1025 rules and original Development ranks
LOAD standard-label in vivo QC feature matrix
MATCH every rule feature by exact name

FOR each rule R:
    APPLY exact stored continuous bounds/inclusivity and categorical states
    DO NOT recalculate in vivo quantiles
    DO NOT re-bin, re-mine, re-rank, prune or tune the rulebook
    COMPUTE in vivo support and positive count
    mark zero-support rule as non-evaluable
END FOR
```

## D. Source-adjusted in vivo enrichment

Use the same source-mixture expectation as P09, but calculate baseline prevalence from the in vivo source proxy used by the transfer analysis.

```text
FOR in vivo source/proxy group s:
    p0_s <- positives_s / rows_s
END FOR

FOR rule R:
    n_Rs <- covered rows from source s
    y_Rs <- covered positives from source s
    O_R <- sum_s y_Rs
    E_R <- sum_s n_Rs * p0_s
    observed_precision_R <- O_R / sum_s n_Rs
    expected_precision_R <- E_R / sum_s n_Rs
    adjusted_uplift_R <- observed_precision_R - expected_precision_R
    adjusted_lift_R <- O_R / E_R when E_R > 0
END FOR
```

Summaries use the frozen Development rank windows Top-10, Top-25, Top-50, Top-100 and all rules, retaining the original window membership even when some rules have zero in vivo support. Development-to-in-vivo Spearman association is computed among the same evaluable frozen rules.

## E. Integrity and interpretation checks

1. No in vivo tuning or feature selection is allowed.
2. All transferred feature names are matched exactly; missing features are reported, not imputed or substituted.
3. The same in vivo folds are used across baseline/Phase-1/Phase-2/Phase-3 comparisons within a label so performance differences are paired to a common split realization.
4. The frozen Case-1 rule conditions/ranks are unchanged and in vivo quantiles are never substituted for in vitro bin boundaries.
5. Feature-level and rule-level transfer conclusions remain separate.
6. Treat the analysis as retrospective cross-domain transferability, not as prospective experimental validation.
7. Compare generated outputs to `01_Baseline_Model_Evaluation/`, `02_Feature_Transfer/`, `03_Rulebook_Transfer/`, and `04_Main_Figure_Source_Data/`.
