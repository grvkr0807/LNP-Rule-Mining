# SAR NM Iterative reproducibility package

This package accompanies **Machine learning-guided design rules for lipid nanoparticles to enhance nucleic acid delivery**. It is organized to support independent understanding, reimplementation, and audit of the published workflow while separating public data/output artifacts from proprietary implementation source code.

## What is included

The public package contains the exact curated study snapshots, activity labels, frozen source partitions, portable feature matrices, chemistry-group assignments, model-selection outputs, feature-refinement decision outputs, final rulebooks, independent-validation results, in vivo transferability outputs, software-environment information, figure/table source data, and detailed implementation-independent pseudocode.

## What is not included

The original Python/Jupyter implementation is not included in the public archive because the project code is subject to third-party proprietary restrictions arising from industry-funded work. The public pseudocode provides an implementation-independent computational specification, while executable access for editors/referees is handled separately through the journal-approved confidential review process. Transient caches, debugging logs, serialized fitted-model objects, and superseded or developmental analyses that are not part of the final published workflow are intentionally omitted.

Complete combination-level Phase 3 per-subset and per-fold tables are intentionally omitted from the public archive because they are large derived computational intermediates rather than primary study inputs or final reported outputs. The package retains the exact locked feature pools, fold assignments, hyperparameters, exhaustive-run configurations, candidate-selection outputs, selection thresholds, final feature sets, performance-complexity summaries, and detailed pseudocode required to audit the published decision path and regenerate these intermediate results.

## Computational environment

The computational workflow was developed and executed on Linux x86-64. `00_Environment/SAR_NM_Feature_Refinement_environment_full_linux_x86_64.yml` records the complete Linux x86-64 Conda environment available at the time the reproducibility package was prepared, including exact Conda build strings and pip-installed packages. `00_Environment/SAR_NM_Feature_Refinement_environment.yml` provides a portable specification of the principal dependencies required to reproduce the computational workflow. `00_Environment/SOFTWARE_VERSIONS.csv` provides a concise, human-readable summary of the principal software versions.

For routine environment creation, the portable specification is recommended:

    conda env create -f 00_Environment/SAR_NM_Feature_Refinement_environment.yml

The complete Linux x86-64 environment snapshot is retained for provenance and for resolving version- or build-specific compatibility questions.

## Start here

1. Read `WORKFLOW_MAP.md`.
2. Use `MANIFEST.csv` to map each deposited artifact to its analysis stage and source provenance.
3. Use `DATA_DICTIONARY.xlsx` for data/feature definitions.
4. Use `10_Pseudocode/` for the complete public algorithmic specification.
5. Use `09_Figure_Table_Source_Data/` to locate the exact data behind manuscript figures and tables.

## Reproducibility philosophy

The manuscript and Supporting Information provide the scientific and mathematical specification of the methods. This package supplies the exact computational inputs, frozen analysis state, and decision-driving outputs needed to audit the published results. It does not archive every transient object created during development.
