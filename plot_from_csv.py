import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import pandas as pd

# Read the CSV data
df = pd.read_csv('quantum_mining_simulation_data.csv')

# Extract unique values for each dimension
difficulties = df['difficulty'].unique()
betas = df['beta'].unique()

# Sort to ensure proper ordering
difficulties = np.sort(difficulties)
betas = np.sort(betas)

# Create the matrix for stale_rate
stale_rate_matrix = np.zeros((len(difficulties), len(betas)))

# Fill the matrix with stale_rate values
for i, diff in enumerate(difficulties):
    for j, beta in enumerate(betas):
        # Find the row with matching difficulty and beta
        mask = (df['difficulty'] == diff) & (df['beta'] == beta)
        if mask.any():
            stale_rate_matrix[i, j] = df.loc[mask, 'stale_rate'].iloc[0]

# Create meshgrid for plotting
D_log = np.log2(difficulties)
D_mesh, beta_mesh = np.meshgrid(D_log, betas, indexing='ij')

# Create the 3D plot
fig = plt.figure(figsize=(14, 10))
ax = fig.add_subplot(111, projection='3d')

# Create surface plot with heatmap colors
surf = ax.plot_surface(D_mesh, beta_mesh, stale_rate_matrix, 
                       cmap='plasma', alpha=0.9, linewidth=0, antialiased=True)

# Add colorbar
cbar = fig.colorbar(surf, ax=ax, shrink=0.5, aspect=20, pad=0.1)
cbar.set_label('$p_{\\text{stale}}$', fontsize=16, rotation=90, labelpad=20)
cbar.ax.tick_params(labelsize=12)

# Set labels with larger font sizes
ax.set_xlabel('$\\log_2(D)$', fontsize=16, labelpad=10)
ax.set_ylabel('$\\beta$', fontsize=16, labelpad=10)
ax.set_zlabel('$p_{\\text{stale}}$', fontsize=16, labelpad=10)

# Increase tick label font sizes
ax.tick_params(axis='x', labelsize=12)
ax.tick_params(axis='y', labelsize=12)
ax.tick_params(axis='z', labelsize=12)

label = '(a)'
fig.text(0.5, 0.01, label, fontsize=16, ha='center', va='bottom')
plt.tight_layout(pad = 2.0, rect = [0, 0.03, 1, 0.95])
plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)

plt.savefig('images/fork_rate_vs_D_and_beta_c2.png', dpi=300)
plt.show()

print(f"Difficulty range: {difficulties.min():.0f} to {difficulties.max():.0f}")
print(f"log2(Difficulty) range: {np.log2(difficulties.min()):.1f} to {np.log2(difficulties.max()):.1f}")
print(f"Beta range: {betas.min()} to {betas.max()}")
print(f"Stale rate range: {stale_rate_matrix.min():.6f} to {stale_rate_matrix.max():.6f}")

print("\n" + "="*60)
print("COMBINATIONS WHERE STALE RATE > 1/3:")
print("="*60)

threshold = 1/3
high_stale_combinations = []

for i, diff in enumerate(difficulties):
    for j, beta in enumerate(betas):
        stale_rate = stale_rate_matrix[i, j]
        if stale_rate > threshold:
            high_stale_combinations.append((diff, beta, stale_rate))
            print(f"Difficulty: {diff:.0f} (log2: {np.log2(diff):.1f}), Beta: {beta}, Stale Rate: {stale_rate:.6f}")

print(f"\nTotal combinations with stale rate > 1/3: {len(high_stale_combinations)}")
print(f"Out of {len(difficulties) * len(betas)} total combinations")
print(f"Percentage: {len(high_stale_combinations) / (len(difficulties) * len(betas)) * 100:.1f}%")