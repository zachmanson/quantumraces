import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

def visualize_nash_equilibria_discrete_file(filename="output.txt", normalization_factor=1500, difficulty_label="high"):
    alice_data, bob_data = {}, {}
    try:
        with open(filename, 'r') as f:
            lines = f.read().strip().split('\n')
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return

    for line in lines:
        if not line.strip():
            continue
        if line.startswith('---'):
            continue
        parts = line.split(' ', 1)
        if len(parts) < 2:
            print(f"Skipping malformed line: {repr(line)}")
            continue
        player = parts[0]
        tuple_str_end_idx = parts[1].rfind(']')
        if tuple_str_end_idx == -1:
            print(f"Skipping line with no ']': {repr(line)}")
            continue
        tuple_str = parts[1][:tuple_str_end_idx + 1]
        try:
            current_tuple = eval(tuple_str.replace('np.int64(', '').replace(')', ''))
        except Exception:
            continue
        try:
            probability = float(parts[1][tuple_str_end_idx + 2:].strip())
        except ValueError:
            continue
        if player == 'Alice':
            alice_data[tuple(current_tuple)] = probability
        elif player == 'Bob':
            bob_data[tuple(current_tuple)] = probability

    def create_discrete_heatmap(player_name, data, label, normalization_factor, difficulty_label):
        if not data:
            return
        sorted_tuples = sorted(data.items(), key=lambda x: x[1], reverse=True)
        max_len = max(len(tup) for tup, _ in sorted_tuples)
        cmap = mcolors.LinearSegmentedColormap.from_list("custom_cmap", ["white", "black"])

        if max_len == 1:
            figsize = min(max(len(sorted_tuples) * 0.6, 8), 12), 3
        else:
            figsize = len(sorted_tuples) * 0.7, max_len * 1.2

        fig, ax = plt.subplots(figsize=figsize)
        x_ticks = []
        for i, (tup, prob) in enumerate(sorted_tuples):
            x_ticks.append(i)
            for j, val in enumerate(tup):
                ax.add_patch(plt.Rectangle((i - 0.5, j - 0.5), 1, 1, facecolor=cmap(val / normalization_factor), edgecolor='black', linewidth=0.5))
        ax.set_xlim(-0.5, len(sorted_tuples) - 0.5)
        ax.set_ylim(max_len - 0.5, -0.5)

        if player_name == 'Alice':
            supp_label = r'$\sigma_A(\mathbf{k})$'
        else:
            supp_label = r'$\sigma_B(\mathbf{k})$'

        ax.set_ylabel('$i$', rotation=0, labelpad=10, fontsize = 14)
        ax.set_xticks([])
        ax.set_xticklabels([])

        if max_len == 1:
            for i, (_, prob) in enumerate(sorted_tuples):
                prob_label = "<0.01" if prob < 0.01 else f"{prob:.2f}"
                ax.text(i, -0.9, prob_label, fontsize=9, rotation=45,
                        ha='right', va='top', transform=ax.get_xaxis_transform())
            ax.set_xlabel(supp_label, fontsize=10, labelpad=40)
        else:
            for i, (_, prob) in enumerate(sorted_tuples):
                prob_label = "<0.01" if prob < 0.01 else f"{prob:.2f}"
                ax.text(i, max_len - 0.5 + 0.1, prob_label, fontsize=9, rotation=0,
                        ha='center', va='top', transform=ax.transData)
            ax.set_xlabel(supp_label, fontsize=10, labelpad=20)

        ax.set_yticks(np.arange(max_len))
        ax.set_yticklabels([f'${i+1}$' for i in range(max_len)], fontsize=10)
        norm = mcolors.Normalize(vmin=0, vmax=1)
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = fig.colorbar(sm, ax=ax, fraction=0.015, pad=0.04, shrink=0.5)
        cbar.set_ticks([0, 1])
        cbar.set_ticklabels(['0', r'$\kappa$'])
        ax.set_aspect('equal', adjustable='box')

        label_y = -0.35 if max_len == 3 else -0.55 if max_len == 2 else -0.30 if max_len == 4 else -3
        ax.text(0.5, label_y, label, fontsize=10, ha='center', va='top', transform=ax.transAxes)

        plt.tight_layout()
        plt.savefig(f'images/{player_name.lower()}_nash_heatmap_c{max_len}_{difficulty_label}.pdf', dpi=300, bbox_inches='tight')
        plt.show()

    create_discrete_heatmap('Alice', alice_data, '(a)', normalization_factor=normalization_factor, difficulty_label=difficulty_label)
    create_discrete_heatmap('Bob', bob_data, '(b)', normalization_factor=normalization_factor, difficulty_label=difficulty_label)

if __name__ == '__main__':
    visualize_nash_equilibria_discrete_file()
