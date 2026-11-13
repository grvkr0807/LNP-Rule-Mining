# Package scope and intentional exclusions

## Included
- Exact curated data snapshots and final source-relative label datasets.
- Frozen source partitions and CV/group assignments available in the source archives.
- Portable pre-QC/QC feature matrices generated from the authoritative project pickles.
- Chemistry-aware grouping assignments and diagnostics.
- Model-selection summaries, OOF outputs and tuning results available as structured files.
- Phase-1 iteration/candidate-selection outputs.
- Complete structured Phase-2 class-combination outputs and candidate selection.
- Phase-3 compression, final retuning, exhaustive-run configuration/folds, candidate selection, and post-hoc summaries.
- Final five rulebooks, bin definitions, rulebook-comparison/sensitivity outputs, independent-validation outputs, and in vivo transferability outputs.
- Detailed public pseudocode and software-environment records.

## Intentionally excluded
- Proprietary Python/Jupyter source code from the public archive.
- Serialized fitted-model objects and project pickles once equivalent portable/public data are deposited.
- Scheduler logs, caches, checkpoints, compiled bytecode, debugging output and duplicate plot images.
- Superseded or developmental analyses that are not part of the final published workflow.
- Raw candidate-level rule tables from every sensitivity setting; the final/structural comparison outputs and locked rulebooks are retained.
- Very large full Phase 3 per-subset and per-fold result tables. These are derived computational intermediates and are intentionally omitted from the public archive. The deposited Phase 3 materials retain the exact locked feature pools, fold assignments, hyperparameters, exhaustive-run configurations, performance-complexity summaries, numerical-best repeated-CV results, selection thresholds, threshold-qualified candidates, and final feature sets required to audit the published selection and regenerate the omitted intermediate tables.

