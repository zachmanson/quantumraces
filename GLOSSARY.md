# Glossary

**Network difficulty (D)**: the ratio of the maximum target to the current target, as reported by blockchain.com. Not a number of hashes.

**Expected work (W)**: expected number of hashes to find a valid block, W = D·2^48/(2^16−1). The model uses W, never D, for probabilities.

**Mining regime**: which search space the quantum oracle covers.
- **Nonce-only**: oracle searches the 32-bit nonce; success probability is averaged over the Binomial(2^32, 1/W) number of valid nonces.
- **Full-header**: oracle searches the full header (Merkle root incl. extraNonce, timestamp, nonce); the marked fraction is 1/W.
_Avoid_: low / high / ideal (retired difficulty regimes).

**Grover iteration budget (κ)**: maximum total Grover iterations a miner may spend across all c measurements in one race; k_opt^32 in nonce-only, k_opt(W) in full-header.

**Measurement**: one run of Grover search ending in a quantum measurement. Each miner makes c per race. Each run searches a fresh candidate header, so a miner's measurements are independent trials.

**Pure strategy**: a c-tuple of Grover iteration counts, one per measurement, summing to at most κ. Zero-iteration measurements are allowed.

**Sampled grid (S0′)**: the n_q+1 quadratically spaced iteration counts the computation draws pure-strategy components from.

**AQMS response**: when one miner's measurement succeeds, the other immediately measures with the iterations accumulated since their own last measurement. Impossible if they have used all c measurements (**exhausted**).

**Tie**: both miners scheduled to measure at the same cumulative iteration count; both scheduled measurements count and there is no separate response.

**Fork**: two or more valid blocks (from either miner or the classical network) for the same height; one is kept and the rest become **stale**.

**First-finder fork rule (γ_S)**: γ_S is the probability that the first-broadcast block (the first finder's, since a find is broadcast at once) wins a fork caused by an AQMS response. The responder's block wins w.p. 1 − γ_S, and in a tie each wins w.p. ½. The game is symmetric for every γ_S (B = Aᵀ). Headline value 0.6. At γ_S = ½ it equals the retired owner rule.
_Avoid_: "probability that Alice's block wins" (the retired owner rule).

**Stale rate (p_stale)**: stale blocks divided by all blocks found (stale blocks included), per simulated day.

**Classical network**: all non-quantum miners. Absent from the game; in the simulation, its blocks arrive as a Poisson process (mean 600 s) and each forks with the baseline probability 0.0024.
