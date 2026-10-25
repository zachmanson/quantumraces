import os

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

from util import read_equilibrium

matplotlib.rc('text', usetex=True)
matplotlib.rc('font', family='serif')
matplotlib.rc('text.latex', preamble=r'\usepackage{bm}\usepackage[T1]{fontenc}')

# Standardized output geometry for all Nash-equilibrium figures (heatmaps and
# the c=1 histogram pair), so every PDF in this family has the same physical
# width when dropped into the paper at a common \includegraphics width.
# Match FIG_MAX_WIDTH_IN to the paper's column/text width.
FIG_MAX_WIDTH_IN = 6.5   # inches; e.g. single-column text width
HIST_HEIGHT_IN = 3.5     # inches; c=1 histogram figure height, for the c=1 special case
DEFAULT_CELL_IN = 0.6    # inches per strategy — cells stay square at this size while support fits FIG_MAX_WIDTH_IN
MARGIN_IN = 1.0          # fixed headroom for tick labels, colorbar, probability annotations

# Equilibria with small enough support are placed side-by-side in the paper
# (each at ~half the single-column width) instead of stacked at full width.
# We target that physical width directly when sizing cells, so the PDF is
# already close to its final on-page size and fonts don't need compensating —
# scaling cells and fonts by the same flat factor cancels out once LaTeX
# rescales to a fixed target width, so that approach doesn't work.
SIDE_BY_SIDE_MAX_STRATEGIES = 12
SIDE_BY_SIDE_TARGET_WIDTH_IN = 3.25   # matches \includegraphics[width=0.48\linewidth] usage

# Since figures render near their true physical width in the paper, these are
# real point sizes on the page — keep them at or below the 10pt document body
# text rather than matplotlib's oversized defaults.
FONT_AXIS_LABEL = 10
FONT_TICK = 8
FONT_PANEL = 9


