import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import re 
import pandas as pd
from collections import defaultdict
from mpl_toolkits.mplot3d import Axes3D

def parse_nash_eqs(filename, strategy_total=None):
    """Parse the Nash equilibria file and return structured data."""
    with open(filename, 'r') as file:
        content = file.read()
    
    equilibria_blocks = content.split('-------------')
    equilibria_blocks = [block.strip() for block in equilibria_blocks if block.strip()]
    
    all_equilibria = []
    
    for eq_idx, block in enumerate(equilibria_blocks):
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        equilibrium = []
        
        for line in lines:
            match = re.match(r'(\w+)\s+\[(.*?)\]\s+([\d.e-]+)', line)
            if match:
                player, strategy_str, probability = match.groups()
                
                strategy_parts = strategy_str.split(',')
                strategy = []
                for part in strategy_parts:
                    part = part.strip()
                    if 'np.int64(' in part:
                        match_int = re.search(r'np\.int64\((\d+)\)', part)
                        if match_int:
                            value = int(match_int.group(1))
                        else:
                            raise ValueError(f"Could not parse integer from part: {part}")
                    else:
                        value = int(part)
                    strategy.append(value)
                
                # Normalize strategy if total is provided
                if strategy_total is not None:
                    normalized_strategy = tuple(round(val / strategy_total, 2) for val in strategy)
                else:
                    normalized_strategy = tuple(strategy)
                
                equilibrium.append({
                    'player': player,
                    'strategy': normalized_strategy,
                    'raw_strategy': tuple(strategy),  # Keep original for reference
                    'probability': float(probability)
                })
        
        if equilibrium:
            all_equilibria.append(equilibrium)
    
    return all_equilibria

def create_improved_3d_plots(equilibria_data):
    """Create improved 3D histogram plots with blue and yellow colors."""
    
    # Filter equilibria with 2D strategies
    equilibria_2d = []
    for eq_idx, equilibrium in enumerate(equilibria_data):
        if all(len(strategy_data['strategy']) == 2 for strategy_data in equilibrium):
            equilibria_2d.append((eq_idx, equilibrium))
    
    if not equilibria_2d:
        print("No equilibria with 2D strategies found for 3D plotting.")
        return []
    
    figures = []
    
    for eq_idx, equilibrium in equilibria_2d:
        fig = plt.figure(figsize=(14, 10))
        ax = fig.add_subplot(111, projection='3d')
        
        # Extract data
        x_coords = []
        y_coords = []
        z_heights = []
        colors = []
        player_labels = []
        
        # Use blue for Alice and yellow for Bob
        player_colors = {'Alice': 'blue', 'Bob': 'gold'}
        
        for strategy_data in equilibrium:
            x, y = strategy_data['strategy']
            z = strategy_data['probability']
            player = strategy_data['player']
            
            x_coords.append(x)
            y_coords.append(y)
            z_heights.append(z)
            colors.append(player_colors.get(player, 'gray'))
            player_labels.append(player)
        
        # Create 3D bars with better visibility
        bar_width = 0.04
        bar_depth = 0.04
        
        for i, (x, y, z, color, player) in enumerate(zip(x_coords, y_coords, z_heights, colors, player_labels)):
            # Use solid bars with edge lines for better visibility
            ax.bar3d(x - bar_width/2, y - bar_depth/2, 0, 
                    bar_width, bar_depth, z, 
                    color=color, alpha=0.95, 
                    edgecolor='black', linewidth=0.5,
                    label=player if player not in [pl for pl in player_labels[:i]] else "")
        
        # Better axis labels and title
        ax.set_xlabel('Strategy Component 1', fontsize=16, fontweight='bold', labelpad=15)
        ax.set_ylabel('Strategy Component 2', fontsize=16, fontweight='bold', labelpad=15)  
        ax.set_zlabel('Probability', fontsize=16, fontweight='bold', labelpad=15)
        ax.set_title(f'Nash Equilibrium {eq_idx + 1} - 3D Strategy Space', 
                    fontsize=18, fontweight='bold', pad=20)
        
        # Better axis limits
        x_range = max(x_coords) - min(x_coords) if len(set(x_coords)) > 1 else 0.2
        y_range = max(y_coords) - min(y_coords) if len(set(y_coords)) > 1 else 0.2
        z_range = max(z_heights)
        
        padding_factor = 0.3
        x_min, x_max = min(x_coords) - x_range * padding_factor, max(x_coords) + x_range * padding_factor
        y_min, y_max = min(y_coords) - y_range * padding_factor, max(y_coords) + y_range * padding_factor
        z_max = z_range * 1.1
        
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.set_zlim(0, z_max)
        
        # Improve tick labels
        ax.tick_params(axis='x', labelsize=12)
        ax.tick_params(axis='y', labelsize=12)
        ax.tick_params(axis='z', labelsize=12)
        
        # Add grid
        ax.grid(True, alpha=0.3)
        
        # Better legend
        unique_players = sorted(list(set(player_labels)))
        if len(unique_players) > 1:
            handles, labels = ax.get_legend_handles_labels()
            if handles:
                ax.legend(handles, labels, loc='upper left', fontsize=14,
                         bbox_to_anchor=(0.02, 0.98), framealpha=0.9)
        
        # Better viewing angle
        ax.view_init(elev=20, azim=45)
        
        plt.tight_layout()
        figures.append(fig)
    
    return figures

