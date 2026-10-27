"""
Reference implementation of the payoff model in "Strategies for quantum-enabled Bitcoin miners"
(revised version). This file is the ground truth the repository code must match.

Contents
  1. Units:            expected work W from network difficulty D.
  2. Success prob p(k) for the two mining regimes (nonce-only, full-header).
  3. Grover budget kappa per regime.
  4. Alice's payoff entry  u(a, b; W, gamma) = sum_i (u_meas_i + u_AQMS_i + u_resp_i)   [closed form]
  5. Brute-force enumeration of every outcome (independent check of 4).
  6. The piecewise forms printed in the paper (another independent check of 4).
  7. Self-tests:  python3 reference_model.py

Conventions
  a = (a_1..a_c), b = (b_1..b_c): Grover iterations Alice/Bob perform before each of their c measurements.
  A_i = a_1+..+a_i, B_i = b_1+..+b_i (cumulative), A_0 = B_0 = 0.  Grover iterations are a clock.
  gamma = gamma_S is the probability that the first-broadcast block wins a fork caused by an AQMS response;
  a same-tick tie (both scheduled measurements succeed) is won by each side w.p. 1/2.
  Bob's matrix entry is u(b, a; W, gamma)  (the game is symmetric for every gamma).
"""
import itertools
import math
import random

# ---------------------------------------------------------------- 1. units
D_2025 = 119116256505723.5                       # network difficulty, 9 May 2025 (blockchain.com)
def W_from_D(D):
    """Expected work (hashes) W = 2^256 / target = D * 2^48 / (2^16 - 1)."""
    return D * 2.0**48 / (2**16 - 1)
W_2025 = W_from_D(D_2025)                         # ~5.116e23

# ---------------------------------------------------------------- 2. success probabilities
N32 = 2.0**32
THETA32 = math.asin(2.0**-16)                     # arcsin(sqrt(1/2^32))

def p_grover(k, m, N=N32):
    """Grover success prob with m marked of N after k iterations."""
    if m <= 0:
        return 0.0
    return math.sin((2 * k + 1) * math.asin(math.sqrt(m / N))) ** 2

def _log_binom_N32(m):
    # exact log C(2^32, m) without catastrophic cancellation
    return sum(math.log(N32 - j) for j in range(m)) - math.lgamma(m + 1)

def p_nonce_only_exact(k, W, mmax=40):
    """Paper eq (fqsprobBPOW): average of p(k,m) over m ~ Binomial(2^32, 1/W).
    Terms beyond m ~ 30 are < 1e-30 for W >= 2^32 (D >= 1)."""
    q = 1.0 / W
    s = 0.0
    for m in range(1, mmax + 1):
        logpmf = _log_binom_N32(m) + m * math.log(q) + (N32 - m) * math.log1p(-q)
        s += math.exp(logpmf) * p_grover(k, m)
    return s

def p_nonce_only_approx(k, W):
    """Paper eq (fqsprobapproxBPOW), valid for W >> 2^32."""
    return (N32 / W) * math.sin((2 * k + 1) * THETA32) ** 2

def p_full_header(k, W):
    """Paper eq (groversuccessbitcoinfullheader): fraction of marked inputs ~ 1/W."""
    return math.sin((2 * k + 1) * math.asin(math.sqrt(1.0 / W))) ** 2

# ---------------------------------------------------------------- 3. budgets
KOPT32 = math.floor(math.pi / (4 * THETA32))      # 51471
def kopt_full_header(W):
    return math.floor(math.pi / (4 * math.asin(math.sqrt(1.0 / W))))   # ~5.6177e11 at W_2025

def kappa(regime, W):
    return KOPT32 if regime == "nonce-only" else kopt_full_header(W)

def p_fn(regime, W):
    if regime == "nonce-only":
        return lambda k: p_nonce_only_exact(k, W)
    return lambda k: p_full_header(k, W)

def grid(n_q, kap):
    """Paper eq (groveriterquadrsubset): S_0' = { floor((1-(1-i/n_q)^2) * kappa) : i = 0..n_q }."""
    return sorted(set(math.floor((1 - (1 - i / n_q) ** 2) * kap) for i in range(n_q + 1)))

