"""Payoff model for the two-player quantum mining race (paper sections on units, regimes and payoffs).

Every function works on Grover iteration counts, never on grid indices.
"""
import math

import numpy as np

D_2025 = 119116256505723.5   # network difficulty, 9 May 2025 (blockchain.com)
REGIMES = ("nonce-only", "full-header")

N32 = 2.0**32
THETA32 = math.asin(2.0**-16)


def W_from_D(D: float) -> float:
    """Expected work (hashes per block) W = D * 2^48 / (2^16 - 1)."""
    return D * 2.0**48 / (2**16 - 1)


def kappa(regime: str, W: float) -> int:
    """Grover iteration budget: k_opt^32 in nonce-only, k_opt(W) in full-header."""
    if regime == "nonce-only":
        return math.floor(math.pi / (4 * THETA32))
    if regime == "full-header":
        return math.floor(math.pi / (4 * math.asin(math.sqrt(1.0 / W))))
    raise ValueError(f"unknown regime {regime!r}")


def grid(n_q: int, kap: int) -> np.ndarray:
    """Sampled iteration counts S_0' = { floor((1 - (1 - i/n_q)^2) * kappa) : i = 0..n_q }, deduplicated."""
    return np.array(sorted({math.floor((1 - (1 - i / n_q) ** 2) * kap) for i in range(n_q + 1)}), dtype=np.int64)


def _nonce_only_terms(W: float, mmax: int = 40) -> tuple[np.ndarray, np.ndarray]:
    """Binomial(2^32, 1/W) weights and Grover angles for m = 1..mmax marked nonces."""
    q = 1.0 / W
    weights, angles = [], []
    for m in range(1, mmax + 1):
        log_binom = sum(math.log(N32 - j) for j in range(m)) - math.lgamma(m + 1)
        weights.append(math.exp(log_binom + m * math.log(q) + (N32 - m) * math.log1p(-q)))
        angles.append(math.asin(math.sqrt(m / N32)))
    return np.array(weights), np.array(angles)


def success_prob(regime: str, W: float):
    """Return p(k) for the regime. Accepts an int or an integer array and returns float(s)."""
    if regime == "nonce-only":
        weights, angles = _nonce_only_terms(W)

        def p(k):
            k = np.asarray(k, dtype=np.float64)
            terms = np.sin((2 * k[..., None] + 1) * angles) ** 2
            return np.sum(weights * terms, axis=-1)[()]
    elif regime == "full-header":
        theta = math.asin(math.sqrt(1.0 / W))

        def p(k):
            k = np.asarray(k, dtype=np.float64)
            return (np.sin((2 * k + 1) * theta) ** 2)[()]
    else:
        raise ValueError(f"unknown regime {regime!r}")
    return p


def payoff_matrix(rows: np.ndarray, cols: np.ndarray, gamma: float, p) -> np.ndarray:
    """Alice's payoff u(a, b; W, gamma) for every row strategy a against every column strategy b.

    u = sum_i (u_meas_i + u_AQMS_i + u_resp_i), the closed form of reference_model.alice_payoff,
    vectorised over the columns. rows: (n, c) and cols: (m, c) arrays of iteration counts.
    """
    rows = np.asarray(rows, dtype=np.int64)
    cols = np.asarray(cols, dtype=np.int64)
    c = rows.shape[1]
    m = cols.shape[0]
    idx = np.arange(m)

    B = np.hstack([np.zeros((m, 1), dtype=np.int64), np.cumsum(cols, axis=1)])   # B_0..B_c per column
    pb = np.asarray(p(cols)).reshape(m, c)
    FB = np.hstack([np.ones((m, 1)), np.cumprod(1 - pb, axis=1)])                # Bob fails his first n

    out = np.empty((rows.shape[0], m), dtype=np.float64)
    for r, a in enumerate(rows):
        A = np.concatenate([[0], np.cumsum(a)])
        pa = np.asarray(p(a)).reshape(c)
        FA = np.concatenate([[1.0], np.cumprod(1 - pa)])
        total = np.zeros(m)
        for i in range(1, c + 1):
            # Alice's i-th measurement; Bob's last measurement strictly before A_i (B is non-decreasing)
            lB = np.sum(B[:, 1:] < A[i], axis=1)
            base = pa[i - 1] * FA[i - 1] * FB[idx, lB]
            # Bob's AQMS response (or his tied scheduled measurement); impossible once he is exhausted
            q = np.where(lB < c, p(A[i] - B[idx, lB]), 0.0)
            total += base * (1 - q)          # u_meas_i
            total += gamma * base * q        # u_AQMS_i
            # Bob's i-th measurement succeeds first and Alice responds (u_resp_i)
            lA = np.sum(A[1:, None] < B[:, i], axis=0)
            responds = (lA < c) & (A[np.minimum(lA + 1, c)] != B[:, i])
            resp = gamma * pb[:, i - 1] * FB[:, i - 1] * FA[lA] * p(B[:, i] - A[lA])
            total += np.where(responds, resp, 0.0)
        out[r] = total
    return out


def payoff_matrices(S: np.ndarray, gamma: float, p) -> tuple[np.ndarray, np.ndarray]:
    """Alice's matrix A and Bob's matrix B over the strategy set S (rows: Alice, columns: Bob).

    B[r, col] = u(S[col], S[r]; 1 - gamma), so at gamma = 0.5, B == A.T exactly.
    """
    A = payoff_matrix(S, S, gamma, p)
    B = payoff_matrix(S, S, 1 - gamma, p).T
    for M in (A, B):
        assert np.all(np.isfinite(M)), "payoff matrix has non-finite entries"
        assert M.min() >= 0.0 and M.max() <= 1.0, f"payoff entries outside [0,1]: [{M.min()}, {M.max()}]"
    return A, np.ascontiguousarray(B)