def visualize_equilibrium(filename, kappa, label, images_dir="images"):
    """Plot one equilibrium file, normalised by the regime's budget kappa.

    label names the regime (and equilibrium, e.g. 'nonce-only_eq2') in the output file names.
    """
    alice_data, bob_data = read_equilibrium(filename)
    normalization_factor = kappa
    difficulty_label = label
    os.makedirs(images_dir, exist_ok=True)

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
        ax.set_xlabel(r'$\bm{k}/\kappa$', fontsize=FONT_AXIS_LABEL)
        ax.set_ylabel(ylabel, fontsize=FONT_AXIS_LABEL)
        ax.tick_params(labelsize=FONT_TICK)
        ax.set_xlim(0, 1)
        ax.text(0.5, -0.25, panel_label, fontsize=FONT_PANEL, ha='center', va='top', transform=ax.transAxes)

    def create_discrete_heatmap(player_name, data, label, normalization_factor, difficulty_label):
        if not data:
            return
        sorted_tuples = sorted(data.items(), key=lambda x: x[1], reverse=True)
        max_len = max(len(tup) for tup, _ in sorted_tuples)

        if player_name == 'Alice':
            supp_label = r'$\sigma_{\mathrm{A}}(\bm{k})$'
        else:
            supp_label = r'$\sigma_{\mathrm{B}}(\bm{k})$'

        # Fixed cell size for readability and square cells, but never exceed the
        # target width for this equilibrium's placement (full column if stacked,
        # ~half column if side-by-side) — shrink cells only for oversized support.
        n_cols = len(sorted_tuples)
        cell_in = min(DEFAULT_CELL_IN, target_width_in / n_cols)
        # Once cells are shrunk below the comfortable size, horizontal probability
        # labels no longer fit side by side — rotate them and reserve extra room.
        dense = cell_in < DEFAULT_CELL_IN
        margin_in = MARGIN_IN + (0.4 if dense else 0.0)
        figsize = (cell_in * n_cols, cell_in * max_len + margin_in)
        font_axis_label = FONT_AXIS_LABEL
        font_tick = FONT_TICK
        font_panel = FONT_PANEL
        cmap = mcolors.LinearSegmentedColormap.from_list("custom_cmap", ["white", "black"])
        fig, ax = plt.subplots(figsize=figsize)

        for i, (tup, prob) in enumerate(sorted_tuples):
            for j, val in enumerate(tup):
                ax.add_patch(plt.Rectangle((i - 0.5, j - 0.5), 1, 1, facecolor=cmap(val / normalization_factor), edgecolor='black', linewidth=0.5))
        ax.set_xlim(-0.5, len(sorted_tuples) - 0.5)
        ax.set_ylim(max_len - 0.5, -0.5)

        ax.set_ylabel('$i$', rotation=0, labelpad=10, fontsize=font_axis_label)
        ax.set_xticks([])
        ax.set_xticklabels([])

        for i, (_, prob) in enumerate(sorted_tuples):
            prob_label = r"$\mathord{<}0.01$" if prob < 0.01 else f"{prob:.2f}"
            if dense:
                ax.text(i, max_len - 0.5 + 0.1, prob_label, fontsize=font_tick, rotation=90,
                        ha='right', va='top', rotation_mode='anchor', transform=ax.transData,
                        clip_on=False)
            else:
                ax.text(i, max_len - 0.5 + 0.1, prob_label, fontsize=font_tick, rotation=0,
                        ha='center', va='top', transform=ax.transData)
        ax.set_xlabel(supp_label, fontsize=font_axis_label, labelpad=20)

        ax.set_yticks(np.arange(max_len))
        ax.set_yticklabels([f'${i+1}$' for i in range(max_len)], fontsize=font_tick)
        norm = mcolors.Normalize(vmin=0, vmax=1)
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = fig.colorbar(sm, ax=ax, fraction=0.015, pad=0.04, shrink=0.5)
        cbar.set_ticks([0, 1])
        cbar.set_ticklabels(['0', r'$\kappa$'])
        cbar.ax.tick_params(labelsize=font_tick)
        ax.set_aspect('equal', adjustable='box')

        # Anchored to the axes edge but offset by a fixed physical distance (points),
        # so placement stays correct regardless of the figure's aspect ratio.
        label_offset_pt = -50 if dense else -38
        ax.annotate(label, xy=(0.5, 0), xycoords='axes fraction',
                    xytext=(0, label_offset_pt), textcoords='offset points',
                    fontsize=font_panel, ha='center', va='top')

        plt.tight_layout()
        plt.savefig(os.path.join(images_dir, f'{player_name.lower()}_nash_heatmap_c{max_len}_{difficulty_label}.pdf'), dpi=300, bbox_inches='tight')
        plt.close(fig)

    # For c=1, both players share a single side-by-side figure
    alice_sorted = sorted(alice_data.items(), key=lambda x: x[1], reverse=True) if alice_data else []
    bob_sorted   = sorted(bob_data.items(),   key=lambda x: x[1], reverse=True) if bob_data   else []
    alice_max_len = max((len(t) for t, _ in alice_sorted), default=0)
    bob_max_len   = max((len(t) for t, _ in bob_sorted),   default=0)

    # Both players' heatmaps for a given equilibrium share one target width,
    # based on whichever support is larger, so the pair stays visually consistent.
    n_strategies = max(len(alice_sorted), len(bob_sorted))
    target_width_in = SIDE_BY_SIDE_TARGET_WIDTH_IN if n_strategies <= SIDE_BY_SIDE_MAX_STRATEGIES else FIG_MAX_WIDTH_IN

    if alice_max_len == 1 and bob_max_len == 1:
        fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(FIG_MAX_WIDTH_IN, HIST_HEIGHT_IN))
        _plot_histogram_ax(ax_a, alice_data, normalization_factor,
                           ylabel=r'$\sigma_{\mathrm{A}}(\bm{k})$', panel_label='(a)')
        _plot_histogram_ax(ax_b, bob_data,   normalization_factor,
                           ylabel=r'$\sigma_{\mathrm{B}}(\bm{k})$', panel_label='(b)')
        plt.tight_layout()
        plt.savefig(os.path.join(images_dir, f'nash_heatmap_c1_{difficulty_label}.pdf'), dpi=300, bbox_inches='tight')
        plt.close(fig)
    else:
        create_discrete_heatmap('Alice', alice_data, '(a)', normalization_factor=normalization_factor, difficulty_label=difficulty_label)
        create_discrete_heatmap('Bob', bob_data, '(b)', normalization_factor=normalization_factor, difficulty_label=difficulty_label)