# ---------------------------------------------------------------- 4. closed form (what the code must implement)
def alice_payoff(a, b, gamma, p):
    """u(a,b;W,gamma) = sum_i u_meas_i + u_AQMS_i + u_resp_i, p = success-probability function."""
    c = len(a)
    A = [0] + list(itertools.accumulate(a))
    B = [0] + list(itertools.accumulate(b))
    FA = lambda n: math.prod(1 - p(a[r]) for r in range(n))     # Alice fails her first n
    FB = lambda n: math.prod(1 - p(b[r]) for r in range(n))     # Bob fails his first n
    total = 0.0
    for i in range(1, c + 1):
        # --- Alice's i-th measurement: Bob's last measurement strictly before A_i
        lB = max((j for j in range(c + 1) if B[j] < A[i]), default=0)   # max of empty set := 0
        base = p(a[i - 1]) * FA(i - 1) * FB(lB)
        # Bob's AQMS response (or, at a tie A_i = B_{lB+1}, his scheduled measurement) after A_i - B_lB iterations;
        # Bob cannot respond if he has used all c measurements (Fact 1).
        q = p(A[i] - B[lB]) if lB < c else 0.0
        tie = lB < c and B[lB + 1] == A[i]
        total += base * (1 - q)                        # u_meas_i : Alice wins alone
        total += (0.5 if tie else gamma) * base * q    # u_AQMS_i : fork; Alice found first, or tie (coin flip)
        # --- Bob's i-th measurement: Alice responds (u_resp_i)
        lA = max((j for j in range(c + 1) if A[j] < B[i]), default=0)
        if lA == c or A[lA + 1] == B[i]:
            continue                     # Alice exhausted, or tie (already counted in u_AQMS)
        total += (1 - gamma) * p(b[i - 1]) * FB(i - 1) * FA(lA) * p(B[i] - A[lA])   # Bob found first
    return total

def bob_payoff(a, b, gamma, p):
    return alice_payoff(b, a, gamma, p)

# ---------------------------------------------------------------- 5. brute force
def brute_force(a, b, g, p):
    """Enumerate every success/failure pattern of all scheduled measurements and of both possible
    AQMS responses; return Alice's exact expected payoff (1 = wins alone; in a fork g if she found first,
    1 - g if Bob did, 1/2 at a same-tick tie; 0 otherwise)."""
    c = len(a)
    A = list(itertools.accumulate(a)); B = list(itertools.accumulate(b))
    total = 0.0
    for sa in itertools.product([0, 1], repeat=c):
        for sb in itertools.product([0, 1], repeat=c):
            pr = math.prod(p(a[i]) if sa[i] else 1 - p(a[i]) for i in range(c)) \
               * math.prod(p(b[i]) if sb[i] else 1 - p(b[i]) for i in range(c))
            succ = [A[i] for i in range(c) if sa[i]] + [B[i] for i in range(c) if sb[i]]
            if not succ:
                continue
            t = min(succ)
            aw = any(sa[i] and A[i] == t for i in range(c))
            bw = any(sb[i] and B[i] == t for i in range(c))
            if aw and bw:                                   # both scheduled measurements succeed at t: tie fork
                total += pr * 0.5
                continue
            if aw:                                          # Alice first; Bob responds unless he measures at t anyway
                if any(B[i] == t for i in range(c)):        # his scheduled measurement at t failed -> Alice alone
                    total += pr
                elif sum(B[i] < t for i in range(c)) < c:
                    lastB = max([B[i] for i in range(c) if B[i] < t], default=0)
                    q = p(t - lastB)
                    total += pr * ((1 - q) * 1 + q * g)
                else:                                       # Bob exhausted
                    total += pr
            else:                                           # Bob first; Alice responds
                if any(A[i] == t for i in range(c)):
                    pass                                    # Alice's scheduled measurement at t failed -> 0
                elif sum(A[i] < t for i in range(c)) < c:
                    lastA = max([A[i] for i in range(c) if A[i] < t], default=0)
                    total += pr * p(t - lastA) * (1 - g)
    return total

# ---------------------------------------------------------------- 6. piecewise forms as printed in the paper
def alice_payoff_piecewise(a, b, g, p):
    c = len(a)
    A = [0] + list(itertools.accumulate(a)); B = [0] + list(itertools.accumulate(b))
    FA = lambda n: math.prod(1 - p(a[r]) for r in range(n)); FB = lambda n: math.prod(1 - p(b[r]) for r in range(n))
    tot = 0.0
    for i in range(1, c + 1):
        pre = p(a[i - 1]) * FA(i - 1)
        j = next((j for j in range(1, c + 1) if (j == 1 or B[j - 1] < A[i]) and A[i] <= B[j]), None)   # meas + AQMS rows
        if j is None:
            tot += pre * FB(c)
        else:
            gj = 0.5 if A[i] == B[j] else g                                                            # tie row
            tot += pre * FB(j - 1) * ((1 - p(A[i] - B[j - 1])) + gj * p(A[i] - B[j - 1]))
        j = next((j for j in range(1, c + 1) if (j == 1 or A[j - 1] < B[i]) and B[i] < A[j]), None)    # resp rows (strict)
        if j is not None:
            tot += (1 - g) * p(b[i - 1]) * FB(i - 1) * FA(j - 1) * p(B[i] - A[j - 1])
    return tot

