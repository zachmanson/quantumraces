# Results v2, first-finder fork rule (headline gamma_S = 0.6)

Produced by `results_v2_g06/run_all.py` (ticket `.scratch/revision-v2/issues/01-first-finder-gamma.md`). Equilibria are Gambit `lcp_solve(rational=True)`, first equilibrium found. Commands run from the repo root.

- Commit: `294db1e83edf20186a21e55c3e71cadb4c4a8f6e`
- Versions (added by hand; the meta JSONs predate version recording): Python 3.12.8, pygambit 16.3.0, numpy 2.0.2, scipy 1.15.1, pandas 2.2.3, matplotlib 3.10.0 (pinned in `requirements.txt`)
- Batch started: 2026-10-27 15:21:16
- Batch finished: 2026-10-28 02:59:14
- Progress: 55 of 55 configurations attempted; 55 done, 0 timed out, 0 failed.
- Wall-clock limit per configuration: 3 h (none for the c = 3 second-equilibrium runs).

## Configurations

| # | configuration | step | status | last stage | started | elapsed (s) | output | command |
|---|---|---|---|---|---|---|---|---|
| 1 | headline_c1_nonce-only | headline | done | finished | 2026-10-27 15:21:16 | 2001 | `.` | `python run.py --regime nonce-only -c 1 --n-q 50 --gamma 0.60 --num-simulations 1000000 --out-dir results_v2_g06 --processes 6` |
| 2 | headline_c1_full-header | headline | done | finished | 2026-10-27 15:54:37 | 5159 | `.` | `python run.py --regime full-header -c 1 --n-q 50 --gamma 0.60 --num-simulations 1000000 --out-dir results_v2_g06 --processes 6` |
| 3 | headline_c2_nonce-only | headline | done | finished | 2026-10-27 17:20:36 | 1160 | `.` | `python run.py --regime nonce-only -c 2 --n-q 45 --gamma 0.60 --num-simulations 1000000 --out-dir results_v2_g06 --processes 6` |
| 4 | headline_c2_full-header | headline | done | finished | 2026-10-27 17:39:56 | 1691 | `.` | `python run.py --regime full-header -c 2 --n-q 45 --gamma 0.60 --num-simulations 1000000 --out-dir results_v2_g06 --processes 6` |
| 5 | sweep_c1_g0.50 | sweep | done | finished | 2026-10-27 18:08:07 | 121 | `sweep/g0.50` | `python run.py --regime full-header -c 1 --n-q 25 --gamma 0.50 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g0.50 --processes 6` |
| 6 | sweep_c1_g0.55 | sweep | done | finished | 2026-10-27 18:10:08 | 158 | `sweep/g0.55` | `python run.py --regime full-header -c 1 --n-q 25 --gamma 0.55 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g0.55 --processes 6` |
| 7 | sweep_c1_g0.60 | sweep | done | finished | 2026-10-27 18:12:45 | 167 | `sweep/g0.60` | `python run.py --regime full-header -c 1 --n-q 25 --gamma 0.60 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g0.60 --processes 6` |
| 8 | sweep_c1_g0.65 | sweep | done | finished | 2026-10-27 18:15:33 | 173 | `sweep/g0.65` | `python run.py --regime full-header -c 1 --n-q 25 --gamma 0.65 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g0.65 --processes 6` |
| 9 | sweep_c1_g0.70 | sweep | done | finished | 2026-10-27 18:18:26 | 178 | `sweep/g0.70` | `python run.py --regime full-header -c 1 --n-q 25 --gamma 0.70 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g0.70 --processes 6` |
| 10 | sweep_c1_g0.75 | sweep | done | finished | 2026-10-27 18:21:24 | 182 | `sweep/g0.75` | `python run.py --regime full-header -c 1 --n-q 25 --gamma 0.75 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g0.75 --processes 6` |
| 11 | sweep_c1_g0.80 | sweep | done | finished | 2026-10-27 18:24:26 | 191 | `sweep/g0.80` | `python run.py --regime full-header -c 1 --n-q 25 --gamma 0.80 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g0.80 --processes 6` |
| 12 | sweep_c1_g0.85 | sweep | done | finished | 2026-10-27 18:27:37 | 187 | `sweep/g0.85` | `python run.py --regime full-header -c 1 --n-q 25 --gamma 0.85 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g0.85 --processes 6` |
| 13 | sweep_c1_g0.90 | sweep | done | finished | 2026-10-27 18:30:44 | 213 | `sweep/g0.90` | `python run.py --regime full-header -c 1 --n-q 25 --gamma 0.90 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g0.90 --processes 6` |
| 14 | sweep_c1_g0.95 | sweep | done | finished | 2026-10-27 18:34:17 | 225 | `sweep/g0.95` | `python run.py --regime full-header -c 1 --n-q 25 --gamma 0.95 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g0.95 --processes 6` |
| 15 | sweep_c1_g1.00 | sweep | done | finished | 2026-10-27 18:38:02 | 220 | `sweep/g1.00` | `python run.py --regime full-header -c 1 --n-q 25 --gamma 1.00 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g1.00 --processes 6` |
| 16 | sweep_c2_g0.50 | sweep | done | finished | 2026-10-27 18:41:42 | 147 | `sweep/g0.50` | `python run.py --regime full-header -c 2 --n-q 30 --gamma 0.50 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g0.50 --processes 6` |
| 17 | sweep_c2_g0.55 | sweep | done | finished | 2026-10-27 18:44:09 | 155 | `sweep/g0.55` | `python run.py --regime full-header -c 2 --n-q 30 --gamma 0.55 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g0.55 --processes 6` |
| 18 | sweep_c2_g0.60 | sweep | done | finished | 2026-10-27 18:46:44 | 163 | `sweep/g0.60` | `python run.py --regime full-header -c 2 --n-q 30 --gamma 0.60 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g0.60 --processes 6` |
| 19 | sweep_c2_g0.65 | sweep | done | finished | 2026-10-27 18:49:26 | 173 | `sweep/g0.65` | `python run.py --regime full-header -c 2 --n-q 30 --gamma 0.65 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g0.65 --processes 6` |
| 20 | sweep_c2_g0.70 | sweep | done | finished | 2026-10-27 18:52:20 | 173 | `sweep/g0.70` | `python run.py --regime full-header -c 2 --n-q 30 --gamma 0.70 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g0.70 --processes 6` |
| 21 | sweep_c2_g0.75 | sweep | done | finished | 2026-10-27 18:55:13 | 179 | `sweep/g0.75` | `python run.py --regime full-header -c 2 --n-q 30 --gamma 0.75 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g0.75 --processes 6` |
| 22 | sweep_c2_g0.80 | sweep | done | finished | 2026-10-27 18:58:11 | 183 | `sweep/g0.80` | `python run.py --regime full-header -c 2 --n-q 30 --gamma 0.80 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g0.80 --processes 6` |
| 23 | sweep_c2_g0.85 | sweep | done | finished | 2026-10-27 19:01:15 | 187 | `sweep/g0.85` | `python run.py --regime full-header -c 2 --n-q 30 --gamma 0.85 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g0.85 --processes 6` |
| 24 | sweep_c2_g0.90 | sweep | done | finished | 2026-10-27 19:04:22 | 186 | `sweep/g0.90` | `python run.py --regime full-header -c 2 --n-q 30 --gamma 0.90 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g0.90 --processes 6` |
| 25 | sweep_c2_g0.95 | sweep | done | finished | 2026-10-27 19:07:28 | 192 | `sweep/g0.95` | `python run.py --regime full-header -c 2 --n-q 30 --gamma 0.95 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g0.95 --processes 6` |
| 26 | sweep_c2_g1.00 | sweep | done | finished | 2026-10-27 19:10:40 | 201 | `sweep/g1.00` | `python run.py --regime full-header -c 2 --n-q 30 --gamma 1.00 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g1.00 --processes 6` |
| 27 | control | control | done | finished | 2026-10-27 19:14:07 | 515 | `.` | `python run.py --regime full-header --control --num-simulations 1000000 --out-dir results_v2_g06 --processes 6` |
| 28 | headline_c3_nonce-only | headline | done | finished | 2026-10-27 19:22:42 | 4929 | `.` | `python run.py --regime nonce-only -c 3 --n-q 35 --gamma 0.60 --num-simulations 1000000 --out-dir results_v2_g06 --processes 6` |
| 29 | headline_c3_full-header | headline | done | finished | 2026-10-27 20:44:51 | 1505 | `.` | `python run.py --regime full-header -c 3 --n-q 35 --gamma 0.60 --num-simulations 1000000 --out-dir results_v2_g06 --processes 6` |
| 30 | headline_c4_nonce-only | headline | done | finished | 2026-10-27 21:09:56 | 1095 | `.` | `python run.py --regime nonce-only -c 4 --n-q 25 --gamma 0.60 --num-simulations 1000000 --out-dir results_v2_g06 --processes 6` |
| 31 | headline_c4_full-header | headline | done | finished | 2026-10-27 21:28:11 | 1877 | `.` | `python run.py --regime full-header -c 4 --n-q 25 --gamma 0.60 --num-simulations 1000000 --out-dir results_v2_g06 --processes 6` |
| 32 | sweep_c3_g0.50 | sweep | done | finished | 2026-10-27 21:59:28 | 160 | `sweep/g0.50` | `python run.py --regime full-header -c 3 --n-q 20 --gamma 0.50 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g0.50 --processes 6` |
| 33 | sweep_c3_g0.55 | sweep | done | finished | 2026-10-27 22:02:08 | 182 | `sweep/g0.55` | `python run.py --regime full-header -c 3 --n-q 20 --gamma 0.55 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g0.55 --processes 6` |
| 34 | sweep_c3_g0.60 | sweep | done | finished | 2026-10-27 22:05:10 | 183 | `sweep/g0.60` | `python run.py --regime full-header -c 3 --n-q 20 --gamma 0.60 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g0.60 --processes 6` |
| 35 | sweep_c3_g0.65 | sweep | done | finished | 2026-10-27 22:08:14 | 195 | `sweep/g0.65` | `python run.py --regime full-header -c 3 --n-q 20 --gamma 0.65 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g0.65 --processes 6` |
| 36 | sweep_c3_g0.70 | sweep | done | finished | 2026-10-27 22:11:29 | 194 | `sweep/g0.70` | `python run.py --regime full-header -c 3 --n-q 20 --gamma 0.70 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g0.70 --processes 6` |
| 37 | sweep_c3_g0.75 | sweep | done | finished | 2026-10-27 22:14:43 | 196 | `sweep/g0.75` | `python run.py --regime full-header -c 3 --n-q 20 --gamma 0.75 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g0.75 --processes 6` |
| 38 | sweep_c3_g0.80 | sweep | done | finished | 2026-10-27 22:17:59 | 195 | `sweep/g0.80` | `python run.py --regime full-header -c 3 --n-q 20 --gamma 0.80 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g0.80 --processes 6` |
| 39 | sweep_c3_g0.85 | sweep | done | finished | 2026-10-27 22:21:14 | 197 | `sweep/g0.85` | `python run.py --regime full-header -c 3 --n-q 20 --gamma 0.85 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g0.85 --processes 6` |
| 40 | sweep_c3_g0.90 | sweep | done | finished | 2026-10-27 22:24:30 | 201 | `sweep/g0.90` | `python run.py --regime full-header -c 3 --n-q 20 --gamma 0.90 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g0.90 --processes 6` |
| 41 | sweep_c3_g0.95 | sweep | done | finished | 2026-10-27 22:27:51 | 1548 | `sweep/g0.95` | `python run.py --regime full-header -c 3 --n-q 20 --gamma 0.95 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g0.95 --processes 6` |
| 42 | sweep_c3_g1.00 | sweep | done | finished | 2026-10-27 22:53:39 | 4803 | `sweep/g1.00` | `python run.py --regime full-header -c 3 --n-q 20 --gamma 1.00 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g1.00 --processes 6` |
| 43 | sweep_c4_g0.50 | sweep | done | finished | 2026-10-28 00:13:42 | 2950 | `sweep/g0.50` | `python run.py --regime full-header -c 4 --n-q 15 --gamma 0.50 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g0.50 --processes 6` |
| 44 | sweep_c4_g0.55 | sweep | done | finished | 2026-10-28 01:02:51 | 145 | `sweep/g0.55` | `python run.py --regime full-header -c 4 --n-q 15 --gamma 0.55 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g0.55 --processes 6` |
| 45 | sweep_c4_g0.60 | sweep | done | finished | 2026-10-28 01:05:16 | 154 | `sweep/g0.60` | `python run.py --regime full-header -c 4 --n-q 15 --gamma 0.60 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g0.60 --processes 6` |
| 46 | sweep_c4_g0.65 | sweep | done | finished | 2026-10-28 01:07:50 | 150 | `sweep/g0.65` | `python run.py --regime full-header -c 4 --n-q 15 --gamma 0.65 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g0.65 --processes 6` |
| 47 | sweep_c4_g0.70 | sweep | done | finished | 2026-10-28 01:10:21 | 168 | `sweep/g0.70` | `python run.py --regime full-header -c 4 --n-q 15 --gamma 0.70 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g0.70 --processes 6` |
| 48 | sweep_c4_g0.75 | sweep | done | finished | 2026-10-28 01:13:09 | 177 | `sweep/g0.75` | `python run.py --regime full-header -c 4 --n-q 15 --gamma 0.75 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g0.75 --processes 6` |
| 49 | sweep_c4_g0.80 | sweep | done | finished | 2026-10-28 01:16:06 | 213 | `sweep/g0.80` | `python run.py --regime full-header -c 4 --n-q 15 --gamma 0.80 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g0.80 --processes 6` |
| 50 | sweep_c4_g0.85 | sweep | done | finished | 2026-10-28 01:19:40 | 190 | `sweep/g0.85` | `python run.py --regime full-header -c 4 --n-q 15 --gamma 0.85 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g0.85 --processes 6` |
| 51 | sweep_c4_g0.90 | sweep | done | finished | 2026-10-28 01:22:50 | 186 | `sweep/g0.90` | `python run.py --regime full-header -c 4 --n-q 15 --gamma 0.90 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g0.90 --processes 6` |
| 52 | sweep_c4_g0.95 | sweep | done | finished | 2026-10-28 01:25:56 | 190 | `sweep/g0.95` | `python run.py --regime full-header -c 4 --n-q 15 --gamma 0.95 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g0.95 --processes 6` |
| 53 | sweep_c4_g1.00 | sweep | done | finished | 2026-10-28 01:29:07 | 200 | `sweep/g1.00` | `python run.py --regime full-header -c 4 --n-q 15 --gamma 1.00 --num-simulations 100000 --no-plot --out-dir results_v2_g06/sweep/g1.00 --processes 6` |
| 54 | c3_stop_after_2_nonce-only | second equilibria | done | finished | 2026-10-28 01:32:30 | 1072 | `c3_stop_after_2` | `python run.py --regime nonce-only -c 3 --n-q 35 --gamma 0.60 --stop-after 2 --num-simulations 1000000 --out-dir results_v2_g06/c3_stop_after_2 --processes 6` |
| 55 | c3_stop_after_2_full-header | second equilibria | done | finished | 2026-10-28 01:50:22 | 4128 | `c3_stop_after_2` | `python run.py --regime full-header -c 3 --n-q 35 --gamma 0.60 --stop-after 2 --num-simulations 1000000 --out-dir results_v2_g06/c3_stop_after_2 --processes 6` |