def create_single_heatmaps(equilibria_data):
    """Create single large heatmaps with unique strategies on x-axis and hardcoded subplot label."""
    
    figures = []
    
    for eq_idx, equilibrium in enumerate(equilibria_data):
        # Get unique strategies across all players
        unique_strategies = []
        strategy_to_index = {}
        
        for strategy_data in equilibrium:
            strat = strategy_data['strategy']
            if strat not in unique_strategies:
                unique_strategies.append(strat)
                strategy_to_index[strat] = len(unique_strategies) - 1
        
        # Create figure
        n_strategies = len(unique_strategies)
        fig_width = max(12, n_strategies * 0.8)
        fig, ax = plt.subplots(figsize=(fig_width, 9))
        
        # Create strategy labels
        strategy_labels = []
        for strat in unique_strategies:
            if len(strat) == 2:
                strategy_labels.append(f"({strat[0]:.2f},{strat[1]:.2f})")
            elif len(strat) <= 4:
                strategy_labels.append(f"({','.join(f'{x:.2f}' for x in strat)})")
            else:
                strategy_labels.append(f"({strat[0]:.2f},{strat[1]:.2f},...)")
        
        # Get unique players
        unique_players = sorted(list(set(s['player'] for s in equilibrium)))
        
        # Create heatmap data matrix: rows = players, cols = unique strategies
        heatmap_data = np.zeros((len(unique_players), len(unique_strategies)))
        
        for strategy_data in equilibrium:
            player = strategy_data['player']
            strat = strategy_data['strategy']
            prob = strategy_data['probability']
            
            player_idx = unique_players.index(player)
            strat_idx = strategy_to_index[strat]
            
            heatmap_data[player_idx, strat_idx] = prob
        
        # Create heatmap WITHOUT annotations (numbers)
        sns.heatmap(heatmap_data, 
                   xticklabels=strategy_labels,
                   yticklabels=unique_players,
                   annot=False,
                   fmt='',
                   cmap='YlOrRd',
                   ax=ax,
                   cbar_kws={'label': 'Probability'},
                   linewidths=0.5,
                   vmin=0)
        
        # Title and labels
        ax.set_xlabel('Unique Strategy Profiles', fontsize=14, fontweight='bold')
        ax.set_ylabel('Players', fontsize=14, fontweight='bold')
        
        # Rotate x-labels
        ax.tick_params(axis='x', labelsize=9, rotation=45)
        ax.tick_params(axis='y', labelsize=12, rotation=0)
        
        # Colorbar
        cbar = ax.collections[0].colorbar
        cbar.ax.tick_params(labelsize=11)
        cbar.set_label('Probability', fontsize=12, fontweight='bold')
        
        # Adjust layout to make room for bottom label
        plt.subplots_adjust(bottom=0.25)
        
        ## ADD SUBPLOT LABEL BELOW FIGURE (hardcoded - change as needed)
        #label = '(c)'  # Change this to whatever label you want
        #ax.text(0.5, -0.25, label, fontsize=16, fontweight='bold', ha='center', va='top', transform=ax.transAxes)
        
        figures.append(fig)
    
    return figures

