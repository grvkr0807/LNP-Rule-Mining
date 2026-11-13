# P08. Phase 4 deterministic rule mining, sensitivity analysis, and final rulebooks

## Purpose and inputs

Rule mining is model-free: it operates on development rows, observed binary activity labels, and the final Phase-3 feature set for each case. It does not use fitted predictive models or the independent validation partition.

Inputs include:

- final selected feature identities from P07;
- development feature matrix and label vector for the corresponding case;
- feature typing that distinguishes continuous variables from validated binary/one-hot categorical variables;
- fixed random-independent rule-mining settings.

Outputs are under `06_Rule_Mining/`, including bin definitions, candidate/eligibility/pruning summaries, retained rulebooks, sensitivity comparisons, and cross-case structural analyses.

## A. Feature binning and atomic conditions

```text
FOR each selected feature p:
    IF p is a validated binary/one-hot categorical variable:
        DEFINE categorical states from the observed encoded values
        DO NOT quantile-bin it as continuous
    ELSE:
        CALCULATE requested empirical quantile boundaries from DEVELOPMENT rows only
        COLLAPSE duplicate boundaries deterministically if quantiles coincide
        DEFINE non-overlapping intervals with explicit lower/upper inclusivity
        STORE every boundary and interval label in Bin_Definitions.csv
    END IF
END FOR
```

A continuous rule condition refers to the frozen numeric interval itself, not merely a bin number. These exact conditions are subsequently transferred unchanged to validation and in vivo data.

## B. Candidate conjunction enumeration

A rule is an axis-aligned conjunction containing at most one atomic condition per feature. Let `o_R` denote rule order (number of conditions).

```text
FOR order o from 1 to M:
    FOR each deterministic combination of o distinct features:
        FOR each deterministic Cartesian product of one atomic state/bin per chosen feature:
            R <- canonical ordered tuple of conditions
            mask_R <- AND of condition masks on development rows
            n_R <- number of TRUE rows in mask_R       # support
            y_R <- number of positive labels in mask_R
            IF n_R == 0:
                discard candidate before precision calculations
            ELSE:
                p_R <- y_R / n_R                       # raw precision
                lift_R <- p_R / p0                     # descriptive only
                p_low_R <- lower bound of two-sided 95% Wilson interval
            END IF
        END FOR
    END FOR
END FOR
```

`p0` is the global positive prevalence in the case's development data. Lift is not a hard eligibility filter.

## C. Wilson lower bound and conservative utility

For support `n`, observed fraction `p_hat`, and `z=1.9599639845`, calculate the standard two-sided Wilson lower confidence bound. The implementation must handle `n=0` before calling this formula.

Define conservative excess-positive count

`EP_low(R) = n_R * (p_low_R - p0)`

and complexity-penalized conservative utility

`U_low(R) = EP_low(R) - lambda * o_R`.

A candidate is initially eligible only if all conditions are satisfied:

```text
n_R >= min_support
p_R >= min_precision
p_low_R >= p0
U_low(R) > 0
```

## D. Exact-coverage and superset pruning

Coverage equivalence is determined from actual development-row masks, not from syntactic similarity.

```text
GROUP/compare eligible rules by exact formulation coverage mask
FOR rules with identical coverage:
    retain deterministic preferred representation according to the documented
    lower-order/utility/ranking logic
END FOR

PROCESS eligible rules from simpler to more complex orders
FOR higher-order rule R:
    simpler_subsets <- already-retained strict condition-subset rules of R
    IF a simpler subset describes a broader/equivalent population and R does not
       provide genuinely higher complexity-penalized conservative utility than
       every relevant retained simpler subset:
        prune R
    ELSE:
        retain R
    END IF
END FOR
```

The pruning audit files must record why each removed rule was removed.

## E. Deterministic final ranking

Retained rules are sorted by the project's deterministic ranking keys, with higher values favored for numeric utility criteria:

1. `U_low`;
2. conservative excess-positive quantity `EP_low`;
3. Wilson lower bound `p_low`;
4. support;
5. canonical rule key as final deterministic tie resolution.

The canonical key is built from ordered feature/condition representations so that equivalent reruns do not depend on Python object ordering.

## F. One-factor-at-a-time sensitivity analysis

Sensitivity is performed in Case 1 using the same mining core. Parameters are fixed sequentially so later analyses are conditional on earlier locked decisions.

```text
# 1. Number of bins
FOR bins in {4,5,6,7,8}:
    mine complete rulebook with other baseline settings fixed
COMPARE feature-prominence structure, favorable-value regions, coverage,
        retained-rule proportion/order, precision/support and utility diagnostics
LOCK bins = 6

# 2. Minimum support
FOR min_support in {30,40,50,60,70}:
    mine using bins=6
COMPARE the same structural/coverage diagnostics
LOCK min_support = 50

# 3. Minimum precision
FOR min_precision in {0.55,0.60,0.65,0.70,0.75}:
    mine using bins=6, min_support=50
LOCK min_precision = 0.65 based on structural representativeness/robustness

# 4. Complexity penalty
FOR lambda in the deposited sensitivity grid spanning 0 through 2:
    mine using previously locked settings
LOCK lambda = 0.5

# 5. Maximum rule order
FOR M in {2,3,4,5}:
    mine using all previously locked settings
COMPARE convergence of coverage, retained-rule composition and added structural value
LOCK M = 4
```

Selection is based primarily on structural robustness and convergence, not on directly optimizing rule counts, support, or precision values that the tested parameter mechanically controls.

## G. Final five-case mining

```text
FINAL_SETTINGS = {bins:6, min_support:50, min_precision:0.65, lambda:0.5, M:4}
FOR case in Cases 1..5:
    LOAD final Phase-3 feature set and development labels
    MINE and prune using exactly FINAL_SETTINGS
    WRITE retained rulebook, bin definitions, masks/audits and ranking summaries
END FOR
```

Expected final retained-rule counts are `1025, 1479, 1099, 187, 733` for Cases 1–5. Rule counts are an integrity check, not a target to optimize.

## Failure and integrity checks

1. Validation and in vivo data must never be loaded during sensitivity or final mining.
2. Continuous bin boundaries must be computed from development data only.
3. Binary/one-hot variables must remain categorical.
4. Each rule contains at most one condition per feature.
5. Coverage redundancy uses exact row masks.
6. Re-running ranking on the same retained rules must produce identical rule IDs/ranks.
7. Final parameters and rule counts must match the deposited `06_Rule_Mining/01_Final_Rulebooks/` outputs.
