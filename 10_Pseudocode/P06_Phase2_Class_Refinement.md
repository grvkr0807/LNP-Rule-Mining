# P06. Phase 2 exhaustive descriptor-class refinement

## Inputs

- Phase-1 selected handoff for each case from P05.
- Frozen 420-feature-to-class mapping under `04_Phase2_Fine_Refinement/01_Descriptor_Class_Taxonomy/`.
- Dedicated hyperparameter partition and case-specific CV strategy.
- Frozen development folds/groups.

## Frozen descriptor taxonomy

Each QC feature has exactly one assignment in the following practical organizational taxonomy:

`C01` Size and Shape; `C02` Topology; `C03` Elements and Functional Groups; `C04` Polarity; `C05` Lipophilicity; `C06` Molar Refractivity; `C07` Electrostatics; `C08` EState; `C09` Rings and Aromaticity; `C10` Composite/Fingerprint; `C11` Composition; `C12` Experimental Context.

The mapping is frozen before case-specific search. Classes are organizational domains and are not assumed to be statistically orthogonal.

## One-time post-Phase-1 retuning

```text
FOR case in Cases 1..5:
    phase1_features <- exact names from P05 handoff
    ASSERT every name maps to one and only one frozen class

    X_hp <- hyperparameter-partition columns phase1_features
    cv_hp <- case-specific five-fold strategy
    RUN RandomizedSearchCV using the established model-specific search space,
        up to 100 candidates, Macro-F1 refit, random_state=42
    params_phase2[case] <- best parameters
    FREEZE params_phase2[case] for every class combination
END FOR
```

No class combination is tuned independently.

## Exhaustive class enumeration

Let `R_case` be the sorted set of classes represented by the Phase-1 handoff. The represented class counts are `[10, 11, 11, 10, 10]`, so the numbers of nonempty combinations are `[1023, 2047, 2047, 1023, 1023]`, totaling `7,163` combinations and `35,815` five-fold model fits.

```text
FOR case:
    represented_classes <- sorted(unique(class_of(f) for f in phase1_features))
    combinations <- all nonempty subsets of represented_classes
    ORDER combinations deterministically by the project's combination-ID convention

    FOR combination in combinations:
        feature_subset <- [f in phase1_features if class_of(f) is in combination]
        PRESERVE Phase-1 feature order

        FOR fold in frozen development folds:
            FIT case model using params_phase2[case]
            PREDICT held-out fold
            RECORD fold Macro-F1, BalAcc, AUROC, AUPRC and companion metrics
        END FOR

        aggregate[combination] <- five-fold means/SDs
        STORE class IDs, exact feature names/count, combination ID and metrics
    END FOR
END FOR
```

There is no SHAP calculation, validation access, feature-level pruning, or per-combination hyperparameter optimization during this exhaustive search.

## Reference-only repeated CV and threshold

```text
numerical_best <- combination with maximum ORIGINAL five-fold mean Macro-F1
resolve exact ties deterministically using the recorded combination ordering

EVALUATE numerical_best only using 10 repetitions x 5 development folds
FOR repeat h:
    repeat_mean[h] <- mean of five fold Macro-F1 values
END FOR
SE_best <- sample_sd(repeat_mean[1..10]) / sqrt(10)

T <- original_five_fold_mean_MacroF1[numerical_best] - SE_best

FOR every exhaustive combination c:
    qualified[c] <- original_five_fold_mean_MacroF1[c] >= T
END FOR

minimum_feature_count <- min(n_features[c] for qualified c)
smallest <- qualified combinations with n_features == minimum_feature_count
SELECT final Phase-2 candidate from smallest by:
    1. higher original five-fold Macro-F1
    2. fewer retained classes
    3. deterministic combination ID
```

Alternative combinations are **not** re-evaluated with repeated CV. Their original five-fold means are compared directly to the threshold defined from the numerical-best reference.

## Locked Phase-2 outputs

The final Phase-2 selected pools contain `31, 41, 42, 12, 26` individual features for Cases 1–5, respectively. These exact pools—not a reconstructed class-only description—are the input to P07.

Use `04_Phase2_Fine_Refinement/03_Candidate_Selection/` to audit numerical-best IDs, repeated-CV reference summaries, thresholds, qualifying combinations, and recommended Phase-3 class combinations.

## Post-hoc analyses

All post-hoc Phase-2 analyses are read-only with respect to candidate selection:

- performance–complexity summaries from the exhaustive table;
- matched marginal contribution for classes retained in the selected candidate;
- matched second-order predictive interaction `Delta_ij(S) = f(S+i+j)-f(S+i)-f(S+j)+f(S)` over admissible backgrounds;
- class recurrence, Jaccard similarity and symmetric core retention across cases.

Negative second-order interaction indicates antagonism/diminishing returns and is not automatically labeled redundancy.

## Integrity checks

1. Every Phase-1 handoff feature maps to exactly one frozen class.
2. Combination counts match `1023/2047/2047/1023/1023`.
3. All combinations in a case use identical post-Phase-1 hyperparameters and frozen folds.
4. Only the numerical-best reference has a 10x5 repeated-CV record.
5. Generated threshold and recommendation match the deposited candidate-selection summaries and hashes.
6. Validation is never loaded.