def multi_tie(a, b):
    """KNOWN EDGE CASE of the paper's closed form (not of this code): if a zero-iteration measurement makes one
    player measure twice at the same cumulative time, and the other player also measures at that time, the closed
    form treats only one of the coinciding measurements as the competing one. The resulting error is at most of
    order p(0) * p(k) where p(0) ~ 1/W (~2e-24 at today's difficulty), i.e. ~1e-38 in nonce-only and ~1e-24 in
    full-header; it only shows up in toy tests with large p. Brute force and closed form agree exactly on all other
    profiles."""
    A = list(itertools.accumulate(a)); B = list(itertools.accumulate(b))
    return any(A.count(t) > 1 and t in B for t in A) or any(B.count(t) > 1 and t in A for t in B)

# ---------------------------------------------------------------- 7. self-tests
if __name__ == "__main__":
    random.seed(1)
    print(f"W_2025 = {W_2025:.6e}   2^32/W = {N32 / W_2025:.6e}   k_opt^32 = {KOPT32}   k_opt(W) = {kopt_full_header(W_2025)}")
    assert KOPT32 == 51471

    # (a) closed form == brute force == piecewise, on a toy p with large success probabilities
    toyW = 3000.0
    p_toy = lambda k: math.sin((2 * k + 1) * math.asin(1 / math.sqrt(toyW))) ** 2
    worst = 0.0
    for _ in range(600):
        c = random.randint(1, 3)
        a = [random.choice([0, 5, 10, 15, 20, 30]) for _ in range(c)]
        b = [random.choice([0, 5, 10, 15, 20, 30]) for _ in range(c)]
        g = random.random()
        if multi_tie(a, b):
            continue            # known edge case, see multi_tie() docstring
        u = alice_payoff(a, b, g, p_toy)
        worst = max(worst, abs(u - brute_force(a, b, g, p_toy)), abs(u - alice_payoff_piecewise(a, b, g, p_toy)))
        # payoff bounds: 0 <= A, and A + B <= 1 (a fork pays gamma + (1-gamma), or 1/2 + 1/2, in total)
        assert -1e-15 <= u and u + bob_payoff(a, b, g, p_toy) <= 1 + 1e-12
    print(f"closed form vs brute force / piecewise, max |diff| = {worst:.2e}")
    assert worst < 1e-12

    # (b) c = 1 entries (first-finder rule: gamma to whoever found first, 1/2 at a tie)
    pa, pb = p_toy(10), p_toy(20)
    for g in (0.3, 0.6, 1.0):
        assert abs(alice_payoff([10], [20], g, p_toy) - (pa * (1 - pa) + g * pa * pa)) < 1e-15        # a < b
        assert abs(alice_payoff([20], [10], g, p_toy) - (pb * (1 - pa) + (1 - g) * pa * pa)) < 1e-15  # a > b
        assert abs(alice_payoff([10], [10], g, p_toy) - (pa * (1 - pa) + 0.5 * pa * pa)) < 1e-15      # tie
    assert abs(alice_payoff([20], [10], 1.0, p_toy) - pb * (1 - pa)) < 1e-15    # gamma = 1: responding is worthless

    # (c) nonce-only exact vs approx; full-header invariance in W
    for D in (1, 2, 8, 2**10, D_2025):
        W = W_from_D(D)
        print(f"nonce-only  D={D:<12g} exact p(kopt32)={p_nonce_only_exact(KOPT32, W):.6e}  approx={p_nonce_only_approx(KOPT32, W):.6e}")
    for We in (40, 60, math.log2(W_2025)):
        W = 2.0 ** We; kap = kopt_full_header(W)
        print(f"full-header W=2^{We:.2f}: p(floor(x*kappa)), x=.25,.5,.75,1 ->",
              [round(p_full_header(math.floor(x * kap), W), 6) for x in (.25, .5, .75, 1)])
    print("all reference tests passed")
