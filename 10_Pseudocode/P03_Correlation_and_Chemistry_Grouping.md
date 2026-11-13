# P03. Correlation structure and chemistry-aware grouping

## Purpose

This stage constructs two different structures that must not be conflated: (1) strict descriptor-correlation clusters used only as a Phase-1 rescue safeguard, and (2) lipid-chemistry group assignments used to test out-of-chemistry generalization. Neither structure performs pre-model feature deletion.

## Inputs and outputs

- Standard-k-means development QC matrix (`420` features) and feature schema.
- `01_Data/05_Feature_Matrices_InVitro/4_Correlation_Summary.xlsx`.
- `4_Feature_Correlation_ConservativeClusters_Activity_KMeans_development.xlsx` and `4_Feature_Correlation_StrictClusters_Activity_KMeans_development.xlsx`.
- Bemis–Murcko and fingerprint-clustering outputs under `01_Data/07_Chemistry_Grouping/`.
- Group-assignment CSVs used by model tuning and the 12-branch analysis.

## A. Joint Pearson/Spearman correlation analysis

For each ordered feature pair `(a,b)` on standard-k-means development data, calculate Pearson correlation `rho_P(a,b)` and Spearman rank correlation `rho_S(a,b)` using rows for which both values are finite.

A pair is linked at threshold `tau` only when both absolute correlations satisfy the threshold:

`|rho_P(a,b)| >= tau AND |rho_S(a,b)| >= tau`.

Multiple high-correlation thresholds were evaluated diagnostically; the final Phase-1 rescue structure uses `tau = 0.99`.

```text
X <- standard-k-means development QC matrix
FOR every unordered pair of features (a,b):
    rho_P[a,b] <- Pearson(X[:,a], X[:,b])
    rho_S[a,b] <- Spearman(X[:,a], X[:,b])
    joint_link_tau[a,b] <- abs(rho_P[a,b]) >= tau AND abs(rho_S[a,b]) >= tau
END FOR

BUILD conservative/connected correlation structures for diagnostics as deposited
BUILD strict clusters using complete-linkage semantics:
    a candidate cluster C is valid at tau only if every unordered pair in C
    satisfies the joint Pearson/Spearman threshold

LOCK the strict tau=0.99 cluster membership for P05 rescue
DO NOT delete any feature merely because it belongs to a correlation cluster
```

The strict structure is deliberately conservative: it is consulted only when a SHAP-driven Phase-1 update would otherwise remove signal distributed across an extremely correlated family.

## B. Bemis–Murcko scaffold diagnostics

```text
FOR each unique ionizable-lipid structure represented in the relevant dataset:
    PARSE molecule
    COMPUTE Bemis-Murcko scaffold when defined
    ASSIGN scaffold identifier
END FOR
SUMMARIZE scaffold frequency and train/test/group novelty diagnostics
```

Scaffold analysis is a chemistry characterization and sensitivity diagnostic. It does not depend on the activity label definition and does not define the final Case-4 grouping.

## C. Morgan fingerprint / Butina grouping

The adopted chemistry-aware grouped CV uses ionizable-lipid Morgan bit-vector fingerprints with radius `2`, `2048` bits and chirality enabled. Pairwise similarity is Tanimoto similarity. The final clustering threshold is similarity `0.70`, equivalent to Butina distance cutoff `0.30`.

```text
unique_lipids <- unique valid ionizable-lipid identities
FOR each unique lipid u in deterministic input order:
    fp[u] <- MorganBitVector(u, radius=2, nBits=2048, useChirality=True)
END FOR

FOR each unordered pair (u,v):
    similarity[u,v] <- Tanimoto(fp[u], fp[v])
    distance[u,v] <- 1 - similarity[u,v]
END FOR

clusters <- ButinaCluster(distance_matrix, cutoff=0.30)
ASSIGN deterministic cluster identifier fingerprint_cluster_id_70 to each lipid
JOIN cluster IDs back to formulation rows
WRITE row-level assignment files
```

When a stored assignment is available, downstream analysis must load that assignment rather than reclustering and risking version-dependent cluster ordering.

## Grouped cross-validation constraint

For Case 4 and the fingerprint-grouped pre-refinement branches, all formulations sharing the same `fingerprint_cluster_id_70` must remain in the same fold. Stratification by activity is preserved as far as allowed by group constraints. The exact deposited split-assignment CSV is the authoritative fold realization.

## Integrity checks

1. Verify every strict 0.99 cluster satisfies the complete-linkage all-pairs joint-correlation criterion.
2. Verify feature names in the correlation workbooks match the 420-feature schema exactly.
3. Verify Morgan settings (`radius=2`, `nBits=2048`, chirality enabled) and Tanimoto/Butina threshold (`0.70` similarity / `0.30` distance).
4. Verify each formulation maps to exactly one fingerprint cluster and no group is split across grouped-CV folds.
5. Confirm neither scaffold nor fingerprint grouping uses the independent validation labels to tune chemistry thresholds.
