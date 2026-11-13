# P07. Phase 3 global-SHAP compression and exhaustive individual-feature refinement

## Publication scope

This specification contains only the adopted Phase-3 workflow used for the published analysis.

## Inputs

- Exact Phase-2 selected feature pools containing `31, 41, 42, 12, 26` features for Cases 1–5.
- Case-specific hyperparameter partition and CV strategy.
- Frozen development folds/groups.
- `05_Phase3_Finest_Refinement/01_Feature_Compression/` through `04_Candidate_Selection/` for exact audit artifacts.

## A. Retune the uncompressed Phase-2 reference

```text
FOR case:
    phase2_pool <- exact ordered Phase-2 feature names
    VALIDATE names/count/hash
    RETUNE the case model once on the hyperparameter partition using phase2_pool
    FREEZE these post-Phase-2 parameters for the compression comparison
END FOR
```

## B. Compute one global held-out-fold SHAP ranking

For each case, fit the uncompressed Phase-2 reference on each frozen development fold and calculate TreeSHAP **main effects** on the corresponding held-out rows. SHAP interaction values are not recalculated for compression.

Let `phi[i,p,l]` be the SHAP main-effect contribution of feature `p` for held-out formulation `i` from fold `l`. Aggregate importance as the mean absolute held-out contribution over all held-out rows/folds.

```text
FOR case:
    INITIALIZE sum_abs_shap[p] and heldout_count
    FOR frozen development fold l:
        FIT reference model using full phase2_pool and frozen post-Phase-2 params
        CALCULATE SHAP main effects on held-out rows only
        ACCUMULATE abs(SHAP) per feature
    END FOR
    Omega[p] <- accumulated absolute SHAP / heldout_count
    global_rank <- feature names sorted by Omega descending with deterministic tie handling
    WRITE ranking and reference metrics
END FOR
```

## C. Top-N compression comparison

Case 4 has only 12 Phase-2 features and therefore skips preliminary compression. For Cases 1, 2, 3 and 5:

```text
FOR N in {14,15,16,17,18}:
    topN <- first N names from the ONE previously calculated global_rank
    FOR frozen development fold:
        FIT/EVALUATE model on topN using the SAME fixed post-Phase-2 parameters
    END FOR
    STORE aggregate metrics
END FOR

EVALUATE the full uncompressed Phase-2 reference in the same workflow
DO NOT recalculate SHAP for any Top-N set
DO NOT retune separately for N=14..18
```

The adopted computational handoff is:

- Cases 1, 2, 3 and 5: global SHAP Top-18;
- Case 4: all 12 Phase-2 features.

Thus the locked exhaustive-search pools are `18/18/18/12/18` features.

## D. Final retuning on the locked pools

```text
FOR case:
    locked_pool <- Top18 or all-12 as specified above
    ASSERT exact names/order/count/hash match deposited selected-features file
    RETUNE model once on the dedicated hyperparameter partition
    params_phase3[case] <- selected final parameters
    FREEZE params_phase3[case] for every individual-feature subset
END FOR
```

## E. Exhaustive individual-feature enumeration

```text
FOR case:
    p <- number of features in locked_pool
    ASSERT p in {18,12}
    total_combinations <- 2^p - 1

    REPRESENT each nonempty subset by deterministic bit mask / combination ID
    FOR combination_id in deterministic nonempty-mask order:
        feature_subset <- locked_pool features whose bits are set
        PRESERVE locked-pool order
        FOR fold in frozen case-specific development folds:
            FIT case model using params_phase3[case]
            PREDICT held-out fold
            RECORD Macro-F1, BalAcc, AUROC, AUPRC and companion metrics
        END FOR
        STORE aggregate five-fold metrics and exact feature identities
    END FOR
END FOR
```

Expected search sizes are `262,143` subsets for each 18-feature case and `4,095` for Case 4, totaling `1,052,667` subsets and `5,263,335` five-fold fits. No subset-specific hyperparameter tuning, SHAP calculation, fitted-model serialization, or validation access is permitted.

## F. Reference-only repeated CV and selection

```text
numerical_best <- subset with highest ORIGINAL five-fold mean Macro-F1
EVALUATE numerical_best only with shared 10 x 5 development CV
repeat_mean[h] <- mean Macro-F1 across five folds of repeat h
SE_best <- sample_sd(repeat_mean[1..10]) / sqrt(10)
T <- original_five_fold_mean[numerical_best] - SE_best

FOR every exhaustive subset c:
    qualified[c] <- original_five_fold_mean[c] >= T
END FOR

min_size <- minimum feature count among qualified subsets
smallest <- qualified subsets with feature count == min_size
SELECT recommendation by:
    1. higher original five-fold mean Macro-F1
    2. deterministic/lexicographic combination ID
```

A threshold-qualified candidate is not automatically a mathematical minimal indistinguishable set. The publication selection is the **smallest qualifying candidate** under the rule above unless subset-minimality has been separately established.

## Locked final feature counts

Compare reproduced recommendations to `Recommended_Final_Feature_Sets.csv`:

- Case 1: 15 features;
- Case 2: 15 features;
- Case 3: 14 features;
- Case 4: 7 features;
- Case 5: 13 features.

## G. Read-only post-hoc analyses

- Pairwise second-order interactions are calculated from the complete locked Phase-3 pool using existing exhaustive subset metrics.
- Marginal contribution is calculated only for features in the final selected set; both the focal feature and every background subset must lie entirely within that final selected set.
- Cross-case feature recurrence, Jaccard similarity and symmetric core retention are calculated directly from final feature identities; an analogous class-level view maps final features back to the frozen Phase-2 taxonomy.

## Integrity checks

1. Confirm the SHAP ranking is calculated once per uncompressed Phase-2 reference and reused for all Top-N sets.
2. Confirm Top-N comparison uses fixed post-Phase-2 hyperparameters and frozen folds.
3. Confirm the locked pool and final retuning files have matching feature hashes.
4. Confirm exhaustive subset counts and candidate IDs are complete.
5. Confirm only the numerical-best subset undergoes repeated CV.
6. Confirm final counts and feature hashes match deposited candidate-selection outputs.
7. Confirm validation is never loaded.