def create_equilibrium_histograms(equilibria_data):
    
    figures = []
    
    for eq_idx, equilibrium in enumerate(equilibria_data):
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Group strategies by player
        player_data = defaultdict(list)
        for strategy_data in equilibrium:
            player_data[strategy_data['player']].append(strategy_data['probability'])
        
        # Create grouped bar chart
        players = sorted(player_data.keys())
        x_pos = np.arange(len(players))
        
        # Calculate bar positions for multiple strategies per player
        max_strategies = max(len(probs) for probs in player_data.values())
        bar_width = 0.8 / max_strategies
        
        # Use blue for Alice and yellow for Bob
        player_colors = {'Alice': 'blue', 'Bob': 'gold'}
        
        for strategy_idx in range(max_strategies):
            strategy_probs = []
            colors_for_bars = []
            for player in players:
                if strategy_idx < len(player_data[player]):
                    strategy_probs.append(player_data[player][strategy_idx])
                    colors_for_bars.append(player_colors.get(player, 'gray'))
                else:
                    strategy_probs.append(0)
                    colors_for_bars.append('white')
            
            x_positions = x_pos + (strategy_idx - max_strategies/2 + 0.5) * bar_width
            bars = ax.bar(x_positions, strategy_probs, bar_width, 
                         color=colors_for_bars, alpha=0.8, edgecolor='black',
                         label=f'Strategy {strategy_idx + 1}' if strategy_idx == 0 else "")
            
            # Add value labels on bars
            for bar, prob in zip(bars, strategy_probs):
                if prob > 0:
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                           f'{prob:.2f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        # Customize
        ax.set_xlabel('Players', fontsize=16, fontweight='bold')
        ax.set_ylabel('Probability', fontsize=16, fontweight='bold')
        ax.set_title(f'Nash Equilibrium {eq_idx + 1} - Probability Distribution', 
                    fontsize=18, fontweight='bold', pad=20)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(players, fontsize=14)
        ax.set_ylim(0, 1)
        ax.grid(True, alpha=0.3, axis='y')
        ax.tick_params(axis='y', labelsize=12)
        
        plt.tight_layout()
        figures.append(fig)
    
    return figures

def print_improved_summary(equilibria_data):
    """Print a cleaner summary of the equilibria."""
    print("\n" + "="*60)
    print("NASH EQUILIBRIA ANALYSIS SUMMARY")
    print("="*60)
    
    total_equilibria = len(equilibria_data)
    total_strategies = sum(len(eq) for eq in equilibria_data)
    
    print(f"Number of equilibria found: {total_equilibria}")
    print(f"Total strategy profiles: {total_strategies}")
    
    # Player analysis
    all_players = set()
    for equilibrium in equilibria_data:
        for strategy_data in equilibrium:
            all_players.add(strategy_data['player'])
    
    print(f"Players involved: {', '.join(sorted(all_players))} ({len(all_players)} total)")
    
    # Strategy dimension analysis
    strategy_dims = set()
    for equilibrium in equilibria_data:
        for strategy_data in equilibrium:
            strategy_dims.add(len(strategy_data['strategy']))
    
    print(f"Strategy dimensions: {sorted(strategy_dims)}")
    
    # Probability statistics
    all_probs = []
    for equilibrium in equilibria_data:
        for strategy_data in equilibrium:
            all_probs.append(strategy_data['probability'])
    
    if all_probs:
        print(f"\nProbability Statistics:")
        print(f"   Mean: {np.mean(all_probs):.4f}")
        print(f"   Std:  {np.std(all_probs):.4f}")
        print(f"   Range: [{np.min(all_probs):.4f}, {np.max(all_probs):.4f}]")
    
    # Per-equilibrium breakdown
    print(f"\nEquilibrium Breakdown:")
    for eq_idx, equilibrium in enumerate(equilibria_data):
        n_strategies = len(equilibrium)
        players_in_eq = set(s['player'] for s in equilibrium)
        avg_prob = np.mean([s['probability'] for s in equilibrium])
        print(f"   Eq {eq_idx + 1}: {n_strategies} strategies, "
              f"players: {', '.join(sorted(players_in_eq))}, "
              f"avg prob: {avg_prob:.3f}")
    
    print("="*60)

def main():
    """Main function - only histograms and heatmaps."""
    
    STRATEGY_TOTAL = 8571866.0
    #STRATEGY_TOTAL = 1500.0
    
    try:
        equilibria_data = parse_nash_eqs('output.txt', strategy_total=STRATEGY_TOTAL)
        
        if not equilibria_data:
            print("No equilibria found in the file!")
            return
        
        print_improved_summary(equilibria_data)
        print("\nGenerating visualizations...")
        
        # Create 3D histograms (blue/yellow for Alice/Bob)
        fig_list_3d = create_improved_3d_plots(equilibria_data)
        for i, fig in enumerate(fig_list_3d):
            filename = f'images/3d_histogram_{i+1}.png'
            fig.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
            print(f"   {filename}")
        
        # Create single large heatmaps (no splitting, no numbers)
        fig_list_heatmaps = create_single_heatmaps(equilibria_data)
        for i, fig in enumerate(fig_list_heatmaps):
            filename = f'images/heatmap_{i+1}_c2_ideal_BTQ.png'
            fig.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
            print(f"   {filename}")
        
        # Create histograms (blue/yellow for Alice/Bob)
        fig_list_histograms = create_equilibrium_histograms(equilibria_data)
        for i, fig in enumerate(fig_list_histograms):
            filename = f'images/histogram_{i+1}.png'
            fig.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
            print(f"   {filename}")
        
        print(f"\nAll visualizations saved!")
        
        plt.show()
        
    except FileNotFoundError:
        print("Error: 'output.txt' file not found!")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()