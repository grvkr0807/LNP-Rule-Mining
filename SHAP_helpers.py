#!/usr/bin/env python
# coding: utf-8


import os, gc, time, pickle
from collections import defaultdict

import numpy as np
import pandas as pd
import shap


# ---------- SHAP helpers (memory-bounded, sparse interactions) ----------
def _row_subsample(X, max_rows=SHAP_ROW_CAP, rng=42):
    """Subsample rows for SHAP to keep memory bounded."""
    if X.shape[0] <= max_rows:
        return X
    rs = np.random.RandomState(rng)
    idx = rs.choice(X.shape[0], size=max_rows, replace=False)
    return X[idx]



def shap_main_and_interactions(model, X_train, background=None):
    """
    Compute SHAP main-effect importances S and full interaction matrix (average |.|).
    Returns:
        S_abs_mean: (D,) float32
        inter_abs_mean: (D, D) float32
    """
    Xs = _row_subsample(X_train, max_rows=SHAP_ROW_CAP)
    expl = shap.TreeExplainer(model, data=background, feature_perturbation="tree_path_dependent")

    # Main effects
    vals = expl.shap_values(Xs)
    if isinstance(vals, list):   # multiclass → average per-class magnitudes
        S = np.mean([np.abs(v).mean(axis=0) for v in vals], axis=0)
    else:
        S = np.abs(vals).mean(axis=0)
    del vals; gc.collect()

    # Interactions (full)
    inter = expl.shap_interaction_values(Xs)
    if isinstance(inter, list):
        inter_abs = np.mean([np.abs(t).mean(axis=0) for t in inter], axis=0)
    else:
        inter_abs = np.abs(inter).mean(axis=0)

    # zero diagonal for cleaner CSV (so we only see pairwise terms)
    np.fill_diagonal(inter_abs, 0.0)

    S = np.asarray(S, dtype=FLOATX)
    inter_abs = np.asarray(inter_abs, dtype=FLOATX)
    return S, inter_abs



def smallest_m_for_mass(S_mean, target_mass):
    """Return the smallest m such that top-m features cover ≥ target_mass of total importance."""
    order = np.argsort(S_mean)[::-1]
    s = S_mean[order]
    cs = np.cumsum(s, dtype=np.float64)
    total = float(cs[-1]) if cs.size and cs[-1] > 0 else 1.0
    frac = cs / total
    m = int(np.searchsorted(frac, target_mass) + 1)
    return max(1, min(m, S_mean.size))



def select_next_feature_subset_with_interactions(
    S_mean,
    inter_mean,
    current_idx,
    iteration,
    target_mass=TARGET_IMPORTANCE_MASS,
    top_n_partners=TOP_N_PARTNERS,
    top_fraction_n=TOP_FRACTION_N,
    min_partners=MIN_PARTNERS,
    max_partners=MAX_PARTNERS,
    preserve_order=True,
):
    """
    Choose next subset using BOTH main effects and interactions.

    Steps:
      1) Find smallest m s.t. cumulative SHAP importance >= target_mass.
      2) Let T be top-m LOCAL indices (by S_mean).
      3) For each i in T, add its top-n interaction partners by inter_mean[i, :].
         n is dynamic:
            - Iteration 0: n = we don't calculate interactions
            - Iteration >=1: n = round(top_fraction_n * D_iter)
         Then clamp with [min_partners, max_partners] and [1, D_iter-1].
      4) Union and map LOCAL -> GLOBAL using current_idx.
      5) Either preserve original column order or reorder by importance.

    Returns: (next_active_global_indices, m, n_effective)
    """
    # 1) smallest m by importance mass
    m = smallest_m_for_mass(S_mean, target_mass)

    # 2) top-m LOCAL indices by importance (the set, not the order)
    order_local_desc = np.argsort(S_mean)[::-1]
    top_m_local = order_local_desc[:m]

    # D at this iteration
    D_iter = int(S_mean.size)

    # compute n (absolute n if provided, else dynamic fraction w/ guardrails)
    if top_n_partners is not None:
        n = int(top_n_partners)
    else:
        # Iteration 0 no longer calls this function; for Iter ≥1 use a single fraction
        n_raw = int(round(top_fraction_n * D_iter))
        n = max(1, n_raw)
        if min_partners is not None:
            n = max(n, int(min_partners))
        n = min(n, D_iter - 1)
        if max_partners is not None:
            n = min(n, int(max_partners))


    # 3) gather partners for each top feature
    selected_local = set(top_m_local.tolist())
    for i in top_m_local:
        row = inter_mean[i].copy()
        row[i] = 0.0  # exclude self
        partners_local = np.argsort(row)[-n:]  # pick n largest interactions
        for j in partners_local:
            if j != i:
                selected_local.add(int(j))

    # 4) LOCAL -> GLOBAL
    current_idx = np.asarray(current_idx, dtype=np.int32)
    if preserve_order:
        # keep original feature order within the current subset
        next_active = [g for local_pos, g in enumerate(current_idx) if local_pos in selected_local]
    else:
        # reorder selected by importance within this iteration
        sel_local = np.array(sorted(list(selected_local)))
        sel_local_sorted = sel_local[np.argsort(S_mean[sel_local])[::-1]]
        next_active = current_idx[sel_local_sorted].tolist()

    return next_active, m, n