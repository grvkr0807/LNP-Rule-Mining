# P01. Data preparation, source-relative activity labeling, and in vitro partition freezing

## Inputs

- `01_Data/01_Curated_Snapshots/Cleaned_Data_17116.csv`.
- Constituent-identity/SMILES fields, formulation composition, experimental context, activity readout, and source/readout identifiers contained in the curated table.
- The deposited label and partition workbooks under `01_Data/02_InVitro_Labels/`, `01_Data/03_InVitro_Partitions/`, and `01_Data/04_InVivo_Labels/` are the authoritative row-level outputs for comparison.

## Outputs

- Source-relative standard k-means labels.
- HC10 and HC20 high-confidence label variants created without refitting k-means.
- Top-10-percentile and Top-20-percentile diagnostic variants; these are not propagated into downstream modeling.
- Frozen in vitro hyperparameter, development, and independent-validation partitions.
- Labeling diagnostics containing source-level sample counts, class counts/fractions, cluster centers, midpoint, separation diagnostics, and silhouette coefficients.

## Fixed definitions

For one retained source/readout group, let the numeric activity values be `x[1..n]`. Fit one-dimensional k-means with `k=2` and random state `42`. After fitting, order the two centroids so that `mu_low < mu_high`. The source-specific boundary is

`b = (mu_low + mu_high) / 2`.

A row receives standard label `0` if assigned to the lower-centroid cluster and `1` if assigned to the higher-centroid cluster. The high-confidence normalized distance is

`d_norm(x) = |x - b| / |mu_high - mu_low|`.

HC10 retains rows with `d_norm >= 0.10`; HC20 retains rows with `d_norm >= 0.20`. The original standard-label cluster assignment is retained for every surviving high-confidence row; k-means is not refitted after exclusion.

## Algorithm

```text
LOAD curated 17,116-record snapshot

STANDARDIZE fields required by the analysis:
    formulation identifier
    ionizable/helper/cholesterol/PEG lipid identity and structural representation
    formulation composition
    experimental/source context
    activity readout and readout type
    biological model/target, administration route and cargo metadata
REMOVE rows that lack fields required for the corresponding analysis branch
PRESERVE stable row/formulation identifiers through every transformation

SPLIT curated snapshot by experimental domain:
    in_vitro_snapshot  -> expected frozen snapshot size 15,243
    in_vivo_snapshot   -> expected frozen snapshot size 1,873

FOR domain in {in vitro, in vivo}:
    GROUP rows by the frozen source/readout grouping used by the project
    FOR each source/readout group g:
        x <- numeric activity vector for g
        IF fewer than two usable observations OR k=2 cannot be fitted:
            mark group according to deposited preprocessing decision; do not invent labels
        ELSE:
            FIT one-dimensional KMeans(k=2, random_state=42)
            ORDER centers -> mu_low, mu_high
            b <- (mu_low + mu_high) / 2
            ASSIGN standard label 0/1 from fitted cluster membership
            FOR every row i in g:
                d_norm[i] <- abs(x[i]-b) / abs(mu_high-mu_low)
                HC10_keep[i] <- d_norm[i] >= 0.10
                HC20_keep[i] <- d_norm[i] >= 0.20
            CREATE HC10 and HC20 by filtering only; do not refit centers
            CALCULATE source diagnostics, including silhouette when defined
        END IF
    END FOR

    CREATE Top10 and Top20 percentile diagnostic labelings using the project's
    deposited source-wise percentile outputs
    FLAG these variants as diagnostics only; exclude them from downstream model/refinement cases
END FOR
```

## In vitro partition freezing

The exact source-disjoint assignment is a deposited experimental state, not a quantity that should be regenerated from a different random draw. Reproduction should therefore load the source assignment represented by the files in `01_Data/03_InVitro_Partitions/`.

```text
LOAD standard-k-means source-to-partition assignment
ASSERT every retained source appears in exactly one of:
    hyperparameter
    development
    validation
ASSERT no source is split across partitions

FOR label variant in {standard, HC10, HC20}:
    JOIN rows to the frozen source assignment
    DROP only rows excluded by that label variant
    DO NOT re-optimize or reshuffle the source assignment
    WRITE label-specific hyperparameter/development/validation files
END FOR
```

The standard-label split-search candidates and final summary are deposited as `Data_Split_Candidates_KMeans.xlsx` and `Data_Split_Output_Summary.xlsx`. These files permit audit of the original split search without requiring a new random source allocation.

## Determinism and tie handling

- K-means uses random state 42.
- Centroids are ordered numerically before assigning low/high semantic labels; therefore the raw library cluster index is never interpreted directly.
- HC10/HC20 use the exact standard-label centroids and midpoint for that source.
- Row order does not define labels or partitions; stable row/formulation identifiers do.

## Validation checks

1. Confirm the frozen `Cleaned_Data_17116.csv`, `Cleaned_Data_InVitro_15243.csv`, and `Cleaned_Data_InVivo_1873.csv` row counts and identifiers.
2. Confirm every labeled row can be traced to the curated snapshot.
3. Recompute each source centroid ordering, midpoint and class counts and compare to the corresponding `*_Labeling_Diagnostics.xlsx` file.
4. Confirm HC10/HC20 are strict subsets of the standard-label rows and that surviving row labels are unchanged.
5. Confirm no source appears in more than one in vitro partition.
6. Confirm the independent-validation partition is not opened by P02–P08 except when applying a preprocessing mask/schema learned without validation outcomes.