## Equilibria

A measurement at iteration 0 is wasted; equilibria that contain one are flagged.

| configuration | eq | after elimination | Alice U | Bob U | E[first]/κ (Alice, Bob) | supports (A, B) | symmetric | zero measurement | P95 | P_det |
|---|---|---|---|---|---|---|---|---|---|---|
| headline_c1_nonce-only | eq1 | 1 × 1 | 0.00000 | 0.00000 | 1.0000, 1.0000 | 1, 1 | True | no | 0.008475 | 0.030644 |
| headline_c1_full-header | eq1 | 35 × 35 | 0.47265 | 0.47265 | 0.6876, 0.6876 | 19, 19 | True | no | 0.359629 | 1.000000 |
| headline_c2_nonce-only | eq1 | 2 × 2 | 0.00000 | 0.00000 | 1.0000, 1.0000 | 1, 1 | True | **yes** | 0.008547 | 0.030701 |
| headline_c2_full-header | eq1 | 97 × 97 | 0.47696 | 0.47696 | 0.6172, 0.6172 | 13, 13 | True | no | 0.318907 | 1.000000 |
| sweep_c1_g0.50 | eq1 | 1 × 1 | 0.50000 | 0.50000 | 1.0000, 1.0000 | 1, 1 | True | no | 0.487751 | 1.000000 |
| sweep_c1_g0.55 | eq1 | 16 × 16 | 0.48427 | 0.48427 | 0.7315, 0.7315 | 9, 9 | True | no | 0.392377 | 1.000000 |
| sweep_c1_g0.60 | eq1 | 17 × 17 | 0.47254 | 0.47254 | 0.6869, 0.6869 | 11, 11 | True | no | 0.361949 | 1.000000 |
| sweep_c1_g0.65 | eq1 | 18 × 18 | 0.46251 | 0.46251 | 0.6577, 0.6577 | 9, 9 | True | no | 0.341067 | 1.000000 |
| sweep_c1_g0.70 | eq1 | 19 × 19 | 0.45375 | 0.45375 | 0.6361, 0.6361 | 9, 9 | True | no | 0.324455 | 1.000000 |
| sweep_c1_g0.75 | eq1 | 19 × 19 | 0.44578 | 0.44577 | 0.6185, 0.6185 | 13, 13 | False | no | 0.310606 | 1.000000 |
| sweep_c1_g0.80 | eq1 | 19 × 19 | 0.43843 | 0.43843 | 0.6035, 0.6035 | 11, 11 | True | no | 0.301508 | 1.000000 |
| sweep_c1_g0.85 | eq1 | 19 × 19 | 0.43175 | 0.43175 | 0.5909, 0.5909 | 13, 13 | True | no | 0.291566 | 1.000000 |
| sweep_c1_g0.90 | eq1 | 20 × 20 | 0.42555 | 0.42555 | 0.5798, 0.5798 | 11, 11 | True | no | 0.280556 | 1.000000 |
| sweep_c1_g0.95 | eq1 | 20 × 20 | 0.41978 | 0.41977 | 0.5700, 0.5701 | 14, 14 | False | no | 0.272237 | 1.000000 |
| sweep_c1_g1.00 | eq1 | 20 × 20 | 0.41426 | 0.41421 | 0.5607, 0.5608 | 13, 13 | False | no | 0.266484 | 1.000000 |
| sweep_c2_g0.50 | eq1 | 2 × 2 | 0.50000 | 0.50000 | 1.0000, 1.0000 | 1, 1 | True | **yes** | 0.487923 | 1.000000 |
| sweep_c2_g0.55 | eq1 | 36 × 36 | 0.48363 | 0.48363 | 0.6765, 0.6765 | 7, 7 | True | no | 0.361050 | 1.000000 |
| sweep_c2_g0.60 | eq1 | 49 × 49 | 0.47638 | 0.47638 | 0.6214, 0.6214 | 7, 7 | True | no | 0.323185 | 1.000000 |
| sweep_c2_g0.65 | eq1 | 60 × 60 | 0.47266 | 0.47266 | 0.5872, 0.5872 | 9, 9 | True | no | 0.299550 | 1.000000 |
| sweep_c2_g0.70 | eq1 | 69 × 69 | 0.47162 | 0.47162 | 0.5653, 0.5653 | 11, 11 | True | no | 0.284653 | 1.000000 |
| sweep_c2_g0.75 | eq1 | 80 × 80 | 0.46879 | 0.46879 | 0.5537, 0.5537 | 9, 9 | True | no | 0.276850 | 1.000000 |
| sweep_c2_g0.80 | eq1 | 91 × 91 | 0.46777 | 0.46777 | 0.5430, 0.5430 | 15, 15 | True | no | 0.269923 | 1.000000 |
| sweep_c2_g0.85 | eq1 | 101 × 101 | 0.46716 | 0.46716 | 0.5377, 0.5377 | 15, 15 | True | no | 0.266497 | 1.000000 |
| sweep_c2_g0.90 | eq1 | 110 × 110 | 0.46336 | 0.46336 | 0.5272, 0.5272 | 13, 13 | True | no | 0.259352 | 1.000000 |
| sweep_c2_g0.95 | eq1 | 119 × 119 | 0.46153 | 0.46153 | 0.5241, 0.5241 | 15, 15 | True | no | 0.256410 | 1.000000 |
| sweep_c2_g1.00 | eq1 | 126 × 126 | 0.46021 | 0.46021 | 0.5198, 0.5198 | 15, 15 | True | no | 0.254098 | 1.000000 |
| headline_c3_nonce-only | eq1 | 3 × 3 | 0.00000 | 0.00000 | 1.0000, 1.0000 | 1, 1 | True | **yes** | 0.008475 | 0.030271 |
| headline_c3_full-header | eq1 | 123 × 123 | 0.47660 | 0.47660 | 0.6196, 0.6196 | 9, 9 | False | **yes** | 0.320542 | 1.000000 |
| headline_c4_nonce-only | eq1 | 4 × 4 | 0.00000 | 0.00000 | 1.0000, 1.0000 | 1, 1 | True | **yes** | 0.008475 | 0.030501 |
| headline_c4_full-header | eq1 | 162 × 162 | 0.47513 | 0.47513 | 0.6212, 0.6212 | 9, 11 | False | **yes** | 0.321995 | 1.000000 |
| sweep_c3_g0.50 | eq1 | 3 × 3 | 0.50000 | 0.50000 | 1.0000, 1.0000 | 1, 1 | True | **yes** | 0.487923 | 1.000000 |
| sweep_c3_g0.55 | eq1 | 42 × 42 | 0.48354 | 0.48354 | 0.6726, 0.6726 | 3, 3 | True | **yes** | 0.363839 | 1.000000 |
| sweep_c3_g0.60 | eq1 | 52 × 52 | 0.47324 | 0.47324 | 0.6248, 0.6248 | 5, 5 | True | **yes** | 0.328767 | 1.000000 |
| sweep_c3_g0.65 | eq1 | 63 × 63 | 0.47092 | 0.47092 | 0.5940, 0.5940 | 7, 7 | True | **yes** | 0.302600 | 1.000000 |
| sweep_c3_g0.70 | eq1 | 75 × 75 | 0.46871 | 0.46871 | 0.5694, 0.5694 | 7, 7 | True | **yes** | 0.289888 | 1.000000 |
| sweep_c3_g0.75 | eq1 | 85 × 85 | 0.46803 | 0.46803 | 0.5549, 0.5549 | 7, 7 | True | **yes** | 0.279343 | 1.000000 |
| sweep_c3_g0.80 | eq1 | 94 × 94 | 0.46771 | 0.46771 | 0.5458, 0.5458 | 9, 9 | True | **yes** | 0.272093 | 1.000000 |
| sweep_c3_g0.85 | eq1 | 111 × 111 | 0.46708 | 0.46708 | 0.5376, 0.5376 | 9, 9 | True | **yes** | 0.267606 | 1.000000 |
| sweep_c3_g0.90 | eq1 | 119 × 119 | 0.46085 | 0.46085 | 0.5253, 0.5253 | 7, 7 | True | **yes** | 0.257683 | 1.000000 |
| sweep_c3_g0.95 | eq1 | 126 × 126 | 0.45687 | 0.45858 | 0.5229, 0.5189 | 8, 8 | False | **yes** | 0.254408 | 1.000000 |
| sweep_c3_g1.00 | eq1 | 129 × 129 | 0.45803 | 0.45803 | 0.5136, 0.5136 | 9, 9 | True | **yes** | 0.250639 | 1.000000 |
| sweep_c4_g0.50 | eq1 | 4 × 4 | 0.50000 | 0.50000 | 1.0000, 1.0000 | 1, 1 | True | **yes** | 0.487923 | 1.000000 |
| sweep_c4_g0.55 | eq1 | 54 × 54 | 0.48386 | 0.48386 | 0.6766, 0.6766 | 3, 3 | True | **yes** | 0.364896 | 1.000000 |
| sweep_c4_g0.60 | eq1 | 60 × 60 | 0.47520 | 0.47520 | 0.6268, 0.6268 | 3, 3 | True | **yes** | 0.332609 | 1.000000 |
| sweep_c4_g0.65 | eq1 | 80 × 80 | 0.46645 | 0.46645 | 0.5975, 0.5975 | 5, 5 | True | **yes** | 0.311005 | 1.000000 |
| sweep_c4_g0.70 | eq1 | 86 × 86 | 0.46248 | 0.46248 | 0.5771, 0.5771 | 5, 5 | True | **yes** | 0.300236 | 1.000000 |
| sweep_c4_g0.75 | eq1 | 105 × 105 | 0.46284 | 0.46284 | 0.5593, 0.5593 | 5, 5 | True | **yes** | 0.280519 | 1.000000 |
| sweep_c4_g0.80 | eq1 | 115 × 115 | 0.46412 | 0.46303 | 0.5459, 0.5557 | 6, 6 | False | **yes** | 0.273657 | 1.000000 |
| sweep_c4_g0.85 | eq1 | 141 × 141 | 0.46304 | 0.46304 | 0.5371, 0.5371 | 5, 5 | False | **yes** | 0.266846 | 1.000000 |
| sweep_c4_g0.90 | eq1 | 151 × 151 | 0.46282 | 0.46282 | 0.5291, 0.5291 | 5, 5 | True | **yes** | 0.263291 | 1.000000 |
| sweep_c4_g0.95 | eq1 | 147 × 147 | 0.46356 | 0.46356 | 0.5308, 0.5308 | 7, 7 | True | **yes** | 0.263923 | 1.000000 |
| sweep_c4_g1.00 | eq1 | 151 × 151 | 0.46277 | 0.46277 | 0.5260, 0.5260 | 9, 9 | True | **yes** | 0.260976 | 1.000000 |
| c3_stop_after_2_nonce-only | eq1 | 3 × 3 | 0.00000 | 0.00000 | 1.0000, 1.0000 | 1, 1 | True | **yes** | 0.008475 | 0.030271 |
| c3_stop_after_2_full-header | eq1 | 123 × 123 | 0.47660 | 0.47660 | 0.6196, 0.6196 | 9, 9 | False | **yes** | 0.320542 | 1.000000 |
| c3_stop_after_2_full-header | eq2 | 123 × 123 | 0.47660 | 0.47660 | 0.6196, 0.6196 | 10, 10 | True | **yes** | 0.320574 | 1.000000 |

## No-quantum-miner control

1,000,000 days: mean p_stale 0.002405 (model 0.0024), P_det 0.030984 [0.030646, 0.031325] (expected about 0.047).

The sweep table is `sweep/stale_rate_vs_gamma.csv` (plots in `sweep/images/`); the summary tables are `tables.md`. Per-configuration logs are in `logs/`.
