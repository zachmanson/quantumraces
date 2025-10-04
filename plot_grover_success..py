import numpy as np
import matplotlib.pyplot as plt

# Parameters
D_exponents = np.arange(20, 50, 0.2)        # D from 2^20 to 2^50
D_vals = 2**D_exponents
N_nonce = 2**32
k_max = int(np.floor(np.pi/4 * np.sqrt(N_nonce)))  # Max Grover iterations per run

# Classical success probability: 1/D
p_classical = 1 / D_vals

# Grover success probability per run
p_grover = np.zeros_like(D_vals)

for i, D in enumerate(D_vals):
    if D <= N_nonce:
        k_opt = int(np.floor(np.pi/4 * np.sqrt(D)))
    else:
        k_opt = k_max
    theta = np.arcsin(1 / np.sqrt(D))
    p_grover[i] = np.sin((2*k_opt + 1) * theta)**2

# Plot
plt.figure(figsize=(8,5))
plt.plot(D_vals, p_classical, label='Classical', color='gray', lw=2)
plt.plot(D_vals, p_grover, label='Quantum', color='blue', lw=2)
plt.axvline(N_nonce, color='red', linestyle='--')
plt.xscale('log', base=2)
plt.yscale('log')
plt.xlabel(r'$D$')
plt.ylabel(r'$p$')
plt.legend()
plt.grid(alpha=0.3, which='both')
plt.tight_layout()
plt.show()
