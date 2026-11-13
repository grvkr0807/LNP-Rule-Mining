# P04. Hyperparameter tuning, seven-model benchmarking, and 12-branch robustness analysis

## Inputs

- In vitro QC feature matrices and labels produced by P02.
- Hyperparameter partition only for tuning.
- Development partition only for model comparison and robustness evaluation.
- Fingerprint group assignments from P03 when grouped CV is required.
- Candidate-level tuning outputs under `02_Model_Selection/01_Hyperparameter_Tuning/` are the authoritative record of the search candidates and selected settings.

## Metrics

For each held-out fold record accuracy, balanced accuracy, class-specific precision/recall/F1, Macro-F1, weighted F1, AUROC, and average-precision AUPRC. Macro-F1 is the prespecified primary model-selection/refit metric.

## A. Hyperparameter tuning

Seven candidate model families are evaluated in the standard-label model benchmark: Balanced Random Forest, class-weighted Random Forest, Extra Trees, XGBoost, LightGBM, CatBoost, and linear SVM.

```text
FOR each required label/CV/model tuning task:
    X_hp, y_hp <- corresponding hyperparameter partition only
    IF CV strategy is standard:
        cv <- StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    ELSE IF CV strategy is fingerprint-grouped:
        groups <- frozen fingerprint_cluster_id_70 for hyperparameter rows
        cv <- stratified grouped five-fold split preserving groups
    END IF

    DEFINE the model-specific search space used by the original task
    RUN RandomizedSearchCV with:
        up to 100 candidate configurations
        primary scoring/refit = Macro-F1
        random_state = 42 where supported
        five folds
    STORE every sampled candidate and CV score
    SELECT best candidate by the search object's Macro-F1 refit rule
    STORE complete selected parameter dictionary
END FOR
```

For exact reruns, do not rely on a potentially version-dependent random sampler to recreate the same candidate list. The candidate-level search results in the deposited tuning workbooks/CSVs define the exact configurations that were actually evaluated; a reimplementation may iterate those recorded candidates deterministically and verify that the same best row is selected.

## B. Seven-model benchmark

```text
label <- standard k-means
development_folds <- StratifiedKFold(5, shuffle=True, random_state=42)

FOR model_family in the seven tuned families:
    params <- selected hyperparameters for model_family
    FOR fold in development_folds:
        FIT model on fold training rows only
        PREDICT labels and probability/decision scores on fold held-out rows
        CALCULATE all metrics
        STORE OOF predictions with stable row IDs and fold IDs
    END FOR
    AGGREGATE fold metrics
END FOR

SELECT primary family by prespecified development Macro-F1 comparison
LOCK LightGBM as primary model family
RETAIN class-weighted Random Forest as model-family robustness branch
```

The deposited benchmark manifest records the exact selected settings and confirms that LightGBM was selected. Reproduction outputs should be compared to `Benchmarking_Model_Summary_Activity_KMeans_development.csv`, the OOF table, and the workbook.

## C. 12-branch robustness design

Construct the Cartesian product:

- labels: standard k-means, HC10, HC20;
- CV strategies: stratified and fingerprint-grouped;
- models: LightGBM and class-weighted Random Forest.

```text
FOR label in {standard, HC10, HC20}:
    FOR cv_strategy in {stratified, fingerprint_grouped}:
        FOR model in {LightGBM, class_weighted_RF}:
            params <- selected parameters for this label/CV/model task
            folds <- frozen corresponding development folds/groups
            FIT/EVALUATE exactly five held-out folds
            STORE fold metrics, OOF predictions and split assignments
        END FOR
    END FOR
END FOR
ASSERT number_of_branches = 12
ASSERT validation_split_loaded = FALSE
```

## D. Five refinement cases

The downstream refinement cases are fixed, complementary robustness cases rather than the five numerically highest branches:

```text
Case 1 = standard k-means / stratified / LightGBM
Case 2 = HC10 / stratified / LightGBM
Case 3 = HC20 / stratified / LightGBM
Case 4 = standard k-means / fingerprint-grouped / LightGBM
Case 5 = standard k-means / stratified / class-weighted RF
```

These choices isolate label-confidence sensitivity (Cases 2–3), chemistry-partition sensitivity (Case 4), and model-family sensitivity (Case 5) around the primary Case 1.

## Determinism and integrity checks

1. Hyperparameter tuning never uses development or validation outcomes.
2. Model benchmarking and 12-branch analysis never use validation outcomes.
3. Every development branch stores row-level fold assignment; reruns must use the deposited assignment when exact equivalence is required.
4. Case-4 grouping must be `fingerprint_cluster_id_70` with no group leakage.
5. Verify the 12-branch manifest reports three labels, two CV strategies, two models and `12` total evaluations.
6. Compare selected parameter dictionaries and OOF/fold metrics to the deposited model-selection outputs before entering P05.
