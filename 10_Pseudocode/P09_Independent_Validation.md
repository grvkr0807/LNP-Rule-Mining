# P09. Independent source-disjoint in vitro validation of the frozen Case-1 rulebook

## Scope

Independent validation is a retrospective rulebook evaluation. The final predictive models are not refit or evaluated on this partition as a second model-selection stage. The Case-1 rulebook, its 1,025 rule conditions, interval semantics, mining parameters and Development ranking are frozen before the validation partition is opened.

## Inputs

- `06_Rule_Mining/01_Final_Rulebooks/KMeans_Stratified_LightGBM/` frozen primary rulebook and bin/condition definitions.
- Standard-k-means in vitro validation rows and 420-feature QC matrix from `01_Data/`.
- Development rule coverage/mask summaries needed for integrity comparison.
- Outputs and audit records under `07_Independent_Validation/`.

## A. Integrity barrier

```text
LOAD frozen Case-1 rulebook
ASSERT number of rules = 1025
RECORD rule IDs, ranks, condition order, numeric lower/upper bounds,
       inclusivity flags, categorical conditions and development support/positive counts
HASH frozen rulebook representation

ONLY NOW load the independent validation feature matrix and labels
MATCH every rule feature by exact name to the validation 420-feature schema
IF any required feature is missing or duplicated:
    STOP
```

No validation information may alter the rulebook.

## B. Apply frozen rules unchanged

```text
FOR each frozen rule R in Development rank order:
    mask_val_R <- TRUE for all validation rows
    FOR condition q in R in frozen condition order:
        IF q is continuous interval:
            APPLY exact stored lower/upper value and inclusivity flags
        ELSE IF q is categorical/binary:
            APPLY exact stored category/state condition
        END IF
        mask_val_R <- mask_val_R AND condition_mask
    END FOR

    support_val_R <- count(mask_val_R)
    positives_val_R <- sum(y_val[mask_val_R])
    evaluable_R <- support_val_R > 0
END FOR
```

Do not recompute quantiles, relabel conditions, re-mine candidates, change support/precision thresholds, re-prune, discard unfavorable evaluable rules, or rerank by validation performance. A zero-support rule is recorded as non-evaluable rather than treated as a failed rule.

## C. Source-adjusted expectation

Validation sources can have different baseline positive rates. Source adjustment compares each rule's observed positive count to the positive count expected from the exact mixture of validation sources covered by that rule.

```text
FOR validation source s:
    p0_s <- positives_in_source_s / rows_in_source_s
END FOR

FOR rule R:
    FOR source s:
        n_Rs <- number of validation rows from s satisfying R
        y_Rs <- positive validation rows from s satisfying R
    END FOR

    N_R <- sum_s n_Rs
    O_R <- sum_s y_Rs
    E_R <- sum_s (n_Rs * p0_s)

    observed_precision_R <- O_R / N_R                     if N_R > 0
    expected_precision_R <- E_R / N_R                     if N_R > 0
    adjusted_uplift_R <- observed_precision_R - expected_precision_R
    adjusted_lift_R <- O_R / E_R                          if E_R > 0
END FOR
```

If `N_R=0`, the rule is non-evaluable. If `E_R=0`, source-adjusted lift is undefined and must not be replaced by an arbitrary finite value; retain the observed/expected counts and handle the undefined metric explicitly.

## D. Frozen rank-window summaries

```text
WINDOWS = {Top10, Top25, Top50, Top100, All}
FOR window W defined by ORIGINAL Development rank:
    evaluable_W <- rules in W with validation support > 0
    REPORT:
        number and fraction evaluable
        fraction of evaluable rules with adjusted_lift > 1
        median adjusted lift
        corresponding source-adjusted uplift summaries
    COMPUTE Development-vs-Validation Spearman association using the same
        evaluable frozen rules and the deposited development/validation rule quantities
END FOR
```

Do not redefine Top-N after removing non-evaluable rules. For example, Top-50 means the original Development ranks 1–50, of which a subset may be evaluable in validation.

## E. Rulebook-union coverage

```text
union_mask <- OR of masks for the specified frozen rule set
CALCULATE overall and source-wise union coverage
REPORT separately from rule enrichment
```

Union coverage is a descriptive coverage diagnostic. It is not a classifier prediction, and it is not converted into accuracy/Macro-F1.

## Integrity audit

The files in `07_Independent_Validation/Integrity_Audit/` verify row alignment, QC-vs-pre-QC feature state, feature distributions, validation label semantics, development rule recalculation, selected rule matches and post-write integrity. A valid rerun must reproduce these consistency checks before interpreting enrichment results.

Key expected scope checks include a frozen 1,025-rule primary rulebook and no rulebook modification after validation access. The exact count of evaluable versus zero-support rules is read from the deposited validation output rather than used as an optimization target.
