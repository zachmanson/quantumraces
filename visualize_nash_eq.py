import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

matplotlib.rc('text', usetex=True)
matplotlib.rc('font', family='serif')
matplotlib.rc('text.latex', preamble=r'\usepackage{bm}\usepackage[T1]{fontenc}')


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

    def _plot_histogram_ax(ax, data, normalization_factor, ylabel, panel_label):
        sorted_tuples = sorted(data.items(), key=lambda x: x[1], reverse=True)
        iters = [tup[0] / normalization_factor for tup, _ in sorted_tuples]
        probs = [prob for _, prob in sorted_tuples]
        num_bins = 20
        bin_edges = np.linspace(0, 1, num_bins + 1)
        bin_probs = np.zeros(num_bins)
        for k, p in zip(iters, probs):
            idx = min(np.searchsorted(bin_edges, k, side='right') - 1, num_bins - 1)
            bin_probs[idx] += p
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        bin_width = bin_edges[1] - bin_edges[0]
        ax.bar(bin_centers, bin_probs, width=bin_width * 0.9, color='black')
        ax.set_xlabel(r'$\bm{k}/\kappa$', fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.set_xlim(0, 1)
        ax.text(0.5, -0.25, panel_label, fontsize=10, ha='center', va='top', transform=ax.transAxes)

    def create_discrete_heatmap(player_name, data, label, normalization_factor, difficulty_label):
        if not data:
            return
        sorted_tuples = sorted(data.items(), key=lambda x: x[1], reverse=True)
        max_len = max(len(tup) for tup, _ in sorted_tuples)

        if player_name == 'Alice':
            supp_label = r'$\sigma_{\mathrm{A}}(\bm{k})$'
        else:
            supp_label = r'$\sigma_{\mathrm{B}}(\bm{k})$'

        figsize = len(sorted_tuples) * 0.7, max_len * 1.2
        cmap = mcolors.LinearSegmentedColormap.from_list("custom_cmap", ["white", "black"])
        fig, ax = plt.subplots(figsize=figsize)

        for i, (tup, prob) in enumerate(sorted_tuples):
            for j, val in enumerate(tup):
                ax.add_patch(plt.Rectangle((i - 0.5, j - 0.5), 1, 1, facecolor=cmap(val / normalization_factor), edgecolor='black', linewidth=0.5))
        ax.set_xlim(-0.5, len(sorted_tuples) - 0.5)
        ax.set_ylim(max_len - 0.5, -0.5)

        ax.set_ylabel('$i$', rotation=0, labelpad=10, fontsize=14)
        ax.set_xticks([])
        ax.set_xticklabels([])

        for i, (_, prob) in enumerate(sorted_tuples):
            prob_label = r"$\mathord{<}0.01$" if prob < 0.01 else f"{prob:.2f}"
            ax.text(i, max_len - 0.5 + 0.1, prob_label, fontsize=11, rotation=0,
                    ha='center', va='top', transform=ax.transData)
        ax.set_xlabel(supp_label, fontsize=12, labelpad=20)

        ax.set_yticks(np.arange(max_len))
        ax.set_yticklabels([f'${i+1}$' for i in range(max_len)], fontsize=10)
        norm = mcolors.Normalize(vmin=0, vmax=1)
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = fig.colorbar(sm, ax=ax, fraction=0.015, pad=0.04, shrink=0.5)
        cbar.set_ticks([0, 1])
        cbar.set_ticklabels(['0', r'$\kappa$'])
        ax.set_aspect('equal', adjustable='box')

        label_y = -0.50 if max_len == 3 else -0.75 if max_len == 2 else -0.45 if max_len == 4 else -3
        ax.text(0.5, label_y, label, fontsize=10, ha='center', va='top', transform=ax.transAxes)

        plt.tight_layout()
        plt.savefig(f'images/{player_name.lower()}_nash_heatmap_c{max_len}_{difficulty_label}.pdf', dpi=300, bbox_inches='tight')
        plt.show()

    # For c=1, both players share a single side-by-side figure
    alice_sorted = sorted(alice_data.items(), key=lambda x: x[1], reverse=True) if alice_data else []
    bob_sorted   = sorted(bob_data.items(),   key=lambda x: x[1], reverse=True) if bob_data   else []
    alice_max_len = max((len(t) for t, _ in alice_sorted), default=0)
    bob_max_len   = max((len(t) for t, _ in bob_sorted),   default=0)

    if alice_max_len == 1 and bob_max_len == 1:
        fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(10, 3.5))
        _plot_histogram_ax(ax_a, alice_data, normalization_factor,
                           ylabel=r'$\sigma_{\mathrm{A}}(\bm{k})$', panel_label='(a)')
        _plot_histogram_ax(ax_b, bob_data,   normalization_factor,
                           ylabel=r'$\sigma_{\mathrm{B}}(\bm{k})$', panel_label='(b)')
        plt.tight_layout()
        plt.savefig(f'images/nash_heatmap_c1_{difficulty_label}.pdf', dpi=300, bbox_inches='tight')
        plt.show()
    else:
        create_discrete_heatmap('Alice', alice_data, '(a)', normalization_factor=normalization_factor, difficulty_label=difficulty_label)
        create_discrete_heatmap('Bob', bob_data, '(b)', normalization_factor=normalization_factor, difficulty_label=difficulty_label)
