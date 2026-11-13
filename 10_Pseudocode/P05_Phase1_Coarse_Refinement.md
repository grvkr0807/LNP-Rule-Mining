# P05. Phase 1 coarse, iterative feature refinement and performance-aware handoff

## Inputs

For each of the five cases:

- the 420-feature QC development matrix and ordered schema;
- the case-specific activity labels;
- frozen five-fold development assignments (stratified for Cases 1, 2, 3, 5; fingerprint-grouped for Case 4);
- the case's current hyperparameter dictionary;
- strict joint Pearson/Spearman complete-linkage clusters at threshold `0.99` from P03.

Authoritative outputs are under `03_Phase1_Coarse_Refinement/02_Case_Trajectories/` and `04_Candidate_Selection/`.

## Fixed refinement settings

- initial active feature count: `420`;
- iterations: `1..25`;
- cumulative SHAP main-effect mass target: `0.75`;
- interaction-partner fraction: `0.25` of the currently active width;
- dynamic partner guardrails: minimum `5`, maximum `50`, and never more than `D-1`;
- random state: `42`;
- correlation rescue threshold: joint strict cluster threshold `0.99`;
- retuning occurs after completed iterations `5, 10, 15, 20` and is used by the next block.

## Iteration-state convention

Let `F_e` be the feature set evaluated and stored as Iteration `e`. SHAP used to generate the next state is computed from fold models trained on the immediately preceding active state. Preserve this state alignment exactly; do not label a SHAP-derived next set as though it were the state on which the SHAP values were calculated.

## Main-effect and interaction selection

For active width `D`, aggregate held-out-fold absolute TreeSHAP main effects into `S_mean[j]` and held-out-fold absolute pairwise SHAP interactions into `I_mean[j,k]`. The diagonal of the interaction matrix is excluded from partner selection.

```text
order <- feature indices sorted by S_mean descending
cumulative_mass <- cumulative_sum(S_mean[order]) / sum(S_mean)
m <- smallest index count for which cumulative_mass >= 0.75
main_set <- first m features in order

n_raw <- round(0.25 * D)
n <- max(1, n_raw)
n <- max(n, 5)
n <- min(n, D-1)
n <- min(n, 50)

interaction_set <- empty
FOR anchor in main_set:
    partner_order <- non-anchor features sorted by I_mean[anchor,*] descending
    ADD strongest n partners to interaction_set
END FOR
```

Where ties occur at a practical selection boundary, preserve the project's deterministic feature order and recorded outcome rather than introducing arbitrary random tie breaking.

## Correlation-cluster rescue

The correlation structure is a rescue safeguard only. It must not replace SHAP ranking or delete features in advance.

```text
base_selected <- union(main_set, interaction_set)
threatened <- active features not in base_selected

FOR each strict 0.99 cluster C intersecting the active set:
    active_C <- C ∩ active_features
    threatened_C <- active_C ∩ threatened
    IF threatened_C is empty:
        CONTINUE

    COMPUTE cluster-level SHAP evidence from member main-effect importances,
            using the size-adjusted aggregation recorded by the Phase-1 implementation
    COMPARE cluster evidence with the current main-effect selection boundary

    IF cluster evidence is insufficient:
        rescue none
    ELSE:
        NORMALIZE member SHAP shares within active_C
        effective_contributors <- inverse-Simpson effective count from normalized shares
        rescue_target <- deterministic integer target derived from effective_contributors
        RANK threatened members by member SHAP evidence
        RESCUE strongest members until rescue_target is satisfied,
               retaining tied members at the final boundary when required by the recorded rule
    END IF
END FOR

F_next <- union(base_selected, correlation_rescues)
PRESERVE original QC feature order in F_next
```

The detailed per-iteration rescue outputs and histories in the archive are the exact audit state for this safeguard.

## Full iterative loop

```text
active_features <- all 420 QC features
params <- pre-refinement parameters for the case

FOR e in 1..25:
    folds <- frozen case-specific development folds
    INITIALIZE held-out SHAP accumulators

    FOR each fold l:
        FIT case model using active_features and params on training rows
        EVALUATE on held-out rows; record Macro-F1, BalAcc, AUROC, AUPRC and other metrics
        CALCULATE TreeSHAP main effects on held-out rows only
        CALCULATE pairwise TreeSHAP interactions on held-out rows only
        ACCUMULATE absolute main and interaction values
    END FOR

    AGGREGATE held-out SHAP statistics
    DETERMINE next active set using 75% main mass + 25% interaction partners + strict-correlation rescue
    WRITE feature set, metrics, SHAP summaries, interaction summaries and hashes

    IF e in {5,10,15,20}:
        RETUNE the case model once on the dedicated hyperparameter partition
        using the feature state at the end of this block
        params <- selected retuned parameters for subsequent iterations
    END IF
END FOR
```

## Pareto resolution and repeated-CV selection

Do not use Iteration 25 automatically. Use the complete 25-iteration performance–complexity history.

```text
FOR each observed iteration/state:
    key <- exact ordered feature-name hash + associated hyperparameter-state hash
    collapse only exact duplicate states; do not collapse different feature sets merely
    because feature count and rounded Macro-F1 are equal
END FOR

A state b dominates a when:
    N_b <= N_a AND mean5_b >= mean5_a
    AND at least one inequality is strict
PARETO <- all non-dominated exact states

CREATE one shared 10 x 5 repeated-development-CV assignment per case
FOR every Pareto state e:
    USE the exact feature set and exact hyperparameter dictionary associated with e
    EVALUATE all 50 folds on shared assignments
    FOR repeat h=1..10:
        repeat_mean[e,h] <- mean of the five fold Macro-F1 values in repeat h
    END FOR
    rep_mean[e] <- mean(repeat_mean[e,*])
    sd[e] <- sample standard deviation of the ten repeat means (ddof=1)
    SE[e] <- sd[e] / sqrt(10)
    CI95[e] <- rep_mean[e] +/- t_0.975,9 * SE[e], with t_0.975,9 = 2.262
END FOR

best <- Pareto state with highest rep_mean
T_1SE <- rep_mean[best] - SE[best]
qualified[e] <- upper_CI95[e] >= T_1SE

SELECT among qualified states by:
    1. smallest feature count
    2. higher repeated-CV mean Macro-F1
    3. longer exact recurrence of the same feature/hyperparameter state in the Phase-1 trajectory
    4. earlier representative iteration
```

## Locked handoff audit

The selected Phase-1 handoffs are:

- Case 1: Iteration 10, 69 features;
- Case 2: Iteration 12, 58 features;
- Case 3: Iteration 5, 81 features;
- Case 4: Iteration 22, 52 features;
- Case 5: Iteration 5, 54 features.

Compare generated selections to each case's `Recommended_Phase2_Features.csv`, `Recommended_Phase2_Iteration.json`, Pareto qualification tables, shared repeated-CV assignments, and feature hashes before P06.

## Failure conditions

Stop if SHAP is computed on training rather than held-out fold rows, if a case uses a different development fold realization, if a Pareto candidate is evaluated with a different hyperparameter state than the one that generated it, or if independent validation data are loaded.
