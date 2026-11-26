# c = 1 grid check (ticket 03, part 3)

Full-header, c = 1, γ_S = 0.6, seed 20261025, commit d447dcb. Each n_q ran as
`python run.py --regime full-header -c 1 --n-q N --gamma 0.60 --num-simulations 100000 --no-plot --out-dir results_v2_g06/nq_check_c1/nqN --processes 6`
(log: `batch.log`; batch 2026-10-28 20:12:05 – 21:03:27). The n_q = 45 run started after `buildpayoff.success_prob` was refactored onto `success_terms` in the working tree; p(k) is bit-identical before and after (checked on 2001 points per regime), so the run is unaffected.

| n_q | days | P(p_stale > ⅓) [95% CI] | P95 | U | E[first]/κ | LH (s) | support dims | source |
|---|---|---|---|---|---|---|---|---|
| 25 | 100k | 0.571 [0.568, 0.574] | 0.3619 | 0.4725 | 0.6869 | 17 | 17×17 | `sweep/g0.60` |
| 30 | 100k | 0.521 [0.518, 0.525] | 0.3600 | 0.4727 | 0.6875 | 68 | 21×21 | `nq_check_c1/nq30` |
| 35 | 100k | 0.512 [0.509, 0.515] | 0.3597 | 0.4727 | 0.6877 | 240 | 25×25 | `nq_check_c1/nq35` |
| 40 | 100k | 0.526 [0.523, 0.529] | 0.3601 | 0.4726 | 0.6875 | 709 | 28×28 | `nq_check_c1/nq40` |
| 45 | 100k | 0.526 [0.523, 0.529] | 0.3601 | 0.4726 | 0.6875 | 1312 | 32×32 | `nq_check_c1/nq45` |
| 50 | 1M | 0.516 [0.515, 0.517] | 0.3596 | 0.4726 | 0.6876 | 3577 | 35×35 | headline (`.`) |

From n_q = 30 to 50, P(>⅓) stays between 0.51 and 0.53 without a trend; n_q = 25 (0.571) is the outlier. P95, U and E[first]/κ move by under 0.002. P(>⅓) is sensitive because P95 ≈ 0.36 sits just above ⅓: tiny shifts in the per-day distribution move many days across the threshold.

The meta JSONs record commit d447dcb because the runs predate the commit. The `buildpayoff` refactor, `forks_per_race.py` and the P(>⅓) sweep plot are in commit 20ece85.
