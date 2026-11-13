# P02. Molecular/formulation featurization and quality control

## Inputs

- Labeled/partitioned rows produced by P01.
- Constituent SMILES for ionizable (`il`), helper (`hl`), cholesterol (`chl`) and PEG (`peg`) lipids.
- Fixed categorical metadata schema used by the study.
- `00_Environment/SOFTWARE_VERSIONS.csv` and the recorded RDKit version (2023.09.1).

## Authoritative outputs

- `01_Data/05_Feature_Matrices_InVitro/Feature_Schema_PreQC_881.csv`.
- `01_Data/05_Feature_Matrices_InVitro/Feature_Schema_QC_420.csv`.
- Portable `PreQC_Feature_Matrix_*.npz` and `QC_Feature_Matrix_*.npz` files plus row-index CSVs.
- `3_Feature_QC_Report.xlsx` and `3_Feature_QC_Filtered_Output_Summary.xlsx`.
- Corresponding in vivo matrices/schema under `01_Data/06_Feature_Matrices_InVivo/`.

## Feature construction

The in vitro pre-QC representation contains 881 ordered columns: 836 RDKit-derived constituent descriptors, three retained custom molecular descriptors, and 42 formulation/experimental-context columns. The public schema files are authoritative for exact column names and order.

```text
FOR each row r:
    FOR constituent c in ordered sequence {il, hl, chl, peg}:
        PARSE constituent SMILES according to the curated structural mapping
        CALCULATE the project RDKit descriptor list in its fixed order
        EXCLUDE descriptor Ipc as specified by the original featurization
        APPEND constituent suffix to each descriptor name
    END FOR

    CALCULATE retained custom structural variables used by the final representation,
    including nitrogen_count, carbonate indicator and disulfide indicator as defined
    in the curated project data

    APPEND quantitative formulation-composition variables in their frozen order

    ENCODE categorical experimental/biological metadata using the fixed schema:
        each expected level has a predetermined output column
        an absent level in a dataset/split is represented by a zero-filled column
        unknown/unmapped values are handled according to the deposited preprocessing state,
        never by adding a new column dynamically
END FOR

CONCATENATE columns exactly according to Feature_Schema_PreQC_881.csv
ASSERT n_features = 881 for the in vitro pre-QC representation
ASSERT each matrix row aligns to its deposited row/formulation identifier file
```

## Quality-control mask

The QC decision is learned once from the standard-k-means **development** matrix. It is then applied without relearning to every in vitro label variant and partition.

```text
X_ref <- standard-k-means development pre-QC matrix
feature_type[j] <- {RDKit molecular, custom molecular, formulation/context}

FOR each feature j:
    COUNT NaN and +/-Inf values
    IF non-finite value violates the final project QC rules:
        fail or handle exactly as recorded in the QC report

    all_zero[j] <- every X_ref[:,j] == 0
    constant[j] <- number_of_unique_finite_values(X_ref[:,j]) <= 1

    IF feature_type[j] is molecular AND (all_zero[j] OR constant[j]):
        drop[j] <- TRUE
    ELSE:
        drop[j] <- FALSE
        # formulation/context fields are retained even when a level is absent in the
        # reference partition so that the fixed schema remains compatible across splits
    END IF
END FOR

keep_indices <- ordered indices for which drop[j] == FALSE
ASSERT length(keep_indices) = 420
WRITE Feature_Schema_QC_420.csv

FOR label in {standard, HC10, HC20}:
    FOR split in {hyperparameter, development, validation}:
        LOAD pre-QC matrix using its deposited row order
        SELECT columns keep_indices without reordering
        WRITE QC matrix and row identifiers
    END FOR
END FOR
```

The public QC workbooks contain the exact flagged and retained features. A reimplementation should compare the generated feature names and keep/drop mask directly to those outputs before continuing.

## In vivo representation

The in vivo branch is featurized with the same descriptor definitions and categorical construction logic but has its own domain-specific QC output because the available records/readouts differ. The recorded in vivo pre-QC feature universe contains 863 columns and the QC representation contains 367 columns. This in vivo QC state is used only for retrospective transferability in P10; it does not alter the in vitro 420-feature universe.

## Deterministic ordering and failure behavior

- The ordered schema, not dictionary/hash iteration order, determines feature positions.
- Constituent suffixes are part of the feature identity; `MolLogP_il` and `MolLogP_hl`, for example, are distinct features.
- A feature transferred downstream must match by exact feature name. Position-only matching is not permitted.
- If a matrix width, schema hash, row identifier, or expected feature name differs from the deposited state, stop rather than silently inserting, deleting, or reordering columns.

## Validation checks

1. Compare pre-QC and QC feature names to the deposited schema CSVs byte-for-name and in order.
2. Confirm in vitro widths `881 -> 420` and in vivo widths `863 -> 367`.
3. Confirm row IDs in every NPZ companion row file match the corresponding label/split table.
4. Recompute QC flags from standard-k-means development only and compare to `3_Feature_QC_Report.xlsx`.
5. Verify that no validation outcome is used to choose the in vitro QC mask.
